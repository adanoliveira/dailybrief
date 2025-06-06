"""
Django management command to check the status of articles by date and region.
"""
from datetime import datetime, date
from django.core.management.base import BaseCommand

from apps.articles.models import Article


class Command(BaseCommand):
    help = 'Check the status of articles by date and region'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            required=True,
            help='Date to check articles (YYYY-MM-DD format, e.g., 2025-06-05)'
        )
        parser.add_argument(
            '--regions',
            type=str,
            default='us,ca,uk,br',
            help='Comma-separated region codes (default: us,ca,uk,br)'
        )
    
    def handle(self, *args, **options):
        # Parse date
        try:
            target_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
        except ValueError:
            self.stdout.write(
                self.style.ERROR(f"❌ Invalid date format. Use YYYY-MM-DD")
            )
            return
        
        # Parse regions
        region_codes = [r.strip() for r in options['regions'].split(',')]
        
        self.stdout.write("=" * 60)
        self.stdout.write(f"📊 ARTICLES STATUS FOR {target_date}")
        self.stdout.write("=" * 60)
        
        # Get articles for the date and regions
        articles = Article.objects.filter(
            published_at__date=target_date,
            regions__code__in=region_codes
        ).distinct()
        
        total_count = articles.count()
        
        # Check articles with content
        with_content = articles.filter(
            raw_html__isnull=False
        ).exclude(raw_html='').exclude(raw_html__exact='')
        
        content_count = with_content.count()
        
        # Check articles with sufficient content (>1000 chars)
        sufficient_content = articles.extra(
            where=["CHAR_LENGTH(raw_html) > %s"],
            params=[1000]
        )
        
        sufficient_count = sufficient_content.count()
        
        # Check AI processed articles
        ai_processed = articles.filter(
            extracted_metadata__ai_extraction=True
        )
        
        ai_count = ai_processed.count()
        
        # Display statistics
        self.stdout.write(f"📰 Total articles: {total_count}")
        self.stdout.write(f"📄 With any content: {content_count}")
        self.stdout.write(f"✅ With sufficient content (>1000 chars): {sufficient_count}")
        self.stdout.write(f"🤖 AI processed: {ai_count}")
        self.stdout.write(f"⏳ Pending content: {total_count - content_count}")
        self.stdout.write(f"⏳ Pending processing: {sufficient_count - ai_count}")
        
        # Sample articles
        if sufficient_count > 0:
            self.stdout.write(f"\n📋 Sample articles ready for processing:")
            sample_articles = list(sufficient_content[:5])
            for i, article in enumerate(sample_articles, 1):
                regions = ', '.join([r.code for r in article.regions.all()])
                content_length = len(article.raw_html) if article.raw_html else 0
                ai_status = "✅ AI" if article.extracted_metadata and article.extracted_metadata.get('ai_extraction') else "❌ No AI"
                self.stdout.write(f"   {i}. ID:{article.id} - {article.title[:50]}... ({content_length:,} chars) {ai_status}")
        
        if content_count == 0:
            self.stdout.write(f"\n⚠️  NO ARTICLES HAVE CONTENT YET")
            self.stdout.write(f"   The fetch process may still be running or may have failed.")
            self.stdout.write(f"   Check the fetch_by_date_region process status.")
        elif sufficient_count == 0:
            self.stdout.write(f"\n⚠️  NO ARTICLES HAVE SUFFICIENT CONTENT (>1000 chars)")
            self.stdout.write(f"   Articles have content but it's too short for processing.")
        elif ai_count == 0:
            self.stdout.write(f"\n✅ {sufficient_count} ARTICLES ARE READY FOR AI PROCESSING")
            self.stdout.write(f"   The process_ready_articles should be picking these up.")
        
        self.stdout.write("=" * 60) 