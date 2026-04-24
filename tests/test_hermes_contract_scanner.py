from __future__ import annotations

from pathlib import Path

from hermescheck.audit import run_audit
from hermescheck.config import AuditConfig
from hermescheck.scanners.hermes_contract import scan_hermes_contract


def _write_minimal_hermes(root: Path) -> Path:
    for relative in (
        "run_agent.py",
        "cli.py",
        "model_tools.py",
        "toolsets.py",
        "tools/registry.py",
        "hermes_state.py",
        "hermes_constants.py",
        "hermes_logging.py",
        "agent/skill_commands.py",
        "gateway/run.py",
        "cron/scheduler.py",
        "hermes_cli/commands.py",
        "skills/example/SKILL.md",
        "optional-skills/example/SKILL.md",
        "gateway/platforms/telegram.py",
        "tools/environments/local.py",
        "plugins/example/README.md",
        "tests/test_smoke.py",
    ):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# hermes fixture\n", encoding="utf-8")
    (root / "hermes_cli" / "commands.py").write_text(
        "\n".join(
            [
                "COMMAND_REGISTRY = []",
                "GATEWAY_KNOWN_COMMANDS = set()",
                "def resolve_command(name): return name",
                "def gateway_help_lines(): return []",
            ]
        ),
        encoding="utf-8",
    )
    (root / "gateway" / "run.py").write_text("from hermes_cli.commands import resolve_command\n", encoding="utf-8")
    return root


def test_hermes_contract_passes_for_complete_checkout_shape(tmp_path: Path) -> None:
    target = _write_minimal_hermes(tmp_path / "hermes-agent")

    assert scan_hermes_contract(target) == []


def test_hermes_contract_flags_partial_hermes_checkout(tmp_path: Path) -> None:
    target = tmp_path / "hermes-agent"
    for relative in ("run_agent.py", "cli.py", "hermes_state.py", "hermes_cli/commands.py"):
        path = target / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# partial hermes checkout\n", encoding="utf-8")

    findings = scan_hermes_contract(target)

    assert findings
    assert findings[0]["title"] == "Hermes Agent core contract is incomplete"


def test_run_audit_includes_hermes_layers_for_hermes_checkout(tmp_path: Path) -> None:
    target = _write_minimal_hermes(tmp_path / "hermes-agent")

    results = run_audit(str(target), config=AuditConfig.from_profile("personal"), verbose=False)

    assert "hermes_runtime_contract" in results["scope"]["layers_to_audit"]
    assert "hermes_command_registry" in results["scope"]["layers_to_audit"]
