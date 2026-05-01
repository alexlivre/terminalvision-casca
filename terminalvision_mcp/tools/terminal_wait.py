"""Terminal wait for stable tool."""

from mcp.types import TextContent
from terminalvision_mcp.client.casca_client import CascaClient


async def terminal_wait(
    client: CascaClient,
    session_id: str,
    condition: str = "stable",
    timeout_ms: int = 10000
) -> TextContent:
    """Wait for a terminal to become stable (no new output)."""
    try:
        result = client.wait(session_id=session_id, condition=condition, timeout_ms=timeout_ms)
        met = result.get("met", False)
        waited = result.get("waited_ms", 0)
        if met:
            return TextContent(type="text", text=f"Condition met after {waited}ms")
        return TextContent(type="text", text=f"Timeout after {waited}ms (condition not met)")
    except Exception as e:
        return TextContent(type="text", text=f"Error: {str(e)}")
