"""Main audit orchestrator."""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from hermescheck.config import (
    AuditConfig,
    SEVERITY_ORDER,
    health_mapping_for_profile,
    normalize_finding_for_profile,
)
from hermescheck.maturity import score_maturity
from hermescheck.scanners import ScannerSpec, get_enabled_scanners
from hermescheck.scanners.path_filters import DEFAULT_SKIP_DIRS, should_skip_path
from hermescheck.self_review import normalize_self_review

SEVERITY_BUCKETS = ("critical", "high", "medium", "low")
MODEL_HINTS = ("openai", "anthropic", "gemini", "ollama", "bedrock", "llama")
CHANNEL_HINTS = {
    "cli": ("argparse", "click", "typer"),
    "http_api": ("fastapi", "flask", "express", "router", "app.get(", "app.post("),
    "web": ("react", "next", "vue", "svelte"),
    "slack": ("slack",),
    "discord": ("discord",),
    "telegram": ("telegram",),
}
ENTRYPOINT_NAMES = ("main.py", "app.py", "server.py", "index.js", "main.ts", "server.ts", "cli.py")
SCOPE_SKIP_DIRS = DEFAULT_SKIP_DIRS | {".github"}


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except (OSError, PermissionError):
        return ""


def _skip_scope_path(path: Path) -> bool:
    return should_skip_path(path, SCOPE_SKIP_DIRS)


def _infer_entrypoints(target: Path) -> list[str]:
    if target.is_file():
        return [str(target)]

    candidates = []
    for name in ENTRYPOINT_NAMES:
        for match in sorted(target.rglob(name)):
            if _skip_scope_path(match):
                continue
            candidates.append(str(match))
            if len(candidates) == 5:
                return candidates
    return candidates or [str(target)]


def _infer_channels(target: Path) -> list[str]:
    if target.is_file():
        contents = [_read_text(target)]
    else:
        files = sorted(
            fp
            for fp in target.rglob("*")
            if fp.is_file() and not _skip_scope_path(fp) and fp.suffix in {".py", ".js", ".ts", ".tsx", ".md"}
        )[:50]
        contents = [_read_text(fp) for fp in files]

    combined = "\n".join(contents).lower()
    channels = [
        channel for channel, patterns in CHANNEL_HINTS.items() if any(pattern in combined for pattern in patterns)
    ]
    return channels or ["unknown"]


def _infer_model_stack(target: Path) -> list[str]:
    if target.is_file():
        contents = [_read_text(target)]
    else:
        files = sorted(
            fp
            for fp in target.rglob("*")
            if fp.is_file() and not _skip_scope_path(fp) and fp.suffix in {".py", ".js", ".ts", ".tsx", ".md", ".toml"}
        )[:80]
        contents = [_read_text(fp) for fp in files]

    combined = "\n".join(contents).lower()
    models = [hint for hint in MODEL_HINTS if hint in combined]
    return models or ["unknown"]


def _build_evidence_pack(target: Path, findings: list[dict[str, Any]]) -> list[dict[str, str]]:
    if not findings:
        return [
            {
                "kind": "code",
                "source": "target",
                "location": str(target),
                "summary": "No findings were emitted for the scanned target.",
                "time_scope": "current_state",
            }
        ]

    evidence_pack = []
    for finding in findings[:20]:
        refs = finding.get("evidence_refs") or ["(none found)"]
        evidence_pack.append(
            {
                "kind": "code",
                "source": finding["title"],
                "location": refs[0],
                "summary": finding["symptom"],
                "time_scope": "current_state",
            }
        )
    return evidence_pack


def _build_executive_verdict(
    findings: list[dict[str, Any]],
    severity_summary: dict[str, int],
    *,
    config: AuditConfig,
) -> dict[str, str]:
    top_severity = next((severity for severity in SEVERITY_BUCKETS if severity_summary[severity]), "none")
    top_finding = findings[0] if findings else None
    health_mapping = health_mapping_for_profile(config)
    return {
        "overall_health": health_mapping[top_severity],
        "primary_failure_mode": top_finding["title"] if top_finding else "No significant findings",
        "most_urgent_fix": (top_finding["recommended_fix"] if top_finding else "No immediate action required."),
    }


def _build_conflict_map(self_review: Optional[dict[str, Any]]) -> list[dict[str, str]]:
    if not self_review:
        return []
    normalized = normalize_self_review(self_review)
    return list(normalized.get("conflicts", []))


def _build_fix_plan(findings: list[dict[str, Any]], conflict_map: list[dict[str, str]]) -> list[dict[str, Any]]:
    conflict_steps = [
        {
            "order": index,
            "goal": f"Resolve architecture conflict: {conflict['note']}",
            "why_now": (
                "Target-agent self-review identified "
                f"{conflict['conflict_type']} between {conflict['from_layer']} and {conflict['to_layer']}."
            ),
            "expected_effect": "Removes conflicting, duplicated, or contradictory architecture logic before regex findings.",
        }
        for index, conflict in enumerate(conflict_map, start=1)
    ]
    finding_steps = [
        {
            "order": index + len(conflict_steps),
            "goal": finding["title"],
            "why_now": f"{finding['severity'].upper()} findings should be handled before lower-severity work.",
            "expected_effect": finding.get("recommended_fix", ""),
        }
        for index, finding in enumerate(findings, start=1)
    ]
    return conflict_steps + finding_steps


def run_audit(
    target_path: str,
    *,
    config: Optional[AuditConfig] = None,
    scanners: Optional[list[ScannerSpec]] = None,
    self_review: Optional[dict[str, Any]] = None,
    verbose: bool = True,
) -> dict[str, Any]:
    """Run all enabled scans against the target directory."""

    target = Path(target_path)
    if not target.exists():
        raise FileNotFoundError(f"Target path does not exist: {target_path}")
    if not target.is_dir():
        raise NotADirectoryError(f"Target path is not a directory: {target_path}")

    config = config or AuditConfig.from_profile("personal")
    selected_scanners = scanners or get_enabled_scanners(config)

    if verbose:
        print("\n🔍 Hermes Agent Architecture Audit")
        print(f"   Target: {target_path}")
        print(f"   Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Profile: {config.profile.display_name}\n")

    findings: list[dict[str, Any]] = []
    severity_summary = {severity: 0 for severity in SEVERITY_BUCKETS}
    start = time.time()

    for spec in selected_scanners:
        if verbose:
            print(f"  Scanning: {spec.name}...")
        try:
            for raw_finding in spec.func(target, config):
                finding = normalize_finding_for_profile(raw_finding, config)
                findings.append(finding)
                severity = finding.get("severity", "low")
                if severity in severity_summary:
                    severity_summary[severity] += 1
        except Exception as exc:  # pragma: no cover - defensive logging path
            if verbose:
                print(f"    ⚠️  Error in {spec.name}: {exc}")

    findings.sort(key=lambda finding: SEVERITY_ORDER.get(finding.get("severity", "low"), 99))
    duration = round(time.time() - start, 2)
    total_findings = sum(severity_summary.values())
    audited_layers = []
    for spec in selected_scanners:
        for layer in spec.audited_layers:
            if layer not in audited_layers:
                audited_layers.append(layer)

    normalized_self_review = normalize_self_review(self_review) if self_review else None
    conflict_map = _build_conflict_map(normalized_self_review)

    results = {
        "schema_version": "hermescheck.report.v1",
        "scan_metadata": {
            "profile": config.profile.key,
            "scan_timestamp": datetime.now().isoformat(),
            "scan_duration_seconds": duration,
            "scanner_count": len(selected_scanners),
        },
        "executive_verdict": _build_executive_verdict(findings, severity_summary, config=config),
        "scope": {
            "target_name": str(target),
            "entrypoints": _infer_entrypoints(target),
            "channels": _infer_channels(target),
            "model_stack": _infer_model_stack(target),
            "time_window": "current_state",
            "layers_to_audit": audited_layers or ["tool_execution"],
        },
        "severity_summary": severity_summary,
        "maturity_score": score_maturity(target, findings),
        "evidence_pack": _build_evidence_pack(target, findings),
        "findings": findings,
        "conflict_map": conflict_map,
        "ordered_fix_plan": _build_fix_plan(findings, conflict_map),
    }
    if normalized_self_review:
        results["target_self_review"] = normalized_self_review

    if verbose:
        print(f"\n{'─' * 50}\n✅ Audit complete. Found {total_findings} issues in {duration:.1f}s:")
        for severity in SEVERITY_BUCKETS:
            print(f"   {severity.upper()}: {severity_summary[severity]}")
        print(f"   Overall: {results['executive_verdict']['overall_health']}")
        maturity = results["maturity_score"]
        print(f"   Era: {maturity['era_name']} ({maturity['score']}/100)")

    return results


def save_results(results: dict[str, Any], path: str = "audit_results.json") -> str:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return str(target)
