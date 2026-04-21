"""
RSS Direct Content Processor.

Handles articles where the RSS feed already delivered the full article body
(via content:encoded). These articles bypass both the BrowserSimulation fetcher
and the LLM extraction step — the RSS HTML is already the article body, so we
only need to clean, structure, and validate it locally.

This saves one LLM extraction call per RSS article at the processing stage.
"""
from __future__ import annotations

import logging
import re
import time
from html import unescape
from typing import List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Comment, Tag

from .models import ContentBlock, ProcessingResult

logger = logging.getLogger(__name__)


_STRIP_TAGS = {
    "script", "style", "noscript", "iframe", "form",
    "button", "input", "select", "textarea",
    "aside", "nav", "footer", "header",
}

_TRACKING_IMG_PATTERNS = (
    re.compile(r"pixel", re.IGNORECASE),
    re.compile(r"tracking", re.IGNORECASE),
    re.compile(r"beacon", re.IGNORECASE),
    re.compile(r"/1x1\.", re.IGNORECASE),
    re.compile(r"doubleclick", re.IGNORECASE),
    re.compile(r"googletagmanager", re.IGNORECASE),
)

_BLOCK_HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
_LIST_TAGS = {"ul", "ol"}


def _is_tracking_image(src: str) -> bool:
    if not src:
        return True
    if any(p.search(src) for p in _TRACKING_IMG_PATTERNS):
        return True
    # 1x1 images are almost always trackers
    return False


def _clean_soup(soup: BeautifulSoup) -> None:
    """Remove tracking pixels, comments, empty tags, and known-noisy elements in place."""
    for comment in soup.find_all(string=lambda s: isinstance(s, Comment)):
        comment.extract()

    for tag_name in _STRIP_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # Tracking pixels and 1x1 images
    for img in soup.find_all("img"):
        src = img.get("src", "") or img.get("data-src", "")
        width = img.get("width")
        height = img.get("height")
        if _is_tracking_image(src):
            img.decompose()
            continue
        try:
            if width and height and int(width) <= 2 and int(height) <= 2:
                img.decompose()
        except (TypeError, ValueError):
            pass

    # Drop empty inline tags (span, a, em, strong) that have no content after stripping
    for tag in soup.find_all(["span", "a", "em", "strong", "i", "b", "u"]):
        if not tag.get_text(strip=True) and not tag.find(["img", "video"]):
            tag.unwrap()


def _resolve_url(src: str, base_url: Optional[str]) -> str:
    if not src:
        return ""
    src = src.strip()
    if not base_url:
        return src
    if src.startswith(("http://", "https://", "//", "data:")):
        return src
    try:
        return urljoin(base_url, src)
    except Exception:
        return src


def _normalize_text(text: str) -> str:
    if not text:
        return ""
    return unescape(" ".join(text.split()))


def _heading_level(tag_name: str) -> int:
    try:
        return max(1, min(6, int(tag_name[1])))
    except (ValueError, IndexError):
        return 2


def _build_blocks_from_soup(soup: BeautifulSoup, base_url: Optional[str]) -> List[ContentBlock]:
    """Walk the cleaned soup and emit ContentBlock entries for paragraphs, headings, lists, etc."""
    blocks: List[ContentBlock] = []
    position = 0

    # If there's no <body>, use the soup itself as the root so standalone fragments work.
    root = soup.body or soup

    # We iterate direct descendants first; if the document is a flat fragment (typical
    # of content:encoded), those descendants ARE the article blocks. If the structure
    # nests the article inside a wrapper <div>, fall through to descendants.
    candidates = list(root.find_all(recursive=True))

    seen: set[int] = set()
    for tag in candidates:
        if not isinstance(tag, Tag):
            continue
        if id(tag) in seen:
            continue

        name = tag.name.lower() if tag.name else ""

        if name == "p":
            text = _normalize_text(tag.get_text(" "))
            if text:
                blocks.append(ContentBlock(type="paragraph", content=text, position=position))
                position += 1
                seen.add(id(tag))

        elif name in _BLOCK_HEADINGS:
            text = _normalize_text(tag.get_text(" "))
            if text:
                blocks.append(ContentBlock(
                    type="heading",
                    content=text,
                    level=_heading_level(name),
                    position=position,
                ))
                position += 1
                seen.add(id(tag))

        elif name == "blockquote":
            text = _normalize_text(tag.get_text(" "))
            if text:
                blocks.append(ContentBlock(
                    type="quote",
                    content=text,
                    position=position,
                    metadata={"type": "blockquote"},
                ))
                position += 1
                seen.add(id(tag))

        elif name in _LIST_TAGS:
            items: List[str] = []
            for li in tag.find_all("li", recursive=False):
                item_text = _normalize_text(li.get_text(" "))
                if item_text:
                    items.append(item_text)
                seen.add(id(li))
            if items:
                blocks.append(ContentBlock(
                    type="list",
                    content="",
                    position=position,
                    metadata={"items": items, "list_type": name},
                ))
                position += 1
                seen.add(id(tag))

        elif name in ("img", "figure"):
            if name == "figure":
                img = tag.find("img")
                caption_tag = tag.find("figcaption")
                caption = _normalize_text(caption_tag.get_text(" ")) if caption_tag else ""
            else:
                img = tag
                caption = ""
            if not img:
                continue
            src = img.get("src") or img.get("data-src") or ""
            if not src or _is_tracking_image(src):
                continue
            resolved = _resolve_url(src, base_url)
            alt = _normalize_text(img.get("alt") or "")
            metadata = {"src": resolved}
            if alt:
                metadata["alt"] = alt
            if caption:
                metadata["caption"] = caption
            for dim in ("width", "height"):
                value = img.get(dim)
                if value:
                    try:
                        metadata[dim] = int(value)
                    except (TypeError, ValueError):
                        pass
            blocks.append(ContentBlock(
                type="image",
                content=caption or alt,
                position=position,
                metadata=metadata,
            ))
            position += 1
            seen.add(id(tag))
            if name == "figure":
                seen.add(id(img))

    return blocks


def _build_clean_content(blocks: List[ContentBlock]) -> str:
    """Render blocks as plain text for downstream summarization / quality eval."""
    parts: List[str] = []
    for block in blocks:
        if block.type == "heading":
            parts.append(block.content)
        elif block.type == "paragraph":
            parts.append(block.content)
        elif block.type == "quote":
            parts.append(f"“{block.content}”")
        elif block.type == "list":
            items = block.metadata.get("items", []) if block.metadata else []
            for item in items:
                parts.append(f"• {item}")
        elif block.type == "image":
            caption = (block.metadata or {}).get("caption") or (block.metadata or {}).get("alt")
            if caption:
                parts.append(f"[Image] {caption}")
    return "\n\n".join(parts).strip()


def _estimate_quality(blocks: List[ContentBlock], clean_content: str) -> float:
    """
    Rough quality score for RSS-direct content, on the same 0–1 scale as other routes.

    We can't do the full semantic scoring the LLM path uses, so we approximate from:
    - Number of paragraph blocks (structure signal)
    - Total word count (depth signal)
    - Presence of some images/headings (richness signal)
    """
    if not blocks or not clean_content:
        return 0.0

    paragraph_count = sum(1 for b in blocks if b.type == "paragraph")
    heading_count = sum(1 for b in blocks if b.type == "heading")
    image_count = sum(1 for b in blocks if b.type == "image")
    word_count = len(clean_content.split())

    # Baseline: paragraphs and length carry most of the weight
    structure_score = min(paragraph_count / 8.0, 1.0) * 0.5
    length_score = min(word_count / 400.0, 1.0) * 0.4
    richness_score = min((heading_count + image_count) / 4.0, 1.0) * 0.1

    return round(structure_score + length_score + richness_score, 3)


def process_rss_content(
    html_content: str,
    *,
    base_url: Optional[str] = None,
) -> ProcessingResult:
    """
    Process pre-extracted RSS content into a ProcessingResult compatible with the
    rest of the pipeline (summarizer, analyzer, quality evaluator).
    """
    start = time.time()

    if not html_content or not html_content.strip():
        return ProcessingResult(
            success=False,
            error_message="RSS content is empty",
            route_used="rss_direct",
        )

    try:
        soup = BeautifulSoup(html_content, "html.parser")
        _clean_soup(soup)
        blocks = _build_blocks_from_soup(soup, base_url=base_url)
    except Exception as e:
        logger.exception("RSS direct processing failed during parsing")
        return ProcessingResult(
            success=False,
            error_message=f"RSS content parsing failed: {e}",
            processing_time_ms=int((time.time() - start) * 1000),
            route_used="rss_direct",
        )

    if not blocks:
        return ProcessingResult(
            success=False,
            error_message="RSS content produced no usable blocks",
            processing_time_ms=int((time.time() - start) * 1000),
            route_used="rss_direct",
        )

    clean_content = _build_clean_content(blocks)
    processing_time_ms = int((time.time() - start) * 1000)
    quality_score = _estimate_quality(blocks, clean_content)

    return ProcessingResult(
        success=True,
        clean_content=clean_content,
        content_blocks=blocks,
        extracted_metadata={
            "rss_direct": True,
            "total_blocks": len(blocks),
            "estimated_word_count": len(clean_content.split()),
            "content_types": {
                "paragraph": sum(1 for b in blocks if b.type == "paragraph"),
                "heading": sum(1 for b in blocks if b.type == "heading"),
                "image": sum(1 for b in blocks if b.type == "image"),
                "quote": sum(1 for b in blocks if b.type == "quote"),
                "list": sum(1 for b in blocks if b.type == "list"),
            },
            "processing_time_ms": processing_time_ms,
        },
        quality_score=quality_score,
        processing_time_ms=processing_time_ms,
        route_used="rss_direct",
    )
