# hermescheck 1.4.0 Release Notes

`hermescheck` 1.4.0 upgrades the cognitive runtime audit model from local
memory governance to whole-system cognitive architecture impact.

## Headline

A serious agent cognition stack is not just a memory feature. It crosses the
device that keeps the agent alive, the low-level runtime substrate, the Python
execution layer, stores, wiki/brain knowledge surfaces, chat channels,
document CLIs, cron, dream, learning, and user feedback.

This release teaches `hermescheck` to flag cognitive architectures that name
memory layers but do not explain how changes affect the whole system.

## What Changed

- Added whole-system impact signals to `cognitive_runtime_governance`.
- The scanner now detects cognitive/governance systems that also mention
  multiple infrastructure surfaces such as device/OS, Rust, Python runtime,
  sqlite/files, brain/wiki, Feishu bot, Feishu CLI, cron, dream, or learning.
- If that architecture lacks a whole-system impact matrix, source-of-truth
  contract, or restart/offline failure-mode review, `hermescheck` reports:
  `Cognitive architecture lacks whole-system impact matrix`.
- Added regression coverage so bounded cognitive systems that document input,
  execution, storage, retrieval, cognition, evolution, and operations layers
  pass cleanly.
- Updated package and VS Code extension metadata to `1.4.0`.

## Why It Matters

An agent can have clean memory admission rules and still fail as a living
runtime if the surrounding system is incoherent:

- group chat can answer from private history
- cron reports can be delivered then forgotten
- a Rust fast path can become a second state authority
- Feishu CLI document evidence can lose identity or token context
- a Mac sleep, network drop, or gateway restart can sever continuity
- a learning loop can silently mutate the agent without discussing the blast
  radius

The 1.4.0 rule is simple: cognitive architecture changes must name affected
layers, source-of-truth movement, user-visible behavior, background-loop
behavior, and restart/offline failure modes before implementation.

## Validation

The release candidate should be validated with:

```bash
uv run python -m hermescheck --version
uv run python -m pytest -q
uv run ruff check
uv run ruff format --check
uv run python -m hermescheck /path/to/target \
  --profile enterprise --quiet \
  -o /tmp/hermescheck-1.4.0-self-audit.json \
  -r /tmp/hermescheck-1.4.0-self-audit.md
uv run python -m hermescheck validate /tmp/hermescheck-1.4.0-self-audit.json
uv run --with build python -m build
uv run --with twine twine check dist/hermescheck-1.4.0.tar.gz \
  dist/hermescheck-1.4.0-py3-none-any.whl
```
