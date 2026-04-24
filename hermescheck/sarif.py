"""SARIF export for GitHub code scanning."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hermescheck import __version__

SARIF_SCHEMA_URL = "https://json.schemastore.org/sarif-2.1.0.json"
SARIF_LEVEL = {
    "critical": "error",
    "high": "error",
    "medium": "warning",
    "low": "note",
}


def _parse_evidence_ref(ref: str) -> tuple[str, int | None]:
    if ":" not in ref:
        return ref, None

    candidate_path, candidate_line = ref.rsplit(":", 1)
    if candidate_line.isdigit():
        return candidate_path, int(candidate_line)
    return ref, None


def _slugify(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-")


def generate_sarif(results: dict[str, Any]) -> dict[str, Any]:
    """Convert hermescheck findings to SARIF 2.1.0."""

    findings = results.get("findings", [])
    rules_by_id: dict[str, dict[str, Any]] = {}
    sarif_results = []

    for finding in findings:
        rule_id = _slugify(finding["title"]) or "hermescheck-finding"
        if rule_id not in rules_by_id:
            rules_by_id[rule_id] = {
                "id": rule_id,
                "name": finding["title"],
                "shortDescription": {"text": finding["title"]},
                "fullDescription": {"text": finding.get("user_impact", finding["title"])},
                "help": {"text": finding.get("recommended_fix", "")},
                "properties": {"precision": "medium"},
            }

        evidence_ref = (finding.get("evidence_refs") or ["(none found)"])[0]
        artifact_uri, line_number = _parse_evidence_ref(evidence_ref)
        result = {
            "ruleId": rule_id,
            "level": SARIF_LEVEL.get(finding.get("severity", "low"), "warning"),
            "message": {"text": finding.get("symptom", finding["title"])},
        }
        if artifact_uri != "(none found)":
            location: dict[str, Any] = {
                "physicalLocation": {
                    "artifactLocation": {"uri": artifact_uri},
                }
            }
            if line_number:
                location["physicalLocation"]["region"] = {"startLine": line_number}
            result["locations"] = [location]
        sarif_results.append(result)

    return {
        "$schema": SARIF_SCHEMA_URL,
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "hermescheck",
                        "version": __version__,
                        "informationUri": "https://github.com/huangrichao2020/hermescheck",
                        "rules": list(rules_by_id.values()),
                    }
                },
                "results": sarif_results,
            }
        ],
    }


def save_sarif(results: dict[str, Any], path: str) -> str:
    """Serialize SARIF to disk."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return str(target)
