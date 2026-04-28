# Release Process

`hermescheck` releases should publish four things together:

- a PyPI package
- a GitHub Release with generated notes
- a checked-in release note under `docs/releases/`
- a Twitter/X posting draft under `docs/marketing/`
- public contributor credit for the people who moved the standard forward

GitHub's generated release notes include merged pull requests, contributors, and a full changelog link. `hermescheck` customizes those notes with `.github/release.yml` so changes are grouped around the project mission: Hermes Agent architecture standards, scanner signals, contribution flow, docs, and release infrastructure.

## Release Checklist

1. Make sure `main` is green.
2. Make sure the version in `pyproject.toml` is the version you want to publish.
3. Confirm merged PRs have useful labels, especially:
   - `era-scoring`
   - `methodology`
   - `doctrine`
   - `scanner`
   - `false-positive`
   - `governance`
   - `contribution-flow`
   - `contributors`
   - `docs`
   - `ci`
   - `release`
   - `packaging`
4. Add All Contributors credit for non-code contributions before tagging when possible.
5. Create and push a version tag:

```bash
git switch main
git pull --ff-only
git tag v1.2.4
git push origin v1.2.4
```

## PR Requirements For Good Release Notes

Release notes are only as good as the merged PRs. Before merging, maintainers should check that each PR has:

- a title that reads well in `What's Changed`
- a clear `Why This Generalizes` section
- public-safe evidence
- validation commands
- useful labels for `.github/release.yml` categories
- contributor credit handled through All Contributors when the contribution is non-code

For example, a release-friendly PR summary should say:

```md
## Release Notes

Category: Agent Intelligence Standards
Credit: @username for ideas, docs

This PR sharpens the 青铜时代 -> 铁器时代 boundary by requiring explicit methodology, memory freshness, and tool ownership evidence.
```

If the PR only says "update docs", the release will be weak. If it says what standard moved forward and who contributed the insight, the release becomes part of the public history of agent intelligence evaluation.

## What Automation Does

Pushing a `v*` tag runs the normal CI pipeline:

- lint
- repository hygiene checks
- tests on Python 3.10, 3.11, 3.12, and 3.13
- package build
- GitHub Release creation with generated release notes and contributors
- PyPI publish through trusted publishing

## What The Release Should Show

A good release should make contributors visible, not buried:

```md
## What's Changed

- docs: define civilization era standards by @contributor in #12
- fix(scanner): reduce provider false positives by @contributor in #13

### Contributors

@contributor and @another-contributor

Full Changelog: v0.2.0...v0.2.1
```

The goal is not just to ship packages. The goal is to make every useful improvement to the agent-intelligence standard visible and creditable.
