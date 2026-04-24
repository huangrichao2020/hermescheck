# CLI Process Pool

A CLI process pool lets a master agent delegate work to external LLM code tools without building a socket protocol or permanent daemon.

The pattern is intentionally Unix-shaped:

```text
Master agent -> Task JSON -> qwen/codex/claude CLI worker -> stdout/stderr/exit code -> master agent
```

## Roles

- Master agent: decomposes the task, chooses the worker, writes the task envelope, starts the process, captures results, and merges the outcome.
- CLI worker: a short-lived Qwen, Codex, Claude, Gemini, or OpenCode process that reads the task file, does the work, and exits.
- Task envelope: a structured JSON file containing goal, context, file paths, constraints, acceptance criteria, and output contract.

## Hermes Angle

Hermes Agent already has the right runtime ingredients: a persistent master loop, tools, skills, session history, gateway work, and cron. A Hermes fork can use a CLI process pool to call external code agents for bounded work while keeping Hermes as the stateful coordinator.

This keeps the architecture simple. The external CLI does not need to become a daemon, socket server, or permanent subagent. It can be an inspectable worker process with a clear task file and captured output.

## Contract

A mature CLI process pool should define:

- which external LLM CLIs are allowed
- how the master writes Task JSON
- where stdout, stderr, exit code, and result artifacts are captured
- timeout, cancellation, concurrency, and retry policy
- how worker output is merged into the master context
- which filesystem or network capabilities each worker can use

## Scanner Implication

`hermescheck` rewards projects that describe LLM CLI workers and task envelopes.

It flags Hermes forks that mention Qwen, Codex, Claude, or other external LLM CLI workers but do not describe Task JSON, output capture, and process controls. Without that contract, CLI delegation becomes shell-shaped hidden orchestration instead of an auditable Hermes runtime primitive.
