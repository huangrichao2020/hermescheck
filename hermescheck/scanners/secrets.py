"""Scan for hardcoded secrets, API keys, and credentials."""

import re
from pathlib import Path
from typing import Any, Dict, List

# Precompiled patterns
SECRET_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9]{20,}", re.IGNORECASE),  # OpenAI
    re.compile(r"ghp_[a-zA-Z0-9]{36}", re.IGNORECASE),  # GitHub
    re.compile(r"glpat-[a-zA-Z0-9]{20,}", re.IGNORECASE),  # GitLab
    re.compile(r"AKIA[0-9A-Z]{16}", re.IGNORECASE),  # AWS access key
    re.compile(r"(?i)(?:api[_-]?key|apikey|secret[_-]?key|token)\s*[=:]\s*['\"]([a-zA-Z0-9+/]{20,}={0,2})['\"]"),
]

SKIP_LINE_RE = re.compile(r"(?:example|your_|placeholder|xxx|test)", re.IGNORECASE)
FAKE_SECRET_RE = re.compile(
    r"(?:"
    r"sk-(?:123|abc|test|fake|dummy|example|x{4,})[a-z0-9_-]*|"
    r"dapi(?:123|abc|test|fake|dummy|example)[a-z0-9_-]*|"
    r"akia(?:0{8,}|1{8,}|6{8,}|test|fake|dummy|example)[a-z0-9_-]*|"
    r"gAAAAABinvalid[a-z0-9_-]*|"
    r"(?:1234567890|abcdef){2,}"
    r")",
    re.IGNORECASE,
)
PUBLIC_CLIENT_KEY_RE = re.compile(
    r"(?:algolia|docsearch|search).*api[_-]?key|api[_-]?key.*(?:algolia|docsearch|search)|"
    r"(?:next_public|vite_|public_|publishable)",
    re.IGNORECASE | re.DOTALL,
)
FIXTURE_PATH_HINTS = {
    "__fixtures__",
    "__snapshots__",
    "cassette",
    "cassettes",
    "fixture",
    "fixtures",
    "recording",
    "recordings",
    "snapshots",
    "vcr_cassettes",
}

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}

SCAN_EXTENSIONS = {".py", ".ts", ".js", ".json", ".yaml", ".yml", ".env", ".toml", ".txt", ".md"}


def _should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def _is_scan_target(path: Path) -> bool:
    return path.suffix in SCAN_EXTENSIONS


def _looks_like_fixture_path(path: Path) -> bool:
    lowered_parts = {part.lower() for part in path.parts}
    return bool(lowered_parts & FIXTURE_PATH_HINTS)


def _match_text(match: re.Match[str]) -> str:
    if match.groups():
        for group in match.groups():
            if group:
                return group
    return match.group(0)


def _looks_like_public_or_fake_secret(path: Path, line: str, context: str, match: re.Match[str]) -> bool:
    matched_text = _match_text(match)
    if FAKE_SECRET_RE.search(matched_text) or FAKE_SECRET_RE.search(line):
        return True
    if PUBLIC_CLIENT_KEY_RE.search(context):
        return True
    if _looks_like_fixture_path(path):
        return True
    return False


def scan_secrets(target: Path) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []

    if target.is_file():
        files = [target]
    else:
        files = sorted(target.rglob("*"))

    for fp in files:
        if not fp.is_file() or _should_skip(fp) or not _is_scan_target(fp):
            continue

        try:
            lines = fp.read_text(encoding="utf-8", errors="ignore").splitlines()
        except (OSError, PermissionError):
            continue

        for lineno, line in enumerate(lines, start=1):
            if SKIP_LINE_RE.search(line):
                continue

            for pat in SECRET_PATTERNS:
                m = pat.search(line)
                if m:
                    start = max(0, lineno - 4)
                    end = min(len(lines), lineno + 3)
                    context = "\n".join(lines[start:end])
                    if _looks_like_public_or_fake_secret(fp, line, context, m):
                        continue
                    findings.append(
                        {
                            "severity": "critical",
                            "title": "Hardcoded secret or API key detected",
                            "symptom": f"Secret pattern found at {fp.name}:{lineno}: {line.strip()[:80]}",
                            "user_impact": "Exposed credentials can be stolen from version control or file dumps, leading to unauthorized access and billing abuse.",
                            "source_layer": "secrets_management",
                            "mechanism": f"Regex match for pattern: {pat.pattern}",
                            "root_cause": "Credentials hardcoded in source instead of using environment variables or a secrets manager.",
                            "evidence_refs": [f"{fp}:{lineno}"],
                            "confidence": 0.9,
                            "fix_type": "code_change",
                            "recommended_fix": "Move credential to environment variable or secrets manager (e.g., AWS Secrets Manager, Doppler). Add pre-commit hook to block secret commits.",
                        }
                    )
                    break  # one finding per line

    return findings
