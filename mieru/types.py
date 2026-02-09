from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class Review:
    review_id: str
    text: str
    rating: Optional[float] = None
    meta: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class EvidenceSpan:
    review_id: str
    sentence: str
    raw_text: str
    rating: Optional[float] = None
