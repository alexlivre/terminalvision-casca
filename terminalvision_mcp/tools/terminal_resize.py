"""Terminal resize tool."""

from mcp.types import TextContent
from terminalvision_mcp.client.casca_client import CascaClient


async def terminal_resize(
    client: CascaClient,
    session_id: str,
    cols: int = 80,
    rows: int = 24
) -> TextContent:
    """Resize a terminal session."""
    try:
        success = client.resize(session_id=session_id, cols=cols, rows=rows)
        if success:
            return TextContent(type="text", text=f"Session `{session_id}` resized to {cols}x{rows}")
        return TextContent(type="text", text="Failed to resize session")
    except Exception as e:
        return TextContent(type="text", text=f"Error: {str(e)}")
