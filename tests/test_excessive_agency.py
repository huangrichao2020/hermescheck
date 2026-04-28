from __future__ import annotations

from pathlib import Path

from hermescheck.audit import run_audit
from hermescheck.config import AuditConfig


def _titles(results: dict) -> list[str]:
    return [finding["title"] for finding in results["findings"]]


def test_personal_profile_skips_approval_sandbox_allowlist_requirements(tmp_path: Path) -> None:
    (tmp_path / "agent.py").write_text(
        "import subprocess\nsubprocess.run(command, shell=True)\n",
        encoding="utf-8",
    )

    results = run_audit(
        str(tmp_path),
        config=AuditConfig.from_profile("personal"),
        verbose=False,
    )

    assert "Privileged agent capabilities lack enterprise controls" not in _titles(results)


def test_enterprise_profile_requires_two_control_categories(tmp_path: Path) -> None:
    (tmp_path / "agent.py").write_text(
        "\n".join(
            [
                "import subprocess",
                "require_approval(user_request)",
                "subprocess.run(command, shell=True)",
            ]
        ),
        encoding="utf-8",
    )

    results = run_audit(
        str(tmp_path),
        config=AuditConfig.from_profile("enterprise"),
        verbose=False,
    )

    finding = next(
        finding
        for finding in results["findings"]
        if finding["title"] == "Privileged agent capabilities lack enterprise controls"
    )
    assert finding["severity"] == "medium"
    assert "at least two" in finding["recommended_fix"]


def test_enterprise_profile_passes_when_two_controls_exist(tmp_path: Path) -> None:
    (tmp_path / "agent.py").write_text(
        "\n".join(
            [
                "import subprocess",
                "require_approval(user_request)",
                "ALLOWED_COMMANDS = {'ls', 'pwd'}",
                "command = get_safe_command(ALLOWED_COMMANDS)",
                "subprocess.run(command, shell=True)",
            ]
        ),
        encoding="utf-8",
    )

    results = run_audit(
        str(tmp_path),
        config=AuditConfig.from_profile("enterprise"),
        verbose=False,
    )

    assert "Privileged agent capabilities lack enterprise controls" not in _titles(results)
