# hermescheck 1.2.4 Release Notes

`hermescheck` 1.2.4 realigns the Hermes-focused scanner with the latest
`agchk` architecture checks while keeping the project centered on Hermes Agent
forks, deployments, and community audits.

## Headline

This release makes restart continuity a first-class architecture standard:
an agent that can restart must also preserve recent conversational continuity
and must not kill its own control plane from inside the active agent process.

## What Changed

- Added critical detection for self-restart paths that can stop the active
  agent, gateway, daemon, service, or worker before the replacement process is
  safely handed off to an external supervisor.
- Added high-severity detection for restartable agents that persist sessions,
  messages, or memory but do not visibly load recent conversations after a
  restart.
- Added maturity-score penalties for self-restart hazards and missing recent
  session recall.
- Added memory active-rule GC checks so long-term memory keeps future-facing
  rules and facts instead of completed-work residue.
- Added self-evolution checks for hands-on validation and reusable
  assetization, so learning is not counted as complete until it runs in a real
  scenario and becomes reusable methodology.
- Updated tests, README coverage, VS Code extension metadata, and package
  versioning to `1.2.4`.

## Why It Matters

Hermes-style agents are persistent systems, not one-shot scripts. Once an
agent has a gateway, scheduler, tools, memory, and long-lived sessions,
"restart" becomes part of the user experience. A restart that comes back alive
but forgets the last few conversations still feels broken. A restart command
that stops the process executing the command can leave the user with a silent
runtime.

`hermescheck` now treats both cases as architecture issues.

## Release Targets

- GitHub repository: `huangrichao2020/hermescheck`
- PyPI package: `hermescheck`
- CLI command: `hermescheck`
- CI release path: push a `v1.2.4` tag after `main` is green
- Social positioning: Hermes Agent-focused architecture health checks for
  stateful agents, restart continuity, memory, gateways, tools, and release
  evidence

## Validation

The release candidate was validated locally with:

```bash
uv run ruff check hermescheck tests
uv run ruff format --check hermescheck tests
uv run pytest tests -q
uv run python -m hermescheck --version
uv run python -m hermescheck audit . --profile personal \
  --output /tmp/hermescheck-self-audit-1.2.4.json \
  --report /tmp/hermescheck-self-audit-1.2.4.md \
  --fail-on none
uv run python -m hermescheck validate /tmp/hermescheck-self-audit-1.2.4.json
uv build
uv run twine check dist/hermescheck-1.2.4.tar.gz \
  dist/hermescheck-1.2.4-py3-none-any.whl
```

