"""Scan for impression pointers between facts, skills, and raw memory."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from hermescheck.scanners.path_filters import should_skip_path

SCAN_EXTENSIONS = {".py", ".ts", ".js", ".tsx", ".jsx", ".md", ".txt", ".yaml", ".yml", ".toml", ".json"}
SKIP_DIRS = {".git", ".github", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "coverage", "locales"}
SKIP_FILENAMES = {"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "poetry.lock", "uv.lock"}
MAX_FILE_BYTES = 250_000

FACT_MEMORY_RE = re.compile(
    r"\b(?:fact|facts|preference|preferences|profile|user profile|entity|entities|attribute|metadata)\b|(?:事实|偏好|画像|实体)",
    re.IGNORECASE,
)
SKILL_MEMORY_RE = re.compile(
    r"\b(?:skill|skills|procedure|procedural|workflow|runbook|sop|playbook|capability)\b|(?:技能|流程|经验|操作手册)",
    re.IGNORECASE,
)
EPISODIC_MEMORY_RE = re.compile(
    r"\b(?:session|conversation|dialogue|transcript|history|episode|event|memory chunk|chunk)\b|(?:会话|对话|片段|事件)",
    re.IGNORECASE,
)
IMPRESSION_RE = re.compile(
    r"\b(?:impression|impressions|associative|association|cue|gist|landmark|mental map|concept map|"
    r"semantic hint|route hint|memory impression|impression chunk)\b|(?:印象|联想|概念路标|路标|线索|语义提示|大概知道)",
    re.IGNORECASE,
)
POINTER_RE = re.compile(
    r"\b(?:pointer_ref|pointer_type|vector_id|file_path|skill_id|semantic_hash|semantic anchor|"
    r"topic_anchor|page table|page entry|page fault|swap in|swap-in|activation_level|in_mind|subconscious|"
    r"forgotten|retrieval pointer)\b|(?:语义锚点|页表|页表项|缺页|换入|激活层级|潜意识|遗忘)",
    re.IGNORECASE,
)
POINTER_CONTEXT_RE = re.compile(
    r"(?:impression|memory|page[_ -]?table|page[_ -]?fault|semantic[_ -]?hash|topic[_ -]?anchor|"
    r"pointer[_ -]?(?:ref|type)|vector_id|activation_level|印象|记忆|页表|缺页|语义锚点)",
    re.IGNORECASE,
)


def _should_skip(path: Path) -> bool:
    if path.name.lower() in SKIP_FILENAMES:
        return True
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return True
    except OSError:
        return True
    return should_skip_path(path, SKIP_DIRS)


def _collect_refs(target: Path) -> dict[str, list[str]]:
    refs = {
        "fact": [],
        "skill": [],
        "episodic": [],
        "impression": [],
        "pointer": [],
    }
    files = [target] if target.is_file() else sorted(target.rglob("*"))
    for fp in files:
        if not fp.is_file() or _should_skip(fp) or fp.suffix not in SCAN_EXTENSIONS:
            continue

        path_text = "/".join(fp.parts)
        path_ref = f"{fp}:1"
        if FACT_MEMORY_RE.search(path_text):
            refs["fact"].append(path_ref)
        if SKILL_MEMORY_RE.search(path_text):
            refs["skill"].append(path_ref)
        if EPISODIC_MEMORY_RE.search(path_text):
            refs["episodic"].append(path_ref)
        if IMPRESSION_RE.search(path_text):
            refs["impression"].append(path_ref)
        if POINTER_RE.search(path_text) and POINTER_CONTEXT_RE.search(path_text):
            refs["pointer"].append(path_ref)

        try:
            lines = fp.read_text(encoding="utf-8", errors="ignore").splitlines()
        except (OSError, PermissionError):
            continue

        for lineno, line in enumerate(lines, start=1):
            ref = f"{fp}:{lineno}"
            if FACT_MEMORY_RE.search(line):
                refs["fact"].append(ref)
            if SKILL_MEMORY_RE.search(line):
                refs["skill"].append(ref)
            if EPISODIC_MEMORY_RE.search(line):
                refs["episodic"].append(ref)
            if IMPRESSION_RE.search(line):
                refs["impression"].append(ref)
            if POINTER_RE.search(line) and (POINTER_CONTEXT_RE.search(line) or POINTER_CONTEXT_RE.search(path_text)):
                refs["pointer"].append(ref)
    return refs


def _evidence(refs: dict[str, list[str]]) -> list[str]:
    evidence_refs: list[str] = []
    seen: set[str] = set()
    for key in ("fact", "skill", "episodic", "impression", "pointer"):
        for ref in refs[key][:4]:
            if ref not in seen:
                evidence_refs.append(ref)
                seen.add(ref)
    return evidence_refs[:10]


def scan_impression_memory(target: Path) -> List[Dict[str, Any]]:
    refs = _collect_refs(target)
    has_memory_system = len(refs["fact"]) >= 2 or len(refs["episodic"]) >= 3
    has_skill_system = len(refs["skill"]) >= 2
    has_impressions = len(refs["impression"]) >= 2
    has_impression_pointers = len(refs["pointer"]) >= 2

    if not has_memory_system or not has_skill_system:
        return []

    findings: List[Dict[str, Any]] = []
    if not has_impressions:
        findings.append(
            {
                "severity": "medium",
                "title": "Impression memory layer missing",
                "symptom": (
                    f"Found fact/episodic memory signals ({len(refs['fact']) + len(refs['episodic'])}) and "
                    f"skill/procedure signals ({len(refs['skill'])}), but only "
                    f"{len(refs['impression'])} impression signals."
                ),
                "user_impact": (
                    "Agents with only factual memory and procedural skills can recall exact notes or run known workflows, "
                    "but they lack lightweight conceptual cues for fast association. They may over-search, "
                    "over-load context, or miss the simple route that a human would remember as an impression."
                ),
                "source_layer": "impression_memory",
                "mechanism": (
                    "Repository scan for fact memory, episodic chunks, procedural skills, and associative impression "
                    "vocabulary."
                ),
                "root_cause": (
                    "The memory architecture appears to separate facts and skills, but does not expose an associative "
                    "impression layer for concept-level recall."
                ),
                "evidence_refs": _evidence(refs),
                "confidence": 0.67,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Add impression chunks: short associative records that connect concepts, routes, preferences, and "
                    "situational cues without pretending to be exact facts or full procedures. Use them as retrieval "
                    "hints, not as authoritative truth."
                ),
            }
        )
        return findings

    if not has_impression_pointers:
        findings.append(
            {
                "severity": "medium",
                "title": "Impression pointers missing",
                "symptom": (
                    f"Found {len(refs['impression'])} impression/cue signals, but only "
                    f"{len(refs['pointer'])} pointer, page-table, or page-fault signals."
                ),
                "user_impact": (
                    "Impression text saves some tokens, but without a pointer it cannot reliably fault in the raw "
                    "memory, file, vector entry, or skill when the user asks for details. The agent gets a slogan, "
                    "not an address."
                ),
                "source_layer": "impression_memory",
                "mechanism": "Repository scan for impression/cue vocabulary versus semantic anchors, pointer refs, and page-fault terms.",
                "root_cause": (
                    "The memory architecture appears to store associative hints, but does not model them as page-table "
                    "entries pointing back to authoritative detail."
                ),
                "evidence_refs": _evidence(refs),
                "confidence": 0.66,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Upgrade impressions into ImpressionPage entries: keep a topic_anchor and small cue in prompt, "
                    "plus semantic_hash, pointer_type, pointer_ref, activation_level, last_accessed, and status. "
                    "Use pointer_ref for deep-dive retrieval when the impression is not enough."
                ),
            }
        )

    return findings
