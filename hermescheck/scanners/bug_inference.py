"""Infer likely runtime bugs from static source patterns."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from hermescheck.scanners.path_filters import iter_source_files, should_skip_path

SCAN_EXTENSIONS = {".py", ".ts", ".js", ".mjs", ".cjs", ".tsx", ".jsx"}
SKIP_DIRS = {".git", ".github", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "coverage"}
MAX_FILE_BYTES = 300_000

ROOT_REPAIR_SCRIPT_RE = re.compile(r"^(?:fix|patch|repair|hotfix|tmp|temp)\d*\.py$", re.IGNORECASE)
MUTATING_REPAIR_RE = re.compile(
    r"\b(?:content\.replace|\.replace\s*\(|write_text\s*\(|open\s*\([^)]*['\"]w|fs\.writeFileSync|"
    r"renameSync|copyFileSync)\b"
)
SOURCE_TARGET_RE = re.compile(r"['\"](?:src|ui|extensions|packages|scripts)/[^'\"]+['\"]")

DYNAMIC_IMPORT_RE = re.compile(r"\bimport\s*\(\s*([^)]{1,180})\)")
SAFE_DYNAMIC_IMPORT_HINT_RE = re.compile(r"\b(?:pathToFileURL|fileURLToPath|import\.meta\.resolve)\b")
PATH_LIKE_HINT_RE = re.compile(r"(?:path|file|filename|entry|script|bundle|resolved|absolute|join|resolve)", re.I)

SET_TIMEOUT_RE = re.compile(r"\bsetTimeout\s*\(")
NUMERIC_TIMEOUT_RE = re.compile(r"\bsetTimeout\s*\(.*,\s*[0-9_]+(?:\s*[),;])")
DELAY_LIKE_RE = re.compile(r"(?:delay|timeout|interval|ttl|duration|ms|seconds|minutes|nextRun|wait)", re.I)
TIMER_GUARD_RE = re.compile(
    r"\b(?:Math\.min|Math\.max|clamp|MAX_TIMEOUT|MAX_DELAY|setTimeout cap|timerDelay|safeDelay)\b"
)
TIMER_CAP_RISK_RE = re.compile(
    r"(?:heartbeat|cron|schedul|deadline|until|nextRun|expire|expiry|refreshAt|-\s*now|hours?|days?)", re.I
)
SHORT_UI_TIMER_RE = re.compile(r"(?:debounce|animation|transition|tooltip|scroll|render|search)", re.I)


def _should_skip(path: Path) -> bool:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return True
    except OSError:
        return True
    return should_skip_path(path, SKIP_DIRS)


def _read_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except (OSError, PermissionError):
        return []


def _line_ref(path: Path, lineno: int) -> str:
    return f"{path}:{lineno}"


def _is_test_path(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    name = path.name.lower()
    return (
        "test" in parts
        or "tests" in parts
        or "test-support" in parts
        or "__tests__" in parts
        or ".test." in name
        or ".spec." in name
    )


def _nearby_has(lines: list[str], lineno: int, pattern: re.Pattern[str], *, radius: int = 4) -> bool:
    start = max(1, lineno - radius)
    end = min(len(lines), lineno + radius)
    return any(pattern.search(lines[index - 1]) for index in range(start, end + 1))


def _scan_root_repair_scripts(target: Path) -> list[dict[str, Any]]:
    if not target.is_dir():
        return []

    evidence: list[str] = []
    for fp in sorted(target.iterdir()):
        if not fp.is_file() or not ROOT_REPAIR_SCRIPT_RE.match(fp.name):
            continue
        lines = _read_lines(fp)
        if not lines:
            continue
        joined = "\n".join(lines)
        if not (MUTATING_REPAIR_RE.search(joined) and SOURCE_TARGET_RE.search(joined)):
            continue
        for lineno, line in enumerate(lines, start=1):
            if MUTATING_REPAIR_RE.search(line) or SOURCE_TARGET_RE.search(line):
                evidence.append(_line_ref(fp, lineno))
                break

    if not evidence:
        return []

    return [
        {
            "severity": "high",
            "title": "Tracked one-off repair script can hide stale bugfix state",
            "symptom": (
                f"Found {len(evidence)} root-level fix/patch-style script(s) that mutate source files directly."
            ),
            "user_impact": (
                "One-off repair scripts left in the repo root make it unclear whether the source tree is already "
                "fixed, whether the script must still be run, or whether future contributors should copy the patch pattern."
            ),
            "source_layer": "bug_inference",
            "mechanism": "Root-level fix/patch script names combined with direct source-file mutation patterns.",
            "root_cause": "Temporary remediation logic appears to be tracked beside normal entrypoints instead of being removed or documented as a migration.",
            "evidence_refs": evidence[:8],
            "confidence": 0.78,
            "fix_type": "code_change",
            "recommended_fix": (
                "Delete stale one-off repair scripts, or move still-needed migrations under a documented scripts/migrations "
                "path with idempotency checks, tests, and a clear invocation contract."
            ),
        }
    ]


def _scan_dynamic_import_paths(files: list[Path]) -> list[dict[str, Any]]:
    evidence: list[str] = []
    for fp in files:
        if fp.suffix not in {".ts", ".js", ".mjs", ".cjs", ".tsx", ".jsx"}:
            continue
        if _is_test_path(fp):
            continue
        if "ui" in {part.lower() for part in fp.parts}:
            continue
        lines = _read_lines(fp)
        if not lines:
            continue
        joined = "\n".join(lines)
        if SAFE_DYNAMIC_IMPORT_HINT_RE.search(joined):
            continue
        for lineno, line in enumerate(lines, start=1):
            match = DYNAMIC_IMPORT_RE.search(line)
            if not match:
                continue
            arg = match.group(1).strip()
            if arg.startswith(("'", '"', "`")):
                continue
            if "new URL" in arg:
                continue
            if re.fullmatch(r"[A-Z0-9_]+", arg) and not re.search(r"(?:PATH|FILE|ENTRY|SCRIPT|BUNDLE)", arg):
                continue
            if PATH_LIKE_HINT_RE.search(arg) or PATH_LIKE_HINT_RE.search(line):
                evidence.append(_line_ref(fp, lineno))
                break

    if not evidence:
        return []

    return [
        {
            "severity": "medium",
            "title": "Dynamic import may receive filesystem path without file URL normalization",
            "symptom": (
                f"Found {len(evidence)} dynamic import site(s) that appear to import path-like variables without "
                "nearby pathToFileURL normalization."
            ),
            "user_impact": (
                "On Windows, passing an absolute path such as C:\\... directly to the ESM loader can fail with an "
                "unsupported protocol error; similar loader ambiguity can also affect generated plugin/module paths."
            ),
            "source_layer": "bug_inference",
            "mechanism": "Static scan for import(variable) path-like call sites without file URL conversion helpers in the same file.",
            "root_cause": "Filesystem paths and module specifiers are treated as interchangeable at dynamic import boundaries.",
            "evidence_refs": evidence[:10],
            "confidence": 0.7,
            "fix_type": "code_change",
            "recommended_fix": (
                "Normalize filesystem paths with pathToFileURL(...).href before dynamic import, and add a Windows-path "
                "regression test for plugin, channel, or generated module loading."
            ),
        }
    ]


def _scan_unbounded_timers(files: list[Path]) -> list[dict[str, Any]]:
    evidence: list[str] = []
    for fp in files:
        if fp.suffix not in {".ts", ".js", ".mjs", ".cjs", ".tsx", ".jsx"}:
            continue
        if _is_test_path(fp):
            continue
        if "ui" in {part.lower() for part in fp.parts}:
            continue
        lines = _read_lines(fp)
        if not lines:
            continue
        for lineno, line in enumerate(lines, start=1):
            if not SET_TIMEOUT_RE.search(line):
                continue
            if NUMERIC_TIMEOUT_RE.search(line):
                continue
            if not DELAY_LIKE_RE.search(line):
                continue
            context = "\n".join(lines[max(0, lineno - 4) : min(len(lines), lineno + 4)])
            if SHORT_UI_TIMER_RE.search(context) and not TIMER_CAP_RISK_RE.search(context):
                continue
            if not TIMER_CAP_RISK_RE.search(f"{fp}\n{context}"):
                continue
            if _nearby_has(lines, lineno, TIMER_GUARD_RE, radius=5):
                continue
            evidence.append(_line_ref(fp, lineno))
            if len(evidence) >= 12:
                break

    if not evidence:
        return []

    return [
        {
            "severity": "medium",
            "title": "Timer delay may exceed runtime setTimeout limits",
            "symptom": (
                f"Found {len(evidence)} setTimeout call(s) using delay-like variables without nearby clamp/cap logic."
            ),
            "user_impact": (
                "Very long scheduler, heartbeat, retry, or timeout values can overflow the JavaScript timer limit and "
                "fire immediately or far earlier than intended, causing stalls, busy loops, or unexpected retries."
            ),
            "source_layer": "bug_inference",
            "mechanism": "Static scan for setTimeout(..., variableDelay) without nearby Math.min/clamp/timerDelay helpers.",
            "root_cause": "Runtime delay values are passed directly to JavaScript timers without a documented maximum cap.",
            "evidence_refs": evidence[:12],
            "confidence": 0.66,
            "fix_type": "code_change",
            "recommended_fix": (
                "Route long delays through a shared timer helper that clamps to the Node/JS setTimeout cap, logs truncation, "
                "and has regression tests for multi-day or extremely large durations."
            ),
        }
    ]


def scan_bug_inference(target: Path) -> List[Dict[str, Any]]:
    files = [fp for fp in iter_source_files(target) if fp.is_file() and not _should_skip(fp)]
    findings: List[Dict[str, Any]] = []
    findings.extend(_scan_root_repair_scripts(target))
    findings.extend(_scan_dynamic_import_paths(files))
    findings.extend(_scan_unbounded_timers(files))
    return findings
