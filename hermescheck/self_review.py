"""Target-agent self-review loading and normalization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CONFLICT_TYPES = {"stale_state", "duplication", "contradiction", "amplification", "silent_override"}


def load_self_review(path: str | Path) -> dict[str, Any]:
    """Load a target-agent self-review JSON file."""

    source = Path(path)
    with source.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Self-review file must contain a JSON object.")
    return normalize_self_review(data, source=str(source))


def normalize_self_review(data: dict[str, Any], *, source: str | None = None) -> dict[str, Any]:
    """Normalize a self-review object into the report contract."""

    normalized = {
        "source": str(source or data.get("source") or "inline"),
        "methodology_version": str(data.get("methodology_version") or "target-agent-self-review.v1"),
        "agent_name": str(data.get("agent_name") or data.get("project_name") or "target-agent"),
        "summary": str(data.get("summary") or "No self-review summary provided."),
        "claims": _normalize_items(data.get("claims")),
        "risks": _normalize_items(data.get("risks")),
        "conflicts": _normalize_conflicts(
            data.get("conflicts")
            or data.get("conflict_map")
            or data.get("contradictions")
            or data.get("duplicated_logic")
        ),
        "false_positive_notes": _normalize_items(data.get("false_positive_notes")),
        "improvement_plan": _normalize_items(data.get("improvement_plan")),
    }
    if data.get("confidence") is not None:
        try:
            normalized["confidence"] = max(0.0, min(1.0, float(data["confidence"])))
        except (TypeError, ValueError):
            normalized["confidence"] = 0.5
    return normalized


def _normalize_conflicts(value: Any) -> list[dict[str, str]]:
    if value is None:
        return []
    if isinstance(value, str):
        return [
            {
                "from_layer": "self_review",
                "to_layer": "architecture",
                "conflict_type": "contradiction",
                "note": value,
            }
        ]
    if not isinstance(value, list):
        return _normalize_conflicts(str(value))

    conflicts = []
    for item in value:
        if isinstance(item, str):
            conflicts.extend(_normalize_conflicts(item))
            continue
        if not isinstance(item, dict):
            conflicts.extend(_normalize_conflicts(str(item)))
            continue
        conflict_type = _normalize_conflict_type(item.get("conflict_type") or item.get("type") or item.get("kind"))
        note = (
            item.get("note")
            or item.get("title")
            or item.get("summary")
            or item.get("problem")
            or "Architecture conflict"
        )
        conflicts.append(
            {
                "from_layer": str(item.get("from_layer") or item.get("left") or item.get("source") or "self_review"),
                "to_layer": str(item.get("to_layer") or item.get("right") or item.get("target") or "architecture"),
                "conflict_type": conflict_type,
                "note": str(note),
            }
        )
    return conflicts


def _normalize_conflict_type(value: Any) -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if text in CONFLICT_TYPES:
        return text
    if "duplic" in text or "repeat" in text or "overlap" in text:
        return "duplication"
    if "stale" in text or "old" in text or "fresh" in text:
        return "stale_state"
    if "override" in text or "shadow" in text:
        return "silent_override"
    if "ampl" in text or "cascade" in text:
        return "amplification"
    return "contradiction"


def _normalize_items(value: Any) -> list[dict[str, str]]:
    if value is None:
        return []
    if isinstance(value, str):
        return [{"title": value, "evidence": "", "recommendation": ""}]
    if not isinstance(value, list):
        return [{"title": str(value), "evidence": "", "recommendation": ""}]

    items = []
    for index, item in enumerate(value, start=1):
        if isinstance(item, str):
            items.append({"title": item, "evidence": "", "recommendation": ""})
        elif isinstance(item, dict):
            title = item.get("title") or item.get("claim") or item.get("risk") or item.get("summary") or f"Item {index}"
            items.append(
                {
                    "title": str(title),
                    "evidence": str(item.get("evidence") or item.get("evidence_ref") or ""),
                    "recommendation": str(item.get("recommendation") or item.get("fix") or ""),
                }
            )
        else:
            items.append({"title": str(item), "evidence": "", "recommendation": ""})
    return items
