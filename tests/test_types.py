"""Tests for type definitions."""

import pytest
from datetime import datetime

from terminalvision_mcp.types import (
    ScreenCapture,
    ScreenCaptureType,
    SessionInfo,
    VisionMCPInfo,
    KeySequence,
    StabilityResult,
)


def test_screen_capture_text():
    """Test text screen capture."""
    capture = ScreenCapture(
        type=ScreenCaptureType.TEXT,
        content="Hello, World!",
        hash="abc123",
    )
    assert capture.type == ScreenCaptureType.TEXT
    assert capture.content == "Hello, World!"
    assert capture.hash == "abc123"


def test_screen_capture_image():
    """Test image screen capture."""
    capture = ScreenCapture(
        type=ScreenCaptureType.IMAGE,
        path="/tmp/screenshot.png",
    )
    assert capture.type == ScreenCaptureType.IMAGE
    assert capture.path == "/tmp/screenshot.png"


def test_session_info():
    """Test session info creation."""
    session = SessionInfo(
        id="test123",
        command="bash",
    )
    assert session.id == "test123"
    assert session.command == "bash"
    assert session.cols == 120  # default
    assert session.rows == 40  # default
    assert session.created is not None


def test_vision_mcp_info():
    """Test vision MCP info."""
    mcp = VisionMCPInfo(
        name="ollama-vision",
        description="Ollama vision MCP",
        source="qwen",
        tools=["describe_image"],
    )
    assert mcp.name == "ollama-vision"
    assert "describe_image" in mcp.tools


def test_stability_result():
    """Test stability result."""
    result = StabilityResult(
        stable=True,
        final_hash="xyz789",
        iterations=5,
    )
    assert result.stable is True
    assert result.final_hash == "xyz789"
    assert result.iterations == 5