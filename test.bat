@echo off
REM TerminalVision-MCP Test Runner
REM Usage: test.bat [args]
cd /d "%~dp0"
call .venv\Scripts\activate.bat
pytest tests\ %*
