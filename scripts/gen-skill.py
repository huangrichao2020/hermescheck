#!/usr/bin/env python3
"""Generate the hermescheck Skill package from hermescheck scanners and schema.

Usage:
    python scripts/gen-skill.py

Reads scanner patterns, audit logic, and JSON schema from the hermescheck package,
then writes a complete hermescheck Skill package to output/hermescheck/.
"""

import json
import re
import sys
from pathlib import Path

HERMESCHECK_ROOT = Path(__file__).parent.parent


def read_scanner_patterns():
    """Extract anti-pattern descriptions from scanner source files."""
    scanners = HERMESCHECK_ROOT / "hermescheck" / "scanners"
    patterns = []

    for fp in sorted(scanners.glob("*.py")):
        if fp.name.startswith("_"):
            continue
        content = fp.read_text()
        # Extract docstring as description
        m = re.search(r'^"""(.+?)"""', content, re.DOTALL)
        desc = m.group(1).strip() if m else ""
        # Extract patterns
        pat_lines = re.findall(r're\.compile\((r?["\'](.+?)["\'])', content)
        patterns.append({
            "module": fp.stem.replace("_", " ").title(),
            "file": fp.name,
            "description": desc.split("\n")[0],
            "regex_count": len(pat_lines),
        })
    return patterns


def generate_code_patterns_md():
    """Generate references/code-patterns.md from scanner regexes."""
    scanners_dir = HERMESCHECK_ROOT / "hermescheck" / "scanners"

    sections = []
    for fp in sorted(scanners_dir.glob("*.py")):
        if fp.name.startswith("_"):
            continue
        content = fp.read_text()
        module_name = fp.stem.replace("_", " ").title()

        # Extract patterns with names
        # Pattern: re.compile(r"...", ...) or (name, re.compile(...))
        name_pat = re.findall(r'(?:re\.compile|r)"([^"]+)"', content)

        section = f"## {module_name}\n\n"
        section += f"**Scanner file**: `hermescheck/scanners/{fp.name}`\n\n"

        # Get severity from the file
        sev_match = re.search(r'"severity":\s*"(critical|high|medium|low)"', content)
        severity = sev_match.group(1) if sev_match else "medium"

        section += f"**Default severity**: `{severity}`\n\n"
        section += f"**Regex patterns**:\n\n"

        for pat in name_pat:
            section += f"- `{pat}`\n"

        sections.append(section)

    header = """# Code-Level Anti-Patterns

Concrete grep-searchable patterns to find agent wrapper failures in source code.

These patterns are auto-generated from the [hermescheck](https://github.com/huangrichao2020/hermescheck) Python scanners.
Each section lists the regex patterns used by that scanner.

## Usage

```bash
pip install hermescheck
hermescheck /path/to/your/agent/project
```

Or run individual grep scans manually:

"""

    return header + "\n".join(sections)


def generate_skill_md():
    """Generate SKILL.md from hermescheck's README + schema + scanners."""
    readme = (HERMESCHECK_ROOT / "README.md").read_text()
    schema = json.loads((HERMESCHECK_ROOT / "hermescheck" / "schema.json").read_text())

    skill = f"""---
name: hermes-agent-health-check
description: Audit a NousResearch/hermes-agent checkout or fork for Hermes-specific runtime-contract drift, command-surface splits, memory/skill/gateway health, and agent architecture risks. Uses the hermescheck Python library ({schema.get('properties', {}).get('schema_version', {}).get('const', 'unknown')}) for structured reports with severity-ranked findings and code-first fix plans.
origin: https://github.com/huangrichao2020/hermescheck
---

# Hermes Agent Health Check

Audit the architecture and health of a Hermes Agent checkout, fork, or deployment support repo.

Hermes Agent has a connected runtime: agent loop, command registry, CLI, TUI, gateway, skills, memory, cron, tools, plugins, and terminal environments. `hermescheck` helps keep those surfaces aligned.

## When to Use

- You are preparing a Hermes Agent PR and want a repeatable architecture review
- A Hermes fork works in CLI but not gateway, TUI, skills, cron, or plugins
- A new slash command risks drifting across surfaces
- A tool or environment change needs clearer capability boundaries
- Memory, session search, or skill behavior regressed after a refactor
- Startup paths or background jobs became hard to reason about

## Quick Start

```bash
pip install hermescheck
hermescheck /path/to/hermes-agent
```

Produces `audit_results.json` and `audit_report.md`.

## The 12-Layer Stack

| # | Layer | What Goes Wrong |
|---|-------|----------------|
| 1 | System prompt | Conflicting instructions, instruction bloat |
| 2 | Session history | Stale context from previous turns |
| 3 | Long-term memory | Pollution across sessions |
| 4 | Distillation | Compressed artifacts re-entering as pseudo-facts |
| 5 | Active recall | Redundant re-summary layers wasting context |
| 6 | Tool selection | Wrong tool routing, model skips required tools |
| 7 | Tool execution | Hallucinated execution — claims to call but doesn't |
| 8 | Tool interpretation | Misread or ignored tool output |
| 9 | Answer shaping | Format corruption in final response |
| 10 | Platform rendering | UI/API/CLI mutates valid answers |
| 11 | Hidden repair loops | Silent fallback/retry agents running second LLM pass |
| 12 | Persistence | Expired state or cached artifacts reused as live evidence |

## Audit Scanners

| # | Scanner | Severity | What It Catches |
|---|---------|----------|-----------------|
| 1 | Hardcoded Secrets | critical | API keys, tokens, credentials in source code |
| 2 | Tool Enforcement Gap | high | "Must use tool X" in prompt but no code validation |
| 3 | Hidden LLM Calls | high | Secret second-pass LLM calls in fallback/repair loops |
| 4 | Unrestricted Code Execution | critical | exec(), eval(), subprocess(shell=True) without sandbox |
| 5 | Static Bug Inference | high | Code-level bug patterns inferred without runtime execution |
| 6 | Token Usage Budget | high | Large default context windows, full-history prompts, missing thrift controls |
| 7 | Memory Lifecycle Governance | medium | Memory without types, lifecycle, retrieval budgets, decay, or evidence pointers |
| 8 | RAG Pipeline Governance | medium | Retrieval without chunk, top-k, rerank, ingestion, or context budget controls |
| 9 | Self-Evolution Capability | high | Learning loops without external signals, source reading, constraint fit, safe landing, or verification |
| 10 | Loop Safety Budget | high | Tool/agent loops without max-iteration, retry budget, stuck-job, or duplicate-call controls |
| 11 | Plugin / Remote Tool Boundary | high | Executable plugins and MCP/OpenAPI tools without sandbox, schema, allowlist, or approval boundaries |
| 12 | Output Pipeline Mutation | medium | Response transformation corrupting correct answers |
| 13 | Missing Observability | medium | No tracing, logging, cost tracking, or audit trail |

## Severity Model

| Level | Meaning |
|-------|---------|
| `critical` | Agent can confidently produce wrong operational behavior |
| `high` | Agent frequently degrades correctness or stability |
| `medium` | Correctness usually survives but output is fragile or wasteful |
| `low` | Mostly cosmetic or maintainability issues |

## Fix Strategy

Default fix order (code-first, not prompt-first):

1. **Code-gate tool requirements** — enforce in code, not just prompt text
2. **Remove or narrow hidden repair agents** — make fallback explicit with contracts
3. **Reduce context duplication** — same info through prompt + history + memory + distillation
4. **Tighten memory admission** — user corrections > agent assertions
5. **Tighten distillation triggers** — don't compress what shouldn't be compressed
6. **Reduce rendering mutation** — pass-through, don't transform
7. **Convert to typed JSON envelopes** — structured internal flow, not freeform prose

## Report Schema

Reports follow a formal JSON Schema (see `references/report-schema.json`) with:
- `overall_health`: critical_risk | high_risk | medium_risk | low_risk
- `findings`: array of severity-ranked issues with evidence refs
- `maturity_score`: positive signal ledger, penalty ledger, score formula, and expected recovery directions
- `ordered_fix_plan`: prioritized fix steps with rationale

## Anti-Patterns to Avoid

- ❌ Saying "the model is weak" without falsifying the wrapper first
- ❌ Saying "memory is bad" without showing the contamination path
- ❌ Letting a clean current state erase a dirty historical incident
- ❌ Treating markdown prose as a trustworthy internal protocol
- ❌ Accepting "must use tool" in prompt text when code never enforces it

## Related

- GitHub: https://github.com/huangrichao2020/hermescheck
"""
    return skill


def generate_playbooks_md():
    """Generate references/playbooks.md from README content."""
    return """# Playbooks

Use one of these as the primary audit mode. Each playbook maps to one or more hermescheck scanners.

## wrapper-regression

Use when: the base model works fine but the wrapped agent is worse.
Scanner: `scan_hidden_llm_calls`, `scan_output_pipeline`
Focus: system prompt conflicts, duplicated context, hidden formatting layers.

## memory-contamination

Use when: old topics bleed into new conversations.
Scanner: `scan_memory_patterns`
Focus: same-session artifact reentry, stale session reuse, weak memory admission.

## tool-discipline

Use when: the agent skips required tools or hallucinates execution.
Scanner: `scan_tool_enforcement`
Focus: code-enforced vs prompt-enforced tool requirements, skip paths.

## rendering-transport

Use when: internal answer is correct but delivery is broken.
Scanner: `scan_output_pipeline`
Focus: transport payload assumptions, platform-layer mutations.

## hidden-agent-layers

Use when: silent repair/retry/summarize loops run without contracts.
Scanner: `scan_hidden_llm_calls`
Focus: hidden repair agents, second-pass LLM calls, maintenance-worker synthesis.

## code-execution-safety

Use when: the agent uses exec/eval/shell without sandboxing.
Scanner: `scan_code_execution`
Focus: resource limits, input validation, isolation.

## memory-growth-hazard

Use when: memory/context grows without limits.
Scanner: `scan_memory_patterns`
Focus: size limits, TTL, retention policies.

## observability-gap

Use when: there is no tracing or debugging capability.
Scanner: `scan_observability`
Focus: add logging, cost metrics, session replay.
"""


def main():
    output_dir = HERMESCHECK_ROOT / "output" / "hermescheck"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate files
    files = {
        "SKILL.md": generate_skill_md(),
        "references/code-patterns.md": generate_code_patterns_md(),
        "references/playbooks.md": generate_playbooks_md(),
    }

    # Copy schema.json as report-schema.json
    schema_content = (HERMESCHECK_ROOT / "hermescheck" / "schema.json").read_text()
    files["references/report-schema.json"] = schema_content

    # Copy README from root
    readme = (HERMESCHECK_ROOT / "README.md").read_text()
    files["README.md"] = readme

    for name, content in files.items():
        fp = output_dir / name
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content)
        print(f"  ✓ {fp.relative_to(HERMESCHECK_ROOT)}")

    print(f"\nGenerated {len(files)} files to {output_dir.relative_to(HERMESCHECK_ROOT)}/")
    print("To sync to hermescheck repo:")
    print(f"  rsync -av {output_dir}/ /path/to/hermescheck/")


if __name__ == "__main__":
    main()
