"""Scan for memory systems without lifecycle, conflict, and retrieval-budget governance."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from hermescheck.scanners.path_filters import iter_source_files, should_skip_path

SCAN_EXTENSIONS = {".py", ".ts", ".js", ".tsx", ".jsx", ".md", ".yaml", ".yml", ".toml", ".json", ".sql"}
SKIP_DIRS = {".git", ".github", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "coverage"}
MAX_FILE_BYTES = 250_000

MEMORY_SYSTEM_RE = re.compile(
    r"\b(?:memory|memories|remember|recall|profile|preference|facts?|episode|reflection|vector store|"
    r"embedding|sqlite|fts5|semantic search|second brain|history|summary)\b|(?:记忆|回忆|偏好|事实|反思)",
    re.IGNORECASE,
)
TYPED_MEMORY_RE = re.compile(
    r"\b(?:identity|preference|goal|project|habit|decision|constraint|relationship|episode|reflection|"
    r"memory[_ -]?type|fact[_ -]?type)\b",
    re.IGNORECASE,
)
RETRIEVAL_BUDGET_RE = re.compile(
    r"\b(?:top[_ -]?k|limit|char(?:acter)?[_ -]?limit|token[_ -]?budget|context[_ -]?budget|retrieval[_ -]?budget|"
    r"max[_ -]?(?:tokens|chars|memories)|fts5|full[-_ ]?text search)\b",
    re.IGNORECASE,
)
CONFLICT_MERGE_RE = re.compile(
    r"\b(?:confidence|conflict|contradiction|merge|dedupe|duplicate|overlap|similarity|newer wins|"
    r"resolve[_ -]?conflict|coalesce|canonical)\b",
    re.IGNORECASE,
)
LIFECYCLE_RE = re.compile(
    r"\b(?:active|durable|ttl|decay|retention|reinforce|reinforcement|prune|dismiss|dismissed|stale|"
    r"expire|expiration|aging|archive)\b",
    re.IGNORECASE,
)
POINTER_RE = re.compile(
    r"\b(?:pointer|anchor|source_ref|evidence_ref|semantic_hash|topic_anchor|page fault|page table|swap in)\b",
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
    refs = {key: [] for key in ("memory", "typed", "budget", "conflict", "lifecycle", "pointer")}
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
            if MEMORY_SYSTEM_RE.search(line):
                refs["memory"].append(ref)
            if TYPED_MEMORY_RE.search(line):
                refs["typed"].append(ref)
            if RETRIEVAL_BUDGET_RE.search(line):
                refs["budget"].append(ref)
            if CONFLICT_MERGE_RE.search(line):
                refs["conflict"].append(ref)
            if LIFECYCLE_RE.search(line):
                refs["lifecycle"].append(ref)
            if POINTER_RE.search(line):
                refs["pointer"].append(ref)
    return refs


def _evidence(refs: dict[str, list[str]], *keys: str, limit: int = 9) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for key in keys:
        for ref in refs.get(key, []):
            if ref not in seen:
                out.append(ref)
                seen.add(ref)
            if len(out) >= limit:
                return out
    return out


def scan_memory_lifecycle(target: Path) -> List[Dict[str, Any]]:
    refs = _collect_refs(target)
    if len(refs["memory"]) < 6:
        return []

    governance = {
        "typed": refs["typed"],
        "retrieval_budget": refs["budget"],
        "conflict_merge": refs["conflict"],
        "lifecycle": refs["lifecycle"],
        "pointers": refs["pointer"],
    }
    present = {name: values for name, values in governance.items() if values}
    if len(present) >= 3:
        return []

    governance_summary = ", ".join(sorted(present)) if present else "none"
    return [
        {
            "severity": "high",
            "title": "Memory system lacks lifecycle governance",
            "symptom": (
                f"Found {len(refs['memory'])} memory-system markers, but only {len(present)} memory governance "
                f"categories were visible ({governance_summary})."
            ),
            "user_impact": (
                "A memory-rich agent can accumulate stale, contradictory, over-injected, or untraceable memories unless "
                "it controls memory type, retrieval budget, merge/conflict behavior, lifecycle, and source pointers."
            ),
            "source_layer": "memory_lifecycle",
            "mechanism": (
                "Repository scan for memory systems versus typed memories, retrieval budgets, conflict/merge policy, "
                "lifecycle/decay policy, and pointer/source-reference signals."
            ),
            "root_cause": "The project appears to store or retrieve memory before defining how memories age, merge, compete, and re-enter context.",
            "evidence_refs": _evidence(refs, "memory", "typed", "budget", "conflict", "lifecycle", "pointer"),
            "confidence": 0.71,
            "fix_type": "architecture_change",
            "recommended_fix": (
                "Add memory lifecycle governance: explicit memory types, top-k/token/character retrieval budgets, "
                "confidence-based conflict resolution, dedupe/merge rules, active-vs-durable lifecycle with decay, "
                "and pointers back to raw evidence or episodic source records."
            ),
        }
    ]
