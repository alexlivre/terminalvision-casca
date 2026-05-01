"""TerminalVision MCP Server - Entry point.

Run with:
    python -m terminalvision_mcp
Or via MCP stdio:
    uvx terminalvision_mcp
"""

import asyncio
import logging
import sys
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.types import (
    ServerCapabilities,
    Tool,
    TextContent,
)
import mcp.server.stdio

from terminalvision_mcp.client.casca_client import CascaClient
from terminalvision_mcp.tools import (
    terminal_spawn,
    terminal_get_screen,
    terminal_send_keys,
    terminal_list_sessions,
    terminal_resize,
    terminal_kill,
    terminal_wait,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("terminalvision")


async def main():
    """Start the MCP server via stdio."""
    client = CascaClient()
    server = Server("terminalvision")

    # Tool definitions
    tools = [
        Tool(
            name="terminal_spawn",
            description="Spawn a new terminal session. Returns session_id.",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Command to run (default: cmd.exe)"},
                    "cols": {"type": "integer", "description": "Number of columns (default: 120)"},
                    "rows": {"type": "integer", "description": "Number of rows (default: 40)"},
                },
                "required": [],
            },
        ),
        Tool(
            name="terminal_get_screen",
            description="Get screen contents from a terminal session.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID"},
                    "format": {"type": "string", "description": "Format: text or image (default: text)"},
                },
                "required": ["session_id"],
            },
        ),
        Tool(
            name="terminal_send_keys",
            description="Send keystrokes to a terminal session.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID"},
                    "keys": {"type": "string", "description": "Keys to send (use \\r\\n for enter)"},
                },
                "required": ["session_id", "keys"],
            },
        ),
        Tool(
            name="terminal_list_sessions",
            description="List all active terminal sessions.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="terminal_resize",
            description="Resize a terminal session.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID"},
                    "cols": {"type": "integer", "description": "Number of columns (default: 80)"},
                    "rows": {"type": "integer", "description": "Number of rows (default: 24)"},
                },
                "required": ["session_id"],
            },
        ),
        Tool(
            name="terminal_kill",
            description="Kill a terminal session.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID"},
                },
                "required": ["session_id"],
            },
        ),
        Tool(
            name="terminal_wait",
            description="Wait for a terminal to become stable or a condition to be met.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID"},
                    "condition": {"type": "string", "description": "Condition to wait for (default: stable)"},
                    "timeout_ms": {"type": "integer", "description": "Timeout in ms (default: 10000)"},
                },
                "required": ["session_id"],
            },
        ),
    ]

    # Map tool names to handler functions
    tool_handlers = {
        "terminal_spawn": terminal_spawn,
        "terminal_get_screen": terminal_get_screen,
        "terminal_send_keys": terminal_send_keys,
        "terminal_list_sessions": terminal_list_sessions,
        "terminal_resize": terminal_resize,
        "terminal_kill": terminal_kill,
        "terminal_wait": terminal_wait,
    }

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return tools

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        handler = tool_handlers.get(name)
        if not handler:
            raise ValueError(f"Unknown tool: {name}")

        logger.info(f"Calling tool: {name} with {arguments}")

        # Only pass client arg for tools that need it
        if name == "terminal_list_sessions":
            result = await handler(client)
        else:
            result = await handler(client, **arguments)

        return [result]

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="terminalvision",
                server_version="0.1.0",
                capabilities=ServerCapabilities(tools={}),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
