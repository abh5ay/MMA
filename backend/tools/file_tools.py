# backend/tools/file_tools.py
"""Read, write, and list files — writes respect absolute paths."""
import os, logging

logger = logging.getLogger(__name__)
MAX_READ_CHARS = 8000

# Fallback directory when no path is given
SANDBOX_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "agent_workspace")
)
os.makedirs(SANDBOX_DIR, exist_ok=True)


def read_file(path: str) -> str:
    try:
        with open(path.strip(), "r", errors="replace") as f:
            content = f.read(MAX_READ_CHARS)
        if len(content) == MAX_READ_CHARS:
            content += "\n...(truncated)"
        return content
    except Exception as e:
        return f"ERROR reading file: {e}"


def write_file(path_and_content: str) -> str:
    """
    Write a file.
    Format:  /full/path/to/file.py\n---\nfile contents here
    If only a filename (no slashes), writes to the agent_workspace sandbox.
    Supports absolute paths on the user's machine (e.g. ~/Desktop/foo.py).
    """
    if "\n---\n" in path_and_content:
        raw_path, content = path_and_content.split("\n---\n", 1)
        raw_path = raw_path.strip()
    else:
        raw_path = "output.txt"
        content  = path_and_content

    # Expand ~ to the real home dir
    raw_path = os.path.expanduser(raw_path)

    # Use as-is if absolute, otherwise put in sandbox
    if os.path.isabs(raw_path):
        dest = raw_path
    else:
        dest = os.path.join(SANDBOX_DIR, raw_path)

    # Create parent directories if needed
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)

    try:
        with open(dest, "w") as f:
            f.write(content)
        return f"✓ File written: {dest}"
    except Exception as e:
        return f"ERROR writing file: {e}"


def list_dir(path: str = ".") -> str:
    try:
        path = os.path.expanduser(path.strip() or ".")
        entries = os.listdir(path)
        return "\n".join(sorted(entries)) or "(empty)"
    except Exception as e:
        return f"ERROR listing directory: {e}"
