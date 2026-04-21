from django.test import TestCase

from apps.feeds.models import Language, Publication, Region, Topic
from apps.rssfeeds.models import RSSFeed


class RSSPublicationMetadataSyncTests(TestCase):
    def setUp(self):
        self.topic_business = Topic.objects.create(name='Business', slug='business')
        self.topic_general = Topic.objects.create(name='General', slug='general')
        self.region_us = Region.objects.create(code='us', name='United States')
        self.region_br = Region.objects.create(code='br', name='Brazil')
        self.language_en = Language.objects.create(iso_code='en', name='English')
        self.language_pt = Language.objects.create(iso_code='pt', name='Portuguese')

        self.publication = Publication.objects.create(
            name='Example Publication',
            website_url='https://example.com',
            description='Test publication',
        )

    def test_create_feed_populates_publication_metadata(self):
        RSSFeed.objects.create(
            publication=self.publication,
            feed_url='https://example.com/rss/business.xml',
            topic=self.topic_business,
            region=self.region_br,
            language=self.language_pt,
        )

        self.assertTrue(
            self.publication.topics.filter(id=self.topic_business.id).exists()
        )
        self.assertTrue(
            self.publication.regions.filter(id=self.region_br.id).exists()
        )
        self.assertTrue(
            self.publication.languages.filter(id=self.language_pt.id).exists()
        )

    def test_updating_feed_classification_adds_new_publication_metadata(self):
        feed = RSSFeed.objects.create(
            publication=self.publication,
            feed_url='https://example.com/rss/top.xml',
            topic=self.topic_general,
            region=self.region_us,
            language=self.language_en,
        )

        feed.topic = self.topic_business
        feed.region = self.region_br
        feed.language = self.language_pt
        feed.save(update_fields=['topic', 'region', 'language'])

        self.assertTrue(
            self.publication.topics.filter(id=self.topic_general.id).exists()
        )
        self.assertTrue(
            self.publication.topics.filter(id=self.topic_business.id).exists()
        )
        self.assertTrue(
            self.publication.regions.filter(id=self.region_us.id).exists()
        )
        self.assertTrue(
            self.publication.regions.filter(id=self.region_br.id).exists()
        )
        self.assertTrue(
            self.publication.languages.filter(id=self.language_en.id).exists()
        )
        self.assertTrue(
            self.publication.languages.filter(id=self.language_pt.id).exists()
        )

    def test_non_classification_update_does_not_add_metadata(self):
        feed = RSSFeed.objects.create(
            publication=self.publication,
            feed_url='https://example.com/rss/empty.xml',
        )

        feed.etag = 'abc123'
        feed.save(update_fields=['etag'])

        self.assertEqual(self.publication.topics.count(), 0)
        self.assertEqual(self.publication.regions.count(), 0)
        self.assertEqual(self.publication.languages.count(), 0)
