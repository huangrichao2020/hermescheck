"""Scan for observability, evidence logs, and handoff/workbook habits."""

import re
from pathlib import Path
from typing import Any, Dict, List

from hermescheck.scanners.path_filters import iter_source_files, should_skip_path

# Precompiled patterns
OBSERVABILITY_RE = re.compile(
    r"(?:langsmith|langfuse|opentelemetry|arize|phoenix|"
    r"callback.*handler|tracer|telemetry|observ|"
    r"cost.*track|token.*count|latency.*track|"
    r"span.*create|trace.*start|metric.*record|"
    r"logger|logging\.|loguru|structlog|audit[_ -]?log|event[_ -]?log|"
    r"run[_ -]?log|operation[_ -]?log|action[_ -]?log|journal|"
    r"promptlayer|helicone|braintrust|smith\.ai|"
    r"langsmith\.run|langfuse\.track|otel\.|open telemetry)",
    re.IGNORECASE,
)
RUNTIME_LOG_RE = re.compile(
    r"\b(?:logger|logging\.|loguru|structlog|console\.(?:log|error|warn)|print\(|"
    r"audit[_ -]?log|event[_ -]?log|run[_ -]?log|operation[_ -]?log|action[_ -]?log|"
    r"journal|trace|tracer|telemetry|span|metric|heartbeat|status[_ -]?update)\b|"
    r"(?:运行日志|审计日志|操作日志|动作日志|事件日志|心跳|状态中转)",
    re.IGNORECASE,
)
EVIDENCE_RE = re.compile(
    r"\b(?:before[_ -]?after|before/after|before\s+and\s+after|evidence|evidence_refs?|"
    r"artifact|artifact_path|changed_files?|commands?_run|stdout|stderr|exit[_ -]?code|"
    r"returncode|diff|patch|snapshot|baseline|verification|verify|smoke[_ -]?test|"
    r"post[_ -]?restart|health[_ -]?check|acceptance)\b|"
    r"(?:前后对比|变更前|变更后|证据|验收|验证|烟测|健康检查|交付物|命令输出|退出码)",
    re.IGNORECASE,
)
HANDOFF_RE = re.compile(
    r"\b(?:handoff|hand[-_ ]?over|runbook|workbook|work[_ -]?manual|operations[_ -]?manual|"
    r"playbook|sop|readme|maintainer[_ -]?notes?|CHANGELOG|WORK_LOG|HANDOFF|"
    r"postmortem|retro|lesson learned)\b|"
    r"(?:交接手册|工作手册|运维手册|接手手册|交接文档|工作日志|复盘|经验沉淀)",
    re.IGNORECASE,
)

SCAN_EXTENSIONS = {".py", ".ts", ".js", ".tsx", ".jsx", ".yaml", ".yml", ".toml", ".txt", ".md", ".json", ".sh"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}


def _should_skip(path: Path) -> bool:
    return should_skip_path(path, SKIP_DIRS)


def _collect_refs(files: list[Path]) -> dict[str, list[str]]:
    refs = {"observability": [], "runtime_log": [], "evidence": [], "handoff": []}
    for fp in files:
        if not fp.is_file() or _should_skip(fp):
            continue
        if fp.suffix not in SCAN_EXTENSIONS:
            continue

        try:
            lines = fp.read_text(encoding="utf-8", errors="ignore").splitlines()
        except (OSError, PermissionError):
            continue

        path_text = str(fp)
        if HANDOFF_RE.search(path_text):
            refs["handoff"].append(f"{fp}:1")

        for lineno, line in enumerate(lines, start=1):
            if OBSERVABILITY_RE.search(line):
                refs["observability"].append(f"{fp}:{lineno}")
            if RUNTIME_LOG_RE.search(line):
                refs["runtime_log"].append(f"{fp}:{lineno}")
            if EVIDENCE_RE.search(line):
                refs["evidence"].append(f"{fp}:{lineno}")
            if HANDOFF_RE.search(line):
                refs["handoff"].append(f"{fp}:{lineno}")
    return {key: value[:8] for key, value in refs.items()}


def _evidence(refs: dict[str, list[str]], *keys: str, limit: int = 8) -> list[str]:
    items: list[str] = []
    for key in keys:
        items.extend(refs.get(key, [])[: max(1, limit // max(1, len(keys)))])
    return items[:limit] or ["(none found)"]


def scan_observability(target: Path) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []

    files = list(iter_source_files(target))
    refs = _collect_refs(files)
    found_any = bool(refs["observability"])
    has_runtime_logs = bool(refs["runtime_log"])
    has_evidence_logs = bool(refs["evidence"])
    has_handoff_habit = bool(refs["handoff"])

    if not found_any and not has_runtime_logs:
        findings.append(
            {
                "severity": "medium",
                "title": "Missing observability/tracing system",
                "symptom": "No observability, tracing, telemetry, or lightweight runtime logging patterns detected in the codebase.",
                "user_impact": (
                    "Without runtime logs, you cannot audit LLM calls, track costs, detect tool-call anomalies, "
                    "or replay agent decisions for incident investigation."
                ),
                "source_layer": "observability",
                "mechanism": (
                    "No match for observability/logging patterns such as LangSmith, Langfuse, OpenTelemetry, "
                    "tracer, telemetry, logger, audit_log, event_log, heartbeat, or status_update."
                ),
                "root_cause": "No observability or runtime logging layer has been added to the agent system.",
                "evidence_refs": _evidence(refs, "observability", "runtime_log"),
                "confidence": 0.8,
                "fix_type": "add_integration",
                "recommended_fix": (
                    "Add an agent observability layer. Start with lightweight structured logs for run_id, turn, "
                    "tool call, stdout/stderr, latency, token/cost counts, heartbeat, and final status. "
                    "For production or shared projects, connect LangSmith, Langfuse, Helicone, or OpenTelemetry."
                ),
            }
        )

    if has_runtime_logs and not has_evidence_logs:
        findings.append(
            {
                "severity": "medium",
                "title": "Runtime logs lack before/after evidence",
                "symptom": "Runtime logging was detected, but no before/after evidence, command result, verification, or artifact capture was found.",
                "user_impact": (
                    "Operators can see that the agent ran, but cannot prove what changed, whether the change worked, "
                    "or how to resume safely after interruption."
                ),
                "source_layer": "observability",
                "mechanism": (
                    "Runtime log signals exist without matching before_after, evidence, changed_files, commands_run, "
                    "stdout/stderr, exit_code, diff, verification, smoke_test, or health_check signals."
                ),
                "root_cause": "The logging layer records activity but not verifiable state transition evidence.",
                "evidence_refs": _evidence(refs, "runtime_log", "evidence"),
                "confidence": 0.78,
                "fix_type": "add_evidence_capture",
                "recommended_fix": (
                    "Extend run logs with before/after evidence: pre-state snapshot, action taken, changed files, "
                    "command stdout/stderr/exit code, post-state health check, and verification artifacts."
                ),
            }
        )

    if (found_any or has_runtime_logs or has_evidence_logs) and not has_handoff_habit:
        findings.append(
            {
                "severity": "medium",
                "title": "Operational handoff/workbook habit missing",
                "symptom": "Agent runtime or evidence logging exists, but no handoff, runbook, SOP, workbook, or work-log habit was detected.",
                "user_impact": (
                    "Even with logs, future maintainers or peer agents may not know startup commands, validation "
                    "commands, state locations, ownership, or how to continue after context loss."
                ),
                "source_layer": "observability",
                "mechanism": (
                    "Observed runtime/evidence signals without matching handoff, runbook, work_manual, playbook, SOP, "
                    "HANDOFF, WORK_LOG, postmortem, or lesson-learned signals."
                ),
                "root_cause": "Operational knowledge remains implicit instead of being converted into a maintainable handbook.",
                "evidence_refs": _evidence(refs, "observability", "runtime_log", "evidence", "handoff"),
                "confidence": 0.76,
                "fix_type": "add_docs",
                "recommended_fix": (
                    "Create or update a handoff/workbook near the changed module. Include purpose, startup/restart "
                    "commands, state/log locations, before/after evidence policy, validation commands, and known traps."
                ),
            }
        )

    return findings
