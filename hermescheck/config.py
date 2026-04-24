"""Shared audit configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, Optional


@dataclass(frozen=True)
class AuditProfile:
    """Profile-specific policy knobs for audits."""

    key: str
    display_name: str
    min_agency_controls: int
    enforce_agency_controls: bool


PROFILE_PRESETS = {
    "personal_development": AuditProfile(
        key="personal_development",
        display_name="Personal Development",
        min_agency_controls=0,
        enforce_agency_controls=False,
    ),
    "enterprise_production": AuditProfile(
        key="enterprise_production",
        display_name="Enterprise Production",
        min_agency_controls=2,
        enforce_agency_controls=True,
    ),
}

PROFILE_ALIASES = {
    "personal": "personal_development",
    "personal_development": "personal_development",
    "enterprise": "enterprise_production",
    "enterprise_production": "enterprise_production",
}

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
FAIL_THRESHOLD_ORDER = {"none": 4, **SEVERITY_ORDER}
ENTERPRISE_HEALTH_BY_SEVERITY = {
    "critical": "critical",
    "high": "high_risk",
    "medium": "unstable",
    "low": "acceptable",
    "none": "strong",
}
PERSONAL_HEALTH_BY_SEVERITY = {
    "critical": "critical",
    "high": "unstable",
    "medium": "acceptable",
    "low": "acceptable",
    "none": "strong",
}
PERSONAL_SEVERITY_OVERRIDES = {
    "code_execution": {"critical": "medium", "high": "low"},
    "llm_routing": {"high": "medium"},
    "memory_management": {"medium": "low"},
    "observability": {"medium": "low"},
    "tool_enforcement": {"high": "medium"},
    "output_pipeline": {"medium": "low"},
}


@dataclass(frozen=True)
class AuditConfig:
    """Runtime config shared across the CLI, orchestrator, and scanners."""

    profile: AuditProfile
    enabled_scanners: Optional[FrozenSet[str]] = None
    fail_on: str = "none"
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_profile(
        cls,
        profile_name: str,
        *,
        enabled_scanners: Optional[list[str]] = None,
        fail_on: str = "none",
    ) -> "AuditConfig":
        profile = resolve_profile(profile_name)
        return cls(
            profile=profile,
            enabled_scanners=frozenset(enabled_scanners) if enabled_scanners else None,
            fail_on=fail_on,
        )


def resolve_profile(profile_name: str | None) -> AuditProfile:
    normalized = PROFILE_ALIASES.get((profile_name or "personal").strip().lower())
    if not normalized:
        valid = ", ".join(sorted(PROFILE_ALIASES))
        raise ValueError(f"Unknown audit profile '{profile_name}'. Expected one of: {valid}")
    return PROFILE_PRESETS[normalized]


def normalize_finding_for_profile(finding: dict, config: AuditConfig) -> dict:
    """Adjust finding severity and guidance based on the selected profile."""

    normalized = dict(finding)
    if config.profile.key != "personal_development":
        return normalized

    source_layer = normalized.get("source_layer")
    severity = normalized.get("severity", "low")
    severity_override = PERSONAL_SEVERITY_OVERRIDES.get(source_layer, {}).get(severity)
    if severity_override:
        normalized["severity"] = severity_override

    if source_layer == "code_execution":
        normalized["recommended_fix"] = (
            "Do not feed untrusted input into exec/eval/shell execution. "
            "For personal or local prototyping, you can keep controlled execution paths "
            "when the input is trusted and the blast radius is small, but prefer safer parsers "
            "such as ast.literal_eval or json.loads when they fit the job."
        )
    elif source_layer == "observability":
        normalized["recommended_fix"] = (
            "For personal development, lightweight logging is usually enough at first. "
            "Add full tracing or cost telemetry once the project becomes collaborative, user-facing, "
            "or production-bound."
        )
    elif source_layer == "memory_management":
        normalized["recommended_fix"] = (
            "For personal prototypes, this is usually a polish issue rather than an immediate blocker. "
            "Once the workflow stabilizes, add explicit retention, truncation, or TTL limits."
        )
    elif source_layer == "tool_enforcement":
        normalized["recommended_fix"] = (
            "For personal development, prompt-only guidance may be acceptable early on. "
            "Before sharing or productionizing the project, add code-level validation for required tools."
        )
    elif source_layer == "llm_routing":
        normalized["recommended_fix"] = (
            "This may be acceptable in a personal prototype if the extra call is intentional and well understood. "
            "If the project grows or is shared with others, document the secondary path and add stronger guardrails."
        )
    elif source_layer == "output_pipeline":
        normalized["recommended_fix"] = (
            "For personal development, small output shaping layers are often acceptable. "
            "If responses become user-facing or safety-sensitive, log the raw and transformed outputs explicitly."
        )

    return normalized


def health_mapping_for_profile(config: AuditConfig) -> dict[str, str]:
    """Return the health verdict mapping appropriate for the selected profile."""

    if config.profile.key == "personal_development":
        return PERSONAL_HEALTH_BY_SEVERITY
    return ENTERPRISE_HEALTH_BY_SEVERITY


def should_fail_for_threshold(results: dict, threshold: str) -> bool:
    """Return True when results should trigger a CI failure."""

    threshold_value = FAIL_THRESHOLD_ORDER[threshold]
    if threshold == "none":
        return False

    for finding in results.get("findings", []):
        severity = finding.get("severity", "low")
        if SEVERITY_ORDER.get(severity, 99) <= threshold_value:
            return True
    return False
