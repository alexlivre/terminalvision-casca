"""Entry point for python -m terminalvision_mcp."""

from terminalvision_mcp.main import main

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
