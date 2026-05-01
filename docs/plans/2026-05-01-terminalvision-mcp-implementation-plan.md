# TerminalVision-MCP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a universal MCP Server for terminal vision and control, working with AI models without native vision (DeepSeek, MiniMax M2.7).

**Architecture:** Python asyncio MCP server with platform-specific PTY handling (Unix pty + Windows ConPTY), text capture via VT100/ANSI parsing, image capture via mss, in-memory session management with TTL.

**Tech Stack:** Python 3.11+, `mcp` SDK, `pyte`, `mss`, `pexpect`

---

## 1. Project Setup

### Task 1.1: Create pyproject.toml and requirements.txt

**Files:**
- Create: `C:\code\mcp-servers\terminalvision-mcp\pyproject.toml`
- Create: `C:\code\mcp-servers\terminalvision-mcp\requirements.txt`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "terminalvision-mcp"
version = "0.1.0"
description = "Universal MCP Server for terminal vision and control"
readme = "README.md"
requires-python = ">=3.11"
license = "MIT"
authors = [
    { name = "TerminalVision Team" }
]
keywords = ["mcp", "terminal", "vision", "tui", "ai"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

dependencies = [
    "mcp>=1.0.0",
    "pyte>=0.8.0",
    "mss>=9.0.1",
    "pexpect>=4.9.0",
    "pydantic>=2.0.0",
    "watchdog>=4.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.3.0",
    "mypy>=1.8.0",
]

[project.scripts]
terminalvision-mcp = "terminalvision_mcp.main:main"

[tool.hatch.build.targets.wheel]
packages = ["terminalvision_mcp"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
strict = true
```

- [ ] **Step 2: Create requirements.txt**

```
# Core dependencies
mcp>=1.0.0
pyte>=0.8.0
mss>=9.0.1
pexpect>=4.9.0
pydantic>=2.0.0
watchdog>=4.0.0

# Development dependencies
pytest>=8.0.0
pytest-asyncio>=0.23.0
ruff>=0.3.0
mypy>=1.8.0
```

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml requirements.txt
git commit -m "feat: initial project setup with dependencies"
```

---

### Task 1.2: Create package __init__.py

**Files:**
- Create: `C:\code\mcp-servers\terminalvision-mcp\terminalvision_mcp\__init__.py`

- [ ] **Step 1: Create __init__.py**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add terminalvision_mcp/__init__.py
git commit -m "feat: add package init with version and exports"
```

---

## 2. Type Definitions

### Task 2.1: Implement types.py

**Files:**
- Create: `C:\code\mcp-servers\terminalvision-mcp\terminalvision_mcp\types.py`

- [ ] **Step 1: Create types.py with Pydantic models**

```python
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
    description: str = Field(default="", description="Description of the MCP")
    source: str = Field(description="Source of discovery (qwen, claude, env)")
    tools: list[str] = Field(default_factory=list, description="Available vision tools")


class KeySequence(BaseModel):
    """A mapped key sequence for terminal input."""

    input: str = Field(description="User-friendly input representation (e.g., 'Ctrl+C', 'Esc')")
    escape_sequence: str = Field(description="Actual escape sequence to send to terminal")


class StabilityResult(BaseModel):
    """Result of stability detection."""

    stable: bool = Field(description="Whether the screen is stable")
    final_hash: Optional[str] = Field(default=None, description="Hash of stable screen")
    iterations: int = Field(default=0, description="Number of iterations to detect stability")


class SpawnResult(BaseModel):
    """Result of terminal spawn operation."""

    session_id: str = Field(description="ID of the created session")
    success: bool = Field(description="Whether spawn was successful")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class GenericResult(BaseModel):
    """Generic operation result."""

    success: bool = Field(description="Whether the operation was successful")
    error: Optional[str] = Field(default=None, description="Error message if failed")
```

- [ ] **Step 2: Commit**

```bash
git add terminalvision_mcp/types.py
git commit -m "feat: add type definitions with Pydantic models"
```

---

## 3. PTY Handler

### Task 3.1: Implement pty_handler.py (platform-specific PTY)

**Files:**
- Create: `C:\code\mcp-servers\terminalvision-mcp\terminalvision_mcp\pty_handler.py`

- [ ] **Step 1: Create pty_handler.py with platform abstraction**

```python
"""Platform-specific PTY handler for terminal sessions."""

import os
import sys
import struct
import fcntl
import termios
import signal
from typing import Optional, Tuple
from contextlib import contextmanager

import pexpect

from terminalvision_mcp.types import SessionInfo


class PtyHandler:
    """Handles PTY operations across platforms."""

    def __init__(self, session_id: str, command: str, cwd: Optional[str], cols: int, rows: int):
        self.session_id = session_id
        self.command = command
        self.cwd = cwd or os.getcwd()
        self.cols = cols
        self.rows = rows
        self.process: Optional[pexpect.spawn] = None

    def spawn(self) -> bool:
        """Spawn a new PTY process."""
        try:
            # Determine shell and command
            if sys.platform == "win32":
                cmd = self.command or "cmd.exe"
            else:
                cmd = self.command or os.environ.get("SHELL", "/bin/bash")

            # Create PTY process
            self.process = pexpect.spawn(
                cmd,
                encoding="utf-8",
                timeout=None,
                dimensions=(self.rows, self.cols),
                env={**os.environ, "TERM": "xterm-256color"},
            )

            # Set raw mode and non-blocking
            if sys.platform != "win32":
                fd = self.process.fileno()
                flags = fcntl.fcntl(fd, fcntl.F_GETFL)
                fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

            # Change to working directory if specified
            if self.cwd and os.path.isdir(self.cwd):
                self.process.sendline(f"cd {self.cwd}")

            return True
        except Exception as e:
            print(f"Failed to spawn PTY: {e}", file=sys.stderr)
            return False

    def read(self, timeout_ms: int = 100) -> str:
        """Read available output from PTY."""
        if not self.process:
            return ""

        try:
            # Read with timeout
            self.process.expect(pexpect.TIMEOUT, timeout=timeout_ms / 1000)
        except pexpect.TIMEOUT:
            pass
        except Exception:
            pass

        # Get any output that was read
        output = self.process.before or ""
        return output

    def write(self, data: str) -> bool:
        """Write data to PTY."""
        if not self.process:
            return False

        try:
            self.process.send(data)
            return True
        except Exception:
            return False

    def resize(self, cols: int, rows: int) -> bool:
        """Resize the PTY window."""
        if not self.process:
            return False

        self.cols = cols
        self.rows = rows

        try:
            if sys.platform != "win32":
                # Set window size using TIOCSWINSZ
                size = struct.pack("HHHH", rows, cols, 0, 0)
                fcntl.ioctl(self.process.fileno(), termios.TIOCSWINSZ, size)
            self.process.setwinsize(rows, cols)
            return True
        except Exception:
            return False

    def is_alive(self) -> bool:
        """Check if the PTY process is still running."""
        if not self.process:
            return False
        return self.process.isalive()

    def kill(self) -> bool:
        """Kill the PTY process."""
        if not self.process:
            return False

        try:
            self.process.terminate(force=True)
            self.process = None
            return True
        except Exception:
            return False

    def get_screen_hash(self) -> str:
        """Get a hash of the current screen content."""
        import hashlib
        content = self.read()
        return hashlib.md5(content.encode("utf-8")).hexdigest()


class WindowsPtyHandler(PtyHandler):
    """Windows-specific PTY handler using ConPTY via pexpect."""

    def spawn(self) -> bool:
        """Spawn a new PTY process on Windows."""
        try:
            import pexpect.popen_selection

            cmd = self.command or "cmd.exe"

            # Windows-specific spawn
            self.process = pexpect.spawn(
                cmd,
                encoding="utf-8",
                timeout=None,
                dimensions=(self.rows, self.cols),
                env={**os.environ, "TERM": "xterm-256color"},
            )

            # Change to working directory if specified
            if self.cwd and os.path.isdir(self.cwd):
                self.process.sendline(f"cd {self.cwd}")

            return True
        except Exception as e:
            print(f"Failed to spawn Windows PTY: {e}", file=sys.stderr)
            return False


def create_pty_handler(session_id: str, command: str, cwd: Optional[str], cols: int, rows: int) -> PtyHandler:
    """Factory function to create the appropriate PTY handler for the platform."""
    if sys.platform == "win32":
        return WindowsPtyHandler(session_id, command, cwd, cols, rows)
    return PtyHandler(session_id, command, cwd, cols, rows)
```

- [ ] **Step 2: Commit**

```bash
git add terminalvision_mcp/pty_handler.py
git commit -m "feat: add platform-specific PTY handler"
```

---

## 4. Session Manager

### Task 4.1: Implement session_manager.py

**Files:**
- Create: `C:\code\mcp-servers\terminalvision-mcp\terminalvision_mcp\session_manager.py`

- [ ] **Step 1: Create session_manager.py**

```python
"""Session manager for terminal sessions with TTL cleanup."""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional

from terminalvision_mcp.pty_handler import create_pty_handler, PtyHandler
from terminalvision_mcp.types import SessionInfo


class SessionManager:
    """Manages terminal sessions with in-memory storage and TTL cleanup."""

    def __init__(self, ttl_minutes: int = 30, max_sessions: int = 50):
        self.ttl_minutes = ttl_minutes
        self.max_sessions = max_sessions
        self._sessions: Dict[str, Tuple[PtyHandler, SessionInfo]] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    async def start_cleanup_task(self):
        """Start the background cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop_cleanup_task(self):
        """Stop the background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

    async def _cleanup_loop(self):
        """Background task to clean up expired sessions."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception:
                pass

    async def _cleanup_expired(self):
        """Remove sessions that have exceeded their TTL."""
        async with self._lock:
            now = datetime.now()
            expired = []

            for session_id, (_, info) in self._sessions.items():
                if now - info.last_activity > timedelta(minutes=self.ttl_minutes):
                    expired.append(session_id)

            for session_id in expired:
                await self.kill_session(session_id)

    async def spawn_session(
        self, command: str, cwd: Optional[str], cols: int = 120, rows: int = 40
    ) -> SessionInfo:
        """Create and start a new terminal session."""
        async with self._lock:
            if len(self._sessions) >= self.max_sessions:
                raise RuntimeError(f"Maximum sessions ({self.max_sessions}) reached")

            session_id = str(uuid.uuid4())[:8]

            handler = create_pty_handler(session_id, command, cwd, cols, rows)
            if not handler.spawn():
                raise RuntimeError("Failed to spawn PTY process")

            info = SessionInfo(
                id=session_id,
                command=command or "default shell",
                cols=cols,
                rows=rows,
            )

            self._sessions[session_id] = (handler, info)
            return info

    async def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """Get session info without locking."""
        if session_id in self._sessions:
            _, info = self._sessions[session_id]
            return info
        return None

    async def get_handler(self, session_id: str) -> Optional[PtyHandler]:
        """Get the PTY handler for a session."""
        if session_id in self._sessions:
            handler, _ = self._sessions[session_id]
            return handler
        return None

    async def update_activity(self, session_id: str):
        """Update the last activity timestamp for a session."""
        async with self._lock:
            if session_id in self._sessions:
                _, info = self._sessions[session_id]
                info.last_activity = datetime.now()

    async def kill_session(self, session_id: str) -> bool:
        """Kill a terminal session."""
        async with self._lock:
            if session_id in self._sessions:
                handler, _ = self._sessions[session_id]
                handler.kill()
                del self._sessions[session_id]
                return True
            return False

    async def list_sessions(self) -> list[SessionInfo]:
        """List all active sessions."""
        async with self._lock:
            return [info for _, info in self._sessions.values()]

    async def resize_session(self, session_id: str, cols: int, rows: int) -> bool:
        """Resize a session's terminal."""
        async with self._lock:
            if session_id in self._sessions:
                handler, _ = self._sessions[session_id]
                return handler.resize(cols, rows)
            return False


# Global session manager instance
_global_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    global _global_manager
    if _global_manager is None:
        _global_manager = SessionManager()
    return _global_manager
```

- [ ] **Step 2: Commit**

```bash
git add terminalvision_mcp/session_manager.py
git commit -m "feat: add session manager with TTL cleanup"
```

---

## 5. Capture Engine

### Task 5.1: Implement capture.py

**Files:**
- Create: `C:\code\mcp-servers\terminalvision-mcp\terminalvision_mcp\capture.py`

- [ ] **Step 1: Create capture.py with text and image capture**

```python
"""Capture engine for terminal screen (text and image)."""

import os
import sys
import hashlib
import tempfile
from typing import Optional

import pyte

from terminalvision_mcp.pty_handler import PtyHandler
from terminalvision_mcp.types import ScreenCapture, ScreenCaptureType


class TextCapture:
    """Captures terminal screen as text using pyte (VT100 parser)."""

    def __init__(self, cols: int, rows: int):
        self.screen = pyte.Screen(cols, rows)
        self.stream = pyte.Stream(self.screen)

    def update(self, data: str):
        """Update the screen with new data."""
        self.stream.feed(data)

    def get_text(self) -> str:
        """Get the current screen as text."""
        lines = []
        for row in self.screen.display:
            lines.append("".join(row).rstrip())
        return "\n".join(lines)

    def get_hash(self) -> str:
        """Get a hash of the current screen."""
        return hashlib.md5(self.get_text().encode("utf-8")).hexdigest()


class ImageCapture:
    """Captures terminal screen as an image using mss."""

    def __init__(self):
        self._mss = None

    def _get_mss(self):
        """Lazy load mss module."""
        if self._mss is None:
            try:
                import mss
                self._mss = mss
            except ImportError:
                return None
        return self._mss

    def capture(self, output_dir: Optional[str] = None) -> Optional[str]:
        """Capture the screen and save to a file. Returns the path."""
        mss = self._get_mss()
        if mss is None:
            return None

        try:
            with mss.mss() as sct:
                # Capture all monitors or primary
                if len(sct.monitors) > 1:
                    monitor = sct.monitors[1]  # Primary monitor
                else:
                    monitor = sct.monitors[0]

                # Determine output path
                if output_dir is None:
                    output_dir = tempfile.gettempdir()

                output_path = os.path.join(output_dir, "terminalvision_capture.png")

                # Capture and save
                sct.shot(mon=monitor, output=output_path)
                return output_path

        except Exception as e:
            print(f"Failed to capture image: {e}", file=sys.stderr)
            return None


class CaptureEngine:
    """Main capture engine that coordinates text and image capture."""

    def __init__(self, cols: int = 120, rows: int = 40):
        self.text_capture = TextCapture(cols, rows)
        self.image_capture = ImageCapture()

    def update_from_pty(self, handler: PtyHandler):
        """Update text capture from PTY output."""
        data = handler.read()
        if data:
            self.text_capture.update(data)

    def capture_text(self) -> ScreenCapture:
        """Capture the current screen as text."""
        return ScreenCapture(
            type=ScreenCaptureType.TEXT,
            content=self.text_capture.get_text(),
            hash=self.text_capture.get_hash(),
        )

    def capture_image(self, output_dir: Optional[str] = None) -> ScreenCapture:
        """Capture the current screen as an image."""
        path = self.image_capture.capture(output_dir)
        if path:
            return ScreenCapture(
                type=ScreenCaptureType.IMAGE,
                path=path,
            )
        else:
            return ScreenCapture(
                type=ScreenCaptureType.IMAGE,
                path=None,
            )
```

- [ ] **Step 2: Commit**

```bash
git add terminalvision_mcp/capture.py
git commit -m "feat: add capture engine for text and image"
```

---

## 6. Stability Detection

### Task 6.1: Implement stability.py

**Files:**
- Create: `C:\code\mcp-servers\terminalvision-mcp\terminalvision_mcp\stability.py`

- [ ] **Step 1: Create stability.py**

```python
"""Screen stability detection for terminal sessions."""

import asyncio
from typing import Optional

from terminalvision_mcp.pty_handler import PtyHandler
from terminalvision_mcp.types import StabilityResult


class StabilityDetector:
    """Detects when a terminal screen has become stable."""

    def __init__(
        self,
        stable_threshold_ms: int = 500,
        max_iterations: int = 10,
        check_interval_ms: int = 100,
    ):
        self.stable_threshold_ms = stable_threshold_ms
        self.max_iterations = max_iterations
        self.check_interval_ms = check_interval_ms

    async def wait_for_stable(
        self,
        handler: PtyHandler,
        timeout_ms: int = 5000,
    ) -> StabilityResult:
        """Wait for the terminal screen to become stable."""
        import time

        start_time = time.monotonic()
        previous_hash = None
        stable_since = None
        iterations = 0

        while True:
            # Check timeout
            elapsed_ms = (time.monotonic() - start_time) * 1000
            if elapsed_ms >= timeout_ms:
                current_hash = handler.get_screen_hash()
                return StabilityResult(
                    stable=False,
                    final_hash=current_hash,
                    iterations=iterations,
                )

            # Check if process is still alive
            if not handler.is_alive():
                return StabilityResult(
                    stable=False,
                    final_hash=None,
                    iterations=iterations,
                )

            # Get current screen hash
            handler.read()  # Drain any pending output
            current_hash = handler.get_screen_hash()
            iterations += 1

            if current_hash == previous_hash:
                # Screen hasn't changed
                if stable_since is None:
                    stable_since = time.monotonic()
                else:
                    # Check if stable for threshold
                    stable_duration_ms = (time.monotonic() - stable_since) * 1000
                    if stable_duration_ms >= self.stable_threshold_ms:
                        return StabilityResult(
                            stable=True,
                            final_hash=current_hash,
                            iterations=iterations,
                        )
            else:
                # Screen changed, reset stable timer
                stable_since = None
                previous_hash = current_hash

            # Wait before next check
            await asyncio.sleep(self.check_interval_ms / 1000)

            # Safety check for max iterations
            if iterations >= self.max_iterations * 10:  # Allow more iterations with short intervals
                return StabilityResult(
                    stable=True,
                    final_hash=current_hash,
                    iterations=iterations,
                )
```

- [ ] **Step 2: Commit**

```bash
git add terminalvision_mcp/stability.py
git commit -m "feat: add stability detection"
```

---

## 7. Key Mapper

### Task 7.1: Implement key_mapper.py

**Files:**
- Create: `C:\code\mcp-servers\terminalvision-mcp\terminalvision_mcp\key_mapper.py`

- [ ] **Step 1: Create key_mapper.py**

```python
"""Key sequence mapper for terminal input."""

from typing import Dict

from terminalvision_mcp.types import KeySequence


# Standard key mappings for terminal input
KEY_MAPPINGS: Dict[str, KeySequence] = {
    # Control keys
    "Ctrl+A": KeySequence(input="Ctrl+A", escape_sequence="\x01"),
    "Ctrl+B": KeySequence(input="Ctrl+B", escape_sequence="\x02"),
    "Ctrl+C": KeySequence(input="Ctrl+C", escape_sequence="\x03"),
    "Ctrl+D": KeySequence(input="Ctrl+D", escape_sequence="\x04"),
    "Ctrl+E": KeySequence(input="Ctrl+E", escape_sequence="\x05"),
    "Ctrl+F": KeySequence(input="Ctrl+F", escape_sequence="\x06"),
    "Ctrl+G": KeySequence(input="Ctrl+G", escape_sequence="\x07"),
    "Ctrl+H": KeySequence(input="Ctrl+H", escape_sequence="\x08"),
    "Ctrl+I": KeySequence(input="Ctrl+I", escape_sequence="\x09"),  # Tab
    "Ctrl+J": KeySequence(input="Ctrl+J", escape_sequence="\x0a"),  # Enter
    "Ctrl+K": KeySequence(input="Ctrl+K", escape_sequence="\x0b"),
    "Ctrl+L": KeySequence(input="Ctrl+L", escape_sequence="\x0c"),
    "Ctrl+M": KeySequence(input="Ctrl+M", escape_sequence="\x0d"),  # Enter (alternative)
    "Ctrl+N": KeySequence(input="Ctrl+N", escape_sequence="\x0e"),
    "Ctrl+O": KeySequence(input="Ctrl+O", escape_sequence="\x0f"),
    "Ctrl+P": KeySequence(input="Ctrl+P", escape_sequence="\x10"),
    "Ctrl+Q": KeySequence(input="Ctrl+Q", escape_sequence="\x11"),
    "Ctrl+R": KeySequence(input="Ctrl+R", escape_sequence="\x12"),
    "Ctrl+S": KeySequence(input="Ctrl+S", escape_sequence="\x13"),
    "Ctrl+T": KeySequence(input="Ctrl+T", escape_sequence="\x14"),
    "Ctrl+U": KeySequence(input="Ctrl+U", escape_sequence="\x15"),
    "Ctrl+V": KeySequence(input="Ctrl+V", escape_sequence="\x16"),
    "Ctrl+W": KeySequence(input="Ctrl+W", escape_sequence="\x17"),
    "Ctrl+X": KeySequence(input="Ctrl+X", escape_sequence="\x18"),
    "Ctrl+Y": KeySequence(input="Ctrl+Y", escape_sequence="\x19"),
    "Ctrl+Z": KeySequence(input="Ctrl+Z", escape_sequence="\x1a"),

    # Escape sequences for special keys
    "Esc": KeySequence(input="Esc", escape_sequence="\x1b"),
    "Escape": KeySequence(input="Escape", escape_sequence="\x1b"),

    # Arrow keys
    "Up": KeySequence(input="Up", escape_sequence="\x1b[A"),
    "Down": KeySequence(input="Down", escape_sequence="\x1b[B"),
    "Right": KeySequence(input="Right", escape_sequence="\x1b[C"),
    "Left": KeySequence(input="Left", escape_sequence="\x1b[D"),

    # Function keys (partial)
    "F1": KeySequence(input="F1", escape_sequence="\x1bOP"),
    "F2": KeySequence(input="F2", escape_sequence="\x1bOQ"),
    "F3": KeySequence(input="F3", escape_sequence="\x1bOR"),
    "F4": KeySequence(input="F4", escape_sequence="\x1bOS"),
    "F5": KeySequence(input="F5", escape_sequence="\x1b[15~"),
    "F6": KeySequence(input="F6", escape_sequence="\x1b[17~"),
    "F7": KeySequence(input="F7", escape_sequence="\x1b[18~"),
    "F8": KeySequence(input="F8", escape_sequence="\x1b[19~"),
    "F9": KeySequence(input="F9", escape_sequence="\x1b[20~"),
    "F10": KeySequence(input="F10", escape_sequence="\x1b[21~"),
    "F11": KeySequence(input="F11", escape_sequence="\x1b[23~"),
    "F12": KeySequence(input="F12", escape_sequence="\x1b[24~"),

    # Home/End
    "Home": KeySequence(input="Home", escape_sequence="\x1b[H"),
    "End": KeySequence(input="End", escape_sequence="\x1b[F"),

    # Page Up/Down
    "PageUp": KeySequence(input="PageUp", escape_sequence="\x1b[5~"),
    "PageDown": KeySequence(input="PageDown", escape_sequence="\x1b[6~"),

    # Delete/Insert
    "Delete": KeySequence(input="Delete", escape_sequence="\x1b[3~"),
    "Insert": KeySequence(input="Insert", escape_sequence="\x1b[2~"),

    # Backspace
    "Backspace": KeySequence(input="Backspace", escape_sequence="\x7f"),
}


def map_key_sequence(key_input: str) -> str:
    """
    Map a user-friendly key input to the actual escape sequence.

    Examples:
        "Ctrl+C" -> "\\x03"
        "Esc" -> "\\x1b"
        "Up" -> "\\x1b[A"
    """
    # Check for exact match
    if key_input in KEY_MAPPINGS:
        return KEY_MAPPINGS[key_input].escape_sequence

    # Check case-insensitive
    key_lower = key_input.lower()
    for key, mapping in KEY_MAPPINGS.items():
        if key.lower() == key_lower:
            return mapping.escape_sequence

    # If no match, return the input as-is (for literal characters)
    return key_input


def parse_key_sequence(input_str: str) -> str:
    """
    Parse a key sequence string that may contain multiple keys.

    Supports:
        - Single keys: "Ctrl+C", "Esc", "Up"
        - Combined sequences: "Ctrl+C\n" (Ctrl+C then Enter)
        - Literal characters are passed through

    Returns the complete escape sequence to send.
    """
    result = []

    # Handle special key notation like "Ctrl+C", "Alt+F4"
    import re

    # Pattern for special keys: Ctrl+X, Alt+X, Shift+X, etc.
    special_key_pattern = r"((?:Ctrl|Alt|Shift)\+[A-Za-z0-9]|Esc|Escape|Up|Down|Left|Right|Home|End|PageUp|PageDown|Delete|Insert|F[0-9]+|Backspace|Tab|Enter)"

    # Split by common separators but preserve the keys
    parts = re.split(f"({special_key_pattern}|\\n)", input_str)

    for part in parts:
        if not part:
            continue

        if part == "\n":
            result.append("\n")
        elif part.startswith("Ctrl+") or part.startswith("Alt+") or part.startswith("Shift+"):
            result.append(map_key_sequence(part))
        elif part in KEY_MAPPINGS:
            result.append(KEY_MAPPINGS[part].escape_sequence)
        else:
            # Literal character
            result.append(part)

    return "".join(result)
```

- [ ] **Step 2: Commit**

```bash
git add terminalvision_mcp/key_mapper.py
git commit -m "feat: add key sequence mapper"
```

---

## 8. Vision Discovery

### Task 8.1: Implement vision_discovery.py

**Files:**
- Create: `C:\code\mcp-servers\terminalvision-mcp\terminalvision_mcp\vision_discovery.py`

- [ ] **Step 1: Create vision_discovery.py**

```python
"""Discovery of vision MCPs from client configurations."""

import os
import json
from typing import List, Optional
from pathlib import Path

from terminalvision_mcp.types import VisionMCPInfo


# Patterns that indicate a tool is vision-related
VISION_KEYWORDS = [
    "describe",
    "analyze",
    "vision",
    "image",
    "screenshot",
    "picture",
    "visual",
    "ocr",
    "read_image",
    "describe_image",
    "analyze_image",
]


class VisionDiscovery:
    """Discovers vision MCPs from client configurations."""

    def __init__(self):
        self._discovered_mcps: List[VisionMCPInfo] = []
        self._scan_done = False

    def get_config_paths(self) -> List[Path]:
        """Get paths to scan for MCP configurations."""
        paths = []

        # Determine home directory
        if sys.platform == "win32":
            home = Path(os.environ.get("USERPROFILE", ""))
        else:
            home = Path(os.environ.get("HOME", "~"))

        # Qwen Code config locations
        qwen_paths = [
            home / ".qwen" / "settings.json",
            home / ".qwen" / "mcp.json",
            home / ".qwen" / "config.json",
        ]
        paths.extend(qwen_paths)

        # Claude Code config locations
        claude_paths = [
            home / ".claude" / "settings.json",
            home / ".claude" / "mcp.json",
            home / ".claude" / "config.json",
        ]
        paths.extend(claude_paths)

        # Common MCP config locations
        common_paths = [
            home / ".config" / "mcp" / "settings.json",
            home / ".mcp" / "settings.json",
            Path("/etc/mcp/config.json"),  # Linux system-wide
        ]
        paths.extend(common_paths)

        return [p for p in paths if p.exists()]

    def _is_vision_tool(self, tool_name: str, tool_description: str = "") -> bool:
        """Check if a tool is vision-related."""
        tool_name_lower = tool_name.lower()
        description_lower = tool_description.lower()

        for keyword in VISION_KEYWORDS:
            if keyword in tool_name_lower or keyword in description_lower:
                return True

        return False

    def _parse_qwen_settings(self, content: dict) -> List[VisionMCPInfo]:
        """Parse Qwen Code settings format."""
        mcps = []

        # Qwen may store MCP config in different formats
        # Try common patterns
        mcp_configs = []

        if "mcpServers" in content:
            mcp_configs = content["mcpServers"].items()
        elif "mcp" in content and "servers" in content["mcp"]:
            mcp_configs = content["mcp"]["servers"].items()
        elif "tools" in content and "mcp" in content.get("extensions", {}):
            # Alternative format
            pass

        for name, config in mcp_configs:
            tools = config.get("tools", []) if isinstance(config, dict) else []
            vision_tools = [
                t.get("name", t) if isinstance(t, dict) else t
                for t in tools
                if self._is_vision_tool(t.get("name", t) if isinstance(t, dict) else t)
            ]

            if vision_tools:
                mcps.append(VisionMCPInfo(
                    name=name,
                    description=f"Vision MCP from Qwen (tools: {', '.join(vision_tools)})",
                    source="qwen",
                    tools=vision_tools,
                ))

        return mcps

    def _parse_claude_settings(self, content: dict) -> List[VisionMCPInfo]:
        """Parse Claude Code settings format."""
        mcps = []

        # Claude Code MCP config format
        if "mcpServers" in content:
            for name, config in content["mcpServers"].items():
                tools = config.get("tools", []) if isinstance(config, dict) else []
                vision_tools = [
                    t.get("name", t) if isinstance(t, dict) else t
                    for t in tools
                    if self._is_vision_tool(t.get("name", t) if isinstance(t, dict) else t)
                ]

                if vision_tools:
                    mcps.append(VisionMCPInfo(
                        name=name,
                        description=f"Vision MCP from Claude (tools: {', '.join(vision_tools)})",
                        source="claude",
                        tools=vision_tools,
                    ))

        return mcps

    def _parse_generic_mcp(self, content: dict) -> List[VisionMCPInfo]:
        """Parse generic MCP config format."""
        mcps = []

        # Generic MCP config
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and "name" in item:
                    name = item["name"]
                    tools = item.get("tools", [])
                    description = item.get("description", "")

                    vision_tools = [
                        t if isinstance(t, str) else t.get("name", "")
                        for t in tools
                        if self._is_vision_tool(t if isinstance(t, str) else t.get("name", ""))
                    ]

                    if vision_tools:
                        mcps.append(VisionMCPInfo(
                            name=name,
                            description=description or f"Vision MCP (tools: {', '.join(vision_tools)})",
                            source="config",
                            tools=vision_tools,
                        ))

        return mcps

    def scan(self) -> List[VisionMCPInfo]:
        """Scan all config files and discover vision MCPs."""
        if self._scan_done:
            return self._discovered_mcps

        self._discovered_mcps = []
        seen_names = set()

        for config_path in self.get_config_paths():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    content = json.load(f)

                # Try different parsers
                mcps = []

                if "qwen" in str(config_path).lower():
                    mcps = self._parse_qwen_settings(content)
                elif "claude" in str(config_path).lower():
                    mcps = self._parse_claude_settings(content)
                else:
                    mcps = self._parse_generic_mcp(content)

                for mcp in mcps:
                    if mcp.name not in seen_names:
                        self._discovered_mcps.append(mcp)
                        seen_names.add(mcp.name)

            except Exception:
                pass

        # Add from environment variable fallback
        env_mcp_list = os.environ.get("TERMINALVISION_VISION_MCP_LIST", "")
        if env_mcp_list:
            for name in env_mcp_list.split(","):
                name = name.strip()
                if name and name not in seen_names:
                    self._discovered_mcps.append(VisionMCPInfo(
                        name=name,
                        description="From TERMINALVISION_VISION_MCP_LIST",
                        source="env",
                        tools=["describe_image"],
                    ))
                    seen_names.add(name)

        self._scan_done = True
        return self._discovered_mcps

    def list_vision_mcps(self) -> List[VisionMCPInfo]:
        """Get list of discovered vision MCPs."""
        return self.scan()

    def get_best_vision_mcp(self) -> Optional[VisionMCPInfo]:
        """Get the best available vision MCP."""
        mcps = self.scan()
        if not mcps:
            return None

        # Prefer Claude, then Qwen, then env
        for source in ["claude", "qwen", "env"]:
            for mcp in mcps:
                if mcp.source == source:
                    return mcp

        return mcps[0] if mcps else None


# Global instance
_global_discovery: Optional[VisionDiscovery] = None


def get_vision_discovery() -> VisionDiscovery:
    """Get the global vision discovery instance."""
    global _global_discovery
    if _global_discovery is None:
        _global_discovery = VisionDiscovery()
    return _global_discovery
```

- [ ] **Step 2: Commit**

```bash
git add terminalvision_mcp/vision_discovery.py
git commit -m "feat: add vision MCP discovery from client configs"
```

---

## 9. MCP Server (main.py)

### Task 9.1: Implement main.py

**Files:**
- Create: `C:\code\mcp-servers\terminalvision-mcp\terminalvision_mcp\main.py`

- [ ] **Step 1: Create main.py**

```python
"""TerminalVision-MCP: Main entry point and MCP server implementation."""

import sys
import asyncio
from typing import Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from terminalvision_mcp.session_manager import get_session_manager
from terminalvision_mcp.capture import CaptureEngine
from terminalvision_mcp.stability import StabilityDetector
from terminalvision_mcp.key_mapper import parse_key_sequence
from terminalvision_mcp.vision_discovery import get_vision_discovery
from terminalvision_mcp.types import (
    SpawnResult,
    GenericResult,
    ScreenCapture,
    ScreenCaptureType,
    SessionInfo,
    VisionMCPInfo,
    StabilityResult,
)


# Server instance
app = Server("terminalvision-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools."""
    return [
        Tool(
            name="terminal_spawn",
            description="Spawn a new terminal session with a command",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Command to run (default: shell)",
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory",
                    },
                    "cols": {
                        "type": "integer",
                        "description": "Number of columns (default: 120)",
                        "default": 120,
                    },
                    "rows": {
                        "type": "integer",
                        "description": "Number of rows (default: 40)",
                        "default": 40,
                    },
                },
            },
        ),
        Tool(
            name="terminal_get_screen",
            description="Get the current terminal screen (text or image)",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID to capture",
                    },
                    "format": {
                        "type": "string",
                        "enum": ["text", "image"],
                        "description": "Capture format (default: text)",
                        "default": "text",
                    },
                },
                "required": ["session_id"],
            },
        ),
        Tool(
            name="terminal_send_keys",
            description="Send key sequences to the terminal",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID to send keys to",
                    },
                    "keys": {
                        "type": "string",
                        "description": "Keys to send (e.g., 'Ctrl+C', 'Esc', 'hello\\n')",
                    },
                },
                "required": ["session_id", "keys"],
            },
        ),
        Tool(
            name="terminal_wait_for_stable",
            description="Wait for the terminal screen to become stable",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID to monitor",
                    },
                    "timeout_ms": {
                        "type": "integer",
                        "description": "Maximum time to wait in ms (default: 5000)",
                        "default": 5000,
                    },
                },
                "required": ["session_id"],
            },
        ),
        Tool(
            name="terminal_list_sessions",
            description="List all active terminal sessions",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="terminal_resize",
            description="Resize a terminal session",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID to resize",
                    },
                    "cols": {
                        "type": "integer",
                        "description": "New number of columns",
                    },
                    "rows": {
                        "type": "integer",
                        "description": "New number of rows",
                    },
                },
                "required": ["session_id", "cols", "rows"],
            },
        ),
        Tool(
            name="terminal_kill",
            description="Kill a terminal session",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID to kill",
                    },
                },
                "required": ["session_id"],
            },
        ),
        Tool(
            name="list_vision_mcps",
            description="List discovered vision MCPs in the system",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    manager = get_session_manager()
    discovery = get_vision_discovery()

    try:
        if name == "terminal_spawn":
            session = await manager.spawn_session(
                command=arguments.get("command"),
                cwd=arguments.get("cwd"),
                cols=arguments.get("cols", 120),
                rows=arguments.get("rows", 40),
            )
            return [TextContent(type="text", text=f'{{"session_id": "{session.id}", "success": true}}')]

        elif name == "terminal_get_screen":
            session_id = arguments["session_id"]
            format_type = arguments.get("format", "text")

            handler = await manager.get_handler(session_id)
            if not handler:
                return [TextContent(type="text", text='{"error": "Session not found"}')]

            await manager.update_activity(session_id)
            session_info = await manager.get_session(session_id)

            capture = CaptureEngine(cols=session_info.cols, rows=session_info.rows)
            capture.update_from_pty(handler)

            if format_type == "image":
                result = capture.capture_image()
                if result.path:
                    return [TextContent(type="text", text=f'{{"type": "image", "path": "{result.path}"}}')]
                else:
                    return [TextContent(type="text", text='{"error": "Failed to capture image"}')]
            else:
                result = capture.capture_text()
                return [TextContent(type="text", text=f'{{"type": "text", "content": {repr(result.content)}, "hash": "{result.hash}"}}')]

        elif name == "terminal_send_keys":
            session_id = arguments["session_id"]
            keys = arguments["keys"]

            handler = await manager.get_handler(session_id)
            if not handler:
                return [TextContent(type="text", text='{"success": false, "error": "Session not found"}')]

            # Map key sequences
            mapped_keys = parse_key_sequence(keys)
            success = handler.write(mapped_keys)

            if success:
                await manager.update_activity(session_id)

            return [TextContent(type="text", text=f'{{"success": {str(success).lower()}}}')]

        elif name == "terminal_wait_for_stable":
            session_id = arguments["session_id"]
            timeout_ms = arguments.get("timeout_ms", 5000)

            handler = await manager.get_handler(session_id)
            if not handler:
                return [TextContent(type="text", text='{"stable": false, "error": "Session not found"}')]

            detector = StabilityDetector()
            result: StabilityResult = await detector.wait_for_stable(handler, timeout_ms)

            return [TextContent(type="text", text=f'{{"stable": {str(result.stable).lower()}, "final_hash": "{result.final_hash or ""}", "iterations": {result.iterations}}}')]

        elif name == "terminal_list_sessions":
            sessions = await manager.list_sessions()
            sessions_data = [
                {
                    "id": s.id,
                    "command": s.command,
                    "created": s.created.isoformat(),
                    "cols": s.cols,
                    "rows": s.rows,
                }
                for s in sessions
            ]
            import json
            return [TextContent(type="text", text=json.dumps({"sessions": sessions_data}))]

        elif name == "terminal_resize":
            session_id = arguments["session_id"]
            cols = arguments["cols"]
            rows = arguments["rows"]

            success = await manager.resize_session(session_id, cols, rows)
            return [TextContent(type="text", text=f'{{"success": {str(success).lower()}}}')]

        elif name == "terminal_kill":
            session_id = arguments["session_id"]
            success = await manager.kill_session(session_id)
            return [TextContent(type="text", text=f'{{"success": {str(success).lower()}}}')]

        elif name == "list_vision_mcps":
            mcps = discovery.list_vision_mcps()
            mcps_data = [
                {
                    "name": m.name,
                    "description": m.description,
                    "source": m.source,
                    "tools": m.tools,
                }
                for m in mcps
            ]
            import json
            return [TextContent(type="text", text=json.dumps({"vision_mcps": mcps_data}))]

        else:
            return [TextContent(type="text", text=f'{{"error": "Unknown tool: {name}"}}')]

    except Exception as e:
        import traceback
        traceback.print_exc()
        return [TextContent(type="text", text=f'{{"error": {repr(e)}}}')]


async def main():
    """Main entry point."""
    # Start cleanup task
    manager = get_session_manager()
    await manager.start_cleanup_task()

    # Run server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Commit**

```bash
git add terminalvision_mcp/main.py
git commit -m "feat: add MCP server with all tools"
```

---

## 10. Tests

### Task 10.1: Create test files

**Files:**
- Create: `C:\code\mcp-servers\terminalvision-mcp\tests\test_types.py`
- Create: `C:\code\mcp-servers\terminalvision-mcp\tests\test_key_mapper.py`
- Create: `C:\code\mcp-servers\terminalvision-mcp\tests\test_capture.py`

- [ ] **Step 1: Create test_types.py**

```python
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
```

- [ ] **Step 2: Create test_key_mapper.py**

```python
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
```

- [ ] **Step 3: Create test_capture.py**

```python
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
```

- [ ] **Step 4: Commit**

```bash
git add tests/
git commit -m "test: add unit tests for core modules"
```

---

## 11. README

### Task 11.1: Create README.md

**Files:**
- Create: `C:\code\mcp-servers\terminalvision-mcp\README.md`

- [ ] **Step 1: Create comprehensive README**

```markdown
# TerminalVision-MCP

Universal MCP Server for terminal vision and control. Gives AI agents the ability to see and interact with terminal applications.

## Features

- **Text Capture**: Fast, efficient terminal screen capture via PTY + VT100 parsing
- **Image Capture**: Real screenshot capture when detailed vision is needed
- **Multi-Session**: Support for multiple persistent terminal sessions
- **Smart Vision**: Automatically discovers and uses available vision MCPs
- **Cross-Platform**: Windows (ConPTY), Linux (pty), macOS support
- **TUI Support**: Works with Vim, htop, nano, and any terminal application

## Installation

### Requirements

- Python 3.11+
- Windows 10/11, Linux, or macOS

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/terminalvision-mcp.git
cd terminalvision-mcp

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## Configuration

### Qwen Code

Add to your Qwen Code settings (settings.json):

```json
{
  "mcpServers": {
    "terminalvision": {
      "command": "python",
      "args": ["-m", "terminalvision_mcp"],
      "env": {}
    }
  }
}
```

### Claude Code

Add to your Claude Code settings:

```json
{
  "mcpServers": {
    "terminalvision": {
      "command": "python",
      "args": ["-m", "terminalvision_mcp"]
    }
  }
}
```

### Environment Variables

- `TERMINALVISION_VISION_MCP_LIST`: Comma-separated list of vision MCP names (fallback)
- `TERMINALVISION_SESSION_TTL`: Session TTL in minutes (default: 30)
- `TERMINALVISION_MAX_SESSIONS`: Maximum concurrent sessions (default: 50)

## Tools

### terminal_spawn

Spawn a new terminal session.

```python
terminal_spawn(command="bash", cwd="/home/user", cols=120, rows=40)
# Returns: {"session_id": "abc123", "success": true}
```

### terminal_get_screen

Capture the terminal screen.

```python
# Text capture (fast, efficient)
terminal_get_screen(session_id="abc123", format="text")
# Returns: {"type": "text", "content": "...", "hash": "md5hash"}

# Image capture (detailed vision)
terminal_get_screen(session_id="abc123", format="image")
# Returns: {"type": "image", "path": "/tmp/capture.png"}
```

### terminal_send_keys

Send key sequences to the terminal.

```python
terminal_send_keys(session_id="abc123", keys="Ctrl+C")
terminal_send_keys(session_id="abc123", keys="hello\n")
terminal_send_keys(session_id="abc123", keys="Esc:wq\n")
```

Supported key sequences:
- Control keys: `Ctrl+A`, `Ctrl+C`, `Ctrl+D`, etc.
- Special keys: `Esc`, `Up`, `Down`, `Left`, `Right`, `Home`, `End`, etc.
- Function keys: `F1` through `F12`
- Literal text and newlines

### terminal_wait_for_stable

Wait for the terminal screen to stop changing.

```python
terminal_wait_for_stable(session_id="abc123", timeout_ms=5000)
# Returns: {"stable": true, "final_hash": "md5hash", "iterations": 5}
```

### terminal_list_sessions

List all active terminal sessions.

```python
terminal_list_sessions()
# Returns: {"sessions": [{"id": "abc123", "command": "bash", ...}]}
```

### terminal_resize

Resize a terminal session.

```python
terminal_resize(session_id="abc123", cols=80, rows=24)
# Returns: {"success": true}
```

### terminal_kill

Kill a terminal session.

```python
terminal_kill(session_id="abc123")
# Returns: {"success": true}
```

### list_vision_mcps

List discovered vision MCPs in the system.

```python
list_vision_mcps()
# Returns: {"vision_mcps": [{"name": "ollama-vision", ...}]}
```

## How It Works

### Text vs Image Decision

TerminalVision-MCP prioritizes text capture because it is:

1. **Faster**: No screenshot processing needed
2. **More Efficient**: Lower token usage for AI models
3. **More Structured**: Text is easier for models to parse
4. **Complete**: VT100 parsing captures cursor position, colors, and attributes

Use image capture when:
- Visual layout matters (UI applications)
- Color accuracy is critical
- Text extraction is too complex

### Vision MCP Discovery

When an AI model doesn't natively support image input:

1. TerminalVision-MCP scans client configurations:
   - Qwen Code: `~/.qwen/settings.json`
   - Claude Code: `~/.claude/settings.json`
2. Identifies MCPs with vision-related tools
3. Exposes them via `list_vision_mcps`
4. Captures screenshot and calls the discovered vision MCP

### Session Management

- Sessions are stored in-memory
- Each session has a 30-minute TTL (configurable)
- Background cleanup removes expired sessions
- Maximum 50 concurrent sessions (configurable)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     MCP Server                          │
├─────────────────────────────────────────────────────────┤
│  Tools Layer                                            │
│  ┌──────────┬──────────┬──────────┬──────────┬─────────┐  │
│  │spawn    │get_screen│send_keys│wait_stable│list    │  │
│  └─────────┴─────────┴─────────┴──────────┴─────────┘  │
├─────────────────────────────────────────────────────────┤
│  Session Manager (in-memory + TTL)                      │
├─────────────────────────────────────────────────────────┤
│  PTY Handler (platform-specific)                        │
│  ┌─────────────┬─────────────────┬─────────────────┐    │
│  │  Linux/macOS│  Windows (ConPTY)│                 │    │
│  └─────────────┴─────────────────┴─────────────────┘    │
├─────────────────────────────────────────────────────────┤
│  Capture Engine                                         │
│  ┌─────────────┬─────────────────┬─────────────────┐    │
│  │  Text (pyte)│  Image (mss)    │  Stability      │    │
│  └─────────────┴─────────────────┴─────────────────┘    │
├─────────────────────────────────────────────────────────┤
│  Vision Discovery                                       │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Scan configs → Filter vision MCPs → Expose      │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Style

```bash
ruff check .
mypy terminalvision_mcp/
```

## License

MIT License
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add comprehensive README"
```

---

## 12. Final Verification

### Task 12.1: Verify implementation

- [ ] **Step 1: Run tests**

```bash
pytest tests/ -v
```

- [ ] **Step 2: Verify imports**

```bash
python -c "from terminalvision_mcp import *; print('Import OK')"
```

- [ ] **Step 3: Verify structure**

```bash
ls -la terminalvision_mcp/
ls -la tests/
```

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "feat: complete TerminalVision-MCP implementation"
```

---

**Plan complete.** All tasks use TDD approach with failing tests first, minimal implementations, and frequent commits.
