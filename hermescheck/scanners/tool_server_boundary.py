"""Scan OpenAPI/MCP remote tool integrations for trust-boundary controls."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from hermescheck.scanners.path_filters import iter_source_files, should_skip_path

SCAN_EXTENSIONS = {".py", ".ts", ".js", ".tsx", ".jsx", ".md", ".yaml", ".yml", ".toml", ".json"}
SKIP_DIRS = {".git", ".github", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "coverage"}
MAX_FILE_BYTES = 250_000

REMOTE_TOOL_RE = re.compile(
    r"\b(?:mcp|model[_ -]?context[_ -]?protocol|openapi|swagger|tool[_ -]?server|remote[_ -]?tool|"
    r"external[_ -]?tool|tool[_ -]?server[_ -]?connections|openapi\.json|/mcp)\b",
    re.IGNORECASE,
)
SPEC_LOADING_RE = re.compile(
    r"\b(?:openapi\.json|swagger\.json|requests\.(?:get|post)|httpx\.(?:get|post)|fetch\s*\(|axios\.|"
    r"load[_ -]?spec|tool[_ -]?manifest|server[_ -]?url|base[_ -]?url)\b",
    re.IGNORECASE,
)
BOUNDARY_POLICY_RE = re.compile(
    r"\b(?:allowlist|denylist|blocklist|trusted[_ -]?servers|allowed[_ -]?(?:servers|tools|hosts)|"
    r"permission|capability|approval|scope|auth|oauth|api[_ -]?key|bearer|timeout|retry[_ -]?budget|"
    r"rate[_ -]?limit|schema[_ -]?validation|jsonschema)\b",
    re.IGNORECASE,
)
PINNING_RE = re.compile(
    r"\b(?:sha256|hash|fingerprint|pinned[_ -]?(?:spec|schema|version)|version[_ -]?pin|etag|"
    r"schema[_ -]?version|lockfile)\b",
    re.IGNORECASE,
)
HIGH_AGENCY_TOOL_RE = re.compile(
    r"\b(?:write[_ -]?file|delete[_ -]?file|shell|terminal|subprocess|exec|browser|playwright|selenium|"
    r"git\s+push|npm\s+publish|docker|kubectl|database|sql|filesystem|network)\b",
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
    refs = {key: [] for key in ("remote_tool", "spec_loading", "boundary_policy", "pinning", "high_agency")}
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
            if REMOTE_TOOL_RE.search(line):
                refs["remote_tool"].append(ref)
            if SPEC_LOADING_RE.search(line):
                refs["spec_loading"].append(ref)
            if BOUNDARY_POLICY_RE.search(line):
                refs["boundary_policy"].append(ref)
            if PINNING_RE.search(line):
                refs["pinning"].append(ref)
            if HIGH_AGENCY_TOOL_RE.search(line):
                refs["high_agency"].append(ref)
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


def scan_tool_server_boundary(target: Path) -> List[Dict[str, Any]]:
    refs = _collect_refs(target)
    if len(refs["remote_tool"]) < 2 and not refs["spec_loading"]:
        return []

    findings: List[Dict[str, Any]] = []
    if len(refs["boundary_policy"]) < 2:
        findings.append(
            {
                "severity": "high",
                "title": "Remote tool server lacks trust-boundary policy",
                "symptom": (
                    f"Detected remote OpenAPI/MCP/tool-server integration with only {len(refs['boundary_policy'])} "
                    "visible boundary policy markers."
                ),
                "user_impact": (
                    "Remote tool servers can change available tools, schemas, and side effects outside the local codebase; "
                    "without a trust policy, the agent may call untrusted or newly expanded capabilities."
                ),
                "source_layer": "tool_server_boundary",
                "mechanism": "Repository scan for MCP/OpenAPI remote tool loading versus auth, allowlist, timeout, and schema controls.",
                "root_cause": "Tool discovery appears to cross a network boundary before the server/tool trust model is explicit.",
                "evidence_refs": _evidence(refs, "remote_tool", "spec_loading", "boundary_policy", "pinning"),
                "confidence": 0.7,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Add a remote-tool boundary: allowed servers/hosts, authentication, per-tool capability policy, "
                    "timeouts and retry budgets, schema validation, and user/admin approval for high-agency tools."
                ),
            }
        )

    if refs["spec_loading"] and not refs["pinning"]:
        findings.append(
            {
                "severity": "medium",
                "title": "Remote tool schema is not pinned or versioned",
                "symptom": "Detected remote tool spec loading without visible schema hash, version, ETag, or lockfile controls.",
                "user_impact": (
                    "An OpenAPI or MCP server can change its schema after review, causing the agent to call tools with "
                    "new arguments or side effects that were never audited."
                ),
                "source_layer": "tool_server_boundary",
                "mechanism": "Repository scan for remote spec loading versus schema pinning/version signals.",
                "root_cause": "The integration appears to trust live tool schemas without a drift-detection mechanism.",
                "evidence_refs": _evidence(refs, "spec_loading", "remote_tool", "pinning"),
                "confidence": 0.66,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Pin remote tool schemas by version, hash, or reviewed snapshot; alert on schema drift before new "
                    "tools or arguments become callable."
                ),
            }
        )

    if refs["high_agency"] and refs["remote_tool"] and not refs["boundary_policy"]:
        findings.append(
            {
                "severity": "critical",
                "title": "High-agency remote tools lack approval boundary",
                "symptom": "Detected remote tool integration near high-agency capability markers without visible approval controls.",
                "user_impact": (
                    "A remote MCP/OpenAPI server can expose file, shell, browser, publish, or database operations that "
                    "the agent may execute as if they were local trusted tools."
                ),
                "source_layer": "tool_server_boundary",
                "mechanism": "Repository scan for remote tool signals near high-agency capabilities and approval policy.",
                "root_cause": "Remote tools appear to inherit trust from the transport rather than from explicit capability review.",
                "evidence_refs": _evidence(refs, "remote_tool", "high_agency", "boundary_policy"),
                "confidence": 0.64,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Require approval or scoped capability grants before remote tools can perform file, shell, browser, "
                    "network, publish, or database side effects."
                ),
            }
        )

    return findings
