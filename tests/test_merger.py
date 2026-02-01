"""Tests for segment merger functions."""

import pytest
from core.merger import find_best_speaker, merge_segments, consolidate_segments


class TestFindBestSpeaker:
    """Tests for find_best_speaker function."""

    def test_exact_match(self):
        diarization = [
            {"start": 0.0, "end": 5.0, "speaker": "SPEAKER_00"},
        ]
        assert find_best_speaker(0.0, 5.0, diarization) == "SPEAKER_00"

    def test_partial_overlap(self):
        diarization = [
            {"start": 0.0, "end": 3.0, "speaker": "SPEAKER_00"},
            {"start": 3.0, "end": 6.0, "speaker": "SPEAKER_01"},
        ]
        # Segment 1-4 overlaps more with SPEAKER_00 (0-3)
        assert find_best_speaker(1.0, 4.0, diarization) == "SPEAKER_00"

    def test_no_overlap(self):
        diarization = [
            {"start": 10.0, "end": 15.0, "speaker": "SPEAKER_00"},
        ]
        assert find_best_speaker(0.0, 5.0, diarization) == "UNKNOWN"

    def test_empty_diarization(self):
        assert find_best_speaker(0.0, 5.0, []) == "UNKNOWN"

    def test_multiple_speakers_choose_max_overlap(self):
        diarization = [
            {"start": 0.0, "end": 2.0, "speaker": "SPEAKER_00"},
            {"start": 2.0, "end": 8.0, "speaker": "SPEAKER_01"},
        ]
        # Segment 1-7 overlaps 1s with SPEAKER_00 and 5s with SPEAKER_01
        assert find_best_speaker(1.0, 7.0, diarization) == "SPEAKER_01"


class TestMergeSegments:
    """Tests for merge_segments function."""

    def test_empty_transcription(self):
        assert merge_segments([], []) == []

    def test_no_diarization(self):
        transcription = [
            {"start": 0.0, "end": 3.0, "text": "Hello"},
        ]
        result = merge_segments(transcription, None)
        assert len(result) == 1
        assert result[0]["speaker"] == "SPEAKER_00"
        assert result[0]["text"] == "Hello"

    def test_with_diarization(self):
        transcription = [
            {"start": 0.0, "end": 3.0, "text": "Hello"},
            {"start": 4.0, "end": 7.0, "text": "How are you?"},
        ]
        diarization = [
            {"start": 0.0, "end": 3.5, "speaker": "SPEAKER_00"},
            {"start": 3.5, "end": 8.0, "speaker": "SPEAKER_01"},
        ]
        result = merge_segments(transcription, diarization)
        assert len(result) == 2
        assert result[0]["speaker"] == "SPEAKER_00"
        assert result[1]["speaker"] == "SPEAKER_01"


class TestConsolidateSegments:
    """Tests for consolidate_segments function."""

    def test_empty_segments(self):
        assert consolidate_segments([]) == []

    def test_single_segment(self):
        segments = [{"start": 0.0, "end": 3.0, "text": "Hello", "speaker": "SPEAKER_00"}]
        result = consolidate_segments(segments)
        assert len(result) == 1

    def test_merge_same_speaker(self):
        segments = [
            {"start": 0.0, "end": 2.0, "text": "Hello", "speaker": "SPEAKER_00"},
            {"start": 2.2, "end": 4.0, "text": "world", "speaker": "SPEAKER_00"},
        ]
        result = consolidate_segments(segments, max_gap=0.5)
        assert len(result) == 1
        assert result[0]["text"] == "Hello world"
        assert result[0]["start"] == 0.0
        assert result[0]["end"] == 4.0

    def test_dont_merge_different_speakers(self):
        segments = [
            {"start": 0.0, "end": 2.0, "text": "Hello", "speaker": "SPEAKER_00"},
            {"start": 2.2, "end": 4.0, "text": "Hi", "speaker": "SPEAKER_01"},
        ]
        result = consolidate_segments(segments, max_gap=0.5)
        assert len(result) == 2

    def test_dont_merge_large_gap(self):
        segments = [
            {"start": 0.0, "end": 2.0, "text": "Hello", "speaker": "SPEAKER_00"},
            {"start": 5.0, "end": 7.0, "text": "world", "speaker": "SPEAKER_00"},
        ]
        result = consolidate_segments(segments, max_gap=0.5)
        assert len(result) == 2

    def test_respect_max_duration(self):
        segments = [
            {"start": 0.0, "end": 5.0, "text": "Long text", "speaker": "SPEAKER_00"},
            {"start": 5.2, "end": 10.0, "text": "More text", "speaker": "SPEAKER_00"},
        ]
        result = consolidate_segments(segments, max_gap=0.5, max_duration=8.0)
        assert len(result) == 2
