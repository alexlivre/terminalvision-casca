"""Capture engine for text and image capture."""

import hashlib
import tempfile
from typing import Optional

import pyte
import mss

from terminalvision_mcp.types import (
    ScreenCapture,
    ScreenCaptureType,
)


class TextCapture:
    """Text capture using pyte terminal emulator."""

    def __init__(self, cols: int = 120, rows: int = 40):
        """Initialize text capture.

        Args:
            cols: Number of columns
            rows: Number of rows
        """
        self.screen = pyte.Screen(cols, rows)
        self.stream = pyte.Stream(self.screen)
        self._last_hash: Optional[str] = None

    def update(self, data: str) -> None:
        """Update with terminal data.

        Args:
            data: Terminal output data
        """
        self.stream.feed(data)

    def get_text(self) -> str:
        """Get current screen text.

        Returns:
            Screen text as string
        """
        lines = []
        for row in self.screen.display:
            # Only filter block chars, keep spaces
            line = "".join(char[0] for char in row if char[0] != "\u2592")
            if line.rstrip():
                lines.append(line.rstrip())
        return "\n".join(lines)

    def get_hash(self) -> str:
        """Get hash of current screen.

        Returns:
            MD5 hash of screen content
        """
        text = self.get_text()
        self._last_hash = hashlib.md5(text.encode()).hexdigest()
        return self._last_hash


class ImageCapture:
    """Image capture using mss."""

    def __init__(self):
        """Initialize image capture."""
        self.sct = mss.MSS()

    def capture(self, output_path: Optional[str] = None) -> str:
        """Capture full screen.

        Args:
            output_path: Optional path to save screenshot

        Returns:
            Path to saved screenshot
        """
        if output_path is None:
            output_path = tempfile.mktemp(suffix=".png")

        self.sct.save(output=output_path)
        return output_path


class CaptureEngine:
    """Combined capture engine for text and image."""

    def __init__(self, cols: int = 120, rows: int = 40):
        """Initialize capture engine.

        Args:
            cols: Number of columns
            rows: Number of rows
        """
        self.text_capture = TextCapture(cols, rows)
        self.image_capture = ImageCapture()
        self.cols = cols
        self.rows = rows

    def update_from_pty(self, handler) -> None:
        """Update text capture from PTY handler.

        Args:
            handler: PTY handler with read() method
        """
        try:
            data = handler.read()
            if data:
                self.text_capture.update(data)
        except Exception:
            pass

    def capture_text(self) -> ScreenCapture:
        """Capture text screen.

        Returns:
            ScreenCapture with text content
        """
        return ScreenCapture(
            type=ScreenCaptureType.TEXT,
            content=self.text_capture.get_text(),
            hash=self.text_capture.get_hash(),
        )

    def capture_image(self) -> ScreenCapture:
        """Capture image screen.

        Returns:
            ScreenCapture with image path
        """
        try:
            path = self.image_capture.capture()
            return ScreenCapture(
                type=ScreenCaptureType.IMAGE,
                path=path,
            )
        except Exception:
            return ScreenCapture(
                type=ScreenCaptureType.IMAGE,
                path=None,
            )