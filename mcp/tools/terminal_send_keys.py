"""Terminal send keys tool."""

from mcp.types import TextContent
from mcp.client.casca_client import CascaClient


async def terminal_send_keys(
    client: CascaClient,
    session_id: str,
    keys: str
) -> TextContent:
    """Send keys to a terminal session."""
    try:
        success = client.send_keys(session_id=session_id, keys=keys)
        if success:
            return TextContent(type="text", text="Keys sent successfully")
        else:
            return TextContent(type="text", text="Failed to send keys")
    except Exception as e:
        return TextContent(type="text", text=f"Error: {str(e)}")