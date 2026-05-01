"""Terminal get screen tool."""

from mcp.types import TextContent
from typing import Any
from mcp.client.casca_client import CascaClient


async def terminal_get_screen(
    client: CascaClient,
    session_id: str,
    format: str = "text"
) -> TextContent:
    """Get screen capture from a terminal session."""
    try:
        result = client.get_screen(session_id=session_id, format=format)
        if result.get("type") == "text":
            content = result.get("content", "")
            return TextContent(type="text", text=content)
        else:
            path = result.get("path", "")
            return TextContent(type="text", text=f"[Image saved to: {path}]")
    except Exception as e:
        return TextContent(type="text", text=f"Error: {str(e)}")