"""Tests for RSS content quality pre-validation.

The validation helper decides whether an RSS entry's content:encoded is usable
as the article body (skipping the fetcher) or whether it's a teaser/truncation
that should still be routed through BrowserSimulation.
"""

from django.test import SimpleTestCase

from apps.rssfeeds.services.article_processor import (
    FULL_CONTENT_WORD_THRESHOLD,
    rss_content_is_usable,
)


def _make_content(paragraph_count=3, words_per_para=220, suffix=""):
    base = "palavra " * words_per_para
    paragraphs = "".join(f"<p>{base.strip()}</p>" for _ in range(paragraph_count))
    return paragraphs + suffix


class RssContentIsUsableTests(SimpleTestCase):
    def test_accepts_full_article(self):
        content = _make_content(paragraph_count=4, words_per_para=200)
        word_count = content.count("palavra")
        self.assertGreater(word_count, FULL_CONTENT_WORD_THRESHOLD)
        self.assertTrue(rss_content_is_usable(content, word_count))

    def test_rejects_short_content(self):
        content = "<p>Short paragraph.</p><p>Another short one.</p>"
        self.assertFalse(rss_content_is_usable(content, word_count=50))

    def test_rejects_truncated_with_ellipsis(self):
        content = _make_content(suffix="<p>The rest is available at our site...</p>")
        word_count = content.count("palavra") + 10
        self.assertFalse(rss_content_is_usable(content, word_count))

    def test_rejects_read_more_marker(self):
        content = _make_content(suffix="<p>Continue reading</p>")
        word_count = content.count("palavra") + 5
        self.assertFalse(rss_content_is_usable(content, word_count))

    def test_rejects_leia_mais_marker(self):
        content = _make_content(suffix="<p>Leia mais</p>")
        word_count = content.count("palavra") + 5
        self.assertFalse(rss_content_is_usable(content, word_count))

    def test_rejects_single_paragraph(self):
        # 800 words, but only a single <p> tag and no double-newlines
        big_text = "word " * 800
        content = f"<p>{big_text.strip()}</p>"
        self.assertFalse(rss_content_is_usable(content, word_count=800))

    def test_accepts_double_newline_structure_without_p_tags(self):
        # Plain-text content with blank-line paragraph separators — still usable
        chunk = ("word " * 220).strip()
        content = f"{chunk}\n\n{chunk}\n\n{chunk}"
        word_count = len(content.split())
        self.assertTrue(rss_content_is_usable(content, word_count))

    def test_rejects_mostly_markup(self):
        # 2 paragraphs of text but drowned in markup — text-to-HTML ratio < 0.3
        short_text = "word " * 120  # ~600 visible chars per paragraph
        bloat_attr = "x" * 10000  # big attribute that isn't visible text
        content = (
            f'<div class="{bloat_attr}"><p>{short_text.strip()}</p></div>'
            f'<div data-tracking="{bloat_attr}"><p>{short_text.strip()}</p></div>'
            f'<div><span class="{bloat_attr}"></span></div>'
        )
        # ~240 visible words passes the length threshold (>500 by padding word_count)
        word_count = 600
        self.assertFalse(rss_content_is_usable(content, word_count))
