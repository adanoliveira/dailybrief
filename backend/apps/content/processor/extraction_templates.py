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


class AlgorithmicExtractionTemplate:
    """
    Algorithmic content extraction template (v3.0).
    
    Features:
    - Step-by-step algorithmic processing instructions
    - Two-phase extraction with embed position mapping
    - Self-checking and validation mechanisms
    - HTML-first formatting approach
    - Progressive disclosure of complexity
    - Consistent visual patterns throughout
    """
    
    def __init__(self):
        """Initialize template with metadata."""
        self.identifier = "algorithmic_extraction_v3"
        self.version = "3.0"
        self.operation = "content_extraction"
    
    def format(self, preprocessed_html: str, article_metadata: Dict[str, Any]) -> str:
        """Format algorithmic extraction prompt with clear structure."""
        system_prompt = self._get_system_prompt()
        
        extraction_algorithm = self._get_extraction_algorithm()
        output_format = self._get_structured_output_format()
        content_types = self._get_content_type_definitions()
        recommended_exclusions = self._get_recommended_content_exclusions()
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
✓ ALL HEADINGS: Every structural h1, h2, h3, h4, h5, h6 in article body (NOT article subtitles)
✓ ALL SUBTITLES: Lead paragraphs/subtitles that provide context to main title (positions 0-2)
✓ ALL PARAGRAPHS: Body text paragraphs with 4+ meaningful words (positions 3+)
✓ ALL IMAGES: Every article image with complete URL
✓ ALL LISTS: Every ul, ol with content items
✓ ALL EMBEDS: Every video, twitter / x, iframe, blockquote
✓ ALL LINKS: Every <a href="..."> kept in content AND stored in metadata.links
✓ SEQUENTIAL POSITIONS: 0, 1, 2, 3... (no gaps, no jumps, all blocks in correct position, no positions swapped)
✓ VISUAL ORDER: Content appears in same order as in original article (embeds not moved to end)
✓ HTML FORMATTING: <strong>, <em> throughout (no markdown)
✓ COMPLETE URLS: Full URLs with file extensions
✓ READABLE CHARACTERS: ', " not &#39;, &#8220;
✓ DETAILED FEEDBACK: Comprehensive extraction_feedback with observations, challenges, and suggestions

Return only the JSON object following the examples above. No code blocks, no commentary."""
        
        return f"{system_prompt}\n\n{extraction_algorithm}\n\n{output_format}\n\n{content_types}\n\n{recommended_exclusions}\n\n{formatting_protocol}\n\n{examples}\n\n{user_prompt}"
    
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
🔗 CRITICAL: Extract ALL links as HTML <a> tags in content AND store them in metadata.links (this format is required for frontend rendering!)

STEP 1: SYSTEMATIC CONTENT INVENTORY
• Scan ENTIRE HTML document from top to bottom - MISS NOTHING
• EXTRACT CLEAN TITLE: Find main article title and create clean version (remove publication name like "- Kotaku", "- The Verge")
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
• Record EXACT CONTEXT for images, videos, tweets, iframes in reading flow
• Example mapping: "Twitter embed appears after 'Nintendo didn't respond' paragraph, before 'similar leak happened' paragraph"
• This position context will be used in Step 2 for precise placement
• DO NOT extract content yet - just map positions

STEP 2: EXHAUSTIVE EXTRACTION (STRICT VISUAL ORDER)
• Process content LINEARLY from top to bottom - NO exceptions
• CRITICAL: Extract each element WHEN you encounter it in the HTML flow
• DO NOT skip complex elements to process later - handle them immediately
• Extract ALL structural headings (h1-h6) that organize content sections
• Extract ALL subtitles/lead paragraphs (early positions 0-2, provide context to title)
• Extract ALL body paragraphs (later positions 3+, main article content)
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

🧠 CONTENT TYPE DECISION GUIDE:
📍 POSITION 0-2 (Early in article):
   • Main title → extracted_title (not a content block)
   • Subtitle/lead that elaborates on title → "subtitle" type
   • Author byline → author_information (not a content block)
   
📍 POSITION 3+ (Article body):
   • Structural section headings (h1-h6) → "heading" type with level
   • Body text paragraphs → "paragraph" type
   • Images with captions → "image" type
   • Lists → "list" type
   • Quotes → "quote" type

🎯 KEY DISTINCTION:
   • SUBTITLE: "Scientists have discovered a new species that could change marine biology"
   • PARAGRAPH: "The research team used advanced sonar equipment to map the ocean floor..."
   • HEADING: "Research Methodology" or "Key Findings"

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
    "extracted_title": "Clean article title without publication name or formatting",
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
✅ INCLUDE: Structural headings that organize article sections (h1, h2, h3, h4, h5, h6)
🎯 FORMAT: content="<strong>Breaking</strong> News", level=1-6, position=sequential
🚫 EXCLUDE: 
    • Navigation menus and section headers
    • "Related Articles" and "Recommended Reading" sections
    • Sidebar widgets and supplementary content headers
    • Newsletter signup prompts and subscription CTAs
    • Article title (extract as title metadata)
    • Article subtitles (use subtitle type)
    • "Editor's Picks" and "Featured Stories" sections
    • Social sharing headers and engagement prompts
    • Footer navigation and site map headers
⚠️ CRITICAL: Do NOT use for article subtitles/lead paragraphs - those should be "subtitle" type
📝 METADATA: {"has_formatting": boolean, "formatting_types": []}

### 📝 SUBTITLE (article subtitle/lead)
✅ INCLUDE: Article subtitles, lead paragraphs, deck text that provides context to the main title
🎯 FORMAT: content="Text that elaborates on the main title with <em>formatting</em>"
🎯 POSITION: Usually appears early in article (positions 0-2), right after main title
🎯 CHARACTERISTICS: Longer than headings, shorter than full paragraphs, descriptive, contextual
✅ EXAMPLES: "Scientists discover new species in deep ocean that could change our understanding of marine life"
✅ EXAMPLES: "The breakthrough comes after years of research and could lead to new treatments"
🚫 EXCLUDE: Regular paragraphs, structural headings, body text, author bylines
⚠️ CRITICAL: Use this instead of "paragraph" for lead/subtitle content that needs special formatting
📝 METADATA: {"has_formatting": boolean, "formatting_types": [], "is_lead": true}

### 📄 PARAGRAPH  
✅ INCLUDE: Main body text paragraphs with complete sentences and HTML formatting (preserve all <br> tags)
🎯 FORMAT: content="Text with <strong>bold</strong> and <em>italic</em>"
🎯 POSITION: Usually after subtitle/lead content (positions 3+)
🎯 CHARACTERISTICS: Full sentences, substantial content, part of article body flow
🚫 EXCLUDE: 
    • Navigation elements and menu text
    • Advertisement content and promotional copy
    • Sidebar widgets and supplementary content
    • Newsletter signup forms and subscription prompts
    • Commission disclosure text and affiliate notices
    • Author bylines and biographical information (extract as author_information)
    • Author role descriptions and credentials
    • Publication dates and timestamps (use metadata)
    • "Suggested reading" and "Related articles" sections
    • Empty paragraphs or those containing only whitespace/special characters
    • Article subtitles and lead paragraphs (use subtitle type)
    • Inline article recommendations and cross-promotional content
⚠️ CRITICAL: Do NOT use for article subtitles/lead content - those should be "subtitle" type
📝 METADATA: {"has_formatting": boolean, "formatting_types": []}

### 🖼️ IMAGE
✅ INCLUDE: Article images that are:
    • Larger than 200x200 pixels
    • Have complete, valid image URLs
    • Are positioned within the main article content flow (especially near heading/subtitle for primary images)
    • Have ANY of the following indicators:
      - Descriptive alt text or captions relating to article content
      - Attribution credits (e.g., "Photo by...", "Credit:...")
      - Large size (>800px width) suggesting primary article imagery
      - Positioned early in article structure (first 3-5 content blocks)
🎯 FORMAT: content="Caption with <em>formatting</em>", metadata with full src
🚫 EXCLUDE: 
    • Advertisements and promotional images (often in sidebars or clearly marked as ads)
    • Profile pictures and author headshots (especially when <200x200px or near bylines)
    • Brand logos and navigation icons (typically small and in headers/footers)
    • UI elements and social media buttons (share icons, platform buttons)
    • Newsletter signup illustrations and subscription graphics
    • Clearly decorative images (patterns, dividers, background graphics)
    • Images in recommended/related article sections
    ⚠️ NOTE: When in doubt for large images (>500px) positioned within article flow, INCLUDE rather than exclude
📝 METADATA: {"src": "COMPLETE_URL.jpg", "alt": "text", "caption": "HTML"}

### 💬 QUOTE (blockquotes, pullquotes)
✅ INCLUDE: Direct quotes, blockquotes with HTML formatting (preserve all <br> tags)
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
    
    def _get_recommended_content_exclusions(self) -> str:
        """Get specific guidance for excluding recommended/related content."""
        return """<<<RECOMMENDED CONTENT EXCLUSIONS>>>
🚨 CRITICAL: Do NOT extract recommended/related article content that breaks the main article flow.

### 🚫 EXCLUDE THESE PATTERNS:
❌ SECTION HEADERS:
    • "Editor's Picks"
    • "Recommended"
    • "Suggested Reading"
    • "See Also"
    • "You May Also Like"
    • "Related Stories"
    • "More from [Publication]"
    • "Don't Miss"
    • "Trending Now"
    • "Popular Stories"
    • "Featured Content"
    • "Must Read"
    • "From Our Archives"
    • "Recommended for You"
    • "Similar Articles"
    • "What to Read Next"
    • "More Stories Like This"
    • "You Might Also Enjoy"
    • "From Around the Web"
❌ INLINE RECOMMENDATIONS: Sudden topic shifts to unrelated articles within paragraphs
❌ CONTENT BREAKS: Sections that interrupt article flow with different topics/stories
❌ PROMOTIONAL BLOCKS: "Subscribe to newsletter", "Follow us", "Download our app", "Sign up", "Newsletter"

### 🎯 IDENTIFICATION SIGNALS:
• Content appears in separate divs/sections from main article
• Topics suddenly shift from main article subject
• Contains publication calls-to-action or subscription prompts
• Includes phrases like "Read more:", "Check out:", "Don't miss:"
• Lists multiple unrelated article titles

### ✅ WHAT TO DO:
• Skip these sections entirely - do not extract as any content type
• Continue extraction with the next main article content
• Maintain sequential position numbering (skip over excluded content)

🎯 FOCUS: Extract only content that serves the main article's narrative and purpose.
<<<END EXCLUSIONS>>>"""
    
    def _get_html_formatting_protocol(self) -> str:
        """Get HTML formatting conversion protocol."""
        return """<<<HTML FORMATTING PROTOCOL>>>
Convert all text formatting to standard HTML tags. Follow these patterns exactly:

### 🔤 TEXT FORMATTING RULES
✅ BOLD: <strong>text</strong> (convert from <b>, <strong>, **text**)
✅ ITALIC: <em>text</em> (convert from <i>, <em>, *text*)  
✅ LINKS: <a href="url">text</a> (keep in content AND store in metadata.links)
✅ CODE: <code>text</code> (preserve <code> tags)
✅ LINE BREAKS: <br> (preserve line breaks in quotes, paragraphs, lists, and structured content)
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

🚨 STEP 4: Keep links as HTML AND store in metadata
✅ CONTENT: "Scientists found evidence. <a href=\"https://example.com/real-article\">Read the article here</a>."
✅ METADATA: links: [{"text": "Read the article here", "href": "https://example.com/real-article"}]

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
      "type": "subtitle",
      "content": "New research reveals unprecedented insights into marine biodiversity",
      "level": null,
      "position": 1,
      "metadata": {
        "has_formatting": false,
        "formatting_types": [],
        "is_lead": true
      }
    },
    {
      "type": "image",
      "content": "Scientists <em>working</em> in the lab. Photo by <a href=\"https://photographer.com/profile\">John Doe</a>",
      "level": null,
      "position": 2,
      "metadata": {
        "src": "/images/discovery.jpg",
        "alt": "Laboratory equipment",
        "caption": "Scientists <em>working</em> in the lab. Photo by John Doe",
        "has_formatting": true,
        "links": [{"text": "John Doe", "href": "https://photographer.com/profile"}]
      }
    },
    {
      "type": "paragraph",
      "content": "Scientists have made a <strong>groundbreaking</strong> discovery that could <a href=\"https://example.com/research\">change everything</a>.",
      "level": null,
      "position": 1,
      "metadata": {
        "has_formatting": true,
        "formatting_types": ["bold", "links"],
        "is_lead": true,
        "links": [{"text": "change everything", "href": "https://example.com/research"}]
      }
    },
    {
      "type": "heading",
      "content": "Key Findings",
      "level": 2,
      "position": 4,
      "metadata": {
        "has_formatting": false,
        "formatting_types": []
      }
    },
    {
      "type": "list",
      "content": "",
      "level": null,
      "position": 5,
      "metadata": {
        "list_type": "ul",
        "items": ["<strong>First</strong> major finding", "Second <em>important</em> result with <a href=\"https://journal.com/details\">more details</a>"],
        "has_formatting": true,
        "formatted_items": true,
        "links": [{"text": "more details", "href": "https://journal.com/details"}]
      }
    },
    {
      "type": "quote",
      "content": "\"<em>This changes our understanding</em> <strong>completely</strong>,\" said <a href=\"https://university.edu/expert\">Dr. Smith</a>.",
      "level": null,
      "position": 6,
      "metadata": {
        "has_formatting": true,
        "attribution_formatted": true,
        "links": [{"text": "Dr. Smith", "href": "https://university.edu/expert"}]
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
      "content": "The <strong><em>revolutionary</em></strong> study found that <code>AI systems</code> can <a href=\"https://research.com\">dramatically improve</a> outcomes.",
      "level": null,
      "position": 0,
              "metadata": {
          "has_formatting": true,
          "formatting_types": ["bold", "italic", "links", "code"],
          "links": [{"text": "dramatically improve", "href": "https://research.com"}]
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


# Template registry - using only the proven algorithmic template
EXTRACTION_TEMPLATES = {
    "algorithmic_extraction_v3": AlgorithmicExtractionTemplate,
}

# Default template
DEFAULT_TEMPLATE = "algorithmic_extraction_v3"


def get_extraction_template(template_id: Optional[str] = None) -> AlgorithmicExtractionTemplate:
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