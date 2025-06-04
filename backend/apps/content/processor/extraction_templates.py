"""
Content Extraction Prompt Templates - AI Content Extraction.

This module provides prompt templates for AI-powered content extraction,
following the proven template architecture from the quality evaluation system.
These templates achieved 100% JSON parsing success in quality evaluation.

Template Features:
- Clear system prompts with role definition
- Comprehensive output format specifications
- Type-specific extraction instructions
- Few-shot examples for consistency
- Robust error handling patterns
"""
import json
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod


class BaseExtractionTemplate(ABC):
    """
    Base class for content extraction prompt templates.
    
    Follows the same architecture as quality evaluation templates
    for consistency and proven reliability.
    """
    
    def __init__(self):
        """Initialize template with metadata."""
        self.identifier = self._get_identifier()
        self.version = self._get_version()
        self.operation = "content_extraction"
    
    @abstractmethod
    def _get_identifier(self) -> str:
        """Get template identifier."""
        pass
    
    @abstractmethod
    def _get_version(self) -> str:
        """Get template version."""
        pass
    
    @abstractmethod
    def format(self, preprocessed_html: str, article_metadata: Dict[str, Any]) -> str:
        """
        Format the extraction prompt with provided content and metadata.
        
        Args:
            preprocessed_html: Preprocessed HTML content
            article_metadata: Article metadata (title, url, source, etc.)
            
        Returns:
            Formatted prompt string
        """
        pass
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for content extraction."""
        return """You are an expert content extraction specialist with deep knowledge of web publishing, journalism, and HTML structure. Your task is to extract clean, structured content from web articles while preserving semantic meaning and proper formatting.

EXTRACTION MINDSET:
- Be COMPREHENSIVE: Extract every piece of main content (aim for 15-30+ blocks)
- Be SYSTEMATIC: Process content sequentially from top to bottom
- Be PRECISE: Use exact position numbers (0, 1, 2, 3, ...) with no gaps
- Be CONSISTENT: Always use HTML formatting (<strong>, <em>) never markdown

CORE PRINCIPLES:
- Focus only on main article content (ignore navigation, ads, sidebars, comments)
- Preserve content hierarchy and semantic relationships
- Maintain original meaning and context
- Extract comprehensive metadata for rich content elements
- Ensure structured output for downstream processing
- Never skip content elements - capture everything in the main article flow

QUALITY STANDARDS:
- Complete URL extraction (including file extensions)
- Sequential position numbering with no gaps
- Consistent HTML formatting throughout
- Comprehensive metadata for all block types"""
    
    def _get_output_format_specification(self) -> str:
        """Get detailed output format specification."""
        return """OUTPUT FORMAT: Return ONLY a JSON object with this exact structure:

STEP-BY-STEP PROCESSING:
1. Extract content blocks sequentially (position 0, 1, 2...)
2. For each block with formatting: convert to HTML tags
3. For each block with links: extract COMPLETE href values to metadata
4. For images: extract COMPLETE src URLs (including file extensions)
5. Validate: ensure all URLs are complete and not truncated

FORMATTING RULES:
- Bold: <strong>text</strong> (NOT **text**)
- Italic: <em>text</em> (NOT *text*)  
- Links: Extract href to metadata, keep plain text in content
- NEVER truncate URLs - always include complete paths and file extensions

{
  "content_blocks": [
    {
      "type": "heading|paragraph|image|quote|list|twitter_embed|video_embed|editorial_note",
      "content": "text with HTML formatting (NO markdown)",
      "level": "number for headings (1-6), null for others",
      "position": "sequential number starting from 0",
      "metadata": {
        // Type-specific metadata (see below)
      }
    }
  ],
  "author_information": {
    "primary_author": {
      "name": "Author full name",
      "title": "Job title if visible",
      "affiliation": "Publication name"
    },
    "byline_text": "Complete byline as it appears",
    "source_confidence": "high|low"
  },
  "extraction_metadata": {
    "total_blocks": "number",
    "estimated_word_count": "number",
    "has_headings": "boolean",
    "has_paragraphs": "boolean", 
    "has_images": "boolean",
    "has_lists": "boolean",
    "has_embeds": "boolean",
    "has_videos": "boolean",
    "has_editorial_notes": "boolean",
    "has_formatted_text": "boolean",
    "formatting_types": ["bold", "italic", "links"] // detected formatting types
  },
  "extraction_feedback": {
    "unmapped_content": [
      {
        "content_type": "Type of content found but not mapped",
        "description": "Brief description of the unmapped content",
        "sample_text": "Short sample of the content (max 100 chars)",
        "suggested_block_type": "Suggested new block type name",
        "frequency": "How often this type appeared (rare|occasional|frequent)"
      }
    ],
    "structural_observations": [
      "Observations about page structure, layout patterns, or content organization"
    ],
    "extraction_challenges": [
      "Specific challenges encountered during extraction (e.g., complex tables, unusual formatting)"
    ],
    "improvement_suggestions": [
      "Suggestions for improving the extraction system or templates"
    ],
    "confidence_notes": "Overall confidence in extraction quality and any concerns",
    "content_completeness": {
      "is_complete": "boolean - true if content appears complete, false if truncated",
      "truncation_indicators": [
        "List of signs suggesting content truncation (e.g., 'paywall detected', 'abrupt ending', 'continue reading prompt')"
      ],
      "confidence": "high|medium|low - confidence in completeness assessment",
      "estimated_completeness_percentage": "number 0-100 - rough estimate of content availability",
      "assessment_notes": "Brief explanation of the completeness assessment"
    }
  }
}

CONTENT BLOCK TYPES WITH FORMATTING:

1. HEADING (h1-h6):
   - content: heading text with HTML formatting (REQUIRED)
   - level: 1-6 (heading level) (REQUIRED)
   - position: sequential number (REQUIRED - start from 0)
   - metadata: {
       "has_formatting": boolean,
       "formatting_types": ["bold", "italic", "links"] // if applicable
     }

2. PARAGRAPH:
   - content: paragraph text with HTML formatting (REQUIRED)
   - position: sequential number (REQUIRED)
   - metadata: {
       "has_formatting": boolean,
       "formatting_types": ["bold", "italic", "links"], // detected formatting
       "link_count": number, // number of links in paragraph
       "external_links": [{"url": "url", "text": "link text", "domain": "domain"}] // external links only
     }

3. IMAGE:
   - content: image caption/description with HTML formatting (can be empty)
   - position: sequential number (REQUIRED)
   - metadata: {
       "src": "image full URL (REQUIRED, NO TRUNCATION)",
       "alt": "alt text",
       "caption": "figure caption with HTML formatting",
       "width": number,
       "height": number,
       "has_formatting": boolean
     }

4. VIDEO_EMBED (YouTube, Vimeo, etc.):
   - content: video title/description with HTML formatting (if available)
   - position: sequential number (REQUIRED)
   - metadata: {
       "src": "embed URL (REQUIRED)",
       "embed_type": "youtube|vimeo|other",
       "video_id": "extracted video ID",
       "thumbnail": "thumbnail URL if available",
       "has_formatting": boolean
     }

5. QUOTE (blockquotes, pullquotes):
   - content: quote text with HTML formatting (REQUIRED)
   - position: sequential number (REQUIRED)
   - metadata: {
       "cite": "attribution/source with HTML formatting",
       "type": "blockquote|pullquote",
       "has_formatting": boolean,
       "attribution_formatted": boolean
     }

6. LIST (ul/ol):
   - content: "" (empty)
   - position: sequential number (REQUIRED)
   - metadata: {
       "list_type": "ul|ol",
       "items": ["item 1 with <strong>formatting</strong>", "item 2 with <em>formatting</em>"], // with HTML
       "list_context": "what this list describes",
       "has_formatting": boolean,
       "formatted_items": boolean
     }

7. TWITTER_EMBED:
   - content: tweet text with HTML formatting (if available)
   - position: sequential number (REQUIRED)
   - metadata: {
       "tweet_id": "tweet ID",
       "embed_url": "twitter URL",
       "has_formatting": boolean
     }

8. EDITORIAL_NOTE (updates, corrections, editor notes):
   - content: editorial note text with HTML formatting (REQUIRED)
   - position: sequential number (REQUIRED)
   - metadata: {
       "note_type": "update|correction|editor_note",
       "timestamp": "timestamp if available",
       "has_formatting": boolean
     }

HTML FORMATTING RULES:
- **Bold text**: Use <strong>text</strong> for <strong> or <b> tags
- *Italic text*: Use <em>text</em> for <em> or <i> tags  
- **Links**: Store link information in metadata.external_links array, keep plain text in content
- **Combined formatting**: Use <strong><em>text</em></strong> for nested bold+italic
- **Code text**: Use <code>text</code> for <code> tags (if present)
- Preserve line breaks with proper spacing
- Maintain original paragraph structure

FORMATTING PRESERVATION EXAMPLES:
INPUT HTML: <p>This is <strong>bold</strong> and <em>italic</em> text with a <a href="https://example.com">link text</a>.</p>
OUTPUT: "This is <strong>bold</strong> and <em>italic</em> text with link text."
METADATA: external_links: [{"url": "https://example.com", "text": "link text", "domain": "example.com"}]

INPUT HTML: <blockquote>The <em>future</em> is <strong>now</strong>, according to <a href="/expert">Dr. Smith</a>.</blockquote>
OUTPUT: "The <em>future</em> is <strong>now</strong>, according to Dr. Smith."
METADATA: external_links: [{"url": "/expert", "text": "Dr. Smith", "domain": "internal"}]

CRITICAL REQUIREMENTS:
- EVERY block MUST have a "position" field with sequential numbers (0, 1, 2, ...)
- PRESERVE all inline formatting using HTML tags
- Extract ALL main content, not just summaries
- Include comprehensive metadata for rich content
- Track formatting presence in metadata
- Convert HTML formatting to consistent HTML tags
- Do not include any explanation or commentary outside the JSON"""

    def _get_extraction_guidelines(self) -> str:
        """Get content extraction guidelines."""
        return """EXTRACTION GUIDELINES:

INCLUDE:
✓ Main article headlines and subheadings
✓ All body paragraphs with full text and formatting
✓ Article content inline images with captions and metadata
✓ Article content blockquotes and pullquotes
✓ Ordered and unordered lists with formatted items
✓ Embedded tweets and social media
✓ Embedded videos and audio
✓ Figure captions and photo credits
✓ All inline formatting (bold, italic, links, code)

EXCLUDE:
✗ Navigation menus and breadcrumbs
✗ Advertisement content
✗ Sidebar content and related, recommended, or similar articles
✗ Comment sections
✗ Footer information
✗ Cookie notices and popups
✗ Social sharing buttons
✗ Sign up, newsletter, or other subscription calls to action
✗ Author bio sections (unless part of article)

CONTENT PRESERVATION WITH FORMATTING:
- Maintain original text without summarization
- PRESERVE ALL INLINE FORMATTING using HTML tags
- Convert HTML formatting to consistent HTML tags
- Preserve paragraph breaks and structure
- Keep important formatting context and semantic meaning
- Extract complete list items with their formatting
- Include full quote text with attribution formatting
- Maintain link relationships and preserve link text

FORMATTING CONVERSION RULES:

1. BOLD TEXT:
   - Convert <strong>text</strong> → <strong>text</strong> (preserve)
   - Convert <b>text</b> → <strong>text</strong> (normalize)
   - Handle nested bold in quotes, headings, captions

2. ITALIC TEXT:
   - Convert <em>text</em> → <em>text</em> (preserve)
   - Convert <i>text</i> → <em>text</em> (normalize)
   - Handle nested italic in quotes, headings, captions

3. LINKS:
   - Extract link information to external_links metadata
   - Store plain link text in content: <a href="url">text</a> → text
   - CRITICAL: Always extract the full href attribute value from <a> tags
   - Include link metadata: {"url": "complete_href_value", "text": "link_text", "domain": "domain_name"}
   - Make relative URLs absolute when possible using article base URL
   - Handle links within formatted text: <em><a href="url">text</a></em> → <em>text</em>

4. COMBINED FORMATTING:
   - <strong><em>text</em></strong> → <strong><em>text</em></strong>
   - <em><strong>text</strong></em> → <strong><em>text</em></strong>
   - Links within formatting: extract link to metadata, preserve surrounding formatting

5. CODE TEXT (if present):
   - Convert <code>text</code> → <code>text</code> (preserve)
   - Handle inline code within paragraphs

6. LINE BREAKS:
   - Preserve meaningful paragraph breaks
   - Convert <br> to appropriate spacing
   - Maintain list structure and spacing

FORMATTING IN DIFFERENT CONTENT TYPES:

HEADINGS:
- Preserve formatting in heading text: <h2>The <em>Future</em> of <strong>Technology</strong></h2>
- Output: "The <em>Future</em> of <strong>Technology</strong>"
- Track formatting in metadata: has_formatting: true

PARAGRAPHS:
- Convert all inline formatting to HTML
- Extract link information to metadata
- Count formatting elements for metadata
- Example: "Scientists have made a <strong>breakthrough</strong> discovery that changes everything." (with link in metadata)

QUOTES:
- Preserve formatting in quote text and attribution
- Handle formatted citations: "said Dr. Smith" (with link in metadata)
- Maintain quote structure with embedded formatting

LISTS:
- Format each list item with HTML
- Handle links and emphasis within list items
- Example items: ["<strong>Important</strong> finding", "Read more details", "See <em>additional research</em>"]

IMAGE CAPTIONS:
- Preserve formatting in caption text
- Handle photo credits with links and emphasis
- Example: "Photo credit: <em>John Doe</em>" (with link in metadata)

METADATA EXTRACTION:
- Complete image URLs (make absolute if relative)
- Accurate alt text and captions with formatting preserved
- Proper list structure (ul vs ol) with formatted items
- Twitter embed identification with formatted content
- Link analysis: count, domains, internal vs external
- Formatting tracking: types present, frequency, complexity

LINK HANDLING SPECIFICS:
- Extract ALL links within content
- ALWAYS capture the complete href attribute value from <a> tags
- Store link text without surrounding formatting in content
- Store complete link information in external_links metadata with full URLs
- Identify external links (different domain) for metadata
- Handle relative links (make absolute when base URL available)
- Track link density and types (internal, external, social media)
- Special handling for social media links, references, citations
- NEVER leave url field empty - if href is present, extract it completely

FORMATTING QUALITY CHECKS:
- Ensure consistent HTML syntax
- Verify link URLs are complete and valid
- Check for properly closed HTML tags
- Validate nested formatting combinations
- Maintain readability while preserving semantics

HEADING HIERARCHY & SUBHEADINGS:
- Identify and preserve the complete heading hierarchy (h1-h6)
- H1: Usually the main article title - include if different from article metadata title
- H2-H3: Primary subheadings that break up main content sections  
- H4-H6: Secondary subheadings within sections
- PRESERVE all formatting within headings using HTML
- CONTEXT: Consider the semantic meaning - subheadings should relate to the content they introduce
- SKIP: Navigation headings, sidebar headings, "Related Articles", "More Stories", etc.
- PRESERVE: Original heading text exactly as written by the author WITH formatting

AUTHOR INFORMATION EXTRACTION:
- Extract author name from byline areas ("By [Name]", "Written by [Name]")
- Include job title if visible (Staff Writer, Reporter, etc.)
- Capture complete byline text as it appears WITH formatting
- Note multiple authors if present
- Skip generic bylines like "Staff Report" or organization names
- Confidence: high for clear bylines, low for unclear/missing
- Handle linked author names: "By John Smith" (with link in metadata)

EXTRACTION FEEDBACK:
- Report content types you encounter that don't fit current block types
- Note unusual page structures or layout patterns
- Identify extraction challenges (complex tables, interactive elements, etc.)
- Suggest new block types for unmapped content
- Provide improvement suggestions for better extraction
- Give overall confidence assessment and concerns
- Report formatting complexity and conversion challenges

CONTENT COMPLETENESS ASSESSMENT:
- Evaluate if the article content appears complete or truncated
- TRUNCATION INDICATORS to look for:
  • Paywall messages ("Subscribe to continue", "Sign in to read more")
  • Abrupt content endings (sentences cut off mid-thought)
  • "Continue reading" or "Read more" prompts
  • Login/registration requirements embedded in content
  • Subscription offers interrupting article flow
  • Content that ends without natural conclusion
  • Missing typical article elements (no conclusion, incomplete quotes)
  • Teaser text followed by access restrictions
- COMPLETENESS SIGNS to look for:
  • Natural article conclusion or summary
  • Complete quotes and paragraphs
  • Full author bylines and publication info
  • Typical article structure (intro, body, conclusion)
  • No obvious content gaps or interruptions
- Estimate completeness percentage based on content flow and structure
- High confidence: clear indicators present, Medium: some signs but ambiguous, Low: difficult to assess

QUALITY STANDARDS:
- Minimum 85% content completeness
- Accurate content block typing
- Proper hierarchical structure
- Complete metadata for rich content
- Consistent HTML formatting conversion
- Preserved semantic meaning and readability
- Valid JSON structure"""


class ContentExtractionTemplateV2(BaseExtractionTemplate):
    """
    Enhanced content extraction template (v2.0).
    
    Supports all content types including lists and social media embeds.
    Includes comprehensive metadata extraction and few-shot examples.
    """
    
    def _get_identifier(self) -> str:
        return "content_extraction_v2"
    
    def _get_version(self) -> str:
        return "2.0"
    
    def format(self, preprocessed_html: str, article_metadata: Dict[str, Any]) -> str:
        """Format comprehensive extraction prompt with examples."""
        system_prompt = self._get_system_prompt()
        
        task_prompt = """TASK: Extract ALL main article content sequentially and structure it into comprehensive semantic content blocks.

CRITICAL REQUIREMENTS:
- EXTRACT EVERY content element from the article (do not skip any paragraphs, headings, images, etc.)
- ASSIGN sequential position numbers starting from 0 (0, 1, 2, 3, ...)
- PROCESS content in reading order (top to bottom as it appears)
- INCLUDE complete URLs without truncation

SUPPORTED CONTENT TYPES: heading, paragraph, image, quote, list, twitter_embed, video_embed, editorial_note

TARGET: 15-30+ content blocks for typical articles (ensure completeness)"""
        
        output_format = self._get_output_format_specification()
        extraction_guidelines = self._get_extraction_guidelines()
        examples = self._get_few_shot_examples()
        
        user_prompt = f"""Extract content from this preprocessed HTML:

ARTICLE METADATA:
Title: {article_metadata.get('title', 'Unknown')}
URL: {article_metadata.get('url', 'Unknown')}
Source: {article_metadata.get('source', 'Unknown')}

HTML CONTENT:
{preprocessed_html}

EXTRACTION PROCESS:
1. Scan the entire HTML content from start to finish
2. Identify ALL content elements (headings, paragraphs, images, quotes, lists, embeds)
3. Extract each element in reading order with sequential positions (0, 1, 2, ...)
4. Preserve all formatting using HTML tags (<strong>, <em>, <code>)
5. Extract all URLs completely without truncation
6. Return comprehensive JSON with all content blocks

VALIDATION CHECKLIST:
✓ All content elements extracted (none skipped)
✓ Position numbers are sequential (0, 1, 2, 3, ...)
✓ All URLs are complete with file extensions
✓ HTML formatting preserved (not markdown)
✓ All required metadata fields present

Return the structured content blocks as JSON following the specified format and examples."""
        
        return f"{system_prompt}\n\n{task_prompt}\n\n{output_format}\n\n{extraction_guidelines}\n\n{examples}\n\n{user_prompt}"
    
    def _get_few_shot_examples(self) -> str:
        """Get few-shot examples for better extraction quality."""
        return """EXTRACTION EXAMPLES:

Example 1 - Basic Article Structure with Formatting:
INPUT HTML:
<article>
  <h1>Breaking News: <em>Major</em> Discovery</h1>
  <p>Scientists have made a <strong>groundbreaking</strong> discovery that could <a href="https://example.com/research">change everything</a>.</p>
  <figure>
    <img src="/images/discovery.jpg" alt="Laboratory equipment">
    <figcaption>Scientists <em>working</em> in the lab. Photo by <a href="https://photographer.com/profile">John Doe</a></figcaption>
  </figure>
  <h2>Key Findings</h2>
  <ul>
    <li><strong>First</strong> major finding</li>
    <li>Second <em>important</em> result with <a href="https://journal.com/details">more details</a></li>
  </ul>
  <blockquote>
    "<em>This changes our understanding</em> <strong>completely</strong>," said <a href="https://university.edu/expert">Dr. Smith</a>.
  </blockquote>
</article>

OUTPUT JSON:
{
  "content_blocks": [
    {
      "type": "heading",
      "content": "Breaking News: <em>Major</em> Discovery",
      "level": 1,
      "position": 0,
      "metadata": {
        "has_formatting": true,
        "formatting_types": ["italic"]
      }
    },
    {
      "type": "paragraph",
      "content": "Scientists have made a <strong>groundbreaking</strong> discovery that could change everything.",
      "level": null,
      "position": 1,
      "metadata": {
        "has_formatting": true,
        "formatting_types": ["bold", "links"],
        "link_count": 1,
        "external_links": [{"url": "https://example.com/research", "text": "change everything", "domain": "example.com"}]
      }
    },
    {
      "type": "image",
      "content": "Scientists <em>working</em> in the lab. Photo by John Doe",
      "level": null,
      "position": 2,
      "metadata": {
        "src": "/images/discovery.jpg",
        "alt": "Laboratory equipment",
        "caption": "Scientists <em>working</em> in the lab. Photo by John Doe",
        "has_formatting": true,
        "external_links": [{"url": "/photographer", "text": "John Doe", "domain": "internal"}]
      }
    },
    {
      "type": "heading",
      "content": "Key Findings",
      "level": 2,
      "position": 3,
      "metadata": {
        "has_formatting": false,
        "formatting_types": []
      }
    },
    {
      "type": "list",
      "content": "",
      "level": null,
      "position": 4,
      "metadata": {
        "list_type": "ul",
        "items": ["<strong>First</strong> major finding", "Second <em>important</em> result with more details"],
        "has_formatting": true,
        "formatted_items": true,
        "external_links": [{"url": "/details", "text": "more details", "domain": "internal"}]
      }
    },
    {
      "type": "quote",
      "content": "\"<em>This changes our understanding</em> <strong>completely</strong>,\" said Dr. Smith.",
      "level": null,
      "position": 5,
      "metadata": {
        "has_formatting": true,
        "attribution_formatted": true,
        "external_links": [{"url": "/expert", "text": "Dr. Smith", "domain": "internal"}]
      }
    }
  ],
  "extraction_metadata": {
    "total_blocks": 6,
    "estimated_word_count": 55,
    "has_headings": true,
    "has_paragraphs": true,
    "has_images": true,
    "has_lists": true,
    "has_embeds": false,
    "has_formatted_text": true,
    "formatting_types": ["bold", "italic", "links"]
  }
}

Example 2 - Complex Formatting:
INPUT HTML:
<p>The <strong><em>revolutionary</em></strong> study found that <code>AI systems</code> can <a href="https://research.com"><strong>dramatically improve</strong></a> outcomes.</p>

OUTPUT JSON:
{
  "content_blocks": [
    {
      "type": "paragraph",
      "content": "The <strong><em>revolutionary</em></strong> study found that <code>AI systems</code> can dramatically improve outcomes.",
      "level": null,
      "position": 0,
      "metadata": {
        "has_formatting": true,
        "formatting_types": ["bold", "italic", "links", "code"],
        "link_count": 1,
        "external_links": [{"url": "https://research.com", "text": "dramatically improve", "domain": "research.com"}]
      }
    }
  ],
  "extraction_metadata": {
    "total_blocks": 1,
    "estimated_word_count": 15,
    "has_headings": false,
    "has_paragraphs": true,
    "has_images": false,
    "has_lists": false,
    "has_embeds": false,
    "has_formatted_text": true,
    "formatting_types": ["bold", "italic", "links", "code"]
  }
}

Example 3 - Twitter Embed with Formatting:
INPUT HTML:
<blockquote class="twitter-tweet">
  <p>Exciting news about our <strong>latest research</strong>! Read more: <a href="https://example.com">here</a> #science</p>
  <a href="https://twitter.com/scientist/status/1234567890">@scientist</a>
</blockquote>

OUTPUT JSON:
{
  "content_blocks": [
    {
      "type": "twitter_embed",
      "content": "Exciting news about our <strong>latest research</strong>! Read more: here #science",
      "level": null,
      "position": 0,
      "metadata": {
        "tweet_id": "1234567890",
        "embed_url": "https://twitter.com/scientist/status/1234567890",
        "has_formatting": true,
        "external_links": [{"url": "https://example.com", "text": "here", "domain": "example.com"}]
      }
    }
  ],
  "extraction_metadata": {
    "total_blocks": 1,
    "estimated_word_count": 10,
    "has_headings": false,
    "has_paragraphs": false,
    "has_images": false,
    "has_lists": false,
    "has_embeds": true,
    "has_formatted_text": true,
    "formatting_types": ["bold", "links"]
  }
}

Follow these examples for structure, format consistency, and proper HTML conversion.

LINK EXTRACTION PROTOCOL (CRITICAL):
For EACH <a> tag found:
1. Extract the COMPLETE href attribute value (never truncate)
2. Extract the link text (content between <a> tags)  
3. Determine domain from href (external vs internal)
4. Store in external_links array as separate entries
5. Replace link in content with plain text only

LINK EXTRACTION EXAMPLES:
<a href="https://example.com/article">read more</a> + <a href="https://other.com/page">details</a>
→ content: "read more details"
→ external_links: [
    {"url": "https://example.com/article", "text": "read more", "domain": "example.com"},
    {"url": "https://other.com/page", "text": "details", "domain": "other.com"}
  ]

IMAGE URL PROTOCOL (CRITICAL):
- Extract COMPLETE src attribute including file extension (.jpg, .png, etc.)
- NEVER truncate URLs - include full path and filename  
- Example: "https://site.com/path/image-12345.jpg" (complete)
- NOT: "https://site.com/path/image-123..." (truncated)

FORMATTING VALIDATION:
- Use <strong>bold</strong> NOT **bold**
- Use <em>italic</em> NOT *italic*
- Store links in metadata NOT [text](url)  
- Include complete URLs with extensions"""


class AlgorithmicExtractionTemplate(BaseExtractionTemplate):
    """
    Algorithmic content extraction template (v3.0).
    
    Features:
    - XML-like visual structure for clarity
    - Step-by-step algorithmic processing instructions
    - Self-checking and validation mechanisms
    - HTML-first formatting approach
    - Progressive disclosure of complexity
    - Consistent visual patterns throughout
    """
    
    def _get_identifier(self) -> str:
        return "algorithmic_extraction_v3"
    
    def _get_version(self) -> str:
        return "3.0"
    
    def format(self, preprocessed_html: str, article_metadata: Dict[str, Any]) -> str:
        """Format algorithmic extraction prompt with clear structure."""
        system_prompt = self._get_system_prompt()
        
        extraction_algorithm = self._get_extraction_algorithm()
        output_format = self._get_structured_output_format()
        content_types = self._get_content_type_definitions()
        formatting_protocol = self._get_html_formatting_protocol()
        examples = self._get_structured_examples()
        
        user_prompt = f"""EXTRACT CONTENT FROM THIS HTML:

ARTICLE METADATA:
Title: {article_metadata.get('title', 'Unknown')}
URL: {article_metadata.get('url', 'Unknown')}
Source: {article_metadata.get('source', 'Unknown')}

HTML CONTENT:
{preprocessed_html}

EXTRACTION REQUIREMENTS (MANDATORY):
1. Extract ALL main content elements (TARGET: 20-40+ blocks for full articles)
2. Process in reading order with sequential positions (0, 1, 2, 3...) - NO GAPS
3. Use HTML formatting (<strong>, <em>) not markdown
4. Extract complete URLs with file extensions  
5. Include comprehensive metadata for each block
6. CRITICAL: Output readable characters, NOT HTML entities (use ' not &#39;, use " not &#8220;)
7. EXTRACT EVERYTHING: All headings, all paragraphs, all images, all lists, all embeds
8. NO SELECTIVITY: Do not skip "minor" content - extract it all

VALIDATION CHECKLIST:
✓ COMPLETENESS: 20-40+ blocks extracted
✓ ALL HEADINGS: Every h1, h2, h3, h4, h5, h6 in article body
✓ ALL PARAGRAPHS: Every paragraph with 4+ meaningful words
✓ ALL IMAGES: Every article image with complete URL
✓ ALL LISTS: Every ul, ol with content items
✓ ALL EMBEDS: Every video, twitter / x, iframe, blockquote
✓ ALL LINKS: Every <a href="..."> extracted to metadata.external_links
✓ SEQUENTIAL POSITIONS: 0, 1, 2, 3... (no gaps, no jumps, all blocks in correct position, no positions swapped)
✓ VISUAL ORDER: Content appears in same order as in original article (embeds not moved to end)
✓ HTML FORMATTING: <strong>, <em> throughout (no markdown)
✓ COMPLETE URLS: Full URLs with file extensions
✓ READABLE CHARACTERS: ', " not &#39;, &#8220;
✓ DETAILED FEEDBACK: Comprehensive extraction_feedback with observations, challenges, and suggestions

Return only the JSON object following the examples above. No code blocks, no commentary."""
        
        return f"{system_prompt}\n\n{extraction_algorithm}\n\n{output_format}\n\n{content_types}\n\n{formatting_protocol}\n\n{examples}\n\n{user_prompt}"
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt with clear mission."""
        return """You are an expert content extraction specialist with deep knowledge of web publishing, journalism, and HTML structure. Your task is to extract clean, structured content from web articles while preserving semantic meaning and proper formatting.

EXTRACTION MINDSET:
- Be COMPREHENSIVE: Extract every piece of main content (aim for 15-30+ blocks)
- Be SYSTEMATIC: Process content sequentially from top to bottom
- Be PRECISE: Use exact position numbers (0, 1, 2, 3, ...) with no gaps
- Be CONSISTENT: Always use HTML formatting (<strong>, <em>) never markdown

CORE PRINCIPLES:
- Focus only on main article content (ignore navigation, ads, sidebars, comments, content notices, etc.)
- Preserve content hierarchy and semantic relationships
- Extract ALL content elements - never skip paragraphs, headings, images
- Use HTML formatting: <strong>bold</strong>, <em>italic</em> (NOT markdown)
- Extract complete URLs without truncation"""
    
    def _get_extraction_algorithm(self) -> str:
        """Get step-by-step algorithmic processing instructions."""
        return """🔥 AGGRESSIVE COMPREHENSIVE EXTRACTION PROCESS 🔥

🚨 EXTRACTION MANDATE: You MUST extract ALL content blocks. NO SKIPPING. NO SELECTIVITY.
🔗 CRITICAL: Extract ALL links and put them in metadata.external_links (this is currently broken - FIX IT!)

STEP 1: SYSTEMATIC CONTENT INVENTORY
• Scan ENTIRE HTML document from top to bottom - MISS NOTHING
• Count ALL content elements and record what you find:
  - Count ALL <h1>, <h2>, <h3>, <h4>, <h5>, <h6> tags
  - Count ALL <p> paragraphs with substantial text (4+ words)
  - Count ALL <img> tags with article images (not ads/logos)
  - Count ALL <ul>, <ol> lists with content items
  - Count ALL <blockquote> quotes and pullquotes
  - Count ALL <iframe>, <video> embeds in article body
  - Count ALL editorial notes, updates, corrections
• TARGET: Expect 20-40+ blocks for typical full articles
• VERIFY: Your final count should match what you found

STEP 1.5: EMBED POSITION MAPPING (CRITICAL FOR CORRECT ORDERING)
• Scan article from top to bottom and NOTE where each embed appears
• Record EXACT CONTEXT for videos, tweets, iframes in reading flow
• Example mapping: "Twitter embed appears after 'Nintendo didn't respond' paragraph, before 'similar leak happened' paragraph"
• This position context will be used in Step 2 for precise placement
• DO NOT extract content yet - just map positions

STEP 2: EXHAUSTIVE EXTRACTION (STRICT VISUAL ORDER)
• Process content LINEARLY from top to bottom - NO exceptions
• CRITICAL: Extract each element WHEN you encounter it in the HTML flow
• DO NOT skip complex elements to process later - handle them immediately
• Extract ALL headings (h1-h6) - even if they seem similar
• Extract ALL paragraphs - even short ones with 4+ meaningful words
• Extract ALL images with captions - miss none
• Extract ALL lists - even small 2-item lists
• Extract ALL quotes and blockquotes
• Extract ALL video/iframe/twitter embeds using the position mapping from Step 1.5
• ASSIGN EMBED POSITIONS: Use the context noted in Step 1.5 to place embeds correctly
• FORBIDDEN: Moving embeds, videos, or tweets to different positions
• Assign sequential positions: 0, 1, 2, 3, ... based on the position mapping
• Convert ALL formatting to HTML: <strong>bold</strong>, <em>italic</em>

STEP 3: COMPREHENSIVE VALIDATION & FEEDBACK
• COUNT YOUR EXTRACTED BLOCKS: Should be 20-40+ for full articles
• VERIFY NOTHING SKIPPED: Go back and double-check you got everything
• CHECK SEQUENTIAL POSITIONS: 0, 1, 2, 3... no gaps or jumps
• VALIDATE EMBED POSITIONS: Ensure embeds match the context mapping from Step 1.5
• VALIDATE ALL URLs: Complete with file extensions
• CONFIRM HTML FORMATTING: No markdown syntax anywhere
• IDENTIFY UNMAPPED CONTENT: Note any content that couldn't be mapped to blocks
• ASSESS STRUCTURAL PATTERNS: Observe layout and organization patterns
• DOCUMENT CHALLENGES: Record any extraction difficulties encountered
• SUGGEST IMPROVEMENTS: Recommend template or system enhancements

🎯 EXTRACTION TARGETS (MINIMUM STANDARDS):
✓ 20-40+ content blocks for full articles (NOT 10-15)
✓ ALL headings extracted (h1, h2, h3, h4, h5, h6)
✓ ALL paragraphs extracted (even short ones)
✓ ALL images extracted with complete URLs
✓ ALL lists extracted (even 2-item lists)
✓ Sequential positions with NO gaps
✓ 95%+ completeness - extract virtually everything

⚠️ RED FLAGS (FAILURE INDICATORS):
❌ Only extracting 10-15 blocks (too selective)
❌ Missing obvious headings or paragraphs
❌ Skipping short content elements
❌ Incomplete URL extraction
❌ Non-sequential position numbers
❌ Embeds/tweets appearing at end instead of their original position
❌ Processing content "out of order" for any reason

🔥 REMEMBER: Be COMPREHENSIVE, not selective. Extract MORE, not less."""
    
    def _get_structured_output_format(self) -> str:
        """Get the structured JSON output format."""
        return """<<<OUTPUT FORMAT>>>
🚨 CRITICAL JSON RULES:
1. Return ONLY a raw JSON object. NO markdown formatting. NO code blocks.
2. Escape ALL quotes inside content strings using \"
3. Escape ALL backslashes using \\\\
4. Remove any line breaks inside content strings (replace with space)
5. Validate JSON syntax before returning

❌ WRONG: ```json { ... } ```
❌ WRONG: ```{ ... }```  
❌ WRONG: "content": "He said "hello" there"
❌ WRONG: "content": "Line 1\nLine 2"
✅ CORRECT: { ... }
✅ CORRECT: "content": "He said \\"hello\\" there"
✅ CORRECT: "content": "Line 1 Line 2"

🔍 JSON VALIDATION CHECKLIST:
- All quotes inside strings are escaped with \"
- No unescaped line breaks in strings
- All brackets and braces are properly paired
- No trailing commas in objects or arrays
- All property names are in double quotes

REQUIRED JSON STRUCTURE:
{
  "content_blocks": [
    {
      "type": "content_type_name",
      "content": "HTML formatted text with escaped quotes",
      "level": "number_or_null",
      "position": "sequential_number",
      "metadata": {
        // Type-specific metadata (see content types below)
      }
    }
  ],
  "author_information": {
    "primary_author": {
      "name": "Author full name",
      "title": "Job title if visible", 
      "affiliation": "Publication name"
    },
    "byline_text": "Complete byline as appears",
    "source_confidence": "high|low"
  },
  "extraction_metadata": {
    "total_blocks": 0,
    "estimated_word_count": 0,
    "has_headings": false,
    "has_paragraphs": false,
    "has_images": false,
    "has_lists": false,
    "has_embeds": false,
    "has_videos": false,
    "has_editorial_notes": false,
    "has_formatted_text": false,
    "formatting_types": []
  },
  "extraction_feedback": {
    "unmapped_content": [
      {
        "content_type": "Type of content found but not mapped",
        "description": "Brief description of the unmapped content", 
        "sample_text": "Short sample of the content (max 100 chars)",
        "suggested_block_type": "Suggested new block type name",
        "frequency": "How often this type appeared (rare|occasional|frequent)"
      }
    ],
    "structural_observations": [
      "Observations about page structure, layout patterns, or content organization"
    ],
    "extraction_challenges": [
      "Specific challenges encountered during extraction (e.g., complex tables, unusual formatting)"
    ],
    "improvement_suggestions": [
      "Suggestions for improving the extraction system or templates"
    ],
    "confidence_notes": "Overall confidence in extraction quality and any concerns",
    "content_completeness": {
      "is_complete": true,
      "truncation_indicators": [
        "List of signs suggesting content truncation (e.g., 'paywall detected', 'abrupt ending', 'continue reading prompt')"
      ],
      "confidence": "high|medium|low",
      "estimated_completeness_percentage": 95,
      "assessment_notes": "Brief explanation of the completeness assessment"
    }
  }
}

🎯 REMEMBER: 
- Output starts with { and ends with }. Nothing else.
- Escape all quotes in content as \"
- Remove line breaks from content strings
- Validate JSON syntax before returning
<<<END FORMAT>>>"""
    
    def _get_content_type_definitions(self) -> str:
        """Get systematic content type definitions."""
        return """<<<CONTENT TYPES>>>
Each content type follows this consistent pattern:

### 📰 HEADING (h1-h6)
✅ INCLUDE: Article headings and subheadings with HTML formatting
🎯 FORMAT: content="<strong>Breaking</strong> News", level=1-6, position=sequential
🚫 EXCLUDE: Navigation headings, "Related Articles", sidebar headings, newsletter and signup calls to action, recommended articles, suggested reading, etc.
📝 METADATA: {"has_formatting": boolean, "formatting_types": []}

### 📄 PARAGRAPH  
✅ INCLUDE: Main body text with complete sentences and HTML formatting
🎯 FORMAT: content="Text with <strong>bold</strong> and <em>italic</em>"
🚫 EXCLUDE: Navigation text, ad copy, sidebar content, newsletter and signup calls to action, commission text, author byline (should be in author_information and metadata), article date and timestamp, suggested reading, empty paragraphs or with meaningless characters, etc.

### 🖼️ IMAGE
✅ INCLUDE: Article images with captions and complete URLs
🎯 FORMAT: content="Caption with <em>formatting</em>", metadata with full src
🚫 EXCLUDE: Ad images, profile photos, logos, navigation icons
📝 METADATA: {"src": "COMPLETE_URL.jpg", "alt": "text", "caption": "HTML"}

### 💬 QUOTE (blockquotes, pullquotes)
✅ INCLUDE: Direct quotes, blockquotes with HTML formatting  
🎯 FORMAT: content="\"<em>Quote</em> text,\" said Author."
🚫 EXCLUDE: Social media quotes (use twitter_embed instead)
📝 METADATA: {"cite": "attribution", "type": "blockquote|pullquote"}

### 📝 LIST (ul/ol)
✅ INCLUDE: Article lists with formatted items
🎯 FORMAT: content="", metadata.items=["<strong>Item</strong> 1", "Item 2"]
🚫 EXCLUDE: Navigation menus, tag lists, related links
📝 METADATA: {"list_type": "ul|ol", "items": [], "formatted_items": boolean}

### 🐦 TWITTER_EMBED
✅ INCLUDE: Embedded tweets relevant to article content, usually in <iframe> tags
🎯 FORMAT: content="Tweet text with <strong>formatting</strong>"
🚫 EXCLUDE: Social sharing buttons, follow prompts
📝 METADATA: {"tweet_id": "id", "embed_url": "url"}
⚠️ CRITICAL: Extract twitter embeds in their EXACT visual position, not at the end

### 🎥 VIDEO_EMBED
✅ INCLUDE: YouTube, Vimeo, and other video embeds in article
🎯 FORMAT: content="Video title/description"
🚫 EXCLUDE: Advertisement videos, auto-play elements
📝 METADATA: {"src": "embed_url", "embed_type": "youtube|vimeo|other"}

### ✏️ EDITORIAL_NOTE
✅ INCLUDE: Updates, corrections, editor's notes with timestamps
🎯 FORMAT: content="<strong>Update 1/27/25:</strong> Additional information..."
🚫 EXCLUDE: Bylines, publication info, copyright notices
📝 METADATA: {"note_type": "update|correction|editor_note", "timestamp": "text"}
<<<END CONTENT TYPES>>>"""
    
    def _get_html_formatting_protocol(self) -> str:
        """Get HTML formatting conversion protocol."""
        return """<<<HTML FORMATTING PROTOCOL>>>
Convert all text formatting to standard HTML tags. Follow these patterns exactly:

### 🔤 TEXT FORMATTING RULES
✅ BOLD: <strong>text</strong> (convert from <b>, <strong>, **text**)
✅ ITALIC: <em>text</em> (convert from <i>, <em>, *text*)  
✅ CODE: <code>text</code> (preserve <code> tags)
✅ NESTED: <strong><em>bold italic</em></strong>
🚫 NEVER: **bold**, *italic*, [text](url) markdown syntax

### 🔗 REAL LINK PROCESSING PROTOCOL (CRITICAL)
For each <a href="URL">text</a> found in the source HTML:

🚨 STEP 1: Extract REAL href value from HTML source (NEVER invent URLs)
✅ FIND: <a href="https://example.com/real-article">link text</a>
✅ EXTRACT: "https://example.com/real-article" (the actual href)
🚫 NEVER: Create fake URLs like "https://kotaku.com/fake-link"

🚨 STEP 2: Extract actual link text content
✅ EXTRACT: "link text" from <a>link text</a>

🚨 STEP 3: Determine domain from REAL href  
✅ EXTERNAL: Different domain → "example.com"
✅ INTERNAL: Same domain or relative → "internal"

🚨 STEP 4: Store REAL URL and remove link from content
✅ CONTENT: "Scientists found evidence. Read the article here."
✅ METADATA: external_links: [{"url": "https://example.com/real-article", "text": "Read the article", "domain": "example.com"}]

🚨 ABSOLUTELY CRITICAL:
- Only use href values that actually exist in the HTML source
- Never invent or create URLs
- If you can't find the real href, don't include the link in metadata

### 🖼️ IMAGE URL PROTOCOL
✅ EXTRACT: Complete src attribute with file extension
✅ EXAMPLE: "https://site.com/images/photo-20250127.jpg"
🚫 NEVER: Truncate or abbreviate URLs
🚫 NEVER: "https://site.com/images/photo-2025..."

### ✅ QUALITY CHECKS
Before finalizing each block:
• Is URL complete with file extension?
• Are HTML tags properly closed?
• Is position number sequential?
• Are required fields present?
• Is formatting consistent throughout?
• Did I use REAL href values (not invented ones)?
<<<END PROTOCOL>>>"""
    
    def _get_structured_examples(self) -> str:
        """Get concrete few-shot examples following V2 proven patterns."""
        return """EXTRACTION EXAMPLES:

Example 1 - Basic Article Structure with Formatting:
INPUT HTML:
<article>
  <h1>Breaking News: <em>Major</em> Discovery</h1>
  <p>Scientists have made a <strong>groundbreaking</strong> discovery that could <a href="https://example.com/research">change everything</a>.</p>
  <figure>
    <img src="/images/discovery.jpg" alt="Laboratory equipment">
    <figcaption>Scientists <em>working</em> in the lab. Photo by <a href="https://photographer.com/profile">John Doe</a></figcaption>
  </figure>
  <h2>Key Findings</h2>
  <ul>
    <li><strong>First</strong> major finding</li>
    <li>Second <em>important</em> result with <a href="https://journal.com/details">more details</a></li>
  </ul>
  <blockquote>
    "<em>This changes our understanding</em> <strong>completely</strong>," said <a href="https://university.edu/expert">Dr. Smith</a>.
  </blockquote>
</article>

OUTPUT JSON:
{
  "content_blocks": [
    {
      "type": "heading",
      "content": "Breaking News: <em>Major</em> Discovery",
      "level": 1,
      "position": 0,
      "metadata": {
        "has_formatting": true,
        "formatting_types": ["italic"]
      }
    },
    {
      "type": "paragraph",
      "content": "Scientists have made a <strong>groundbreaking</strong> discovery that could change everything.",
      "level": null,
      "position": 1,
      "metadata": {
        "has_formatting": true,
        "formatting_types": ["bold", "links"],
        "link_count": 1,
        "external_links": [{"url": "https://example.com/research", "text": "change everything", "domain": "example.com"}]
      }
    },
    {
      "type": "image",
      "content": "Scientists <em>working</em> in the lab. Photo by John Doe",
      "level": null,
      "position": 2,
      "metadata": {
        "src": "/images/discovery.jpg",
        "alt": "Laboratory equipment",
        "caption": "Scientists <em>working</em> in the lab. Photo by John Doe",
        "has_formatting": true,
        "external_links": [{"url": "https://photographer.com/profile", "text": "John Doe", "domain": "photographer.com"}]
      }
    },
    {
      "type": "heading",
      "content": "Key Findings",
      "level": 2,
      "position": 3,
      "metadata": {
        "has_formatting": false,
        "formatting_types": []
      }
    },
    {
      "type": "list",
      "content": "",
      "level": null,
      "position": 4,
      "metadata": {
        "list_type": "ul",
        "items": ["<strong>First</strong> major finding", "Second <em>important</em> result with more details"],
        "has_formatting": true,
        "formatted_items": true,
        "external_links": [{"url": "https://journal.com/details", "text": "more details", "domain": "journal.com"}]
      }
    },
    {
      "type": "quote",
      "content": "\"<em>This changes our understanding</em> <strong>completely</strong>,\" said Dr. Smith.",
      "level": null,
      "position": 5,
      "metadata": {
        "has_formatting": true,
        "attribution_formatted": true,
        "external_links": [{"url": "https://university.edu/expert", "text": "Dr. Smith", "domain": "university.edu"}]
      }
    }
  ],
  "extraction_metadata": {
    "total_blocks": 6,
    "estimated_word_count": 55,
    "has_headings": true,
    "has_paragraphs": true,
    "has_images": true,
    "has_lists": true,
    "has_embeds": false,
    "has_formatted_text": true,
    "formatting_types": ["bold", "italic", "links"]
  }
}

Example 2 - Complex Formatting:
INPUT HTML:
<p>The <strong><em>revolutionary</em></strong> study found that <code>AI systems</code> can <a href="https://research.com"><strong>dramatically improve</strong></a> outcomes.</p>

OUTPUT JSON:
{
  "content_blocks": [
    {
      "type": "paragraph",
      "content": "The <strong><em>revolutionary</em></strong> study found that <code>AI systems</code> can dramatically improve outcomes.",
      "level": null,
      "position": 0,
      "metadata": {
        "has_formatting": true,
        "formatting_types": ["bold", "italic", "links", "code"],
        "link_count": 1,
        "external_links": [{"url": "https://research.com", "text": "dramatically improve", "domain": "research.com"}]
      }
    }
  ],
  "extraction_metadata": {
    "total_blocks": 1,
    "estimated_word_count": 15,
    "has_headings": false,
    "has_paragraphs": true,
    "has_images": false,
    "has_lists": false,
    "has_embeds": false,
    "has_formatted_text": true,
    "formatting_types": ["bold", "italic", "links", "code"]
  }
}

KEY PATTERNS TO FOLLOW:
✅ Position numbers: Sequential (0, 1, 2, 3, ...)
✅ HTML formatting: <strong>, <em> tags preserved
✅ Links: Extracted to metadata, plain text in content
✅ Complete URLs: Include file extensions
✅ Comprehensive extraction: All content blocks captured"""


# Template registry - simplified to single template
EXTRACTION_TEMPLATES = {
    "content_extraction_v2": ContentExtractionTemplateV2,
    "algorithmic_extraction_v3": AlgorithmicExtractionTemplate,
}

# Default template
DEFAULT_TEMPLATE = "algorithmic_extraction_v3"


def get_extraction_template(template_id: Optional[str] = None) -> BaseExtractionTemplate:
    """
    Get extraction template instance following quality evaluation patterns.
    
    Args:
        template_id: Template identifier, or None for default
        
    Returns:
        Template instance
        
    Raises:
        ValueError: If template_id is not found
    """
    if template_id is None:
        template_id = DEFAULT_TEMPLATE
    
    if template_id not in EXTRACTION_TEMPLATES:
        available = ", ".join(EXTRACTION_TEMPLATES.keys())
        raise ValueError(f"Unknown template '{template_id}'. Available: {available}")
    
    template_class = EXTRACTION_TEMPLATES[template_id]
    return template_class()


def get_available_templates() -> List[str]:
    """
    Get list of available template identifiers.
    
    Returns:
        List of template identifiers
    """
    return list(EXTRACTION_TEMPLATES.keys())


def get_template_info(template_id: str) -> Dict[str, str]:
    """
    Get template information.
    
    Args:
        template_id: Template identifier
        
    Returns:
        Dictionary with template metadata
        
    Raises:
        ValueError: If template_id is not found
    """
    if template_id not in EXTRACTION_TEMPLATES:
        available = ", ".join(EXTRACTION_TEMPLATES.keys())
        raise ValueError(f"Unknown template '{template_id}'. Available: {available}")
    
    template = get_extraction_template(template_id)
    return {
        "identifier": template.identifier,
        "version": template.version,
        "operation": template.operation,
        "class_name": template.__class__.__name__
    } 