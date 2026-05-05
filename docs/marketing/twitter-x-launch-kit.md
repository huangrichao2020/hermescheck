# hermescheck Twitter/X Launch Kit

Use this file as the public posting base for `hermescheck` releases. Keep the
message centered on `hermescheck`; mention `agchk` only as prior art when it is
useful context.

## Positioning

`hermescheck` is a Hermes Agent-focused architecture health-check tool for
stateful AI agents. It scans for runtime contracts, restart continuity, memory
freshness, gateway/tool boundaries, observability, and release evidence.

## Short Post

`hermescheck` 1.3.3 is out.

It now treats cognitive runtime mechanisms as part of agent architecture:

- cognitive depth routing needs visible-output boundaries
- post-turn reflection needs memory admission governance
- runtime sidecars need budgets and fail-soft behavior
- gateway timeouts should evict stale cached agents

Hermes-style agents are persistent systems. `hermescheck` is evolving toward
audits that check runtime structure, memory, and the cognitive mechanisms that
shape each turn.

GitHub: https://github.com/huangrichao2020/hermescheck
PyPI: https://pypi.org/project/hermescheck/

## Thread Draft

1. `hermescheck` 1.3.3 is out. The core idea: cognitive runtime mechanisms are
   architecture, not just prompt flavor.

2. This release adds checks for cognitive-depth routing, post-turn reflection
   governance, runtime sidecar safety, and gateway timeout cache eviction.

3. A depth router should say both how deeply to process a turn and where the
   visible answer should stop.

4. Post-turn reflection should be structured, compact, confidence-scored, and
   reviewed before it becomes durable memory.

5. Runtime sidecars like loop detectors and context sandboxes should be
   bounded and fail-soft, so they improve the agent without blocking the task.

6. Repo: https://github.com/huangrichao2020/hermescheck
   PyPI: https://pypi.org/project/hermescheck/

## Hashtags

`#AIagents` `#HermesAgent` `#OpenSource` `#AgentArchitecture`
