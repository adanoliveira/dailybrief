"""
Unified content processing models.

Provides consistent data structures for all content processors (AI, algorithmic, etc.)
to ensure proper serialization and frontend compatibility.
"""
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class ContentBlock:
    """
    Unified content block structure for all processors.
    
    This replaces the multiple ContentBlock definitions across different modules
    to ensure consistency between AI processor, algorithmic processor, and database storage.
    """
    type: str  # heading, paragraph, image, video, quote, list, twitter_embed, video_embed, editorial_note
    content: str
    level: Optional[int] = None  # For headings (1-6)
    position: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ContentBlock to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContentBlock':
        """Create ContentBlock from dictionary (for deserialization)."""
        return cls(
            type=data.get('type', ''),
            content=data.get('content', ''),
            level=data.get('level'),
            position=data.get('position', 0),
            metadata=data.get('metadata', {})
        )


@dataclass 
class ProcessingResult:
    """
    Unified processing result structure for all processors.
    
    Used by both AI and algorithmic processors to ensure consistent
    return types and database storage.
    """
    success: bool
    clean_content: str = ""
    content_blocks: List[ContentBlock] = None
    extracted_metadata: Dict[str, Any] = None
    quality_score: float = 0.0
    processing_time_ms: int = 0
    error_message: str = ""
    raw_response: str = ""  # For debugging - stores raw AI response
    
    def __post_init__(self):
        if self.content_blocks is None:
            self.content_blocks = []
        if self.extracted_metadata is None:
            self.extracted_metadata = {}
    
    def get_content_blocks_as_dicts(self) -> List[Dict[str, Any]]:
        """Get content blocks as dictionaries for JSON serialization."""
        return [block.to_dict() for block in self.content_blocks]


def serialize_content_blocks(content_blocks: List[ContentBlock]) -> List[Dict[str, Any]]:
    """Serialize content blocks for database storage."""
    return [block.to_dict() for block in content_blocks]


def deserialize_content_blocks(data: List[Dict[str, Any]]) -> List[ContentBlock]:
    """Deserialize content blocks from database storage."""
    return [ContentBlock.from_dict(block_data) for block_data in data] 