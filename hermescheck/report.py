"""Generate human-readable markdown reports."""

from __future__ import annotations

from typing import Any, Dict, Optional

SEVERITY_EMOJI = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}


def _refs(refs: list[str], *, limit: int = 2) -> str:
    shown = [f"`{ref}`" for ref in refs[:limit]]
    if len(refs) > limit:
        shown.append(f"+{len(refs) - limit} more")
    return "<br>".join(shown) if shown else "-"


def _cell(value: Any) -> str:
    return str(value).replace("\n", " ").replace("|", "\\|")


def _finding_penalty_lookup(maturity: Dict[str, Any]) -> dict[str, int]:
    return {
        item.get("title", ""): item.get("total_penalty", 0)
        for item in maturity.get("penalty_breakdown", [])
    }


def generate_report(results: Dict[str, Any], output_file: Optional[str] = None) -> str:
    """Generate a markdown report from audit results."""

    verdict = results.get("executive_verdict", {})
    scope = results.get("scope", {})
    metadata = results.get("scan_metadata", {})
    summary = results.get("severity_summary", {})
    maturity = results.get("maturity_score", {})

    lines = [
        "# Hermes Agent Architecture Audit Report",
        "",
        f"**Target**: `{scope.get('target_name', 'Unknown')}`",
        f"**Profile**: `{metadata.get('profile', 'unknown')}`",
        f"**Date**: {metadata.get('scan_timestamp', 'Unknown')}",
        f"**Duration**: {metadata.get('scan_duration_seconds', 'N/A')}s",
        f"**Overall Health**: **{verdict.get('overall_health', 'Unknown')}**",
        f"**Architecture Era**: **{maturity.get('era_name', 'Unknown')}** ({maturity.get('score', 'N/A')}/100)",
        f"**Primary Failure Mode**: {verdict.get('primary_failure_mode', 'Unknown')}",
        f"**Most Urgent Fix**: {verdict.get('most_urgent_fix', 'Unknown')}",
        "",
        "## Scope",
        "",
        f"- Entry points: {', '.join(scope.get('entrypoints', [])) or 'Unknown'}",
        f"- Channels: {', '.join(scope.get('channels', [])) or 'Unknown'}",
        f"- Model stack: {', '.join(scope.get('model_stack', [])) or 'Unknown'}",
        f"- Audited layers: {', '.join(scope.get('layers_to_audit', [])) or 'Unknown'}",
        "",
        "## Summary",
        "",
        f"> {maturity.get('share_line', 'No maturity score available.')}",
        "",
        "| Severity | Count |",
        "|----------|-------|",
    ]

    for severity in ("critical", "high", "medium", "low"):
        lines.append(f"| {SEVERITY_EMOJI.get(severity, '')} {severity.upper()} | {summary.get(severity, 0)} |")
    lines.extend(["", f"**Total findings**: {sum(summary.values())}", ""])

    if maturity:
        lines.extend(
            [
                "## Architecture Era Score",
                "",
                f"- Era: **{maturity.get('era_name', 'Unknown')}**",
                f"- Score: **{maturity.get('score', 'N/A')}/100**",
                f"- Raw points: `{maturity.get('raw_points', 'N/A')}`",
                f"- Capped raw points: `{maturity.get('capped_raw_points', 'N/A')}`",
                f"- Pre-penalty score: `{maturity.get('pre_penalty_score', 'N/A')}`",
                f"- Finding penalty: `{maturity.get('penalty', 'N/A')}`"
                f" (uncapped `{maturity.get('uncapped_penalty', 'N/A')}`, cap `{maturity.get('penalty_cap', 'N/A')}`)",
                f"- Formula: `{maturity.get('score_formula', 'N/A')}`",
                f"- Methodology gate: {maturity.get('methodology_gate', {}).get('note', 'Unknown')}",
                f"- Self-evolution gate: {maturity.get('self_evolution_gate', {}).get('note', 'Unknown')}",
                f"- Meaning: {maturity.get('era_description', 'Unknown')}",
                "",
            ]
        )
        if maturity.get("score_caps"):
            lines.append("**Score Caps Applied**:")
            for cap in maturity["score_caps"]:
                lines.append(
                    f"- `{cap.get('gate')}`: {cap.get('before')} -> {cap.get('after')}. {cap.get('reason')}"
                )
            lines.append("")
        if maturity.get("signal_points"):
            lines.extend(
                [
                    "### Positive Signal Ledger",
                    "",
                    "| Signal | Points | Evidence |",
                    "|--------|--------|----------|",
                ]
            )
            for signal in maturity["signal_points"]:
                lines.append(
                    f"| {_cell(signal.get('label', signal.get('key', 'unknown')))} | +{signal.get('points', 0)} | "
                    f"{_refs(signal.get('evidence_refs', []))} |"
                )
            lines.append("")
        if maturity.get("penalty_breakdown"):
            lines.extend(
                [
                    "### Penalty Ledger",
                    "",
                    "| Finding | Severity | Penalty | Evidence | Fix Direction |",
                    "|---------|----------|---------|----------|---------------|",
                ]
            )
            for item in maturity["penalty_breakdown"]:
                penalty = (
                    f"-{item.get('total_penalty', 0)} "
                    f"(rule {item.get('title_penalty', 0)} + severity {item.get('severity_penalty', 0)})"
                )
                fix = _cell(item.get("recommended_fix", ""))
                if len(fix) > 180:
                    fix = fix[:177] + "..."
                lines.append(
                    f"| {_cell(item.get('title', ''))} | {item.get('severity', '').upper()} | {penalty} | "
                    f"{_refs(item.get('evidence_refs', []), limit=1)} | {fix or '-'} |"
                )
            lines.append("")
        if maturity.get("strengths"):
            lines.append("**Strengths**:")
            for strength in maturity["strengths"]:
                lines.append(f"- {strength}")
            lines.append("")
        if maturity.get("next_milestones"):
            lines.append("**Next Milestones**:")
            for milestone in maturity["next_milestones"]:
                lines.append(f"- {milestone}")
            lines.append("")

    if results.get("evidence_pack"):
        lines.extend(["## Evidence Pack", ""])
        for evidence in results["evidence_pack"]:
            lines.append(f"- `{evidence['kind']}` {evidence['location']} — {evidence['summary']}")
        lines.append("")

    if results.get("target_self_review"):
        self_review = results["target_self_review"]
        lines.extend(
            [
                "## Target Agent Self-Review",
                "",
                f"**Agent**: `{self_review.get('agent_name', 'target-agent')}`",
                f"**Methodology**: `{self_review.get('methodology_version', 'target-agent-self-review.v1')}`",
                f"**Source**: `{self_review.get('source', 'inline')}`",
                "",
                self_review.get("summary", "No self-review summary provided."),
                "",
            ]
        )
        for title, key in (
            ("Self-Claimed Architecture Strengths", "claims"),
            ("Self-Identified Risks", "risks"),
            ("Likely hermescheck False Positives", "false_positive_notes"),
            ("Target Agent Improvement Plan", "improvement_plan"),
        ):
            if self_review.get(key):
                lines.append(f"**{title}**:")
                for item in self_review[key]:
                    line = f"- {item['title']}"
                    if item.get("evidence"):
                        line += f" Evidence: `{item['evidence']}`."
                    if item.get("recommendation"):
                        line += f" Recommendation: {item['recommendation']}"
                    lines.append(line)
                lines.append("")

    penalty_lookup = _finding_penalty_lookup(maturity)
    for index, finding in enumerate(results.get("findings", []), start=1):
        severity = finding.get("severity", "low")
        lines.extend(
            [
                f"### {index}. {SEVERITY_EMOJI.get(severity, '')} [{severity.upper()}] {finding.get('title', '')}",
                "",
            ]
        )
        for key in ("symptom", "user_impact", "source_layer", "mechanism", "root_cause", "recommended_fix"):
            if finding.get(key):
                lines.append(f"**{key.replace('_', ' ').title()}**: {finding[key]}")
        score_impact = penalty_lookup.get(finding.get("title", ""), 0)
        if score_impact:
            lines.append(f"**Score Impact**: -{score_impact} points")
        if finding.get("evidence_refs"):
            lines.append("**Evidence**:")
            for ref in finding["evidence_refs"]:
                lines.append(f"- `{ref}`")
        if finding.get("confidence") is not None:
            lines.append(f"**Confidence**: {finding['confidence']:.0%}")
        lines.append("")

    if results.get("ordered_fix_plan"):
        lines.extend(["## Ordered Fix Plan", ""])
        for step in results["ordered_fix_plan"]:
            score_impact = penalty_lookup.get(step.get("goal", ""), 0)
            impact = f" Expected score recovery: up to +{score_impact}." if score_impact else ""
            lines.append(
                f"{step['order']}. **{step['goal']}** — {step['why_now']}"
                f"{impact} Expected effect: {step.get('expected_effect', '')}"
            )
        lines.append("")

    markdown = "\n".join(lines)
    if output_file:
        with open(output_file, "w", encoding="utf-8") as handle:
            handle.write(markdown)
    return markdown
