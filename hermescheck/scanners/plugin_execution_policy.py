"""Scan executable plugin/function systems for sandbox and dependency policy."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from hermescheck.scanners.path_filters import iter_source_files, should_skip_path

SCAN_EXTENSIONS = {".py", ".ts", ".js", ".tsx", ".jsx", ".md", ".yaml", ".yml", ".toml", ".json"}
SKIP_DIRS = {".git", ".github", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "coverage"}
MAX_FILE_BYTES = 250_000

PLUGIN_RE = re.compile(
    r"\b(?:plugin|plugins|function|functions|pipe|valves|user[_ -]?valves|extension|extensions|"
    r"load[_ -]?plugin|plugin[_ -]?loader|dynamic[_ -]?tool|custom[_ -]?tool)\b",
    re.IGNORECASE,
)
DYNAMIC_EXEC_RE = re.compile(
    r"\b(?:exec\s*\(|eval\s*\(|compile\s*\(|importlib|__import__|load_module|module_from_spec|"
    r"exec_module|dynamic[_ -]?import)\b",
    re.IGNORECASE,
)
DEPENDENCY_INSTALL_RE = re.compile(
    r"\b(?:pip\s+install|uv\s+pip\s+install|subprocess\.(?:run|Popen).*pip|requirements|dependencies|"
    r"install[_ -]?requirements|frontmatter)\b",
    re.IGNORECASE,
)
SANDBOX_POLICY_RE = re.compile(
    r"\b(?:sandbox|allowlist|denylist|blocklist|permission|capability|scope|isolat(?:e|ion)|"
    r"container|venv|virtualenv|timeout|resource[_ -]?limit|read[_ -]?scope|write[_ -]?scope)\b",
    re.IGNORECASE,
)
DEPENDENCY_POLICY_RE = re.compile(
    r"\b(?:hash|sha256|pinned|pin|lockfile|allowlisted[_ -]?packages|allowed[_ -]?packages|"
    r"package[_ -]?allowlist|constraints\.txt|requirements\.lock)\b",
    re.IGNORECASE,
)
USER_BOUNDARY_RE = re.compile(
    r"\b(?:admin[_ -]?only|user[_ -]?plugin|tenant|owner|role|rbac|oauth|auth|trusted|untrusted|"
    r"review|approval|enable[_ -]?plugin|disable[_ -]?plugin)\b",
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
    refs = {
        key: []
        for key in ("plugin", "dynamic_exec", "dependency_install", "sandbox", "dependency_policy", "user_boundary")
    }
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
            if PLUGIN_RE.search(line):
                refs["plugin"].append(ref)
            if DYNAMIC_EXEC_RE.search(line):
                refs["dynamic_exec"].append(ref)
            if DEPENDENCY_INSTALL_RE.search(line):
                refs["dependency_install"].append(ref)
            if SANDBOX_POLICY_RE.search(line):
                refs["sandbox"].append(ref)
            if DEPENDENCY_POLICY_RE.search(line):
                refs["dependency_policy"].append(ref)
            if USER_BOUNDARY_RE.search(line):
                refs["user_boundary"].append(ref)
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


def scan_plugin_execution_policy(target: Path) -> List[Dict[str, Any]]:
    refs = _collect_refs(target)
    if len(refs["plugin"]) < 3:
        return []

    findings: List[Dict[str, Any]] = []
    if refs["dynamic_exec"] and len(refs["sandbox"]) < 2:
        findings.append(
            {
                "severity": "critical",
                "title": "Executable plugin system lacks sandbox policy",
                "symptom": (
                    f"Detected executable plugin/function loading with {len(refs['dynamic_exec'])} dynamic execution "
                    f"markers, but only {len(refs['sandbox'])} sandbox or permission policy markers."
                ),
                "user_impact": (
                    "A plugin system that executes arbitrary code can read files, install packages, call networks, or "
                    "mutate state unless it is isolated and capability-scoped."
                ),
                "source_layer": "plugin_execution",
                "mechanism": "Repository scan for plugin/function loaders and dynamic exec/import paths versus sandbox policy signals.",
                "root_cause": "Code-level extensibility appears to be exposed before defining plugin capabilities and isolation.",
                "evidence_refs": _evidence(refs, "dynamic_exec", "plugin", "sandbox", "user_boundary"),
                "confidence": 0.72,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Run executable plugins behind a policy boundary: sandbox or subprocess isolation, timeout/resource "
                    "limits, explicit capabilities, read/write scopes, review/approval, and separate trust levels for "
                    "system, admin, and user plugins."
                ),
            }
        )

    if refs["dependency_install"] and not refs["dependency_policy"]:
        findings.append(
            {
                "severity": "high",
                "title": "Plugin dependency installation lacks supply-chain policy",
                "symptom": "Detected plugin dependency installation or requirements loading without visible pin/hash/allowlist policy.",
                "user_impact": (
                    "Automatic plugin package installation can pull unreviewed or drifting code into the runtime, "
                    "turning a plugin feature into a supply-chain entry point."
                ),
                "source_layer": "plugin_execution",
                "mechanism": "Repository scan for plugin requirements or pip install behavior versus package pinning and allowlist controls.",
                "root_cause": "The plugin loader appears to trust dependency declarations without constraining package provenance.",
                "evidence_refs": _evidence(refs, "dependency_install", "plugin", "dependency_policy"),
                "confidence": 0.69,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Pin plugin dependencies, verify hashes where practical, restrict package names through an allowlist "
                    "for shared deployments, and log dependency installs with plugin identity and reviewer context."
                ),
            }
        )

    return findings
