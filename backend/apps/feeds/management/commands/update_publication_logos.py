import json
import os
import logging
from django.core.management.base import BaseCommand
from apps.feeds.models import Publication

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Updates publication logo URLs from initial_data.json fixture"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry_run",
            action="store_true",
            help="Show what would be updated without making actual changes",
        )
        parser.add_argument(
            "--fixture_path",
            type=str,
            default="apps/feeds/fixtures/initial_data.json",
            help="Path to the fixture file (relative to Django project root)",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)
        fixture_path = options.get("fixture_path")
        
        # Format with absolute path
        mode = "DRY RUN" if dry_run else "UPDATE"
        self.stdout.write(f"\n{mode}: Updating publication logo URLs from fixture\n")
        self.stdout.write(f"Using fixture: {fixture_path}")
        self.stdout.write("=" * 50)
        
        # Load the fixture data
        try:
            with open(fixture_path, 'r') as fixture_file:
                fixture_data = json.load(fixture_file)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Fixture file not found: {fixture_path}"))
            return
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f"Invalid JSON in fixture file: {fixture_path}"))
            return
        
        # Create a mapping of publication IDs to logo URLs from the fixture
        logo_map = {}
        for item in fixture_data:
            if item['model'] == 'feeds.publication':
                pub_id = item['pk']
                logo_url = item['fields'].get('logo_url')
                if logo_url:
                    logo_map[pub_id] = logo_url
        
        if not logo_map:
            self.stdout.write(self.style.ERROR("No publication logo URLs found in fixture file"))
            return
            
        self.stdout.write(self.style.SUCCESS(f"Found {len(logo_map)} publication logo URLs in fixture"))
        
        # Get all publications from the database
        publications = Publication.objects.all()
        total_count = publications.count()
        
        # Track statistics
        updated_count = 0
        skipped_count = 0
        not_in_fixture_count = 0
        
        # Process each publication
        for pub in publications:
            if pub.id not in logo_map:
                self.stdout.write(self.style.WARNING(
                    f"SKIPPED (#{pub.id}): {pub.name} - Not found in fixture"
                ))
                not_in_fixture_count += 1
                continue
                
            new_logo_url = logo_map[pub.id]
            
            # Skip if the logo URL is the same
            if pub.logo_url == new_logo_url:
                self.stdout.write(self.style.WARNING(
                    f"SKIPPED (#{pub.id}): {pub.name} - Logo URL already up to date"
                ))
                skipped_count += 1
                continue
                
            # Update the publication
            old_logo = pub.logo_url or "(None)"
            if not dry_run:
                pub.logo_url = new_logo_url
                pub.save(update_fields=["logo_url"])
                
            updated_count += 1
            self.stdout.write(self.style.SUCCESS(
                f"UPDATED (#{pub.id}): {pub.name}\n"
                f"  Old: {old_logo}\n"
                f"  New: {new_logo_url}"
            ))
                
        # Print summary
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(f"Summary ({mode}):")
        self.stdout.write(f"  Total publications: {total_count}")
        self.stdout.write(f"  Updated: {updated_count}")
        self.stdout.write(f"  Skipped (same URL): {skipped_count}")
        self.stdout.write(f"  Not in fixture: {not_in_fixture_count}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING(
                "\nThis was a dry run. No changes were made to the database."
                "\nRun without --dry_run to apply changes."
            )) 