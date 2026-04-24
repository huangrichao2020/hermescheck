from __future__ import annotations

from pathlib import Path

from hermescheck.audit import run_audit
from hermescheck.sarif import generate_sarif


def test_generate_sarif_emits_github_compatible_shape(tmp_path: Path) -> None:
    (tmp_path / "agent.py").write_text(
        "import subprocess\nsubprocess.run(command, shell=True)\n",
        encoding="utf-8",
    )

    report = run_audit(str(tmp_path), verbose=False)
    sarif = generate_sarif(report)

    assert sarif["version"] == "2.1.0"
    assert sarif["runs"]
    run = sarif["runs"][0]
    assert run["tool"]["driver"]["name"] == "hermescheck"
    assert run["results"]
    assert run["results"][0]["level"] in {"error", "warning", "note"}
