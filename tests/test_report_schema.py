from __future__ import annotations

from pathlib import Path

from hermescheck.audit import run_audit
from hermescheck.config import AuditConfig
from hermescheck.schema import validate_report


def test_run_audit_produces_schema_valid_report(tmp_path: Path) -> None:
    (tmp_path / "agent.py").write_text(
        "import subprocess\nsubprocess.run(command, shell=True)\n",
        encoding="utf-8",
    )

    results = run_audit(
        str(tmp_path),
        config=AuditConfig.from_profile("enterprise"),
        verbose=False,
    )

    assert validate_report(results) == []
    assert results["schema_version"] == "hermescheck.report.v1"
    assert results["executive_verdict"]["overall_health"] in {
        "critical",
        "high_risk",
        "unstable",
        "acceptable",
        "strong",
    }
    assert results["scope"]["target_name"] == str(tmp_path)
    assert results["scope"]["layers_to_audit"]
    assert results["severity_summary"]["critical"] == 0
    assert results["severity_summary"]["medium"] >= 1
    assert results["evidence_pack"]


def test_run_audit_scope_ignores_dependency_entrypoints(tmp_path: Path) -> None:
    site_package = tmp_path / ".venv" / "lib" / "python3.12" / "site-packages" / "dependency"
    site_package.mkdir(parents=True)
    (site_package / "main.py").write_text("print('dependency')\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("print('project')\n", encoding="utf-8")

    results = run_audit(
        str(tmp_path),
        config=AuditConfig.from_profile("personal"),
        verbose=False,
    )

    assert results["scope"]["entrypoints"] == [str(tmp_path / "app.py")]


def test_run_audit_can_include_target_agent_self_review(tmp_path: Path) -> None:
    (tmp_path / "agent.py").write_text("print('agent')\n", encoding="utf-8")

    results = run_audit(
        str(tmp_path),
        config=AuditConfig.from_profile("personal"),
        self_review={
            "agent_name": "Hermes",
            "summary": "I parse my own source tree and know the router owns tool dispatch.",
            "claims": [{"title": "Router ownership is explicit", "evidence": "src/router.py"}],
            "risks": ["Completion closure is still manual"],
            "false_positive_notes": ["Provider files are intentional"],
            "improvement_plan": [
                {"title": "Add impression cards", "recommendation": "Close file/index/card/pointer loop"}
            ],
        },
        verbose=False,
    )

    assert validate_report(results) == []
    assert results["target_self_review"]["agent_name"] == "Hermes"
    assert results["target_self_review"]["claims"][0]["evidence"] == "src/router.py"
