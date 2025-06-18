"""
Digest Services Package

This package contains the core business logic for digest generation:
- DigestService: Main orchestrator for digest creation and management
- DigestContentSelector: Content filtering and event grouping logic
- DigestAIGenerator: AI-powered content synthesis and enhancement
"""

from .digest_service import DigestService
from .content_selector import DigestContentSelector
from .ai_generator import DigestAIGenerator

__all__ = [
    'DigestService',
    'DigestContentSelector', 
    'DigestAIGenerator',
] 