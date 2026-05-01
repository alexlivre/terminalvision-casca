"""Terminal list sessions tool."""

from mcp.types import TextContent
from terminalvision_mcp.client.casca_client import CascaClient


async def terminal_list_sessions(client: CascaClient) -> TextContent:
    """List all active terminal sessions."""
    try:
        sessions = client.list_sessions()
        if not sessions:
            return TextContent(type="text", text="No active sessions.")
        lines = [f"**Active Sessions ({len(sessions)}):**"]
        for s in sessions:
            lines.append(
                f"- `{s.get('session_id','?')}` "
                f"cmd: `{s.get('command','?')}` "
                f"PID: {s.get('pid','?')} "
                f"status: {s.get('status','?')} "
                f"mode: {s.get('mode','?')}"
            )
        return TextContent(type="text", text="\n".join(lines))
    except Exception as e:
        return TextContent(type="text", text=f"Error: {str(e)}")
