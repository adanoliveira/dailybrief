from django.core.management.base import BaseCommand
from apps.feeds.models import Topic, Region, Language

class Command(BaseCommand):
    help = 'Populate descriptions for topics, regions, and languages where they add value'

    def handle(self, *args, **options):
        # Topic descriptions - matching our actual topics
        topic_descriptions = {
            'business': "Business news, markets, companies, and economic developments",
            'entertainment': "Arts, media, celebrity news, and cultural events",
            'general': "General news covering various topics of broad interest",
            'science': "Scientific discoveries, research, and technological advances",
            'sports': "Sports news, events, and athletic achievements",
            'technology': "Technology industry, digital innovation, and tech trends",
            'health': "Healthcare, medical research, and public health issues",
        }

        # Region descriptions - matching our actual region codes
        region_descriptions = {
            'us': "United States - News from or primarily affecting the United States",
            'gb': "United Kingdom - News from or primarily affecting the UK/Britain",
            'ca': "Canada - News and developments from Canadian sources",
            'au': "Australia - Coverage of Australian and Oceania news",
            'in': "India - News from the Indian subcontinent",
            'fr': "France - French national and regional news coverage",
            'de': "Germany - News from Germany and German-speaking regions",
            'jp': "Japan - Japanese national and business news",
            'br': "Brazil - Brazilian and Portuguese-language news",
            'ru': "Russia - News from Russian Federation and Russian-speaking regions",
            'cn': "China - News from mainland China and Chinese territories",
            'sa': "Saudi Arabia - News from Saudi Arabia and Gulf region",
        }

        # Language descriptions - matching our actual language codes
        language_descriptions = {
            'en': "English - International standard English",
            'es': "Spanish - Including both European and Latin American variants",
            'fr': "French - Standard French including regional variations",
            'de': "German - Standard German including regional variants",
            'it': "Italian - Standard Italian language",
            'ru': "Russian - Modern standard Russian",
            'ar': "Arabic - Modern Standard Arabic",
            'zh': "Chinese - Mandarin and other variants",
            'he': "Hebrew - Modern Hebrew",
            'no': "Norwegian - Bokmål and Nynorsk variants",
            'pt': "Portuguese - Brazilian and European variants",
            'sv': "Swedish - Standard Swedish",
            'nl': "Dutch - Standard Dutch including Flemish",
            'ud': "Urdu - Standard Urdu",
        }

        # Debug current state
        self.stdout.write("Current state:")
        self.stdout.write("\nTopics:")
        for topic in Topic.objects.all():
            self.stdout.write(f"- {topic.slug}: {topic.name} (Current desc: {topic.description or 'None'})")
        
        self.stdout.write("\nRegions:")
        for region in Region.objects.all():
            self.stdout.write(f"- {region.code}: {region.name} (Current desc: {region.description or 'None'})")
        
        self.stdout.write("\nLanguages:")
        for lang in Language.objects.all():
            self.stdout.write(f"- {lang.iso_code}: {lang.name} (Current desc: {lang.description or 'None'})")

        # Update topics
        updated_topics = 0
        for topic in Topic.objects.all():
            if topic.slug in topic_descriptions:
                topic.description = topic_descriptions[topic.slug]
                topic.save()
                updated_topics += 1
                self.stdout.write(f"Updated topic {topic.slug} with description: {topic.description}")
        self.stdout.write(f"Updated {updated_topics} topic descriptions")

        # Update regions
        updated_regions = 0
        for region in Region.objects.all():
            if region.code in region_descriptions:
                region.description = region_descriptions[region.code]
                region.save()
                updated_regions += 1
                self.stdout.write(f"Updated region {region.code} with description: {region.description}")
        self.stdout.write(f"Updated {updated_regions} region descriptions")

        # Update languages
        updated_languages = 0
        for language in Language.objects.all():
            if language.iso_code in language_descriptions:
                language.description = language_descriptions[language.iso_code]
                language.save()
                updated_languages += 1
                self.stdout.write(f"Updated language {language.iso_code} with description: {language.description}")
        self.stdout.write(f"Updated {updated_languages} language descriptions") 