"""Scan for unsafe code execution patterns (exec, eval, shell=True, etc.)."""

import re
from pathlib import Path
from typing import Any, Dict, List

from hermescheck.scanners.path_filters import should_skip_path

# Precompiled patterns
# NOTE: Built-in `compile(...)` can still be risky, but `re.compile(...)`
# and other dotted variants are routine safe usage. Keep the pattern narrow
# so we only match direct builtin-style calls.
DANGEROUS_CALLS = {
    "exec(": re.compile(r"(?<!\.)\bexec\s*\("),
    "eval(": re.compile(r"(?<!\.)\beval\s*\("),
    "compile(": re.compile(r"(?<!\.)\bcompile\s*\("),
    "os.system(": re.compile(r"\bos\.system\s*\("),
    "new Function(": re.compile(r"\bnew\s+Function\s*\("),
}

SHELL_TRUE_RE = re.compile(r"subprocess\..*shell\s*=\s*True", re.IGNORECASE)

SANDBOX_RE = re.compile(
    r"(?:sandbox|docker|container|seccomp|chroot|\bvm\b|"
    r"subprocess.*timeout|resource\.setrlimit|jail|"
    r"nsjail|firejail|gvisor|kata)",
    re.IGNORECASE,
)

SCAN_EXTENSIONS = {".py", ".ts", ".js"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}


def _should_skip(path: Path) -> bool:
    return should_skip_path(path, SKIP_DIRS)


def _scan_file(fp: Path) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []

    try:
        lines = fp.read_text(encoding="utf-8", errors="ignore").splitlines()
    except (OSError, PermissionError):
        return findings

    # Check for sandbox/safety patterns across the whole file
    try:
        full_content = fp.read_text(encoding="utf-8", errors="ignore")
    except (OSError, PermissionError):
        full_content = ""
    has_sandbox = bool(SANDBOX_RE.search(full_content))

    for lineno, line in enumerate(lines, start=1):
        matched_pattern = None
        pattern_name = None

        # Check dangerous function calls
        for name, pat in DANGEROUS_CALLS.items():
            if pat.search(line):
                matched_pattern = pat
                pattern_name = name
                break

        # Check subprocess shell=True
        if not matched_pattern and SHELL_TRUE_RE.search(line):
            pattern_name = "subprocess(shell=True)"

        if pattern_name:
            severity = (
                "critical" if pattern_name in ("exec(", "eval(", "subprocess(shell=True)", "os.system(") else "high"
            )

            findings.append(
                {
                    "severity": severity,
                    "title": f"Unsafe code execution: {pattern_name}",
                    "symptom": f"Found {pattern_name} at {fp.name}:{lineno}: {line.strip()[:100]}",
                    "user_impact": "Arbitrary code execution from untrusted input can lead to full system compromise, data exfiltration, or remote code execution.",
                    "source_layer": "code_execution",
                    "mechanism": f"Regex match for dangerous function: {pattern_name}",
                    "root_cause": f"Use of {pattern_name} without proper input sanitization or sandboxing.",
                    "evidence_refs": [f"{fp}:{lineno}"],
                    "confidence": 0.65 if has_sandbox else 0.9,
                    "fix_type": "code_change",
                    "recommended_fix": (
                        "Replace with safe alternatives: use ast.literal_eval instead of eval(), "
                        "subprocess.run with list args instead of shell=True, or execute in an isolated sandbox "
                        "(Docker, gVisor, nsjail) with resource limits and network disabled."
                    ),
                }
            )

    return findings


def scan_code_execution(target: Path) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []

    files = [target] if target.is_file() else sorted(target.rglob("*"))

    for fp in files:
        if not fp.is_file() or _should_skip(fp) or fp.suffix not in SCAN_EXTENSIONS:
            continue
        findings.extend(_scan_file(fp))

    return findings
