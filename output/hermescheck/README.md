# hermescheck

Hermes Agent-focused architecture and runtime health checks.

`hermescheck` is a community companion tool for
[NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent). It
scans a Hermes Agent checkout or fork and produces a structured report about
runtime contracts, command-surface drift, memory and skill architecture,
gateway readiness, scheduled jobs, tool boundaries, observability, and common
agent-system failure modes.

This project is not an official Nous Research project. It is built for the
Hermes Agent community and derived from the general-purpose
[`agchk`](https://github.com/huangrichao2020/agchk) scanner, then narrowed for
Hermes-specific review workflows.

<p align="center">
  <a href="https://github.com/huangrichao2020/hermescheck/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/huangrichao2020/hermescheck/ci.yml?branch=main&label=CI&style=flat-square"></a>
  <a href="./LICENSE"><img alt="License" src="https://img.shields.io/github/license/huangrichao2020/hermescheck?style=flat-square"></a>
  <!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
  <a href="#contributors"><img alt="All Contributors" src="https://img.shields.io/badge/all_contributors-1-orange.svg?style=flat-square"></a>
  <!-- ALL-CONTRIBUTORS-BADGE:END -->
</p>

## Why It Exists

Hermes Agent is more than a chat CLI. It is a persistent agent runtime with a
conversation loop, tool registry, skills, memory, session search, messaging
gateway, scheduled automations, terminal backends, plugins, and training
surfaces. That power is exactly why Hermes forks and deployments can drift in
ways ordinary linters do not catch.

`hermescheck` asks Hermes-shaped questions:

- Does this checkout still contain the core Hermes runtime surfaces?
- Are slash commands derived from the central registry instead of diverging per surface?
- Do CLI, TUI, gateway, skills, cron, and SessionDB still line up?
- Are tool/syscall boundaries explicit enough for high-agency operation?
- Is memory becoming a durable subsystem rather than context stuffing?
- Are startup paths, plugins, and background jobs becoming hard to reason about?
- Can findings be exported to Markdown, JSON, and SARIF for repeatable review?

## Quick Start

Until the first PyPI release, install from GitHub:

```bash
python -m pip install "git+https://github.com/huangrichao2020/hermescheck.git"
```

Scan a Hermes Agent checkout:

```bash
git clone https://github.com/NousResearch/hermes-agent.git
hermescheck ./hermes-agent
```

Write machine-readable, human-readable, and GitHub code-scanning outputs:

```bash
hermescheck ./hermes-agent \
  --profile personal \
  -o audit_results.json \
  -r audit_report.md \
  --sarif hermescheck.sarif.json
```

Run as a module from a local clone:

```bash
python -m hermescheck ./path/to/hermes-agent --quiet
```

## Hermes-Specific Checks

### Runtime Contract

`hermescheck` first detects whether the target looks like a Hermes Agent
checkout. If it does, it verifies the presence of core runtime surfaces:

| Surface | Expected path |
| --- | --- |
| Agent loop | `run_agent.py` |
| Tool orchestration | `model_tools.py`, `toolsets.py`, `tools/registry.py` |
| CLI | `cli.py`, `hermes_cli/commands.py` |
| Session memory | `hermes_state.py` |
| Profile-aware paths and logs | `hermes_constants.py`, `hermes_logging.py` |
| Skills | `skills/`, `optional-skills/`, `agent/skill_commands.py` |
| Gateway | `gateway/run.py`, `gateway/platforms/` |
| Scheduling | `cron/scheduler.py` |
| Execution environments | `tools/environments/` |
| Plugins and tests | `plugins/`, `tests/` |

If a fork or packaging step drops one of these surfaces, the report makes the
drift visible before the missing piece becomes a runtime surprise.

### Slash Command Contract

Hermes shares slash commands across the classic CLI, TUI, messaging gateway,
help text, autocomplete, and platform menus. `hermescheck` looks for the shared
`COMMAND_REGISTRY`, `GATEWAY_KNOWN_COMMANDS`, `resolve_command`, and
`gateway_help_lines` helpers so command changes do not silently split by
surface.

### General Agent Architecture Signals

The Hermes-specific scanner runs alongside inherited architecture checks:

- internal orchestration sprawl
- completion-closure gaps
- memory freshness confusion
- impression/pointer memory gaps
- role-play handoff chains
- agent-OS architecture gaps
- duplicated skills and SOPs
- startup and runtime surface sprawl
- hidden LLM calls
- tool-enforcement gaps
- output pipeline mutation
- code execution risks
- missing observability
- excessive agency controls in enterprise mode

## Profiles

`hermescheck` keeps two practical profiles:

| Profile | Intended use | Behavior |
| --- | --- | --- |
| `personal` | Local Hermes forks, experiments, solo operator setups | Prioritizes internal drag, closure, memory shape, and runtime clarity |
| `enterprise` | Team-owned or production Hermes deployments | Keeps stricter checks for secrets, code execution, approvals, and observability |

Examples:

```bash
hermescheck ./hermes-agent --profile personal
hermescheck ./hermes-agent --profile enterprise --fail-on high
```

## Report Shape

Every scan produces:

- `schema_version`: stable JSON schema identifier
- `scan_metadata`: timestamp, duration, scanner count, profile
- `executive_verdict`: health, primary failure mode, urgent fix
- `scope`: entry points, channels, model stack, audited layers
- `maturity_score`: architecture-era score and share line
- `evidence_pack`: compact evidence references
- `findings`: severity-ranked issues with fixes
- `ordered_fix_plan`: practical next steps

Generate Markdown from a previous JSON report:

```bash
hermescheck report audit_results.json -o audit_report.md
```

Validate a report:

```bash
hermescheck validate audit_results.json
```

## Use With Hermes PRs

For contributors preparing a Hermes Agent PR:

```bash
hermescheck ./hermes-agent --profile personal -o audit_results.json -r audit_report.md
```

Then use the report to answer:

- Did the change touch the agent loop, command registry, gateway, skills, cron, or SessionDB?
- Did any interface work in CLI but not gateway, or vice versa?
- Did a new tool path get a capability boundary, test, and observable failure mode?
- Did a memory or skill change preserve recall, search, and closure behavior?
- Can the PR description cite a concrete validation command?

The goal is not to block Hermes experimentation. The goal is to make drift
visible early so community tools, forks, and upstream contributions stay easy to
review.

## Development

```bash
git clone https://github.com/huangrichao2020/hermescheck.git
cd hermescheck
python -m pip install -e ".[dev]"
pytest -q
ruff check hermescheck tests
ruff format --check hermescheck tests
```

The CI pipeline runs lint, repository hygiene checks, tests across supported
Python versions, a self-scan, and package build validation.

## Contributing

Useful contributions include:

- sharper Hermes-specific contract checks
- false-positive reductions from real Hermes forks
- report examples from public-safe scans
- SARIF or CI integration improvements
- docs that make Hermes review workflows easier to repeat

See:

- [Contribution examples](./docs/examples/contribution-examples.md)
- [Release process](./docs/governance/release-process.md)
- [Agent prompt](./docs/AGENT_PROMPT.md)

## Contributors

Thanks goes to these people for code, docs, ideas, tests, reviews, examples, and
real-world self-scan lessons.

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/huangrichao2020"><img src="https://avatars.githubusercontent.com/u/72842645?v=4?s=100" width="100px;" alt="Huang richao"/><br /><sub><b>Huang richao</b></sub></a><br /><a href="https://github.com/huangrichao2020/hermescheck/commits?author=huangrichao2020" title="Code">Code</a> <a href="https://github.com/huangrichao2020/hermescheck/commits?author=huangrichao2020" title="Documentation">Docs</a> <a href="#ideas-huangrichao2020" title="Ideas, Planning, & Feedback">Ideas</a> <a href="#maintenance-huangrichao2020" title="Maintenance">Maintenance</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

## License

MIT. See [LICENSE](./LICENSE).
