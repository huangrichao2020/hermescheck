"""Scan for memory freshness confusion and overlapping memory surfaces."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

MEMORY_FILE_RE = re.compile(
    r"(?:memory|checkpoint|archive|summary|history|session|state|snapshot|insight)",
    re.IGNORECASE,
)
GENERATION_SUFFIX_RE = re.compile(
    r"(?:^|[-_ ])(?:old|new|latest|final|draft|copy|backup|bak|v\d+)(?:$|[-_ ])", re.IGNORECASE
)
SCAN_EXTENSIONS = {".py", ".ts", ".js", ".json", ".md", ".txt", ".yaml", ".yml", ".toml"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "coverage"}


def _should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def _normalize_memory_stem(path: Path) -> str:
    stem = path.stem.lower()
    stem = GENERATION_SUFFIX_RE.sub("-", stem)
    stem = re.sub(r"[^a-z0-9]+", "-", stem).strip("-")
    return stem


def scan_memory_freshness(target: Path) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    memory_files: list[Path] = []
    categories_present: set[str] = set()

    files = [target] if target.is_file() else sorted(target.rglob("*"))
    for fp in files:
        if not fp.is_file() or _should_skip(fp) or fp.suffix not in SCAN_EXTENSIONS:
            continue
        path_text = "/".join(fp.parts)
        if MEMORY_FILE_RE.search(path_text):
            memory_files.append(fp)
            for category in (
                "memory",
                "checkpoint",
                "archive",
                "summary",
                "history",
                "session",
                "state",
                "snapshot",
                "insight",
            ):
                if category in path_text.lower():
                    categories_present.add(category)

    if len(memory_files) < 3:
        return findings

    grouped: dict[str, list[Path]] = {}
    for fp in memory_files:
        grouped.setdefault(_normalize_memory_stem(fp), []).append(fp)

    duplicate_groups = {key: paths for key, paths in grouped.items() if len(paths) >= 2 and key}
    if len(categories_present) < 3 and not duplicate_groups:
        return findings

    evidence_refs: list[str] = []
    for paths in duplicate_groups.values():
        evidence_refs.extend(str(path) for path in paths[:2])
    if not evidence_refs:
        evidence_refs = [str(path) for path in memory_files[:5]]

    duplicate_summary = ", ".join(sorted(duplicate_groups)[:5]) if duplicate_groups else "none"
    severity = "high" if duplicate_groups else "medium"
    findings.append(
        {
            "severity": severity,
            "title": "Memory freshness / generation confusion detected",
            "symptom": (
                f"Found {len(memory_files)} memory-like surfaces spanning {len(categories_present)} categories; "
                f"overlapping memory stems: {duplicate_summary}."
            ),
            "user_impact": (
                "When checkpoints, archives, summaries, histories, and session notes overlap, agents can load stale "
                "or contradictory memory and humans lose track of which memory surface is current."
            ),
            "source_layer": "memory_freshness",
            "mechanism": "Repository scan for memory/checkpoint/archive/summary/session style file families and overlapping stems.",
            "root_cause": "The project appears to maintain multiple memory generations or memory surfaces without a clear freshness contract.",
            "evidence_refs": evidence_refs,
            "confidence": 0.71,
            "fix_type": "architecture_change",
            "recommended_fix": (
                "Define one authoritative current memory surface and make archives or summaries explicitly secondary. "
                "Rename or retire overlapping generations so humans and agents can tell what is fresh."
            ),
        }
    )
    return findings
