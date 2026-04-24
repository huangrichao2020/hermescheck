"""Scan for runtime surface sprawl and operational complexity."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

SCAN_EXTENSIONS = {".py", ".ts", ".js", ".tsx", ".jsx", ".json", ".yaml", ".yml", ".toml", ".md"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "coverage"}
RUNTIME_PATTERNS = {
    "web_api": re.compile(r"\b(fastapi|flask|express|django|router|api router)\b", re.IGNORECASE),
    "ui": re.compile(r"\b(streamlit|react|next|vue|svelte|electron|pywebview|tauri)\b", re.IGNORECASE),
    "queue_jobs": re.compile(r"\b(celery|rq|bullmq|rabbitmq|kafka|worker queue)\b", re.IGNORECASE),
    "ops": re.compile(r"\b(docker|kubernetes|pm2|supervisor|launchd|systemd|nginx|gunicorn)\b", re.IGNORECASE),
    "storage": re.compile(r"\b(redis|postgres|mysql|mongodb|sqlite|vector store|milvus|pinecone)\b", re.IGNORECASE),
    "agent_stack": re.compile(r"\b(langchain|autogen|crewai|mcp|swarm|agent loop|tool calling)\b", re.IGNORECASE),
}


def _should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def scan_runtime_complexity(target: Path) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    matched_categories: dict[str, list[str]] = {key: [] for key in RUNTIME_PATTERNS}

    files = [target] if target.is_file() else sorted(target.rglob("*"))
    for fp in files:
        if not fp.is_file() or _should_skip(fp) or fp.suffix not in SCAN_EXTENSIONS:
            continue
        try:
            lines = fp.read_text(encoding="utf-8", errors="ignore").splitlines()
        except (OSError, PermissionError):
            continue

        for lineno, line in enumerate(lines, start=1):
            for category, pattern in RUNTIME_PATTERNS.items():
                if pattern.search(line):
                    matched_categories[category].append(f"{fp}:{lineno}")

    present_categories = {category: refs for category, refs in matched_categories.items() if refs}
    if len(present_categories) < 4:
        return findings

    severity = "high" if len(present_categories) >= 5 else "medium"
    category_summary = ", ".join(sorted(present_categories))
    evidence_refs: list[str] = []
    for refs in present_categories.values():
        evidence_refs.extend(refs[:2])

    findings.append(
        {
            "severity": severity,
            "title": "Runtime surface sprawl detected",
            "symptom": (
                f"Found runtime markers across {len(present_categories)} operating surfaces ({category_summary})."
            ),
            "user_impact": (
                "Projects that mix many runtime surfaces are harder to start, debug, document, and evolve without "
                "internal friction."
            ),
            "source_layer": "runtime_architecture",
            "mechanism": "Repository scan for API/UI/queue/ops/storage/agent-runtime surfaces.",
            "root_cause": "The project appears to accumulate many runtime responsibilities and deployment surfaces in one place.",
            "evidence_refs": evidence_refs,
            "confidence": 0.73,
            "fix_type": "architecture_change",
            "recommended_fix": (
                "Reduce the number of runtime surfaces each developer must hold in their head. Document the primary "
                "runtime path and separate optional services or deployment layers more clearly."
            ),
        }
    )
    return findings
