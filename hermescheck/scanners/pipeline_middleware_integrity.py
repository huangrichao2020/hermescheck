"""Scan LLM request/response middleware chains for observability and failure policy."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from hermescheck.scanners.path_filters import iter_source_files, should_skip_path

SCAN_EXTENSIONS = {".py", ".ts", ".js", ".tsx", ".jsx", ".md", ".yaml", ".yml", ".toml", ".json"}
SKIP_DIRS = {".git", ".github", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "coverage"}
MAX_FILE_BYTES = 250_000

PIPELINE_RE = re.compile(
    r"\b(?:pipeline|pipelines|middleware|filter|filters|inbound|outbound|pre[_ -]?process|post[_ -]?process|"
    r"before[_ -]?(?:llm|model)|after[_ -]?(?:llm|model)|request[_ -]?filter|response[_ -]?filter)\b",
    re.IGNORECASE,
)
MUTATION_RE = re.compile(
    r"\b(?:sanitize|redact|mask|moderation|translate|rewrite|inject[_ -]?prompt|transform[_ -]?(?:message|response)|"
    r"strip|replace|content[_ -]?filter|pii|sensitive)\b",
    re.IGNORECASE,
)
ORDER_RE = re.compile(r"\b(?:priority|order|sequence|sort|chain|before|after|stage|rank|position)\b", re.IGNORECASE)
AUDIT_RE = re.compile(
    r"\b(?:raw[_ -]?(?:message|response|request)|transformed[_ -]?(?:message|response|request)|audit[_ -]?log|"
    r"trace|span|diff|before[_ -]?after|log[_ -]?mutation|original[_ -]?content)\b",
    re.IGNORECASE,
)
FAILURE_RE = re.compile(
    r"\b(?:fail[_ -]?(?:open|closed)|on[_ -]?error|try\s*:|except|catch|fallback|skip[_ -]?filter|"
    r"filter[_ -]?error|raise|timeout)\b",
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
    refs = {key: [] for key in ("pipeline", "mutation", "order", "audit", "failure")}
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
            if PIPELINE_RE.search(line):
                refs["pipeline"].append(ref)
            if MUTATION_RE.search(line):
                refs["mutation"].append(ref)
            if ORDER_RE.search(line):
                refs["order"].append(ref)
            if AUDIT_RE.search(line):
                refs["audit"].append(ref)
            if FAILURE_RE.search(line):
                refs["failure"].append(ref)
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


def scan_pipeline_middleware_integrity(target: Path) -> List[Dict[str, Any]]:
    refs = _collect_refs(target)
    if len(refs["pipeline"]) < 3:
        return []

    findings: List[Dict[str, Any]] = []
    if refs["mutation"] and not refs["audit"]:
        findings.append(
            {
                "severity": "high",
                "title": "LLM pipeline mutates messages without audit trail",
                "symptom": (
                    "Detected request/response pipeline mutation such as sanitize, translate, redact, rewrite, or prompt "
                    "injection without visible raw/transformed audit logging."
                ),
                "user_impact": (
                    "Users and maintainers cannot tell whether an answer came from the model, a filter, a translation "
                    "step, or a prompt-injection middleware."
                ),
                "source_layer": "pipeline_middleware",
                "mechanism": "Repository scan for LLM middleware and mutation filters versus raw/transformed trace signals.",
                "root_cause": "The pipeline appears to transform model inputs or outputs before making those transformations observable.",
                "evidence_refs": _evidence(refs, "mutation", "pipeline", "audit"),
                "confidence": 0.71,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Log or trace raw and transformed messages with filter identity, order, and reason; keep sensitive "
                    "raw logs protected while preserving enough evidence for debugging."
                ),
            }
        )

    if len(refs["pipeline"]) >= 4 and not refs["order"]:
        findings.append(
            {
                "severity": "medium",
                "title": "LLM pipeline order is implicit",
                "symptom": "Detected multiple pipeline/filter markers without visible priority, order, stage, or chain controls.",
                "user_impact": (
                    "Filter behavior can depend on incidental registration order, making moderation, redaction, "
                    "translation, and prompt injection hard to reason about."
                ),
                "source_layer": "pipeline_middleware",
                "mechanism": "Repository scan for multiple middleware/filter signals versus explicit ordering controls.",
                "root_cause": "Middleware registration appears to rely on implicit order rather than a declared pipeline contract.",
                "evidence_refs": _evidence(refs, "pipeline", "order"),
                "confidence": 0.67,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Declare pipeline ordering with stages or priorities, document inbound/outbound order, and test "
                    "conflicting filters such as translate-before-redact versus redact-before-translate."
                ),
            }
        )

    if refs["pipeline"] and not refs["failure"]:
        findings.append(
            {
                "severity": "medium",
                "title": "LLM pipeline lacks filter failure policy",
                "symptom": "Detected LLM middleware/filter chain without visible error, timeout, or fail-open/fail-closed policy.",
                "user_impact": (
                    "A broken sanitizer, translator, or moderation filter may silently skip protection or block all "
                    "responses depending on default exception behavior."
                ),
                "source_layer": "pipeline_middleware",
                "mechanism": "Repository scan for middleware chains versus filter error-handling policy.",
                "root_cause": "The pipeline exposes automatic message transformation without defining what happens when filters fail.",
                "evidence_refs": _evidence(refs, "pipeline", "failure"),
                "confidence": 0.65,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Define per-filter error behavior, timeouts, and fail-open/fail-closed defaults; surface filter "
                    "failures in logs and user-visible status when they affect output."
                ),
            }
        )

    return findings
