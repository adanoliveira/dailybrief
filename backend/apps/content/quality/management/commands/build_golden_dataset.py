"""
Build the golden dataset for content extraction evaluation.

For each candidate article, fetches the publisher URL fresh and produces
a "publisher canonical body" via two independent extractors:

  1. readability-lxml (Mozilla Readability port) — primary ground truth
  2. newspaper3k                                  — secondary cross-check

When the two agree (high token overlap), confidence is HIGH.
When they disagree, confidence is LOW — article still saved but flagged
as ambiguous for later review.

Optional escalation (--with-screenshot):
  Captures a full-page screenshot via Playwright for audit + visual diff.

Output:
  apps/content/quality/fixtures/golden/<article_id>/
    ├── ground_truth.txt          # readability output (primary)
    ├── ground_truth_alt.txt      # newspaper3k output (secondary)
    ├── publisher.html            # raw HTML fetched fresh from publisher
    ├── screenshot.png            # full-page screenshot (if --with-screenshot)
    └── metadata.json             # URL, fetch_status, paywall_detected,
                                  # extraction_confidence, char_overlap, etc.

After successful capture, this also creates/updates a row in
quality_reference_examples so the eval pipeline (compare_templates,
quality_benchmark) can use these as calibration / benchmarking examples.
"""

import base64
import json
import logging
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

import requests
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15"
)
REQUEST_TIMEOUT_S = 25
PLAYWRIGHT_TIMEOUT_MS = 45_000
PLAYWRIGHT_VIEWPORT = {"width": 1280, "height": 900}
VISION_MODEL = "gpt-4o-mini"
VISION_MAX_TOKENS = 200
# gpt-4o-mini pricing (2026): $0.15 / 1M prompt, $0.60 / 1M completion
VISION_PROMPT_COST_PER_TOKEN = 0.15 / 1_000_000
VISION_COMPLETION_COST_PER_TOKEN = 0.60 / 1_000_000

# Per-publisher canonical body selectors. Selectors are tried in order; first
# non-empty extraction with >=80 words wins. New publishers can be added here
# without touching command logic. Generic fallbacks (article, main) live below.
PUBLISHER_SELECTORS: dict[str, list[str]] = {
    "globo.com": ["p.content-text__container"],          # ge.globo.com, g1.globo.com, valor.globo.com
    "cbssports.com": ["article"],                        # take FIRST article element
    "bbc.com": ["article"],
    "bbc.co.uk": ["article"],
    "nytimes.com": ["section[name='articleBody']", "[itemprop='articleBody']", "article"],
    "washingtonpost.com": ["[data-qa='article-body']", "article"],
}
GENERIC_SELECTORS = ["[itemprop='articleBody']", "article", "main article", "main"]
# Lines containing only these words are stripped as chrome (BBC has share/save bars etc.)
CHROME_TOKENS = {
    "Share", "Save", "Copy link", "Add as preferred", "Reuters", "Watch:", "Read more",
    "More on this story", "Related stories", "Sign up", "Subscribe", "Advertisement",
}
# Vision LLM is used ONLY as a 3-class CLASSIFIER (not a text extractor — vision LLMs hallucinate
# verbatim transcription on text-heavy news screenshots). It looks at the screenshot and decides
# whether the page is a real article, a paywall block, or a still-loading skeleton.
VISION_PROMPT = (
    "You are looking at a full-page screenshot of a webpage. Classify what kind of page it is.\n\n"
    "Output exactly ONE of these three tokens — no commentary, no other text:\n\n"
    "ARTICLE_PAGE — the screenshot shows a real news article with a headline and at least a few "
    "paragraphs of body prose visible. Promotional banners, ads, subscription strips, sharing "
    "buttons, and related-article cards may also be present, but actual article paragraphs are "
    "visible somewhere on the page.\n\n"
    "PAYWALL_OR_BLOCK_PAGE — the article body is completely hidden behind a paywall, subscribe-to-read "
    "modal, login wall, or bot-detection challenge page. No real article paragraphs are visible.\n\n"
    "SKELETON_LOAD — the page is still loading; you mostly see grey rectangles or shimmer placeholders "
    "where article paragraphs should be."
)
GOLDEN_DIR = (
    Path(__file__).resolve().parents[2] / "fixtures" / "golden"
)
CANDIDATES_FILE = GOLDEN_DIR / "candidates.json"


@dataclass
class CaptureResult:
    article_id: int
    url: str
    stratum: str
    source: str
    fetch_ok: bool
    http_status: Optional[int]
    fetch_error: Optional[str]
    readability_chars: int
    readability_words: int
    newspaper_chars: int
    newspaper_words: int
    selector_chars: int = 0
    selector_words: int = 0
    selector_used: Optional[str] = None         # which CSS selector matched
    page_class: str = "unknown"                 # ARTICLE_PAGE | PAYWALL_OR_BLOCK_PAGE | SKELETON_LOAD | unknown
    vision_cost_usd: float = 0.0
    char_overlap_ratio: float = 0.0             # selector vs readability agreement
    token_overlap_jaccard: float = 0.0
    primary_source: str = "selector"            # selector | readability | newspaper | none
    confidence: str = "low"                     # high | medium | low | failed
    screenshot_captured: bool = False
    notes: list = field(default_factory=list)


class Command(BaseCommand):
    help = "Capture publisher-canonical ground truth for golden dataset articles."

    def add_arguments(self, parser):
        parser.add_argument(
            "--candidates",
            type=str,
            default=str(CANDIDATES_FILE),
            help="Path to candidates.json (default: fixtures/golden/candidates.json)",
        )
        parser.add_argument(
            "--article-ids",
            nargs="+",
            type=int,
            default=None,
            help="Restrict to specific article IDs (subset of candidates).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Cap on number of articles to process (for smoke tests).",
        )
        parser.add_argument(
            "--fetcher",
            choices=["playwright", "requests", "app"],
            default="playwright",
            help="How to fetch publisher pages. "
                 "'playwright' (default): real Chromium with JS rendering + screenshot. "
                 "'requests': fast static fetch (fails on bot-detection / JS sites). "
                 "'app': use the production ContentFetcher (Chrome→Firefox→Safari→Mobile→"
                 "PaywallBypass UA rotation; bypasses many bot-detection walls but does NOT "
                 "render JS). Pairs well with playwright as a fallback.",
        )
        parser.add_argument(
            "--no-screenshot",
            action="store_true",
            help="Skip the screenshot when using --fetcher=playwright.",
        )
        parser.add_argument(
            "--no-vision",
            action="store_true",
            help="Skip the vision-LLM ground-truth pass on screenshots. "
                 "Defaults to ON when a screenshot is available and OPENAI_API_KEY is set.",
        )
        parser.add_argument(
            "--seed-reference-examples",
            action="store_true",
            help="After capture, insert/update rows in quality_reference_examples "
                 "(requires DB access + the article record to exist).",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite existing fixtures.",
        )

    # ------------------------------------------------------------------ runner

    def handle(self, *args, **options):
        candidates = self._load_candidates(options["candidates"])
        if options["article_ids"]:
            wanted = set(options["article_ids"])
            candidates = [c for c in candidates if c["id"] in wanted]
        if options["limit"]:
            candidates = candidates[: options["limit"]]

        if not candidates:
            self.stderr.write("No candidates to process.")
            return

        self.stdout.write(
            f"📚 Capturing ground truth for {len(candidates)} article(s) → {GOLDEN_DIR}"
        )

        results: list[CaptureResult] = []
        for c in candidates:
            try:
                results.append(self._capture(c, options))
            except Exception as exc:  # noqa: BLE001
                logger.exception("Capture failed for article %s", c["id"])
                results.append(
                    CaptureResult(
                        article_id=c["id"],
                        url=c["url"],
                        stratum=c["stratum"],
                        source=c["source"],
                        fetch_ok=False,
                        http_status=None,
                        fetch_error=str(exc),
                        readability_chars=0,
                        readability_words=0,
                        newspaper_chars=0,
                        newspaper_words=0,
                        char_overlap_ratio=0.0,
                        token_overlap_jaccard=0.0,
                        confidence="failed",
                        screenshot_captured=False,
                        notes=[f"unhandled: {exc!r}"],
                    )
                )

        self._write_summary(results)
        if options["seed_reference_examples"]:
            self._seed_reference_examples(results)

    # ---------------------------------------------------------------- per-item

    def _capture(self, candidate: dict, options: dict) -> CaptureResult:
        article_id = candidate["id"]
        url = candidate["url"]
        out_dir = GOLDEN_DIR / str(article_id)
        out_dir.mkdir(parents=True, exist_ok=True)

        notes: list[str] = []
        meta_path = out_dir / "metadata.json"
        if meta_path.exists() and not options["force"]:
            self.stdout.write(f"  · {article_id} ({candidate['stratum']}) — exists, skipping")
            existing = json.loads(meta_path.read_text())
            return CaptureResult(**existing["result"])

        self.stdout.write(f"  → {article_id} ({candidate['stratum']}) {url[:90]}")

        # 1. Fetch publisher HTML — playwright (real browser) by default
        screenshot_ok = False
        if options["fetcher"] == "playwright":
            html, http_status, fetch_error, screenshot_ok = self._fetch_playwright(
                url, out_dir, capture_screenshot=not options["no_screenshot"]
            )
        elif options["fetcher"] == "app":
            html, http_status, fetch_error = self._fetch_app(url, notes)
        else:
            html, http_status, fetch_error = self._fetch_requests(url)
        if html is None:
            return CaptureResult(
                article_id=article_id, url=url, stratum=candidate["stratum"],
                source=candidate["source"], fetch_ok=False, http_status=http_status,
                fetch_error=fetch_error, readability_chars=0, readability_words=0,
                newspaper_chars=0, newspaper_words=0, char_overlap_ratio=0.0,
                token_overlap_jaccard=0.0, confidence="failed",
                screenshot_captured=False, notes=[f"fetch_failed: {fetch_error}"],
            )

        (out_dir / "publisher.html").write_text(html, encoding="utf-8")

        # 2. Extract via readability-lxml (primary)
        readability_text = self._extract_readability(html, url, notes)
        (out_dir / "ground_truth.txt").write_text(readability_text, encoding="utf-8")

        # 3. Extract via newspaper3k (cross-check)
        newspaper_text = self._extract_newspaper(html, url, notes)
        (out_dir / "ground_truth_newspaper.txt").write_text(newspaper_text, encoding="utf-8")

        # 4. Extract via per-publisher CSS selectors (PRIMARY ground truth source)
        selector_text, selector_used = self._extract_via_selectors(html, url, notes)
        (out_dir / "ground_truth_selector.txt").write_text(selector_text, encoding="utf-8")

        # 5. Vision LLM as a CLASSIFIER ONLY (not a text source — vision LLMs hallucinate
        #    verbatim transcription). Tells us whether the screenshot shows an article,
        #    a paywall block, or a still-loading skeleton.
        page_class = "unknown"
        vision_cost = 0.0
        if screenshot_ok and not options["no_vision"] and os.environ.get("OPENAI_API_KEY"):
            page_class, vision_cost = self._classify_page(out_dir / "screenshot.png", notes)

        # 6. Pick primary text + compute agreement.
        #    Selector wins if it has substantial output AND vision says it's an article page.
        primary_text, primary_source = self._pick_primary(
            selector_text, readability_text, newspaper_text, page_class
        )
        (out_dir / "ground_truth.txt").write_text(primary_text, encoding="utf-8")
        (out_dir / "ground_truth_readability.txt").write_text(readability_text, encoding="utf-8")

        char_ratio, jaccard, confidence = self._three_way_confidence(
            selector_text, readability_text, newspaper_text, page_class
        )

        result = CaptureResult(
            article_id=article_id, url=url, stratum=candidate["stratum"],
            source=candidate["source"], fetch_ok=True, http_status=http_status,
            fetch_error=None,
            readability_chars=len(readability_text),
            readability_words=len(readability_text.split()),
            newspaper_chars=len(newspaper_text),
            newspaper_words=len(newspaper_text.split()),
            selector_chars=len(selector_text),
            selector_words=len(selector_text.split()),
            selector_used=selector_used,
            page_class=page_class,
            vision_cost_usd=round(vision_cost, 5),
            char_overlap_ratio=round(char_ratio, 3),
            token_overlap_jaccard=round(jaccard, 3),
            primary_source=primary_source,
            confidence=confidence,
            screenshot_captured=screenshot_ok,
            notes=notes,
        )

        meta_path.write_text(
            json.dumps(
                {
                    "candidate": candidate,
                    "result": asdict(result),
                    "fetched_at_utc": _utcnow_iso(),
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        self.stdout.write(
            f"    ✓ selector={result.selector_words}w[{result.selector_used or '-'}] "
            f"readability={result.readability_words}w "
            f"newspaper={result.newspaper_words}w "
            f"page={result.page_class} "
            f"primary={result.primary_source} "
            f"jaccard={jaccard:.2f} confidence={confidence}"
        )
        return result

    # ------------------------------------------------------------- extractors

    def _fetch_requests(self, url: str) -> tuple[Optional[str], Optional[int], Optional[str]]:
        try:
            r = requests.get(
                url,
                headers={"User-Agent": USER_AGENT, "Accept-Language": "en;q=0.9,pt-BR;q=0.8"},
                timeout=REQUEST_TIMEOUT_S,
                allow_redirects=True,
            )
            r.raise_for_status()
            return r.text, r.status_code, None
        except requests.HTTPError as e:
            return None, e.response.status_code if e.response else None, str(e)
        except Exception as e:  # noqa: BLE001
            return None, None, str(e)

    def _fetch_app(self, url: str, notes: list) -> tuple[Optional[str], Optional[int], Optional[str]]:
        """
        Use the production ContentFetcher's strategy chain. Bypasses many bot-detection
        walls via UA rotation (Chrome → Firefox → Safari → Mobile → PaywallBypass) plus
        realistic header sets. Does NOT render JS — pair with --fetcher=playwright as a
        fallback for JS-heavy sites.
        """
        try:
            from apps.content.fetcher.fetcher import ContentFetcher
        except ImportError as e:
            notes.append(f"app_fetcher_import_failed: {e!r}")
            return None, None, str(e)

        try:
            fetcher = ContentFetcher()
            result = fetcher._extract_with_strategies(url)
            if not result.success or not result.raw_html:
                err = result.error_message or "all_strategies_failed"
                notes.append(f"app_fetcher_failed: {err} (last_strategy={result.strategy_used})")
                return None, None, err
            notes.append(f"app_fetcher_strategy={result.strategy_used}")
            return result.raw_html, 200, None
        except Exception as e:  # noqa: BLE001
            notes.append(f"app_fetcher_exception: {e!r}")
            return None, None, str(e)

    def _fetch_playwright(
        self, url: str, out_dir: Path, capture_screenshot: bool = True
    ) -> tuple[Optional[str], Optional[int], Optional[str], bool]:
        """
        Fetch via real Chromium so JS-rendered article bodies materialize.
        Captures a full-page screenshot in the same browser session.
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return None, None, "playwright_missing", False

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(args=["--disable-blink-features=AutomationControlled"])
                context = browser.new_context(
                    viewport=PLAYWRIGHT_VIEWPORT,
                    user_agent=USER_AGENT,
                    locale="en-US",
                )
                page = context.new_page()
                response = page.goto(url, timeout=PLAYWRIGHT_TIMEOUT_MS, wait_until="domcontentloaded")
                # Best-effort: let JS settle. networkidle can hang forever on some sites.
                try:
                    page.wait_for_load_state("networkidle", timeout=8_000)
                except Exception:
                    pass
                # Best-effort: dismiss obvious cookie/popup overlays.
                self._dismiss_overlays(page)
                # Trigger lazy-loaded body content: scroll through, wait for paragraphs to stabilize.
                self._wait_for_article_body(page)

                html = page.content()
                status = response.status if response else None
                screenshot_ok = False
                if capture_screenshot:
                    try:
                        page.screenshot(path=str(out_dir / "screenshot.png"), full_page=True)
                        screenshot_ok = True
                    except Exception:
                        pass

                browser.close()
                return html, status, None, screenshot_ok
        except Exception as e:  # noqa: BLE001
            return None, None, str(e), False

    def _wait_for_article_body(self, page) -> None:
        """
        Scroll to trigger lazy-loaders, then wait until the paragraph count stabilizes.

        Globo, NYT, WaPo and many others lazy-render the body — `domcontentloaded` and even
        `networkidle` can return before the article paragraphs are mounted. We poll
        `<article> p` (and the page-wide `p` count as a fallback) until two consecutive
        readings match, capping at ~12s total.
        """
        try:
            # Force lazy loaders by scrolling progressively to bottom and back to top.
            page.evaluate(
                """async () => {
                    await new Promise(resolve => {
                        let y = 0;
                        const step = window.innerHeight;
                        const timer = setInterval(() => {
                            window.scrollBy(0, step);
                            y += step;
                            if (y >= document.body.scrollHeight) {
                                clearInterval(timer);
                                window.scrollTo(0, 0);
                                resolve();
                            }
                        }, 120);
                    });
                }"""
            )
        except Exception:
            pass

        last = -1
        stable_for = 0
        for _ in range(12):  # ~12 * 1s = 12s budget
            try:
                count = page.evaluate(
                    "() => document.querySelectorAll('article p, [data-component=\"paragraph\"], "
                    "main p, [itemprop=\"articleBody\"] p').length || document.querySelectorAll('p').length"
                )
            except Exception:
                count = 0
            if count == last and count >= 3:
                stable_for += 1
                if stable_for >= 1:  # one stable reading after a non-zero count
                    return
            else:
                stable_for = 0
            last = count
            page.wait_for_timeout(1_000)

    def _dismiss_overlays(self, page) -> None:
        # Cheap, generic attempts. Per-publisher selectors can be added later.
        candidates = [
            'button:has-text("Accept")', 'button:has-text("Aceitar")',
            'button:has-text("I agree")', 'button:has-text("Concordo")',
            'button:has-text("Got it")', '[aria-label="Close"]',
            'button[aria-label="Fechar"]',
        ]
        for sel in candidates:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=500):
                    el.click(timeout=1_000)
            except Exception:
                continue

    def _extract_readability(self, html: str, url: str, notes: list) -> str:
        try:
            from readability import Document
            from bs4 import BeautifulSoup

            doc = Document(html, url=url)
            summary_html = doc.summary(html_partial=True)
            text = BeautifulSoup(summary_html, "lxml").get_text(separator="\n").strip()
            return _normalize_whitespace(text)
        except Exception as e:  # noqa: BLE001
            notes.append(f"readability_failed: {e!r}")
            return ""

    def _extract_newspaper(self, html: str, url: str, notes: list) -> str:
        try:
            from newspaper import Article

            article = Article(url=url, language="pt" if "globo.com" in url else "en")
            article.download(input_html=html)
            article.parse()
            return _normalize_whitespace(article.text or "")
        except Exception as e:  # noqa: BLE001
            notes.append(f"newspaper_failed: {e!r}")
            return ""

    def _extract_via_selectors(self, html: str, url: str, notes: list) -> tuple[str, Optional[str]]:
        """
        Try per-publisher CSS selectors (and generic fallbacks) on the rendered HTML.
        Returns (extracted_text, selector_used). Picks the first selector that yields
        >=80 words of clean text.
        """
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            notes.append("bs4_missing")
            return "", None

        soup = BeautifulSoup(html, "lxml")

        domain_selectors: list[str] = []
        for domain_pat, sels in PUBLISHER_SELECTORS.items():
            if domain_pat in url:
                domain_selectors = list(sels)
                break

        # Try domain-specific selectors first, then generic fallbacks.
        for sel in domain_selectors + GENERIC_SELECTORS:
            try:
                nodes = soup.select(sel)
            except Exception:
                continue
            if not nodes:
                continue
            # For multi-node selectors that target paragraphs (e.g. p.content-text__container),
            # join all node texts. For single-element selectors (article, main), take just
            # the first to avoid concatenating multiple stories.
            if any(tag in sel.lower() for tag in (" p", "p.", "p[", "p:", "[itemprop")):
                pieces = [n.get_text(" ", strip=True) for n in nodes]
            else:
                pieces = [nodes[0].get_text(" ", strip=True)]
            text = _strip_chrome("\n\n".join(p for p in pieces if p))
            if len(text.split()) >= 80:
                return text, sel
        return "", None

    def _classify_page(self, screenshot_path: Path, notes: list) -> tuple[str, float]:
        """
        Vision-LLM CLASSIFIER (not a text source). Returns (page_class, cost_usd).
        page_class ∈ {ARTICLE_PAGE, PAYWALL_OR_BLOCK_PAGE, SKELETON_LOAD, unknown}
        """
        try:
            from openai import OpenAI
        except ImportError:
            notes.append("openai_lib_missing")
            return "unknown", 0.0

        try:
            png_bytes = screenshot_path.read_bytes()
            data_url = f"data:image/png;base64,{base64.b64encode(png_bytes).decode('ascii')}"
            client = OpenAI()
            resp = client.chat.completions.create(
                model=VISION_MODEL,
                max_tokens=VISION_MAX_TOKENS,
                temperature=0.0,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": VISION_PROMPT},
                            {"type": "image_url", "image_url": {"url": data_url, "detail": "low"}},
                        ],
                    }
                ],
            )
            answer = (resp.choices[0].message.content or "").strip().upper()
            usage = resp.usage
            cost = (
                usage.prompt_tokens * VISION_PROMPT_COST_PER_TOKEN
                + usage.completion_tokens * VISION_COMPLETION_COST_PER_TOKEN
            )
            for label in ("ARTICLE_PAGE", "PAYWALL_OR_BLOCK_PAGE", "SKELETON_LOAD"):
                if label in answer:
                    return label, cost
            notes.append(f"vision_classify_unparseable: {answer[:80]!r}")
            return "unknown", cost
        except Exception as e:  # noqa: BLE001
            notes.append(f"vision_classify_failed: {e!r}")
            return "unknown", 0.0

    # ------------------------------------------------------------- agreement

    def _compute_agreement(self, a: str, b: str) -> tuple[float, float]:
        if not a or not b:
            return 0.0, 0.0
        char_ratio = min(len(a), len(b)) / max(len(a), len(b))
        a_tokens, b_tokens = set(a.lower().split()), set(b.lower().split())
        if not a_tokens or not b_tokens:
            return char_ratio, 0.0
        jaccard = len(a_tokens & b_tokens) / len(a_tokens | b_tokens)
        return char_ratio, jaccard

    def _pick_primary(
        self, selector: str, readability: str, newspaper: str, page_class: str
    ) -> tuple[str, str]:
        """
        Pick the most trustworthy ground-truth text.

        Priority:
          1. Page is paywall/skeleton → no ground truth ("")
          2. Selector extraction is substantial → use it (deterministic, publisher-specific)
          3. Fall back to whichever HTML extractor produced more text
        """
        if page_class in ("PAYWALL_OR_BLOCK_PAGE", "SKELETON_LOAD"):
            return "", "none"
        if len(selector.split()) >= 80:
            return selector, "selector"
        if len(readability.split()) >= len(newspaper.split()) and readability:
            return readability, "readability"
        if newspaper:
            return newspaper, "newspaper"
        return "", "none"

    def _three_way_confidence(
        self, selector: str, readability: str, newspaper: str, page_class: str
    ) -> tuple[float, float, str]:
        """
        Confidence comes from the best agreement among any pair that both produced text.
        Selector↔readability agreement is the strongest signal — both are looking at the
        same DOM via different heuristics, so when they agree, ground truth is solid.
        """
        if page_class in ("PAYWALL_OR_BLOCK_PAGE", "SKELETON_LOAD"):
            return 0.0, 0.0, "failed"

        pairs = []
        if selector and readability:
            pairs.append(self._compute_agreement(selector, readability))
        if selector and newspaper:
            pairs.append(self._compute_agreement(selector, newspaper))
        if readability and newspaper:
            pairs.append(self._compute_agreement(readability, newspaper))

        char_ratio, jaccard = max(pairs, key=lambda p: p[1]) if pairs else (0.0, 0.0)

        # Selector-led confidence: when the publisher-specific selector returns substantial
        # text AND the vision classifier confirmed an article page, we trust the selector
        # output regardless of agreement with the noisy generic extractors. Spot-checked:
        # Globo's `p.content-text__container` and BBC's `<article>` produce verbatim ground
        # truth even when readability picks the wrong block.
        selector_wc = len(selector.split())
        if page_class == "ARTICLE_PAGE" and selector_wc >= 200:
            return char_ratio, jaccard, "high"
        if page_class == "ARTICLE_PAGE" and selector_wc >= 80:
            return char_ratio, jaccard, "medium"

        # No selector hit — fall back to readability/newspaper3k agreement.
        if not pairs:
            return 0.0, 0.0, "failed"
        if jaccard >= 0.70 and char_ratio >= 0.65:
            return char_ratio, jaccard, "high"
        if jaccard >= 0.45 and char_ratio >= 0.45:
            return char_ratio, jaccard, "medium"
        return char_ratio, jaccard, "low"

    # ----------------------------------------------------------------- output

    def _write_summary(self, results: list[CaptureResult]) -> None:
        """
        Write summary.json by MERGING this run's results with prior runs (keyed by
        article_id, latest wins). Avoids overwriting the global view when only a
        subset of articles is processed.
        """
        summary_path = GOLDEN_DIR / "summary.json"
        prior_by_id: dict[int, dict] = {}
        if summary_path.exists():
            try:
                prior = json.loads(summary_path.read_text(encoding="utf-8"))
                for r in prior.get("results", []):
                    prior_by_id[r["article_id"]] = r
            except Exception:  # noqa: BLE001
                prior_by_id = {}

        # Latest run wins for any overlapping IDs.
        for r in results:
            prior_by_id[r.article_id] = asdict(r)

        merged = list(prior_by_id.values())

        # Reconstruct grouped counts from the merged view.
        def _count(key):
            out: dict = {}
            for r in merged:
                out[r.get(key)] = out.get(r.get(key), 0) + 1
            return out

        summary = {
            "total": len(merged),
            "by_confidence": _count("confidence"),
            "by_stratum": _count("stratum"),
            "by_source": _count("source"),
            "results": merged,
        }
        summary_path.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        self.stdout.write("\n=== Summary ===")
        self.stdout.write(f"  total      : {summary['total']}")
        for k, v in sorted(summary["by_confidence"].items()):
            self.stdout.write(f"  {k:11s}: {v}")
        self.stdout.write(f"  written to : {summary_path}")

    # -------------------------------------------------------- reference seeds

    def _seed_reference_examples(self, results: list[CaptureResult]) -> None:
        """Insert/update quality_reference_examples rows for confident captures."""
        from apps.articles.models import Article
        from apps.content.quality.models import ReferenceQualityExample

        seeded = 0
        for r in results:
            if r.confidence not in ("high", "medium"):
                continue
            try:
                article = Article.objects.get(id=r.article_id)
            except Article.DoesNotExist:
                self.stdout.write(f"  skip {r.article_id}: not in articles_article")
                continue

            quality_class = self._infer_quality_class(r)
            ref, created = ReferenceQualityExample.objects.update_or_create(
                article=article,
                defaults={
                    "quality_class": quality_class,
                    "reference_overall_score": _confidence_to_score(r.confidence),
                    "reference_completeness": 1.0 if r.confidence == "high" else 0.7,
                    "reference_purity": 1.0 if r.confidence == "high" else 0.7,
                    "reference_structure": 0.8,
                    "reference_readability": 0.8,
                    "use_for_calibration": True,
                    "use_for_benchmarking": True,
                    "use_in_prompts": False,
                },
            )
            seeded += 1
            tag = "created" if created else "updated"
            self.stdout.write(f"  {tag} ReferenceQualityExample for article {article.id} ({quality_class})")

        self.stdout.write(f"\n📌 Seeded/updated {seeded} reference example(s).")

    def _infer_quality_class(self, r: CaptureResult) -> str:
        # Map our capture confidence onto ReferenceQualityExample.QualityClass
        # (perfect / good / imperfect / awful)
        if r.confidence == "high" and r.readability_words >= 200:
            return "perfect"
        if r.confidence == "high":
            return "good"
        if r.confidence == "medium":
            return "imperfect"
        return "awful"

    # ----------------------------------------------------------------- helpers

    def _load_candidates(self, path: str) -> list[dict]:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return data.get("candidates", [])


# ---------------------------------------------------------------- module utils


def _normalize_whitespace(text: str) -> str:
    lines = [ln.strip() for ln in (text or "").splitlines()]
    return "\n".join(ln for ln in lines if ln)


def _strip_chrome(text: str) -> str:
    """Strip lines that are pure UI chrome (Share/Save/Subscribe/Read more/etc.)."""
    if not text:
        return ""
    keep = []
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        # If a line is short and matches a chrome phrase, drop it.
        if len(ln) < 60 and any(tok.lower() == ln.lower() or ln.lower().startswith(tok.lower() + " ")
                                for tok in CHROME_TOKENS):
            continue
        keep.append(ln)
    return "\n".join(keep)


def _count_by(results, key):
    out: dict = {}
    for r in results:
        out[key(r)] = out.get(key(r), 0) + 1
    return out


def _confidence_to_score(c: str) -> float:
    return {"high": 0.9, "medium": 0.7, "low": 0.4, "failed": 0.0}.get(c, 0.0)


def _utcnow_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
