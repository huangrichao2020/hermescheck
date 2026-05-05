# hermescheck 1.1.2 Release Notes

`hermescheck` 1.1.2 expanded the project from a Hermes contract checker into a
broader architecture audit tool for stateful agent runtimes.

## Headline

This release added the Mercury-era scanner set: runtime boundaries, lifecycle
checks, memory governance, tool policy, token budget risks, RAG governance, and
self-evolution signals.

## What Changed

- Added runtime scanners for command capability policy, daemon lifecycle,
  memory lifecycle, token usage, RAG governance, plugin execution policy, tool
  server boundaries, pipeline middleware integrity, static bug inference, and
  loop safety.
- Added maturity scoring so reports can explain architecture era, positive
  signals, and penalties instead of listing findings only.
- Expanded the Markdown report with score formulas, signal ledgers, penalty
  ledgers, strengths, and next milestones.
- Added the first VS Code extension package metadata and generated skill
  references.

## Why It Matters

Hermes-style agents are persistent systems. They need review coverage for
memory, scheduler behavior, runtime daemons, tool boundaries, command
capabilities, and self-improvement loops. Version 1.1.2 gave `hermescheck` the
foundation for auditing those agent-runtime concerns directly.

