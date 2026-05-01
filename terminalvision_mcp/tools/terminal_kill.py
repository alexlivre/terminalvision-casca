"""Terminal kill tool."""

from mcp.types import TextContent
from terminalvision_mcp.client.casca_client import CascaClient


async def terminal_kill(
    client: CascaClient,
    session_id: str
) -> TextContent:
    """Kill a terminal session."""
    try:
        success = client.kill(session_id=session_id)
        if success:
            return TextContent(type="text", text=f"Session `{session_id}` killed.")
        return TextContent(type="text", text=f"Failed to kill session `{session_id}`")
    except Exception as e:
        return TextContent(type="text", text=f"Error: {str(e)}")
