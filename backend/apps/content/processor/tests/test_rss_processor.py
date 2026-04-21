"""Tests for RSS direct processing and the content resolution chain.

Covers:
- process_rss_content() standalone HTML processing
- ContentProcessor._resolve_content_for_processing priority
- ContentProcessor routes RSS-origin articles to rss_direct without hitting the LLM
"""

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from apps.content.processor.rss_processor import process_rss_content
from apps.content.processor.services import ContentProcessor


RSS_HTML_FULL_ARTICLE = """
<p>Mercados fecharam em alta nesta quarta-feira após os dados de inflação mais
brandos do que o esperado animarem investidores. Traders disseram que o relatório
reduziu a pressão por novos aumentos de juros no curto prazo.</p>
<h2>Setores em destaque</h2>
<p>O setor financeiro liderou os ganhos, com bancos subindo mais de 2%. O setor
de tecnologia também avançou, impulsionado por ações de semicondutores.</p>
<ul>
  <li>Bancos: +2,3%</li>
  <li>Tecnologia: +1,8%</li>
  <li>Varejo: +1,1%</li>
</ul>
<figure>
  <img src="/images/market-rally.jpg" alt="Traders na bolsa">
  <figcaption>Traders comemoram na B3</figcaption>
</figure>
<p>Analistas projetam que o movimento de alta deve continuar caso os próximos
indicadores econômicos confirmem a tendência de desaceleração da inflação.</p>
<blockquote>A leitura foi positiva e alinhada às expectativas do mercado.</blockquote>
"""


class ProcessRssContentTests(SimpleTestCase):
    def test_parses_paragraphs_and_headings(self):
        result = process_rss_content(RSS_HTML_FULL_ARTICLE, base_url="https://example.com/article")

        self.assertTrue(result.success)
        self.assertEqual(result.route_used, "rss_direct")

        types = [b.type for b in result.content_blocks]
        self.assertIn("paragraph", types)
        self.assertIn("heading", types)
        self.assertIn("list", types)
        self.assertIn("quote", types)
        self.assertIn("image", types)

    def test_image_src_is_resolved_against_base_url(self):
        result = process_rss_content(RSS_HTML_FULL_ARTICLE, base_url="https://example.com/news/")
        image_blocks = [b for b in result.content_blocks if b.type == "image"]
        self.assertEqual(len(image_blocks), 1)
        self.assertEqual(image_blocks[0].metadata["src"], "https://example.com/images/market-rally.jpg")
        self.assertEqual(image_blocks[0].metadata["alt"], "Traders na bolsa")
        self.assertEqual(image_blocks[0].metadata["caption"], "Traders comemoram na B3")

    def test_clean_content_is_plain_text(self):
        result = process_rss_content(RSS_HTML_FULL_ARTICLE)
        self.assertNotIn("<p>", result.clean_content)
        self.assertNotIn("<h2>", result.clean_content)
        self.assertIn("Mercados fecharam", result.clean_content)

    def test_tracking_pixels_are_stripped(self):
        html = (
            '<p>Real content here with enough text to be kept.</p>'
            '<img src="https://track.example.com/pixel.gif" width="1" height="1">'
            '<img src="https://doubleclick.net/foo.gif">'
            '<p>Second paragraph follows.</p>'
        )
        result = process_rss_content(html)
        image_blocks = [b for b in result.content_blocks if b.type == "image"]
        self.assertEqual(image_blocks, [])

    def test_scripts_and_styles_removed(self):
        html = (
            '<script>alert("x")</script>'
            '<style>body { color: red; }</style>'
            '<p>Actual body content paragraph here.</p>'
        )
        result = process_rss_content(html)
        self.assertTrue(result.success)
        self.assertEqual(len(result.content_blocks), 1)
        self.assertEqual(result.content_blocks[0].type, "paragraph")

    def test_empty_content_returns_failure(self):
        result = process_rss_content("")
        self.assertFalse(result.success)

    def test_content_with_no_blocks_returns_failure(self):
        result = process_rss_content("<div><span></span></div>")
        self.assertFalse(result.success)

    def test_list_items_preserved(self):
        html = '<p>Intro paragraph.</p><ol><li>First</li><li>Second</li></ol>'
        result = process_rss_content(html)
        list_blocks = [b for b in result.content_blocks if b.type == "list"]
        self.assertEqual(len(list_blocks), 1)
        self.assertEqual(list_blocks[0].metadata["items"], ["First", "Second"])
        self.assertEqual(list_blocks[0].metadata["list_type"], "ol")


class ResolveContentForProcessingTests(SimpleTestCase):
    def setUp(self):
        self.processor = ContentProcessor()

    def _make_article(self, raw_html="", content="", basic_content=""):
        article = MagicMock()
        article.raw_html = raw_html
        article.content = content
        article.basic_content = basic_content
        return article

    def test_prefers_raw_html(self):
        article = self._make_article(raw_html="<html>x</html>", content="rss", basic_content="basic")
        content, source = self.processor._resolve_content_for_processing(article)
        self.assertEqual(source, "raw_html")
        self.assertEqual(content, "<html>x</html>")

    def test_falls_back_to_content(self):
        long_content = "x" * 300
        article = self._make_article(content=long_content)
        content, source = self.processor._resolve_content_for_processing(article)
        self.assertEqual(source, "rss_content")
        self.assertEqual(content, long_content)

    def test_falls_back_to_basic_content(self):
        long_basic = "y" * 300
        article = self._make_article(basic_content=long_basic)
        content, source = self.processor._resolve_content_for_processing(article)
        self.assertEqual(source, "basic_content")
        self.assertEqual(content, long_basic)

    def test_returns_none_when_no_usable_content(self):
        article = self._make_article(content="short", basic_content="also short")
        content, source = self.processor._resolve_content_for_processing(article)
        self.assertIsNone(content)
        self.assertIsNone(source)


class ProcessArticleContentRoutingTests(SimpleTestCase):
    def setUp(self):
        self.processor = ContentProcessor()

    def _make_article(self, raw_html="", content="", basic_content="", url=""):
        article = MagicMock()
        article.id = 1
        article.raw_html = raw_html
        article.content = content
        article.basic_content = basic_content
        article.url = url
        return article

    def test_rss_article_routes_to_rss_direct(self):
        article = self._make_article(
            content=RSS_HTML_FULL_ARTICLE,
            url="https://example.com/article",
        )
        with patch.object(self.processor, "llm_processor") as mock_llm:
            result = self.processor.process_article_content(article)
        mock_llm.process_content.assert_not_called()
        self.assertTrue(result.success)
        self.assertEqual(result.route_used, "rss_direct")

    def test_raw_html_path_unchanged(self):
        article = self._make_article(raw_html="<html><body>ok</body></html>")
        fake_result = MagicMock(success=True, quality_score=0.9)
        with patch.object(self.processor, "_process_llm_enhanced_mode", return_value=fake_result) as mock_llm_mode:
            result = self.processor.process_article_content(article)
        mock_llm_mode.assert_called_once()
        self.assertIs(result, fake_result)

    def test_missing_content_returns_failure(self):
        article = self._make_article()
        result = self.processor.process_article_content(article)
        self.assertFalse(result.success)
        self.assertIn("No usable content", result.error_message)
