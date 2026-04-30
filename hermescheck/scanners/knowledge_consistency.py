"""Scan durable project knowledge for stale references and sync gaps."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import unquote

from hermescheck.scanners.path_filters import should_skip_path

DOC_EXTENSIONS = {".md", ".txt", ".rst"}
CODE_EXTENSIONS = {".py", ".ts", ".js", ".tsx", ".jsx"}
ROOT_DOC_NAMES = {
    "README.md",
    "README.txt",
    "README.rst",
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    "HERMES.md",
    "HANDOFF.md",
    "RUNBOOK.md",
}
DOC_DIR_HINTS = {
    "docs",
    "doc",
    "memory",
    "memories",
    "knowledge",
    "skills",
    "optional-skills",
    "runbooks",
    "handoffs",
}
SKIP_DIRS = {".git", ".github", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "coverage"}
MAX_FILE_BYTES = 250_000
MAX_EVIDENCE = 10

MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
INLINE_PATH_RE = re.compile(r"`([^`\n]+)`")
LOCAL_PATH_EXTENSIONS = DOC_EXTENSIONS | CODE_EXTENSIONS | {".json", ".yaml", ".yml", ".toml", ".sh", ".bash"}
RELATIVE_TIME_RE = re.compile(
    r"\b(?:today|yesterday|tomorrow|recently|last\s+week|next\s+week|this\s+week|last\s+month|next\s+month)\b|"
    r"(?:今天|昨天|明天|最近|近期|刚刚|上周|下周|这周|本周|上个月|下个月)",
    re.IGNORECASE,
)
AGENT_CODE_RE = re.compile(r"(?:agent|subagent|tool_call|function_call|memory|skill|scheduler|orchestrator)", re.IGNORECASE)


def _should_skip(path: Path) -> bool:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return True
    except OSError:
        return True
    return should_skip_path(path, SKIP_DIRS)


def _is_doc_surface(path: Path, target: Path) -> bool:
    if path.suffix.lower() not in DOC_EXTENSIONS:
        return False
    try:
        rel_parts = path.relative_to(target).parts if target.is_dir() else (path.name,)
    except ValueError:
        rel_parts = path.parts
    lowered_parts = {part.lower() for part in rel_parts[:-1]}
    return path.name in ROOT_DOC_NAMES or bool(lowered_parts & DOC_DIR_HINTS)


def _iter_files(target: Path) -> list[Path]:
    files = [target] if target.is_file() else sorted(target.rglob("*"))
    return [fp for fp in files if fp.is_file() and not _should_skip(fp)]


def _iter_doc_surfaces(target: Path) -> list[Path]:
    return [fp for fp in _iter_files(target) if _is_doc_surface(fp, target)]


def _clean_path_token(raw: str) -> str | None:
    token = unquote(raw.strip().strip("<>").strip("'\""))
    if not token or token.startswith(("#", "mailto:", "http://", "https://")):
        return None
    token = token.split("#", 1)[0].split("?", 1)[0]
    token = re.sub(r":\d+(?::\d+)?$", "", token)
    if not token or token.startswith(("$", "{")):
        return None
    return token


def _looks_like_local_path(token: str) -> bool:
    if "\n" in token or len(token) > 180:
        return False
    if token.startswith(("./", "../", "/")):
        return True
    suffix = Path(token).suffix.lower()
    return ("/" in token or "\\" in token) and suffix in LOCAL_PATH_EXTENSIONS


def _path_exists(token: str, doc_path: Path, target: Path) -> bool:
    candidate = Path(token)
    if candidate.is_absolute():
        return candidate.exists()

    checks = [doc_path.parent / candidate]
    if target.is_dir():
        checks.append(target / candidate)
        if candidate.parts and candidate.parts[0] == target.name:
            checks.append(target.parent / candidate)
    return any(path.exists() for path in checks)


def _missing_path_refs(target: Path, doc_files: list[Path]) -> list[str]:
    refs: list[str] = []
    seen: set[tuple[Path, int, str]] = set()
    for fp in doc_files:
        try:
            lines = fp.read_text(encoding="utf-8", errors="ignore").splitlines()
        except (OSError, PermissionError):
            continue

        for lineno, line in enumerate(lines, start=1):
            tokens = [match.group(1) for match in MARKDOWN_LINK_RE.finditer(line)]
            tokens.extend(match.group(1) for match in INLINE_PATH_RE.finditer(line))
            for raw in tokens:
                token = _clean_path_token(raw)
                if not token or not _looks_like_local_path(token):
                    continue
                if _path_exists(token, fp, target):
                    continue
                key = (fp, lineno, token)
                if key in seen:
                    continue
                seen.add(key)
                refs.append(f"{fp}:{lineno} -> {token}")
                if len(refs) >= MAX_EVIDENCE:
                    return refs
    return refs


def _relative_time_refs(doc_files: list[Path]) -> list[str]:
    refs: list[str] = []
    for fp in doc_files:
        try:
            lines = fp.read_text(encoding="utf-8", errors="ignore").splitlines()
        except (OSError, PermissionError):
            continue

        for lineno, line in enumerate(lines, start=1):
            if RELATIVE_TIME_RE.search(line):
                refs.append(f"{fp}:{lineno}")
                if len(refs) >= MAX_EVIDENCE:
                    return refs
    return refs


def _has_agent_code(files: list[Path]) -> bool:
    for fp in files:
        if fp.suffix.lower() not in CODE_EXTENSIONS:
            continue
        if AGENT_CODE_RE.search("/".join(fp.parts)):
            return True
        try:
            sample = fp.read_text(encoding="utf-8", errors="ignore")[:4000]
        except (OSError, PermissionError):
            continue
        if AGENT_CODE_RE.search(sample):
            return True
    return False


def _inventory_gap_refs(target: Path, files: list[Path], doc_files: list[Path]) -> list[str]:
    if not target.is_dir():
        return []

    has_root_instruction = any((target / name).exists() for name in ("AGENTS.md", "CLAUDE.md", "GEMINI.md", "HERMES.md"))
    has_readme_or_docs = any(fp.name.startswith("README") or "docs" in {part.lower() for part in fp.parts} for fp in doc_files)
    has_memory_or_skills = any(part.lower() in {"memory", "memories", "skills", "optional-skills"} for fp in files for part in fp.parts)
    has_agent_code = _has_agent_code(files)

    if (has_memory_or_skills and not has_root_instruction) or (has_agent_code and not has_readme_or_docs):
        refs: list[str] = []
        if has_memory_or_skills:
            refs.append("memory_or_skill_surface_present")
        if has_agent_code:
            refs.append("agent_code_surface_present")
        if not has_root_instruction:
            refs.append("missing_root_agent_instruction")
        if not has_readme_or_docs:
            refs.append("missing_readme_or_docs")
        return refs
    return []


def scan_knowledge_consistency(target: Path) -> List[Dict[str, Any]]:
    """Return advisory findings for docs, memory, and skill consistency."""

    files = _iter_files(target)
    doc_files = _iter_doc_surfaces(target)
    findings: List[Dict[str, Any]] = []

    inventory_refs = _inventory_gap_refs(target, files, doc_files)
    if inventory_refs:
        findings.append(
            {
                "severity": "low",
                "title": "Knowledge surface inventory is incomplete",
                "symptom": "The project appears to have agent code, memory, or skills without a complete root knowledge surface.",
                "user_impact": (
                    "Future audits may over-index on source regexes because the target agent has not clearly declared "
                    "where durable instructions, procedures, and project docs live."
                ),
                "source_layer": "knowledge_consistency",
                "mechanism": "Inventory of root instructions, README/docs, memory directories, skill directories, and agent code.",
                "root_cause": "The durable knowledge layers are not all discoverable from the project root.",
                "evidence_refs": inventory_refs,
                "confidence": 0.54,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Ask the target agent to inventory its root instructions, docs, memory, skills, and handoff files; "
                    "then state which layer is authoritative for facts, procedures, and project runbooks."
                ),
            }
        )

    missing_refs = _missing_path_refs(target, doc_files)
    if missing_refs:
        findings.append(
            {
                "severity": "medium",
                "title": "Documentation references missing local paths",
                "symptom": "Durable documentation points at local files or runbooks that were not found on disk.",
                "user_impact": (
                    "A target agent following stale paths can waste audit time, miss the real source of truth, or "
                    "resurrect outdated operational instructions."
                ),
                "source_layer": "knowledge_consistency",
                "mechanism": "Markdown link and inline-path check against files relative to the document and repository root.",
                "root_cause": "Knowledge artifacts were likely moved, deleted, or renamed without updating durable docs.",
                "evidence_refs": missing_refs,
                "confidence": 0.66,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Ask the target agent to verify each missing path against the current tree, update or delete stale "
                    "references, and keep only one live runbook link for each repeated operation."
                ),
            }
        )

    time_refs = _relative_time_refs(doc_files)
    if time_refs:
        findings.append(
            {
                "severity": "low",
                "title": "Durable docs contain relative time language",
                "symptom": "Durable docs or memory surfaces use relative time words such as today, yesterday, or recently.",
                "user_impact": (
                    "Relative dates become ambiguous across sessions, so future agents may treat stale notes as current state."
                ),
                "source_layer": "knowledge_consistency",
                "mechanism": "Scan of durable docs, memory, runbook, and skill surfaces for relative temporal language.",
                "root_cause": "Session notes were likely copied into long-lived docs without converting them into dated facts.",
                "evidence_refs": time_refs,
                "confidence": 0.58,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Ask the target agent to replace relative dates with absolute dates, mark superseded notes, and "
                    "delete completed scratch history once the useful fact has been merged."
                ),
            }
        )

    return findings
