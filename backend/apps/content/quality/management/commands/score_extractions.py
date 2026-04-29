"""
Score the production extraction routes against the golden ground-truth dataset.

For each article in the golden set:
  1. Pulls the article's stored `raw_html` from the database (what prod actually processes)
  2. Runs each requested extraction route (algo / ai / hybrid) on that HTML
  3. Scores the extracted text against `ground_truth.txt` (selector-based publisher canonical)

Metrics per (article, route):
  - token_f1            : unigram precision/recall F1 on lowercased tokens
  - jaccard             : set-based token overlap
  - char_length_ratio   : len(extracted) / len(ground_truth)  (>>1 = noise, <<1 = truncation)
  - missing_paragraphs  : count of ground-truth paragraphs without a fuzzy match in extraction
  - noise_paragraphs    : count of extraction paragraphs without a fuzzy match in ground truth
  - cost_usd            : LLM cost (algo=0)
  - duration_ms         : wall-clock time
  - verdict             : "good" (token_f1 >= .80 & missing<=1) | "partial" | "bad"

Aggregate report breaks down per route: median F1, % good, total cost on the dataset.
"""

import json
import logging
import statistics
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

GOLDEN_DIR = (
    Path(__file__).resolve().parents[2] / "fixtures" / "golden"
)
DEFAULT_ROUTES = ["algo", "ai", "hybrid"]
DEFAULT_MIN_CONFIDENCE = "medium"      # high | medium | low | failed
PARAGRAPH_FUZZ_THRESHOLD = 0.55         # token-Jaccard between two paragraphs to count as "match"
GOOD_F1 = 0.80
GOOD_MISSING_MAX = 1
PARTIAL_F1 = 0.55


@dataclass
class RouteScore:
    article_id: int
    route: str
    success: bool
    extracted_words: int
    ground_truth_words: int
    token_f1: float
    token_precision: float
    token_recall: float
    jaccard: float
    char_length_ratio: float
    missing_paragraphs: int
    noise_paragraphs: int
    matched_paragraphs: int
    quality_score: float                 # extractor's self-reported score (0–1)
    cost_usd: float
    duration_ms: int
    verdict: str
    error: Optional[str] = None
    notes: list = field(default_factory=list)


class Command(BaseCommand):
    help = "Score production extraction routes (algo/ai/hybrid) against the golden dataset."

    def add_arguments(self, parser):
        parser.add_argument(
            "--routes", nargs="+", default=DEFAULT_ROUTES,
            choices=["algo", "ai", "hybrid"],
            help="Which extraction routes to score (default: all three).",
        )
        parser.add_argument(
            "--article-ids", nargs="+", type=int, default=None,
            help="Restrict to specific article IDs.",
        )
        parser.add_argument(
            "--min-confidence", default=DEFAULT_MIN_CONFIDENCE,
            choices=["high", "medium", "low"],
            help="Minimum ground-truth confidence to include (default: medium).",
        )
        parser.add_argument(
            "--use-fixture-html", action="store_true",
            help="Use the freshly-fetched publisher.html from the fixture instead of "
                 "the article's stored raw_html. Default uses stored raw_html — that's "
                 "what production actually processes.",
        )
        parser.add_argument(
            "--out", type=str,
            default=str(GOLDEN_DIR / "scoring_report.json"),
            help="Where to write the per-article + aggregate report.",
        )
        parser.add_argument(
            "--max-articles", type=int, default=None,
            help="Cap on number of articles to score (smoke tests).",
        )

    # ------------------------------------------------------------------ runner

    def handle(self, *args, **options):
        targets = self._select_targets(options)
        if not targets:
            self.stderr.write("No articles match the selection.")
            return

        self.stdout.write(
            f"📊 Scoring {len(targets)} article(s) on routes: {', '.join(options['routes'])}\n"
        )

        all_scores: list[RouteScore] = []
        for fixture in targets:
            article_id = fixture["article_id"]
            ground_truth = self._load_ground_truth(article_id)
            if not ground_truth:
                self.stdout.write(f"  · {article_id} skipped — no ground truth")
                continue

            html, url, title, paywall = self._load_article_input(article_id, options)
            if not html:
                self.stdout.write(f"  · {article_id} skipped — no html available")
                continue

            self.stdout.write(f"  → {article_id} ({fixture['source']}, gt={len(ground_truth.split())}w)")
            for route in options["routes"]:
                score = self._score_route(
                    route=route, article_id=article_id, html=html, url=url,
                    title=title, paywall=paywall, ground_truth=ground_truth,
                )
                all_scores.append(score)
                self.stdout.write(
                    f"      {route:6s} f1={score.token_f1:.2f} "
                    f"len_ratio={score.char_length_ratio:.2f} "
                    f"miss={score.missing_paragraphs} noise={score.noise_paragraphs} "
                    f"cost=${score.cost_usd:.4f} verdict={score.verdict}"
                )

        report = self._build_report(all_scores, options)
        Path(options["out"]).write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        self._print_aggregate(report)

    # ------------------------------------------------------------------ inputs

    def _select_targets(self, options: dict) -> list[dict]:
        """
        Walk every per-article fixture directory under GOLDEN_DIR and pull its
        metadata.json. We deliberately don't trust summary.json (overwritten by
        each build run) — per-article files are the durable source of truth.
        """
        confidence_order = ["high", "medium", "low", "failed"]
        min_idx = confidence_order.index(options["min_confidence"])

        kept: list[dict] = []
        for child in sorted(GOLDEN_DIR.iterdir()):
            if not child.is_dir():
                continue
            meta_path = child / "metadata.json"
            if not meta_path.exists():
                continue
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                continue
            result = meta.get("result", {})
            conf = result.get("confidence", "failed")
            if conf not in confidence_order:
                continue
            if confidence_order.index(conf) > min_idx:
                continue
            # Include the candidate's source/url for output, alongside the result.
            kept.append({
                "article_id": result["article_id"],
                "source": result.get("source") or meta.get("candidate", {}).get("source"),
                "stratum": result.get("stratum"),
                "confidence": conf,
                "url": result.get("url") or meta.get("candidate", {}).get("url"),
            })
        if options["article_ids"]:
            wanted = set(options["article_ids"])
            kept = [r for r in kept if r["article_id"] in wanted]
        if options["max_articles"]:
            kept = kept[: options["max_articles"]]
        return kept

    def _load_ground_truth(self, article_id: int) -> str:
        gt_path = GOLDEN_DIR / str(article_id) / "ground_truth.txt"
        if not gt_path.exists():
            return ""
        return gt_path.read_text(encoding="utf-8").strip()

    def _load_article_input(
        self, article_id: int, options: dict
    ) -> tuple[Optional[str], Optional[str], Optional[str], bool]:
        """Return (raw_html, url, title, paywall_detected)."""
        if options["use_fixture_html"]:
            html_path = GOLDEN_DIR / str(article_id) / "publisher.html"
            html = html_path.read_text(encoding="utf-8") if html_path.exists() else None
            meta_path = GOLDEN_DIR / str(article_id) / "metadata.json"
            meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
            cand = meta.get("candidate", {})
            return html, cand.get("url"), None, bool(cand.get("paywall"))

        # Default: load from production DB. This is what prod processing actually sees.
        from apps.articles.models import Article
        try:
            a = Article.objects.get(id=article_id)
        except Article.DoesNotExist:
            return None, None, None, False
        return a.raw_html, a.url, a.title, bool(a.paywall_detected)

    # ------------------------------------------------------------------- routes

    def _score_route(
        self, route: str, article_id: int, html: str, url: str,
        title: Optional[str], paywall: bool, ground_truth: str,
    ) -> RouteScore:
        start = time.time()
        try:
            if route == "algo":
                extracted, quality, cost, blocks_n, success, err = self._run_algo(html, url)
            elif route == "ai":
                extracted, quality, cost, blocks_n, success, err = self._run_ai(html, url, title)
            elif route == "hybrid":
                extracted, quality, cost, blocks_n, success, err = self._run_hybrid(
                    html, url, title, paywall
                )
            else:
                return self._make_score(article_id, route, "", ground_truth, 0, 0, False,
                                        f"unknown route {route}", 0)
        except Exception as e:  # noqa: BLE001
            logger.exception("route %s failed for %s", route, article_id)
            return self._make_score(article_id, route, "", ground_truth, 0, 0, False, repr(e), 0)

        duration_ms = int((time.time() - start) * 1000)
        return self._make_score(
            article_id, route, extracted, ground_truth, quality, cost, success, err, duration_ms
        )

    def _run_algo(self, html: str, url: Optional[str]):
        from apps.content.processor.algorithmic_processor import AlgorithmicProcessor
        proc = AlgorithmicProcessor()
        result = proc.process_content(html, {"url": url})
        text = result.clean_content or ""
        return (
            text, float(getattr(result, "quality_score", 0.0)), 0.0,
            len(getattr(result, "content_blocks", []) or []),
            bool(result.success), getattr(result, "error_message", None),
        )

    def _run_ai(self, html: str, url: Optional[str], title: Optional[str]):
        from apps.content.processor.ai_processor import AIContentProcessor
        proc = AIContentProcessor()
        meta = {"url": url, "title": title or ""}
        result = proc.process_content(html, meta, base_url=url)
        text = result.clean_content or ""
        # AI processor stashes cost inside extracted_metadata, not as a top-level field.
        em = result.extracted_metadata or {}
        cost = float(em.get("estimated_cost_usd") or em.get("total_cost") or 0.0)
        return (
            text, float(getattr(result, "quality_score", 0.0)), cost,
            len(getattr(result, "content_blocks", []) or []),
            bool(result.success), getattr(result, "error_message", None),
        )

    def _run_hybrid(self, html: str, url: Optional[str], title: Optional[str], paywall: bool):
        """
        True hybrid: HybridPreprocessor (subtractive HTML cleaner) → HybridExtractor
        (LLM on cleaner input, no internal AI preprocessing).

        Earlier this method ran a "decision-rule hybrid" that almost never
        escalated because algo's self-rated quality_score is uncalibrated. The
        new path always runs preprocessor + extractor — the cost saving comes
        from the smaller LLM input, not from skipping the LLM call.
        """
        from apps.content.processor.hybrid import HybridProcessor
        proc = HybridProcessor()
        meta = {"url": url, "title": title or ""}
        result = proc.process_content(html, meta, base_url=url)

        text = result.clean_content or ""
        em = result.extracted_metadata or {}
        cost = float(em.get("estimated_cost_usd") or em.get("total_cost") or 0.0)
        return (
            text, float(getattr(result, "quality_score", 0.0)), cost,
            len(getattr(result, "content_blocks", []) or []),
            bool(result.success), getattr(result, "error_message", None),
        )

    # -------------------------------------------------------------- scoring

    def _make_score(
        self, article_id: int, route: str, extracted: str, ground_truth: str,
        quality: float, cost: float, success: bool, err: Optional[str], duration_ms: int,
    ) -> RouteScore:
        gt_words = len(ground_truth.split())
        ext_words = len(extracted.split())

        f1, prec, rec = self._token_f1(extracted, ground_truth)
        jacc = self._jaccard(extracted, ground_truth)
        len_ratio = (len(extracted) / len(ground_truth)) if ground_truth else 0.0
        missing, noise, matched = self._paragraph_diff(extracted, ground_truth)

        verdict = self._classify(f1, missing, success)

        return RouteScore(
            article_id=article_id, route=route, success=success,
            extracted_words=ext_words, ground_truth_words=gt_words,
            token_f1=round(f1, 3), token_precision=round(prec, 3), token_recall=round(rec, 3),
            jaccard=round(jacc, 3), char_length_ratio=round(len_ratio, 3),
            missing_paragraphs=missing, noise_paragraphs=noise, matched_paragraphs=matched,
            quality_score=round(quality, 3),
            cost_usd=round(cost, 5), duration_ms=duration_ms,
            verdict=verdict, error=err,
        )

    @staticmethod
    def _tokens(text: str) -> list[str]:
        # Cheap tokenizer: lower + split on non-word chars; drops 1-char tokens.
        import re
        return [t for t in re.findall(r"\w+", (text or "").lower()) if len(t) > 1]

    def _token_f1(self, a: str, b: str) -> tuple[float, float, float]:
        ta, tb = self._tokens(a), self._tokens(b)
        if not ta or not tb:
            return 0.0, 0.0, 0.0
        from collections import Counter
        ca, cb = Counter(ta), Counter(tb)
        overlap = sum((ca & cb).values())
        if overlap == 0:
            return 0.0, 0.0, 0.0
        prec = overlap / len(ta)
        rec = overlap / len(tb)
        f1 = 2 * prec * rec / (prec + rec)
        return f1, prec, rec

    def _jaccard(self, a: str, b: str) -> float:
        sa, sb = set(self._tokens(a)), set(self._tokens(b))
        if not sa or not sb:
            return 0.0
        return len(sa & sb) / len(sa | sb)

    def _paragraph_diff(self, extracted: str, ground_truth: str) -> tuple[int, int, int]:
        """
        Split both into paragraphs (blank-line separated, plus single-newline fallback).
        Fuzzy-match each ground-truth paragraph to the closest extraction paragraph by
        token-Jaccard. Count missing (gt without match) + noise (extraction without match).
        """
        def paragraphs(text: str) -> list[str]:
            parts = [p.strip() for p in (text or "").split("\n\n") if p.strip()]
            if len(parts) <= 1:
                parts = [p.strip() for p in (text or "").splitlines() if p.strip()]
            # Drop 1-line fragments shorter than ~10 words — too noisy for matching.
            return [p for p in parts if len(p.split()) >= 10]

        gt_paras = paragraphs(ground_truth)
        ext_paras = paragraphs(extracted)
        if not gt_paras:
            return 0, len(ext_paras), 0

        def jac(a: str, b: str) -> float:
            sa, sb = set(self._tokens(a)), set(self._tokens(b))
            if not sa or not sb:
                return 0.0
            return len(sa & sb) / len(sa | sb)

        matched_gt: set[int] = set()
        matched_ext: set[int] = set()
        for i, gp in enumerate(gt_paras):
            best_j, best_v = -1, 0.0
            for j, ep in enumerate(ext_paras):
                if j in matched_ext:
                    continue
                v = jac(gp, ep)
                if v > best_v:
                    best_v, best_j = v, j
            if best_j >= 0 and best_v >= PARAGRAPH_FUZZ_THRESHOLD:
                matched_gt.add(i)
                matched_ext.add(best_j)

        missing = len(gt_paras) - len(matched_gt)
        noise = len(ext_paras) - len(matched_ext)
        return missing, noise, len(matched_gt)

    @staticmethod
    def _classify(f1: float, missing: int, success: bool) -> str:
        if not success:
            return "failed"
        if f1 >= GOOD_F1 and missing <= GOOD_MISSING_MAX:
            return "good"
        if f1 >= PARTIAL_F1:
            return "partial"
        return "bad"

    # ------------------------------------------------------------------- report

    def _build_report(self, scores: list[RouteScore], options: dict) -> dict:
        per_article = [asdict(s) for s in scores]
        by_route: dict[str, list[RouteScore]] = {}
        for s in scores:
            by_route.setdefault(s.route, []).append(s)

        aggregate = {}
        for route, rows in by_route.items():
            f1s = [r.token_f1 for r in rows if r.success]
            costs = [r.cost_usd for r in rows]
            verdicts = [r.verdict for r in rows]
            aggregate[route] = {
                "n": len(rows),
                "n_success": sum(1 for r in rows if r.success),
                "median_f1": round(statistics.median(f1s), 3) if f1s else 0.0,
                "mean_f1": round(statistics.mean(f1s), 3) if f1s else 0.0,
                "min_f1": round(min(f1s), 3) if f1s else 0.0,
                "pct_good": round(sum(1 for v in verdicts if v == "good") / len(verdicts) * 100, 1)
                            if verdicts else 0.0,
                "pct_partial": round(sum(1 for v in verdicts if v == "partial") / len(verdicts) * 100, 1)
                               if verdicts else 0.0,
                "pct_bad_or_failed": round(
                    sum(1 for v in verdicts if v in ("bad", "failed")) / len(verdicts) * 100, 1
                ) if verdicts else 0.0,
                "total_cost_usd": round(sum(costs), 4),
                "median_missing_paragraphs": round(statistics.median(
                    [r.missing_paragraphs for r in rows]), 1) if rows else 0,
                "median_noise_paragraphs": round(statistics.median(
                    [r.noise_paragraphs for r in rows]), 1) if rows else 0,
            }

        return {
            "options": {k: v for k, v in options.items() if k != "out"},
            "aggregate": aggregate,
            "per_article": per_article,
        }

    def _print_aggregate(self, report: dict) -> None:
        agg = report["aggregate"]
        self.stdout.write("\n=== Aggregate ===")
        header = f"  {'route':8s} {'n':>3s} {'med_f1':>7s} {'mean_f1':>8s} " \
                 f"{'%good':>6s} {'%part':>6s} {'%bad':>6s} {'$total':>8s} " \
                 f"{'med_miss':>9s} {'med_noise':>10s}"
        self.stdout.write(header)
        for route, m in agg.items():
            self.stdout.write(
                f"  {route:8s} {m['n']:>3d} {m['median_f1']:>7.2f} {m['mean_f1']:>8.2f} "
                f"{m['pct_good']:>5.1f}% {m['pct_partial']:>5.1f}% {m['pct_bad_or_failed']:>5.1f}% "
                f"${m['total_cost_usd']:>7.4f} {m['median_missing_paragraphs']:>9.1f} "
                f"{m['median_noise_paragraphs']:>10.1f}"
            )
        self.stdout.write(f"\n  report → {report['options'].get('out', GOLDEN_DIR / 'scoring_report.json')}")
