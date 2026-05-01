"""TerminalVision-MCP: Universal MCP Server for terminal vision and control."""

__version__ = "0.1.0"
__author__ = "TerminalVision Team"

from terminalvision_mcp.types import (
    ScreenCapture,
    ScreenCaptureType,
    SessionInfo,
    VisionMCPInfo,
)

__all__ = [
    "__version__",
    "ScreenCapture",
    "ScreenCaptureType",
    "SessionInfo",
    "VisionMCPInfo",
]