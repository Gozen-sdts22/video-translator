"""Tests for Segment data model."""

import pytest
from datetime import datetime
from models.segment import Segment, Suggestion, DictionaryEntry


class TestSuggestion:
    """Tests for Suggestion dataclass."""

    def test_create_suggestion(self):
        suggestion = Suggestion(
            type="recognition",
            field="text_ja",
            original="おしめん",
            suggested="推しメン",
            reason="アイドル用語の修正",
        )
        assert suggestion.type == "recognition"
        assert suggestion.add_to_dict is False

    def test_with_dict_flag(self):
        suggestion = Suggestion(
            type="recognition",
            field="text_ja",
            original="test",
            suggested="Test",
            reason="Test reason",
            add_to_dict=True,
        )
        assert suggestion.add_to_dict is True


class TestSegment:
    """Tests for Segment dataclass."""

    def test_create_segment(self):
        segment = Segment(
            id=1,
            start=0.5,
            end=3.0,
            speaker="SPEAKER_00",
            text_ja="こんにちは",
        )
        assert segment.id == 1
        assert segment.start == 0.5
        assert segment.end == 3.0
        assert segment.speaker == "SPEAKER_00"
        assert segment.text_ja == "こんにちは"
        assert segment.text_zh == ""
        assert segment.status == "ok"
        assert segment.suggestions == []

    def test_duration_property(self):
        segment = Segment(
            id=1,
            start=1.0,
            end=4.5,
            speaker="SPEAKER_00",
            text_ja="Test",
        )
        assert segment.duration == 3.5

    def test_to_dict(self):
        segment = Segment(
            id=1,
            start=0.5,
            end=3.0,
            speaker="SPEAKER_00",
            text_ja="こんにちは",
            text_zh="你好",
        )
        data = segment.to_dict()
        assert data["id"] == 1
        assert data["start"] == 0.5
        assert data["text_ja"] == "こんにちは"
        assert data["text_zh"] == "你好"

    def test_from_dict(self):
        data = {
            "id": 1,
            "start": 0.5,
            "end": 3.0,
            "speaker": "SPEAKER_00",
            "text_ja": "こんにちは",
            "text_zh": "你好",
        }
        segment = Segment.from_dict(data)
        assert segment.id == 1
        assert segment.text_ja == "こんにちは"

    def test_round_trip(self):
        original = Segment(
            id=1,
            start=0.5,
            end=3.0,
            speaker="SPEAKER_00",
            text_ja="Test",
            text_zh="测试",
            status="warning",
            suggestions=[
                Suggestion(
                    type="translation",
                    field="text_zh",
                    original="测试",
                    suggested="考试",
                    reason="Better translation",
                )
            ],
        )
        data = original.to_dict()
        restored = Segment.from_dict(data)

        assert restored.id == original.id
        assert restored.start == original.start
        assert restored.status == original.status
        assert len(restored.suggestions) == 1
        assert restored.suggestions[0].type == "translation"


class TestDictionaryEntry:
    """Tests for DictionaryEntry dataclass."""

    def test_create_entry(self):
        entry = DictionaryEntry(
            id=1,
            wrong="おしめん",
            correct="推しメン",
            category="アイドル用語",
        )
        assert entry.wrong == "おしめん"
        assert entry.correct == "推しメン"
        assert entry.used_count == 0

    def test_to_dict(self):
        entry = DictionaryEntry(
            id=1,
            wrong="test",
            correct="Test",
            category="general",
        )
        data = entry.to_dict()
        assert data["id"] == 1
        assert data["wrong"] == "test"
        assert "created_at" in data

    def test_from_dict(self):
        data = {
            "id": 1,
            "wrong": "test",
            "correct": "Test",
            "category": "general",
            "created_at": "2024-01-01T00:00:00",
            "used_count": 5,
        }
        entry = DictionaryEntry.from_dict(data)
        assert entry.id == 1
        assert entry.used_count == 5
        assert isinstance(entry.created_at, datetime)
