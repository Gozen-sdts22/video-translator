"""Tests for translator functions."""

import pytest
from core.translator import parse_numbered_response


class TestParseNumberedResponse:
    """Tests for parse_numbered_response function."""

    def test_simple_response(self):
        response = "1. 你好\n2. 再见"
        result = parse_numbered_response(response, 2)
        assert result == ["你好", "再见"]

    def test_with_colon_separator(self):
        response = "1: 你好\n2: 再见"
        result = parse_numbered_response(response, 2)
        assert result == ["你好", "再见"]

    def test_missing_number(self):
        response = "1. 你好\n3. 再见"
        result = parse_numbered_response(response, 3)
        assert result[0] == "你好"
        assert result[1] == ""  # Missing #2
        assert result[2] == "再见"

    def test_with_extra_whitespace(self):
        response = "  1.  你好  \n  2.  再见  "
        result = parse_numbered_response(response, 2)
        assert result == ["你好", "再见"]

    def test_empty_response(self):
        result = parse_numbered_response("", 2)
        assert result == ["", ""]

    def test_single_item(self):
        response = "1. 你好"
        result = parse_numbered_response(response, 1)
        assert result == ["你好"]
