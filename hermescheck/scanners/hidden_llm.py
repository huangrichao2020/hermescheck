"""Scan for hidden or secondary LLM calls that may bypass the main agent loop."""

import re
from pathlib import Path
from typing import Any, Dict, List

from hermescheck.scanners.path_filters import should_skip_path

API_LLM_RE = re.compile(
    r"(?:chat(?:\.completions)?\.create|messages\.create|completions\.create|llm\.invoke|"
    r"openai\.chat|anthropic\.messages|vertexai\.predict|"
    r"bedrock.*invoke|model\.generate|completion\.create)\s*\(",
    re.IGNORECASE,
)

SUSPICIOUS_CONTEXT_RE = re.compile(
    r"(?:fallback|repair|second.*pass|re-prompt|retry.*llm|judge.*llm|reflect.*llm)",
    re.IGNORECASE,
)

MAIN_LOOP_RE = re.compile(
    r"(?:agent.*loop|main.*loop|orchestrat|chain.*run|agent.*run|"
    r"agent_executor|react.*loop|tool.*loop|cycle.*run)",
    re.IGNORECASE,
)

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "test", "tests"}
SCAN_EXTENSIONS = {".py", ".ts", ".js"}
PROVIDER_PATH_RE = re.compile(
    r"(?:provider|adapter|client_factory|model_backend|llm_gateway|client|gateway)",
    re.IGNORECASE,
)
PROVIDER_CONTENT_RE = re.compile(r"(?:class\s+\w*Provider|def\s+\w*provider)", re.IGNORECASE)


def _should_skip(path: Path) -> bool:
    return should_skip_path(path, SKIP_DIRS)


def _looks_like_provider_file(path: Path, content: str) -> bool:
    path_text = "/".join(path.parts)
    return bool(PROVIDER_PATH_RE.search(path_text) or PROVIDER_CONTENT_RE.search(content))


def _has_suspicious_context(path: Path, lines: list[str], lineno: int) -> bool:
    if SUSPICIOUS_CONTEXT_RE.search(path.name):
        return True

    start = max(0, lineno - 3)
    end = min(len(lines), lineno + 2)
    context = "\n".join(lines[start:end])
    return bool(SUSPICIOUS_CONTEXT_RE.search(context))


def scan_hidden_llm_calls(target: Path) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    has_main_loop = False
    llm_call_sites: List[tuple[Path, int, str]] = []

    files = [target] if target.is_file() else sorted(target.rglob("*"))

    for fp in files:
        if not fp.is_file() or _should_skip(fp) or fp.suffix not in SCAN_EXTENSIONS:
            continue

        try:
            content = fp.read_text(encoding="utf-8", errors="ignore")
            lines = content.splitlines()
        except (OSError, PermissionError):
            continue

        file_has_main_loop = any(MAIN_LOOP_RE.search(line) for line in lines)
        if file_has_main_loop:
            has_main_loop = True

        is_provider_file = _looks_like_provider_file(fp, content)
        for lineno, line in enumerate(lines, start=1):
            if not API_LLM_RE.search(line):
                continue

            if _has_suspicious_context(fp, lines, lineno):
                llm_call_sites.append((fp, lineno, line.strip()[:120]))
                continue

            if file_has_main_loop or is_provider_file:
                continue

            llm_call_sites.append((fp, lineno, line.strip()[:120]))

    for fp, lineno, snippet in llm_call_sites:
        findings.append(
            {
                "severity": "high",
                "title": "Hidden or secondary LLM call detected",
                "symptom": f"LLM API call found at {fp.name}:{lineno}: {snippet}",
                "user_impact": "Secondary LLM calls may bypass tool restrictions, safety checks, or cost controls defined in the main agent loop.",
                "source_layer": "llm_routing",
                "mechanism": "Regex match for LLM call pattern outside main agent loop file.",
                "root_cause": "Additional LLM invocations exist outside the primary orchestration path, potentially unguarded.",
                "evidence_refs": [f"{fp}:{lineno}"],
                "confidence": 0.8,
                "fix_type": "code_change",
                "recommended_fix": "Consolidate all LLM calls through the main agent loop. If a secondary call is intentional, add explicit documentation, guardrails, and cost tracking.",
            }
        )

    if not has_main_loop and llm_call_sites:
        findings.append(
            {
                "severity": "high",
                "title": "No main agent loop pattern found",
                "symptom": "LLM calls detected but no recognized main loop (agent_loop, main_loop, orchestrator, chain_run) pattern.",
                "user_impact": "Without a clear orchestration loop, LLM calls may be scattered and uncoordinated, making it hard to enforce tool policies or cost limits.",
                "source_layer": "llm_routing",
                "mechanism": "No match for main loop patterns (agent.*loop, main.*loop, orchestrat, chain.*run).",
                "root_cause": "Missing or non-standard agent orchestration structure.",
                "evidence_refs": [f"{fp}:{lineno}" for fp, lineno, _ in llm_call_sites],
                "confidence": 0.7,
                "fix_type": "code_change",
                "recommended_fix": "Implement a clear main agent loop that centralizes all LLM invocations, tool routing, and policy enforcement.",
            }
        )

    return findings
