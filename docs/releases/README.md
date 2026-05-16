# hermescheck Release Notes

This page summarizes the product direction behind each `hermescheck` release.
The through-line is simple: keep moving from generic static scanning toward a
Hermes-shaped architecture audit tool for persistent, stateful agent runtimes.

## Unreleased on main

No unreleased changes yet.

## [1.4.0](./hermescheck-1.4.0.md)

**Whole-system cognitive architecture impact**

- Expanded cognitive runtime checks from local memory governance to
  whole-system architecture impact across device/OS, Rust, Python runtime,
  sqlite/files, brain/wiki, Feishu bot, Feishu CLI, cron, dream, and learning
  loops.
- Added a finding for cognitive architectures that span several infrastructure
  layers without an impact matrix, source-of-truth contract, or restart/offline
  failure-mode review.
- Updated release surfaces to make this a major audit-model step, not a small
  regex patch.

## [1.3.5](./hermescheck-1.3.5.md)

**Cognitive governance admission loop**

- Expanded cognitive runtime checks for Purpose/admission boundaries,
  scheduled-report hot memory, dream admission trails, and L5 diary privacy.
- Excluded generated audit output directories and report artifacts from scanner
  inputs.
- Added doctrine for the latest `how-to-agent` cognition-governance model:
  inputs are evidence, Purpose controls attention, and admission controls
  durability.

## [1.3.4](./hermescheck-1.3.4.md)

**Architecture separation and report cards**

- Added checks for long-running output stream separation, knowledge authority,
  self-evolution governance, bounded sidecars, dependency remediation order,
  and evidence-backed completion.
- Folded the newest `how-to-agent` architecture lessons into the runtime audit
  model.
- Included `hermescheck card` in the release line for PNG audit summary cards.

## [1.3.3](./hermescheck-1.3.3.md)

**Cognitive runtime governance**

- Added checks for cognitive-depth routing, visible-output boundaries,
  post-turn reflection admission, and bounded sidecar runtime mechanisms.
- Added gateway timeout checks so cached agents and sessions do not leak stale
  state into later turns.
- Registered the `cognitive_runtime` report layer for Hermes-style agents that
  now include reflection, intent classification, and internal reasoning
  mechanisms.

## [1.3.2](./hermescheck-1.3.2.md)

**Large-directory pruning and extension polish**

- Made skipped directories such as `node_modules/`, `.venv/`, build outputs,
  and generated assets cheaper to ignore across scanners.
- Reduced audit runs that previously stalled on dependency or environment
  directories.
- Updated the VS Code extension packaging metadata and troubleshooting copy for
  the narrower runtime audit scope.

## [1.3.1](./hermescheck-1.3.1.md)

**Production/runtime audit boundary**

- Narrowed target findings to production and runtime architecture paths.
- Excluded tests, fixtures, specs, and coverage artifacts from behavior-focused
  scanner inputs.
- Routed secret scanning through shared path filters so fixture values do not
  dominate audit output.
- Documented the principle that tests are supporting evidence, not the primary
  audit target.

## [1.3.0](./hermescheck-1.3.0.md)

**Knowledge consistency and target-agent self-review**

- Added advisory checks for stale documentation paths, relative time language,
  missing root knowledge surfaces, and drift between docs, skills, memory, and
  runbooks.
- Recalibrated regex-heavy architecture findings toward self-review prompts
  instead of over-punishing vocabulary.
- Made the target agent's knowledge layer part of the architecture review.

## [1.2.6](./hermescheck-1.2.6.md)

**Self-reviewed architecture conflicts**

- Added a target-agent self-review flow that can surface conflicting,
  duplicated, or contradictory architecture links before static findings.
- Promoted conflict-map evidence into reports so maintainers can compare the
  scanner's view with the target agent's own explanation.
- Reduced loop-safety noise where the stronger signal was an architecture
  conflict rather than a generic control-flow pattern.

## [1.2.5](./hermescheck-1.2.5.md)

**Execution-risk recalibration**

- Reclassified static execution markers such as `exec()`, `eval()`,
  `os.system()`, shell subprocesses, and dynamic JavaScript functions as
  medium-risk review findings by default.
- Kept the signal while avoiding automatic critical findings without confirmed
  reachability, missing isolation, and meaningful blast radius.
- Updated plugin-loader guidance toward scoped policy instead of brittle
  blanket removal of useful runtime helpers.

## [1.2.4](./hermescheck-1.2.4.md)

**Restart continuity and learning assetization**

- Added checks for self-restart hazards where the active agent can stop its own
  control plane before a replacement is safely supervised.
- Added checks for restartable agents that persist sessions but do not visibly
  reload recent conversation context.
- Added memory active-rule GC checks and self-evolution checks for hands-on
  validation plus reusable methodology.

## [1.1.2](./hermescheck-1.1.2.md)

**Mercury-era runtime scanner expansion**

- Expanded `hermescheck` from a Hermes contract checker into a broader
  stateful-agent architecture audit tool.
- Added runtime scanners for command capability policy, daemon lifecycle,
  memory lifecycle, token usage, RAG governance, plugin execution, tool server
  boundaries, pipeline middleware, static bug inference, and self-evolution.
- Added maturity scoring and richer Markdown reporting so findings could be
  summarized as architecture era, positive signals, and penalties.

## Release Themes

- **1.1.x -> 1.2.x**: Grow from contract checks into stateful runtime,
  lifecycle, memory, and execution-boundary audits.
- **1.2.x -> 1.3.x**: Reduce false positives, respect production/runtime scope,
  and add self-review for maintainers.
- **1.3.x onward**: Track newer Hermes runtime concepts such as cognitive
  routing, reflection governance, gateway lifecycle, and shareable report
  artifacts.
