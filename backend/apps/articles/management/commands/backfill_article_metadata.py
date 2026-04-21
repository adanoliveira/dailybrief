"""
Backfill missing article metadata from existing data.

Fixes:
  1. image_url from content_blocks (articles already processed but image_url is null)
  2. image_url from og:image in stored raw_html
  3. description from og:description in stored raw_html

Usage:
    python manage.py backfill_article_metadata              # Run all backfills
    python manage.py backfill_article_metadata --images     # Only image backfill
    python manage.py backfill_article_metadata --descriptions  # Only description backfill
    python manage.py backfill_article_metadata --dry-run    # Preview without saving
"""

import re
import logging

from django.core.management.base import BaseCommand
from django.db.models import Q

from apps.articles.models import Article

logger = logging.getLogger(__name__)


def extract_og_tag(html: str, property_name: str) -> str | None:
    """Extract an Open Graph meta tag value from HTML."""
    from bs4 import BeautifulSoup

    try:
        soup = BeautifulSoup(html[:100000], 'html.parser')
        wanted = property_name.lower()
        for tag in soup.find_all('meta'):
            prop = (tag.get('property') or tag.get('name') or '').strip().lower()
            if prop == wanted:
                content = (tag.get('content') or '').strip()
                if content:
                    return content
    except Exception:
        # Fall back to regex matching below.
        pass

    patterns = [
        rf'property="{property_name}"\s+content="([^"]+)"',
        rf'content="([^"]+)"\s+property="{property_name}"',
        rf"property='{property_name}'\s+content='([^']+)'",
        rf"content='([^']+)'\s+property='{property_name}'",
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


class Command(BaseCommand):
    help = 'Backfill missing image_url and description from existing processed data'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Preview without saving')
        parser.add_argument('--images', action='store_true', help='Only backfill images')
        parser.add_argument('--descriptions', action='store_true', help='Only backfill descriptions')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        do_images = options['images'] or (not options['images'] and not options['descriptions'])
        do_descs = options['descriptions'] or (not options['images'] and not options['descriptions'])

        if do_images:
            self._backfill_images_from_blocks(dry_run)
            self._backfill_images_from_og(dry_run)

        if do_descs:
            self._backfill_descriptions_from_og(dry_run)

    def _backfill_images_from_blocks(self, dry_run: bool):
        """Set image_url from first image in content_blocks."""
        self.stdout.write("\n--- Backfill image_url from content_blocks ---")

        articles = Article.objects.filter(
            process_status='completed',
            content_blocks__isnull=False,
        ).filter(Q(image_url__isnull=True) | Q(image_url=''))

        fixed = 0
        for article in articles.iterator(chunk_size=200):
            for block in (article.content_blocks or []):
                if block.get('type') in ('image', 'img', 'figure'):
                    src = (block.get('metadata') or {}).get('src')
                    if src and src.startswith('http'):
                        if not dry_run:
                            article.image_url = src[:1024]
                            article.save(update_fields=['image_url'])
                        fixed += 1
                        break

        label = "(DRY RUN)" if dry_run else ""
        self.stdout.write(self.style.SUCCESS(f"  Fixed {fixed} articles from content_blocks {label}"))

    def _backfill_images_from_og(self, dry_run: bool):
        """Extract og:image from stored raw_html for articles with no image."""
        self.stdout.write("\n--- Backfill image_url from og:image in raw_html ---")

        articles = Article.objects.filter(
            fetch_status='completed',
            raw_html__gt='',
        ).filter(Q(image_url__isnull=True) | Q(image_url=''))

        fixed = 0
        checked = 0
        for article in articles.iterator(chunk_size=50):
            checked += 1
            og_image = extract_og_tag(article.raw_html, 'og:image')
            if og_image and og_image.startswith('http'):
                if not dry_run:
                    article.image_url = og_image[:1024]
                    article.save(update_fields=['image_url'])
                fixed += 1

        label = "(DRY RUN)" if dry_run else ""
        self.stdout.write(self.style.SUCCESS(
            f"  Fixed {fixed} / {checked} articles from og:image {label}"
        ))

    def _backfill_descriptions_from_og(self, dry_run: bool):
        """Extract og:description from stored raw_html for articles with no description."""
        self.stdout.write("\n--- Backfill description from og:description in raw_html ---")

        articles = Article.objects.filter(
            fetch_status='completed',
            raw_html__gt='',
        ).filter(Q(description__isnull=True) | Q(description=''))

        fixed = 0
        checked = 0
        for article in articles.iterator(chunk_size=50):
            checked += 1
            og_desc = extract_og_tag(article.raw_html, 'og:description')
            if og_desc and len(og_desc) > 10:
                import html
                og_desc = html.unescape(og_desc)
                if not dry_run:
                    article.description = og_desc[:500]
                    article.save(update_fields=['description'])
                fixed += 1

        label = "(DRY RUN)" if dry_run else ""
        self.stdout.write(self.style.SUCCESS(
            f"  Fixed {fixed} / {checked} articles from og:description {label}"
        ))
