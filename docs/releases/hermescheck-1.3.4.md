# hermescheck 1.3.4 Release Notes

`hermescheck` 1.3.4 folds the newest `how-to-agent` architecture lessons into
runtime audit signals.

## Headline

This release treats excellent agent architecture as a set of explicit
separations: output streams, knowledge authority, self-evolution governance,
core-versus-sidecar runtime paths, dependency remediation order, and evidence
closure.

## What Changed

- Added an `architecture_separation` scanner based on the `how-to-agent`
  architecture method.
- Added checks for long-running channel output that lacks separate progress
  and conclusion streams.
- Added checks for knowledge surfaces that do not distinguish active facts,
  procedures, session history, and cold archives.
- Added checks for self-evolution without proposal, evidence, risk,
  validation, rollback, and apply-gate governance.
- Added checks for runtime sidecars without primary-path, bounded, or
  fail-soft semantics.
- Added checks for dependency remediation that lacks runtime-risk triage.
- Added checks that distinguish "code changed" from evidence-backed
  completion.
- Included the report-card rendering capability in the release line.
- Updated package and VS Code extension metadata to `1.3.4`.

## Why It Matters

Persistent agents increasingly run through chat gateways, memory layers,
skills, telemetry, sidecars, and live deployment actions. The failure mode is
rarely one bad prompt. More often, it is a boundary problem: the wrong layer
owns state, history masquerades as authority, self-evolution bypasses review,
or completion is claimed before the live system proves it.

The `how-to-agent` method gives those boundary instincts a portable shape.
`hermescheck` now audits the same instincts directly while staying focused on
runtime and production architecture rather than test fixtures or generated
artifacts.

## Validation

The release candidate was validated locally with:

```bash
uv run python -m hermescheck --version
uv run python -m pytest -q
uv run ruff check
uv run ruff format --check
uv run python -m hermescheck /path/to/target \
  --profile enterprise --quiet \
  -o /tmp/hermescheck-1.3.4-self-audit.json \
  -r /tmp/hermescheck-1.3.4-self-audit.md
uv run python -m hermescheck validate /tmp/hermescheck-1.3.4-self-audit.json
uv run --with build python -m build
uv run --with twine twine check dist/hermescheck-1.3.4.tar.gz \
  dist/hermescheck-1.3.4-py3-none-any.whl
```
