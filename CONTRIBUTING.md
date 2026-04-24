# Contributing to hermescheck

`hermescheck` is not just a scanner collection. We are building it as a sustainable 100-year open source project for agent architecture doctrine, self-audit methods, and reusable engineering patterns.

We welcome contributions from anywhere in the world, especially from real agent systems that scan themselves and surface:

- new design failure modes
- scanner false positives
- generalized fixes
- framework-specific patterns
- better doctrine and vocabulary

## Contribution Principles

1. Doctrine before cleverness.
2. Generalize before upstreaming.
3. Public-safe evidence only.
4. Tests and docs should move with scanner logic.
5. `hermescheck` should remain layered, explainable, and extensible.

## The Five Layers

Every contribution should say which layer it improves:

- `Doctrine`: principles, vocabulary, failure modes, prioritization
- `Contract`: `hermescheck.yaml` or future architecture declarations
- `Scanner`: concrete detection logic
- `Contribution Flow`: self-scan bundles and upstream contribution mechanics
- `Governance`: PR policy, code ownership, review workflow, repo rules

## Preferred Contribution Flow

For external agent projects, the preferred path is fork-based upstreaming:

1. Run `hermescheck` against the local project.
2. Review the report with the agent owner.
3. Run `hermescheck contribute prepare` to build a local contribution bundle.
4. Decide what can be generalized into a public contribution.
5. Remove or rewrite any private code, customer details, secrets, prompts, or internal paths.
6. Use `hermescheck contribute pr --owner-consent --public-safe` to open a fork-based upstream PR.
7. Use the repository PR template and complete all required sections.

## Self-Scan Contributions

Self-scan contributions are especially valuable, but they must meet a higher bar.

They must include:

- explicit owner consent to publish the contribution upstream
- public-safe evidence only
- a clear explanation of why the pattern generalizes beyond one project
- tests or fixtures that protect the new behavior
- doctrine or README updates if the change affects method or vocabulary

They must not include:

- raw private repositories or large proprietary code dumps
- secrets, credentials, internal URLs, customer data, or sensitive logs
- scanner changes without a claim about what got less noisy or more accurate

## Pull Request Expectations

All pull requests should explain:

- why this change matters to the long-term mission
- which layer(s) it changes
- whether it is a self-scan contribution or a maintainer-originated change
- what evidence supports the change
- what validation was run

For self-scan contributions, the PR title should start with `[self-scan]`.

## Release-Friendly PR Notes

Merged PRs become the raw material for GitHub Release notes. Please make your PR readable as a future changelog entry:

- Use a clear title, for example `docs: refine civilization era standards` or `fix(scanner): reduce provider false positives`.
- Explain the user-visible change in `## What Changed` or `## Evidence`.
- Explain why the lesson generalizes beyond one project.
- Mention the contribution type that should be credited, such as `ideas`, `doc`, `code`, `test`, `review`, or `example`.
- Ask maintainers to add labels that match the release categories, such as `era-scoring`, `methodology`, `scanner`, `false-positive`, `governance`, `contributors`, `docs`, `ci`, `release`, or `packaging`.

If the PR came from a real self-scan, keep the release note public-safe: describe the generalized pattern, not the private project.

## Contributor Recognition

`hermescheck` uses [All Contributors](https://all-contributors.github.io/) to recognize more than code.

Maintainers can add contributors after useful issues, PRs, reviews, tests, examples, docs, or era-standard discussions with comments like:

```text
@all-contributors please add @username for ideas
@all-contributors please add @username for doc
@all-contributors please add @username for code, test
```

This matters because many of the most important `hermescheck` contributions will be methodology, false-positive reports, self-scan lessons, and civilization-era scoring improvements.

## Review Standard

Upstream maintainers will review for:

- public safety
- generalizability
- layering and extensibility
- signal-to-noise improvement
- tests and docs quality

The best contributions do not merely fix one project. They improve `hermescheck` as shared method infrastructure for future agent systems.
