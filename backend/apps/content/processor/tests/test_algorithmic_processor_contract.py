"""Contract tests for AlgorithmicProcessor orchestration behavior.

These tests intentionally assert broad output contracts so internal extraction
heuristics can evolve while external processor behavior remains stable.
"""

from django.test import SimpleTestCase

from apps.content.processor.algorithmic_processor import AlgorithmicProcessor


LONG_ARTICLE_HTML = """
<!doctype html>
<html>
  <head>
    <title>Markets Rally as Inflation Cools</title>
  </head>
  <body>
    <header>
      <nav>Home Business Politics Technology Subscribe</nav>
    </header>

    <main>
      <article id="article-body" class="post-content article-body">
        <h1>Markets Rally as Inflation Cools in New Report</h1>

        <p>
          Global markets opened sharply higher on Wednesday after the latest inflation report
          showed a broader-than-expected slowdown across food, transport, and services.
          Traders said the report gave investors confidence that central banks can avoid further
          aggressive rate hikes while still keeping price growth under control over the next quarter.
          Analysts noted that sentiment improved across both equities and credit markets as the data
          reduced uncertainty around the near-term policy path.
        </p>

        <p>
          Portfolio managers described the move as a "relief rally" driven by lower volatility and
          stronger guidance from large multinational companies. Several firms revised earnings outlooks
          upward after reporting better margins and resilient consumer demand, especially in logistics,
          software, and energy infrastructure. While some sectors remain under pressure, strategists said
          broad participation in the rally indicates improving risk appetite rather than a narrow rotation.
        </p>

        <p>
          Policymakers cautioned that a single report does not establish a lasting trend, but they also
          acknowledged meaningful progress compared with conditions seen earlier in the year. Economic
          researchers highlighted that wage growth and hiring remain healthy, suggesting the economy is
          slowing in a more balanced way than feared. If upcoming labor and spending data confirm this
          pattern, expectations for a soft landing are likely to strengthen.
        </p>
      </article>

      <aside class="sidebar related promo">
        Subscribe for newsletters and deals.
      </aside>

      <div id="comments">
        Reader comments and reactions here.
      </div>
    </main>

    <footer>Copyright 2026 Daily Example News.</footer>
  </body>
</html>
"""


class AlgorithmicProcessorContractTests(SimpleTestCase):
    """Ensure public processor contracts remain stable after refactors."""

    def setUp(self):
        self.processor = AlgorithmicProcessor()
        self.article_metadata = {
            "title": "Markets Rally as Inflation Cools in New Report",
            "source_name": "Daily Example News",
            "author": "Reporter",
            "url": "https://example.com/markets-rally",
        }

    def test_process_content_success_contract(self):
        """Valid long-form HTML should produce structured safari_mode output."""
        result = self.processor.process_content(LONG_ARTICLE_HTML, self.article_metadata)

        self.assertTrue(result.success)
        self.assertEqual(result.route_used, "safari_mode")
        self.assertGreater(len(result.clean_content), 600)
        self.assertGreaterEqual(len(result.content_blocks), 3)
        self.assertGreaterEqual(result.quality_score, 0.0)
        self.assertIn("Global markets opened sharply higher", result.clean_content)

    def test_non_content_noise_is_not_dominant(self):
        """Navigation/marketing text should not dominate extracted content."""
        result = self.processor.process_content(LONG_ARTICLE_HTML, self.article_metadata)

        self.assertTrue(result.success)
        self.assertNotIn("Subscribe for newsletters and deals", result.clean_content)
        self.assertNotIn("Reader comments and reactions", result.clean_content)

    def test_invalid_html_input_contract(self):
        """Invalid input should fail gracefully with safari_mode_failed route."""
        result = self.processor.process_content("", self.article_metadata)

        self.assertFalse(result.success)
        self.assertEqual(result.route_used, "safari_mode_failed")
        self.assertIn("Invalid HTML input", result.error_message)

    def test_short_html_input_contract(self):
        """Too-short HTML should fail fast without raising exceptions."""
        result = self.processor.process_content("<html><body>short</body></html>", self.article_metadata)

        self.assertFalse(result.success)
        self.assertEqual(result.route_used, "safari_mode_failed")
        self.assertIn("too short", result.error_message.lower())
