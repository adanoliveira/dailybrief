"""
Article Analyzer Service for DailyBrief - Following Exact Draft Plan Specifications.

Implements cost-optimal 8-stage pipeline:
1. Language ID (langdetect - FREE)
2. Linguistic Analysis (textstat + word count + GPT for style_tone only)
3. Named-entity (spaCy + regex - CPU only)
4. Entity resolve (lookup-or-create with deduplication)
5. Event extraction (GPT-4o-mini)
6. Region classification (GPT-4o-mini)
7. Topic classification (GPT-4o-mini)
8. Event resolve (hash + ANN)
9. Persist (update existing Article fields)

Target cost: ≤ $0.00019/article (vs previous $0.0004)
"""
import logging
import time
import re
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
from datetime import datetime

from django.utils import timezone as django_timezone
from django.db import transaction
from django.core.exceptions import ValidationError

# Import required libraries following plan
import langdetect
import textstat
import spacy
from scipy.spatial.distance import cosine

from apps.articles.models import Article, AnalyzerStatus
from apps.feeds.models import Topic, Region, Language
from apps.aiproviders.services import get_ai_service
from .models import (
    Entity, EntityAlias, Event, ArticleAnalysis, ArticleEntity, 
    ArticleEvent, EventEntity, AnalyzerRequest
)
from .prompt_templates import AnalyzerPrompts

logger = logging.getLogger(__name__)

# Load spaCy model (use en_core_web_lg as per plan)
try:
    nlp = spacy.load("en_core_web_lg")
except OSError:
    logger.warning("spaCy model en_core_web_lg not found. Falling back to en_core_web_sm.")
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        logger.warning("No spaCy model found. Please install en_core_web_lg or en_core_web_sm.")
        nlp = None


class AnalyzerService:
    """
    Cost-optimized analyzer service following exact draft plan specifications.
    
    Uses open-source tools for most tasks, GPT-4o-mini only where necessary:
    - FREE: Language detection (langdetect)
    - FREE: Readability, word count (textstat) 
    - CPU-only: Entity extraction (spaCy)
    - LLM: Style tone, events, topics, regions (GPT-4o-mini)
    
    Target: $0.00019/article (vs $0.0004 with all-LLM approach)
    """
    
    def __init__(self):
        """Initialize service with AI provider and configuration."""
        self.ai_service = get_ai_service()
        self.prompts = AnalyzerPrompts()
        self.version = "1.0"
        
        logger.info("AnalyzerService initialized with cost-optimal tool mix")
    
    def analyze_article(self, article: Article, force: bool = False) -> Dict[str, Any]:
        """
        Analyze article following exact 8-stage pipeline from draft plan.
        
        Args:
            article: Article instance to analyze
            force: Whether to force re-analysis
            
        Returns:
            Dict containing analysis results and metadata
        """
        # Check if article needs analysis
        if not force and not article.needs_analysis:
            return {
                'success': False,
                'reason': 'Article does not need analysis',
                'status': article.analyzer_status
            }
        
        # Check if article has analyzable content
        if not article.has_analyzable_content:
            return {
                'success': False,
                'reason': 'Article has no analyzable content'
            }
        
        # Create analyzer request for tracking
        analyzer_request = AnalyzerRequest.objects.create(
            article=article,
            status='queued'
        )
        
        start_time = time.time()
        total_cost = Decimal('0.00')
        
        try:
            # Update article status
            article.analyzer_status = AnalyzerStatus.PROCESSING
            article.analyzer_attempts += 1
            article.last_analyzer_attempt = django_timezone.now()
            article.save(
                update_fields=[
                    'analyzer_status', 'analyzer_attempts', 'last_analyzer_attempt'
                ]
            )
            
            # Update request tracking
            analyzer_request.status = 'linguistic_processing'
            analyzer_request.pipeline_start_time = django_timezone.now()
            analyzer_request.attempts = article.analyzer_attempts
            analyzer_request.save()
            
            # Get content for analysis
            content = article.best_content_for_analysis
            if not content:
                raise ValueError("No suitable content found for analysis")
            
            # Create or get ArticleAnalysis record
            analysis_record, created = ArticleAnalysis.objects.get_or_create(
                article=article,
                defaults={
                    'analyzer_version': self.version,
                    'ai_model_used': 'gpt-4o-mini'
                }
            )
            
            results = {}
            
            # STAGE 1: Language ID (FREE - langdetect)
            logger.info(f"Stage 1: Language detection for article {article.id}")
            lang_result = self._stage_1_language_detection(article, content)
            results['language'] = lang_result
            analyzer_request.mark_stage_completed('language_detection')
            
            # STAGE 2: Linguistic Analysis (FREE + minimal LLM)
            logger.info(f"Stage 2: Linguistic analysis for article {article.id}")
            analyzer_request.current_stage = 'linguistic_processing'
            analyzer_request.save()
            
            linguistic_result = self._stage_2_linguistic_analysis(article, content, analysis_record)
            results['linguistic'] = linguistic_result
            total_cost += linguistic_result.get('cost', Decimal('0.00'))
            analyzer_request.mark_stage_completed('linguistic_processing')
            
            # STAGE 3: Named Entity Recognition (CPU-only - spaCy)
            logger.info(f"Stage 3: Entity extraction for article {article.id}")
            analyzer_request.current_stage = 'entity_processing'
            analyzer_request.save()
            
            entity_result = self._stage_3_entity_extraction(article, content)
            results['entities'] = entity_result
            analyzer_request.mark_stage_completed('entity_processing')
            
            # STAGE 4: Entity Resolution (CPU-only)
            entity_ids = self._stage_4_entity_resolution(entity_result.get('entities', []))
            results['entity_resolution'] = {'entity_ids': entity_ids}
            
            # STAGE 5: Event Extraction (LLM - GPT-4o-mini)
            logger.info(f"Stage 5: Event extraction for article {article.id}")
            analyzer_request.current_stage = 'event_processing'
            analyzer_request.save()
            
            event_result = self._stage_5_event_extraction(article, content)
            results['events'] = event_result
            total_cost += event_result.get('cost', Decimal('0.00'))
            analyzer_request.mark_stage_completed('event_processing')
            
            # STAGE 6: Region Classification (LLM - GPT-4o-mini)
            logger.info(f"Stage 6: Region classification for article {article.id}")
            analyzer_request.current_stage = 'region_processing'
            analyzer_request.save()
            
            region_result = self._stage_6_region_classification(article, content, analysis_record)
            results['regions'] = region_result
            total_cost += region_result.get('cost', Decimal('0.00'))
            analyzer_request.mark_stage_completed('region_processing')
            
            # STAGE 7: Topic Classification (LLM - GPT-4o-mini)
            logger.info(f"Stage 7: Topic classification for article {article.id}")
            analyzer_request.current_stage = 'topic_processing'
            analyzer_request.save()
            
            topic_result = self._stage_7_topic_classification(article, content, analysis_record)
            results['topics'] = topic_result
            total_cost += topic_result.get('cost', Decimal('0.00'))
            analyzer_request.mark_stage_completed('topic_processing')
            
            # STAGE 8: Event Resolution (CPU-only)
            event_id = self._stage_8_event_resolution(
                event_result.get('main_event'),
                entity_ids,
                article
            )
            results['event_resolution'] = {'event_id': event_id}
            
            # STAGE 9: Persist to existing Article fields
            self._stage_9_persist_results(article, results, analysis_record)
            
            # Calculate total duration
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Update analysis record with final metrics
            analysis_record.processing_time_ms = duration_ms
            analysis_record.cost_usd = total_cost
            analysis_record.save()
            
            # Update article status
            article.analyzer_status = AnalyzerStatus.COMPLETED
            article.analyzed_at = django_timezone.now()
            article.analyzer_duration_ms = duration_ms
            article.analyzer_cost_usd = total_cost
            article.analyzer_error_message = ''
            article.save(
                update_fields=[
                    'analyzer_status', 'analyzed_at', 'analyzer_duration_ms',
                    'analyzer_cost_usd', 'analyzer_error_message'
                ]
            )
            
            # Update request completion
            analyzer_request.status = 'completed'
            analyzer_request.pipeline_end_time = django_timezone.now()
            analyzer_request.total_cost_usd = total_cost
            analyzer_request.total_duration_ms = duration_ms
            analyzer_request.completed_at = django_timezone.now()
            analyzer_request.save()
            
            logger.info(
                f"Successfully analyzed article {article.id} in {duration_ms}ms "
                f"for ${total_cost:.6f} (target: $0.00019)"
            )
            
            return {
                'success': True,
                'results': results,
                'duration_ms': duration_ms,
                'cost_usd': total_cost,
                'stages_completed': analyzer_request.stages_completed
            }
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            
            logger.error(f"Failed to analyze article {article.id}: {error_msg}")
            
            # Update article with error state
            article.analyzer_status = AnalyzerStatus.FAILED
            article.analyzer_error_message = error_msg
            article.analyzer_duration_ms = duration_ms
            article.analyzer_cost_usd = total_cost
            article.save(
                update_fields=[
                    'analyzer_status', 'analyzer_error_message', 
                    'analyzer_duration_ms', 'analyzer_cost_usd'
                ]
            )
            
            # Update request with error info
            analyzer_request.status = 'failed'
            analyzer_request.last_error = error_msg
            analyzer_request.failed_stage = analyzer_request.current_stage
            analyzer_request.total_cost_usd = total_cost
            analyzer_request.total_duration_ms = duration_ms
            analyzer_request.pipeline_end_time = django_timezone.now()
            analyzer_request.save()
            
            return {
                'success': False,
                'error': error_msg,
                'duration_ms': duration_ms,
                'cost_usd': total_cost,
                'failed_stage': analyzer_request.current_stage
            }
    
    def _stage_1_language_detection(self, article: Article, content: str) -> Dict[str, Any]:
        """
        Stage 1: Language detection using fastText lid.176.bin (FREE) as per plan.
        
        Updates Article.language field directly.
        """
        stage_start = time.time()
        
        try:
            # Use fastText for language detection (plan requirement)
            text_sample = f"{article.title} {content[:500]}"  # Use title + first 500 chars
            
            # Try fastText first (plan requirement)
            try:
                import fasttext
                
                # Load fastText model (cached)
                if not hasattr(self, '_fasttext_model'):
                    try:
                        # Try to download model if not exists
                        import os
                        model_path = '/tmp/lid.176.bin'
                        if not os.path.exists(model_path):
                            logger.info("Downloading fastText language identification model...")
                            import urllib.request
                            urllib.request.urlretrieve(
                                'https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin',
                                model_path
                            )
                        self._fasttext_model = fasttext.load_model(model_path)
                    except Exception as e:
                        logger.warning(f"Failed to load fastText model: {e}, falling back to langdetect")
                        raise
                
                # Predict language
                predictions = self._fasttext_model.predict(text_sample, k=1)
                detected_lang = predictions[0][0].replace('__label__', '')
                confidence = float(predictions[1][0])
                
            except Exception as e:
                logger.warning(f"fastText failed: {e}, using langdetect fallback")
                # Fallback to langdetect
                detected_lang = langdetect.detect(text_sample)
                confidence = langdetect.detect_langs(text_sample)[0].prob
            
            # Map common language codes to our Language model
            lang_mapping = {
                'en': 'en', 'es': 'es', 'fr': 'fr', 'de': 'de', 'pt': 'pt',
                'it': 'it', 'nl': 'nl', 'ru': 'ru', 'zh': 'zh', 'ja': 'ja',
                'ar': 'ar', 'hi': 'hi', 'ko': 'ko', 'tr': 'tr', 'pl': 'pl'
            }
            
            lang_code = lang_mapping.get(detected_lang, detected_lang)
            
            # Update article language if confidence is high and not already set
            if confidence > 0.8 and not article.language:
                try:
                    language = Language.objects.get(iso_code=lang_code)
                    article.language = language
                    article.save(update_fields=['language'])
                except Language.DoesNotExist:
                    logger.warning(f"Language {lang_code} not found in database")
            
            duration_ms = int((time.time() - stage_start) * 1000)
            
            return {
                'success': True,
                'detected_language': detected_lang,
                'confidence': confidence,
                'duration_ms': duration_ms,
                'cost': Decimal('0.00'),  # FREE
                'tokens_input': 0,
                'tokens_output': 0
            }
            
        except Exception as e:
            logger.error(f"Language detection failed for article {article.id}: {e}")
            duration_ms = int((time.time() - stage_start) * 1000)
            return {
                'success': False,
                'error': str(e),
                'duration_ms': duration_ms,
                'cost': Decimal('0.00')
            }
    
    def _stage_2_linguistic_analysis(self, article: Article, content: str, analysis_record: ArticleAnalysis) -> Dict[str, Any]:
        """
        Stage 2: Linguistic analysis using textstat (FREE) + GPT for style_tone only.
        
        Updates existing Article fields: word_count, read_time_minutes.
        """
        stage_start = time.time()
        
        try:
            # FREE: Calculate readability and reading time using textstat
            full_text = f"{article.title} {content}"
            
            # Word count and reading time (FREE) - following plan: word_count / 200 wpm
            word_count = len(full_text.split())
            reading_time_minutes = word_count / 200  # 200 words per minute (as per plan)
            
            # Readability score (FREE) - Flesch score 0-100, higher = easier
            flesch_score = textstat.flesch_reading_ease(full_text)
            
            # Extract keywords using YAKE algorithm (FREE, better than regex)
            try:
                import yake
                kw_extractor = yake.KeywordExtractor(
                    lan="en",
                    n=3,  # Extract 1-3 word phrases
                    dedupLim=0.7,
                    top=8  # Top 8 keywords
                )
                yake_keywords = kw_extractor.extract_keywords(full_text)
                # YAKE returns (keyword, score) tuples, lower score = better
                keywords = [kw[0] for kw in yake_keywords]  # Extract the keyword (index 0), not the score (index 1)
                
            except Exception as e:
                logger.warning(f"YAKE keyword extraction failed for article {article.id}: {e}")
                # Fallback to simple title extraction
                import re
                title_words = re.findall(r'\b[A-Za-z]{3,}\b', article.title.lower())
                stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her', 'was', 'one', 'our', 'had', 'what', 'has', 'have', 'with', 'this', 'that', 'they', 'will', 'been', 'from', 'said', 'about', 'their'}
                keywords = [word for word in title_words if word not in stop_words][:8]
            
            # Sentiment analysis using spacytextblob (better than word counting)
            sentiment_score = 0.0  # Default neutral
            try:
                # Import spacytextblob for sentiment analysis
                import spacy
                from spacytextblob.spacytextblob import SpacyTextBlob
                
                # Use small model with textblob
                nlp_sentiment = spacy.load("en_core_web_sm")
                nlp_sentiment.add_pipe('spacytextblob')
                
                # Analyze sentiment on title + first 500 chars (for performance)
                sentiment_text = f"{article.title} {content[:500]}"
                doc = nlp_sentiment(sentiment_text)
                sentiment_score = doc._.polarity  # Returns -1.0 to 1.0
                
            except Exception as e:
                logger.warning(f"Sentiment analysis failed for article {article.id}: {e}")
                # Leave sentiment as 0.0 (neutral) for MVP if spacytextblob fails
                sentiment_score = 0.0
            
            # Update existing Article fields directly (following plan integration)
            article.word_count = word_count
            article.read_time_minutes = reading_time_minutes
            article.readability_score = flesch_score  # NEW: Store readability score
            article.keywords = keywords
            article.sentiment_score = sentiment_score
            article.save(update_fields=[
                'word_count', 'read_time_minutes', 'readability_score', 
                'keywords', 'sentiment_score'
            ])
            
            # PAID: Style tone classification using GPT-4o-mini
            style_prompt = self.prompts.linguistic_analysis_prompt(article.title, content[:2000])
            
            ai_response = self.ai_service.call_llm(
                prompt=style_prompt,
                operation='linguistic_analysis',
                max_tokens=50,
                temperature=0.0
            )
            
            if ai_response.success:
                validation_result = self.prompts.validate_linguistic_output(ai_response.content)
                if validation_result['success']:
                    linguistic_data = validation_result['data']
                    
                    # Store style_tone in analysis record
                    analysis_record.style_tone = linguistic_data.get('style_tone')
                    analysis_record.language_confidence = linguistic_data.get('language_confidence', 0.0)
                    analysis_record.save()
                    
                    # Store additional data we calculated
                    linguistic_data['word_count'] = word_count
                    linguistic_data['reading_time_minutes'] = reading_time_minutes
                    linguistic_data['readability_score'] = flesch_score
                    linguistic_data['keywords'] = keywords
                    linguistic_data['sentiment_score'] = sentiment_score
                else:
                    raise ValueError(f"Invalid linguistic analysis output: {validation_result['error']}")
            else:
                raise ValueError(f"AI service failed: {ai_response.error_message}")
            
            duration_ms = int((time.time() - stage_start) * 1000)
            
            return {
                'success': True,
                'data': linguistic_data,
                'duration_ms': duration_ms,
                'cost': Decimal(str(ai_response.usage.get('total_cost', 0))),
                'tokens_input': ai_response.usage.get('prompt_tokens', 0),
                'tokens_output': ai_response.usage.get('completion_tokens', 0)
            }
            
        except Exception as e:
            logger.error(f"Linguistic analysis failed for article {article.id}: {e}")
            duration_ms = int((time.time() - stage_start) * 1000)
            return {
                'success': False,
                'error': str(e),
                'duration_ms': duration_ms,
                'cost': Decimal('0.00')
            }
    
    def _stage_3_entity_extraction(self, article: Article, content: str) -> Dict[str, Any]:
        """
        Stage 3: Named entity extraction using spaCy (CPU-only, FREE).
        
        Extracts entities and ticker symbols, stores in Article.entities field.
        """
        stage_start = time.time()
        
        try:
            if not nlp:
                raise ValueError("spaCy model not loaded")
            
            # Process text with spaCy
            text_sample = f"{article.title} {content[:3000]}"  # Limit to 3000 chars
            doc = nlp(text_sample)
            
            # Extract entities from spaCy
            entities = []
            entity_counts = {}
            
            for ent in doc.ents:
                entity_name = ent.text.strip()
                entity_type = self._map_spacy_entity_type(ent.label_)
                
                if len(entity_name) < 2 or len(entity_name) > 100:
                    continue
                
                # Count mentions
                if entity_name in entity_counts:
                    entity_counts[entity_name]['mentions'] += 1
                else:
                    entity_counts[entity_name] = {
                        'name': entity_name,
                        'type': entity_type,
                        'mentions': 1,
                        'confidence': 0.9  # High confidence for spaCy
                    }
            
            # Extract ticker symbols with regex
            ticker_pattern = r'\$([A-Z]{2,6})'
            tickers = re.findall(ticker_pattern, content)
            
            for ticker in tickers:
                ticker_name = f"${ticker}"
                if ticker_name in entity_counts:
                    entity_counts[ticker_name]['mentions'] += 1
                else:
                    entity_counts[ticker_name] = {
                        'name': ticker_name,
                        'type': 'FINANCIAL_ASSET',
                        'mentions': 1,
                        'confidence': 0.95
                    }
            
            # Convert to list and filter by relevance
            entities = list(entity_counts.values())
            
            # Sort by mention count and take top 15
            entities = sorted(entities, key=lambda x: x['mentions'], reverse=True)[:15]
            
            # Store in Article.entities field (JSONField)
            article.entities = {
                'extracted_entities': entities,
                'extraction_method': 'spacy_en_core_web_lg',
                'extracted_at': django_timezone.now().isoformat()
            }
            article.save(update_fields=['entities'])
            
            duration_ms = int((time.time() - stage_start) * 1000)
            
            return {
                'success': True,
                'entities': entities,
                'entities_count': len(entities),
                'duration_ms': duration_ms,
                'cost': Decimal('0.00'),  # CPU-only, FREE
                'tokens_input': 0,
                'tokens_output': 0
            }
            
        except Exception as e:
            logger.error(f"Entity extraction failed for article {article.id}: {e}")
            duration_ms = int((time.time() - stage_start) * 1000)
            return {
                'success': False,
                'error': str(e),
                'duration_ms': duration_ms,
                'cost': Decimal('0.00')
            }
    
    def _stage_4_entity_resolution(self, extracted_entities: List[Dict]) -> List[int]:
        """
        Stage 4: Entity resolution with deduplication (CPU-only).
        
        Implements the exact lookup-or-create algorithm from the plan.
        """
        entity_ids = []
        
        for entity_info in extracted_entities:
            try:
                entity = self._resolve_entity(
                    name=entity_info['name'],
                    entity_type=entity_info['type'],
                    confidence=entity_info['confidence']
                )
                entity_ids.append(entity.id)
            except Exception as e:
                logger.error(f"Entity resolution failed for {entity_info['name']}: {e}")
                continue
        
        return entity_ids
    
    def _stage_5_event_extraction(self, article: Article, content: str) -> Dict[str, Any]:
        """
        Stage 5: Event extraction using GPT-4o-mini.
        
        Identifies main event for later resolution and clustering.
        """
        stage_start = time.time()
        
        try:
            # Prepare event extraction prompt
            event_prompt = self.prompts.event_detection_prompt(article.title, content[:2500])
            
            ai_response = self.ai_service.call_llm(
                prompt=event_prompt,
                operation='event_detection',
                max_tokens=600,
                temperature=0.1
            )
            
            if ai_response.success:
                # Parse and validate response
                import json
                try:
                    event_data = json.loads(ai_response.content.strip())
                    main_event = event_data.get('main_event')
                    timeline = event_data.get('timeline', {})
                    
                    if not main_event:
                        # Fallback: create basic event from article
                        main_event = {
                            'title': article.title,
                            'abstract': article.description or article.title,
                            'facts': [f"Published: {article.published_at.strftime('%Y-%m-%d')}"],
                            'event_type': 'other',
                            'significance': 'moderate'
                        }
                    
                    duration_ms = int((time.time() - stage_start) * 1000)
                    
                    return {
                        'success': True,
                        'main_event': main_event,
                        'timeline': timeline,
                        'duration_ms': duration_ms,
                        'cost': Decimal(str(ai_response.usage.get('total_cost', 0.00005))),
                        'tokens_input': ai_response.usage.get('prompt_tokens', 0),
                        'tokens_output': ai_response.usage.get('completion_tokens', 0)
                    }
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse event extraction JSON: {e}")
                    # Fallback to basic event
                    main_event = {
                        'title': article.title,
                        'abstract': article.description or article.title,
                        'facts': [f"Published: {article.published_at.strftime('%Y-%m-%d')}"]
                    }
                    
                    duration_ms = int((time.time() - stage_start) * 1000)
                    return {
                        'success': True,
                        'main_event': main_event,
                        'duration_ms': duration_ms,
                        'cost': Decimal(str(ai_response.usage.get('total_cost', 0.00005)))
                    }
            else:
                raise ValueError(f"AI service failed: {ai_response.error_message}")
            
        except Exception as e:
            logger.error(f"Event extraction failed for article {article.id}: {e}")
            duration_ms = int((time.time() - stage_start) * 1000)
            return {
                'success': False,
                'error': str(e),
                'duration_ms': duration_ms,
                'cost': Decimal('0.00')
            }
    
    def _stage_6_region_classification(self, article: Article, content: str, analysis_record: ArticleAnalysis) -> Dict[str, Any]:
        """
        Stage 6: Region classification using GPT-4o-mini.
        
        Updates Article.primary_region and Article.regions fields.
        """
        stage_start = time.time()
        
        try:
            # Get available regions with descriptions
            available_regions = list(Region.objects.all().values('code', 'name', 'description'))
            if not available_regions:
                raise ValueError("No regions available in database")
            
            # Prepare region classification prompt
            region_prompt = self.prompts.region_classification_prompt(article.title, content[:2500], available_regions)
            
            ai_response = self.ai_service.call_llm(
                prompt=region_prompt,
                operation='region_classification',
                max_tokens=300,
                temperature=0.1
            )
            
            if ai_response.success:
                # Validate and parse response
                valid_options = [r['code'] for r in available_regions]
                validation_result = self.prompts.validate_classification_output(ai_response.content, valid_options)
                
                if validation_result['success']:
                    region_data = validation_result['data']
                    
                    primary_region_code = region_data.get('primary_region')
                    primary_confidence = region_data.get('primary_region_confidence', 0.0)
                    secondary_regions = region_data.get('secondary_regions', [])
                    
                    # Update Article fields
                    with transaction.atomic():
                        # Set primary region
                        if primary_region_code and primary_confidence > 0.5:
                            try:
                                primary_region = Region.objects.get(code=primary_region_code)
                                article.primary_region = primary_region
                                analysis_record.primary_region_confidence = primary_confidence
                                
                                # Add to M2M regions
                                article.regions.add(primary_region)
                            except Region.DoesNotExist:
                                logger.warning(f"Primary region {primary_region_code} not found")
                        
                        # Add secondary regions
                        for region_code in secondary_regions:
                            try:
                                region = Region.objects.get(code=region_code)
                                article.regions.add(region)
                            except Region.DoesNotExist:
                                logger.warning(f"Secondary region {region_code} not found")
                        
                        # Save changes
                        article.save(update_fields=['primary_region'])
                        analysis_record.secondary_regions = secondary_regions
                        analysis_record.save()
                    
                    duration_ms = int((time.time() - stage_start) * 1000)
                    
                    return {
                        'success': True,
                        'primary_region': primary_region_code,
                        'primary_confidence': primary_confidence,
                        'secondary_regions': secondary_regions,
                        'duration_ms': duration_ms,
                        'cost': Decimal(str(ai_response.usage.get('total_cost', 0.00005))),
                        'tokens_input': ai_response.usage.get('prompt_tokens', 0),
                        'tokens_output': ai_response.usage.get('completion_tokens', 0)
                    }
                else:
                    raise ValueError(f"Invalid region classification output: {validation_result['error']}")
            else:
                raise ValueError(f"AI service failed: {ai_response.error_message}")
            
        except Exception as e:
            logger.error(f"Region classification failed for article {article.id}: {e}")
            duration_ms = int((time.time() - stage_start) * 1000)
            return {
                'success': False,
                'error': str(e),
                'duration_ms': duration_ms,
                'cost': Decimal('0.00')
            }
    
    def _stage_7_topic_classification(self, article: Article, content: str, analysis_record: ArticleAnalysis) -> Dict[str, Any]:
        """
        Stage 7: Topic classification using GPT-4o-mini.
        
        Updates Article.primary_topic and Article.topics fields.
        """
        stage_start = time.time()
        
        try:
            # Get available topics with descriptions
            available_topics = list(Topic.objects.all().values('slug', 'name', 'description'))
            if not available_topics:
                raise ValueError("No topics available in database")
            
            # Prepare topic classification prompt
            topic_prompt = self.prompts.topic_classification_prompt(article.title, content[:2500], available_topics)
            
            ai_response = self.ai_service.call_llm(
                prompt=topic_prompt,
                operation='topic_classification',
                max_tokens=400,
                temperature=0.1
            )
            
            if ai_response.success:
                # Validate and parse response
                valid_options = [t['slug'] for t in available_topics]
                validation_result = self.prompts.validate_classification_output(ai_response.content, valid_options)
                
                if validation_result['success']:
                    topic_data = validation_result['data']
                    
                    primary_topic_slug = topic_data.get('primary_topic')
                    primary_confidence = topic_data.get('primary_topic_confidence', 0.0)
                    secondary_topics = topic_data.get('secondary_topics', [])
                    
                    # Update Article fields
                    with transaction.atomic():
                        # Set primary topic
                        if primary_topic_slug and primary_confidence > 0.5:
                            try:
                                primary_topic = Topic.objects.get(slug=primary_topic_slug)
                                article.primary_topic = primary_topic
                                analysis_record.primary_topic_confidence = primary_confidence
                                
                                # Add to M2M topics
                                article.topics.add(primary_topic)
                            except Topic.DoesNotExist:
                                logger.warning(f"Primary topic {primary_topic_slug} not found")
                        
                        # Add secondary topics
                        for topic_slug in secondary_topics:
                            try:
                                topic = Topic.objects.get(slug=topic_slug)
                                article.topics.add(topic)
                            except Topic.DoesNotExist:
                                logger.warning(f"Secondary topic {topic_slug} not found")
                        
                        # Save changes
                        article.save(update_fields=['primary_topic'])
                        analysis_record.secondary_topics = secondary_topics
                        analysis_record.save()
                    
                    duration_ms = int((time.time() - stage_start) * 1000)
                    
                    return {
                        'success': True,
                        'primary_topic': primary_topic_slug,
                        'primary_confidence': primary_confidence,
                        'secondary_topics': secondary_topics,
                        'duration_ms': duration_ms,
                        'cost': Decimal(str(ai_response.usage.get('total_cost', 0.00007))),
                        'tokens_input': ai_response.usage.get('prompt_tokens', 0),
                        'tokens_output': ai_response.usage.get('completion_tokens', 0)
                    }
                else:
                    raise ValueError(f"Invalid topic classification output: {validation_result['error']}")
            else:
                raise ValueError(f"AI service failed: {ai_response.error_message}")
            
        except Exception as e:
            logger.error(f"Topic classification failed for article {article.id}: {e}")
            duration_ms = int((time.time() - stage_start) * 1000)
            return {
                'success': False,
                'error': str(e),
                'duration_ms': duration_ms,
                'cost': Decimal('0.00')
            }
    
    def _stage_8_event_resolution(self, main_event: Dict, entity_ids: List[int], article: Article) -> Optional[int]:
        """
        Stage 8: Event resolution with hash-based deduplication and semantic clustering.
        
        Following exact plan algorithm:
        1. Generate event hash for exact matching
        2. If hash matches, link to existing event
        3. If no match, try semantic matching on recent events
        4. If no semantic match, create new event
        """
        try:
            if not main_event:
                return None
            
            # Generate event hash (plan algorithm)
            event_title = main_event.get('title', article.title)
            facts = main_event.get('facts', [])
            event_hash = Event.generate_event_hash(event_title, facts)
            
            # Step 1: Try exact hash match
            try:
                existing_event = Event.objects.get(event_hash=event_hash)
                
                # Update existing event
                existing_event.last_seen_at = article.published_at
                existing_event.article_count += 1
                existing_event.save(update_fields=['last_seen_at', 'article_count'])
                
                # Link article to existing event
                ArticleEvent.objects.get_or_create(
                    article=article,
                    defaults={'event': existing_event}
                )
                
                logger.info(f"Article {article.id} linked to existing event {existing_event.id} via hash match")
                return existing_event.id
                
            except Event.DoesNotExist:
                pass
            
            # Step 2: Try semantic matching on recent events
            from django.utils import timezone
            from datetime import timedelta
            
            # Get article embedding from summariser
            article_embedding = article.summary.embedding if article.summary else None
            
            if article_embedding:
                # Find similar events from last 48 hours
                recent_cutoff = timezone.now() - timedelta(hours=48)
                
                from pgvector.django import CosineDistance
                similar_events = Event.objects.filter(
                    last_seen_at__gte=recent_cutoff,
                    centroid_embed__isnull=False
                ).annotate(
                    distance=CosineDistance('centroid_embed', article_embedding)
                ).filter(
                    distance__lt=0.18  # Lower distance = more similar
                ).order_by('distance')
                
                # Check entity overlap for each candidate
                for event in similar_events:
                    event_entity_ids = set(
                        EventEntity.objects.filter(event=event)
                        .values_list('entity_id', flat=True)
                    )
                    
                    shared_entities = len(event_entity_ids.intersection(entity_ids))
                    
                    if shared_entities >= 2:
                        # Found matching event, update it
                        event.last_seen_at = article.published_at
                        event.article_count += 1
                        event.update_centroid(article_embedding)  # Updates running mean
                        
                        # Link article to event
                        ArticleEvent.objects.create(
                            article=article,
                            event=event
                        )
                        
                        # Link entities to event
                        for entity_id in entity_ids:
                            try:
                                entity = Entity.objects.get(id=entity_id)
                                EventEntity.objects.get_or_create(
                                    event=event,
                                    entity=entity
                                )
                            except Entity.DoesNotExist:
                                continue
                        
                        logger.info(f"Article {article.id} linked to existing event {event.id} via semantic match")
                        return event.id
            
            # Step 3: Create new event
            new_event = Event.objects.create(
                title=event_title,
                abstract=main_event.get('abstract', article.description or article.title),
                facts=facts,
                event_hash=event_hash,
                first_seen_at=article.published_at,
                last_seen_at=article.published_at,
                centroid_embed=article_embedding or [0.0] * 1536,  # Use article embedding or placeholder
                article_count=1
            )
            
            # Link article to new event
            ArticleEvent.objects.create(
                article=article,
                event=new_event
            )
            
            # Link entities to event
            for entity_id in entity_ids:
                try:
                    entity = Entity.objects.get(id=entity_id)
                    EventEntity.objects.get_or_create(
                        event=new_event,
                        entity=entity
                    )
                except Entity.DoesNotExist:
                    continue
            
            logger.info(f"Article {article.id} linked to new event {new_event.id}")
            return new_event.id
                
        except Exception as e:
            logger.error(f"Event resolution failed for article {article.id}: {e}")
            return None
    
    def _stage_9_persist_results(self, article: Article, results: Dict, analysis_record: ArticleAnalysis):
        """
        Stage 9: Persist results to database.
        
        Most data is already persisted in individual stages to existing Article fields.
        This just handles entity linking and final cleanup.
        """
        try:
            # Link entities to article
            entity_ids = results.get('entity_resolution', {}).get('entity_ids', [])
            
            # Clear existing entity links
            ArticleEntity.objects.filter(article=article).delete()
            
            # Create new entity links (use get_or_create to avoid duplicates)
            for entity_id in entity_ids:
                try:
                    entity = Entity.objects.get(id=entity_id)
                    ArticleEntity.objects.get_or_create(
                        article=article,
                        entity=entity,
                        defaults={
                            'confidence': 0.9,  # Default confidence
                            'mention_count': 1   # Default mention count
                        }
                    )
                except Entity.DoesNotExist:
                    logger.warning(f"Entity {entity_id} not found for linking")
            
            # Mark analysis stages as completed
            analysis_record.mark_stage_completed('entity_linking')
            analysis_record.mark_stage_completed('persistence')
            
            logger.info(f"Persisted analysis results for article {article.id}")
            
        except Exception as e:
            logger.error(f"Failed to persist results for article {article.id}: {e}")
            raise
    
    # Helper methods
    
    def _map_spacy_entity_type(self, spacy_label: str) -> str:
        """Map spaCy entity labels to our taxonomy."""
        mapping = {
            'PERSON': 'PERSON',
            'ORG': 'ORGANIZATION', 
            'GPE': 'LOCATION',  # Geopolitical entity
            'LOC': 'LOCATION',
            'FAC': 'FACILITY',
            'EVENT': 'EVENT',
            'WORK_OF_ART': 'WORK',
            'PRODUCT': 'PRODUCT',
            'LAW': 'LAW',
            'MONEY': 'FINANCIAL_ASSET',
            'DATE': 'OTHER',
            'TIME': 'OTHER',
            'PERCENT': 'OTHER',
            'QUANTITY': 'OTHER',
            'ORDINAL': 'OTHER',
            'CARDINAL': 'OTHER'
        }
        return mapping.get(spacy_label, 'OTHER')
    
    def _resolve_entity(self, name: str, entity_type: str, confidence: float = 0.9) -> Entity:
        """
        Entity resolver following exact plan algorithm.
        
        1. Canonical name lookup
        2. Alias lookup
        3. Embedding similarity search (MiniLM 384-dim, threshold 0.10)
        4. Create new entity
        """
        canonical_name = Entity.canonicalize_name(name)
        
        # 1. Exact canonical match
        try:
            return Entity.objects.get(canonical_name=canonical_name)
        except Entity.DoesNotExist:
            pass
        
        # 2. Alias match
        try:
            alias = EntityAlias.objects.select_related('entity').get(alias=canonical_name)
            return alias.entity
        except EntityAlias.DoesNotExist:
            pass
        
        # 3. Embedding similarity search (following plan exactly)
        MIN_SIM = 0.10  # Plan threshold
        try:
            # Generate embedding for the name
            embedding = self._generate_entity_embedding(canonical_name)
            
            if embedding is not None:
                # Use pgvector for similarity search
                from pgvector.django import CosineDistance
                
                similar_entities = Entity.objects.filter(
                    entity_type=entity_type,  # Same type only
                    embedding__isnull=False
                ).annotate(
                    distance=CosineDistance('embedding', embedding)
                ).filter(
                    distance__lt=MIN_SIM  # Lower distance = more similar
                ).order_by('distance').first()
                
                if similar_entities:
                    # Found similar entity, add alias and return existing
                    EntityAlias.objects.get_or_create(
                        entity=similar_entities,
                        alias=canonical_name,
                        defaults={'alias_type': 'embedding_match'}
                    )
                    return similar_entities
        except Exception as e:
            logger.warning(f"Embedding similarity search failed for {canonical_name}: {e}")
        
        # 4. Create new entity with embedding
        with transaction.atomic():
            entity = Entity.objects.create(
                canonical_name=canonical_name,
                display_name=name,
                entity_type=entity_type,
                embedding=self._generate_entity_embedding(canonical_name)
            )
            
            # Create alias if different from canonical
            if name.lower() != canonical_name:
                EntityAlias.objects.create(
                    entity=entity,
                    alias=name.lower(),
                    alias_type='spelling'
                )
        
        return entity
    
    def _generate_entity_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate 1536-dimensional embedding for entity using OpenAI.
        
        Following plan specification for entity deduplication.
        """
        try:
            # Use OpenAI embeddings (same as summariser)
            ai_response = self.ai_service.call_llm(
                prompt=text,
                operation='text_embedding',
                model='text-embedding-3-small'
            )
            
            if ai_response.success and ai_response.embedding:
                return ai_response.embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding for {text}: {e}")
        return None 