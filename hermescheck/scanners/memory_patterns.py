"""Scan for memory-related patterns: admission, growth, and missing limits."""

import re
from pathlib import Path
from typing import Any, Dict, List

from hermescheck.scanners.path_filters import should_skip_path

# Precompiled patterns
MEMORY_ADMISSION_RE = re.compile(
    r"(?:memory.*admit|long.?term.*update|persist.*memory|save.*to.*memory|"
    r"memory.*store|write.*memory|commit.*memory|memory.*insert)",
    re.IGNORECASE,
)

MEMORY_GROWTH_RE = re.compile(
    r"(?:add.*memory|upsert.*vector|append.*context|history.*append|"
    r"messages.*append|memory.*push|context.*grow|buffer.*append|"
    r"memory.*add|vector.*insert|embeddings.*store)",
    re.IGNORECASE,
)

MEMORY_LIMIT_RE = re.compile(
    r"(?:max_|limit|ttl|expire|k=|top_|threshold|trim|truncate|"
    r"max_|_max|capacity|bounded|evict|prune|retention|window_size)",
    re.IGNORECASE,
)

SCAN_EXTENSIONS = {".py", ".ts", ".js"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
LOOKAHEAD_LINES = 5


def _should_skip(path: Path) -> bool:
    return should_skip_path(path, SKIP_DIRS)


def _check_limit_nearby(lines: List[str], growth_lineno: int, window: int) -> bool:
    """Check if a limit pattern exists within `window` lines of the growth operation."""
    start = max(0, growth_lineno - 1 - window)
    end = min(len(lines), growth_lineno + window)
    for i in range(start, end):
        if MEMORY_LIMIT_RE.search(lines[i]):
            return True
    return False


def scan_memory_patterns(target: Path) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []

    files = [target] if target.is_file() else sorted(target.rglob("*"))

    for fp in files:
        if not fp.is_file() or _should_skip(fp) or fp.suffix not in SCAN_EXTENSIONS:
            continue

        try:
            content = fp.read_text(encoding="utf-8", errors="ignore")
            lines = content.splitlines()
        except (OSError, PermissionError):
            continue

        has_growth = False
        has_limit = False

        for lineno, line in enumerate(lines, start=1):
            if MEMORY_GROWTH_RE.search(line):
                has_growth = True
            if MEMORY_LIMIT_RE.search(line):
                has_limit = True

        if has_growth and not has_limit:
            findings.append(
                {
                    "severity": "medium",
                    "title": "Memory growth without apparent limit",
                    "symptom": f"Memory/context growth pattern in {fp.name} without nearby limit/trim/expire pattern.",
                    "user_impact": "Unbounded memory growth can cause context window overflow, increased costs, and degraded response quality.",
                    "source_layer": "memory_management",
                    "mechanism": "Growth operation detected but no limit/truncation pattern found within proximity.",
                    "root_cause": "Memory or context is appended without size bounds, TTL, or eviction policy.",
                    "evidence_refs": [str(fp)],
                    "confidence": 0.75,
                    "fix_type": "code_change",
                    "recommended_fix": "Add memory limits: max context size, TTL for old entries, truncation strategy (e.g., keep last N messages, summary-based compaction).",
                }
            )

    return findings
