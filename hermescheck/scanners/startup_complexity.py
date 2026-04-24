"""Scan for startup surface sprawl and launcher chains."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

SCAN_EXTENSIONS = {".py", ".sh", ".bash", ".zsh", ".js", ".ts", ".json", ".yaml", ".yml", ".toml", ".plist", ".service"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "coverage"}
STARTUP_FILE_RE = re.compile(
    r"(?:launch|start|run|serve|bootstrap|entrypoint|daemon|supervisord|pm2|launchd|docker-compose|compose|procfile|app)\b",
    re.IGNORECASE,
)
WRAPPER_RE = re.compile(
    r"(?:subprocess\.run|subprocess\.Popen|os\.system|exec\s+|python\s+-m|node\s+|bash\s+|sh\s+|launchctl|pm2|supervisor)",
    re.IGNORECASE,
)


def _should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def scan_startup_complexity(target: Path) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    startup_files: list[Path] = []
    wrapper_sites: list[str] = []

    files = [target] if target.is_file() else sorted(target.rglob("*"))
    for fp in files:
        if not fp.is_file() or _should_skip(fp) or fp.suffix not in SCAN_EXTENSIONS:
            continue

        path_text = "/".join(fp.parts).lower()
        if STARTUP_FILE_RE.search(path_text):
            startup_files.append(fp)

        try:
            lines = fp.read_text(encoding="utf-8", errors="ignore").splitlines()
        except (OSError, PermissionError):
            continue

        if not STARTUP_FILE_RE.search(path_text):
            continue
        for lineno, line in enumerate(lines, start=1):
            if WRAPPER_RE.search(line):
                wrapper_sites.append(f"{fp}:{lineno}")

    if len(startup_files) < 3 and len(wrapper_sites) < 4:
        return findings

    severity = "high" if len(startup_files) >= 5 or len(wrapper_sites) >= 6 else "medium"
    findings.append(
        {
            "severity": severity,
            "title": "Startup surface sprawl detected",
            "symptom": (
                f"Found {len(startup_files)} startup-like files and {len(wrapper_sites)} launcher/wrapper sites."
            ),
            "user_impact": (
                "When a project can be started through many overlapping wrappers, scripts, and service managers, "
                "startup becomes slower to debug, easier to break, and harder to document correctly."
            ),
            "source_layer": "startup",
            "mechanism": "Repository scan for launcher files and wrapper chains that shell out into other launchers.",
            "root_cause": "The project appears to have accumulated multiple startup paths without a clear canonical boot flow.",
            "evidence_refs": [str(path) for path in startup_files[:3]] + wrapper_sites[:4],
            "confidence": 0.74,
            "fix_type": "architecture_change",
            "recommended_fix": (
                "Choose one canonical startup path for development and one for background/service operation. "
                "Reduce wrapper layers and document the exact order in which launchers delegate to each other."
            ),
        }
    )
    return findings
