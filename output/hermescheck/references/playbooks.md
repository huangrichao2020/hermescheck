# Playbooks

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
