"""Shared datatypes for algorithmic content processing."""

from dataclasses import dataclass
from typing import List

from bs4 import Tag


@dataclass
class CandidateElement:
    """Candidate element for main content with Safari-like scoring."""

    element: Tag
    raw_score: float = 0.0
    tag_score_multiplier: float = 1.0
    language_score_multiplier: float = 1.0
    final_score: float = 0.0
    score_density: float = 0.0
    text_nodes: List = None

    def __post_init__(self):
        if self.text_nodes is None:
            self.text_nodes = []
