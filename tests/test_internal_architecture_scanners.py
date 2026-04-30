from __future__ import annotations

from pathlib import Path

from hermescheck.audit import run_audit
from hermescheck.config import AuditConfig
from hermescheck.scanners.role_play_orchestration import scan_role_play_orchestration


def _titles(results: dict) -> list[str]:
    return [finding["title"] for finding in results["findings"]]


def test_personal_profile_surfaces_internal_architecture_findings(tmp_path: Path) -> None:
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    (memory_dir / "global_mem_insight.txt").write_text("current routing insight\n", encoding="utf-8")
    (memory_dir / "global_mem_insight_v2.txt").write_text("new routing insight\n", encoding="utf-8")
    (memory_dir / "session_archive.md").write_text("old session archive\n", encoding="utf-8")
    (memory_dir / "checkpoint_state.md").write_text("checkpoint snapshot\n", encoding="utf-8")

    skill_dir = tmp_path / "skills"
    skill_dir.mkdir()
    (skill_dir / "send_email_skill.md").write_text("# Send email skill\n", encoding="utf-8")
    (skill_dir / "send-email-skill-v2.md").write_text("# Send email skill v2\n", encoding="utf-8")
    (skill_dir / "send_email_sop.md").write_text("# Send email SOP\n", encoding="utf-8")

    (tmp_path / "agent_loop.py").write_text(
        "\n".join(
            [
                "def plan_task(task):",
                "    route_to_worker(task)",
                "    schedule_job(task)",
                "    retry_llm(task)",
                "    delegate_to_subagent(task)",
                "    reflect_on_result(task)",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "AGENT_ROLES.md").write_text(
        "\n".join(
            [
                "The PM agent passes work to the architect agent.",
                "The architect agent hands off to the developer agent.",
                "The QA agent reviews the next agent stage in the pipeline chain.",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "launch.py").write_text(
        "import subprocess\nsubprocess.run(['python', '-m', 'app'])\n", encoding="utf-8"
    )
    (tmp_path / "start.sh").write_text("python -m launch\n", encoding="utf-8")
    (tmp_path / "docker-compose.yml").write_text("services:\n  app:\n    image: test\n", encoding="utf-8")
    (tmp_path / "com.example.agent.plist").write_text("<plist></plist>\n", encoding="utf-8")
    (tmp_path / "runtime.py").write_text(
        "\n".join(
            [
                "import fastapi",
                "import streamlit",
                "import celery",
                "import redis",
                "# docker deployment",
                "# langchain agent loop",
            ]
        ),
        encoding="utf-8",
    )

    results = run_audit(
        str(tmp_path),
        config=AuditConfig.from_profile("personal"),
        verbose=False,
    )

    titles = _titles(results)
    assert "Internal orchestration sprawl detected" in titles
    assert "Memory freshness / generation confusion detected" in titles
    assert "Role-play handoff orchestration detected" in titles
    assert "Duplicated skill / SOP artifacts detected" in titles
    assert "Startup surface sprawl detected" in titles
    assert "Runtime surface sprawl detected" in titles


def test_role_play_orchestration_flags_serial_org_chart_agents(tmp_path: Path) -> None:
    (tmp_path / "AGENT_DESIGN.md").write_text(
        "\n".join(
            [
                "# Agent team",
                "The PM agent receives the request and passes it to the architect agent.",
                "The architect agent creates a plan and handoff to the coder agent.",
                "The developer agent transfers to the QA agent in the next agent step.",
                "The reviewer agent then relays findings through the pipeline chain.",
            ]
        ),
        encoding="utf-8",
    )

    findings = scan_role_play_orchestration(tmp_path)

    assert len(findings) == 1
    assert findings[0]["title"] == "Role-play handoff orchestration detected"
    assert findings[0]["severity"] == "medium"


def test_role_play_orchestration_ignores_simple_parallel_subagent_notes(tmp_path: Path) -> None:
    (tmp_path / "DESIGN.md").write_text(
        "\n".join(
            [
                "Use two subagents to inspect independent files.",
                "The main loop keeps the full user intent and merges their evidence.",
                "A reviewer checks the final patch before release.",
            ]
        ),
        encoding="utf-8",
    )

    assert scan_role_play_orchestration(tmp_path) == []
