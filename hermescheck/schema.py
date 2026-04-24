"""JSON Schema and validation for audit reports."""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any, Dict

from jsonschema import Draft202012Validator

REPORT_SCHEMA = json.loads(files("hermescheck").joinpath("schema.json").read_text())


def validate_report(report: Dict[str, Any]) -> list[str]:
    """Validate a report using the packaged JSON Schema."""

    validator = Draft202012Validator(REPORT_SCHEMA)
    errors = []
    for error in sorted(validator.iter_errors(report), key=lambda item: list(item.path)):
        path = ".".join(str(part) for part in error.path) or "<root>"
        errors.append(f"{path}: {error.message}")
    return errors
