"""Contract tests for ProcessingRouter behavior and thresholds."""

from dataclasses import dataclass, field

from bs4 import BeautifulSoup
from django.test import SimpleTestCase

from apps.content.processor.routing import ProcessingRouter


@dataclass
class DummyArticle:
    id: int = 1
    raw_html: str = "<html><body><article><p>content</p></article></body></html>"
    has_raw_content: bool = True
    source_name: str = "example.com"
    paywall_detected: bool = False
    paywall_indicators: list = field(default_factory=list)


class ProcessingRouterContractTests(SimpleTestCase):
    def setUp(self):
        self.router = ProcessingRouter()

    def test_determine_route_falls_back_when_no_content(self):
        article = DummyArticle(has_raw_content=False, raw_html="")
        self.assertEqual(self.router.determine_route(article), "safari_mode")

    def test_determine_route_falls_back_on_exception(self):
        article = DummyArticle()

        def boom(*args, **kwargs):
            raise RuntimeError("boom")

        self.router.analyze_content_complexity = boom
        self.assertEqual(self.router.determine_route(article), "safari_mode")

    def test_analyze_content_complexity_returns_contract_shape(self):
        article = DummyArticle(raw_html="<html><body><article><p>Normal body text.</p></article></body></html>")
        analysis = self.router.analyze_content_complexity(article.raw_html, article)

        self.assertTrue(0.0 <= analysis.overall_score <= 1.0)
        self.assertIn(analysis.recommended_route, {"algorithmic", "llm_enhanced", "hybrid"})
        self.assertIsInstance(analysis.indicators, dict)
        self.assertEqual(set(analysis.indicators.keys()), set(self.router.COMPLEXITY_INDICATORS.keys()))

    def test_paywall_analysis_uses_article_flag(self):
        article = DummyArticle(paywall_detected=True, paywall_indicators=["subscription_required"])
        score = self.router._analyze_paywall_content(article.raw_html, article)
        self.assertGreaterEqual(score, 0.4)

    def test_paywall_analysis_detects_patterns(self):
        article = DummyArticle(raw_html="<html><body>Subscriber only premium content. Continue reading.</body></html>")
        score = self.router._analyze_paywall_content(article.raw_html, article)
        self.assertGreater(score, 0.0)

    def test_complex_layout_detection(self):
        html = """
        <html><body>
          <div class='grid layout'>x</div>
          <div class='column content'>x</div>
          <div class='content section'>x</div>
          <div class='content section'>x</div>
          <div class='content section'>x</div>
          <aside class='sidebar related'>x</aside>
          <aside class='sidebar related'>x</aside>
          <div class='modal overlay'>x</div>
        </body></html>
        """
        score = self.router._detect_complex_layout(BeautifulSoup(html, "html.parser"))
        self.assertGreater(score, 0.0)

    def test_embedded_media_analysis(self):
        html = """
        <html><body>
          <iframe src='https://twitter.com/embed/abc'></iframe>
          <iframe src='https://youtube.com/embed/abc'></iframe>
          <video></video>
          <div class='interactive-chart'></div>
        </body></html>
        """
        score = self.router._analyze_embedded_media(BeautifulSoup(html, "html.parser"))
        self.assertGreater(score, 0.0)

    def test_dynamic_content_assessment(self):
        html = """
        <html><body>
          <script>window.react=true</script>
          <script>window.ajax=true</script>
          <script>window.lazyload=true</script>
          <div data-content-url='/api/content'></div>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")
        score = self.router._assess_dynamic_content(soup, html)
        self.assertGreater(score, 0.0)

    def test_noise_ratio_empty_document(self):
        soup = BeautifulSoup("<html></html>", "html.parser")
        self.assertEqual(self.router._calculate_noise_ratio(soup), 1.0)

    def test_noise_ratio_detects_noise_sections(self):
        html = """
        <html><body>
          <nav>Top links and navigation menu</nav>
          <header>Header promo content</header>
          <article><p>Main reporting body with long factual text.</p></article>
          <footer>Footer links and policies</footer>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")
        ratio = self.router._calculate_noise_ratio(soup)
        self.assertGreaterEqual(ratio, 0.0)
        self.assertLessEqual(ratio, 1.0)

    def test_source_complexity_known_complex_source(self):
        article = DummyArticle(source_name="news.ft.com")
        self.assertEqual(self.router._get_source_complexity_score(article), 0.8)

    def test_source_complexity_known_simple_source(self):
        article = DummyArticle(source_name="www.reuters.com")
        self.assertEqual(self.router._get_source_complexity_score(article), 0.2)

    def test_source_complexity_unknown_source_defaults_medium(self):
        article = DummyArticle(source_name="unknown-source.test")
        self.assertEqual(self.router._get_source_complexity_score(article), 0.5)

    def test_determine_route_from_score_algorithmic(self):
        route, confidence, _ = self.router._determine_route_from_score(0.2, {"paywall_content": 0.0})
        self.assertEqual(route, "algorithmic")
        self.assertGreaterEqual(confidence, 0.0)

    def test_determine_route_from_score_llm(self):
        route, confidence, _ = self.router._determine_route_from_score(0.7, {"paywall_content": 0.5})
        self.assertEqual(route, "llm_enhanced")
        self.assertGreaterEqual(confidence, 0.0)

    def test_determine_route_from_score_hybrid(self):
        route, confidence, _ = self.router._determine_route_from_score(0.95, {"paywall_content": 0.8})
        self.assertEqual(route, "hybrid")
        self.assertGreaterEqual(confidence, 0.0)

    def test_update_thresholds_clamps_values(self):
        self.router.update_thresholds(llm_threshold=-1.0, hybrid_threshold=2.0)
        self.assertEqual(self.router.llm_threshold, 0.0)
        self.assertEqual(self.router.hybrid_threshold, 1.0)
