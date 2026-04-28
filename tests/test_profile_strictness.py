from __future__ import annotations

from pathlib import Path

from hermescheck.audit import run_audit
from hermescheck.config import AuditConfig


def _finding(results: dict, title_prefix: str) -> dict:
    return next(finding for finding in results["findings"] if finding["title"].startswith(title_prefix))


def test_personal_profile_relaxes_common_prototyping_findings(tmp_path: Path) -> None:
    (tmp_path / "agent.py").write_text(
        "\n".join(
            [
                "import subprocess",
                "history = []",
                "history.append(user_message)",
                "subprocess.run(command, shell=True)",
            ]
        ),
        encoding="utf-8",
    )

    results = run_audit(
        str(tmp_path),
        config=AuditConfig.from_profile("personal"),
        verbose=False,
    )

    code_exec = _finding(results, "Unsafe code execution:")
    memory_growth = _finding(results, "Memory growth without apparent limit")
    observability = _finding(results, "Missing observability/tracing system")

    assert code_exec["severity"] == "medium"
    assert "untrusted input" in code_exec["recommended_fix"].lower()
    assert memory_growth["severity"] == "low"
    assert observability["severity"] == "low"
    assert results["executive_verdict"]["overall_health"] == "acceptable"


def test_enterprise_profile_treats_static_code_execution_as_medium_risk(tmp_path: Path) -> None:
    (tmp_path / "agent.py").write_text(
        "import subprocess\nsubprocess.run(command, shell=True)\n",
        encoding="utf-8",
    )

    results = run_audit(
        str(tmp_path),
        config=AuditConfig.from_profile("enterprise"),
        verbose=False,
    )

    code_exec = _finding(results, "Unsafe code execution:")
    assert code_exec["severity"] == "medium"
    assert "path scopes" in code_exec["recommended_fix"].lower()
    assert results["executive_verdict"]["overall_health"] == "unstable"
