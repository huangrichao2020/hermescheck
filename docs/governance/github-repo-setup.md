# GitHub Repository Setup

This document describes the intended PR governance for `huangrichao2020/hermescheck`.

## Required Repository Settings

Repository administrators should configure:

- default workflow permissions: `read`
- do not send write tokens or secrets to fork pull request workflows
- require approval from code owners before merge
- dismiss stale approvals when new commits are pushed
- require these status checks before merge:
  - `CI / lint`
  - `CI / test`
  - `PR Governance / validate-pr-body`

## Review Routing

Use `.github/CODEOWNERS` to route all material changes to the maintainer.

The critical paths are:

- scanner logic
- doctrine docs
- governance files
- tests

## Pull Request Classes

The repository recognizes three broad PR classes:

- `self-scan`: contribution derived from a real agent scanning itself
- `maintainer`: maintainer-originated code or rule changes
- `docs/governance`: doctrinal, community, or review-process changes

## PR Body Policy

Every PR should include:

- mission alignment
- contribution mode
- affected layers
- validation evidence

Self-scan PRs additionally require:

- explicit owner consent
- public-safety confirmation
- generalization statement
- evidence summary

## Security Posture

PR-body validation should not require repository secrets.

The workflow should validate the PR body using the event payload, not contributor-provided runtime state. This keeps governance checks safe even for fork-based contributions.
