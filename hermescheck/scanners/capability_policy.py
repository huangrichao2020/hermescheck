"""Scan for high-agency tool capabilities without a clear permission policy."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from hermescheck.scanners.path_filters import iter_source_files, should_skip_path

SCAN_EXTENSIONS = {".py", ".ts", ".js", ".tsx", ".jsx", ".md", ".yaml", ".yml", ".toml", ".json"}
SKIP_DIRS = {".git", ".github", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "coverage"}
MAX_FILE_BYTES = 250_000

AGENT_CONTEXT_RE = re.compile(
    r"\b(?:agent|assistant|tool_call|tool use|function_call|planner|scheduler|autonomous|daemon|"
    r"always[-_ ]?on|human[-_ ]?in[-_ ]?the[-_ ]?loop)\b",
    re.IGNORECASE,
)
POWERFUL_CAPABILITY_RE = re.compile(
    r"(?:subprocess\.(?:run|Popen)|os\.system|shell\s*=\s*True|\bexec\s*\(|\beval\s*\(|"
    r"write_text\(|write_bytes\(|\.unlink\(|os\.remove\(|shutil\.rmtree\(|"
    r"requests\.(?:get|post|put|delete)|httpx\.(?:get|post|put|delete)|\bfetch\s*\(|axios\."
    r"|git\s+push|npm\s+publish|pip\s+install|docker\s+|kubectl\s+|browser_control|playwright|selenium)",
    re.IGNORECASE,
)
POLICY_PATTERNS = {
    "blocklist": re.compile(
        r"\b(?:blocklist|denylist|blacklist|forbidden|blocked_commands|dangerous_commands)\b", re.IGNORECASE
    ),
    "allowlist": re.compile(
        r"\b(?:allowlist|whitelist|auto[-_ ]?approved|safe_commands|allowed_commands|allowed_paths|permitted_paths)\b",
        re.IGNORECASE,
    ),
    "approval": re.compile(
        r"\b(?:needs[_ -]?approval|require[_ -]?approval|request[_ -]?approval|confirm|consent|human[_ -]?approval|"
        r"ask[_ -]?to[_ -]?continue|manual_review)\b",
        re.IGNORECASE,
    ),
    "scope": re.compile(
        r"\b(?:read[_ -]?scope|write[_ -]?scope|path[_ -]?scope|temp[_ -]?scope|workspace[_ -]?scope|"
        r"permission matrix|capability table|capabilities|sandbox)\b",
        re.IGNORECASE,
    ),
}
TOOL_DISPATCH_RE = re.compile(
    r"\b(?:def\s+[_a-zA-Z0-9]*(?:invoke|dispatch|execute|run)[_a-zA-Z0-9]*(?:tool|function|command)|"
    r"async\s+def\s+[_a-zA-Z0-9]*(?:invoke|dispatch|execute|run)[_a-zA-Z0-9]*(?:tool|function|command)|"
    r"(?:invoke|dispatch|execute|run)[_a-zA-Z0-9]*(?:tool|function|command)\s*\(|"
    r"tool_call\s*\(|function_call\s*\(|subprocess\.(?:run|Popen)|os\.system\s*\()\b",
    re.IGNORECASE,
)
PERMISSION_ENFORCEMENT_RE = re.compile(
    r"\b(?:check[_ -]?permission|PermissionEngine|permission_engine|is_allowed|is_blocked|deny|denied|"
    r"require[_ -]?approval|needs[_ -]?approval|allowed_commands|blocked_commands|blocklist|allowlist|"
    r"capability[_ -]?check|policy\.check)\b",
    re.IGNORECASE,
)


def _should_skip(path: Path) -> bool:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return True
    except OSError:
        return True
    return should_skip_path(path, SKIP_DIRS)


def _nearby(ref_lineno: int, guard_lines: list[int], window: int = 3) -> bool:
    return any(abs(ref_lineno - guard_lineno) <= window for guard_lineno in guard_lines)


def _collect_refs(target: Path) -> tuple[list[str], list[str], dict[str, list[str]], list[str], list[str], list[str]]:
    agent_refs: list[str] = []
    capability_refs: list[str] = []
    policy_refs: dict[str, list[str]] = {key: [] for key in POLICY_PATTERNS}
    dispatch_refs: list[str] = []
    enforcement_refs: list[str] = []
    unguarded_dispatch_refs: list[str] = []
    files = list(iter_source_files(target))
    for fp in files:
        if not fp.is_file() or _should_skip(fp) or fp.suffix not in SCAN_EXTENSIONS:
            continue
        try:
            lines = fp.read_text(encoding="utf-8", errors="ignore").splitlines()
        except (OSError, PermissionError):
            continue
        for lineno, line in enumerate(lines, start=1):
            ref = f"{fp}:{lineno}"
            if AGENT_CONTEXT_RE.search(line):
                agent_refs.append(ref)
            if POWERFUL_CAPABILITY_RE.search(line):
                capability_refs.append(ref)
            for name, pattern in POLICY_PATTERNS.items():
                if pattern.search(line):
                    policy_refs[name].append(ref)
            if TOOL_DISPATCH_RE.search(line):
                dispatch_refs.append(ref)
            if PERMISSION_ENFORCEMENT_RE.search(line):
                enforcement_refs.append(ref)

        guard_lines = [lineno for lineno, line in enumerate(lines, start=1) if PERMISSION_ENFORCEMENT_RE.search(line)]
        for lineno, line in enumerate(lines, start=1):
            if TOOL_DISPATCH_RE.search(line) and not _nearby(lineno, guard_lines):
                unguarded_dispatch_refs.append(f"{fp}:{lineno}")

    return agent_refs, capability_refs, policy_refs, dispatch_refs, enforcement_refs, unguarded_dispatch_refs


def scan_capability_policy(target: Path) -> List[Dict[str, Any]]:
    agent_refs, capability_refs, policy_refs, dispatch_refs, enforcement_refs, unguarded_dispatch_refs = _collect_refs(
        target
    )
    findings: List[Dict[str, Any]] = []

    present = {name: refs for name, refs in policy_refs.items() if refs}
    if len(agent_refs) >= 2 and len(capability_refs) >= 3 and len(present) < 3:
        evidence_refs = capability_refs[:5]
        for refs in present.values():
            evidence_refs.extend(refs[:2])

        policy_summary = ", ".join(sorted(present)) if present else "none"
        findings.append(
            {
                "severity": "high" if not present else "medium",
                "title": "High-agency tools lack layered permission policy",
                "symptom": (
                    f"Detected {len(capability_refs)} powerful tool/capability sites in an agent context, but only "
                    f"{len(present)} permission policy categories were visible ({policy_summary})."
                ),
                "user_impact": (
                    "A local or always-on agent can execute commands, write files, browse, publish, or delete state without "
                    "a predictable policy for what is blocked, auto-approved, approval-gated, or scoped to safe paths."
                ),
                "source_layer": "capability_policy",
                "mechanism": "Repository scan for high-agency capabilities versus blocklist, allowlist, approval, and scope policy signals.",
                "root_cause": "Powerful tool access appears to be exposed before the permission model is explicit and layered.",
                "evidence_refs": evidence_refs[:9],
                "confidence": 0.74,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Define a layered permission policy: deny/block list for irreversible commands, auto-approved safe "
                    "commands, needs-approval actions, and read/write/path scopes. Enforce it in code rather than only "
                    "describing it in prompts."
                ),
            }
        )

    if len(dispatch_refs) >= 2 and enforcement_refs and unguarded_dispatch_refs:
        findings.append(
            {
                "severity": "high",
                "title": "Permission policy is not enforced on all dispatch paths",
                "symptom": (
                    f"Detected {len(dispatch_refs)} tool/command dispatch sites and permission enforcement signals, "
                    f"but {len(unguarded_dispatch_refs)} dispatch sites were not near a permission check."
                ),
                "user_impact": (
                    "A runtime can look permission-hardened while sequential, concurrent, scheduled, or delegated tool "
                    "paths bypass the policy and execute high-agency actions unchecked."
                ),
                "source_layer": "capability_policy",
                "mechanism": "Line-proximity scan for tool dispatch sites versus nearby permission enforcement calls.",
                "root_cause": "Permission checks appear to be attached to some dispatch paths instead of the common tool boundary.",
                "evidence_refs": (unguarded_dispatch_refs + enforcement_refs + dispatch_refs)[:9],
                "confidence": 0.66,
                "fix_type": "code_change",
                "recommended_fix": (
                    "Move permission enforcement to the shared tool-dispatch boundary, or add equivalent checks to "
                    "every sequential, concurrent, scheduled, and delegated execution path before tool invocation."
                ),
            }
        )

    return findings
