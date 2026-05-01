@echo off
REM TerminalVision-MCP Python REPL (with venv activated)
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python %*
