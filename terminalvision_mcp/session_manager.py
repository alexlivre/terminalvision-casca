"""Session manager for terminal sessions."""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional

from terminalvision_mcp.types import SessionInfo


_SESSION_TTL_MINUTES = 30
_MAX_SESSIONS = 50


class SessionManager:
    """Manages terminal sessions with TTL and cleanup."""

    def __init__(self, ttl_minutes: int = _SESSION_TTL_MINUTES, max_sessions: int = _MAX_SESSIONS):
        """Initialize session manager.
        
        Args:
            ttl_minutes: Session TTL in minutes
            max_sessions: Maximum concurrent sessions
        """
        self.sessions: Dict[str, SessionInfo] = {}
        self.handlers: Dict[str, any] = {}
        self.ttl = timedelta(minutes=ttl_minutes)
        self.max_sessions = max_sessions
        self._cleanup_task: Optional[asyncio.Task] = None

    async def spawn_session(
        self,
        command: str,
        cwd: Optional[str] = None,
        cols: int = 120,
        rows: int = 40,
    ) -> SessionInfo:
        """Spawn a new terminal session.
        
        Args:
            command: Command to execute
            cwd: Working directory
            cols: Number of columns
            rows: Number of rows
            
        Returns:
            SessionInfo for the new session
        """
        if len(self.sessions) >= self.max_sessions:
            raise RuntimeError(f"Maximum sessions ({self.max_sessions}) reached")

        session_id = str(uuid.uuid4())[:8]
        
        session = SessionInfo(
            id=session_id,
            command=command,
            cols=cols,
            rows=rows,
        )
        
        self.sessions[session_id] = session
        
        return session

    async def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """Get session info.
        
        Args:
            session_id: Session ID
            
        Returns:
            SessionInfo or None if not found
        """
        return self.sessions.get(session_id)

    async def get_handler(self, session_id: str):
        """Get PTY handler for session.
        
        Args:
            session_id: Session ID
            
        Returns:
            PTY handler or None
        """
        return self.handlers.get(session_id)

    async def update_activity(self, session_id: str) -> None:
        """Update last activity timestamp.
        
        Args:
            session_id: Session ID
        """
        session = self.sessions.get(session_id)
        if session:
            session.last_activity = datetime.now()

    async def resize_session(self, session_id: str, cols: int, rows: int) -> bool:
        """Resize a session.
        
        Args:
            session_id: Session ID
            cols: New number of columns
            rows: New number of rows
            
        Returns:
            True if successful
        """
        session = self.sessions.get(session_id)
        if session:
            session.cols = cols
            session.rows = rows
            return True
        return False

    async def kill_session(self, session_id: str) -> bool:
        """Kill a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if successful
        """
        handler = self.handlers.pop(session_id, None)
        if handler:
            try:
                handler.close()
            except Exception:
                pass
        
        session = self.sessions.pop(session_id, None)
        return session is not None

    async def list_sessions(self) -> list[SessionInfo]:
        """List all active sessions.
        
        Returns:
            List of SessionInfo
        """
        return list(self.sessions.values())

    async def start_cleanup_task(self) -> None:
        """Start background cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def _cleanup_loop(self) -> None:
        """Background cleanup loop."""
        while True:
            await asyncio.sleep(60)
            await self._cleanup_expired()

    async def _cleanup_expired(self) -> None:
        """Clean up expired sessions."""
        now = datetime.now()
        expired = [
            sid for sid, session in self.sessions.items()
            if now - session.last_activity > self.ttl
        ]
        
        for session_id in expired:
            await self.kill_session(session_id)


_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get global session manager instance.
    
    Returns:
        SessionManager singleton
    """
    global _manager
    if _manager is None:
        _manager = SessionManager()
    return _manager