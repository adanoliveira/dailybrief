"""
AI Provider Service for DailyBrief - Pure AI Infrastructure Layer.

This module provides a unified interface for communicating with various AI providers
(OpenAI, Anthropic) without any domain-specific logic. It serves other apps by
abstracting away AI provider complexity.

Following SOLID principles with clean separation of concerns.
"""
import os
import time
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from decimal import Decimal

from django.conf import settings
from django.utils import timezone

# Import OpenAI client
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# Import Anthropic client (for future fallback support)
try:
    import anthropic
    from anthropic import Anthropic
except ImportError:
    anthropic = None
    Anthropic = None

from .models import AIProviderConfig, AIProviderUsage


logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """
    Standardized response structure for all LLM operations.
    
    Provides consistent interface regardless of the underlying provider.
    Pure data structure without domain logic.
    """
    content: str
    success: bool
    usage: Dict[str, int]
    response_time: float
    provider: str
    model: str
    error_message: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


@dataclass
class EmbeddingResponse:
    """
    Standardized response structure for embedding operations.
    
    Provides consistent interface for vector embedding generation.
    """
    embeddings: List[List[float]]
    success: bool
    usage: Dict[str, int]
    response_time: float
    provider: str
    model: str
    input_texts: List[str]
    error_message: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


class AIProviderService:
    """
    Pure AI provider service - handles only AI communication infrastructure.
    
    This service abstracts away AI provider complexity and serves other apps
    without embedding domain-specific logic. Other apps import this service
    to get AI capabilities.
    
    Responsibilities:
    - Provider client management
    - Request routing and error handling  
    - Usage tracking and cost monitoring
    - Response standardization
    
    NOT responsible for:
    - Domain-specific prompt engineering
    - Business logic interpretation
    - Content analysis or scoring
    """
    
    def __init__(self):
        """Initialize the service with provider clients."""
        self._openai_client: Optional[OpenAI] = None
        self._anthropic_client: Optional[Anthropic] = None
        self._initialize_clients()
    
    def _initialize_clients(self) -> None:
        """Initialize AI provider clients based on available API keys."""
        # Initialize OpenAI client
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if openai_api_key and OpenAI:
            try:
                self._openai_client = OpenAI(api_key=openai_api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
        else:
            logger.warning("OpenAI API key not found or openai package not installed")
        
        # Initialize Anthropic client (for future use)
        anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        if anthropic_api_key and Anthropic:
            try:
                self._anthropic_client = Anthropic(api_key=anthropic_api_key)
                logger.info("Anthropic client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")
    
    def get_provider_config(self, operation: str) -> Optional[AIProviderConfig]:
        """
        Get the active provider configuration for a specific operation.
        
        Args:
            operation: The operation type (e.g., 'quality_assessment', 'summarization')
            
        Returns:
            AIProviderConfig instance or None if not found
        """
        try:
            return AIProviderConfig.objects.filter(
                operation=operation,
                is_active=True
            ).first()
        except Exception as e:
            logger.error(f"Error fetching provider config for {operation}: {e}")
            return None
    
    def call_llm(
        self,
        prompt: str,
        operation: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.3,
        model_override: Optional[str] = None,
        response_format: Optional[str] = None
    ) -> LLMResponse:
        """
        Make a call to the configured LLM provider.
        
        Pure infrastructure method - handles only the mechanics of calling AI.
        Domain logic should be in the calling service.
        
        Args:
            prompt: The input prompt for the LLM
            operation: Operation type for provider selection
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
            model_override: Override the configured model
            response_format: Expected response format hint
            
        Returns:
            LLMResponse with standardized result
        """
        start_time = time.time()
        
        # Get provider configuration
        config = self.get_provider_config(operation)
        if not config:
            return LLMResponse(
                content="",
                success=False,
                usage={},
                response_time=0.0,
                provider="none",
                model="none",
                error_message=f"No active provider configuration found for operation: {operation}"
            )
        
        provider = config.provider
        model = model_override or config.model
        
        # Route to appropriate provider
        if provider == 'openai':
            return self._call_openai(prompt, model, max_tokens, temperature, operation, start_time)
        elif provider == 'anthropic':
            return self._call_anthropic(prompt, model, max_tokens, temperature, operation, start_time)
        else:
            return LLMResponse(
                content="",
                success=False,
                usage={},
                response_time=time.time() - start_time,
                provider=provider,
                model=model,
                error_message=f"Unsupported provider: {provider}"
            )
    
    def _call_openai(
        self,
        prompt: str,
        model: str,
        max_tokens: Optional[int],
        temperature: float,
        operation: str,
        start_time: float
    ) -> LLMResponse:
        """
        Make a call to OpenAI API.
        
        Pure infrastructure method - no domain logic.
        """
        if not self._openai_client:
            return LLMResponse(
                content="",
                success=False,
                usage={},
                response_time=time.time() - start_time,
                provider="openai",
                model=model,
                error_message="OpenAI client not initialized"
            )
        
        try:
            # Handle max_tokens=None by using high defaults for content extraction
            # or letting OpenAI use model defaults for other operations
            api_params = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature
            }
            
            if max_tokens is not None:
                api_params["max_tokens"] = max_tokens
            elif operation == "content_extraction":
                # For content extraction, use a high token limit based on model capabilities
                # Large articles can have 100+ blocks requiring 20k-30k+ output tokens
                model_lower = model.lower()
                if "gpt-4.1" in model_lower:
                    # GPT-4.1 can handle up to 32,768 output tokens
                    api_params["max_tokens"] = 30000
                elif "gpt-4o" in model_lower or "gpt-4" in model_lower:
                    # GPT-4o and GPT-4 can handle 4k-8k output tokens safely
                    api_params["max_tokens"] = 8000
                else:
                    # Conservative default for other models
                    api_params["max_tokens"] = 4000
            # For other operations, let OpenAI use model defaults (no max_tokens param)
            
            response = self._openai_client.chat.completions.create(**api_params)
            
            response_time = time.time() - start_time
            content = response.choices[0].message.content or ""
            
            # Extract usage information
            usage = {
                'prompt_tokens': response.usage.prompt_tokens if response.usage else 0,
                'completion_tokens': response.usage.completion_tokens if response.usage else 0,
                'total_tokens': response.usage.total_tokens if response.usage else 0,
            }
            
            # Calculate cost estimate using official OpenAI pricing (as of April 2025)
            cost_estimate = Decimal('0.0')
            model_lower = model.lower()
            
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)
            
            if 'gpt-4.1' in model_lower:
                if 'nano' in model_lower:
                    # GPT-4.1 Nano: $0.10/1M input, $0.40/1M output
                    input_cost = Decimal(str(prompt_tokens)) * Decimal('0.0000001')  # $0.10/1M
                    output_cost = Decimal(str(completion_tokens)) * Decimal('0.0000004')  # $0.40/1M
                    cost_estimate = input_cost + output_cost
                elif 'mini' in model_lower:
                    # GPT-4.1 Mini: $0.40/1M input, $1.60/1M output
                    input_cost = Decimal(str(prompt_tokens)) * Decimal('0.0000004')  # $0.40/1M
                    output_cost = Decimal(str(completion_tokens)) * Decimal('0.0000016')  # $1.60/1M
                    cost_estimate = input_cost + output_cost
                else:
                    # GPT-4.1 (full): $2.00/1M input, $8.00/1M output
                    input_cost = Decimal(str(prompt_tokens)) * Decimal('0.000002')  # $2.00/1M
                    output_cost = Decimal(str(completion_tokens)) * Decimal('0.000008')  # $8.00/1M
                    cost_estimate = input_cost + output_cost
            elif 'gpt-4o-mini' in model_lower:
                # GPT-4o-mini: $0.15/1M input, $0.075/1M output (older pricing)
                input_cost = Decimal(str(prompt_tokens)) * Decimal('0.00000015')  # $0.15/1M
                output_cost = Decimal(str(completion_tokens)) * Decimal('0.000000075')  # $0.075/1M
                cost_estimate = input_cost + output_cost
            
            # Log usage to database
            self._log_usage(
                provider="openai",
                model=model,
                operation=operation,
                usage=usage,
                response_time=response_time,
                success=True,
                request_data={"prompt_length": len(prompt), "max_tokens": max_tokens or "auto", "temperature": temperature},
                response_data={"content_length": len(content)}
            )
            
            return LLMResponse(
                content=content,
                success=True,
                usage=usage,
                response_time=response_time,
                provider="openai",
                model=model,
                raw_response=response.model_dump() if hasattr(response, 'model_dump') else None
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            error_message = str(e)
            
            # Log failed usage
            self._log_usage(
                provider="openai",
                model=model,
                operation=operation,
                usage={},
                response_time=response_time,
                success=False,
                error_message=error_message,
                request_data={"prompt_length": len(prompt), "max_tokens": max_tokens or "auto", "temperature": temperature}
            )
            
            logger.error(f"OpenAI API call failed: {error_message}")
            
            return LLMResponse(
                content="",
                success=False,
                usage={},
                response_time=response_time,
                provider="openai",
                model=model,
                error_message=error_message
            )
    
    def _call_anthropic(
        self,
        prompt: str,
        model: str,
        max_tokens: Optional[int],
        temperature: float,
        operation: str,
        start_time: float
    ) -> LLMResponse:
        """
        Make a call to Anthropic API (placeholder for future implementation).
        """
        # TODO: Implement Anthropic integration when needed
        response_time = time.time() - start_time
        
        return LLMResponse(
            content="",
            success=False,
            usage={},
            response_time=response_time,
            provider="anthropic",
            model=model,
            error_message="Anthropic integration not yet implemented"
        )
    
    def _log_usage(
        self,
        provider: str,
        model: str,
        operation: str,
        usage: Dict[str, int],
        response_time: float,
        success: bool,
        request_data: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        error_message: str = ""
    ) -> None:
        """
        Log AI provider usage to database for cost tracking and monitoring.
        """
        try:
            # Calculate estimated cost using official OpenAI pricing (as of April 2025)
            estimated_cost = Decimal('0.0')
            if provider == 'openai' and success:
                model_lower = model.lower()
                prompt_tokens = usage.get('prompt_tokens', 0)
                completion_tokens = usage.get('completion_tokens', 0)
                
                if 'gpt-4.1' in model_lower:
                    if 'nano' in model_lower:
                        # GPT-4.1 Nano: $0.10/1M input, $0.40/1M output
                        input_cost = Decimal(str(prompt_tokens)) * Decimal('0.0000001')  # $0.10/1M
                        output_cost = Decimal(str(completion_tokens)) * Decimal('0.0000004')  # $0.40/1M
                        estimated_cost = input_cost + output_cost
                    elif 'mini' in model_lower:
                        # GPT-4.1 Mini: $0.40/1M input, $1.60/1M output
                        input_cost = Decimal(str(prompt_tokens)) * Decimal('0.0000004')  # $0.40/1M
                        output_cost = Decimal(str(completion_tokens)) * Decimal('0.0000016')  # $1.60/1M
                        estimated_cost = input_cost + output_cost
                    else:
                        # GPT-4.1 (full): $2.00/1M input, $8.00/1M output
                        input_cost = Decimal(str(prompt_tokens)) * Decimal('0.000002')  # $2.00/1M
                        output_cost = Decimal(str(completion_tokens)) * Decimal('0.000008')  # $8.00/1M
                        estimated_cost = input_cost + output_cost
                elif 'gpt-4o-mini' in model_lower:
                    # GPT-4o-mini: $0.15/1M input, $0.075/1M output (older pricing)
                    input_cost = Decimal(str(prompt_tokens)) * Decimal('0.00000015')  # $0.15/1M
                    output_cost = Decimal(str(completion_tokens)) * Decimal('0.000000075')  # $0.075/1M
                    estimated_cost = input_cost + output_cost
            
            AIProviderUsage.objects.create(
                provider=provider,
                model=model,
                operation=operation,
                prompt_tokens=usage.get('prompt_tokens', 0),
                completion_tokens=usage.get('completion_tokens', 0),
                total_tokens=usage.get('total_tokens', 0),
                estimated_cost=estimated_cost,
                response_time=response_time,
                success=success,
                error_message=error_message,
                request_data=request_data or {},
                response_data=response_data or {}
            )
            
        except Exception as e:
            logger.error(f"Failed to log AI provider usage: {e}")

    def generate_embedding(
        self,
        texts: List[str],
        operation: str = 'embedding_generation',
        model_override: Optional[str] = None,
        dimensions: Optional[int] = None
    ) -> EmbeddingResponse:
        """
        Generate embeddings for one or more texts.
        
        Args:
            texts: List of texts to embed (max 96 per OpenAI batch)
            operation: Operation type for provider selection
            model_override: Override the configured model
            dimensions: Specific dimension count (for supported models)
            
        Returns:
            EmbeddingResponse with embeddings and metadata
        """
        start_time = time.time()
        
        # Validate input
        if not texts or not any(text.strip() for text in texts):
            return EmbeddingResponse(
                embeddings=[],
                success=False,
                usage={},
                response_time=0.0,
                provider="none",
                model="none",
                input_texts=texts,
                error_message="No valid texts provided for embedding"
            )
        
        # OpenAI has a batch limit of 2048 inputs per request
        if len(texts) > 2048:
            return EmbeddingResponse(
                embeddings=[],
                success=False,
                usage={},
                response_time=time.time() - start_time,
                provider="none",
                model="none",
                input_texts=texts,
                error_message=f"Too many texts: {len(texts)}. Maximum is 2048 per batch."
            )
        
        # Get provider configuration
        config = self.get_provider_config(operation)
        if not config:
            return EmbeddingResponse(
                embeddings=[],
                success=False,
                usage={},
                response_time=0.0,
                provider="none",
                model="none",
                input_texts=texts,
                error_message=f"No active provider configuration found for operation: {operation}"
            )
        
        provider = config.provider
        model = model_override or config.model
        
        # Route to appropriate provider
        if provider == 'openai':
            return self._generate_openai_embedding(texts, model, operation, start_time, dimensions)
        else:
            return EmbeddingResponse(
                embeddings=[],
                success=False,
                usage={},
                response_time=time.time() - start_time,
                provider=provider,
                model=model,
                input_texts=texts,
                error_message=f"Embedding not supported for provider: {provider}"
            )
    
    def _generate_openai_embedding(
        self,
        texts: List[str],
        model: str,
        operation: str,
        start_time: float,
        dimensions: Optional[int] = None
    ) -> EmbeddingResponse:
        """
        Generate embeddings using OpenAI API.
        
        Pure infrastructure method - handles only the OpenAI API mechanics.
        """
        if not self._openai_client:
            return EmbeddingResponse(
                embeddings=[],
                success=False,
                usage={},
                response_time=time.time() - start_time,
                provider="openai",
                model=model,
                input_texts=texts,
                error_message="OpenAI client not initialized"
            )
        
        try:
            # Prepare API parameters
            api_params = {
                "model": model,
                "input": texts,
                "encoding_format": "float"
            }
            
            # Add dimensions parameter if specified and model supports it
            if dimensions and model in ['text-embedding-3-small', 'text-embedding-3-large']:
                api_params["dimensions"] = dimensions
            
            # Make API call
            response = self._openai_client.embeddings.create(**api_params)
            
            response_time = time.time() - start_time
            
            # Extract embeddings from response
            embeddings = [embedding.embedding for embedding in response.data]
            
            # Extract usage information
            usage = {
                'prompt_tokens': response.usage.prompt_tokens if response.usage else 0,
                'total_tokens': response.usage.total_tokens if response.usage else 0,
                'completion_tokens': 0  # Embeddings don't have completion tokens
            }
            
            # Calculate cost estimate using official OpenAI embedding pricing
            cost_estimate = Decimal('0.0')
            model_lower = model.lower()
            input_tokens = usage.get('prompt_tokens', 0)
            
            if 'text-embedding-3-small' in model_lower:
                # text-embedding-3-small: $0.020/1M tokens
                cost_estimate = Decimal(str(input_tokens)) * Decimal('0.00000002')  # $0.020/1M
            elif 'text-embedding-3-large' in model_lower:
                # text-embedding-3-large: $0.130/1M tokens  
                cost_estimate = Decimal(str(input_tokens)) * Decimal('0.00000013')  # $0.130/1M
            elif 'text-embedding-ada-002' in model_lower:
                # text-embedding-ada-002: $0.100/1M tokens
                cost_estimate = Decimal(str(input_tokens)) * Decimal('0.0000001')  # $0.100/1M
            
            # Log usage to database
            self._log_usage(
                provider="openai",
                model=model,
                operation=operation,
                usage=usage,
                response_time=response_time,
                success=True,
                request_data={
                    "input_count": len(texts),
                    "total_input_chars": sum(len(text) for text in texts),
                    "dimensions": dimensions
                },
                response_data={
                    "embedding_count": len(embeddings),
                    "embedding_dimensions": len(embeddings[0]) if embeddings else 0
                }
            )
            
            return EmbeddingResponse(
                embeddings=embeddings,
                success=True,
                usage=usage,
                response_time=response_time,
                provider="openai",
                model=model,
                input_texts=texts,
                raw_response=response.model_dump() if hasattr(response, 'model_dump') else None
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            error_message = str(e)
            
            # Log failed usage
            self._log_usage(
                provider="openai",
                model=model,
                operation=operation,
                usage={},
                response_time=response_time,
                success=False,
                error_message=error_message,
                request_data={
                    "input_count": len(texts),
                    "total_input_chars": sum(len(text) for text in texts),
                    "dimensions": dimensions
                }
            )
            
            logger.error(f"OpenAI embedding API call failed: {error_message}")
            
            return EmbeddingResponse(
                embeddings=[],
                success=False,
                usage={},
                response_time=response_time,
                provider="openai",
                model=model,
                input_texts=texts,
                error_message=error_message
            )


# Singleton service instance
_ai_service_instance = None

def get_ai_service() -> AIProviderService:
    """
    Get a singleton instance of AIProviderService.
    
    This is the main interface other apps should use to access AI capabilities.
    
    Returns:
        AIProviderService instance
    """
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = AIProviderService()
    return _ai_service_instance 