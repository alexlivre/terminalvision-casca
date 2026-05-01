"""PTY handler with platform-specific implementations."""

import os
import sys
import platform
from abc import ABC, abstractmethod
from typing import Optional


class PTYHandler(ABC):
    """Abstract PTY handler."""

    @abstractmethod
    def read(self) -> str:
        """Read available data from PTY."""
        pass

    @abstractmethod
    def write(self, data: str) -> bool:
        """Write data to PTY."""
        pass

    @abstractmethod
    def resize(self, cols: int, rows: int) -> bool:
        """Resize terminal."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close PTY."""
        pass


class UnixPTYHandler(PTYHandler):
    """Unix PTY handler using pty module."""

    def __init__(self, command: str, cwd: Optional[str] = None, cols: int = 120, rows: int = 40):
        """Initialize Unix PTY handler.

        Args:
            command: Command to execute
            cwd: Working directory
            cols: Columns
            rows: Rows
        """
        import pty

        self.pid, self.fd = pty.fork()

        if self.pid == 0:
            # Child process
            if cwd:
                os.chdir(cwd)
            os.execvp("sh", ["sh", "-c", command])
        else:
            # Parent process
            import fcntl
            import struct
            import termios

            # Set non-blocking
            flags = fcntl.fcntl(self.fd, fcntl.F_GETFL)
            fcntl.fcntl(self.fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

            # Set terminal size
            self.resize(cols, rows)

    def read(self) -> str:
        """Read available data."""
        try:
            return os.read(self.fd, 4096).decode("utf-8", errors="replace")
        except OSError:
            return ""

    def write(self, data: str) -> bool:
        """Write data."""
        try:
            os.write(self.fd, data.encode("utf-8"))
            return True
        except OSError:
            return False

    def resize(self, cols: int, rows: int) -> bool:
        """Resize terminal."""
        import fcntl
        import struct
        import termios

        try:
            winsize = struct.pack("HHHH", rows, cols, 0, 0)
            fcntl.ioctl(self.fd, termios.TIOCSWINSZ, winsize)
            return True
        except OSError:
            return False

    def close(self) -> None:
        """Close PTY."""
        try:
            os.close(self.fd)
        except OSError:
            pass
        try:
            import fcntl
            fcntl.wait4(self.pid, 0)
        except OSError:
            pass


def create_pty_handler(command: str, cwd: Optional[str] = None, cols: int = 120, rows: int = 40) -> PTYHandler:
    """Create platform-appropriate PTY handler.

    Args:
        command: Command to execute
        cwd: Working directory
        cols: Columns
        rows: Rows

    Returns:
        PTYHandler instance
    """
    if platform.system() == "Windows":
        return WindowsConPTYHandler(command, cwd, cols, rows)
    else:
        return UnixPTYHandler(command, cwd, cols, rows)


class WindowsConPTYHandler(PTYHandler):
    """Windows ConPTY handler."""

    def __init__(self, command: str, cwd: Optional[str] = None, cols: int = 120, rows: int = 40):
        """Initialize Windows ConPTY handler.

        Args:
            command: Command to execute
            cwd: Working directory
            cols: Columns
            rows: Rows
        """
        self.command = command
        self.cwd = cwd
        self.cols = cols
        self.rows = rows
        self.process: Optional[any] = None
        self._started = False

    def _start(self) -> None:
        """Start the subprocess."""
        if self._started:
            return

        import subprocess

        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE

        self.process = subprocess.Popen(
            self.command,
            shell=True,
            cwd=self.cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=startupinfo,
            env=os.environ.copy(),
        )
        self._started = True

    def read(self) -> str:
        """Read available data."""
        self._start()
        if self.process and self.process.stdout:
            import select

            if select.select([self.process.stdout], [], [], 0)[0]:
                return self.process.stdout.read().decode("utf-8", errors="replace")
        return ""

    def write(self, data: str) -> bool:
        """Write data."""
        self._start()
        if self.process and self.process.stdin:
            try:
                self.process.stdin.write(data.encode("utf-8"))
                self.process.stdin.flush()
                return True
            except OSError:
                return False
        return False

    def resize(self, cols: int, rows: int) -> bool:
        """Resize terminal (Windows ConPTY auto-resizes)."""
        self.cols = cols
        self.rows = rows
        return True

    def close(self) -> None:
        """Close subprocess."""
        if self.process:
            self.process.terminate()
            self.process.wait()