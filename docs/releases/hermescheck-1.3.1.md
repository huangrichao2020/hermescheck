# hermescheck 1.3.1 Release Notes

`hermescheck` 1.3.1 narrows target audits to production/runtime architecture
and keeps tests, fixtures, specs, and coverage artifacts out of findings.

## Headline

This patch release makes the audit boundary explicit: test evidence can help a
maintainer close or verify an issue, but target findings should be grounded in
runtime source paths and architecture contracts.

## What Changed

- Excluded tests, fixtures, specs, and coverage artifacts from shared
  behavior-focused scanner inputs.
- Removed the CJK memory retrieval "missing multilingual regression tests"
  finding; the scanner now checks runtime retrieval safeguards instead of test
  coverage.
- Routed secret scanning through the shared path filters so fixture keys do not
  leak into target audit reports.
- Documented the production/runtime audit boundary in the README and generated
  skill README.
- Ignored local `.omx/` agent-state artifacts.

## Why It Matters

Maintainers can reasonably answer broad audit reports with source inspection and
existing test coverage. `hermescheck` should respect that workflow by treating
tests as supporting proof rather than as standalone audit targets. The result is
a quieter report that points reviewers at production behavior and runtime
contracts.

## Release Targets

- GitHub repository: `huangrichao2020/hermescheck`
- PyPI package: `hermescheck`
- CLI command: `hermescheck`
- CI release path: push a `v1.3.1` tag after `main` is green
- Social positioning: sharper architecture-audit scope for Hermes-style agent
  runtime reviews

## Validation

The release candidate was validated locally with:

```bash
uv run ruff check hermescheck/ tests/
uv run ruff format --check hermescheck/ tests/
uv run pytest tests -q
uv run python -m hermescheck --version
uv run python -m hermescheck audit . --profile personal \
  --output /tmp/hermescheck-self-audit-1.3.1.json \
  --report /tmp/hermescheck-self-audit-1.3.1.md \
  --fail-on none
uv run python -m hermescheck validate /tmp/hermescheck-self-audit-1.3.1.json
uv run --with build python -m build
uv run --with twine twine check dist/hermescheck-1.3.1.tar.gz \
  dist/hermescheck-1.3.1-py3-none-any.whl
```
