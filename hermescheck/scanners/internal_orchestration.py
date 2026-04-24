"""Scan for orchestration sprawl and coordination overhead."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from hermescheck.scanners.path_filters import should_skip_path

SCAN_EXTENSIONS = {".py", ".ts", ".js", ".tsx", ".jsx", ".md", ".yaml", ".yml", ".toml"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "coverage"}

ORCHESTRATION_PATTERNS = {
    "planning": re.compile(r"(?:^|[^a-z])plan(?:ner|ning|_task|_step)?", re.IGNORECASE),
    "routing": re.compile(r"(?:route|router|dispatch|selector|handoff)", re.IGNORECASE),
    "delegation": re.compile(r"(?:subagent|worker|delegate|swarm|team|multi[_ -]?agent)", re.IGNORECASE),
    "scheduling": re.compile(r"(?:schedule|scheduler|cron|heartbeat|timer)", re.IGNORECASE),
    "recovery": re.compile(r"(?:retry|fallback|repair|reflect|judge|critic)", re.IGNORECASE),
}


def _should_skip(path: Path) -> bool:
    return should_skip_path(path, SKIP_DIRS)


def scan_internal_orchestration(target: Path) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    matched_categories: dict[str, list[str]] = {key: [] for key in ORCHESTRATION_PATTERNS}

    files = [target] if target.is_file() else sorted(target.rglob("*"))
    for fp in files:
        if not fp.is_file() or _should_skip(fp) or fp.suffix not in SCAN_EXTENSIONS:
            continue

        try:
            lines = fp.read_text(encoding="utf-8", errors="ignore").splitlines()
        except (OSError, PermissionError):
            continue

        for lineno, line in enumerate(lines, start=1):
            for category, pattern in ORCHESTRATION_PATTERNS.items():
                if pattern.search(line):
                    matched_categories[category].append(f"{fp}:{lineno}")

    present_categories = {category: refs for category, refs in matched_categories.items() if refs}
    total_refs = sum(len(refs) for refs in present_categories.values())
    if len(present_categories) < 3 or total_refs < 5:
        return findings

    severity = "high" if len(present_categories) >= 4 or total_refs >= 10 else "medium"
    category_summary = ", ".join(sorted(present_categories))
    evidence_refs: list[str] = []
    for refs in present_categories.values():
        evidence_refs.extend(refs[:2])

    findings.append(
        {
            "severity": severity,
            "title": "Internal orchestration sprawl detected",
            "symptom": (
                f"Found {total_refs} orchestration markers across {len(present_categories)} coordination categories "
                f"({category_summary})."
            ),
            "user_impact": (
                "Too many planning, routing, delegation, scheduling, and recovery layers can make the agent harder to "
                "debug, slower to reason about, and more likely to hide internal contradictions."
            ),
            "source_layer": "orchestration",
            "mechanism": "Repository-wide scan for planner/router/subagent/scheduler/fallback style orchestration markers.",
            "root_cause": "The agent runtime appears to coordinate work through many overlapping orchestration layers.",
            "evidence_refs": evidence_refs,
            "confidence": 0.72,
            "fix_type": "architecture_change",
            "recommended_fix": (
                "Collapse overlapping coordination layers where possible. Keep one clear main loop, minimize hidden "
                "fallback paths, and document which module owns planning, routing, and retries."
            ),
        }
    )
    return findings
