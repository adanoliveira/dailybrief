"""
Content Block Builder - AI Response to ContentBlock Conversion.

This module converts AI extraction JSON responses to ContentBlock objects,
following the same validation and conversion patterns used in the quality
evaluation system for consistent and reliable object creation.

Responsibilities:
- JSON response validation and sanitization
- ContentBlock object creation and validation
- Type-specific metadata handling
- Error handling and logging
"""
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

from .models import ContentBlock


logger = logging.getLogger(__name__)


class ContentBlockBuilder:
    """
    Converts AI extraction JSON responses to ContentBlock objects.
    
    Follows the same validation and conversion patterns as quality evaluation
    for consistent and reliable object creation. Provides comprehensive
    validation for each content block type.
    """
    
    # Valid content block types
    VALID_BLOCK_TYPES = {
        "heading", "paragraph", "image", "img", "figure", "quote", "list", "twitter_embed", "video_embed", "editorial_note"
    }
    
    # Valid list types
    VALID_LIST_TYPES = {"ul", "ol"}
    
    def __init__(self):
        """Initialize the content block builder."""
        self.validation_errors = []
    
    def build_blocks(self, blocks_data: List[dict]) -> List[ContentBlock]:
        """
        Convert AI JSON response to ContentBlock objects.
        
        Args:
            blocks_data: List of content block dictionaries from AI response
            
        Returns:
            List of validated ContentBlock objects
        """
        self.validation_errors = []
        content_blocks = []
        
        if not isinstance(blocks_data, list):
            logger.error("Blocks data is not a list")
            return content_blocks
        
        for i, block_data in enumerate(blocks_data):
            try:
                # Validate and build individual block
                block = self._build_single_block(block_data, i)
                if block:
                    content_blocks.append(block)
                    
            except Exception as e:
                logger.error(f"Error building content block {i}: {e}")
                self.validation_errors.append(f"Block {i}: {e}")
                continue
        
        # Log validation summary
        if self.validation_errors:
            logger.warning(f"Content block validation errors: {len(self.validation_errors)} errors")
            for error in self.validation_errors[:5]:  # Log first 5 errors
                logger.warning(f"  - {error}")
        
        logger.info(f"Successfully built {len(content_blocks)} content blocks from {len(blocks_data)} AI blocks")
        return content_blocks
    
    def _build_single_block(self, block_data: dict, position: int) -> Optional[ContentBlock]:
        """
        Build a single ContentBlock from AI JSON data.
        
        Args:
            block_data: Content block dictionary from AI response
            position: Position index for error reporting
            
        Returns:
            ContentBlock object or None if validation fails
        """
        if not isinstance(block_data, dict):
            self.validation_errors.append(f"Block {position}: Not a dictionary")
            return None
        
        # Extract and validate basic fields
        block_type = block_data.get("type")
        if not self._validate_block_type(block_type, position):
            return None
        

        
        # Extract content and metadata
        content = self._extract_content(block_data, block_type, position)
        level = self._extract_level(block_data, block_type, position)
        metadata = self._extract_metadata(block_data, block_type, position)
        block_position = block_data.get("position", position)
        
        # Validate extracted data
        if not self._validate_block_data(block_type, content, level, metadata, position):
            return None
        
        # Create and return ContentBlock
        try:
            return ContentBlock(
                type=block_type,
                content=content,
                level=level,
                position=block_position,
                metadata=metadata
            )
        except Exception as e:
            self.validation_errors.append(f"Block {position}: Error creating ContentBlock: {e}")
            return None
    
    def _validate_block_type(self, block_type: str, position: int) -> bool:
        """
        Validate content block type.
        
        Args:
            block_type: Block type from AI response
            position: Position for error reporting
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(block_type, str):
            self.validation_errors.append(f"Block {position}: Type is not a string")
            return False
        
        if block_type not in self.VALID_BLOCK_TYPES:
            self.validation_errors.append(f"Block {position}: Invalid type '{block_type}'")
            return False
        
        return True
    

    def _extract_content(self, block_data: dict, block_type: str, position: int) -> str:
        """
        Extract and clean content text from block data.
        
        Args:
            block_data: Block data dictionary
            block_type: Type of content block
            position: Position for error reporting
            
        Returns:
            Cleaned content string
        """
        from html import unescape
        
        content = block_data.get("content", "")
        
        if not isinstance(content, str):
            logger.warning(f"Block {position}: Content is not a string, converting")
            content = str(content) if content is not None else ""
        
        # Clean and normalize content
        content = content.strip()
        
        # Remove excessive whitespace
        content = " ".join(content.split())
        
        # Decode HTML entities to ensure readable characters
        content = unescape(content)
        
        return content
    
    def _extract_level(self, block_data: dict, block_type: str, position: int) -> Optional[int]:
        """
        Extract and validate heading level.
        
        Args:
            block_data: Block data dictionary
            block_type: Type of content block
            position: Position for error reporting
            
        Returns:
            Heading level (1-6) for headings, None for other types
        """
        if block_type != "heading":
            return None
        
        level = block_data.get("level")
        
        if level is None:
            self.validation_errors.append(f"Block {position}: Heading missing level")
            return 1  # Default to h1
        
        if not isinstance(level, int):
            try:
                level = int(level)
            except (ValueError, TypeError):
                self.validation_errors.append(f"Block {position}: Invalid heading level '{level}'")
                return 1
        
        # Validate level range
        if not (1 <= level <= 6):
            self.validation_errors.append(f"Block {position}: Heading level {level} out of range (1-6)")
            level = max(1, min(6, level))  # Clamp to valid range
        
        return level
    
    def _extract_metadata(self, block_data: dict, block_type: str, position: int) -> Dict[str, Any]:
        """
        Extract and validate metadata based on block type.
        
        Args:
            block_data: Block data dictionary
            block_type: Type of content block
            position: Position for error reporting
            
        Returns:
            Validated metadata dictionary
        """
        raw_metadata = block_data.get("metadata", {})
        
        if not isinstance(raw_metadata, dict):
            self.validation_errors.append(f"Block {position}: Metadata is not a dictionary")
            raw_metadata = {}
        
        # Type-specific metadata validation and extraction
        if block_type in ["image", "img", "figure"]:
            return self._extract_image_metadata(raw_metadata, position)
        elif block_type == "list":
            return self._extract_list_metadata(raw_metadata, position)
        elif block_type == "twitter_embed":
            return self._extract_twitter_metadata(raw_metadata, position)
        elif block_type == "video_embed":
            return self._extract_video_metadata(raw_metadata, position)
        elif block_type == "paragraph":
            return self._extract_paragraph_metadata(raw_metadata, position)
        elif block_type == "quote":
            return self._extract_quote_metadata(raw_metadata, position)
        elif block_type == "editorial_note":
            return self._extract_editorial_metadata(raw_metadata, position)
        else:
            # For headings and other types, return cleaned metadata
            return self._clean_generic_metadata(raw_metadata)
    
    def _extract_image_metadata(self, metadata: dict, position: int) -> Dict[str, Any]:
        """
        Extract and validate image metadata.
        
        Args:
            metadata: Raw metadata dictionary
            position: Position for error reporting
            
        Returns:
            Validated image metadata
        """
        cleaned_metadata = {}
        
        # Required: src
        src = metadata.get("src", "")
        if not isinstance(src, str) or not src.strip():
            self.validation_errors.append(f"Block {position}: Image missing or invalid src")
            src = ""
        else:
            # Validate and clean URL
            src = self._clean_url(src.strip())
            if not src:
                self.validation_errors.append(f"Block {position}: Image src is not a valid URL")
        
        cleaned_metadata["src"] = src
        
        # Optional: alt text
        alt = metadata.get("alt", "")
        if isinstance(alt, str):
            cleaned_metadata["alt"] = alt.strip()
        
        # Optional: caption
        caption = metadata.get("caption", "")
        if isinstance(caption, str):
            cleaned_metadata["caption"] = caption.strip()
        
        # Optional: width and height
        for dimension in ["width", "height"]:
            value = metadata.get(dimension)
            if value is not None:
                try:
                    cleaned_metadata[dimension] = int(value)
                except (ValueError, TypeError):
                    logger.warning(f"Block {position}: Invalid image {dimension}: {value}")
        
        return cleaned_metadata
    
    def _extract_list_metadata(self, metadata: dict, position: int) -> Dict[str, Any]:
        """
        Extract and validate list metadata.
        
        Args:
            metadata: Raw metadata dictionary
            position: Position for error reporting
            
        Returns:
            Validated list metadata
        """
        cleaned_metadata = {}
        
        # Required: items
        items = metadata.get("items", [])
        if not isinstance(items, list):
            self.validation_errors.append(f"Block {position}: List items is not a list")
            items = []
        
        # Clean and validate list items
        cleaned_items = []
        for i, item in enumerate(items):
            if isinstance(item, str):
                cleaned_item = item.strip()
                if cleaned_item:
                    cleaned_items.append(cleaned_item)
            else:
                logger.warning(f"Block {position}: List item {i} is not a string")
        
        cleaned_metadata["items"] = cleaned_items
        
        # Required: list_type
        list_type = metadata.get("list_type", "ul")
        if list_type not in self.VALID_LIST_TYPES:
            self.validation_errors.append(f"Block {position}: Invalid list type '{list_type}'")
            list_type = "ul"  # Default to unordered
        
        cleaned_metadata["list_type"] = list_type
        
        return cleaned_metadata
    
    def _extract_twitter_metadata(self, metadata: dict, position: int) -> Dict[str, Any]:
        """
        Extract and validate Twitter embed metadata.
        
        Args:
            metadata: Raw metadata dictionary
            position: Position for error reporting
            
        Returns:
            Validated Twitter metadata
        """
        cleaned_metadata = {}
        
        # Required: tweet_id
        tweet_id = metadata.get("tweet_id", "")
        if not isinstance(tweet_id, str) or not tweet_id.strip():
            self.validation_errors.append(f"Block {position}: Twitter embed missing tweet_id")
            tweet_id = ""
        else:
            # Clean tweet ID (remove any non-numeric characters except for status URLs)
            tweet_id = tweet_id.strip()
            
            # Extract tweet ID from various formats
            if "status/" in tweet_id:
                # Extract from URL format
                try:
                    tweet_id = tweet_id.split("status/")[1].split("?")[0].split("/")[0]
                except IndexError:
                    self.validation_errors.append(f"Block {position}: Cannot extract tweet ID from URL")
                    tweet_id = ""
            
            # Validate tweet ID format (should be numeric)
            if tweet_id and not tweet_id.isdigit():
                logger.warning(f"Block {position}: Tweet ID may not be valid: {tweet_id}")
        
        cleaned_metadata["tweet_id"] = tweet_id
        
        # Optional: embed_url
        embed_url = metadata.get("embed_url", "")
        if isinstance(embed_url, str) and embed_url.strip():
            embed_url = self._clean_url(embed_url.strip())
            if embed_url:
                cleaned_metadata["embed_url"] = embed_url
        
        return cleaned_metadata
    
    def _extract_video_metadata(self, metadata: dict, position: int) -> Dict[str, Any]:
        """
        Extract and validate video metadata.
        
        Args:
            metadata: Raw metadata dictionary
            position: Position for error reporting
            
        Returns:
            Validated video metadata
        """
        cleaned_metadata = {}
        
        # Required: src (embed URL)
        src = metadata.get("src", "")
        if not isinstance(src, str) or not src.strip():
            self.validation_errors.append(f"Block {position}: Video embed missing src")
            src = ""
        else:
            # Validate and clean URL
            src = self._clean_url(src.strip())
            if not src:
                self.validation_errors.append(f"Block {position}: Video embed src is not a valid URL")
        
        cleaned_metadata["src"] = src
        
        # Optional: embed_type
        embed_type = metadata.get("embed_type", "")
        if isinstance(embed_type, str) and embed_type.strip():
            embed_type = embed_type.strip().lower()
            if embed_type in ["youtube", "vimeo", "other"]:
                cleaned_metadata["embed_type"] = embed_type
            else:
                # Try to detect embed type from URL
                if "youtube" in src or "youtu.be" in src:
                    cleaned_metadata["embed_type"] = "youtube"
                elif "vimeo" in src:
                    cleaned_metadata["embed_type"] = "vimeo"
                else:
                    cleaned_metadata["embed_type"] = "other"
        elif src:
            # Auto-detect from URL
            if "youtube" in src or "youtu.be" in src:
                cleaned_metadata["embed_type"] = "youtube"
            elif "vimeo" in src:
                cleaned_metadata["embed_type"] = "vimeo"
            else:
                cleaned_metadata["embed_type"] = "other"
        
        # Optional: video_id
        video_id = metadata.get("video_id", "")
        if isinstance(video_id, str) and video_id.strip():
            cleaned_metadata["video_id"] = video_id.strip()
        elif src and not video_id:
            # Try to extract video ID from URL
            if "youtube" in src:
                # Extract YouTube video ID
                import re
                youtube_match = re.search(r'(?:youtube\.com/embed/|youtu\.be/|v=)([a-zA-Z0-9_-]+)', src)
                if youtube_match:
                    cleaned_metadata["video_id"] = youtube_match.group(1)
        
        # Optional: thumbnail
        thumbnail = metadata.get("thumbnail", "")
        if isinstance(thumbnail, str) and thumbnail.strip():
            thumbnail_url = self._clean_url(thumbnail.strip())
            if thumbnail_url:
                cleaned_metadata["thumbnail"] = thumbnail_url
        
        return cleaned_metadata
    
    def _extract_paragraph_metadata(self, metadata: dict, position: int) -> Dict[str, Any]:
        """
        Extract and validate paragraph metadata.
        
        Args:
            metadata: Raw metadata dictionary
            position: Position for error reporting
            
        Returns:
            Validated paragraph metadata
        """
        cleaned_metadata = {}
        
        # Optional: links
        links = metadata.get("links", [])
        if isinstance(links, list):
            cleaned_links = []
            for link in links:
                if isinstance(link, dict) and "href" in link:
                    href = self._clean_url(str(link["href"]))
                    if href:
                        cleaned_link = {"href": href}
                        if "text" in link:
                            cleaned_link["text"] = str(link["text"]).strip()
                        cleaned_links.append(cleaned_link)
            
            if cleaned_links:
                cleaned_metadata["links"] = cleaned_links
        
        return cleaned_metadata
    
    def _extract_quote_metadata(self, metadata: dict, position: int) -> Dict[str, Any]:
        """
        Extract and validate quote metadata.
        
        Args:
            metadata: Raw metadata dictionary
            position: Position for error reporting
            
        Returns:
            Validated quote metadata
        """
        cleaned_metadata = {}
        
        # Optional: cite (source attribution)
        cite = metadata.get("cite", "")
        if isinstance(cite, str) and cite.strip():
            cleaned_metadata["cite"] = cite.strip()
        
        # Optional: type (pullquote, blockquote, etc.)
        quote_type = metadata.get("type", "")
        if isinstance(quote_type, str) and quote_type.strip():
            cleaned_metadata["type"] = quote_type.strip()
        
        return cleaned_metadata
    
    def _extract_editorial_metadata(self, metadata: dict, position: int) -> Dict[str, Any]:
        """
        Extract and validate editorial note metadata.
        
        Args:
            metadata: Raw metadata dictionary
            position: Position for error reporting
            
        Returns:
            Validated editorial note metadata
        """
        cleaned_metadata = {}
        
        # Optional: note_type
        note_type = metadata.get("note_type", "")
        if isinstance(note_type, str) and note_type.strip():
            note_type = note_type.strip().lower()
            if note_type in ["update", "correction", "editor_note"]:
                cleaned_metadata["note_type"] = note_type
            else:
                # Try to auto-detect note type from content
                cleaned_metadata["note_type"] = "editor_note"  # Default
        
        # Optional: timestamp
        timestamp = metadata.get("timestamp", "")
        if isinstance(timestamp, str) and timestamp.strip():
            cleaned_metadata["timestamp"] = timestamp.strip()
        
        return cleaned_metadata
    
    def _clean_generic_metadata(self, metadata: dict) -> Dict[str, Any]:
        """
        Clean generic metadata for basic content types.
        
        Args:
            metadata: Raw metadata dictionary
            
        Returns:
            Cleaned metadata dictionary
        """
        cleaned_metadata = {}
        
        # Copy safe string values
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                if isinstance(value, str):
                    value = value.strip()
                    if value:  # Only add non-empty strings
                        cleaned_metadata[key] = value
                else:
                    cleaned_metadata[key] = value
        
        return cleaned_metadata
    
    def _validate_block_data(
        self, 
        block_type: str, 
        content: str, 
        level: Optional[int], 
        metadata: Dict[str, Any], 
        position: int
    ) -> bool:
        """
        Final validation of extracted block data.
        
        Args:
            block_type: Content block type
            content: Extracted content
            level: Heading level (if applicable)
            metadata: Extracted metadata
            position: Position for error reporting
            
        Returns:
            True if valid, False otherwise
        """
        # Type-specific validation
        if block_type == "heading":
            if level is None or not (1 <= level <= 6):
                self.validation_errors.append(f"Block {position}: Invalid heading level")
                return False
            if not content:
                self.validation_errors.append(f"Block {position}: Heading has no content")
                return False
            # Enhanced: Validate heading context and semantic meaning
            if not self._validate_heading_context(content, level, position):
                return False
        
        elif block_type == "paragraph":
            if not content:
                self.validation_errors.append(f"Block {position}: Paragraph has no content")
                return False
        
        elif block_type == "image":
            if not metadata.get("src"):
                self.validation_errors.append(f"Block {position}: Image has no src")
                return False
        
        elif block_type == "list":
            items = metadata.get("items", [])
            if not items:
                self.validation_errors.append(f"Block {position}: List has no items")
                return False
        
        elif block_type == "quote":
            if not content:
                self.validation_errors.append(f"Block {position}: Quote has no content")
                return False
        
        elif block_type == "twitter_embed":
            if not metadata.get("tweet_id"):
                self.validation_errors.append(f"Block {position}: Twitter embed has no tweet_id")
                return False
        
        elif block_type == "video_embed":
            if not metadata.get("src"):
                self.validation_errors.append(f"Block {position}: Video embed has no src")
                return False
        
        elif block_type == "editorial_note":
            if not content:
                self.validation_errors.append(f"Block {position}: Editorial note has no content")
                return False
        
        return True
    
    def _clean_url(self, url: str) -> str:
        """
        Clean and validate URL.
        
        Args:
            url: Raw URL string
            
        Returns:
            Cleaned URL or empty string if invalid
        """
        if not url:
            return ""
        
        try:
            # Parse URL to validate structure
            parsed = urlparse(url)
            
            # Must have scheme and netloc for absolute URLs
            if parsed.scheme and parsed.netloc:
                return url
            
            # Handle relative URLs (start with /)
            if url.startswith("/"):
                return url
            
            # Handle protocol-relative URLs
            if url.startswith("//"):
                return url
            
            # Try adding https:// if it looks like a domain
            if "." in url and " " not in url:
                test_url = f"https://{url}"
                test_parsed = urlparse(test_url)
                if test_parsed.netloc:
                    return test_url
            
            return ""
            
        except Exception:
            return ""
    
    def get_validation_errors(self) -> List[str]:
        """
        Get validation errors from the last build operation.
        
        Returns:
            List of validation error messages
        """
        return self.validation_errors.copy()
    
    def _validate_heading_context(self, content: str, level: int, position: int) -> bool:
        """
        Validate that a heading makes semantic sense in the article context.
        
        Args:
            content: Heading text content
            level: Heading level (1-6)
            position: Position in the content flow
            
        Returns:
            True if heading appears to be legitimate article content
        """
        if not content or len(content.strip()) < 3:
            return False
        
        content_lower = content.lower().strip()
        
        # Skip obvious navigation/sidebar headings
        navigation_patterns = [
            "related articles", "more stories", "trending now", "popular posts",
            "you might like", "recommended", "latest news", "more from",
            "subscribe", "newsletter", "follow us", "share this", "tags",
            "categories", "recent posts", "archive", "advertisement",
            "sponsored content", "also read", "see also", "don't miss"
        ]
        
        for pattern in navigation_patterns:
            if pattern in content_lower:
                self.validation_errors.append(
                    f"Block {position}: Heading '{content[:50]}...' appears to be navigation/sidebar content"
                )
                return False
        
        # Skip very short headings that are likely navigation
        if len(content.strip()) < 8 and level > 2:
            self.validation_errors.append(
                f"Block {position}: Heading '{content}' is too short for level h{level}"
            )
            return False
        
        # Validate heading level makes sense for position
        if level == 1 and position > 3:
            # H1 after position 3 is unusual - might be a mistake
            self.validation_errors.append(
                f"Block {position}: H1 heading at position {position} is unusual - verify content hierarchy"
            )
        
        return True
    
    def analyze_heading_hierarchy(self, content_blocks: List[ContentBlock]) -> Dict[str, Any]:
        """
        Analyze the heading hierarchy structure of the extracted content.
        
        Args:
            content_blocks: List of all content blocks
            
        Returns:
            Analysis results with hierarchy information and potential issues
        """
        headings = [block for block in content_blocks if block.type == "heading"]
        
        if not headings:
            return {
                "has_headings": False,
                "hierarchy_valid": True,
                "issues": [],
                "structure": []
            }
        
        hierarchy_issues = []
        structure = []
        
        # Analyze heading progression
        prev_level = 0
        for i, heading in enumerate(headings):
            current_level = heading.level or 1
            
            structure.append({
                "position": heading.position,
                "level": current_level,
                "content": heading.content[:50] + "..." if len(heading.content) > 50 else heading.content,
                "length": len(heading.content)
            })
            
            # Check for level jumps (e.g., h1 → h4)
            if prev_level > 0 and current_level > prev_level + 1:
                hierarchy_issues.append(
                    f"Heading level jump: h{prev_level} → h{current_level} at position {heading.position}"
                )
            
            # Check for very long headings (might be misclassified paragraphs)
            if len(heading.content) > 150:
                hierarchy_issues.append(
                    f"Very long heading at position {heading.position} ({len(heading.content)} chars) - might be misclassified paragraph"
                )
            
            # Check for duplicate headings
            for j, other_heading in enumerate(headings[i+1:], i+1):
                if heading.content.strip().lower() == other_heading.content.strip().lower():
                    hierarchy_issues.append(
                        f"Duplicate heading text at positions {heading.position} and {other_heading.position}"
                    )
            
            prev_level = current_level
        
        return {
            "has_headings": True,
            "heading_count": len(headings),
            "max_level": max(h.level or 1 for h in headings),
            "hierarchy_valid": len(hierarchy_issues) == 0,
            "issues": hierarchy_issues,
            "structure": structure,
            "level_distribution": {
                level: len([h for h in headings if h.level == level])
                for level in range(1, 7)
                if any(h.level == level for h in headings)
            }
        } 