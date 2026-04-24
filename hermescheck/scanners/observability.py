"""Scan for observability and tracing system presence."""

import re
from pathlib import Path
from typing import Any, Dict, List

from hermescheck.scanners.path_filters import should_skip_path

# Precompiled patterns
OBSERVABILITY_RE = re.compile(
    r"(?:langsmith|langfuse|opentelemetry|arize|phoenix|"
    r"callback.*handler|tracer|telemetry|observ|"
    r"cost.*track|token.*count|latency.*track|"
    r"span.*create|trace.*start|metric.*record|"
    r"promptlayer|helicone|braintrust|smith\.ai|"
    r"langsmith\.run|langfuse\.track|otel\.|open telemetry)",
    re.IGNORECASE,
)

SCAN_EXTENSIONS = {".py", ".ts", ".js", ".yaml", ".yml", ".toml", ".txt"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}


def _should_skip(path: Path) -> bool:
    return should_skip_path(path, SKIP_DIRS)


def scan_observability(target: Path) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    found_any = False
    evidence: List[str] = []

    files = [target] if target.is_file() else sorted(target.rglob("*"))

    for fp in files:
        if not fp.is_file() or _should_skip(fp):
            continue
        if fp.suffix not in SCAN_EXTENSIONS:
            continue

        try:
            content = fp.read_text(encoding="utf-8", errors="ignore")
        except (OSError, PermissionError):
            continue

        if OBSERVABILITY_RE.search(content):
            found_any = True
            # Collect first few matches as evidence
            for lineno, line in enumerate(content.splitlines(), start=1):
                if OBSERVABILITY_RE.search(line):
                    evidence.append(f"{fp}:{lineno}")
                    if len(evidence) >= 5:
                        break
        if found_any:
            break

    if not found_any:
        findings.append(
            {
                "severity": "medium",
                "title": "Missing observability/tracing system",
                "symptom": "No observability, tracing, or telemetry patterns detected in the codebase.",
                "user_impact": "Without tracing, you cannot audit LLM calls, track costs, detect tool-call anomalies, or replay agent decisions for incident investigation.",
                "source_layer": "observability",
                "mechanism": "No match for observability patterns (langsmith, langfuse, opentelemetry, tracer, telemetry, cost tracking, etc.).",
                "root_cause": "No observability or tracing integration has been added to the agent system.",
                "evidence_refs": evidence if evidence else ["(none found)"],
                "confidence": 0.8,
                "fix_type": "add_integration",
                "recommended_fix": (
                    "Add an LLM observability layer: LangSmith, Langfuse, or Helicone for tracing LLM calls. "
                    "Implement cost tracking, token counting, and latency monitoring. "
                    "Use OpenTelemetry for distributed traces across agent steps."
                ),
            }
        )

    return findings
