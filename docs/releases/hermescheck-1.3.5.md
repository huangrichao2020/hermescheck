# hermescheck 1.3.5 Release Notes

`hermescheck` 1.3.5 updates the cognitive runtime scanner with the newest
`how-to-agent` cognition-governance lessons.

## Headline

This release treats long-term cognition as an admission-governed runtime loop:
Purpose selects attention, evidence is classified before storage, scheduled
reports enter same-day hot memory, and L5 diary material stays private unless a
summary is explicitly admitted.

## What Changed

- Expanded `cognitive_runtime_governance` with checks for cognition ladders
  that lack Purpose detection or admission-store boundaries.
- Added checks for scheduled reports and dream cycles that bypass same-day hot
  channel memory, target-day bookkeeping, admitted-item lists, or skipped
  reasons.
- Added checks for L5 diary and voice-input ingestion that lacks local/private
  raw-text handling, admitted summaries, or non-identity boundaries.
- Excluded generated `output/`, `outputs/`, and `reports/` directories plus
  root audit report artifacts from source scanning so previous findings do not
  become new findings.
- Added cognitive-governance doctrine so the scanner behavior is tied to a
  public architecture principle instead of a one-off regex list.
- Updated package and VS Code extension metadata to `1.3.5`.

## Why It Matters

An agent that remembers more does not automatically think better. The risky
failure mode is authority collapse: traces, episodes, claims, facts, skills,
identity rules, scheduled reports, and diary material all get treated as the
same kind of memory.

The latest `how-to-agent` work makes the healthier shape explicit. Inputs are
evidence; Purpose controls attention; admission controls durability; feedback
controls future updates. `hermescheck` now audits those boundaries directly.

## Validation

The release candidate was validated locally with:

```bash
uv run python -m hermescheck --version
uv run python -m pytest -q
uv run ruff check
uv run ruff format --check
uv run python -m hermescheck /path/to/target \
  --profile enterprise --quiet \
  -o /tmp/hermescheck-1.3.5-self-audit.json \
  -r /tmp/hermescheck-1.3.5-self-audit.md
uv run python -m hermescheck validate /tmp/hermescheck-1.3.5-self-audit.json
uv run --with build python -m build
uv run --with twine twine check dist/hermescheck-1.3.5.tar.gz \
  dist/hermescheck-1.3.5-py3-none-any.whl
```
