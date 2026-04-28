"""Scan for privileged agent capabilities without enough enterprise controls."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from hermescheck.config import AuditConfig
from hermescheck.scanners.path_filters import should_skip_path

PRIVILEGED_CAPABILITY_RE = re.compile(
    r"(?:subprocess\.run|subprocess\.Popen|os\.system|shell\s*=\s*True|"
    r"\bexec\s*\(|\beval\s*\(|browser_control|playwright|selenium|"
    r"requests\.(?:get|post|put|delete)|httpx\.(?:get|post|put|delete)|"
    r"\bfetch\s*\(|axios\.(?:get|post|put|delete)|write_text\(|write_bytes\(|"
    r"\.unlink\(|os\.remove\(|shutil\.rmtree\()",
    re.IGNORECASE,
)

CONTROL_PATTERNS = {
    "approval": re.compile(
        r"(?:approve|approval|confirm|consent|require_approval|request_approval|"
        r"user_confirm|human_in_the_loop|manual_review)",
        re.IGNORECASE,
    ),
    "sandbox": re.compile(
        r"(?:sandbox|docker|container|isolat|gvisor|nsjail|seccomp|read_only|"
        r"readonly|resource\.setrlimit|timeout\s*=|network_disabled)",
        re.IGNORECASE,
    ),
    "allowlist": re.compile(
        r"(?:allowlist|whitelist|ALLOWED_|SAFE_COMMANDS|allowed_commands|"
        r"allowed_paths|permitted_commands|permitted_paths)",
        re.IGNORECASE,
    ),
}

SCAN_EXTENSIONS = {".py", ".ts", ".js", ".tsx", ".jsx"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "coverage"}


def _should_skip(path: Path) -> bool:
    return should_skip_path(path, SKIP_DIRS)


def scan_excessive_agency(target: Path, config: AuditConfig) -> List[Dict[str, Any]]:
    """Enterprise profile requires at least two of approval/sandbox/allowlist."""

    if not config.profile.enforce_agency_controls:
        return []

    capability_refs: List[str] = []
    control_refs: dict[str, List[str]] = {key: [] for key in CONTROL_PATTERNS}

    files = [target] if target.is_file() else sorted(target.rglob("*"))
    for fp in files:
        if not fp.is_file() or _should_skip(fp) or fp.suffix not in SCAN_EXTENSIONS:
            continue

        try:
            lines = fp.read_text(encoding="utf-8", errors="ignore").splitlines()
        except (OSError, PermissionError):
            continue

        for lineno, line in enumerate(lines, start=1):
            if PRIVILEGED_CAPABILITY_RE.search(line):
                capability_refs.append(f"{fp}:{lineno}")
            for control_name, pattern in CONTROL_PATTERNS.items():
                if pattern.search(line):
                    control_refs[control_name].append(f"{fp}:{lineno}")

    if not capability_refs:
        return []

    present_controls = {name: refs for name, refs in control_refs.items() if refs}
    if len(present_controls) >= config.profile.min_agency_controls:
        return []

    severity = "medium"
    control_summary = ", ".join(sorted(present_controls)) if present_controls else "none"
    evidence_refs = capability_refs[:5]
    for refs in present_controls.values():
        evidence_refs.extend(refs[:2])

    return [
        {
            "severity": severity,
            "title": "Privileged agent capabilities lack enterprise controls",
            "symptom": (
                f"Detected {len(capability_refs)} privileged capability sites, but only "
                f"{len(present_controls)} control categories were found ({control_summary})."
            ),
            "user_impact": (
                "High-agency agents can execute commands, modify files, browse externally, or send data. Static "
                "capability markers should trigger review, but they should not be treated as critical without a "
                "confirmed unsafe dispatch path."
            ),
            "source_layer": "tool_execution",
            "mechanism": (
                "Privileged capability regexes matched, then approval/sandbox/allowlist control "
                "categories were counted across the scanned project."
            ),
            "root_cause": (
                "The project exposes powerful agent capabilities without meeting the minimum "
                "enterprise-production control threshold."
            ),
            "evidence_refs": evidence_refs,
            "confidence": 0.82,
            "fix_type": "architecture_change",
            "recommended_fix": (
                "For enterprise production, require at least two of the three control categories: "
                "approval, sandbox, and allowlist. Approval should gate risky actions, sandbox "
                "should isolate execution, and allowlists should constrain commands or paths. Keep routine runtime "
                "capabilities available where needed; add scoped policy instead of blanket disabling."
            ),
        }
    ]
