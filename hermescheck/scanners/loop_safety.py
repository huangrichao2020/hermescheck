"""Scan for agent loops, tool loops, and scheduled jobs without loop safety controls."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from hermescheck.scanners.path_filters import iter_source_files, should_skip_path

SCAN_EXTENSIONS = {".py", ".ts", ".js", ".tsx", ".jsx", ".md", ".yaml", ".yml", ".toml", ".json"}
SKIP_DIRS = {".git", ".github", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "coverage"}
MAX_FILE_BYTES = 250_000

AGENT_LOOP_RE = re.compile(
    r"\b(?:agent[_ -]?loop|main[_ -]?loop|react[_ -]?loop|tool[_ -]?loop|while\s+True|for\s*\(\s*;;|"
    r"while\s*\(\s*true\s*\)|loop_detector|run_forever|always[-_ ]?on|daemon)\b",
    re.IGNORECASE,
)
TOOL_REPEAT_RE = re.compile(
    r"\b(?:tool_call|toolCall|tool_use|function_call|execute[_ -]?shell|shell command|subprocess|"
    r"delegate_task|retry|fallback|provider fallback)\b",
    re.IGNORECASE,
)
SCHEDULED_WORK_RE = re.compile(
    r"\b(?:cron|scheduler|heartbeat|interval|setInterval|schedule\.|task[_ -]?queue|job[_ -]?queue|"
    r"worker[_ -]?queue|workerQueue|background[_ -]?task|backgroundTask|daemon|watchdog)\b",
    re.IGNORECASE,
)
LOOP_GUARD_RE = re.compile(
    r"\b(?:max[_ -]?(?:steps|turns|iterations|loops|retries)|iteration[_ -]?limit|tool[_ -]?call[_ -]?limit|"
    r"loop[_ -]?detector|repetition[_ -]?detector|same[_ -]?args|args[_ -]?hash|dedupe|circuit[_ -]?breaker|"
    r"timeout|deadline|retry[_ -]?budget|backoff|ask[_ -]?to[_ -]?continue|confirm[_ -]?continue|"
    r"cancel|cancellation|abort|stop[_ -]?signal)\b",
    re.IGNORECASE,
)
TOOL_PATH_RE = re.compile(
    r"\b(?:def\s+[_a-zA-Z0-9]*(?:invoke|dispatch|execute|run)[_a-zA-Z0-9]*(?:tool|function|command)|"
    r"async\s+def\s+[_a-zA-Z0-9]*(?:invoke|dispatch|execute|run)[_a-zA-Z0-9]*(?:tool|function|command)|"
    r"(?:invoke|dispatch|execute|run)[_a-zA-Z0-9]*(?:tool|function|command)\s*\(|"
    r"tool_call\s*\(|function_call\s*\(|subprocess\.(?:run|Popen)|os\.system\s*\()\b",
    re.IGNORECASE,
)
LOOP_OBSERVER_RE = re.compile(
    r"\b(?:loop[_ -]?detector|repetition[_ -]?detector|record[_ -]?tool|record\s*\(|same[_ -]?args|"
    r"args[_ -]?hash|max[_ -]?(?:steps|turns|iterations|loops|retries)|retry[_ -]?budget|timeout|deadline|"
    r"circuit[_ -]?breaker|ask[_ -]?to[_ -]?continue)\b",
    re.IGNORECASE,
)


def _should_skip(path: Path) -> bool:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return True
    except OSError:
        return True
    return should_skip_path(path, SKIP_DIRS)


def _collect_refs(target: Path) -> dict[str, list[str]]:
    refs = {
        "agent_loop": [],
        "tool_repeat": [],
        "scheduled_work": [],
        "loop_guard": [],
        "tool_path": [],
        "loop_observer": [],
        "unguarded_tool_path": [],
    }
    files = list(iter_source_files(target))
    for fp in files:
        if not fp.is_file() or _should_skip(fp) or fp.suffix not in SCAN_EXTENSIONS:
            continue
        try:
            lines = fp.read_text(encoding="utf-8", errors="ignore").splitlines()
        except (OSError, PermissionError):
            continue
        for lineno, line in enumerate(lines, start=1):
            if AGENT_LOOP_RE.search(line):
                refs["agent_loop"].append(f"{fp}:{lineno}")
            if TOOL_REPEAT_RE.search(line):
                refs["tool_repeat"].append(f"{fp}:{lineno}")
            if SCHEDULED_WORK_RE.search(line):
                refs["scheduled_work"].append(f"{fp}:{lineno}")
            if LOOP_GUARD_RE.search(line):
                refs["loop_guard"].append(f"{fp}:{lineno}")
            if TOOL_PATH_RE.search(line):
                refs["tool_path"].append(f"{fp}:{lineno}")
            if LOOP_OBSERVER_RE.search(line):
                refs["loop_observer"].append(f"{fp}:{lineno}")

        observer_lines = [lineno for lineno, line in enumerate(lines, start=1) if LOOP_OBSERVER_RE.search(line)]
        for lineno, line in enumerate(lines, start=1):
            if TOOL_PATH_RE.search(line) and not any(
                abs(lineno - guard_lineno) <= 3 for guard_lineno in observer_lines
            ):
                refs["unguarded_tool_path"].append(f"{fp}:{lineno}")
    return refs


def _evidence(refs: dict[str, list[str]], *keys: str, limit: int = 8) -> list[str]:
    evidence_refs: list[str] = []
    seen: set[str] = set()
    for key in keys:
        for ref in refs.get(key, []):
            if ref not in seen:
                evidence_refs.append(ref)
                seen.add(ref)
            if len(evidence_refs) >= limit:
                return evidence_refs
    return evidence_refs


def scan_loop_safety(target: Path) -> List[Dict[str, Any]]:
    refs = _collect_refs(target)
    findings: List[Dict[str, Any]] = []

    loop_pressure = len(refs["agent_loop"]) + len(refs["tool_repeat"])
    guard_count = len(refs["loop_guard"])
    if loop_pressure >= 4 and guard_count < 2:
        findings.append(
            {
                "severity": "high",
                "title": "Agent/tool loop lacks loop safety budget",
                "symptom": (
                    f"Found {len(refs['agent_loop'])} agent-loop markers and "
                    f"{len(refs['tool_repeat'])} repeated tool/retry markers, but only {guard_count} loop guard markers."
                ),
                "user_impact": (
                    "A 24/7 or autonomous agent can repeat the same tool call, retry path, or repair loop until it "
                    "burns tokens, blocks the user, or mutates state repeatedly."
                ),
                "source_layer": "loop_safety",
                "mechanism": "Repository scan for agent loops and repeated tool calls versus iteration limits and loop guards.",
                "root_cause": "The runtime exposes repeated agent/tool execution without a visible loop detector or budget.",
                "evidence_refs": _evidence(refs, "agent_loop", "tool_repeat", "loop_guard"),
                "confidence": 0.72,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Add a loop safety budget: max turns/iterations, repeated tool-call signature detection, timeout or "
                    "deadline controls, retry budget/backoff, and an ask-to-continue path when a loop looks stuck."
                ),
            }
        )

    scheduled_pressure = len(refs["scheduled_work"])
    if scheduled_pressure >= 3 and guard_count < 2:
        findings.append(
            {
                "severity": "medium",
                "title": "Scheduled agent work lacks stuck-job controls",
                "symptom": f"Found {scheduled_pressure} scheduler/cron/daemon markers but only {guard_count} loop guard markers.",
                "user_impact": (
                    "Background jobs and cron-style agents can keep retrying after failure, consuming tokens or "
                    "resources without a user-visible stop condition."
                ),
                "source_layer": "loop_safety",
                "mechanism": "Repository scan for scheduled/daemon work versus timeout, backoff, cancellation, and circuit breakers.",
                "root_cause": "The project appears to run background work, but the stuck-job policy is not explicit.",
                "evidence_refs": _evidence(refs, "scheduled_work", "loop_guard"),
                "confidence": 0.68,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Give scheduled jobs an execution contract: per-run timeout, retry budget, exponential backoff, "
                    "circuit breaker after repeated failures, cancellation, and visible stuck-job logs."
                ),
            }
        )

    if len(refs["tool_path"]) >= 2 and refs["loop_observer"] and refs["unguarded_tool_path"]:
        findings.append(
            {
                "severity": "high",
                "title": "Loop detector does not observe all tool-call paths",
                "symptom": (
                    f"Detected {len(refs['tool_path'])} tool/function dispatch sites and loop-safety signals, but "
                    f"{len(refs['unguarded_tool_path'])} dispatch sites were not near loop observation or budget checks."
                ),
                "user_impact": (
                    "A runtime can detect loops in one execution mode while sequential, concurrent, scheduled, or "
                    "delegated paths keep repeating tool calls without warning, reset, or budget enforcement."
                ),
                "source_layer": "loop_safety",
                "mechanism": "Line-proximity scan for tool dispatch sites versus loop detector record/budget calls.",
                "root_cause": "Loop detection appears to be attached to a partial execution path rather than the common tool boundary.",
                "evidence_refs": _evidence(refs, "unguarded_tool_path", "loop_observer", "tool_path"),
                "confidence": 0.66,
                "fix_type": "code_change",
                "recommended_fix": (
                    "Record every tool call at the shared dispatch boundary, including tool name, normalized arguments, "
                    "result/error status, and reset scope; apply the same loop budget across sequential, concurrent, "
                    "scheduled, and delegated paths."
                ),
            }
        )

    return findings
