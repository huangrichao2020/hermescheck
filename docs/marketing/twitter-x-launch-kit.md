# hermescheck Twitter/X Launch Kit

Use this file as the public posting base for `hermescheck` releases. Keep the
message centered on `hermescheck`; mention `agchk` only as prior art when it is
useful context.

## Positioning

`hermescheck` is a Hermes Agent-focused architecture health-check tool for
stateful AI agents. It scans for runtime contracts, restart continuity, memory
freshness, gateway/tool boundaries, observability, and release evidence.

## Short Post

`hermescheck` 1.3.0 is out.

It now treats knowledge consistency as part of agent architecture:

- docs, memory, skills, and root instructions should agree
- stale local paths and relative dates are review prompts
- regex-heavy architecture findings are softer and more advisory
- target agents are asked to self-review before code changes are prescribed

Hermes-style agents are persistent systems. `hermescheck` is evolving toward
audits that check both runtime structure and the knowledge layer agents depend
on.

GitHub: https://github.com/huangrichao2020/hermescheck
PyPI: https://pypi.org/project/hermescheck/

## Thread Draft

1. `hermescheck` 1.3.0 is out. The core idea: an agent audit should inspect the
   knowledge layer, not just the code.

2. This release adds knowledge consistency checks: stale local doc paths,
   relative time language in durable docs, and missing root inventories for
   docs, memory, skills, and runbooks.

3. The goal is not to punish docs. The goal is to ask the target agent where
   its current source of truth lives before recommending code changes.

4. I also softened regex-heavy architecture findings. Orchestration, hidden
   LLM calls, tool enforcement, and pipeline middleware now read more like
   self-review prompts than automatic failure labels.

5. This makes `hermescheck` more useful for Hermes-style persistent agents:
   runtime contracts, memory, skills, docs, runbooks, and self-review all have
   to line up.

6. Repo: https://github.com/huangrichao2020/hermescheck
   PyPI: https://pypi.org/project/hermescheck/

## Hashtags

`#AIagents` `#HermesAgent` `#OpenSource` `#AgentArchitecture`
