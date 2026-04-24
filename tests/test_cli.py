from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _write_project(root: Path, code: str) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "agent.py").write_text(code, encoding="utf-8")
    return root


def _cli_env() -> dict[str, str]:
    env = os.environ.copy()
    repo_root = str(Path(__file__).resolve().parents[1])
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = repo_root if not existing else f"{repo_root}{os.pathsep}{existing}"
    return env


def test_cli_accepts_direct_target_path_and_writes_outputs(tmp_path: Path) -> None:
    project = _write_project(
        tmp_path / "project",
        "import subprocess\nsubprocess.run(command, shell=True)\n",
    )
    json_output = tmp_path / "audit.json"
    report_output = tmp_path / "audit.md"
    sarif_output = tmp_path / "audit.sarif.json"

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "hermescheck.cli",
            str(project),
            "--profile",
            "enterprise",
            "-o",
            str(json_output),
            "-r",
            str(report_output),
            "--sarif",
            str(sarif_output),
        ],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env=_cli_env(),
    )

    assert proc.returncode == 0, proc.stderr
    assert json_output.exists()
    assert report_output.exists()
    assert sarif_output.exists()

    data = json.loads(json_output.read_text(encoding="utf-8"))
    assert data["scan_metadata"]["profile"] == "enterprise_production"
    assert data["maturity_score"]["era_name"]

    markdown = report_output.read_text(encoding="utf-8")
    assert "**Architecture Era**" in markdown
    assert "## Architecture Era Score" in markdown


def test_cli_accepts_package_module_entrypoint(tmp_path: Path) -> None:
    project = _write_project(
        tmp_path / "project",
        "print('hello agent')\n",
    )
    json_output = tmp_path / "audit.json"

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "hermescheck",
            str(project),
            "-o",
            str(json_output),
            "-r",
            str(tmp_path / "audit.md"),
            "--quiet",
        ],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env=_cli_env(),
    )

    assert proc.returncode == 0, proc.stderr
    assert json_output.exists()


def test_cli_accepts_target_agent_self_review(tmp_path: Path) -> None:
    project = _write_project(
        tmp_path / "project",
        "print('hello agent')\n",
    )
    self_review = tmp_path / "self_review.json"
    self_review.write_text(
        json.dumps(
            {
                "agent_name": "LocalAgent",
                "summary": "I inspected my own workspace before hermescheck ran.",
                "claims": ["The provider abstraction is intentional."],
                "risks": ["Completion closure can stop too early."],
                "false_positive_notes": ["Provider implementation is not hidden LLM usage."],
                "improvement_plan": ["Add anchor and pointer registration."],
            }
        ),
        encoding="utf-8",
    )
    json_output = tmp_path / "audit.json"
    report_output = tmp_path / "audit.md"

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "hermescheck",
            str(project),
            "--self-review",
            str(self_review),
            "-o",
            str(json_output),
            "-r",
            str(report_output),
            "--quiet",
        ],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env=_cli_env(),
    )

    assert proc.returncode == 0, proc.stderr
    data = json.loads(json_output.read_text(encoding="utf-8"))
    assert data["target_self_review"]["agent_name"] == "LocalAgent"
    assert str(self_review) in data["target_self_review"]["source"]
    assert "Target Agent Self-Review" in report_output.read_text(encoding="utf-8")


def test_cli_can_fail_ci_on_severity_threshold(tmp_path: Path) -> None:
    project = _write_project(
        tmp_path / "project",
        "import subprocess\nsubprocess.run(command, shell=True)\n",
    )

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "hermescheck.cli",
            "audit",
            str(project),
            "--profile",
            "enterprise",
            "--fail-on",
            "high",
        ],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env=_cli_env(),
    )

    assert proc.returncode == 1
