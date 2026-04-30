from __future__ import annotations

from pathlib import Path

from hermescheck.audit import run_audit
from hermescheck.config import AuditConfig
from hermescheck.schema import validate_report
from hermescheck.scanners.knowledge_consistency import scan_knowledge_consistency


def _titles(findings: list[dict]) -> list[str]:
    return [finding["title"] for finding in findings]


def test_knowledge_consistency_flags_stale_paths_and_relative_time(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "README.md").write_text(
        "\n".join(
            [
                "# Agent",
                "最近 the restart notes moved, but see [old runbook](docs/missing-runbook.md).",
                "The live command is documented in `src/agent_loop.py`.",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "agent_loop.py").write_text("def agent_loop():\n    pass\n", encoding="utf-8")

    findings = scan_knowledge_consistency(tmp_path)

    assert "Documentation references missing local paths" in _titles(findings)
    assert "Durable docs contain relative time language" in _titles(findings)
    assert all(finding["severity"] in {"low", "medium"} for finding in findings)


def test_knowledge_consistency_guides_missing_root_instruction_surface(tmp_path: Path) -> None:
    (tmp_path / "skills").mkdir()
    (tmp_path / "skills" / "restart.md").write_text("# Restart\n", encoding="utf-8")
    (tmp_path / "memory").mkdir()
    (tmp_path / "memory" / "facts.md").write_text("Use layered memory.\n", encoding="utf-8")
    (tmp_path / "agent.py").write_text("def agent_loop():\n    return 'ok'\n", encoding="utf-8")

    findings = scan_knowledge_consistency(tmp_path)

    assert "Knowledge surface inventory is incomplete" in _titles(findings)
    inventory = next(finding for finding in findings if finding["title"] == "Knowledge surface inventory is incomplete")
    assert inventory["severity"] == "low"
    assert "ask the target agent" in inventory["recommended_fix"].lower()


def test_knowledge_consistency_is_enabled_and_schema_valid(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "Today the agent docs reference `docs/missing.md`.\n",
        encoding="utf-8",
    )
    results = run_audit(str(tmp_path), config=AuditConfig.from_profile("personal"), verbose=False)

    assert "knowledge_consistency" in results["scope"]["layers_to_audit"]
    assert "Documentation references missing local paths" in _titles(results["findings"])
    assert validate_report(results) == []
