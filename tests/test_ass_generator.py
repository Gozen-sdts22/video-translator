"""Tests for ASS subtitle generator."""

import pytest
import tempfile
from pathlib import Path

from utils.ass_generator import (
    generate_styles,
    escape_ass_text,
    generate_dialogue_line,
    generate_ass,
    SPEAKER_COLORS,
)


class TestGenerateStyles:
    """Tests for generate_styles function."""

    def test_single_speaker(self):
        styles = generate_styles(["SPEAKER_00"])
        assert "SPEAKER_00" in styles
        assert SPEAKER_COLORS["SPEAKER_00"] in styles

    def test_multiple_speakers(self):
        styles = generate_styles(["SPEAKER_00", "SPEAKER_01"])
        assert "SPEAKER_00" in styles
        assert "SPEAKER_01" in styles

    def test_includes_unknown_fallback(self):
        styles = generate_styles(["SPEAKER_00"])
        assert "UNKNOWN" in styles


class TestEscapeAssText:
    """Tests for escape_ass_text function."""

    def test_normal_text(self):
        assert escape_ass_text("Hello world") == "Hello world"

    def test_newlines(self):
        assert escape_ass_text("Hello\nworld") == "Hello\\Nworld"

    def test_curly_braces(self):
        assert escape_ass_text("{tag}") == "\\{tag\\}"

    def test_combined(self):
        assert escape_ass_text("Hello\n{world}") == "Hello\\N\\{world\\}"


class TestGenerateDialogueLine:
    """Tests for generate_dialogue_line function."""

    def test_japanese_only(self):
        line = generate_dialogue_line(
            start=0.5,
            end=3.0,
            speaker="SPEAKER_00",
            text_ja="こんにちは",
        )
        assert "0:00:00.50" in line
        assert "0:00:03.00" in line
        assert "SPEAKER_00" in line
        assert "こんにちは" in line

    def test_with_translation(self):
        line = generate_dialogue_line(
            start=0.5,
            end=3.0,
            speaker="SPEAKER_00",
            text_ja="こんにちは",
            text_zh="你好",
        )
        assert "こんにちは\\N你好" in line

    def test_dialogue_format(self):
        line = generate_dialogue_line(
            start=0.0,
            end=1.0,
            speaker="SPEAKER_00",
            text_ja="Test",
        )
        assert line.startswith("Dialogue: 0,")


class TestGenerateAss:
    """Tests for generate_ass function."""

    def test_generates_valid_file(self):
        segments = [
            {
                "start": 0.5,
                "end": 3.0,
                "speaker": "SPEAKER_00",
                "text": "こんにちは",
                "translation": "你好",
            },
            {
                "start": 3.5,
                "end": 6.0,
                "speaker": "SPEAKER_01",
                "text": "お元気ですか",
                "translation": "你好吗",
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.ass"
            result = generate_ass(segments, str(output_path))

            assert Path(result).exists()
            content = Path(result).read_text(encoding="utf-8")

            # Check header
            assert "[Script Info]" in content
            assert "[V4+ Styles]" in content
            assert "[Events]" in content

            # Check styles
            assert "SPEAKER_00" in content
            assert "SPEAKER_01" in content

            # Check dialogue
            assert "こんにちは" in content
            assert "你好" in content

    def test_empty_segments_raises(self):
        with pytest.raises(ValueError):
            generate_ass([], "test.ass")

    def test_without_translation(self):
        segments = [
            {
                "start": 0.0,
                "end": 1.0,
                "speaker": "SPEAKER_00",
                "text": "Hello",
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.ass"
            result = generate_ass(segments, str(output_path), include_translation=False)

            content = Path(result).read_text(encoding="utf-8")
            assert "Hello" in content
            assert "\\N" not in content  # No line break for translation
