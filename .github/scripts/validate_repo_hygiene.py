"""Validate repository-level hygiene that keeps hermescheck contribution flow coherent."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKIP_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
}

REQUIRED_PR_TEMPLATE_SECTIONS = [
    "## Mission Alignment",
    "## Contribution Mode",
    "## Layers Changed",
    "## Owner Consent",
    "## Public Safety",
    "## Why This Generalizes",
    "## Evidence",
    "## Validation",
]

TEXT_SUFFIXES = {
    ".md",
    ".py",
    ".yml",
    ".yaml",
    ".json",
    ".toml",
    ".txt",
}


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _validate_json_file(path: str, errors: list[str]) -> dict:
    try:
        return json.loads(_read(path))
    except json.JSONDecodeError as exc:
        errors.append(f"{path} is not valid JSON: {exc}")
    except FileNotFoundError:
        errors.append(f"{path} is missing")
    return {}


def _validate_all_contributors(errors: list[str]) -> None:
    config = _validate_json_file(".all-contributorsrc", errors)
    if not config:
        return

    _require(config.get("projectOwner") == "huangrichao2020", ".all-contributorsrc projectOwner must be huangrichao2020", errors)
    _require(config.get("projectName") == "hermescheck", ".all-contributorsrc projectName must be hermescheck", errors)
    _require("README.md" in config.get("files", []), ".all-contributorsrc must update README.md", errors)
    contributors = config.get("contributors", [])
    _require(bool(contributors), ".all-contributorsrc must include at least one contributor", errors)
    for index, contributor in enumerate(contributors, start=1):
        prefix = f".all-contributorsrc contributor #{index}"
        _require(bool(contributor.get("login")), f"{prefix} must include login", errors)
        _require(bool(contributor.get("name")), f"{prefix} must include name", errors)
        _require(bool(contributor.get("profile")), f"{prefix} must include profile", errors)
        _require(bool(contributor.get("contributions")), f"{prefix} must include contributions", errors)

    readme = _read("README.md")
    for marker in (
        "ALL-CONTRIBUTORS-BADGE:START",
        "ALL-CONTRIBUTORS-BADGE:END",
        "ALL-CONTRIBUTORS-LIST:START",
        "ALL-CONTRIBUTORS-LIST:END",
    ):
        _require(marker in readme, f"README.md is missing All Contributors marker: {marker}", errors)


def _validate_contribution_docs(errors: list[str]) -> None:
    readme = _read("README.md")
    _require(
        "./docs/examples/contribution-examples.md" in readme,
        "README.md must link to docs/examples/contribution-examples.md",
        errors,
    )
    _require(
        (ROOT / "docs/examples/contribution-examples.md").exists(),
        "docs/examples/contribution-examples.md is missing",
        errors,
    )

    for template_path in (
        ".github/pull_request_template.md",
        ".github/PULL_REQUEST_TEMPLATE/self-scan-contribution.md",
        ".github/PULL_REQUEST_TEMPLATE/maintainer-change.md",
    ):
        body = _read(template_path)
        for section in REQUIRED_PR_TEMPLATE_SECTIONS:
            _require(section in body, f"{template_path} is missing {section}", errors)


def _validate_release_config(errors: list[str]) -> None:
    workflow = _read(".github/workflows/ci.yml")
    release_config = _read(".github/release.yml")
    readme = _read("README.md")

    for required in (
        'tags:',
        '"v*"',
        "softprops/action-gh-release",
        "generate_release_notes: true",
        "pypa/gh-action-pypi-publish",
        "contents: write",
        "id-token: write",
    ):
        _require(required in workflow, f".github/workflows/ci.yml must include release setting: {required}", errors)

    for required in (
        "Agent Intelligence Standards",
        "Scanner Signals",
        "Contribution Flow and Governance",
        "CI, Release, and Packaging",
        "Other Changes",
    ):
        _require(required in release_config, f".github/release.yml must include category: {required}", errors)

    _require(
        "./docs/governance/release-process.md" in readme,
        "README.md must link to docs/governance/release-process.md",
        errors,
    )
    _require(
        (ROOT / "docs/governance/release-process.md").exists(),
        "docs/governance/release-process.md is missing",
        errors,
    )


def _validate_schema_json(errors: list[str]) -> None:
    _validate_json_file("hermescheck/schema.json", errors)


def _validate_no_conflict_markers(errors: list[str]) -> None:
    conflict_markers = (
        "<" * 7 + " ",
        "=" * 7 + "\n",
        ">" * 7 + " ",
    )
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for marker in conflict_markers:
            if marker in text:
                errors.append(f"{path.relative_to(ROOT)} contains merge conflict marker {marker.strip()}")


def main() -> int:
    errors: list[str] = []
    _validate_schema_json(errors)
    _validate_all_contributors(errors)
    _validate_contribution_docs(errors)
    _validate_release_config(errors)
    _validate_no_conflict_markers(errors)

    if errors:
        print("Repository hygiene validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Repository hygiene validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
