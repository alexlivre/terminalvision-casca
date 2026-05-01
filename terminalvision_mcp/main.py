"""TerminalVision-MCP: Universal MCP Server for terminal vision and control."""

import asyncio

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from terminalvision_mcp.session_manager import get_session_manager
from terminalvision_mcp.vision_discovery import get_vision_discovery
from terminalvision_mcp.capture import CaptureEngine
from terminalvision_mcp.key_mapper import parse_key_sequence
from terminalvision_mcp.stability import StabilityDetector
from terminalvision_mcp.handlers import create_pty_handler
from terminalvision_mcp.types import StabilityResult


app = Server("terminalvision-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="terminal_spawn",
            description="Spawn a new terminal session",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Command to execute",
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory",
                    },
                    "cols": {
                        "type": "integer",
                        "description": "Number of columns",
                        "default": 120,
                    },
                    "rows": {
                        "type": "integer",
                        "description": "Number of rows",
                        "default": 40,
                    },
                },
                "required": ["command"],
            },
        ),
        Tool(
            name="terminal_get_screen",
            description="Capture the terminal screen (text or image)",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID to capture",
                    },
                    "format": {
                        "type": "string",
                        "enum": ["text", "image"],
                        "description": "Capture format",
                        "default": "text",
                    },
                },
                "required": ["session_id"],
            },
        ),
        Tool(
            name="terminal_send_keys",
            description="Send key sequences to the terminal",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID",
                    },
                    "keys": {
                        "type": "string",
                        "description": "Keys to send (e.g., 'Ctrl+C', 'hello\\n')",
                    },
                },
                "required": ["session_id", "keys"],
            },
        ),
        Tool(
            name="terminal_wait_for_stable",
            description="Wait for terminal screen to become stable",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID",
                    },
                    "timeout_ms": {
                        "type": "integer",
                        "description": "Timeout in milliseconds",
                        "default": 5000,
                    },
                },
                "required": ["session_id"],
            },
        ),
        Tool(
            name="terminal_list_sessions",
            description="List all active terminal sessions",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="terminal_resize",
            description="Resize a terminal session",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID to resize",
                    },
                    "cols": {
                        "type": "integer",
                        "description": "New number of columns",
                    },
                    "rows": {
                        "type": "integer",
                        "description": "New number of rows",
                    },
                },
                "required": ["session_id", "cols", "rows"],
            },
        ),
        Tool(
            name="terminal_kill",
            description="Kill a terminal session",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID to kill",
                    },
                },
                "required": ["session_id"],
            },
        ),
        Tool(
            name="list_vision_mcps",
            description="List discovered vision MCPs in the system",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    manager = get_session_manager()
    discovery = get_vision_discovery()

    try:
        if name == "terminal_spawn":
            session = await manager.spawn_session(
                command=arguments.get("command"),
                cwd=arguments.get("cwd"),
                cols=arguments.get("cols", 120),
                rows=arguments.get("rows", 40),
            )

            # Create and store PTY handler
            handler = create_pty_handler(
                command=session.command,
                cwd=arguments.get("cwd"),
                cols=session.cols,
                rows=session.rows,
            )
            manager.handlers[session.id] = handler

            return [TextContent(type="text", text=f'{{"session_id": "{session.id}", "success": true}}')]

        elif name == "terminal_get_screen":
            session_id = arguments["session_id"]
            format_type = arguments.get("format", "text")

            handler = await manager.get_handler(session_id)
            if not handler:
                return [TextContent(type="text", text='{"error": "Session not found"}')]

            await manager.update_activity(session_id)
            session_info = await manager.get_session(session_id)

            capture = CaptureEngine(cols=session_info.cols, rows=session_info.rows)
            capture.update_from_pty(handler)

            if format_type == "image":
                result = capture.capture_image()
                if result.path:
                    return [TextContent(type="text", text=f'{{"type": "image", "path": "{result.path}"}}')]
                else:
                    return [TextContent(type="text", text='{"error": "Failed to capture image"}')]
            else:
                result = capture.capture_text()
                return [TextContent(type="text", text=f'{{"type": "text", "content": {repr(result.content)}, "hash": "{result.hash}"}}')]

        elif name == "terminal_send_keys":
            session_id = arguments["session_id"]
            keys = arguments["keys"]

            handler = await manager.get_handler(session_id)
            if not handler:
                return [TextContent(type="text", text='{"success": false, "error": "Session not found"}')]

            # Map key sequences
            mapped_keys = parse_key_sequence(keys)
            success = handler.write(mapped_keys)

            if success:
                await manager.update_activity(session_id)

            return [TextContent(type="text", text=f'{{"success": {str(success).lower()}}}')]

        elif name == "terminal_wait_for_stable":
            session_id = arguments["session_id"]
            timeout_ms = arguments.get("timeout_ms", 5000)

            handler = await manager.get_handler(session_id)
            if not handler:
                return [TextContent(type="text", text='{"stable": false, "error": "Session not found"}')]

            session_info = await manager.get_session(session_id)
            detector = StabilityDetector()
            result: StabilityResult = await detector.wait_for_stable(
                handler,
                timeout_ms,
                cols=session_info.cols,
                rows=session_info.rows,
            )

            return [TextContent(type="text", text=f'{{"stable": {str(result.stable).lower()}, "final_hash": "{result.final_hash or ""}", "iterations": {result.iterations}}}')]

        elif name == "terminal_list_sessions":
            sessions = await manager.list_sessions()
            sessions_data = [
                {
                    "id": s.id,
                    "command": s.command,
                    "created": s.created.isoformat(),
                    "cols": s.cols,
                    "rows": s.rows,
                }
                for s in sessions
            ]
            import json
            return [TextContent(type="text", text=json.dumps({"sessions": sessions_data}))]

        elif name == "terminal_resize":
            session_id = arguments["session_id"]
            cols = arguments["cols"]
            rows = arguments["rows"]

            handler = await manager.get_handler(session_id)
            if handler:
                handler.resize(cols, rows)

            success = await manager.resize_session(session_id, cols, rows)
            return [TextContent(type="text", text=f'{{"success": {str(success).lower()}}}')]

        elif name == "terminal_kill":
            session_id = arguments["session_id"]
            success = await manager.kill_session(session_id)
            return [TextContent(type="text", text=f'{{"success": {str(success).lower()}}}')]

        elif name == "list_vision_mcps":
            mcps = discovery.list_vision_mcps()
            mcps_data = [
                {
                    "name": m.name,
                    "description": m.description,
                    "source": m.source,
                    "tools": m.tools,
                }
                for m in mcps
            ]
            import json
            return [TextContent(type="text", text=json.dumps({"vision_mcps": mcps_data}))]

        else:
            return [TextContent(type="text", text=f'{{"error": "Unknown tool: {name}"}}')]

    except Exception as e:
        import traceback
        traceback.print_exc()
        return [TextContent(type="text", text=f'{{"error": {repr(e)}}}')]


async def main():
    """Main entry point."""
    manager = get_session_manager()
    await manager.start_cleanup_task()

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())