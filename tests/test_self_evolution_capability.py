from __future__ import annotations

from pathlib import Path

from hermescheck.audit import run_audit
from hermescheck.config import AuditConfig
from hermescheck.scanners.self_evolution_capability import scan_self_evolution_capability


def _titles(findings: list[dict]) -> list[str]:
    return [finding["title"] for finding in findings]


def test_self_evolution_flags_agent_runtime_without_learning_loop(tmp_path: Path) -> None:
    (tmp_path / "agent.py").write_text(
        "\n".join(
            [
                "class AgentRuntime:",
                "    def agent_loop(self, message):",
                "        self.memory.remember(message)",
                "        self.scheduler.enqueue(self.tool_call(message))",
                "        return self.llm.generate(message)",
            ]
        ),
        encoding="utf-8",
    )

    findings = scan_self_evolution_capability(tmp_path)

    assert "Agent lacks self-evolution capability" in _titles(findings)


def test_self_evolution_flags_learning_without_constraint_fit(tmp_path: Path) -> None:
    (tmp_path / "evolution.md").write_text(
        "\n".join(
            [
                "Agent runtime: agent loop, tool_call, memory, scheduler, LLM.",
                "External signal intake watches upstream projects, issues, PRs, benchmarks, and user feedback.",
                "Source-level learning reads the directory tree, entrypoint, main loop, core class, ADR, and design doc.",
                "Pattern extraction turns each design pattern into a reusable pattern, not a code copy.",
                "Every change ends with a verification loop, regression test, smoke test, acceptance, and retro.",
            ]
        ),
        encoding="utf-8",
    )

    findings = scan_self_evolution_capability(tmp_path)

    assert "Evolution process lacks constraint adaptation" in _titles(findings)


def test_self_evolution_flags_learning_without_verification(tmp_path: Path) -> None:
    (tmp_path / "evolution.md").write_text(
        "\n".join(
            [
                "Agent runtime: agent loop, tool_call, memory, scheduler, LLM.",
                "External signal screening watches reference projects and production logs.",
                "Source reading covers entrypoint, main loop, core class, decision record, and boundary analysis.",
                "Pattern extraction keeps reusable design patterns, not copied code.",
                "Constraint adaptation checks local constraints, zero heavy dependencies, lightweight fit, and 2GB RAM.",
                "Small-step landing uses an independent module, try/except, fail-soft integration, and rollback.",
            ]
        ),
        encoding="utf-8",
    )

    findings = scan_self_evolution_capability(tmp_path)

    assert "Evolution loop lacks verification closure" in _titles(findings)


def test_self_evolution_accepts_closed_loop_methodology(tmp_path: Path) -> None:
    (tmp_path / "evolution.md").write_text(
        "\n".join(
            [
                "Agent runtime: agent loop, tool_call, memory, scheduler, LLM.",
                "External signal intake watches upstream projects, issues, PRs, benchmarks, and user feedback.",
                "Source-level learning reads the directory tree, entrypoint, main loop, core class, ADR, and design doc.",
                "Pattern extraction turns each design pattern into a reusable pattern, not a code copy.",
                "Constraint adaptation checks local constraints, zero heavy dependencies, lightweight fit, and 2GB RAM.",
                "Small-step landing uses an independent module, try/except, fail-soft integration, and rollback.",
                "Every change ends with a verification loop, regression test, smoke test, acceptance, and retro.",
                "The new capability must pass a hands-on live tool call against a real endpoint before it is accepted.",
                "After manual acceptance, the lesson is crystallized into a methodology artifact, procedure skill, and impression fragment.",
            ]
        ),
        encoding="utf-8",
    )

    assert scan_self_evolution_capability(tmp_path) == []


def test_self_evolution_flags_learning_without_hands_on_validation(tmp_path: Path) -> None:
    (tmp_path / "evolution.md").write_text(
        "\n".join(
            [
                "Agent runtime: agent loop, tool_call, memory, scheduler, LLM.",
                "External signal intake watches upstream projects, issues, PRs, benchmarks, and user feedback.",
                "Source-level learning reads the directory tree, entrypoint, main loop, core class, ADR, and design doc.",
                "Pattern extraction turns each design pattern into a reusable pattern, not a code copy.",
                "Constraint adaptation checks local constraints, zero heavy dependencies, lightweight fit, and 2GB RAM.",
                "Small-step landing uses an independent module, try/except, fail-soft integration, and rollback.",
                "Every change ends with a verification loop, regression test, smoke test, acceptance, and retro.",
                "After acceptance, the lesson is crystallized into a methodology artifact, procedure skill, and impression fragment.",
            ]
        ),
        encoding="utf-8",
    )

    findings = scan_self_evolution_capability(tmp_path)

    assert "Learning loop lacks hands-on validation" in _titles(findings)


def test_self_evolution_flags_learning_without_assetization(tmp_path: Path) -> None:
    (tmp_path / "evolution.md").write_text(
        "\n".join(
            [
                "Agent runtime: agent loop, tool_call, memory, scheduler, LLM.",
                "External signal intake watches upstream projects, issues, PRs, benchmarks, and user feedback.",
                "Source-level learning reads the directory tree, entrypoint, main loop, core class, ADR, and design doc.",
                "Pattern extraction turns each design pattern into a reusable pattern, not a code copy.",
                "Constraint adaptation checks local constraints, zero heavy dependencies, lightweight fit, and 2GB RAM.",
                "Small-step landing uses an independent module, try/except, fail-soft integration, and rollback.",
                "Every change ends with a verification loop, regression test, smoke test, acceptance, and retro.",
                "The new capability must pass a hands-on live tool call against a real endpoint before it is accepted.",
            ]
        ),
        encoding="utf-8",
    )

    findings = scan_self_evolution_capability(tmp_path)

    assert "Learning loop lacks reusable assetization" in _titles(findings)


def test_self_evolution_scanner_is_enabled_in_personal_audits(tmp_path: Path) -> None:
    (tmp_path / "agent.py").write_text(
        "\n".join(
            [
                "class AgentRuntime:",
                "    def agent_loop(self, message):",
                "        self.memory.remember(message)",
                "        self.scheduler.enqueue(self.tool_call(message))",
                "        return self.llm.generate(message)",
            ]
        ),
        encoding="utf-8",
    )

    results = run_audit(str(tmp_path), config=AuditConfig.from_profile("personal"), verbose=False)

    assert "Agent lacks self-evolution capability" in _titles(results["findings"])
