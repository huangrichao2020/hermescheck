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
ACTIVE_RETENTION_RE = re.compile(
    r"\b(?:active[_ -]?(?:rule|fact|constraint)|still[_ -]?(?:matter|needed|relevant)|"
    r"still needs? to be followed|landed (?:in|to) (?:code|config|docs|tests)|"
    r"delete or skip completed|remove completed|do not store completed|memory gc|retention gc)\b|"
    r"(?:仍需遵守|未来仍需遵守|还需要遵守|已落地见效|已修复|已发布|已验证.{0,12}(?:不要写入|删除|清理)|"
    r"只保留.{0,24}(?:规则|事实)|完成记录.{0,12}(?:不要写入|删除|清理))",
    re.IGNORECASE,
)
COMPLETED_MEMORY_RE = re.compile(
    r"\b(?:completed[_ -]?work|task progress|session outcome|work log|done list|finished task|"
    r"save(?:d)? (?:progress|outcome|completion)|remember(?:ed)? (?:progress|completion|task result))\b|"
    r"(?:完成记录|任务进度|已完成|已修复|已发布|工作日志|过程记录)",
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
        key: []
        for key in (
            "memory",
            "typed",
            "budget",
            "conflict",
            "lifecycle",
            "pointer",
            "active_retention",
            "completed_memory",
        )
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
            if ACTIVE_RETENTION_RE.search(line):
                refs["active_retention"].append(ref)
            if MEMORY_SYSTEM_RE.search(line) and COMPLETED_MEMORY_RE.search(line):
                refs["completed_memory"].append(ref)
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
        "active_retention": refs["active_retention"],
    }
    present = {name: values for name, values in governance.items() if values}
    findings: List[Dict[str, Any]] = []

    governance_summary = ", ".join(sorted(present)) if present else "none"
    if len(present) < 3:
        findings.append(
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
        )

    if not refs["active_retention"] and (refs["completed_memory"] or len(refs["memory"]) >= 10):
        evidence_keys = ("completed_memory", "memory", "lifecycle", "typed", "budget", "conflict", "pointer")
        findings.append(
            {
                "severity": "high" if refs["completed_memory"] else "medium",
                "title": "Memory retention lacks active-rule GC policy",
                "symptom": (
                    "The project has long-term memory signals but no visible rule that memory should keep only "
                    "still-actionable rules/facts and remove completed or already-landed work notes."
                ),
                "user_impact": (
                    "Agents that remember every completed task slowly pollute future context with stale status, old fixes, "
                    "and already-landed implementation details. That wastes tokens and can make the agent follow obsolete "
                    "instructions instead of the current codebase."
                ),
                "source_layer": "memory_lifecycle",
                "mechanism": (
                    "Repository scan for memory writes and lifecycle policy versus active-retention/GC language such as "
                    "'still needs to be followed', 'delete completed work notes', or '只保留仍需遵守的规则/事实'."
                ),
                "root_cause": (
                    "The memory policy does not distinguish durable future constraints from completed-work artifacts "
                    "that should live in git history, logs, or transcripts instead of always-on memory."
                ),
                "evidence_refs": _evidence(refs, *evidence_keys),
                "confidence": 0.76 if refs["completed_memory"] else 0.63,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Add a memory GC rule: memory only keeps rules/facts that still need to be followed; once a change has "
                    "landed in code, config, docs, or tests, delete or skip the completed-work memory. Keep completion "
                    "history in logs/transcripts and compress only the remaining future-facing constraint."
                ),
            }
        )

    return findings
