"""Scan RAG stacks for retrieval, context, and ingestion governance."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from hermescheck.scanners.path_filters import iter_source_files, should_skip_path

SCAN_EXTENSIONS = {".py", ".ts", ".js", ".tsx", ".jsx", ".md", ".yaml", ".yml", ".toml", ".json"}
SKIP_DIRS = {".git", ".github", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "coverage"}
MAX_FILE_BYTES = 250_000

RAG_RE = re.compile(
    r"\b(?:rag|retrieval[_ -]?augmented|knowledge[_ -]?base|vector[_ -]?(?:store|db|search)|"
    r"embedding|embeddings|document[_ -]?(?:loader|upload|ingest)|chroma|qdrant|milvus|faiss|"
    r"bm25|hybrid[_ -]?search|rerank|reranker)\b",
    re.IGNORECASE,
)
CHUNKING_RE = re.compile(
    r"\b(?:chunk[_ -]?(?:size|overlap)|text[_ -]?splitter|recursivecharactertextsplitter|split[_ -]?documents|"
    r"token[_ -]?splitter|document[_ -]?chunk)\b",
    re.IGNORECASE,
)
RETRIEVAL_BUDGET_RE = re.compile(
    r"\b(?:top[_ -]?k|limit|score[_ -]?threshold|max[_ -]?(?:tokens|chars|context|documents)|"
    r"context[_ -]?budget|retrieval[_ -]?budget|similarity[_ -]?threshold|rerank[_ -]?top[_ -]?k)\b",
    re.IGNORECASE,
)
FALLBACK_MODE_RE = re.compile(
    r"\b(?:full[_ -]?context|rag[_ -]?full[_ -]?context|bypass[_ -]?embedding|bypass[_ -]?retrieval|"
    r"skip[_ -]?retrieval|raw[_ -]?document|entire[_ -]?document)\b",
    re.IGNORECASE,
)
INGESTION_STATE_RE = re.compile(
    r"\b(?:ingest[_ -]?status|embedding[_ -]?status|async[_ -]?embedding|retry|backoff|dedupe|"
    r"content[_ -]?hash|document[_ -]?(?:id|version)|index[_ -]?version|reindex|failed[_ -]?documents)\b",
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
    refs = {key: [] for key in ("rag", "chunking", "budget", "fallback", "ingestion")}
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
            if RAG_RE.search(line):
                refs["rag"].append(ref)
            if CHUNKING_RE.search(line):
                refs["chunking"].append(ref)
            if RETRIEVAL_BUDGET_RE.search(line):
                refs["budget"].append(ref)
            if FALLBACK_MODE_RE.search(line):
                refs["fallback"].append(ref)
            if INGESTION_STATE_RE.search(line):
                refs["ingestion"].append(ref)
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


def scan_rag_pipeline_governance(target: Path) -> List[Dict[str, Any]]:
    refs = _collect_refs(target)
    if len(refs["rag"]) < 4:
        return []

    findings: List[Dict[str, Any]] = []
    governance = {
        "chunking": refs["chunking"],
        "retrieval_budget": refs["budget"],
        "ingestion_state": refs["ingestion"],
    }
    present = {name: values for name, values in governance.items() if values}
    if len(present) < 2:
        present_summary = ", ".join(sorted(present)) if present else "none"
        findings.append(
            {
                "severity": "high",
                "title": "RAG pipeline lacks retrieval governance",
                "symptom": (
                    f"Found {len(refs['rag'])} RAG/vector/embedding markers, but only {len(present)} governance "
                    f"categories were visible ({present_summary})."
                ),
                "user_impact": (
                    "A RAG system can silently over-inject context, retrieve unstable chunks, or leave failed document "
                    "ingestion unnoticed, making answers expensive and hard to trust."
                ),
                "source_layer": "rag_pipeline",
                "mechanism": "Repository scan for RAG stack signals versus chunking, retrieval budget, and ingestion-state controls.",
                "root_cause": "The project appears to add document retrieval before defining the retrieval and indexing contract.",
                "evidence_refs": _evidence(refs, "rag", "chunking", "budget", "ingestion"),
                "confidence": 0.7,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Define RAG governance: explicit chunk size/overlap, top-k or score thresholds, context token/char "
                    "budgets, ingestion status, content hashes or document versions, retry/backoff, and reindex behavior."
                ),
            }
        )

    if refs["fallback"] and not refs["budget"]:
        findings.append(
            {
                "severity": "medium",
                "title": "RAG full-context mode lacks context budget",
                "symptom": "Detected full-context or retrieval-bypass modes without visible token/character context budgets.",
                "user_impact": (
                    "Full-document injection can explode prompt size, leak irrelevant content, and make cost or latency "
                    "unpredictable unless it has an explicit budget and fallback behavior."
                ),
                "source_layer": "rag_pipeline",
                "mechanism": "Repository scan for full-context/bypass retrieval modes versus context budget controls.",
                "root_cause": "The project exposes a high-context RAG mode before bounding its prompt impact.",
                "evidence_refs": _evidence(refs, "fallback", "rag", "budget"),
                "confidence": 0.67,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Gate full-context and bypass-retrieval modes with max tokens/chars, document size checks, user/admin "
                    "settings, and logs showing why retrieval was bypassed."
                ),
            }
        )

    return findings
