# TerminalVision-MCP

Universal MCP Server for terminal vision and control. Gives AI agents the ability to see and interact with terminal applications.

## Features

- **Text Capture**: Fast, efficient terminal screen capture via PTY + VT100 parsing
- **Image Capture**: Real screenshot capture when detailed vision is needed
- **Multi-Session**: Support for multiple persistent terminal sessions
- **Smart Vision**: Automatically discovers and uses available vision MCPs
- **Cross-Platform**: Windows (ConPTY), Linux (pty), macOS support
- **TUI Support**: Works with Vim, htop, nano, and any terminal application

## Installation

### Requirements

- Python 3.11+
- Windows 10/11, Linux, or macOS

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/terminalvision-mcp.git
cd terminalvision-mcp

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## Configuration

### Qwen Code

Add to your Qwen Code settings (settings.json):

```json
{
  "mcpServers": {
    "terminalvision": {
      "command": "python",
      "args": ["-m", "terminalvision_mcp"],
      "env": {}
    }
  }
}
```

### Claude Code

Add to your Claude Code settings:

```json
{
  "mcpServers": {
    "terminalvision": {
      "command": "python",
      "args": ["-m", "terminalvision_mcp"]
    }
  }
}
```

### Environment Variables

- `TERMINALVISION_VISION_MCP_LIST`: Comma-separated list of vision MCP names (fallback)
- `TERMINALVISION_SESSION_TTL`: Session TTL in minutes (default: 30)
- `TERMINALVISION_MAX_SESSIONS`: Maximum concurrent sessions (default: 50)

## Tools

### terminal_spawn

Spawn a new terminal session.

```python
terminal_spawn(command="bash", cwd="/home/user", cols=120, rows=40)
# Returns: {"session_id": "abc123", "success": true}
```

### terminal_get_screen

Capture the terminal screen.

```python
# Text capture (fast, efficient)
terminal_get_screen(session_id="abc123", format="text")
# Returns: {"type": "text", "content": "...", "hash": "md5hash"}

# Image capture (detailed vision)
terminal_get_screen(session_id="abc123", format="image")
# Returns: {"type": "image", "path": "/tmp/capture.png"}
```

### terminal_send_keys

Send key sequences to the terminal.

```python
terminal_send_keys(session_id="abc123", keys="Ctrl+C")
terminal_send_keys(session_id="abc123", keys="hello\n")
terminal_send_keys(session_id="abc123", keys="Esc:wq\n")
```

Supported key sequences:
- Control keys: `Ctrl+A`, `Ctrl+C`, `Ctrl+D`, etc.
- Special keys: `Esc`, `Up`, `Down`, `Left`, `Right`, `Home`, `End`, etc.
- Function keys: `F1` through `F12`
- Literal text and newlines

### terminal_wait_for_stable

Wait for the terminal screen to stop changing.

```python
terminal_wait_for_stable(session_id="abc123", timeout_ms=5000)
# Returns: {"stable": true, "final_hash": "md5hash", "iterations": 5}
```

### terminal_list_sessions

List all active terminal sessions.

```python
terminal_list_sessions()
# Returns: {"sessions": [{"id": "abc123", "command": "bash", ...}]}
```

### terminal_resize

Resize a terminal session.

```python
terminal_resize(session_id="abc123", cols=80, rows=24)
# Returns: {"success": true}
```

### terminal_kill

Kill a terminal session.

```python
terminal_kill(session_id="abc123")
# Returns: {"success": true}
```

### list_vision_mcps

List discovered vision MCPs in the system.

```python
list_vision_mcps()
# Returns: {"vision_mcps": [{"name": "ollama-vision", ...}]}
```

## How It Works

### Text vs Image Decision

TerminalVision-MCP prioritizes text capture because it is:

1. **Faster**: No screenshot processing needed
2. **More Efficient**: Lower token usage for AI models
3. **More Structured**: Text is easier for models to parse
4. **Complete**: VT100 parsing captures cursor position, colors, and attributes

Use image capture when:
- Visual layout matters (UI applications)
- Color accuracy is critical
- Text extraction is too complex

### Vision MCP Discovery

When an AI model doesn't natively support image input:

1. TerminalVision-MCP scans client configurations:
   - Qwen Code: `~/.qwen/settings.json`
   - Claude Code: `~/.claude/settings.json`
2. Identifies MCPs with vision-related tools
3. Exposes them via `list_vision_mcps`
4. Captures screenshot and calls the discovered vision MCP

### Session Management

- Sessions are stored in-memory
- Each session has a 30-minute TTL (configurable)
- Background cleanup removes expired sessions
- Maximum 50 concurrent sessions (configurable)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     MCP Server                          │
├─────────────────────────────────────────────────────────┤
│  Tools Layer                                            │
│  ┌──────────┬──────────┬──────────┬──────────┬─────────┐  │
│  │spawn    │get_screen│send_keys│wait_stable│list    │  │
│  └─────────┴─────────┴─────────┴──────────┴─────────┘  │
├─────────────────────────────────────────────────────────┤
│  Session Manager (in-memory + TTL)                     │
├─────────────────────────────────────────────────────────┤
│  PTY Handler (platform-specific)                        │
│  ┌─────────────┬─────────────────┬─────────────────┐    │
│  │  Linux/macOS│  Windows (ConPTY)│                 │    │
│  └─────────────┴─────────────────┴─────────────────┘    │
├─────────────────────────────────────────────────────────┤
│  Capture Engine                                         │
│  ┌─────────────┬─────────────────┬─────────────────┐    │
│  │  Text (pyte)│  Image (mss)    │  Stability      │    │
│  └─────────────┴─────────────────┴─────────────────┘    │
├─────────────────────────────────────────────────────────┤
│  Vision Discovery                                       │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Scan configs → Filter vision MCPs → Expose      │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Style

```bash
ruff check .
mypy terminalvision_mcp/
```

## License

MIT License
