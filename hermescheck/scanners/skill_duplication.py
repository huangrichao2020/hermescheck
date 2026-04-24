"""Scan for duplicated skill/SOP/runbook artifacts."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

SKILL_FILE_RE = re.compile(r"(?:skill|sop|runbook|playbook|guide|checklist|instruction)", re.IGNORECASE)
SUFFIX_RE = re.compile(r"(?:^|[-_ ])(?:old|new|latest|final|draft|copy|backup|bak|v\d+)(?:$|[-_ ])", re.IGNORECASE)
SCAN_EXTENSIONS = {".md", ".txt", ".py", ".json", ".yaml", ".yml"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "coverage"}


def _should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def _normalize_skill_stem(path: Path) -> str:
    stem = path.stem.lower()
    stem = SUFFIX_RE.sub("-", stem)
    stem = re.sub(r"[^a-z0-9]+", "-", stem).strip("-")
    return stem


def scan_skill_duplication(target: Path) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    skill_files: list[Path] = []

    files = [target] if target.is_file() else sorted(target.rglob("*"))
    for fp in files:
        if not fp.is_file() or _should_skip(fp) or fp.suffix not in SCAN_EXTENSIONS:
            continue
        path_text = "/".join(fp.parts)
        if SKILL_FILE_RE.search(path_text):
            skill_files.append(fp)

    if len(skill_files) < 3:
        return findings

    grouped: dict[str, list[Path]] = {}
    for fp in skill_files:
        grouped.setdefault(_normalize_skill_stem(fp), []).append(fp)

    duplicate_groups = {key: paths for key, paths in grouped.items() if len(paths) >= 2 and key}
    if not duplicate_groups:
        return findings

    evidence_refs: list[str] = []
    for paths in duplicate_groups.values():
        evidence_refs.extend(str(path) for path in paths[:2])

    findings.append(
        {
            "severity": "medium",
            "title": "Duplicated skill / SOP artifacts detected",
            "symptom": (
                f"Found {sum(len(paths) for paths in duplicate_groups.values())} overlapping skill-like files "
                f"across {len(duplicate_groups)} duplicate groups."
            ),
            "user_impact": (
                "Duplicated SOPs and skill files create maintenance drift, make routing less predictable, and force "
                "humans or agents to guess which version is canonical."
            ),
            "source_layer": "skill_system",
            "mechanism": "Grouped skill/SOP/runbook-like files by normalized stem and flagged overlapping groups.",
            "root_cause": "The skill system appears to contain duplicated or version-fragmented artifacts.",
            "evidence_refs": evidence_refs,
            "confidence": 0.75,
            "fix_type": "architecture_change",
            "recommended_fix": (
                "Pick one canonical skill or SOP per task shape. Archive or delete duplicated variants and keep "
                "version history in Git rather than in multiple near-identical files."
            ),
        }
    )
    return findings
