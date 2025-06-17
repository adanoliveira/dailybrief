"""
Content Assembler for DailyBrief Summarization.

Converts structured content blocks to markdown format while preserving semantic 
formatting and metadata. Implements intelligent truncation based on journalism 
principles and information density.
"""
import re
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import logging

# Replace SUMY imports with Gensim imports
try:
    import gensim
    from gensim import corpora, models, similarities
    from gensim.utils import simple_preprocess
    from gensim.parsing.preprocessing import STOPWORDS
    GENSIM_AVAILABLE = True
except ImportError:
    GENSIM_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class ContentSection:
    """Represents a semantic section of content with priority."""
    content: str
    priority: int  # 1=highest (lead), 2=medium (body), 3=low (filler)
    section_type: str  # 'lead', 'body', 'quote', 'conclusion', 'metadata'
    original_length: int
    is_truncatable: bool = True


class MarkdownContentAssembler:
    """
    Intelligent content assembler that produces markdown-formatted text suitable for AI processing.
    
    Supports both custom truncation and SUMY-based intelligent summarization.
    """
    
    # Block priority mapping (1=highest priority, 3=lowest)
    block_priorities = {
        'subtitle': 1,
        'heading': 1, 
        'quote': 1,
        'paragraph': 2,
        'list': 2,
        'image': 3,
        'divider': 3
    }
    
    def __init__(self, max_chars: int = 25000, use_intelligent_summarization: bool = True, summarization_mode: str = "hybrid"):
        """
        Initialize the content assembler.
        
        Args:
            max_chars: Maximum character limit for assembled content
            use_intelligent_summarization: Whether to use SUMY for intelligent summarization
            summarization_mode: 'intelligent', 'custom', or 'hybrid' (default)
        """
        self.max_chars = max_chars
        self.use_intelligent_summarization = use_intelligent_summarization and GENSIM_AVAILABLE
        self.summarization_mode = summarization_mode
        
        if self.use_intelligent_summarization and not GENSIM_AVAILABLE:
            logger.warning("Gensim not available, falling back to custom truncation")
            self.use_intelligent_summarization = False
            self.summarization_mode = "custom"
    
    def assemble_content(self, content_blocks: List[Dict[str, Any]], title: str = None) -> str:
        """
        Assemble content blocks into structured markdown.
        
        Uses intelligent summarization (SUMY) if available, otherwise falls back to 
        custom truncation logic.
        
        Args:
            content_blocks: List of content block dictionaries
            title: Optional article title to include at the beginning
            
        Returns:
            Assembled markdown content within character limits
        """
        if not content_blocks:
            return f"# {title}\n\n" if title else ""
        
        logger.info(f"Assembling {len(content_blocks)} content blocks into markdown")
        
        # First, convert all blocks to markdown
        full_content = self._blocks_to_markdown(content_blocks)
        
        # Add title at the beginning if provided
        if title:
            full_content = f"# {title}\n\n{full_content}"
        
        content_length = len(full_content)
        
        # If content is within limits, return as-is
        if content_length <= self.max_chars:
            logger.info(f"No truncation needed: {content_length} chars <= {self.max_chars}")
            return full_content
        
        logger.info(f"Truncation needed: {content_length} chars > {self.max_chars}")
        
        # Choose summarization approach
        if self.use_intelligent_summarization:
            if self.summarization_mode == "hybrid":
                return self._hybrid_summarize(content_blocks, full_content, title)
            else:
                return self._intelligent_summarize(full_content, title)
        else:
            return self._custom_truncate(content_blocks, title)
    
    def _blocks_to_markdown(self, blocks: List[Dict[str, Any]]) -> str:
        """Convert content blocks directly to markdown without truncation."""
        markdown_parts = []
        
        for block in blocks:
            markdown = self._block_to_markdown(block)
            if markdown.strip():
                markdown_parts.append(markdown)
        
        return "".join(markdown_parts).strip()
    
    def _intelligent_summarize(self, content: str, title: str = None) -> str:
        """
        Use Gensim's TextRank for intelligent text summarization.
        This preserves the most semantically important sentences.
        """
        if not GENSIM_AVAILABLE:
            logger.warning("Gensim not available, falling back to simple truncation")
            return self._smart_truncate_text(content, self.max_chars - 100)
            
        try:
            original_length = len(content)
            
            # Calculate target ratio based on character limit
            title_length = len(f"# {title}\n\n") if title else 0
            available_chars = self.max_chars - title_length - 200  # Buffer for processing info
            target_ratio = available_chars / original_length if original_length > 0 else 0.5
            target_ratio = max(0.1, min(0.9, target_ratio))  # Keep between 10% and 90%
            
            # Use Gensim's summarization functionality
            try:
                # Import summarize function from gensim.summarization
                from gensim.summarization import summarize
                
                # Generate summary with target ratio
                summarized_content = summarize(content, ratio=target_ratio)
                
                # If summarization returned empty, fall back to TextRank implementation
                if not summarized_content:
                    summarized_content = self._textrank_summarize(content, target_ratio)
            except ImportError:
                # If gensim.summarization is not available, use our custom implementation
                summarized_content = self._textrank_summarize(content, target_ratio)
            
            # If summarization failed or returned empty, fall back to simple truncation
            if not summarized_content:
                summarized_content = self._smart_truncate_text(content, available_chars)
            
            # Add title at the beginning if provided
            if title:
                summarized_content = f"# {title}\n\n{summarized_content}"
            
            # Add processing information for AI model
            final_length = len(summarized_content) - title_length
            reduction_percentage = ((original_length - final_length) / original_length * 100) if original_length > 0 else 0
            
            if reduction_percentage >= 10:  # Only add if significant reduction
                processing_info = f"*[INTELLIGENT SUMMARIZATION: {original_length:,} → {final_length:,} characters ({reduction_percentage:.1f}% reduction using Gensim TextRank algorithm)]*"
                summarized_content += f"\n\n{processing_info}"
            
            # Final length check and truncation if needed
            if len(summarized_content) > self.max_chars:
                summarized_content = self._smart_truncate_text(summarized_content, self.max_chars - 60)
                summarized_content += "\n\n*[Content truncated to fit character limit]*"
            
            logger.info(f"Intelligent summarization complete: {original_length} -> {len(summarized_content)} chars")
            return summarized_content
            
        except Exception as e:
            logger.warning(f"Gensim summarization failed: {e}, falling back to simple truncation")
            # Simple fallback with title support
            result = self._smart_truncate_text(content, self.max_chars - 100)
            if title:
                result = f"# {title}\n\n{result}"
            result += "\n\n*[Content truncated due to summarization failure]*"
            return result
            
    def _textrank_summarize(self, text: str, ratio: float) -> str:
        """
        Custom TextRank implementation using Gensim's core functionality.
        This is a fallback in case gensim.summarization is not available.
        """
        try:
            # Split text into sentences (simple split by period, question mark, exclamation mark)
            sentences = re.split(r'(?<=[.!?])\s+', text)
            if len(sentences) <= 5:  # Too few sentences for meaningful summarization
                return text
                
            # Preprocess sentences
            clean_sentences = []
            for s in sentences:
                s = s.strip()
                if s:  # Skip empty sentences
                    clean_sentences.append(s)
                    
            # Create sentence vectors using TF-IDF
            processed_sentences = []
            for sentence in clean_sentences:
                tokens = simple_preprocess(sentence)
                tokens = [token for token in tokens if token not in STOPWORDS]
                processed_sentences.append(tokens)
                
            # Create dictionary and corpus
            dictionary = corpora.Dictionary(processed_sentences)
            corpus = [dictionary.doc2bow(sentence) for sentence in processed_sentences]
            
            # Create TF-IDF model
            tfidf = models.TfidfModel(corpus)
            corpus_tfidf = tfidf[corpus]
            
            # Create similarity matrix
            similarity_matrix = similarities.MatrixSimilarity(corpus_tfidf)
            
            # Calculate sentence scores based on similarity to other sentences
            scores = []
            for i, sentence in enumerate(corpus_tfidf):
                # Get similarities to all other sentences
                sims = similarity_matrix[sentence]
                # Sum of similarities (excluding self-similarity)
                score = sum(sims) - sims[i]  # Subtract self-similarity
                scores.append(score)
                
            # Select top sentences based on ratio
            num_sentences = max(1, int(len(clean_sentences) * ratio))
            top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:num_sentences]
            top_indices.sort()  # Sort by original order
            
            # Assemble summary
            summary = " ".join(clean_sentences[i] for i in top_indices)
            return summary
            
        except Exception as e:
            logger.warning(f"Custom TextRank summarization failed: {e}")
            return ""
    
    def _hybrid_summarize(self, content_blocks: List[Dict[str, Any]], full_content: str, title: str = None) -> str:
        """
        Hybrid approach: Use intelligent summarization while preserving document structure and flow.
        
        This approach maintains the natural order of the document while intelligently selecting
        which content blocks to include, providing the best balance of content quality and structure.
        """
        try:
            # Calculate space requirements, reserving space for title
            title_length = len(f"# {title}\n\n") if title else 0
            available_chars = self.max_chars - title_length - 200  # Buffer for truncation indicators
            
            if available_chars < 1000:
                logger.warning("Not enough space for hybrid summarization, falling back to intelligent")
                return self._intelligent_summarize(full_content, title)
            
            # Score each content block for importance while preserving order
            scored_blocks = self._score_blocks_for_importance(content_blocks, available_chars)
            
            # Select blocks to include based on scores and space constraints
            selected_blocks = self._select_blocks_with_flow(scored_blocks, available_chars)
            
            # Build final content maintaining document order with proper spacing
            result_parts = []
            prev_block_type = None
            
            for block_info in selected_blocks:
                block_type = block_info['block'].get('type', 'paragraph')
                markdown_content = block_info['markdown']
                
                # Add extra spacing before headings if needed
                if block_type in ['subtitle', 'heading'] and prev_block_type is not None:
                    result_parts.append("")  # Add an extra empty line before headings
                
                result_parts.append(markdown_content.rstrip())
                prev_block_type = block_type
            
            # Join with double newlines to ensure proper spacing
            result_content = "\n\n".join(result_parts)
            
            # Add title at the beginning if provided
            if title:
                result_content = f"# {title}\n\n{result_content}"
            
            # Add comprehensive truncation indicators for the AI model
            original_length = sum(len(self._block_to_markdown(block)) for block in content_blocks)
            final_length = len(result_content) - title_length
            total_blocks = len(content_blocks)
            selected_blocks_count = len(selected_blocks)
            
            # Calculate content type statistics
            original_stats = self._calculate_content_stats(content_blocks)
            selected_stats = self._calculate_content_stats([info['block'] for info in selected_blocks])
            
            # Add detailed processing information for the AI model
            processing_info = self._generate_processing_summary(
                original_length, final_length, total_blocks, selected_blocks_count,
                original_stats, selected_stats, available_chars
            )
            
            if processing_info:
                result_content += f"\n\n{processing_info}"
            
            # Final length check
            if len(result_content) > self.max_chars:
                result_content = self._smart_truncate_text(result_content, self.max_chars - 100)
                result_content += "\n\n*[Final content truncated to fit character limit]*"
            
            final_length = len(result_content)
            logger.info(f"Hybrid summarization complete: {original_length} -> {final_length} chars (order preserved)")
            
            return result_content
            
        except Exception as e:
            logger.warning(f"Hybrid summarization failed: {e}, falling back to intelligent summarization")
            return self._intelligent_summarize(full_content, title)
    
    def _score_blocks_for_importance(self, content_blocks: List[Dict[str, Any]], available_chars: int) -> List[Dict[str, Any]]:
        """
        Score content blocks based on semantic importance using Gensim's advanced features.
        This approach evaluates blocks based on semantic similarity to the overall document.
        """
        if not GENSIM_AVAILABLE:
            logger.warning("Gensim not available, falling back to base scoring")
            return self._score_blocks_base(content_blocks, available_chars)
        
        scored_blocks = []
        total_blocks = len(content_blocks)
        
        # Convert blocks to markdown and gather texts
        block_texts = []
        for block in content_blocks:
            markdown = self._block_to_markdown(block)
            block_texts.append(markdown)
        
        # Skip if too few blocks
        if len(block_texts) <= 1:
            return [{'block': block, 
                    'position': i, 
                    'score': 1.0, 
                    'length': len(text), 
                    'markdown': text} 
                    for i, (block, text) in enumerate(zip(content_blocks, block_texts))]
        
        try:
            # Preprocess texts - remove stopwords and tokenize
            processed_texts = []
            for text in block_texts:
                # Simple preprocessing without NLTK
                tokens = simple_preprocess(text)
                # Remove stopwords
                tokens = [token for token in tokens if token not in STOPWORDS]
                processed_texts.append(tokens)
            
            # Create dictionary and corpus
            dictionary = corpora.Dictionary(processed_texts)
            corpus = [dictionary.doc2bow(text) for text in processed_texts]
            
            # Create TF-IDF model
            tfidf = models.TfidfModel(corpus)
            corpus_tfidf = tfidf[corpus]
            
            # Create LSI model for semantic analysis
            # Number of topics should be appropriate for the content
            num_topics = min(len(corpus), 10)  # Use fewer topics for small documents
            lsi = models.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=num_topics)
            corpus_lsi = lsi[corpus_tfidf]
            
            # Compute similarity matrix
            index = similarities.MatrixSimilarity(corpus_lsi)
            
            # Create a "document centroid" by averaging all block vectors
            # This represents the overall semantic meaning of the document
            doc_centroid = [0] * num_topics
            for doc_vec in corpus_lsi:
                for topic_id, weight in doc_vec:
                    doc_centroid[topic_id] += weight / len(corpus_lsi)
            
            # Score each block based on similarity to document centroid
            # and other important factors
            for i, block in enumerate(content_blocks):
                # Base score from position, type, etc.
                base_score = self._get_base_importance_score(block, i, total_blocks)
                
                # Get semantic similarity to document centroid
                block_vec = corpus_lsi[i]
                semantic_score = 0
                for topic_id, weight in block_vec:
                    semantic_score += weight * doc_centroid[topic_id]
                
                # Normalize semantic score (0-5 range to match your original scale)
                semantic_score = min(5, max(0, semantic_score * 5))
                
                # Information density score based on TF-IDF values
                tfidf_sum = sum(weight for _, weight in corpus_tfidf[i])
                tfidf_len = len(corpus_tfidf[i]) if len(corpus_tfidf[i]) > 0 else 1
                density_score = min(3, tfidf_sum / tfidf_len * 3)  # Scale to 0-3 range
                
                # Calculate final score with appropriate weighting
                final_score = base_score + semantic_score + density_score
                
                # Add to scored blocks
                scored_blocks.append({
                    'block': block,
                    'position': i,
                    'score': final_score,
                    'length': len(block_texts[i]),
                    'markdown': block_texts[i],
                    'semantic_score': semantic_score,  # For debugging
                    'density_score': density_score     # For debugging
                })
            
        except Exception as e:
            logger.warning(f"Advanced semantic scoring failed: {e}, falling back to simpler method")
            return self._score_blocks_simpler(content_blocks, block_texts, available_chars)
        
        # Sort by score (highest first)
        scored_blocks.sort(key=lambda x: x['score'], reverse=True)
        
        return scored_blocks

    def _score_blocks_simpler(self, content_blocks: List[Dict[str, Any]], block_texts: List[str], available_chars: int) -> List[Dict[str, Any]]:
        """Simpler fallback scoring method using basic TF-IDF without LSI."""
        try:
            scored_blocks = []
            total_blocks = len(content_blocks)
            
            # Preprocess texts
            processed_texts = []
            for text in block_texts:
                tokens = simple_preprocess(text)
                tokens = [token for token in tokens if token not in STOPWORDS]
                processed_texts.append(tokens)
            
            # Create dictionary and corpus
            dictionary = corpora.Dictionary(processed_texts)
            corpus = [dictionary.doc2bow(text) for text in processed_texts]
            
            # Create TF-IDF model
            tfidf = models.TfidfModel(corpus)
            corpus_tfidf = tfidf[corpus]
            
            # Score each block
            for i, block in enumerate(content_blocks):
                # Base score from position, type, etc.
                base_score = self._get_base_importance_score(block, i, total_blocks)
                
                # TF-IDF score
                tfidf_score = 0
                if len(corpus_tfidf[i]) > 0:
                    tfidf_score = sum(weight for _, weight in corpus_tfidf[i]) / len(corpus_tfidf[i]) * 5
                
                # Final score
                final_score = base_score + tfidf_score
                
                scored_blocks.append({
                    'block': block,
                    'position': i,
                    'score': final_score,
                    'length': len(block_texts[i]),
                    'markdown': block_texts[i]
                })
                
            # Sort by score
            scored_blocks.sort(key=lambda x: x['score'], reverse=True)
            return scored_blocks
            
        except Exception as e:
            logger.warning(f"Simple scoring failed: {e}, falling back to base scoring")
            return self._score_blocks_base(content_blocks, available_chars)

    def _score_blocks_base(self, content_blocks: List[Dict[str, Any]], available_chars: int) -> List[Dict[str, Any]]:
        """Base scoring method using only position and block type."""
        scored_blocks = []
        total_blocks = len(content_blocks)
        
        for i, block in enumerate(content_blocks):
            markdown = self._block_to_markdown(block)
            score = self._get_base_importance_score(block, i, total_blocks)
            
            scored_blocks.append({
                'block': block,
                'position': i,
                'score': score,
                'length': len(markdown),
                'markdown': markdown
            })
        
        # Sort by score
        scored_blocks.sort(key=lambda x: x['score'], reverse=True)
        return scored_blocks
    
    def _get_base_importance_score(self, block: Dict[str, Any], position: int, total_blocks: int) -> float:
        """Get base importance score for a content block based on type and position."""
        block_type = block.get('type', 'paragraph')
        
        # Base scores by block type
        type_scores = {
            'subtitle': 10.0,     # Always include subtitles
            'heading': 8.0,       # Always include headings
            'quote': 7.0,         # High priority for quotes
            'paragraph': 3.0,     # Default paragraph score
            'list': 5.0,          # Lists are fairly important
            'image': 4.0,         # Images provide context
            'divider': 1.0        # Low priority
        }
        
        base_score = type_scores.get(block_type, 3.0)
        
        # Position bonuses
        if position <= 3:  # Lead content
            base_score += 3.0
        elif position >= total_blocks - 3:  # Conclusion content
            base_score += 2.0
        elif position <= total_blocks * 0.1:  # Early content (first 10%)
            base_score += 1.0
        elif position >= total_blocks * 0.9:  # Late content (last 10%)
            base_score += 1.0
        
        # Content quality indicators for quotes and paragraphs
        if block_type in ['quote', 'paragraph']:
            content = block.get('content', '')
            # Boost for quotes with key terms or short impactful content
            if len(content) < 200 and any(keyword in content.lower() for keyword in ['trump', 'crypto', 'dinner', 'token']):
                base_score += 1.0
        
        return base_score
    
    def _select_blocks_with_flow(self, scored_blocks: List[Dict[str, Any]], available_chars: int) -> List[Dict[str, Any]]:
        """
        Select blocks to include while maintaining document flow and respecting character limits.
        
        Strategy:
        1. Always include very high-priority items (subtitles, headings)
        2. Select highest-scored content that fits within limits
        3. Ensure we maintain document flow by including connecting elements
        """
        # Sort by score (descending) while tracking original order
        blocks_by_score = sorted(scored_blocks, key=lambda x: x['score'], reverse=True)
        
        selected_indices = set()
        current_length = 0
        
        # Phase 1: Include all critical structural elements
        for block_info in blocks_by_score:
            block_type = block_info['block'].get('type', 'paragraph')
            if block_type in ['subtitle', 'heading']:
                if current_length + block_info['length'] <= available_chars:
                    selected_indices.add(block_info['position'])
                    current_length += block_info['length']
        
        # Phase 2: Add highest-scoring content blocks
        for block_info in blocks_by_score:
            if block_info['position'] not in selected_indices:
                if current_length + block_info['length'] <= available_chars:
                    selected_indices.add(block_info['position'])
                    current_length += block_info['length']
                elif current_length >= available_chars * 0.8:  # Stop when we're at 80% capacity
                    break
        
        # Phase 3: Return selected blocks in original document order
        selected_blocks = []
        for block_info in scored_blocks:
            if block_info['position'] in selected_indices:
                selected_blocks.append(block_info)
        
        # Sort by original index to maintain document order
        selected_blocks.sort(key=lambda x: x['position'])
        
        return selected_blocks
    
    def _smart_truncate_text(self, text: str, max_chars: int) -> str:
        """Smart truncation that preserves sentence boundaries."""
        if len(text) <= max_chars:
            return text
        
        # Find good truncation point near the limit
        truncate_point = max_chars - 100  # Leave some buffer
        
        # Look for sentence boundaries
        sentences = re.split(r'[.!?]+\s+', text)
        result = ""
        
        for sentence in sentences:
            if len(result) + len(sentence) + 2 <= truncate_point:  # +2 for punctuation and space
                result += sentence + ". "
            else:
                break
        
        return result.strip()
    
    def _custom_truncate(self, content_blocks: List[Dict[str, Any]], title: str = None) -> str:
        """Fallback to original custom truncation logic."""
        # Convert to sections for original logic
        sections = self._convert_blocks_to_sections(content_blocks)
        
        # Apply intelligent truncation
        truncated_sections = self._intelligent_truncation(sections)
        
        # Assemble final content
        result = self._assemble_sections(truncated_sections)
        
        # Add title at the beginning if provided
        if title:
            result = f"# {title}\n\n{result}"
        
        return result
    
    def _convert_blocks_to_sections(self, blocks: List[Dict[str, Any]]) -> List[ContentSection]:
        """Convert content blocks to markdown sections with priorities."""
        sections = []
        
        for i, block in enumerate(blocks):
            block_type = block.get('type', 'paragraph')
            content = block.get('content', '')
            metadata = block.get('metadata', {})
            position = block.get('position', i + 1)
            
            # Convert to markdown
            markdown_content = self._block_to_markdown(block)
            
            if not markdown_content.strip():
                continue
            
            # Determine priority and section type
            priority = self.block_priorities.get(block_type, 2)
            section_type = self._determine_section_type(block, position, len(blocks))
            
            # Adjust priority based on position and content
            if position <= 3:  # Lead content
                priority = min(priority, 1)
            elif position >= len(blocks) - 3:  # Conclusion content
                priority = min(priority, 1)  # Give conclusion same priority as lead
            
            sections.append(ContentSection(
                content=markdown_content,
                priority=priority,
                section_type=section_type,
                original_length=len(markdown_content),
                is_truncatable=block_type not in ['quote', 'subtitle', 'heading']
            ))
        
        return sections
    
    def _block_to_markdown(self, block: Dict[str, Any]) -> str:
        """Convert a single content block to markdown format."""
        block_type = block.get('type', 'paragraph')
        content = block.get('content', '').strip()
        metadata = block.get('metadata', {})
        
        # Early return for empty content, except for list blocks which may have items in metadata
        if not content and block_type != 'list':
            return ""
        
        # Clean HTML from content
        clean_content = self._clean_html(content)
        
        if block_type == 'subtitle':
            return f"## {clean_content}\n\n"
        
        elif block_type == 'heading':
            level = metadata.get('level', 3)
            hashes = '#' * min(level + 2, 6)  # H3-H6 for article headings
            return f"{hashes} {clean_content}\n\n"
        
        elif block_type == 'quote':
            quote_type = metadata.get('type', 'quote')
            if quote_type == 'pullquote':
                return f"> **{clean_content}**\n\n"
            else:
                return f"> {clean_content}\n\n"
        
        elif block_type == 'list':
            # Handle both ordered and unordered lists
            items = metadata.get('items', [])
            
            if not items and content:
                # Parse HTML lists from content
                items = self._parse_html_list(content)
            
            if not items:
                # Final fallback: split content by common delimiters
                items = [item.strip() for item in re.split(r'[•\n\r\-\*]+', content) if item.strip()]
            
            if not items:
                # If still no items, treat as regular paragraph
                return f"{self._clean_html(content)}\n\n"
            
            # Determine if it's an ordered list
            is_ordered = self._is_ordered_list(content, metadata)
            
            list_md = ""
            for i, item in enumerate(items):
                clean_item = self._clean_html(item).strip()
                if clean_item:
                    if is_ordered:
                        list_md += f"{i + 1}. {clean_item}\n"
                    else:
                        list_md += f"- {clean_item}\n"
            
            return f"{list_md}\n" if list_md else ""
        
        elif block_type == 'image':
            # Include image context as metadata
            alt_text = metadata.get('alt', '')
            caption = metadata.get('caption', clean_content)
            src = metadata.get('src', '')
            
            image_context = f"*[Image: {caption}]*"
            if alt_text and alt_text != caption:
                image_context += f" *(Alt: {alt_text})*"
            
            return f"{image_context}\n\n"
        
        elif block_type == 'divider':
            return "---\n\n"
        
        else:  # paragraph and other text blocks
            # Add link context if available
            links = metadata.get('links', [])
            if links:
                link_context = " ".join([f"[{link.get('text', 'link')}]" for link in links[:2]])
                clean_content = f"{clean_content} {link_context}"
            
            return f"{clean_content}\n\n"
    
    def _clean_html(self, content: str) -> str:
        """Clean HTML tags while preserving important formatting cues."""
        if not content:
            return ""
        
        # Preserve important formatting with markdown equivalents
        content = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', content, flags=re.IGNORECASE)
        content = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', content, flags=re.IGNORECASE)
        content = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', content, flags=re.IGNORECASE)
        content = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', content, flags=re.IGNORECASE)
        
        # Extract link text (already handled in metadata, so just clean)
        content = re.sub(r'<a[^>]*>(.*?)</a>', r'\1', content, flags=re.IGNORECASE)
        
        # Handle line breaks and paragraphs
        content = re.sub(r'<br[^>]*>', ' ', content, flags=re.IGNORECASE)
        content = re.sub(r'</p>\s*<p[^>]*>', ' ', content, flags=re.IGNORECASE)
        
        # Remove remaining HTML tags
        content = re.sub(r'<[^>]+>', '', content)
        
        # Decode common HTML entities
        content = content.replace('&nbsp;', ' ')
        content = content.replace('&amp;', '&')
        content = content.replace('&lt;', '<')
        content = content.replace('&gt;', '>')
        content = content.replace('&quot;', '"')
        content = content.replace('&#39;', "'")
        content = content.replace('&rsquo;', "'")
        content = content.replace('&lsquo;', "'")
        content = content.replace('&rdquo;', '"')
        content = content.replace('&ldquo;', '"')
        
        # Clean up whitespace
        content = re.sub(r'\s+', ' ', content).strip()
        
        return content
    
    def _parse_html_list(self, content: str) -> List[str]:
        """
        Parse HTML ul/ol elements and extract list items.
        
        Args:
            content: HTML content containing list elements
            
        Returns:
            List of item texts
        """
        if not content:
            return []
        
        items = []
        
        # Match both <ul> and <ol> lists
        list_pattern = r'<(?:ul|ol)[^>]*>(.*?)</(?:ul|ol)>'
        list_matches = re.findall(list_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for list_content in list_matches:
            # Extract <li> items from the list
            item_pattern = r'<li[^>]*>(.*?)</li>'
            item_matches = re.findall(item_pattern, list_content, re.DOTALL | re.IGNORECASE)
            
            for item_html in item_matches:
                # Clean the item text
                clean_item = self._clean_html(item_html).strip()
                if clean_item:
                    items.append(clean_item)
        
        return items
    
    def _is_ordered_list(self, content: str, metadata: Dict[str, Any]) -> bool:
        """
        Determine if a list should be rendered as ordered (numbered).
        
        Args:
            content: HTML content
            metadata: Block metadata
            
        Returns:
            True if list should be ordered
        """
        # Check metadata first
        list_type = metadata.get('list_type', '').lower()
        if list_type in ['ordered', 'ol', 'numbered']:
            return True
        elif list_type in ['unordered', 'ul', 'bulleted']:
            return False
        
        # Check HTML content for <ol> tags
        if re.search(r'<ol[^>]*>', content, re.IGNORECASE):
            return True
        
        # Default to unordered
        return False
    
    def _determine_section_type(self, block: Dict[str, Any], position: int, total_blocks: int) -> str:
        """Determine the semantic section type of a block."""
        block_type = block.get('type', 'paragraph')
        metadata = block.get('metadata', {})
        
        # Lead section (first few blocks)
        if position <= 3 or metadata.get('is_lead', False):
            return 'lead'
        
        # Conclusion section (last few blocks)
        elif position >= total_blocks - 2:
            return 'conclusion'
        
        # Special content types
        elif block_type in ['quote', 'list']:
            return 'highlight'
        
        elif block_type in ['image', 'divider']:
            return 'metadata'
        
        # Default body content
        else:
            return 'body'
    
    def _intelligent_truncation(self, sections: List[ContentSection]) -> List[ContentSection]:
        """
        Apply intelligent truncation based on journalism and information density principles.
        
        Strategy:
        1. Always keep lead and conclusion sections
        2. Keep all quotes and structured content (lists)
        3. For body paragraphs: keep beginning and end, truncate middle
        4. Remove low-priority metadata sections if needed
        """
        target_length = self.max_chars
        current_length = sum(s.original_length for s in sections)
        
        if current_length <= target_length:
            return sections
        
        # Sort by priority (1=highest priority)
        priority_sections = {1: [], 2: [], 3: []}
        for section in sections:
            priority_sections[section.priority].append(section)
        
        result_sections = []
        remaining_chars = target_length
        
        # Step 1: Include all priority 1 content (lead, quotes, structure)
        for section in priority_sections[1]:
            if section.original_length <= remaining_chars:
                result_sections.append(section)
                remaining_chars -= section.original_length
            elif section.section_type in ['lead', 'highlight', 'conclusion']:
                # Force include critical content (lead, quotes, conclusion), truncate if needed
                truncated = self._truncate_section(section, remaining_chars)
                result_sections.append(truncated)
                remaining_chars = 0
                break
        
        # Step 2: Include priority 2 content (body paragraphs) with smart truncation
        if remaining_chars > 0:
            for section in priority_sections[2]:
                if section.original_length <= remaining_chars:
                    result_sections.append(section)
                    remaining_chars -= section.original_length
                elif section.is_truncatable and remaining_chars > 100:
                    # Apply paragraph-level smart truncation
                    truncated = self._truncate_paragraph(section, remaining_chars)
                    result_sections.append(truncated)
                    remaining_chars -= truncated.original_length
                    if remaining_chars <= 100:
                        break
        
        # Step 3: Include priority 3 content only if space allows
        if remaining_chars > 200:
            for section in priority_sections[3]:
                if section.original_length <= remaining_chars:
                    result_sections.append(section)
                    remaining_chars -= section.original_length
        
        # Sort back to original order for readability
        result_sections.sort(key=lambda s: sections.index(s) if s in sections else len(sections))
        
        final_length = sum(s.original_length for s in result_sections)
        logger.info(f"Truncation complete: {current_length} -> {final_length} chars")
        
        return result_sections
    
    def _truncate_paragraph(self, section: ContentSection, max_chars: int) -> ContentSection:
        """
        Truncate a paragraph by keeping beginning and end, removing middle.
        
        This preserves the most information-dense parts of paragraphs.
        """
        content = section.content.strip()
        
        if len(content) <= max_chars:
            return section
        
        # Split into sentences
        sentences = re.split(r'[.!?]+\s+', content)
        
        if len(sentences) <= 2:
            # Short paragraph, just truncate
            return self._truncate_section(section, max_chars)
        
        # Keep first and last sentences, truncate middle
        first_sentence = sentences[0] + '.'
        last_sentence = sentences[-1]
        
        available = max_chars - len(first_sentence) - len(last_sentence) - 10  # buffer for " [...] "
        
        if available > 0:
            # Try to include some middle content
            middle_content = " ".join(sentences[1:-1])
            if len(middle_content) <= available:
                truncated_content = f"{first_sentence} {middle_content} {last_sentence}"
            else:
                truncated_content = f"{first_sentence} [...] {last_sentence}"
        else:
            truncated_content = f"{first_sentence} [...] {last_sentence}"
        
        return ContentSection(
            content=truncated_content,
            priority=section.priority,
            section_type=section.section_type,
            original_length=len(truncated_content),
            is_truncatable=section.is_truncatable
        )
    
    def _truncate_section(self, section: ContentSection, max_chars: int) -> ContentSection:
        """Simple truncation for critical content."""
        if len(section.content) <= max_chars:
            return section
        
        truncated = section.content[:max_chars - 4] + "..."
        
        return ContentSection(
            content=truncated,
            priority=section.priority,
            section_type=section.section_type,
            original_length=len(truncated),
            is_truncatable=section.is_truncatable
        )
    
    def _assemble_sections(self, sections: List[ContentSection]) -> str:
        """Assemble sections into final markdown content."""
        return "".join(section.content for section in sections).strip()
    
    def _calculate_content_stats(self, content_blocks: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate statistics about content blocks by type."""
        stats = {
            'paragraphs': 0,
            'quotes': 0,
            'headings': 0,
            'images': 0,
            'lists': 0,
            'other': 0
        }
        
        for block in content_blocks:
            block_type = block.get('type', 'paragraph')
            if block_type == 'paragraph':
                stats['paragraphs'] += 1
            elif block_type == 'quote':
                stats['quotes'] += 1
            elif block_type in ['heading', 'subtitle']:
                stats['headings'] += 1
            elif block_type == 'image':
                stats['images'] += 1
            elif block_type == 'list':
                stats['lists'] += 1
            else:
                stats['other'] += 1
        
        return stats
    
    def _generate_processing_summary(self, original_length: int, final_length: int, 
                                   total_blocks: int, selected_blocks: int,
                                   original_stats: Dict[str, int], selected_stats: Dict[str, int],
                                   available_chars: int) -> str:
        """Generate a comprehensive processing summary for the AI model."""
        
        reduction_percentage = ((original_length - final_length) / original_length * 100) if original_length > 0 else 0
        block_retention = (selected_blocks / total_blocks * 100) if total_blocks > 0 else 100
        
        # Only add processing info if there was significant reduction or selection
        if reduction_percentage < 10 and block_retention > 90:
            return ""  # Minor processing, no need for detailed info
        
        summary_parts = []
        
        # Main processing summary
        if reduction_percentage >= 50:
            summary_parts.append(f"*[MAJOR CONTENT REDUCTION: {original_length:,} → {final_length:,} characters ({reduction_percentage:.1f}% reduction)]*")
        elif reduction_percentage >= 25:
            summary_parts.append(f"*[CONTENT SUMMARIZED: {original_length:,} → {final_length:,} characters ({reduction_percentage:.1f}% reduction)]*")
        elif reduction_percentage >= 10:
            summary_parts.append(f"*[CONTENT OPTIMIZED: {original_length:,} → {final_length:,} characters ({reduction_percentage:.1f}% reduction)]*")
        
        # Block selection summary
        if block_retention < 80:
            excluded_blocks = total_blocks - selected_blocks
            summary_parts.append(f"*[CONTENT SELECTION: {selected_blocks}/{total_blocks} blocks retained, {excluded_blocks} blocks excluded]*")
        
        # Content type preservation summary
        content_changes = []
        for content_type, original_count in original_stats.items():
            selected_count = selected_stats.get(content_type, 0)
            if original_count > 0 and selected_count != original_count:
                if selected_count == 0:
                    content_changes.append(f"{original_count} {content_type} excluded")
                elif selected_count < original_count:
                    content_changes.append(f"{original_count-selected_count}/{original_count} {content_type} excluded")
        
        if content_changes:
            summary_parts.append(f"*[CONTENT TYPES AFFECTED: {', '.join(content_changes)}]*")
        
        # Methodology note
        if reduction_percentage >= 25:
            summary_parts.append("*[METHODOLOGY: Intelligent summarization using Gensim TextRank algorithm with structural preservation]*")
        
        return "\n\n".join(summary_parts) if summary_parts else ""

    def get_scoring_analysis(self, content_blocks: List[Dict[str, Any]], max_chars: int) -> Dict[str, Any]:
        """
        Get detailed scoring analysis for debugging purposes.
        
        Returns information about which blocks were selected/excluded and their scores.
        """
        if self.summarization_mode != "hybrid":
            return {"error": "Scoring analysis only available for hybrid mode"}
        
        try:
            # Calculate space requirements
            available_chars = max_chars - 200  # Buffer for indicators
            
            # Score blocks for importance
            scored_blocks = self._score_blocks_for_importance(content_blocks, available_chars)
            
            # Select blocks
            selected_blocks = self._select_blocks_with_flow(scored_blocks, available_chars)
            selected_indices = {block['position'] for block in selected_blocks}
            
            # Separate selected and excluded blocks
            selected_analysis = []
            excluded_analysis = []
            
            for block_info in scored_blocks:
                block_type = block_info['block'].get('type', 'paragraph')
                analysis_item = {
                    'position': block_info['position'],
                    'type': block_type,
                    'score': block_info['score'],
                    'length': block_info['length'],
                    'content_preview': block_info['markdown'][:100] + "..." if len(block_info['markdown']) > 100 else block_info['markdown'],
                    'final_score': block_info['score']
                }
                
                if block_info['position'] in selected_indices:
                    selected_analysis.append(analysis_item)
                else:
                    excluded_analysis.append(analysis_item)
            
            # Sort excluded blocks by score (lowest first) to show least relevant
            excluded_analysis.sort(key=lambda x: x['score'])
            selected_analysis.sort(key=lambda x: x['score'], reverse=True)
            
            return {
                'total_blocks': len(content_blocks),
                'selected_count': len(selected_analysis),
                'excluded_count': len(excluded_analysis),
                'selected_blocks': selected_analysis,
                'excluded_blocks': excluded_analysis,
                'selection_quality': {
                    'avg_selected_score': sum(b['score'] for b in selected_analysis) / len(selected_analysis) if selected_analysis else 0,
                    'avg_excluded_score': sum(b['score'] for b in excluded_analysis) / len(excluded_analysis) if excluded_analysis else 0,
                    'lowest_selected_score': min(b['score'] for b in selected_analysis) if selected_analysis else 0,
                    'highest_excluded_score': max(b['score'] for b in excluded_analysis) if excluded_analysis else 0,
                }
            }
            
        except Exception as e:
            return {"error": f"Analysis failed: {e}"}


def get_markdown_assembler(max_chars: int = 25000, use_intelligent_summarization: bool = True, summarization_mode: str = "hybrid") -> MarkdownContentAssembler:
    """
    Get content assembler instance.
    
    Args:
        max_chars: Maximum character limit for content
        use_intelligent_summarization: Whether to use SUMY-based intelligent summarization
        summarization_mode: 'intelligent', 'custom', or 'hybrid' (default)
        
    Returns:
        Configured MarkdownContentAssembler instance
    """
    return MarkdownContentAssembler(
        max_chars=max_chars, 
        use_intelligent_summarization=use_intelligent_summarization,
        summarization_mode=summarization_mode
    ) 