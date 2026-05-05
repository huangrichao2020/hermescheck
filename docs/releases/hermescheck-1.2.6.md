# hermescheck 1.2.6 Release Notes

`hermescheck` 1.2.6 introduced target-agent self-review so architecture
conflicts can be inspected before generic static findings dominate the report.

## Headline

This release lets the target agent describe its own architecture claims, risks,
and conflicts. `hermescheck` then promotes those conflicts into the report so
maintainers can compare self-review evidence with static scanner evidence.

## What Changed

- Added target-agent self-review loading and normalization.
- Added `conflict_map` output for conflicting, duplicated, or contradictory
  architecture links.
- Updated Markdown reports to show self-reviewed architecture conflicts before
  ordinary findings.
- Reduced loop-safety noise where the stronger signal is an ownership or
  architecture conflict rather than a generic pattern match.
- Updated tests, schema, package versioning, and VS Code extension metadata to
  `1.2.6`.

## Why It Matters

Maintainers often know when a scary-looking static finding is intentional,
transitional, or already mitigated elsewhere. Self-review gives the target
agent a structured place to say that, while still making genuine contradictions
visible. The result is a more collaborative audit report.

