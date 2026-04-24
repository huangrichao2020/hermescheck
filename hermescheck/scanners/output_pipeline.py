"""Scan for output mutation and response transformation patterns."""

import re
from pathlib import Path
from typing import Any, Dict, List

from hermescheck.scanners.path_filters import should_skip_path

# Precompiled patterns
OUTPUT_MUTATION_RE = re.compile(
    r"(?:mutate.*response|rewrite.*output|transform.*answer|shape.*response|"
    r"post.?process.*llm|stream.*chunk|yield.*token|format.*response|"
    r"response.*filter|output.*sanitize|strip.*tag|clean.*response|"
    r"response.*hook|after.*llm|post.*llm)",
    re.IGNORECASE,
)

ASSEMBLY_RE = re.compile(
    r"(?:buffer|assemble|reconstruct|join|concat|merge.*stream|"
    r"chunk.*buffer|response.*build|output.*assemble|token.*stream)",
    re.IGNORECASE,
)

SCAN_EXTENSIONS = {".py", ".ts", ".js"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}


def _should_skip(path: Path) -> bool:
    return should_skip_path(path, SKIP_DIRS)


def scan_output_pipeline(target: Path) -> List[Dict[str, Any]]:
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

        has_mutation = False
        has_assembly = False
        mutation_lines: List[tuple[int, str]] = []

        for lineno, line in enumerate(lines, start=1):
            if OUTPUT_MUTATION_RE.search(line):
                has_mutation = True
                mutation_lines.append((lineno, line.strip()[:100]))
            if ASSEMBLY_RE.search(line):
                has_assembly = True

        if has_mutation:
            # Lower confidence if assembly patterns are present (suggests intentional streaming)
            confidence = 0.6 if has_assembly else 0.8

            finding_lines = "; ".join(f"L{ln}: {s}" for ln, s in mutation_lines[:3])
            if len(mutation_lines) > 3:
                finding_lines += f" (+{len(mutation_lines) - 3} more)"

            findings.append(
                {
                    "severity": "medium",
                    "title": "Output mutation / response transformation detected",
                    "symptom": f"Response mutation in {fp.name}: {finding_lines}",
                    "user_impact": "Post-processing of LLM output can silently alter, censor, or inject content into responses, changing what the user sees vs. what the model produced.",
                    "source_layer": "output_pipeline",
                    "mechanism": "Regex match for output mutation/transformation patterns.",
                    "root_cause": "LLM responses are modified after generation but before delivery to user.",
                    "evidence_refs": [f"{fp}:{ln}" for ln, _ in mutation_lines],
                    "confidence": confidence,
                    "fix_type": "code_change",
                    "recommended_fix": (
                        "Document all output transformations. Use explicit allowlists for modifications. "
                        "Log both raw LLM output and post-processed output for auditability. "
                        "Avoid injecting content that could be attributed to the model."
                    ),
                }
            )

    return findings
