# backend/core/agentic_runner.py
"""
Two-phase agentic loop:
  Phase "plan"    → single direct LLM call → we save implementation.md ourselves → return content
  Phase "execute" → full tool loop to build everything
"""
import re, logging, os
from typing import Callable, List, Dict

from backend.tools.code_runner import run_python, run_bash
from backend.tools.file_tools   import read_file, write_file, list_dir

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 10

PLAN_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "agent_workspace", "implementation.md")
)
os.makedirs(os.path.dirname(PLAN_PATH), exist_ok=True)

# ─── Tool format docs (for execution phase) ──────────────────────────────────
TOOLS_DOC = """
You have tools. Use ONE per message in this EXACT format:
<tool>TOOL_NAME</tool><input>INPUT_HERE</input>

TOOLS:
- run_python  : Execute Python code. Input = code string.
- run_bash    : Execute shell command.
- read_file   : Read a file. Input = absolute path.
- write_file  : Write a file. Input:
                /absolute/path/to/file.ext
                ---
                file contents
- list_dir    : List directory contents.

ABSOLUTE PATH RULES (CRITICAL):
- ALWAYS use full paths: /Users/abhaypratapsingh/Desktop/myproject/app.py
- ~/Desktop/ expands to /Users/abhaypratapsingh/Desktop/
- NEVER use ./relative/paths
- When done with ALL work, write a final summary with NO tool call.
"""

# ─── Planning prompt (direct call, no tools) ─────────────────────────────────
PLANNING_PROMPT = """You are a world-class software architect. Your task is to create a COMPREHENSIVE implementation plan.

Think deeply like a senior engineer — analyze EVERY aspect before writing:

1. PROJECT SCOPE: All features a real version would have
2. TECH STACK: Right stack for the job (not just the simplest)
3. ARCHITECTURE: How all pieces connect
4. FILE STRUCTURE: Every single file to be created
5. UI/UX DESIGN: Colors, layout, pages, responsiveness
6. DATA MODELS: Schemas, structures
7. DEPENDENCIES: Every package needed
8. BUILD ORDER: Logical steps to implement

EXAMPLES OF DEPTH REQUIRED:
- "Zomato clone" → Full Flask backend + 5 HTML pages + SQLite + red/orange theme + search + cart + orders
- "Snake game" → Pygame GUI + score + levels + high-score saving + animations
- "Chat app" → WebSocket server + React frontend + message history + rooms

Output ONLY the implementation plan in this markdown structure:

# Implementation Plan: [Project Name]

## 🎯 Project Overview
[What this builds, target user, key value]

## ✨ Full Feature List
1. Feature one
2. Feature two
...

## 🛠️ Tech Stack
| Layer | Technology | Reason |
|-------|-----------|--------|
| Frontend | ... | ... |
...

## 📁 Complete File Structure
```
project-root/
├── app.py              — Flask app entry point
├── static/
│   ├── css/
│   │   └── style.css   — Main stylesheet
│   └── js/
│       └── script.js   — Frontend logic
├── templates/
│   ├── index.html      — Home page
│   └── restaurant.html — Restaurant detail
└── ...
```

## 🎨 UI/UX Design
- **Color scheme**: primary #..., accent #...
- **Typography**: Font choices
- **Key pages**: What each page contains
- **Responsive**: Mobile breakpoints

## 🗃️ Data Models
[Database schema or data structures]

## 📦 Dependencies
```
pip install flask flask-sqlalchemy ...
```

## 🚀 Build Steps (in order)
1. Step one
2. Step two
...

## ⏱️ Estimated Complexity
[Low / Medium / High] — [reason]
"""

# ─── Execution prompt ─────────────────────────────────────────────────────────
EXECUTION_PROMPT = """
EXECUTION PHASE — Build the ENTIRE project now.

The approved plan is provided. Execute ALL steps:
- Create EVERY file from the file structure
- Use run_bash to install dependencies first
- Use run_bash to create directory structure
- Build each file completely (no placeholders, no TODOs)
- Test the code if possible
- Use ABSOLUTE paths always

When every file is built, give a final summary showing:
- All files created with their paths
- How to run the project
"""

# ─── Tool dispatch ────────────────────────────────────────────────────────────
TOOL_DISPATCH = {
    "run_python": run_python,
    "run_bash":   run_bash,
    "read_file":  read_file,
    "list_dir":   list_dir,
    "write_file": write_file,
}


def _extract_tool_call(text: str):
    m = re.search(r"<tool>(.*?)</tool>\s*<input>(.*?)</input>", text, re.DOTALL)
    return (m.group(1).strip(), m.group(2)) if m else None


def _run_tool_loop(messages, call_model, max_iter=MAX_ITERATIONS):
    steps = []
    for i in range(max_iter):
        logger.info(f"  Tool loop iter {i+1}/{max_iter}")
        response = call_model(messages)
        logger.info(f"  Response[:250]: {response[:250]}")

        tool_call = _extract_tool_call(response)
        if tool_call is None:
            steps.append({"type": "answer", "content": response})
            break

        name, inp = tool_call
        steps.append({"type": "tool", "tool": name, "content": inp})

        fn = TOOL_DISPATCH.get(name)
        result = fn(inp) if fn else f"ERROR: unknown tool '{name}'"
        logger.info(f"  Tool '{name}' result[:200]: {result[:200]}")
        steps.append({"type": "result", "tool": name, "content": result})

        messages.append({"role": "assistant", "content": response})
        messages.append({"role": "user",      "content": f"<tool_result>{result}</tool_result>\nContinue."})
    else:
        steps.append({"type": "answer", "content": "_(Reached max iterations — work may be incomplete)_"})

    return steps


# ─── Public API ───────────────────────────────────────────────────────────────
def run_planning_phase(prompt: str, system_prompt: str, call_model: Callable):
    """
    Phase 1: Single direct LLM call — returns plan as text.
    We save it to implementation.md ourselves (no tool loop = no chance of model going rogue).
    Returns: (steps, True, plan_content_str)
    """
    messages = [
        {"role": "system", "content": PLANNING_PROMPT},
        {"role": "user",   "content": f"Create a comprehensive implementation plan for: {prompt}"},
    ]

    logger.info("Planning phase: calling model for plan...")
    plan_content = call_model(messages)
    logger.info(f"Plan received ({len(plan_content)} chars)")

    # Save to implementation.md
    try:
        with open(PLAN_PATH, "w") as f:
            f.write(plan_content)
        save_result = f"✓ File written: {PLAN_PATH}"
    except Exception as e:
        save_result = f"ERROR saving plan: {e}"
        logger.error(save_result)

    steps = [
        {"type": "tool",   "tool": "write_file", "content": PLAN_PATH},
        {"type": "result", "tool": "write_file",  "content": save_result},
    ]

    return steps, True, plan_content


def run_execution_phase(prompt: str, system_prompt: str, call_model: Callable):
    """
    Phase 2: Full tool loop to build everything from the approved plan.
    """
    plan_content = ""
    if os.path.exists(PLAN_PATH):
        try:
            with open(PLAN_PATH) as f:
                plan_content = f.read()
        except Exception:
            pass

    full_system = system_prompt + "\n\n" + TOOLS_DOC + "\n\n" + EXECUTION_PROMPT
    messages = [
        {"role": "system",    "content": full_system},
        {"role": "user",      "content": f"Original task: {prompt}"},
        {"role": "assistant", "content": f"Approved implementation plan:\n\n{plan_content}"},
        {"role": "user",      "content": "Execute the plan NOW. Build every file. Start with dependencies and directory setup."},
    ]
    return _run_tool_loop(messages, call_model)


def run_agent_loop(prompt: str, system_prompt: str, call_model: Callable):
    """Unrestricted loop for non-developer agents."""
    full_system = system_prompt + "\n\n" + TOOLS_DOC
    messages = [
        {"role": "system", "content": full_system},
        {"role": "user",   "content": prompt},
    ]
    return _run_tool_loop(messages, call_model)
