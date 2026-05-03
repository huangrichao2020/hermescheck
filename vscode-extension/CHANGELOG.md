# Changelog

## 1.3.0

- Add knowledge consistency checks for stale doc paths, relative time language, and missing root knowledge surfaces.
- Recalibrate regex-heavy architecture findings toward advisory target-agent self-review prompts.
- Reduce personal-profile severity for orchestration, hidden LLM, tool enforcement, and pipeline middleware findings.
- Exclude tests, fixtures, specs, and coverage artifacts from target audit findings.

## 1.2.6

- Disable loop-safety static findings and keep the compatibility scanner as a no-op.
- Promote target-agent self-review conflicts into the official `conflict_map`.
- Prioritize conflicting, duplicated, or contradictory architecture links ahead of static regex findings in the fix plan.

## 1.2.5

- Recalibrate static execution-risk findings so dangerous function and shell markers are medium-risk review items, not automatic critical failures.
- Update plugin sandbox guidance to prefer scoped file, capability, timeout, resource, and audit policies over blanket removal of Python runtime helpers.
- Reduce maturity-score penalties for regex-level high-agency and plugin-loader findings.

## 1.2.4

- Align the core architecture checks with `agchk` 1.2.4.
- Add critical detection for self-restart paths that can kill their own control plane.
- Add restart recent-session recall checks and maturity-score penalties.
- Add memory active-rule GC, hands-on validation, and reusable assetization signals.

## 1.1.4

- Add observability checks for before/after evidence capture in runtime logs.
- Add handoff/workbook habit checks so audit reports call out missing operational manuals.
- Update Marketplace documentation to describe evidence and handoff quality signals.

## 1.1.3

- Expand Marketplace documentation with quick start, scanner coverage, output shape, settings, and troubleshooting.
- Add Marketplace icon and screenshots.

## 1.1.2

- Add the first VS Code wrapper for running `hermescheck` against the current workspace.
- Align extension version with the `hermescheck` CLI and ClawHub skill release.
