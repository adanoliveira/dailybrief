"""Regression tests for the hybrid HTML preprocessor."""

from bs4 import BeautifulSoup
from django.test import SimpleTestCase

from apps.content.processor.hybrid.preprocessor import HybridPreprocessor


class HybridPreprocessorRegressionTests(SimpleTestCase):
    def setUp(self):
        self.processor = HybridPreprocessor()

    def test_preserves_short_body_paragraphs(self):
        html = """
        <html><body><article>
          <p>Lead line.</p>
          <p>Q&A</p>
          <p>This is a longer paragraph that ensures the sample is realistic and above the
             minimum size threshold for preprocessing.</p>
          <p>Updated.</p>
        </article></body></html>
        """

        result = self.processor.preprocess(html)

        self.assertTrue(result.success)
        soup = BeautifulSoup(result.cleaned_html, "html.parser")
        text_by_p = [p.get_text(" ", strip=True) for p in soup.find_all("p")]

        self.assertIn("Lead line.", text_by_p)
        self.assertIn("Q&A", text_by_p)
        self.assertIn("Updated.", text_by_p)

    def test_preserves_img_wrapped_by_picture_and_resolves_src(self):
        html = """
        <html><body><article>
          <p>Intro paragraph with enough text for preprocessing to run safely.</p>
          <picture class="hero-image">
            <source srcset="/images/hero.webp 1x, /images/hero@2x.webp 2x" type="image/webp">
            <img src="/images/hero.jpg" alt="Hero">
          </picture>
          <p>Outro paragraph keeps this sample closer to a real article body.</p>
        </article></body></html>
        """

        result = self.processor.preprocess(html, base_url="https://example.com/news/story")

        self.assertTrue(result.success)
        soup = BeautifulSoup(result.cleaned_html, "html.parser")
        image = soup.find("img")
        self.assertIsNotNone(image)
        self.assertEqual(image.get("src"), "https://example.com/images/hero.jpg")
