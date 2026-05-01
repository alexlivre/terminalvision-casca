"""Tests for key mapper."""

import pytest

from terminalvision_mcp.key_mapper import (
    map_key_sequence,
    parse_key_sequence,
    KEY_MAPPINGS,
)


def test_ctrl_keys():
    """Test control key mappings."""
    assert map_key_sequence("Ctrl+C") == "\x03"
    assert map_key_sequence("Ctrl+D") == "\x04"
    assert map_key_sequence("Ctrl+Z") == "\x1a"


def test_escape_key():
    """Test escape key."""
    assert map_key_sequence("Esc") == "\x1b"
    assert map_key_sequence("Escape") == "\x1b"


def test_arrow_keys():
    """Test arrow key mappings."""
    assert map_key_sequence("Up") == "\x1b[A"
    assert map_key_sequence("Down") == "\x1b[B"
    assert map_key_sequence("Left") == "\x1b[D"
    assert map_key_sequence("Right") == "\x1b[C"


def test_function_keys():
    """Test function key mappings."""
    assert map_key_sequence("F1") == "\x1bOP"
    assert map_key_sequence("F12") == "\x1b[24~"


def test_parse_key_sequence_simple():
    """Test parsing simple key sequences."""
    result = parse_key_sequence("Ctrl+C")
    assert result == "\x03"


def test_parse_key_sequence_combined():
    """Test parsing combined key sequences."""
    result = parse_key_sequence("Ctrl+C\n")
    assert "\x03" in result
    assert "\n" in result


def test_parse_key_sequence_literal():
    """Test parsing literal characters."""
    result = parse_key_sequence("hello")
    assert result == "hello"


def test_parse_key_sequence_mixed():
    """Test parsing mixed key sequences."""
    result = parse_key_sequence("hello\nEscworld")
    assert "hello" in result
    assert "\n" in result
    assert "\x1b" in result
    assert "world" in result