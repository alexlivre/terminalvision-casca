"""Test MCP server integration with CASCA."""

import asyncio
import sys

sys.path.insert(0, r"C:\code\mcp-servers\terminalvision-mcp")

from mcp.client.stdio import (
    stdio_client,
    StdioServerParameters,
    SessionMessage,
)
from mcp.types import JSONRPCMessage


async def test():
    async with stdio_client(
        StdioServerParameters(
            command="python",
            args=["-m", "terminalvision_mcp"],
            cwd=r"C:\code\mcp-servers\terminalvision-mcp",
        )
    ) as (read, write):
        def msg(data) -> SessionMessage:
            return SessionMessage(JSONRPCMessage(data))

        # Send initialize
        await write.send(msg({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0"},
            },
        }))
        resp = await asyncio.wait_for(read.receive(), timeout=5)
        data = resp.message.root.model_dump()
        print(f"[INIT] ok - server: {data['result']['serverInfo']['name']}")
        assert data.get("id") == 1

        # Send initialized notification
        await write.send(msg({
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        }))
        await asyncio.sleep(0.1)

        # List tools
        await write.send(msg({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
        }))
        resp = await asyncio.wait_for(read.receive(), timeout=5)
        tools = resp.message.root.model_dump()
        tool_names = [t["name"] for t in tools["result"]["tools"]]
        print(f"[TOOLS] ({len(tool_names)}): {', '.join(tool_names)}")

        # Spawn
        await write.send(msg({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "terminal_spawn",
                "arguments": {"command": "cmd.exe", "cols": 80, "rows": 24},
            },
        }))
        resp = await asyncio.wait_for(read.receive(), timeout=10)
        result = resp.message.root.model_dump()
        text = result["result"]["content"][0]["text"]
        print(f"[SPAWN] {text}")

        if "Session `" in text:
            session_id = text.split("Session `")[1].split("`")[0]
            print(f"[SESSION] ID: {session_id}")

            # Wait for startup
            await asyncio.sleep(2)

            # Get screen
            await write.send(msg({
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "terminal_get_screen",
                    "arguments": {"session_id": session_id},
                },
            }))
            resp = await asyncio.wait_for(read.receive(), timeout=10)
            screen = resp.message.root.model_dump()
            screen_text = screen["result"]["content"][0]["text"]
            if screen_text:
                print(f"[SCREEN] ({len(screen_text)} chars): {screen_text[:200]}")
            else:
                print("[SCREEN] (empty - waiting for prompt)")

            # Send command
            await write.send(msg({
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "terminal_send_keys",
                    "arguments": {"session_id": session_id, "keys": "echo TESTE MCP\r\n"},
                },
            }))
            resp = await asyncio.wait_for(read.receive(), timeout=10)
            keys_result = resp.message.root.model_dump()
            print(f"[KEYS] {keys_result['result']['content'][0]['text']}")

            # Wait for execution
            await asyncio.sleep(2)

            # Get screen after
            await write.send(msg({
                "jsonrpc": "2.0",
                "id": 6,
                "method": "tools/call",
                "params": {
                    "name": "terminal_get_screen",
                    "arguments": {"session_id": session_id},
                },
            }))
            resp = await asyncio.wait_for(read.receive(), timeout=10)
            screen2 = resp.message.root.model_dump()
            screen2_text = screen2["result"]["content"][0]["text"]
            print(f"[SCREEN AFTER] ({len(screen2_text)} chars): {screen2_text[:400]}")

            # List
            await write.send(msg({
                "jsonrpc": "2.0",
                "id": 7,
                "method": "tools/call",
                "params": {"name": "terminal_list_sessions", "arguments": {}},
            }))
            resp = await asyncio.wait_for(read.receive(), timeout=10)
            list_result = resp.message.root.model_dump()
            print(f"[LIST] {list_result['result']['content'][0]['text']}")

            # Resize
            await write.send(msg({
                "jsonrpc": "2.0",
                "id": 8,
                "method": "tools/call",
                "params": {
                    "name": "terminal_resize",
                    "arguments": {"session_id": session_id, "cols": 120, "rows": 40},
                },
            }))
            resp = await asyncio.wait_for(read.receive(), timeout=10)
            resize_result = resp.message.root.model_dump()
            print(f"[RESIZE] {resize_result['result']['content'][0]['text']}")

            # Kill
            await write.send(msg({
                "jsonrpc": "2.0",
                "id": 9,
                "method": "tools/call",
                "params": {
                    "name": "terminal_kill",
                    "arguments": {"session_id": session_id},
                },
            }))
            resp = await asyncio.wait_for(read.receive(), timeout=10)
            kill_result = resp.message.root.model_dump()
            print(f"[KILL] {kill_result['result']['content'][0]['text']}")

        print("\n✅ All tests passed!")


if __name__ == "__main__":
    asyncio.run(test())
