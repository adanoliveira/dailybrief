"""
Simple test command to verify AI processor imports and basic functionality.
"""
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    """Test AI processor imports and basic functionality."""
    
    help = 'Test AI processor imports and basic functionality'
    
    def handle(self, *args, **options):
        """Test the imports and basic functionality."""
        
        try:
            # Test imports
            self.stdout.write("🔍 Testing imports...")
            
            from apps.content.processor.ai_processor import get_ai_processor
            self.stdout.write("   ✅ AI processor imported successfully")
            
            from apps.content.processor.extraction_templates import get_extraction_template
            self.stdout.write("   ✅ Extraction templates imported successfully")
            
            from apps.content.processor.content_block_builder import ContentBlockBuilder
            self.stdout.write("   ✅ Content block builder imported successfully")
            
            # Test basic instantiation
            self.stdout.write("\n🔧 Testing basic instantiation...")
            
            processor = get_ai_processor()
            self.stdout.write("   ✅ AI processor instance created successfully")
            
            template = get_extraction_template()
            self.stdout.write(f"   ✅ Template created: {template.identifier} v{template.version}")
            
            builder = ContentBlockBuilder()
            self.stdout.write("   ✅ Content block builder instance created successfully")
            
            # Test available templates
            self.stdout.write("\n📋 Available templates:")
            from apps.content.processor.extraction_templates import get_available_templates
            templates = get_available_templates()
            for template_id in templates:
                template_info = get_extraction_template(template_id)
                self.stdout.write(f"   - {template_id}: {template_info.identifier} v{template_info.version}")
            
            # Test template content
            self.stdout.write("\n📝 Testing template formatting...")
            test_html = "<h1>Test Title</h1><p>Test content</p>"
            test_metadata = {"title": "Test Article", "url": "http://example.com", "source": "Test Source"}
            
            formatted_prompt = template.format(
                preprocessed_html=test_html,
                article_metadata=test_metadata
            )
            
            prompt_length = len(formatted_prompt)
            self.stdout.write(f"   ✅ Template formatted successfully ({prompt_length:,} characters)")
            
            # Test content block builder with sample data
            self.stdout.write("\n🧱 Testing content block builder...")
            sample_blocks = [
                {
                    "type": "heading",
                    "content": "Test Heading",
                    "level": 1,
                    "position": 0,
                    "metadata": {}
                },
                {
                    "type": "paragraph",
                    "content": "Test paragraph content",
                    "level": None,
                    "position": 1,
                    "metadata": {}
                }
            ]
            
            content_blocks = builder.build_blocks(sample_blocks)
            self.stdout.write(f"   ✅ Built {len(content_blocks)} content blocks from sample data")
            
            for block in content_blocks:
                self.stdout.write(f"     - {block.type}: {block.content[:50]}...")
            
            self.stdout.write(self.style.SUCCESS("\n🎉 All tests passed! AI processor is ready for use."))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Test failed: {e}"))
            import traceback
            self.stdout.write(traceback.format_exc()) 