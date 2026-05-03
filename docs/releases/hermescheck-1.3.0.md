# hermescheck 1.3.0 Release Notes

`hermescheck` 1.3.0 adds advisory knowledge consistency checks, softens
regex-heavy architecture findings, and narrows target audits to
production/runtime architecture instead of test-suite quality.

## Headline

This release treats the target agent's knowledge layer as part of the
architecture: docs, root instructions, memory, skills, and runbooks must point
to the current source of truth. It also makes the audit boundary sharper:
tests, fixtures, specs, and coverage artifacts are maintainer proof surfaces,
not target findings.

## What Changed

- Added a `knowledge_consistency` scanner for stale local doc paths, relative
  time language in durable docs, and missing root knowledge surfaces.
- Registered knowledge consistency in the structured report schema and personal
  audit profile.
- Recalibrated internal orchestration, role-play handoff, hidden LLM,
  tool-enforcement, and pipeline-middleware findings toward advisory
  self-review prompts.
- Reduced maturity-score penalties for regex-level orchestration and pipeline
  middleware findings.
- Excluded tests, fixtures, specs, and coverage artifacts from behavior-focused
  scanner inputs so reports stay centered on production/runtime paths.
- Removed the "missing multilingual regression tests" finding from the CJK
  memory retrieval scanner; it now checks the runtime retrieval path instead of
  test coverage.
- Routed the secret scanner through the shared path filters so fixture keys do
  not leak back into target audit findings.
- Updated the VS Code extension metadata and changelog to `1.3.0`.
- Cleaned the skill-generation helper so release lint stays green.

## Why It Matters

Agent audits often fail because the code and the knowledge layer disagree:
README links drift, handoff docs keep relative dates, skills and memory exist
without a root inventory, and scanners end up judging names instead of actual
runtime behavior.

`hermescheck` now asks the target agent to explain and verify those surfaces
before recommending code changes. The result should be less noise, clearer
self-review, and more useful audits for Hermes-style persistent agents. Test
evidence remains valuable, but it should support a maintainer decision rather
than become a standalone audit complaint.

## Release Targets

- GitHub repository: `huangrichao2020/hermescheck`
- PyPI package: `hermescheck`
- CLI command: `hermescheck`
- CI release path: push a `v1.3.0` tag after `main` is green
- Social positioning: knowledge consistency and target-agent self-review for
  stateful agent architecture audits

## Validation

The release candidate was validated locally with:

```bash
uv run ruff check hermescheck/ tests/
uv run ruff format --check hermescheck/ tests/
uv run pytest tests -q
uv run python -m hermescheck --version
uv run python -m hermescheck audit . --profile personal \
  --output /tmp/hermescheck-self-audit-1.3.0.json \
  --report /tmp/hermescheck-self-audit-1.3.0.md \
  --fail-on none
uv run python -m hermescheck validate /tmp/hermescheck-self-audit-1.3.0.json
uv run --with build python -m build
uv run --with twine twine check dist/hermescheck-1.3.0.tar.gz \
  dist/hermescheck-1.3.0-py3-none-any.whl
```
