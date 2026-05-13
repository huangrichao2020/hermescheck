# hermescheck Twitter/X Launch Kit

Use this file as the public posting base for `hermescheck` releases. Keep the
message centered on `hermescheck`; mention `agchk` only as prior art when it is
useful context.

## Positioning

`hermescheck` is a Hermes Agent-focused architecture health-check tool for
stateful AI agents. It scans for runtime contracts, restart continuity, memory
freshness, gateway/tool boundaries, observability, and release evidence.

## Short Post

`hermescheck` 1.3.4 is out.

It now checks the architecture separations that keep persistent agents calm:

- long Feishu/chat tasks need progress and conclusion streams
- memory needs current facts, skills, session history, and cold archives split
- self-evolution needs proposal, evidence, risk, validation, and rollback
- sidecars need a primary runtime path and fail-soft boundaries
- completion needs live evidence, not just edited files

This release folds the newest `how-to-agent` lessons into `hermescheck`, plus
PNG report cards for sharing audit results.

GitHub: https://github.com/huangrichao2020/hermescheck
PyPI: https://pypi.org/project/hermescheck/

## Thread Draft

1. `hermescheck` 1.3.4 is out. The core idea: excellent agent architecture is a
   set of explicit separations.

2. Long-running chat gateways should split progress/status output from final
   conclusions. Editing one rich-text message forever is brittle.

3. Memory needs authority boundaries: current facts, procedures/skills,
   searchable session history, and cold archives are not the same layer.

4. Self-evolution needs a ratchet: proposal, evidence, risk classification,
   validation plan, rollback plan, apply gate, and post-change audit.

5. Sidecars should be bounded and fail-soft, dependency fixes should be ordered
   by runtime blast radius, and completion should close with live evidence.

6. Repo: https://github.com/huangrichao2020/hermescheck
   PyPI: https://pypi.org/project/hermescheck/

## Hashtags

`#AIagents` `#HermesAgent` `#OpenSource` `#AgentArchitecture`
