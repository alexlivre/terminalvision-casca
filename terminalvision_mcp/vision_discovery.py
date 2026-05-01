"""Vision MCP discovery - scans client configs for vision MCPs."""

import json
import os
import sys
from pathlib import Path
from typing import List, Optional

from terminalvision_mcp.types import VisionMCPInfo


# Vision-related tool patterns
VISION_TOOL_PATTERNS = [
    "vision",
    "image",
    "describe",
    "screenshot",
    "ocr",
    "screen",
]


def _match_vision_tool(tool_name: str) -> bool:
    """Check if a tool name suggests vision capability."""
    tool_lower = tool_name.lower()
    return any(pattern in tool_lower for pattern in VISION_TOOL_PATTERNS)


def _parse_mcp_config(config_path: Path) -> List[VisionMCPInfo]:
    """Parse a MCP config file and extract vision MCPs.
    
    Args:
        config_path: Path to config file
        
    Returns:
        List of VisionMCPInfo for discovered vision MCPs
    """
    mcps: List[VisionMCPInfo] = []
    
    try:
        with open(config_path) as f:
            config = json.load(f)
        
        # Handle different config formats
        servers = config.get("mcpServers", config.get("mcp_servers", {}))
        
        for name, server_config in servers.items():
            # Get tools if available
            tools = server_config.get("tools", [])
            
            # Check if any tools suggest vision capability
            if tools:
                vision_tools = [t for t in tools if _match_vision_tool(t)]
                if vision_tools:
                    mcps.append(VisionMCPInfo(
                        name=name,
                        description=f"Vision MCP from {config_path.parent.name}",
                        source=config_path.parent.name,
                        tools=vision_tools,
                    ))
    except Exception:
        pass
    
    return mcps


class VisionDiscovery:
    """Discovers vision MCPs from client configurations."""

    def __init__(self):
        """Initialize vision discovery."""
        self._mcps: List[VisionMCPInfo] = []
        self._discovered = False

    def discover(self) -> None:
        """Discover vision MCPs from all sources."""
        if self._discovered:
            return
        
        self._mcps = []
        
        # Platform-specific config paths
        if sys.platform == "win32":
            base = Path(os.path.expanduser("~"))
            config_paths = [
                base / ".qwen" / "settings.json",
                base / ".claude" / "settings.json",
            ]
        else:
            base = Path(os.path.expanduser("~"))
            config_paths = [
                base / ".claude" / "settings.json",
                base / ".config" / "qwen" / "settings.json",
            ]
        
        # Scan config files
        for path in config_paths:
            if path.exists():
                self._mcps.extend(_parse_mcp_config(path))
        
        # Environment variable fallback
        env_list = os.environ.get("TERMINALVISION_VISION_MCP_LIST", "")
        if env_list:
            for name in env_list.split(","):
                name = name.strip()
                if name:
                    self._mcps.append(VisionMCPInfo(
                        name=name,
                        description="From TERMINALVISION_VISION_MCP_LIST",
                        source="env",
                        tools=["vision"],
                    ))
        
        self._discovered = True

    def list_vision_mcps(self) -> List[VisionMCPInfo]:
        """List discovered vision MCPs.
        
        Returns:
            List of VisionMCPInfo
        """
        self.discover()
        return self._mcps


_discovery: Optional[VisionDiscovery] = None


def get_vision_discovery() -> VisionDiscovery:
    """Get global vision discovery instance.
    
    Returns:
        VisionDiscovery singleton
    """
    global _discovery
    if _discovery is None:
        _discovery = VisionDiscovery()
    return _discovery
