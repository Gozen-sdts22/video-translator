"""Tests for time utility functions."""

import pytest
from utils.time_utils import seconds_to_ass_time, ass_time_to_seconds, format_duration


class TestSecondsToAssTime:
    """Tests for seconds_to_ass_time function."""

    def test_zero_seconds(self):
        assert seconds_to_ass_time(0) == "0:00:00.00"

    def test_simple_seconds(self):
        assert seconds_to_ass_time(30) == "0:00:30.00"

    def test_minutes_and_seconds(self):
        assert seconds_to_ass_time(90) == "0:01:30.00"

    def test_hours(self):
        assert seconds_to_ass_time(3661) == "1:01:01.00"

    def test_fractional_seconds(self):
        assert seconds_to_ass_time(1.5) == "0:00:01.50"
        assert seconds_to_ass_time(0.75) == "0:00:00.75"

    def test_negative_becomes_zero(self):
        assert seconds_to_ass_time(-5) == "0:00:00.00"

    def test_precise_centiseconds(self):
        assert seconds_to_ass_time(1.23) == "0:00:01.23"


class TestAssTimeToSeconds:
    """Tests for ass_time_to_seconds function."""

    def test_zero(self):
        assert ass_time_to_seconds("0:00:00.00") == 0.0

    def test_simple(self):
        assert ass_time_to_seconds("0:00:30.00") == 30.0

    def test_minutes(self):
        assert ass_time_to_seconds("0:01:30.00") == 90.0

    def test_hours(self):
        assert ass_time_to_seconds("1:01:01.00") == 3661.0

    def test_fractional(self):
        assert ass_time_to_seconds("0:00:01.50") == 1.5

    def test_invalid_format(self):
        with pytest.raises(ValueError):
            ass_time_to_seconds("invalid")

    def test_missing_parts(self):
        with pytest.raises(ValueError):
            ass_time_to_seconds("00:00")


class TestFormatDuration:
    """Tests for format_duration function."""

    def test_seconds_only(self):
        assert format_duration(30) == "30s"

    def test_minutes_and_seconds(self):
        assert format_duration(90) == "1m 30s"

    def test_hours(self):
        assert format_duration(3661) == "1h 1m 1s"

    def test_zero(self):
        assert format_duration(0) == "0s"

    def test_negative(self):
        assert format_duration(-5) == "0s"
