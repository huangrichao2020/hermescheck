# Contribution Examples

This page shows what a useful `hermescheck` issue or pull request can look like.

It is intentionally public-safe. A good contribution should generalize a real lesson without uploading private source code, secrets, customer data, or internal-only context.

## Example Issue

Use an issue when you have a pattern, false positive, scoring gap, or doctrine question, but you are not yet ready to change code.

Example title:

```text
Example: propose a civilization-era scoring improvement from a real self-scan
```

Example body:

```md
## What This Issue Demonstrates

This issue proposes a general `hermescheck` improvement based on a real self-scan lesson.

## Source Context

- Project type: agent / LLM coding tool
- Profile: `personal`
- Report fields included: `maturity_score.era_name`, `maturity_score.score`, `maturity_score.share_line`
- Public-safety rule: no private source code, secrets, customer data, or internal URLs

## Observed Pattern

The target agent ran `hermescheck`, but its final human-facing summary omitted the civilization era score even though the official `audit_report.md` contained it.

## Proposed Standard Improvement

The standard final report should require the first screen to show:

- `maturity_score.era_name`
- `maturity_score.score/100`
- `maturity_score.share_line`
- top findings
- likely false positives
- next optimization prescription

## Why This Generalizes

Many agents will synthesize a conversational report instead of showing raw `audit_report.md`. `hermescheck` should therefore document what a good synthesized report looks like.

## Owner Consent / Public Safety

- [ ] The owner agrees this lesson may be discussed publicly.
- [ ] No secrets, proprietary code, customer data, or internal-only context are included.
```

Live maintainer example: [issue #2](https://github.com/huangrichao2020/hermescheck/issues/2).

## Example Pull Request

Use a PR when the lesson is ready to become a concrete improvement: docs, doctrine, tests, scanner logic, schema, or contribution flow.

Example title:

```text
docs: add contribution examples for self-scan lessons
```

Example PR body:

```md
## Mission Alignment

This PR turns a real self-scan lesson into reusable contribution guidance, helping `hermescheck` become a long-lived open standard for agent architecture evaluation.

## Contribution Mode

- [ ] Self-scan contribution
- [ ] Maintainer improvement
- [x] Docs or governance change

## Layers Changed

- [x] Doctrine
- [ ] Contract
- [ ] Scanner
- [x] Contribution Flow
- [ ] Governance

## Owner Consent

- [x] This PR is not based on private third-party code.
- [x] The maintainer intentionally created it as a public example.

## Public Safety

- [x] No secrets, credentials, proprietary code dumps, customer data, or internal-only materials are included.
- [x] Examples and evidence have been minimized and generalized for public release.

## Why This Generalizes

Most agent projects will discover useful lessons during self-scan. They need a low-friction way to turn those lessons into public-safe issues and PRs.

## Evidence

The README already asks agents to show civilization-era scores. This PR adds an explicit example so future contributors know what a good issue or PR looks like.

## Validation

- `git diff --check`
```

## What Good Contributions Improve

- A civilization-era scoring milestone.
- A false positive that can be generalized away.
- A scanner signal that catches a real agent architecture failure.
- A doctrine page that sharpens how agents should reason about memory, tools, scheduling, or methodology.
- A contribution workflow that keeps private project details out of public GitHub.

## One-Sentence Rule

Do not upstream a project dump. Upstream the smallest public-safe lesson that makes `hermescheck` smarter for the next agent project.
