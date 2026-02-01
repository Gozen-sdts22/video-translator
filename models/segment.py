"""Data models for subtitle segments and suggestions."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Suggestion:
    """A modification suggestion for a segment."""

    type: str  # "recognition" | "translation" | "consistency"
    field: str  # "text_ja" | "text_zh"
    original: str
    suggested: str
    reason: str
    add_to_dict: bool = False


@dataclass
class Segment:
    """A subtitle segment with timing, speaker, and text information."""

    id: int
    start: float  # Start time in seconds
    end: float  # End time in seconds
    speaker: str  # Speaker ID (e.g., "SPEAKER_00")
    text_ja: str  # Japanese text
    text_zh: str = ""  # Chinese text (translation)
    status: str = "ok"  # "ok" | "warning" | "error"
    suggestions: list[Suggestion] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert the segment to a dictionary."""
        return {
            "id": self.id,
            "start": self.start,
            "end": self.end,
            "speaker": self.speaker,
            "text_ja": self.text_ja,
            "text_zh": self.text_zh,
            "status": self.status,
            "suggestions": [
                {
                    "type": s.type,
                    "field": s.field,
                    "original": s.original,
                    "suggested": s.suggested,
                    "reason": s.reason,
                    "add_to_dict": s.add_to_dict,
                }
                for s in self.suggestions
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Segment":
        """Create a Segment from a dictionary."""
        suggestions = [
            Suggestion(
                type=s["type"],
                field=s["field"],
                original=s["original"],
                suggested=s["suggested"],
                reason=s["reason"],
                add_to_dict=s.get("add_to_dict", False),
            )
            for s in data.get("suggestions", [])
        ]
        return cls(
            id=data["id"],
            start=data["start"],
            end=data["end"],
            speaker=data["speaker"],
            text_ja=data["text_ja"],
            text_zh=data.get("text_zh", ""),
            status=data.get("status", "ok"),
            suggestions=suggestions,
        )

    @property
    def duration(self) -> float:
        """Get the duration of the segment in seconds."""
        return self.end - self.start


@dataclass
class DictionaryEntry:
    """A custom dictionary entry for correcting misrecognitions."""

    id: int
    wrong: str  # Misrecognized pattern
    correct: str  # Correct representation
    category: str  # Category (e.g., "idol terms")
    created_at: datetime = field(default_factory=datetime.now)
    used_count: int = 0

    def to_dict(self) -> dict:
        """Convert the entry to a dictionary."""
        return {
            "id": self.id,
            "wrong": self.wrong,
            "correct": self.correct,
            "category": self.category,
            "created_at": self.created_at.isoformat(),
            "used_count": self.used_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DictionaryEntry":
        """Create a DictionaryEntry from a dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()

        return cls(
            id=data["id"],
            wrong=data["wrong"],
            correct=data["correct"],
            category=data.get("category", ""),
            created_at=created_at,
            used_count=data.get("used_count", 0),
        )
