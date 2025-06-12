"""
Summarization Service for DailyBrief.

Main service layer for article summarization following the 4-stage pipeline:
1. Rich Bullet Compression (RBC)
2. Skeleton Summary Generation
3. Critic Review (Conditional)
4. Summary Repair (If needed)
5. Embedding Generation

Integrates with aiproviders service for AI operations while maintaining
domain-specific logic and prompt management.
"""
import json
import time
import logging
from typing import Optional, Dict, Any, List, Tuple
from decimal import Decimal
from dataclasses import asdict

from django.db import transaction
from django.utils import timezone
from django.conf import settings

from apps.aiproviders.services import get_ai_service
from apps.articles.models import Article, SummarizationStatus
from .models import (
    ArticleRBC, ArticleSummary, ArticleEmbedding, 
    SummarizationRequest, SummarizationResult
)
from .prompt_templates import SummarizationPrompts, EmbeddingPrompts

logger = logging.getLogger(__name__)


class SummarizationService:
    """
    Main summarization service following established DailyBrief patterns.
    
    Coordinates 4-stage pipeline while using aiproviders service
    for AI operations. Contains domain-specific prompt logic and
    business rules for summarization.
    """
    
    def __init__(self):
        """Initialize service with AI provider and configuration."""
        self.ai_service = get_ai_service()
        self.prompts = SummarizationPrompts()
        
        # Configuration from settings
        self.max_content_chars = getattr(settings, 'SUMMARIZATION_MAX_CONTENT_CHARS', 15000)
        self.enable_critic = getattr(settings, 'SUMMARIZATION_ENABLE_CRITIC', True)
        self.enable_repair = getattr(settings, 'SUMMARIZATION_ENABLE_REPAIR', True)
        self.enable_embeddings = getattr(settings, 'SUMMARIZATION_ENABLE_EMBEDDINGS', False)  # Disabled until implemented
        
        logger.info("SummarizationService initialized")
    
    def summarize_article(self, article: Article, force_regenerate: bool = False) -> SummarizationResult:
        """
        Main entry point for article summarization.
        
        Orchestrates the complete 4-stage pipeline with proper error handling
        and performance tracking.
        
        Args:
            article: Article instance to summarize
            force_regenerate: Whether to regenerate existing summaries
            
        Returns:
            SummarizationResult with complete pipeline output
        """
        start_time = time.time()
        
        logger.info(f"Starting summarization for article {article.id}: {article.title[:50]}")
        
        # Check if already summarized
        if not force_regenerate and article.summarization_status == SummarizationStatus.COMPLETED:
            logger.info(f"Article {article.id} already summarized, skipping")
            return self._get_existing_summary_result(article)
        
        # Validate input
        content, content_source = article.best_content_for_summarization
        if not content:
            error_msg = "No suitable content available for summarization"
            logger.error(f"Article {article.id}: {error_msg}")
            return SummarizationResult(
                success=False,
                article_id=article.id,
                error_message=error_msg,
                failed_stage="validation"
            )
        
        # Create or get summarization request
        request = self._create_summarization_request(article)
        
        try:
            with transaction.atomic():
                # Update article status
                article.summarization_status = SummarizationStatus.PROCESSING
                article.last_summarization_attempt = timezone.now()
                article.summarization_attempts += 1
                article.save(update_fields=[
                    'summarization_status', 'last_summarization_attempt', 'summarization_attempts'
                ])
                
                # Execute pipeline stages
                result = self._execute_pipeline(article, content, content_source, request)
                
                # Update final status
                if result.success:
                    article.summarization_status = SummarizationStatus.COMPLETED
                    article.summarized_at = timezone.now()
                    article.summary_ready = True
                    
                    # Performance tracking
                    total_duration = int((time.time() - start_time) * 1000)
                    article.summarization_duration_ms = total_duration
                    article.summarization_cost_usd = result.total_cost_usd
                    article.summary_content_source = content_source
                    
                    request.status = 'completed'
                    request.completed_at = timezone.now()
                    request.pipeline_end_time = timezone.now()
                    request.total_cost_usd = result.total_cost_usd
                    request.total_duration_ms = total_duration
                    
                    logger.info(f"Summarization completed for article {article.id} in {total_duration}ms, cost: ${result.total_cost_usd}")
                else:
                    article.summarization_status = SummarizationStatus.FAILED
                    article.summarization_error_message = result.error_message
                    
                    request.status = 'failed'
                    request.last_error = result.error_message
                    request.failed_stage = result.failed_stage
                    
                    logger.error(f"Summarization failed for article {article.id}: {result.error_message}")
                
                article.save()
                request.save()
                
                return result
                
        except Exception as e:
            logger.error(f"Unexpected error during summarization of article {article.id}: {str(e)}")
            
            # Update status on error
            article.summarization_status = SummarizationStatus.FAILED
            article.summarization_error_message = str(e)
            article.save(update_fields=['summarization_status', 'summarization_error_message'])
            
            request.status = 'failed'
            request.last_error = str(e)
            request.failed_stage = 'system_error'
            request.save()
            
            return SummarizationResult(
                success=False,
                article_id=article.id,
                error_message=str(e),
                failed_stage="system_error"
            )
    
    def _execute_pipeline(self, article: Article, content: str, content_source: str, request: SummarizationRequest) -> SummarizationResult:
        """
        Execute the complete 4-stage summarization pipeline.
        
        Args:
            article: Article to process
            content: Content text to summarize
            content_source: Source of content ('basic_content' or 'clean_content')
            request: Tracking request instance
            
        Returns:
            SummarizationResult with all pipeline outputs
        """
        result = SummarizationResult(success=True, article_id=article.id, content_source=content_source)
        request.pipeline_start_time = timezone.now()
        request.save()
        
        # Stage 1: Rich Bullet Compression
        logger.info(f"Stage 1: RBC compression for article {article.id}")
        request.current_stage = 'rbc_processing'
        request.status = 'rbc_processing'
        request.save()
        
        rbc_result = self._stage_1_rbc_compression(content, content_source)
        if not rbc_result['success']:
            result.success = False
            result.error_message = rbc_result['error']
            result.failed_stage = 'rbc_compression'
            return result
        
        # Store RBC
        rbc_instance = self._store_rbc_result(article, rbc_result, content_source)
        result.rbc_bullets = rbc_result['data']['bullets']
        result.total_cost_usd += rbc_result['cost_usd']
        request.mark_stage_completed('rbc_compression')
        
        # Stage 2: Skeleton Summary Generation
        logger.info(f"Stage 2: Skeleton summary for article {article.id}")
        request.current_stage = 'summary_processing'
        request.status = 'summary_processing'
        request.save()
        
        summary_result = self._stage_2_skeleton_summary(rbc_result['data'])
        if not summary_result['success']:
            result.success = False
            result.error_message = summary_result['error']
            result.failed_stage = 'skeleton_summary'
            return result
        
        summary_data = summary_result['data']
        result.headline = summary_data['headline']
        result.abstract = summary_data['abstract']
        result.facts = summary_data['facts']
        result.opinions = summary_data['opinions']
        result.impact = summary_data['impact']
        result.total_cost_usd += summary_result['cost_usd']
        request.mark_stage_completed('skeleton_summary')
        
        # Stage 3: Critic Review (Conditional)
        should_critique, critique_reasons = SummarizationPrompts.should_trigger_critic(summary_data, rbc_result['data'])
        result.required_critic = should_critique
        
        if should_critique and self.enable_critic:
            logger.info(f"Stage 3: Critic review for article {article.id}, reasons: {critique_reasons}")
            request.current_stage = 'critic_processing'
            request.status = 'critic_processing'
            request.save()
            
            critic_result = self._stage_3_critic_review(rbc_result['data'], summary_data)
            if not critic_result['success']:
                # Critic failure is not fatal - we can proceed with the summary
                logger.warning(f"Critic review failed for article {article.id}: {critic_result['error']}")
            else:
                result.total_cost_usd += critic_result['cost_usd']
                request.mark_stage_completed('critic_review')
                
                # Stage 4: Summary Repair (If needed)
                critic_data = critic_result['data']
                if not critic_data['faithful'] and self.enable_repair:
                    logger.info(f"Stage 4: Summary repair for article {article.id}")
                    request.current_stage = 'repair_processing'
                    request.status = 'repair_processing'
                    request.save()
                    
                    repair_result = self._stage_4_repair_summary(summary_data, critic_data['issues'])
                    if repair_result['success']:
                        # Update with repaired summary
                        summary_data = repair_result['data']
                        result.headline = summary_data['headline']
                        result.abstract = summary_data['abstract']
                        result.facts = summary_data['facts']
                        result.opinions = summary_data['opinions']
                        result.impact = summary_data['impact']
                        result.was_repaired = True
                        result.total_cost_usd += repair_result['cost_usd']
                        request.mark_stage_completed('summary_repair')
                    else:
                        logger.warning(f"Summary repair failed for article {article.id}: {repair_result['error']}")
        
        # Store final summary
        summary_instance = self._store_summary_result(article, summary_data, summary_result, result)
        
        # Stage 5: Embedding Generation
        if self.enable_embeddings:
            logger.info(f"Stage 5: Embedding generation for article {article.id}")
            request.current_stage = 'embedding_processing'
            request.status = 'embedding_processing'
            request.save()
            
            embedding_result = self._generate_embedding(result.headline, result.abstract)
            if embedding_result['success']:
                embedding_instance = self._store_embedding_result(article, embedding_result, result.headline, result.abstract)
                result.embedding = embedding_result['data']
                result.total_cost_usd += embedding_result['cost_usd']
                request.mark_stage_completed('embedding_generation')
            else:
                logger.warning(f"Embedding generation failed for article {article.id}: {embedding_result['error']}")
        
        result.stages_completed = request.stages_completed
        return result
    
    def _stage_1_rbc_compression(self, content: str, content_source: str) -> Dict[str, Any]:
        """
        Stage 1: Rich Bullet Compression.
        
        Converts article content into ≤25 labeled bullet points for lossless compression.
        """
        # Truncate content at sentence boundary
        truncated_content, truncated_at = self._smart_truncate(content, self.max_content_chars)
        
        # Generate prompt
        prompt = SummarizationPrompts.rbc_compression_prompt(truncated_content)
        prompt_config = SummarizationPrompts.get_prompt_metadata('rbc_compression')
        
        # Call AI service
        ai_response = self.ai_service.call_llm(
            prompt=prompt,
            operation=prompt_config['operation'],
            max_tokens=prompt_config['max_tokens'],
            temperature=prompt_config['temperature']
        )
        
        if not ai_response.success:
            return {
                'success': False,
                'error': f"AI call failed: {ai_response.error_message}",
                'cost_usd': Decimal('0.0')
            }
        
        # Check for empty response
        if not ai_response.content or ai_response.content.strip() == "":
            return {
                'success': False,
                'error': f"Empty response from AI model",
                'cost_usd': self._calculate_cost(ai_response.usage)
            }

        # Validate output
        validation = SummarizationPrompts.validate_rbc_output(ai_response.content)
        if not validation['valid']:
            return {
                'success': False,
                'error': f"Invalid RBC output: {validation['error']}",
                'cost_usd': self._calculate_cost(ai_response.usage)
            }
        
        return {
            'success': True,
            'data': validation['data'],
            'cost_usd': self._calculate_cost(ai_response.usage),
            'tokens_used': ai_response.usage,
            'processing_time_ms': int(ai_response.response_time * 1000),
            'original_length': len(content),
            'truncated_at': truncated_at,
            'ai_model': ai_response.model
        }
    
    def _stage_2_skeleton_summary(self, rbc_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stage 2: Skeleton Summary Generation.
        
        Creates structured summary using only RBC bullets as source.
        """
        # Generate prompt
        rbc_json = json.dumps(rbc_data, ensure_ascii=False)
        prompt = SummarizationPrompts.skeleton_summary_prompt(rbc_json)
        prompt_config = SummarizationPrompts.get_prompt_metadata('skeleton_summary')
        
        # Call AI service
        ai_response = self.ai_service.call_llm(
            prompt=prompt,
            operation=prompt_config['operation'],
            max_tokens=prompt_config['max_tokens'],
            temperature=prompt_config['temperature']
        )
        
        if not ai_response.success:
            return {
                'success': False,
                'error': f"AI call failed: {ai_response.error_message}",
                'cost_usd': Decimal('0.0')
            }
        
        # Validate output
        validation = SummarizationPrompts.validate_summary_output(ai_response.content)
        if not validation['valid']:
            return {
                'success': False,
                'error': f"Invalid summary output: {validation['error']}",
                'cost_usd': self._calculate_cost(ai_response.usage)
            }
        
        return {
            'success': True,
            'data': validation['data'],
            'cost_usd': self._calculate_cost(ai_response.usage),
            'tokens_used': ai_response.usage,
            'processing_time_ms': int(ai_response.response_time * 1000),
            'ai_model': ai_response.model
        }
    
    def _stage_3_critic_review(self, rbc_data: Dict[str, Any], summary_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stage 3: Critic Review.
        
        Detects hallucinations and verifies faithfulness to source bullets.
        """
        # Generate prompt
        rbc_json = json.dumps(rbc_data, ensure_ascii=False)
        summary_json = json.dumps(summary_data, ensure_ascii=False)
        prompt = SummarizationPrompts.critic_review_prompt(rbc_json, summary_json)
        prompt_config = SummarizationPrompts.get_prompt_metadata('summary_critique')
        
        # Call AI service
        ai_response = self.ai_service.call_llm(
            prompt=prompt,
            operation=prompt_config['operation'],
            max_tokens=prompt_config['max_tokens'],
            temperature=prompt_config['temperature']
        )
        
        if not ai_response.success:
            return {
                'success': False,
                'error': f"AI call failed: {ai_response.error_message}",
                'cost_usd': Decimal('0.0')
            }
        
        # Validate output
        validation = SummarizationPrompts.validate_critic_output(ai_response.content)
        if not validation['valid']:
            return {
                'success': False,
                'error': f"Invalid critic output: {validation['error']}",
                'cost_usd': self._calculate_cost(ai_response.usage)
            }
        
        return {
            'success': True,
            'data': validation['data'],
            'cost_usd': self._calculate_cost(ai_response.usage),
            'tokens_used': ai_response.usage,
            'processing_time_ms': int(ai_response.response_time * 1000),
            'ai_model': ai_response.model
        }
    
    def _stage_4_repair_summary(self, summary_data: Dict[str, Any], issues: List[str]) -> Dict[str, Any]:
        """
        Stage 4: Summary Repair.
        
        Fixes identified issues while preserving JSON structure.
        """
        # Generate prompt
        summary_json = json.dumps(summary_data, ensure_ascii=False)
        prompt = SummarizationPrompts.repair_summary_prompt(summary_json, issues)
        prompt_config = SummarizationPrompts.get_prompt_metadata('summary_repair')
        
        # Call AI service
        ai_response = self.ai_service.call_llm(
            prompt=prompt,
            operation=prompt_config['operation'],
            max_tokens=prompt_config['max_tokens'],
            temperature=prompt_config['temperature']
        )
        
        if not ai_response.success:
            return {
                'success': False,
                'error': f"AI call failed: {ai_response.error_message}",
                'cost_usd': Decimal('0.0')
            }
        
        # Validate output
        validation = SummarizationPrompts.validate_summary_output(ai_response.content)
        if not validation['valid']:
            return {
                'success': False,
                'error': f"Invalid repaired summary: {validation['error']}",
                'cost_usd': self._calculate_cost(ai_response.usage)
            }
        
        return {
            'success': True,
            'data': validation['data'],
            'cost_usd': self._calculate_cost(ai_response.usage),
            'tokens_used': ai_response.usage,
            'processing_time_ms': int(ai_response.response_time * 1000),
            'ai_model': ai_response.model
        }
    
    def _generate_embedding(self, headline: str, abstract: str) -> Dict[str, Any]:
        """
        Generate embedding from headline and abstract.
        
        Uses OpenAI's text-embedding-3-small model for semantic search.
        """
        # Prepare text for embedding
        embedding_text = EmbeddingPrompts.prepare_embedding_text(headline, abstract)
        if not embedding_text:
            return {
                'success': False,
                'error': "No text available for embedding",
                'cost_usd': Decimal('0.0')
            }
        
        # Call AI service for embedding
        # Note: This would need to be implemented in aiproviders service
        # For now, we'll create a placeholder that could be implemented
        try:
            # This is a placeholder - actual implementation would call aiproviders
            # ai_response = self.ai_service.generate_embedding(embedding_text, model='text-embedding-3-small')
            
            # Placeholder return for now
            return {
                'success': True,
                'data': [0.0] * 1536,  # Placeholder embedding
                'cost_usd': Decimal('0.00002'),
                'tokens_used': len(embedding_text.split()),
                'processing_time_ms': 200,
                'embedding_text': embedding_text
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Embedding generation failed: {str(e)}",
                'cost_usd': Decimal('0.0')
            }
    
    def _smart_truncate(self, text: str, max_chars: int) -> Tuple[str, Optional[int]]:
        """
        Truncate text at sentence boundary to preserve readability.
        
        Returns (truncated_text, truncation_position) or (original_text, None)
        """
        if len(text) <= max_chars:
            return text, None
        
        # Find last sentence boundary before max_chars
        truncated = text[:max_chars]
        
        # Look for sentence endings (., !, ?)
        sentence_endings = ['.', '!', '?']
        last_sentence_end = -1
        
        for i in range(len(truncated) - 1, -1, -1):
            if truncated[i] in sentence_endings:
                # Check if this looks like end of sentence (followed by space or end)
                if i == len(truncated) - 1 or truncated[i + 1].isspace():
                    last_sentence_end = i
                    break
        
        if last_sentence_end > max_chars * 0.7:  # Only truncate if we keep at least 70%
            return truncated[:last_sentence_end + 1], last_sentence_end + 1
        else:
            return truncated, max_chars
    
    def _calculate_cost(self, usage: Dict[str, int]) -> Decimal:
        """
        Calculate cost based on token usage.
        
        Uses current OpenAI pricing for gpt-4o-mini.
        """
        input_tokens = usage.get('prompt_tokens', 0)
        output_tokens = usage.get('completion_tokens', 0)
        
        # GPT-4o-mini pricing (as of 2024)
        input_cost_per_1k = Decimal('0.00015')  # $0.00015 per 1K input tokens
        output_cost_per_1k = Decimal('0.0006')  # $0.0006 per 1K output tokens
        
        input_cost = (Decimal(input_tokens) / 1000) * input_cost_per_1k
        output_cost = (Decimal(output_tokens) / 1000) * output_cost_per_1k
        
        return input_cost + output_cost
    
    def _create_summarization_request(self, article: Article) -> SummarizationRequest:
        """Create or get existing summarization request."""
        request, created = SummarizationRequest.objects.get_or_create(
            article=article,
            status='queued',
            defaults={
                'current_stage': 'queued',
                'pipeline_start_time': timezone.now()
            }
        )
        
        if not created:
            # Reset existing request
            request.status = 'queued'
            request.current_stage = 'queued'
            request.stages_completed = []
            request.pipeline_start_time = timezone.now()
            request.pipeline_end_time = None
            request.attempts += 1
            request.save()
        
        return request
    
    def _store_rbc_result(self, article: Article, rbc_result: Dict[str, Any], content_source: str) -> ArticleRBC:
        """Store RBC compression result."""
        rbc_data = rbc_result['data']
        
        rbc, created = ArticleRBC.objects.update_or_create(
            article=article,
            defaults={
                'bullets': rbc_data['bullets'],
                'bullet_count': len(rbc_data['bullets']),
                'content_source': content_source,
                'original_content_length': rbc_result['original_length'],
                'truncated_at': rbc_result.get('truncated_at'),
                'tokens_input': rbc_result['tokens_used'].get('prompt_tokens', 0),
                'tokens_output': rbc_result['tokens_used'].get('completion_tokens', 0),
                'processing_time_ms': rbc_result['processing_time_ms'],
                'cost_usd': rbc_result['cost_usd'],
                'ai_model_used': rbc_result['ai_model']
            }
        )
        
        return rbc
    
    def _store_summary_result(self, article: Article, summary_data: Dict[str, Any], 
                            summary_result: Dict[str, Any], pipeline_result: SummarizationResult) -> ArticleSummary:
        """Store structured summary result."""
        # Calculate word counts
        headline_words = len(summary_data['headline'].split()) if summary_data.get('headline') else 0
        abstract_words = len(summary_data['abstract'].split()) if summary_data.get('abstract') else 0
        facts_count = len(summary_data.get('facts', []))
        
        summary, created = ArticleSummary.objects.update_or_create(
            article=article,
            defaults={
                'headline': summary_data['headline'],
                'abstract': summary_data['abstract'],
                'facts': summary_data['facts'],
                'opinions': summary_data['opinions'],
                'impact': summary_data['impact'],
                'content_source': pipeline_result.content_source,
                'headline_words': headline_words,
                'abstract_words': abstract_words,
                'facts_count': facts_count,
                'tokens_input': summary_result['tokens_used'].get('prompt_tokens', 0),
                'tokens_output': summary_result['tokens_used'].get('completion_tokens', 0),
                'processing_time_ms': summary_result['processing_time_ms'],
                'cost_usd': summary_result['cost_usd'],
                'ai_model_used': summary_result['ai_model'],
                'required_critic_review': pipeline_result.required_critic,
                'was_repaired': pipeline_result.was_repaired
            }
        )
        
        return summary
    
    def _store_embedding_result(self, article: Article, embedding_result: Dict[str, Any], 
                              headline: str, abstract: str) -> ArticleEmbedding:
        """Store embedding result."""
        embedding, created = ArticleEmbedding.objects.update_or_create(
            article=article,
            defaults={
                'embedding': embedding_result['data'],
                'embedding_text': embedding_result['embedding_text'],
                'embedding_length': len(embedding_result['data']),
                'tokens_used': embedding_result['tokens_used'],
                'processing_time_ms': embedding_result['processing_time_ms'],
                'cost_usd': embedding_result['cost_usd']
            }
        )
        
        return embedding
    
    def _get_existing_summary_result(self, article: Article) -> SummarizationResult:
        """Get existing summary as SummarizationResult."""
        try:
            summary = article.structured_summary
            result = SummarizationResult(
                success=True,
                article_id=article.id,
                headline=summary.headline,
                abstract=summary.abstract,
                facts=summary.facts,
                opinions=summary.opinions,
                impact=summary.impact,
                total_cost_usd=summary.cost_usd,
                content_source=summary.content_source,
                required_critic=summary.required_critic_review,
                was_repaired=summary.was_repaired
            )
            
            # Add RBC bullets if available
            if hasattr(article, 'rbc'):
                result.rbc_bullets = article.rbc.bullets
            
            return result
            
        except ArticleSummary.DoesNotExist:
            return SummarizationResult(
                success=False,
                article_id=article.id,
                error_message="No existing summary found",
                failed_stage="retrieval"
            )


def get_summarization_service() -> SummarizationService:
    """
    Get summarization service instance.
    
    Following established pattern from other services.
    """
    return SummarizationService() 