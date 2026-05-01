"""Stability detection for terminal screen changes."""

import asyncio
from typing import Optional

from terminalvision_mcp.types import StabilityResult
from terminalvision_mcp.capture import CaptureEngine


_STABILITY_CHECK_INTERVAL = 0.1  # seconds
_STABILITY_THRESHOLD = 3  # consecutive same hashes to be stable


class StabilityDetector:
    """Detects when terminal screen becomes stable."""

    async def wait_for_stable(
        self,
        handler,
        timeout_ms: int = 5000,
        cols: int = 120,
        rows: int = 40,
    ) -> StabilityResult:
        """Wait for terminal screen to become stable.
        
        Args:
            handler: PTY handler
            timeout_ms: Maximum wait time in milliseconds
            cols: Number of columns
            rows: Number of rows
            
        Returns:
            StabilityResult with stability status
        """
        capture = CaptureEngine(cols=cols, rows=rows)
        timeout = timeout_ms / 1000.0
        start = asyncio.get_event_loop().time()
        
        last_hash: Optional[str] = None
        consecutive = 0
        
        while True:
            elapsed = asyncio.get_event_loop().time() - start
            if elapsed >= timeout:
                return StabilityResult(
                    stable=False,
                    final_hash=last_hash,
                    iterations=consecutive,
                )
            
            capture.update_from_pty(handler)
            current_hash = capture.text_capture.get_hash()
            
            if current_hash == last_hash:
                consecutive += 1
                if consecutive >= _STABILITY_THRESHOLD:
                    return StabilityResult(
                        stable=True,
                        final_hash=current_hash,
                        iterations=consecutive,
                    )
            else:
                consecutive = 0
                last_hash = current_hash
            
            await asyncio.sleep(_STABILITY_CHECK_INTERVAL)