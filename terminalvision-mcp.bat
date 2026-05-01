@echo off
REM TerminalVision-MCP Server Launcher
REM Usage: terminalvision-mcp.bat [args]
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python -m terminalvision_mcp %*
