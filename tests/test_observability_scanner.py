from __future__ import annotations

from pathlib import Path

from hermescheck.maturity import score_maturity
from hermescheck.scanners.observability import scan_observability


def _titles(findings: list[dict]) -> list[str]:
    return [finding["title"] for finding in findings]


def test_observability_flags_missing_runtime_logs(tmp_path: Path) -> None:
    (tmp_path / "agent.py").write_text(
        "\n".join(
            [
                "def run_agent(task):",
                "    result = tool_call(task)",
                "    return result",
            ]
        ),
        encoding="utf-8",
    )

    findings = scan_observability(tmp_path)

    assert "Missing observability/tracing system" in _titles(findings)


def test_observability_flags_logs_without_evidence_or_handoff(tmp_path: Path) -> None:
    (tmp_path / "agent.py").write_text(
        "\n".join(
            [
                "import logging",
                "logger = logging.getLogger(__name__)",
                "def run_agent(task):",
                "    logger.info('tool call started')",
                "    heartbeat.tick()",
                "    return tool_call(task)",
            ]
        ),
        encoding="utf-8",
    )

    findings = scan_observability(tmp_path)
    titles = _titles(findings)

    assert "Runtime logs lack before/after evidence" in titles
    assert "Operational handoff/workbook habit missing" in titles
    assert "Missing observability/tracing system" not in titles


def test_observability_accepts_logs_evidence_and_handoff(tmp_path: Path) -> None:
    (tmp_path / "agent.py").write_text(
        "\n".join(
            [
                "import logging",
                "logger = logging.getLogger(__name__)",
                "def run_agent(task):",
                "    before_snapshot = capture_state()",
                "    result = run_tool(task)",
                "    audit_log.record(before_after=(before_snapshot, capture_state()), stdout=result.stdout, stderr=result.stderr, exit_code=result.returncode)",
                "    smoke_test_result = run_smoke_test()",
                "    return smoke_test_result",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "HANDOFF.md").write_text(
        "\n".join(
            [
                "# Agent Handoff",
                "Startup command: python agent.py",
                "Logs: audit_log.jsonl",
                "Validation: run smoke_test and capture before/after evidence.",
            ]
        ),
        encoding="utf-8",
    )

    assert scan_observability(tmp_path) == []


def test_maturity_score_rewards_evidence_and_handoff(tmp_path: Path) -> None:
    (tmp_path / "ops.md").write_text(
        "\n".join(
            [
                "methodology: operational evidence rubric",
                "runtime logger writes audit_log and event_log with heartbeat and status_update.",
                "Each action stores before_after evidence, changed_files, commands_run, stdout, stderr, exit_code, smoke_test, and health_check.",
                "HANDOFF runbook and work_manual document startup, restart, log locations, validation commands, and known traps.",
            ]
        ),
        encoding="utf-8",
    )

    score = score_maturity(tmp_path, findings=[])

    assert "traces/evals" in score["strengths"]
    assert "before/after evidence logging" in score["strengths"]
    assert "handoff/workbook habit" in score["strengths"]
