"""
HybridPreprocessor -- subtractive HTML cleaner for the hybrid pipeline.

Removes obvious non-content (scripts, nav, ads, related-cards, popups, comments).
Does NOT:
  - pick "the article element" (that's the LLM's job downstream)
  - extract text or build content blocks (also the LLM's job)
  - score elements (no Safari Reader Mode heuristics here)

Returns a PreprocessResult with the cleaned HTML + size stats so we can measure
how much we shrank the LLM input.

Pattern reuse: NEGATIVE_PATTERNS / VERY_NEGATIVE_PATTERNS / REMOVE_TAGS are
copy-pasted from AlgorithmicProcessor (lines 67–86) so the two paths share the
same notion of "obvious non-content" without coupling the modules.
"""

from __future__ import annotations

import html as html_module
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Comment

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------- patterns
# Mirrors AlgorithmicProcessor (algorithmic_processor.py:67-86). Kept verbatim
# so updates in either place are easy to diff. A future refactor could lift
# these to a shared constants module -- leaving them duplicated for now to keep
# the three paths textually independent.

NEGATIVE_PATTERNS = re.compile(
    r"advertisement|breadcrumb|combx|comment|contact|disqus|footer|"
    r"mod-conversations|promo|related|scroll|share|shoutbox|sidebar|social|"
    r"sponsor|subscribe|tags|toolbox|widget|_ad$|navigation|nav-|menu-|"
    r"newsletter|popup|paywall|cookie|gdpr|consent|recirc|recommended|"
    r"trending|read-more|read-next|read-also|hide-on-print",
    re.IGNORECASE,
)

# Patterns whose match means "definitely not article body". Stricter than
# NEGATIVE_PATTERNS -- we delete on match without further checks.
VERY_NEGATIVE_PATTERNS = re.compile(
    r"instapaper_ignore|skip-to-content|visually-hidden|sr-only",
    re.IGNORECASE,
)

# Tags removed wholesale -- never article content.
REMOVE_TAGS = {
    "script", "style", "noscript", "link", "meta", "template",
    "iframe", "object", "embed", "form", "input", "button", "select",
    "textarea", "label", "fieldset",
    "nav", "header", "footer", "aside",
    "svg",
}

# Tags KEPT regardless of what NEGATIVE_PATTERNS says about their class/id.
# Anything inside these is structural article content the LLM needs to see.
PROTECTED_TAGS = {"article", "main"}

# Attributes worth keeping on surviving elements. Everything else is dropped.
KEEP_ATTRS = {"href", "src", "srcset", "alt", "title", "id", "class", "datetime", "cite"}

# Link-density above this fraction → the element is mostly link-list (related,
# nav, footer-of-links). Stricter than algo's 0.5 because the preprocessor is
# more conservative -- we'd rather keep an ambiguous block than drop content.
HIGH_LINK_DENSITY = 0.6
MIN_TEXT_FOR_LINK_DENSITY_CHECK = 60   # below this many chars, link density is noisy

# Wrappers shorter than this are likely empty placeholders / chrome.
MIN_TEXT_LEN_FOR_DIV_OR_SPAN = 25


# ------------------------------------------------------------------- result type


@dataclass
class PreprocessResult:
    """Output of HybridPreprocessor.preprocess()."""
    success: bool
    cleaned_html: str = ""
    error_message: str = ""

    original_size_bytes: int = 0
    cleaned_size_bytes: int = 0
    size_reduction_pct: float = 0.0

    elements_removed: int = 0
    counts_by_reason: dict = field(default_factory=dict)
    processing_time_ms: int = 0

    def __post_init__(self):
        if self.original_size_bytes:
            self.size_reduction_pct = round(
                100.0 * (1.0 - self.cleaned_size_bytes / self.original_size_bytes), 2
            )


# -------------------------------------------------------------------- preprocessor


class HybridPreprocessor:
    """
    Subtractive HTML cleaner. Strips clearly non-content elements while keeping
    everything plausibly article-related. The downstream LLM extractor will do
    the finer "what's actually the article body" decision.
    """

    def __init__(self, link_density_threshold: float = HIGH_LINK_DENSITY):
        self._link_density = link_density_threshold

    # ------------------------------------------------------------- public API

    def preprocess(
        self, raw_html: str, base_url: Optional[str] = None
    ) -> PreprocessResult:
        start = time.time()
        if not raw_html or len(raw_html) < 100:
            return PreprocessResult(
                success=False,
                error_message="raw_html too small (<100 chars)",
                original_size_bytes=len(raw_html or ""),
                processing_time_ms=int((time.time() - start) * 1000),
            )

        try:
            decoded = self._decode(raw_html)
            soup = BeautifulSoup(decoded, "html.parser")
            counts = {
                "removed_tag": 0,
                "removed_comment": 0,
                "removed_negative_pattern": 0,
                "removed_very_negative_pattern": 0,
                "removed_high_link_density": 0,
                "removed_empty_wrapper": 0,
                "attr_stripped": 0,
                "url_resolved": 0,
            }

            # Operate on the body if there is one -- otherwise the whole tree.
            scope = soup.body if soup.body else soup

            self._remove_unwanted_tags(scope, counts)
            self._remove_html_comments(scope, counts)
            self._remove_by_negative_patterns(scope, counts)
            self._remove_high_link_density(scope, counts)
            self._remove_empty_wrappers(scope, counts)
            self._strip_attributes(scope, counts)
            if base_url:
                self._resolve_urls(scope, base_url, counts)

            cleaned_html = str(scope)
            elements_removed = sum(v for k, v in counts.items() if k.startswith("removed_"))

            return PreprocessResult(
                success=True,
                cleaned_html=cleaned_html,
                original_size_bytes=len(raw_html),
                cleaned_size_bytes=len(cleaned_html),
                elements_removed=elements_removed,
                counts_by_reason=counts,
                processing_time_ms=int((time.time() - start) * 1000),
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("HybridPreprocessor failed")
            return PreprocessResult(
                success=False,
                error_message=f"preprocessing_error: {exc!r}",
                original_size_bytes=len(raw_html),
                processing_time_ms=int((time.time() - start) * 1000),
            )

    # ------------------------------------------------------------- pipeline steps

    def _decode(self, raw: str) -> str:
        """
        Decode HTML entities + Unicode escapes the way Algorithmic does
        (algorithmic_processor.py:137-145). Many publishers ship JSON-stringified
        HTML inside script tags; this normalises both forms.
        """
        decoded = html_module.unescape(raw)
        # Some publishers ship HTML inside JSON-stringified payloads — undo the
        # common Unicode and backslash escapes so BeautifulSoup sees real markup.
        replacements = [
            ("\\u003c", "<"), ("\\u003e", ">"), ("\\u0026", "&"),
            ("\\u002F", "/"), ("\\u0027", "'"), ("\\u0022", '"'),
            ("\\\"", '"'), ("\\/", "/"),
        ]
        for needle, repl in replacements:
            if needle in decoded:
                decoded = decoded.replace(needle, repl)
        return decoded

    def _remove_unwanted_tags(self, scope, counts: dict) -> None:
        for tag_name in REMOVE_TAGS:
            for el in scope.find_all(tag_name):
                el.decompose()
                counts["removed_tag"] += 1

    def _remove_html_comments(self, scope, counts: dict) -> None:
        for c in scope.find_all(string=lambda s: isinstance(s, Comment)):
            c.extract()
            counts["removed_comment"] += 1

    def _remove_by_negative_patterns(self, scope, counts: dict) -> None:
        """
        Remove elements whose class/id matches the noise patterns.

        Heuristic guards (kept conservative -- false positives would drop real content):
          - Don't drop PROTECTED_TAGS (article/main) regardless of class.
          - Don't drop elements that contain an <article> or <main> descendant --
            the negative-pattern wrapper might be a layout div around real content.
          - VERY_NEGATIVE_PATTERNS bypass the guards (they're never content).
        """
        # Snapshot the list because decompose() mutates the tree.
        candidates = scope.find_all(True, attrs={"class": True}) + \
                     scope.find_all(True, attrs={"id": True})
        # Dedup by id() -- find_all(class) and find_all(id) overlap.
        seen = set()

        for el in candidates:
            if id(el) in seen:
                continue
            seen.add(id(el))
            if not el.parent:  # already removed (parent gone)
                continue

            class_id = self._class_id_str(el)
            if not class_id:
                continue

            if VERY_NEGATIVE_PATTERNS.search(class_id):
                el.decompose()
                counts["removed_very_negative_pattern"] += 1
                continue

            if not NEGATIVE_PATTERNS.search(class_id):
                continue

            # Soft guards
            if el.name and el.name.lower() in PROTECTED_TAGS:
                continue
            if el.find(["article", "main"]):
                continue
            # If the element contains substantial prose (>=120 chars and >=2 <p>),
            # the negative class is probably a layout misnomer (e.g. "main-comment"
            # on a primary-content div). Keep it.
            text_len = len(el.get_text(" ", strip=True))
            if text_len >= 200 and len(el.find_all("p")) >= 2:
                continue

            el.decompose()
            counts["removed_negative_pattern"] += 1

    def _remove_high_link_density(self, scope, counts: dict) -> None:
        """
        Remove blocks where most of the text is inside links -- recommended-article
        carousels, in-article 'related' boxes, footers-of-links.
        """
        for el in scope.find_all(["div", "section", "ul", "ol"]):
            if not el.parent:
                continue
            if el.name and el.name.lower() in PROTECTED_TAGS:
                continue
            text = el.get_text(" ", strip=True)
            if len(text) < MIN_TEXT_FOR_LINK_DENSITY_CHECK:
                continue
            link_text_len = sum(
                len(a.get_text(" ", strip=True)) for a in el.find_all("a")
            )
            density = link_text_len / max(len(text), 1)
            if density >= self._link_density:
                el.decompose()
                counts["removed_high_link_density"] += 1

    def _remove_empty_wrappers(self, scope, counts: dict) -> None:
        """
        Drop now-empty wrappers left over after other passes. We do two passes
        because removing inner wrappers can make outer ones empty too.

        Important: do NOT drop <p> tags here. Very short paragraphs are common
        in real article bodies ("Lead", "Updated", "Q&A", etc.) and removing
        them is a content regression.
        """
        for _ in range(2):
            removed_this_pass = 0
            for el in scope.find_all(["div", "span", "section", "figure"]):
                if not el.parent:
                    continue
                if el.name and el.name.lower() in PROTECTED_TAGS:
                    continue
                text = el.get_text(" ", strip=True)
                if text and len(text) >= MIN_TEXT_LEN_FOR_DIV_OR_SPAN:
                    continue
                # Wrapper is empty-ish -- but keep if it carries an <img> / <video>.
                if el.find(["img", "video", "audio", "iframe", "blockquote", "h1", "h2", "h3", "h4"]):
                    continue
                el.decompose()
                removed_this_pass += 1
            counts["removed_empty_wrapper"] += removed_this_pass
            if removed_this_pass == 0:
                break

    def _strip_attributes(self, scope, counts: dict) -> None:
        for el in scope.find_all(True):
            if not el.attrs:
                continue
            keep = {k: v for k, v in el.attrs.items() if k in KEEP_ATTRS}
            dropped = len(el.attrs) - len(keep)
            if dropped > 0:
                el.attrs = keep
                counts["attr_stripped"] += dropped

    def _resolve_urls(self, scope, base_url: str, counts: dict) -> None:
        """Make hrefs/srcs absolute so the downstream LLM gets canonical URLs."""
        for el in scope.find_all(True):
            for attr in ("href", "src"):
                v = el.attrs.get(attr)
                if isinstance(v, str) and v and not v.startswith(("http://", "https://", "data:", "mailto:", "tel:", "javascript:")):
                    try:
                        el.attrs[attr] = urljoin(base_url, v)
                        counts["url_resolved"] += 1
                    except Exception:
                        pass

    # ----------------------------------------------------------------- helpers

    @staticmethod
    def _class_id_str(el) -> str:
        cls = el.attrs.get("class")
        if isinstance(cls, list):
            cls = " ".join(cls)
        eid = el.attrs.get("id") or ""
        return f"{cls or ''} {eid}".strip()
