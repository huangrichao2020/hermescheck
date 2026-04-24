"""Validate pull request body structure for hermescheck governance."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

REQUIRED_HEADINGS = [
    "## Mission Alignment",
    "## Contribution Mode",
    "## Layers Changed",
    "## Validation",
]

SELF_SCAN_HEADINGS = [
    "## Owner Consent",
    "## Public Safety",
    "## Why This Generalizes",
    "## Evidence",
]

PLACEHOLDER_PATTERNS = [
    r"\bTBD\b",
    r"\bTODO\b",
    r"Describe here",
    r"Explain here",
]

SELF_SCAN_TITLE_PREFIX = "[self-scan]"


def _checked(body: str, label: str) -> bool:
    pattern = re.compile(rf"- \[x\] {re.escape(label)}", re.IGNORECASE)
    return bool(pattern.search(body))


def _require_heading(body: str, heading: str, errors: list[str]) -> None:
    if heading not in body:
        errors.append(f"Missing required section: {heading}")


def main() -> int:
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        print("GITHUB_EVENT_PATH is not set.", file=sys.stderr)
        return 1

    payload = json.loads(Path(event_path).read_text(encoding="utf-8"))
    pull_request = payload.get("pull_request") or {}
    body = pull_request.get("body") or ""
    title = pull_request.get("title") or ""
    errors: list[str] = []

    for heading in REQUIRED_HEADINGS:
        _require_heading(body, heading, errors)

    if not (
        _checked(body, "Self-scan contribution")
        or _checked(body, "Maintainer improvement")
        or _checked(body, "Docs or governance change")
    ):
        errors.append("At least one contribution mode checkbox must be checked.")

    if not (
        _checked(body, "Doctrine")
        or _checked(body, "Contract")
        or _checked(body, "Scanner")
        or _checked(body, "Contribution Flow")
        or _checked(body, "Governance")
    ):
        errors.append("At least one layer checkbox must be checked.")

    is_self_scan = _checked(body, "Self-scan contribution")
    if is_self_scan:
        for heading in SELF_SCAN_HEADINGS:
            _require_heading(body, heading, errors)

        if not title.lower().startswith(SELF_SCAN_TITLE_PREFIX):
            errors.append("Self-scan PR titles must start with [self-scan].")

        if not _checked(body, "The agent owner explicitly agreed that this contribution may be published upstream."):
            errors.append("Self-scan PRs require explicit owner consent.")

        if not _checked(body, "No secrets, credentials, proprietary code dumps, customer data, or internal-only materials are included."):
            errors.append("Self-scan PRs must confirm public safety.")

        if not _checked(body, "Examples and evidence have been minimized and generalized for public release."):
            errors.append("Self-scan PRs must confirm evidence minimization.")
    else:
        if not _checked(body, "This PR is not based on a self-scan contribution."):
            errors.append(
                "Non-self-scan PRs must check 'This PR is not based on a self-scan contribution.'"
            )

    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, body, re.IGNORECASE):
            errors.append(f"PR body still contains placeholder text matching: {pattern}")

    if errors:
        print("PR body validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PR body validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
