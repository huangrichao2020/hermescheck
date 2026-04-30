"""Scan for tool-calling requirements in prompts and whether code enforces them."""

import re
from pathlib import Path
from typing import Any, Dict, List

from hermescheck.scanners.path_filters import should_skip_path

# Precompiled patterns
PROMPT_TOOL_RE = re.compile(
    r"(?:must use tool|required call|always use|tool is required|"
    r"required to call|you must call|mandatory tool use)",
    re.IGNORECASE,
)

TOOL_CALL_RE = re.compile(
    r"(?:tool_call|toolCall|tool_use|function_call|tool_choice|use_tool)",
    re.IGNORECASE,
)

VALIDATION_RE = re.compile(
    r"(?:assert |if not |raise |\.validate|\.check|verify|guard|enforce|sanity_check)",
    re.IGNORECASE,
)

SCAN_PROMPT_EXT = {".md", ".txt"}
SCAN_CODE_EXT = {".py", ".ts", ".js"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}


def _should_skip(path: Path) -> bool:
    return should_skip_path(path, SKIP_DIRS)


def _scan_prompts(target: Path) -> List[Path]:
    """Return files that contain tool-use requirements in prompts."""
    result = []
    files = [target] if target.is_file() else sorted(target.rglob("*"))
    for fp in files:
        if not fp.is_file() or _should_skip(fp) or fp.suffix not in SCAN_PROMPT_EXT:
            continue
        try:
            content = fp.read_text(encoding="utf-8", errors="ignore")
        except (OSError, PermissionError):
            continue
        if PROMPT_TOOL_RE.search(content):
            result.append(fp)
    return result


def _scan_code_enforcement(target: Path) -> tuple[bool, List[Path]]:
    """Return (has_validation, files_with_tool_calls)."""
    tool_call_files: List[Path] = []
    has_validation = False
    files = [target] if target.is_file() else sorted(target.rglob("*"))
    for fp in files:
        if not fp.is_file() or _should_skip(fp) or fp.suffix not in SCAN_CODE_EXT:
            continue
        try:
            content = fp.read_text(encoding="utf-8", errors="ignore")
        except (OSError, PermissionError):
            continue
        if TOOL_CALL_RE.search(content):
            tool_call_files.append(fp)
            if VALIDATION_RE.search(content):
                has_validation = True
    return has_validation, tool_call_files


def scan_tool_enforcement(target: Path) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []

    prompt_files = _scan_prompts(target)
    has_validation, tool_call_files = _scan_code_enforcement(target)

    if prompt_files and not tool_call_files:
        # Prompts require tools but no tool-calling code found
        for pf in prompt_files:
            findings.append(
                {
                    "severity": "medium",
                    "title": "Tool calling required by prompt but not implemented in code",
                    "symptom": f"Prompt file {pf.name} specifies tool requirements but no tool-calling code exists.",
                    "user_impact": (
                        "The agent may treat mandatory tool-use wording as advisory unless the requirement is "
                        "implemented in code."
                    ),
                    "source_layer": "tool_enforcement",
                    "mechanism": "Heuristic scan for prompt-level tool requirements without matching tool-call code.",
                    "root_cause": "The project may be using prompt guidance where the docs imply a hard tool contract.",
                    "evidence_refs": [str(pf) for pf in prompt_files],
                    "confidence": 0.62,
                    "fix_type": "code_change",
                    "recommended_fix": (
                        "Ask the target agent to classify each tool instruction as advisory or required. Keep advisory "
                        "instructions in prompts; add validation only for required tools whose absence would change the "
                        "answer's truth or safety."
                    ),
                }
            )

    elif prompt_files and not has_validation:
        # Tool calling code exists but no validation
        findings.append(
            {
                "severity": "medium",
                "title": "Tool calls lack validation or enforcement",
                "symptom": "Prompts require specific tool usage but code does not validate tool call results or schema.",
                "user_impact": (
                    "Unchecked tool calls can return malformed data or fail silently, but prompt-only flows may be "
                    "acceptable while the project is still personal or exploratory."
                ),
                "source_layer": "tool_enforcement",
                "mechanism": "Heuristic scan for tool-calling code without nearby validation markers.",
                "root_cause": "The project has not made clear which tool results need hard validation versus human review.",
                "evidence_refs": [str(f) for f in prompt_files + tool_call_files],
                "confidence": 0.6,
                "fix_type": "code_change",
                "recommended_fix": (
                    "Ask the target agent to name the tool result fields that must be trusted by later steps. Add small "
                    "schema checks only for those fields, and document tolerated best-effort tool failures."
                ),
            }
        )

    return findings
