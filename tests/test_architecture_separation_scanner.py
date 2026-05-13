from __future__ import annotations

from pathlib import Path

from hermescheck.audit import run_audit
from hermescheck.config import AuditConfig
from hermescheck.scanners.architecture_separation import scan_architecture_separation


def _titles(findings: list[dict]) -> list[str]:
    return [finding["title"] for finding in findings]


def test_architecture_separation_flags_missing_long_task_stream_split(tmp_path: Path) -> None:
    (tmp_path / "feishu_adapter.py").write_text(
        "\n".join(
            [
                "class FeishuAdapter:",
                "    def update_message(self, task):",
                "        # Long-running agent task edits the same rich-text message with every tool_call chunk.",
                "        self.client.patch_rich_text(task.message_id, task.status)",
                "        # Memory, skills, session history, and archive are all loaded together.",
                "        self.memory.append(task.session_history)",
                "        self.skills.append(task.archive)",
                "        task.archive.save(task.memory)",
            ]
        ),
        encoding="utf-8",
    )

    findings = scan_architecture_separation(tmp_path)
    titles = _titles(findings)

    assert "Long-running channel output lacks stream separation" in titles
    assert "Knowledge authority boundary is unclear" in titles


def test_architecture_separation_flags_ungoverned_self_evolution(tmp_path: Path) -> None:
    (tmp_path / "skill_evolve.md").write_text(
        "\n".join(
            [
                "# Skill evolution",
                "The agent can self-evolve skills after post-turn reflection.",
                "It may auto-apply improvements to memory and skills during the next run.",
                "Sidecar telemetry and subagent workers observe the result.",
            ]
        ),
        encoding="utf-8",
    )

    findings = scan_architecture_separation(tmp_path)
    titles = _titles(findings)

    assert "Self-evolution lacks proposal and rollback governance" in titles
    assert "Runtime sidecars lack primary-path boundary" in titles


def test_architecture_separation_accepts_how_to_agent_style_boundaries(tmp_path: Path) -> None:
    (tmp_path / "ARCHITECTURE.md").write_text(
        "\n".join(
            [
                "# Agent runtime architecture",
                "Feishu long-running tasks use a progress stream plus a conclusion stream.",
                "An append-only event trail stores tool milestones.",
                "Current facts are active memory; session history is not default instruction memory.",
                "Cold archive records are searchable archives loaded only on demand.",
                "Self-evolution uses proposal, evidence, risk classification, validation plan, rollback plan,",
                "apply gate, human gate, and post-change audit.",
                "There is one primary runtime path. Telemetry and audit sidecars are bounded, non-blocking,",
                "and fail-soft optional helpers.",
                "Dependabot dependency alerts are handled by blast radius: runtime dependencies first,",
                "bridge next, website docs last, closest available test, patched version, scanner lag.",
                "Completion evidence includes tests passed, live service running, working tree clean,",
                "origin/main...main = 0 0, and next agent can find the handoff.",
            ]
        ),
        encoding="utf-8",
    )

    assert scan_architecture_separation(tmp_path) == []


def test_architecture_separation_registered_in_personal_audit(tmp_path: Path) -> None:
    (tmp_path / "adapter.py").write_text(
        "\n".join(
            [
                "# agent loop with Feishu rich-text message update",
                "def render(task):",
                "    return task.memory + task.session_history + task.rich_text_status",
            ]
        ),
        encoding="utf-8",
    )

    results = run_audit(str(tmp_path), config=AuditConfig.from_profile("personal"), verbose=False)

    assert "architecture_separation" in results["scope"]["layers_to_audit"] or any(
        finding["source_layer"] == "architecture_separation" for finding in results["findings"]
    )
