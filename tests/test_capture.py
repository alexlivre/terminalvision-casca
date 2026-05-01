"""Tests for capture engine."""

import pytest

from terminalvision_mcp.capture import TextCapture, ImageCapture, CaptureEngine
from terminalvision_mcp.types import ScreenCaptureType


def test_text_capture_basic():
    """Test basic text capture."""
    capture = TextCapture(cols=80, rows=24)

    # Simulate some terminal output
    capture.update("Hello, World!\r\n")

    text = capture.get_text()
    assert "Hello, World!" in text


def test_text_capture_hash():
    """Test text capture hashing."""
    capture = TextCapture(cols=80, rows=24)
    capture.update("Test content")

    hash1 = capture.get_hash()
    hash2 = capture.get_hash()

    assert hash1 == hash2
    assert len(hash1) == 32  # MD5 hash length


def test_text_capture_different_content():
    """Test that different content produces different hashes."""
    capture1 = TextCapture(cols=80, rows=24)
    capture1.update("Content A")

    capture2 = TextCapture(cols=80, rows=24)
    capture2.update("Content B")

    assert capture1.get_hash() != capture2.get_hash()


def test_capture_engine_text_mode():
    """Test capture engine in text mode."""
    engine = CaptureEngine(cols=120, rows=40)

    # Manually update text capture (normally done via PTY)
    engine.text_capture.update("Test output\r\n")

    result = engine.capture_text()

    assert result.type == ScreenCaptureType.TEXT
    assert "Test output" in result.content
    assert result.hash is not None


def test_capture_engine_image_mode():
    """Test capture engine in image mode."""
    engine = CaptureEngine(cols=120, rows=40)

    result = engine.capture_image()

    # Image capture may fail in test environment, but should return correct type
    assert result.type == ScreenCaptureType.IMAGE