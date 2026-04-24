"""Target-agent self-review loading and normalization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


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
        "false_positive_notes": _normalize_items(data.get("false_positive_notes")),
        "improvement_plan": _normalize_items(data.get("improvement_plan")),
    }
    if data.get("confidence") is not None:
        try:
            normalized["confidence"] = max(0.0, min(1.0, float(data["confidence"])))
        except (TypeError, ValueError):
            normalized["confidence"] = 0.5
    return normalized


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
