"""Type definitions for TerminalVision-MCP."""

from enum import Enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ScreenCaptureType(str, Enum):
    """Type of screen capture."""

    TEXT = "text"
    IMAGE = "image"


class ScreenCapture(BaseModel):
    """Result of a screen capture operation."""

    type: ScreenCaptureType
    content: Optional[str] = Field(default=None, description="Text content for text capture")
    hash: Optional[str] = Field(default=None, description="Hash of the captured screen")
    path: Optional[str] = Field(default=None, description="Path to image for image capture")

    class Config:
        frozen = True


class SessionInfo(BaseModel):
    """Information about a terminal session."""

    id: str = Field(description="Unique session identifier")
    command: str = Field(description="Command running in this session")
    created: datetime = Field(default_factory=datetime.now, description="Session creation time")
    cols: int = Field(default=120, description="Number of columns")
    rows: int = Field(default=40, description="Number of rows")
    last_activity: datetime = Field(default_factory=datetime.now, description="Last activity timestamp")


class VisionMCPInfo(BaseModel):
    """Information about a discovered vision MCP."""

    name: str = Field(description="Name of the vision MCP")
    description: Optional[str] = Field(default=None, description="Description of the MCP")
    source: str = Field(description="Source of discovery (qwen, claude, env)")
    tools: list[str] = Field(default_factory=list, description="Vision-related tools available")


class KeySequence(BaseModel):
    """A parsed key sequence."""

    raw: str = Field(description="Original input string")
    mapped: str = Field(description="Mapped bytes to send to terminal")


class StabilityResult(BaseModel):
    """Result of stability detection."""

    stable: bool = Field(description="Whether the screen is stable")
    final_hash: Optional[str] = Field(default=None, description="Hash when stable")
    iterations: int = Field(default=0, description="Number of iterations until stability")