"""
Create Reference Quality Examples

Management command to create reference quality examples for evaluation
calibration, few-shot learning, and benchmarking.
"""
from django.core.management.base import BaseCommand
from apps.articles.models import Article
from apps.content.quality.models import ReferenceQualityExample
from apps.content.quality.html_preprocessor import HTMLPreprocessor
import json


class Command(BaseCommand):
    help = 'Create reference quality examples for evaluation calibration and few-shot learning'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing reference examples before creating new ones'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating it'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('📚 Creating Reference Quality Examples')
        )
        
        if options['clear_existing']:
            if not options['dry_run']:
                count = ReferenceQualityExample.objects.count()
                ReferenceQualityExample.objects.all().delete()
                self.stdout.write(f"🗑️ Cleared {count} existing reference examples")
            else:
                self.stdout.write("🗑️ Would clear existing reference examples")
        
        # Reference examples data with their classifications
        reference_data = [
            # Perfect examples (>0.95)
            {
                'article_id': 15239,
                'quality_class': 'perfect',
                'reference_scores': {
                    'overall': 0.96,
                    'completeness': 0.98,
                    'purity': 0.96,
                    'structure': 0.94,
                    'readability': 0.96
                },
                'explanation': "Excellent extraction with complete content capture including images, text, and embeds. Perfect formatting preservation with correct image captions and embedded content. No noise detected.",
                'missing_elements': [],
                'noise_detected': [],
                'key_strengths': ["Complete content capture", "Perfect formatting", "Correct image captions", "Embedded content preserved"],
                'improvement_areas': []
            },
            
            # Good examples (0.80-0.95)
            {
                'article_id': 15193,
                'quality_class': 'good',
                'reference_scores': {
                    'overall': 0.85,
                    'completeness': 0.88,
                    'purity': 0.92,
                    'structure': 0.82,
                    'readability': 0.88
                },
                'explanation': "High-quality extraction with almost complete content and good formatting. Missing JW video embed (not feasible) and minor image formatting issues.",
                'missing_elements': ["JW video embed", "Side-by-side image formatting"],
                'noise_detected': [],
                'key_strengths': ["Clean content", "Good formatting", "Images captured"],
                'improvement_areas': ["Image formatting preservation", "Video embed handling"]
            },
            {
                'article_id': 15158,
                'quality_class': 'good',
                'reference_scores': {
                    'overall': 0.83,
                    'completeness': 0.85,
                    'purity': 0.88,
                    'structure': 0.80,
                    'readability': 0.85
                },
                'explanation': "Good extraction with minimal noise and well-preserved formatting including bold, italics, and pull quotes. Missing Twitter embeds and contains ethics notice.",
                'missing_elements': ["Twitter embeds"],
                'noise_detected': ["Ethics notice"],
                'key_strengths': ["Good formatting", "Bold/italic preservation", "Pull quotes"],
                'improvement_areas': ["Social media embed handling", "Editorial notice filtering"]
            },
            {
                'article_id': 15157,
                'quality_class': 'good',
                'reference_scores': {
                    'overall': 0.82,
                    'completeness': 0.80,
                    'purity': 0.92,
                    'structure': 0.78,
                    'readability': 0.85
                },
                'explanation': "Clean extraction with good content capture. Missing article subheading and content carousel section about COVID risk conditions.",
                'missing_elements': ["Article subheading", "Content carousel section"],
                'noise_detected': [],
                'key_strengths': ["Clean content", "Good structure", "No noise"],
                'improvement_areas': ["Section completeness", "Carousel content handling"]
            },
            
            # Imperfect examples (0.00-0.80)
            {
                'article_id': 16108,
                'quality_class': 'imperfect',
                'reference_scores': {
                    'overall': 0.45,
                    'completeness': 0.75,
                    'purity': 0.35,
                    'structure': 0.40,
                    'readability': 0.50
                },
                'explanation': "Contains substantial noise including social media sharing and related articles. Poor distinction between main text, captions, and summary text.",
                'missing_elements': [],
                'noise_detected': ["Social media sharing", "Related articles", "Poor content distinction"],
                'key_strengths': ["Full content present"],
                'improvement_areas': ["Noise filtering", "Content type distinction", "Formatting improvement"]
            },
            {
                'article_id': 15997,
                'quality_class': 'imperfect',
                'reference_scores': {
                    'overall': 0.55,
                    'completeness': 0.70,
                    'purity': 0.60,
                    'structure': 0.65,
                    'readability': 0.70
                },
                'explanation': "Contains core content with good formatting but missing main image and includes commercial noise like newsletter subscriptions.",
                'missing_elements': ["Main article image"],
                'noise_detected': ["Newsletter subscription", "Commercial content"],
                'key_strengths': ["Core content present", "Good formatting"],
                'improvement_areas': ["Image extraction", "Commercial noise filtering"]
            },
            {
                'article_id': 15163,
                'quality_class': 'imperfect',
                'reference_scores': {
                    'overall': 0.35,
                    'completeness': 0.70,
                    'purity': 0.40,
                    'structure': 0.20,
                    'readability': 0.45
                },
                'explanation': "Core content present but missing main image and subheading. Contains noise from comments and signup prompts. No formatting captured.",
                'missing_elements': ["Main image", "Subheading"],
                'noise_detected': ["Comments", "Signup prompts"],
                'key_strengths': ["Core content present"],
                'improvement_areas': ["Image extraction", "Noise filtering", "Formatting preservation"]
            },
            {
                'article_id': 15999,
                'quality_class': 'imperfect',
                'reference_scores': {
                    'overall': 0.40,
                    'completeness': 0.75,
                    'purity': 0.35,
                    'structure': 0.45,
                    'readability': 0.55
                },
                'explanation': "Core content present with minimal formatting but substantial noise including article date in body and editor's notes as plain text.",
                'missing_elements': [],
                'noise_detected': ["Article date in body", "Editor's note as plain text", "Newsletter callouts"],
                'key_strengths': ["Core content present", "Minimal formatting"],
                'improvement_areas': ["Metadata placement", "Editorial content handling", "Newsletter filtering"]
            },
            {
                'article_id': 16114,
                'quality_class': 'imperfect',
                'reference_scores': {
                    'overall': 0.50,
                    'completeness': 0.70,
                    'purity': 0.45,
                    'structure': 0.55,
                    'readability': 0.60
                },
                'explanation': "Core content with acceptable formatting but missing main image and contains noise like byline in article body and sharing CTAs.",
                'missing_elements': ["Main image", "Some links"],
                'noise_detected': ["Byline in article body", "Sharing CTAs"],
                'key_strengths': ["Core content present", "Acceptable formatting"],
                'improvement_areas': ["Image extraction", "Byline placement", "CTA filtering"]
            },
            {
                'article_id': 16106,
                'quality_class': 'imperfect',
                'reference_scores': {
                    'overall': 0.25,
                    'completeness': 0.85,
                    'purity': 0.20,
                    'structure': 0.30,
                    'readability': 0.40
                },
                'explanation': "Virtually all core content present with good formatting but filled with substantial noise including tags, newsletter callouts, and faulty formatting.",
                'missing_elements': [],
                'noise_detected': ["Byline in article body", "Article date in body", "Tags", "Newsletter callouts", "Comments", "Related articles"],
                'key_strengths': ["Complete content", "Good formatting"],
                'improvement_areas': ["Extensive noise filtering", "Metadata placement", "Structure correction"]
            },
            
            # Awful examples (<0.00)
            {
                'article_id': 16142,
                'quality_class': 'awful',
                'reference_scores': {
                    'overall': -0.80,
                    'completeness': 0.05,
                    'purity': 0.10,
                    'structure': 0.05,
                    'readability': 0.10
                },
                'explanation': "Contains virtually only noise with no core content. Mostly comments, author bylines, and related articles with no actual article text.",
                'missing_elements': ["All main content", "Article text", "Headlines"],
                'noise_detected': ["Comments", "Author bylines in body", "Related articles", "No actual content"],
                'key_strengths': [],
                'improvement_areas': ["Complete extraction overhaul", "Content detection", "Noise elimination"]
            },
            {
                'article_id': 16144,  # Note: This appears to be a duplicate ID, might need clarification
                'quality_class': 'awful',
                'reference_scores': {
                    'overall': -0.20,
                    'completeness': 0.60,
                    'purity': 0.25,
                    'structure': 0.35,
                    'readability': 0.40
                },
                'explanation': "Heavy noise and duplicate content with 'read more' links and related articles. Missing YouTube video and main image. No subheading detection.",
                'missing_elements': ["YouTube video embed", "Article image", "Subheadings"],
                'noise_detected': ["Read more links", "Related articles", "Titles", "Tags", "Duplicate content"],
                'key_strengths': ["Main content mostly present"],
                'improvement_areas': ["Duplicate content removal", "Video embed handling", "Subheading detection"]
            }
        ]
        
        preprocessor = HTMLPreprocessor()
        created_count = 0
        
        for ref_data in reference_data:
            try:
                # Get article by ID
                article = Article.objects.get(id=ref_data['article_id'])
                
                self.stdout.write(f"\n📄 Processing Article {ref_data['article_id']}: {article.title[:50]}...")
                
                if options['dry_run']:
                    self.stdout.write(f"   📊 Would create {ref_data['quality_class']} example (Score: {ref_data['reference_scores']['overall']:.3f})")
                    continue
                
                # Check if example already exists
                existing = ReferenceQualityExample.objects.filter(article=article).first()
                if existing:
                    self.stdout.write(f"   ⚠️ Reference example already exists, skipping...")
                    continue
                
                # Prepare content data
                content = article.clean_content or article.basic_content or article.content or ""
                content_blocks = article.content_blocks or []
                
                # Preprocess HTML if available
                preprocessed_html = ""
                if article.raw_html:
                    try:
                        preprocessed = preprocessor.preprocess_for_evaluation(
                            article.raw_html,
                            url=article.url,
                            max_tokens=10000,
                            use_cache=True
                        )
                        preprocessed_html = preprocessed.cleaned_html
                    except Exception as e:
                        self.stdout.write(f"   ⚠️ HTML preprocessing failed: {e}")
                
                # Create reference example
                reference_example = ReferenceQualityExample.objects.create(
                    article=article,
                    quality_class=ref_data['quality_class'],
                    reference_overall_score=ref_data['reference_scores']['overall'],
                    reference_completeness=ref_data['reference_scores']['completeness'],
                    reference_purity=ref_data['reference_scores']['purity'],
                    reference_structure=ref_data['reference_scores']['structure'],
                    reference_readability=ref_data['reference_scores']['readability'],
                    reference_explanation=ref_data['explanation'],
                    reference_missing_elements=ref_data['missing_elements'],
                    reference_noise_detected=ref_data['noise_detected'],
                    reference_key_strengths=ref_data['key_strengths'],
                    reference_improvement_areas=ref_data['improvement_areas'],
                    stored_raw_html=article.raw_html or "",
                    stored_preprocessed_html=preprocessed_html,
                    stored_extracted_content=content,
                    stored_content_blocks=content_blocks,
                    created_by="manual_curation",
                    notes=f"Curated reference example for {ref_data['quality_class']} quality"
                )
                
                created_count += 1
                self.stdout.write(f"   ✅ Created {ref_data['quality_class']} reference example (Score: {ref_data['reference_scores']['overall']:.3f})")
                
            except Article.DoesNotExist:
                self.stdout.write(f"   ❌ Article {ref_data['article_id']} not found")
                continue
            except Exception as e:
                self.stdout.write(f"   ❌ Error creating reference example: {e}")
                continue
        
        # Summary
        self.stdout.write(f"\n{'='*60}")
        if options['dry_run']:
            self.stdout.write(self.style.SUCCESS(f'📊 DRY RUN: Would create {len(reference_data)} reference examples'))
        else:
            self.stdout.write(self.style.SUCCESS(f'📚 Created {created_count} reference examples successfully'))
            
            # Show summary by quality class
            if created_count > 0:
                self.stdout.write(f"\n📊 Reference Examples by Quality Class:")
                for quality_class in ReferenceQualityExample.QualityClass.values:
                    count = ReferenceQualityExample.objects.filter(quality_class=quality_class).count()
                    if count > 0:
                        self.stdout.write(f"   📝 {quality_class.title()}: {count} examples")
        
        self.stdout.write(f"✅ Reference quality examples setup completed!") 