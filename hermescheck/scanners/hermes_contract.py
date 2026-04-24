"""Hermes Agent-specific architecture contract checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

HERMES_SENTINELS = (
    "run_agent.py",
    "cli.py",
    "hermes_state.py",
    "model_tools.py",
    "hermes_cli/commands.py",
    "gateway/run.py",
)

HERMES_CORE_FILES = {
    "run_agent.py": "core AIAgent conversation loop",
    "model_tools.py": "tool orchestration and function-call dispatch",
    "toolsets.py": "toolset definitions and core-tool grouping",
    "tools/registry.py": "auto-discovered tool registry",
    "cli.py": "interactive CLI entry point",
    "hermes_cli/commands.py": "central slash-command registry",
    "hermes_state.py": "SQLite session store and full-text recall",
    "hermes_constants.py": "profile-aware Hermes home paths",
    "hermes_logging.py": "profile-aware agent and gateway logging",
    "agent/skill_commands.py": "skill slash-command loader",
    "gateway/run.py": "messaging gateway runtime",
    "cron/scheduler.py": "natural-language scheduled jobs",
}

HERMES_CORE_DIRS = {
    "skills": "built-in skills",
    "optional-skills": "optional skills",
    "gateway/platforms": "messaging platform adapters",
    "tools/environments": "terminal backends",
    "plugins": "plugin system",
    "tests": "regression suite",
}


def _exists(root: Path, relative: str) -> bool:
    return (root / relative).exists()


def _detect_hermes_checkout(target: Path) -> bool:
    if target.is_file():
        return False
    hits = sum(1 for relative in HERMES_SENTINELS if _exists(target, relative))
    return hits >= 3


def _line_ref(path: Path, needle: str) -> str | None:
    try:
        for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
            if needle in line:
                return f"{path}:{lineno}"
    except (OSError, PermissionError):
        return None
    return None


def _command_registry_findings(target: Path) -> list[dict[str, Any]]:
    commands_file = target / "hermes_cli" / "commands.py"
    gateway_file = target / "gateway" / "run.py"
    if not commands_file.exists():
        return []

    refs = [
        ref
        for ref in (
            _line_ref(commands_file, "COMMAND_REGISTRY"),
            _line_ref(commands_file, "GATEWAY_KNOWN_COMMANDS"),
            _line_ref(gateway_file, "resolve_command") if gateway_file.exists() else None,
        )
        if ref
    ]

    try:
        commands_text = commands_file.read_text(encoding="utf-8", errors="ignore")
    except (OSError, PermissionError):
        commands_text = ""

    missing_terms = [
        term
        for term in ("COMMAND_REGISTRY", "GATEWAY_KNOWN_COMMANDS", "resolve_command", "gateway_help_lines")
        if term not in commands_text
    ]
    if not missing_terms:
        return []

    return [
        {
            "severity": "high",
            "title": "Hermes slash-command registry contract drift",
            "symptom": "The central Hermes slash-command registry is missing expected command or gateway helpers.",
            "user_impact": (
                "Hermes commands are shared by the CLI, TUI, gateway, autocomplete, and platform menus. "
                "Registry drift can make a command work in one surface while disappearing in another."
            ),
            "source_layer": "hermes_command_registry",
            "mechanism": "Hermes-specific scan of hermes_cli/commands.py for shared registry helpers.",
            "root_cause": f"Missing registry terms: {', '.join(missing_terms)}.",
            "evidence_refs": refs or [str(commands_file)],
            "confidence": 0.82,
            "fix_type": "architecture_change",
            "recommended_fix": (
                "Keep new slash commands in COMMAND_REGISTRY and derive CLI help, gateway help, platform menus, "
                "and autocomplete from that registry instead of adding surface-specific command lists."
            ),
        }
    ]


def scan_hermes_contract(target: Path) -> List[Dict[str, Any]]:
    """Check Hermes Agent-specific runtime contracts when scanning a Hermes checkout."""

    if not _detect_hermes_checkout(target):
        return []

    findings: List[Dict[str, Any]] = []
    missing_files = [relative for relative in HERMES_CORE_FILES if not _exists(target, relative)]
    missing_dirs = [relative for relative in HERMES_CORE_DIRS if not _exists(target, relative)]

    if missing_files or missing_dirs:
        missing_summary = [
            *(f"{relative} ({HERMES_CORE_FILES[relative]})" for relative in missing_files),
            *(f"{relative}/ ({HERMES_CORE_DIRS[relative]})" for relative in missing_dirs),
        ]
        severity = "critical" if len(missing_files) >= 3 else "high"
        findings.append(
            {
                "severity": severity,
                "title": "Hermes Agent core contract is incomplete",
                "symptom": "This looks like a Hermes Agent checkout, but required runtime surfaces are missing.",
                "user_impact": (
                    "Hermes depends on a connected runtime: agent loop, tool registry, CLI, gateway, sessions, "
                    "skills, scheduled jobs, and profile-aware storage. Missing surfaces usually mean a fork, "
                    "packaging step, or partial checkout cannot exercise the full agent."
                ),
                "source_layer": "hermes_runtime_contract",
                "mechanism": "Hermes-specific file and directory contract scan.",
                "root_cause": (
                    "The checkout does not contain every Hermes runtime surface expected by hermescheck: "
                    + "; ".join(missing_summary)
                ),
                "evidence_refs": [str(target / relative) for relative in [*missing_files, *missing_dirs]][:12],
                "confidence": 0.9,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Restore the missing Hermes surfaces or document why the fork intentionally excludes them. "
                    "For upstream PRs, keep changes compatible with the main loop, command registry, gateway, "
                    "skills, cron, and SessionDB rather than validating only a single interface."
                ),
            }
        )

    findings.extend(_command_registry_findings(target))
    return findings
