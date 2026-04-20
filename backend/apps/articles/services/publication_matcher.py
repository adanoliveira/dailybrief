"""
Shared publication matching service.

Finds or creates Publication records based on source identifiers (domain, API ID, name).
Used by all ingestion gateways to map articles to publications consistently.
"""

import logging

from django.db import models

from apps.feeds.models import Publication
from apps.feeds.utils import extract_domain, generate_logo_url

logger = logging.getLogger(__name__)


class PublicationMatcher:
    """
    Finds or creates Publication records from article metadata.

    Caches lookups in memory for the lifetime of the instance (typically one sync batch).

    Usage:
        matcher = PublicationMatcher()
        pub = matcher.match(source_id='reuters', source_name='Reuters', article_url='https://reuters.com/...')
    """

    def __init__(self):
        self._mapping = self._build_mapping()

    def _build_mapping(self) -> dict:
        """Build in-memory lookup of publications by source ID and domain."""
        mapping = {}
        for pub in Publication.objects.filter(
            models.Q(news_api_id__isnull=False) | models.Q(domain__isnull=False)
        ):
            if pub.news_api_id:
                mapping[f"id:{pub.news_api_id.lower()}"] = pub
            if pub.domain:
                mapping[f"domain:{pub.domain.lower()}"] = pub
        return mapping

    def match(
        self,
        source_id: str | None = None,
        source_name: str = '',
        article_url: str = '',
    ) -> Publication | None:
        """
        Find an existing publication or create a new one.

        Lookup order:
        1. By source_id (e.g., NewsAPI ID)
        2. By domain extracted from article_url
        3. Create new publication if enough info is available

        Args:
            source_id: Source-specific identifier (e.g., newsapi source ID)
            source_name: Human-readable source name
            article_url: URL of an article (used for domain extraction)

        Returns:
            Publication instance or None if insufficient data.
        """
        domain = extract_domain(article_url)

        # Try by source ID
        if source_id:
            key = f"id:{source_id.lower()}"
            if key in self._mapping:
                pub = self._mapping[key]
                self._update_if_needed(pub, domain)
                return pub

        # Try by domain
        if domain:
            key = f"domain:{domain.lower()}"
            if key in self._mapping:
                pub = self._mapping[key]
                self._update_if_needed(pub, domain)
                return pub

        # Create new publication if we have enough info
        if source_name and (source_id or domain):
            pub = self._create_publication(source_id, source_name, domain)
            return pub

        return None

    def match_by_publication(self, publication: Publication) -> Publication:
        """
        Directly return a known publication (used by RSS where feed→publication FK exists).
        Ensures the publication is in the cache for future lookups.
        """
        if publication.news_api_id:
            self._mapping[f"id:{publication.news_api_id.lower()}"] = publication
        if publication.domain:
            self._mapping[f"domain:{publication.domain.lower()}"] = publication
        return publication

    def _update_if_needed(self, pub: Publication, domain: str | None):
        """Update domain and logo if missing."""
        updated_fields = []

        if domain and not pub.domain:
            pub.domain = domain
            updated_fields.append('domain')

        if domain and not pub.logo_url:
            logo_url = generate_logo_url(domain)
            if logo_url:
                pub.logo_url = logo_url
                updated_fields.append('logo_url')

        if updated_fields:
            pub.save(update_fields=updated_fields)

    def _create_publication(
        self, source_id: str | None, source_name: str, domain: str | None
    ) -> Publication:
        """Create a new publication and add to cache."""
        logo_url = generate_logo_url(domain) if domain else None

        pub = Publication(
            name=source_name,
            news_api_id=source_id,
            domain=domain,
            website_url=f"https://{domain}" if domain else "",
            logo_url=logo_url,
        )
        pub.save()

        # Add to cache
        if source_id:
            self._mapping[f"id:{source_id.lower()}"] = pub
        if domain:
            self._mapping[f"domain:{domain.lower()}"] = pub

        logger.info(f"Created new publication: {source_name} (domain: {domain}, id: {source_id})")
        return pub
