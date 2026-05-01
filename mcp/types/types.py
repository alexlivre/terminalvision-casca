"""Types for TerminalVision MCP."""

from pydantic import BaseModel
from typing import Optional


class TerminalSpawnParams(BaseModel):
    """Parameters for terminal_spawn."""
    command: str = "cmd.exe"
    cwd: Optional[str] = None
    cols: int = 120
    rows: int = 40


class TerminalSendKeysParams(BaseModel):
    """Parameters for terminal_send_keys."""
    session_id: str
    keys: str


class TerminalGetScreenParams(BaseModel):
    """Parameters for terminal_get_screen."""
    session_id: str
    format: str = "text"  # "text" or "image"


class TerminalResizeParams(BaseModel):
    """Parameters for terminal_resize."""
    session_id: str
    cols: int
    rows: int


class SessionInfo(BaseModel):
    """Terminal session info."""
    session_id: str
    command: str
    pid: Optional[int] = None
    status: str = "running"


class ScreenCapture(BaseModel):
    """Screen capture result."""
    type: str  # "text" or "image"
    content: Optional[str] = None
    path: Optional[str] = None
    hash: Optional[str] = None
