from django.test import SimpleTestCase

from apps.feeds.utils import extract_domain, generate_logo_url


class FeedUtilityTests(SimpleTestCase):
    def test_extract_domain_handles_protocol_and_subdomain(self):
        self.assertEqual(extract_domain("https://www.nytimes.com/world/article"), "nytimes.com")
        self.assertEqual(extract_domain("http://bbc.co.uk/news"), "bbc.co.uk")
        self.assertEqual(extract_domain("www.techcrunch.com/news/ai"), "techcrunch.com")

    def test_extract_domain_removes_port_and_normalizes_case(self):
        self.assertEqual(extract_domain("HTTPS://WWW.EXAMPLE.COM:8080/path"), "example.com")

    def test_extract_domain_returns_none_for_empty_values(self):
        self.assertIsNone(extract_domain(""))
        self.assertIsNone(extract_domain(None))

    def test_generate_logo_url_uses_google_favicon_service(self):
        self.assertEqual(
            generate_logo_url("nytimes.com"),
            "https://www.google.com/s2/favicons?domain=nytimes.com&sz=128",
        )

    def test_generate_logo_url_returns_none_when_domain_missing(self):
        self.assertIsNone(generate_logo_url(""))
        self.assertIsNone(generate_logo_url(None))
