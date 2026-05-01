"""HTTP client for CASCA terminal (Go daemon)."""

import httpx
from typing import Optional, List, Dict, Any


class CascaClient:
    """Client for CASCA terminal API."""

    def __init__(self, base_url: str = "http://localhost:8787"):
        self.base_url = base_url
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=30.0)
        return self._client

    def spawn(self, command: str = "cmd.exe", cols: int = 120, rows: int = 40, cwd: str | None = None) -> Dict[str, Any]:
        """Spawn a new terminal session."""
        payload = {"command": command, "cols": cols, "rows": rows}
        if cwd:
            payload["cwd"] = cwd
        response = self._get_client().post(
            f"{self.base_url}/terminal/spawn",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions."""
        response = self._get_client().get(f"{self.base_url}/terminal/list")
        response.raise_for_status()
        return response.json().get("sessions", [])

    def send_keys(self, session_id: str, keys: str) -> bool:
        """Send keys to a terminal session."""
        response = self._get_client().post(
            f"{self.base_url}/terminal/{session_id}/keys",
            json={"keys": keys}
        )
        response.raise_for_status()
        return response.json().get("success", False)

    def get_screen(self, session_id: str, format: str = "text") -> Dict[str, Any]:
        """Get screen capture from a terminal session."""
        response = self._get_client().get(
            f"{self.base_url}/terminal/{session_id}/screen",
            params={"format": format}
        )
        response.raise_for_status()
        return response.json()

    def resize(self, session_id: str, cols: int, rows: int) -> bool:
        """Resize a terminal session."""
        response = self._get_client().post(
            f"{self.base_url}/terminal/{session_id}/resize",
            json={"cols": cols, "rows": rows}
        )
        response.raise_for_status()
        return response.json().get("success", False)

    def kill(self, session_id: str) -> bool:
        """Kill a terminal session."""
        response = self._get_client().delete(f"{self.base_url}/terminal/{session_id}")
        response.raise_for_status()
        return response.json().get("success", False)

    def wait(self, session_id: str, condition: str, timeout_ms: int = 10000) -> Dict[str, Any]:
        """Wait for a condition on a terminal session."""
        response = self._get_client().get(
            f"{self.base_url}/terminal/{session_id}/wait",
            params={"condition": condition, "timeout_ms": timeout_ms}
        )
        response.raise_for_status()
        return response.json()

    def close(self):
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None
