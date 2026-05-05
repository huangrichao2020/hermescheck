# hermescheck 1.3.3 Release Notes

`hermescheck` 1.3.3 turns the latest Hermes runtime ideas into reusable audit
signals for cognitive routing, post-turn reflection, and gateway timeout
recovery.

## Headline

This release treats cognitive runtime mechanisms as architecture, not just
prompt behavior: depth routing needs visible-output boundaries, reflection
needs admission governance, and runtime sidecars need budgets and fail-soft
integration.

## What Changed

- Added a `cognitive_runtime_governance` scanner for cognitive-depth routing,
  visible-output boundaries, post-turn reflection governance, and sidecar
  runtime mechanism safety.
- Added gateway inactivity-timeout checks so cached agent/session objects are
  evicted after a timeout instead of poisoning the next turn.
- Registered the new `cognitive_runtime` report layer in the schema and
  personal audit profile.
- Updated the VS Code extension metadata and changelog to `1.3.3`.

## Why It Matters

Hermes-style agents are now growing native cognitive runtime layers: intent
classification, post-turn reflection, loop detectors, internalization, and
context sandboxes. Those mechanisms are powerful, but they need the same
architecture discipline as tools and memory: explicit boundaries, resource
limits, durable evidence, and safe failure behavior.

`hermescheck` now audits those concepts directly while staying scoped to
runtime source paths rather than tests or fixtures.

## Validation

The release candidate was validated locally with:

```bash
uv run python -m pytest -q
uv run python -m py_compile hermescheck/scanners/cognitive_runtime_governance.py \
  hermescheck/scanners/daemon_lifecycle.py hermescheck/scanners/__init__.py
uv run python -m hermescheck /tmp/hermescheck-remote-hermes-20260506-044340 \
  --profile enterprise --quiet -o output/hermes-recent-concepts/results.json \
  -r output/hermes-recent-concepts/report.md
uv run python -m hermescheck validate output/hermes-recent-concepts/results.json
```
