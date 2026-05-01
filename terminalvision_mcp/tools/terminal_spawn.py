"""Terminal spawn tool."""

from mcp.types import TextContent
from terminalvision_mcp.client.casca_client import CascaClient


async def terminal_spawn(
    client: CascaClient,
    command: str = "cmd.exe",
    cols: int = 120,
    rows: int = 40,
    cwd: str | None = None
) -> TextContent:
    """Spawn a new terminal session."""
    try:
        result = client.spawn(command=command, cols=cols, rows=rows, cwd=cwd)
        session_id = result.get("session_id", "unknown")
        pid = result.get("pid", "?")
        return TextContent(
            type="text",
            text=f"Session `{session_id}` created (PID: {pid}, command: {command})"
        )
    except Exception as e:
        return TextContent(type="text", text=f"Error: {str(e)}")
