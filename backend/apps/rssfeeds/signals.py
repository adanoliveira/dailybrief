"""
Signal handlers for RSS feeds.
"""

from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.rssfeeds.models import RSSFeed


CLASSIFICATION_FIELDS = {'publication', 'topic', 'region', 'language'}


@receiver(post_save, sender=RSSFeed)
def sync_publication_metadata_from_feed(
    sender,  # noqa: ANN001
    instance: RSSFeed,
    created: bool,
    update_fields=None,
    **kwargs,  # noqa: ANN003
) -> None:
    """
    Ensure Publication M2M metadata mirrors RSSFeed classifications.

    This keeps onboarding/recommendation filters consistent for RSS-only
    publications that may not have NewsAPI IDs or publication_relations entries.
    """
    if not created and update_fields is not None:
        if not CLASSIFICATION_FIELDS.intersection(set(update_fields)):
            return

    publication = instance.publication

    if instance.topic_id:
        publication.topics.add(instance.topic_id)

    if instance.region_id:
        publication.regions.add(instance.region_id)

    if instance.language_id:
        publication.languages.add(instance.language_id)
