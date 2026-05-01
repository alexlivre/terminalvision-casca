"""Key sequence mapper for terminal control."""

from typing import Dict

KEY_MAPPINGS: Dict[str, str] = {
    # Control keys
    "Ctrl+A": "\x01",
    "Ctrl+B": "\x02",
    "Ctrl+C": "\x03",
    "Ctrl+D": "\x04",
    "Ctrl+E": "\x05",
    "Ctrl+F": "\x06",
    "Ctrl+G": "\x07",
    "Ctrl+H": "\x08",
    "Ctrl+I": "\x09",  # Tab
    "Ctrl+J": "\x0a",
    "Ctrl+K": "\x0b",
    "Ctrl+L": "\x0c",
    "Ctrl+M": "\x0d",  # Enter
    "Ctrl+N": "\x0e",
    "Ctrl+O": "\x0f",
    "Ctrl+P": "\x10",
    "Ctrl+Q": "\x11",
    "Ctrl+R": "\x12",
    "Ctrl+S": "\x13",
    "Ctrl+T": "\x14",
    "Ctrl+U": "\x15",
    "Ctrl+V": "\x16",
    "Ctrl+W": "\x17",
    "Ctrl+X": "\x18",
    "Ctrl+Y": "\x19",
    "Ctrl+Z": "\x1a",
    # Escape
    "Esc": "\x1b",
    "Escape": "\x1b",
    # Arrow keys
    "Up": "\x1b[A",
    "Down": "\x1b[B",
    "Right": "\x1b[C",
    "Left": "\x1b[D",
    # Navigation
    "Home": "\x1b[H",
    "End": "\x1b[F",
    "PageUp": "\x1b[5~",
    "PageDown": "\x1b[6~",
    # Function keys (F1-F12)
    "F1": "\x1bOP",
    "F2": "\x1bOQ",
    "F3": "\x1bOR",
    "F4": "\x1bOS",
    "F5": "\x1b[15~",
    "F6": "\x1b[17~",
    "F7": "\x1b[18~",
    "F8": "\x1b[19~",
    "F9": "\x1b[20~",
    "F10": "\x1b[21~",
    "F11": "\x1b[23~",
    "F12": "\x1b[24~",
    # Delete/Insert/Backspace
    "Delete": "\x1b[3~",
    "Insert": "\x1b[2~",
    "Backspace": "\x7f",
}


def map_key_sequence(key: str) -> str:
    """Map a key name to its terminal escape sequence.

    Args:
        key: Key name (e.g., "Ctrl+C", "Up", "Esc")

    Returns:
        Escape sequence to send to terminal
    """
    return KEY_MAPPINGS.get(key, key)


def parse_key_sequence(input_str: str) -> str:
    """Parse a key sequence string and return bytes to send.

    Handles:
    - Named keys (Ctrl+C, Up, Esc, etc.)
    - Literal text (preserved as-is)
    - Newlines (\n -> \r\n for terminal)

    Args:
        input_str: Key sequence string

    Returns:
        Bytes to send to terminal
    """
    result = []
    remaining = input_str

    while remaining:
        # Try to match a named key at the start
        matched = False
        for key_name in sorted(KEY_MAPPINGS.keys(), key=len, reverse=True):
            if remaining.startswith(key_name):
                result.append(KEY_MAPPINGS[key_name])
                remaining = remaining[len(key_name):]
                matched = True
                break

        if not matched:
            # Take one character
            char = remaining[0]
            remaining = remaining[1:]

            # Convert newlines to CRLF for terminal
            if char == "\n":
                result.append("\r\n")
            else:
                result.append(char)

    return "".join(result)
