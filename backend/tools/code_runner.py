# backend/tools/code_runner.py
"""Execute Python and Bash code snippets and return output."""
import subprocess, tempfile, os, textwrap, logging

logger = logging.getLogger(__name__)
MAX_OUTPUT_CHARS = 3000


def run_python(code: str, timeout: int = 20) -> str:
    """Execute Python code and return stdout+stderr."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(textwrap.dedent(code))
        path = f.name
    try:
        result = subprocess.run(
            ["python3", path],
            capture_output=True, text=True, timeout=timeout
        )
        out = (result.stdout + result.stderr).strip()
        return out[:MAX_OUTPUT_CHARS] if out else "(no output)"
    except subprocess.TimeoutExpired:
        return "ERROR: Python execution timed out"
    except Exception as e:
        return f"ERROR: {e}"
    finally:
        try: os.unlink(path)
        except: pass


def run_bash(command: str, timeout: int = 30) -> str:
    """
    Execute a bash command and return output.
    Uses /bin/bash -c so heredoc syntax works correctly:
      cat > /path/file << 'HEREDOC'
      content
      HEREDOC
    """
    try:
        result = subprocess.run(
            ["/bin/bash", "-c", command],   # explicit bash for heredoc support
            capture_output=True, text=True, timeout=timeout,
            cwd=os.path.expanduser("~")     # start from home, not backend dir
        )
        out = (result.stdout + result.stderr).strip()
        if not out:
            # Return what was executed so user can see progress
            first_line = command.strip().split('\n')[0][:80]
            return f"✓ Done: {first_line}"
        return out[:MAX_OUTPUT_CHARS]
    except subprocess.TimeoutExpired:
        return "ERROR: command timed out (30s)"
    except Exception as e:
        return f"ERROR: {e}"
