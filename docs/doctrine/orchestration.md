# Orchestration Doctrine

Agent architecture should be judged by information flow, not by how naturally it resembles a human organization chart.

## Core Claim

Good multi-agent design is usually one intent owner forking independent exploration, then merging evidence back into a coherent decision.

Weak multi-agent design often looks like a company:

- PM agent
- architect agent
- coder agent
- QA agent
- reviewer agent
- manager agent

This is easy to explain and easy to draw. It is not automatically good engineering.

## Why Role Charts Fail

Serial handoffs leak context. Every "next agent" receives a compressed version of the task, inherits the previous agent's framing mistakes, and then adds another layer of local reasoning. The system can look busy while the original user intent gets thinner at each step.

The common symptom is local correctness with global confusion:

- the planner has a reasonable plan
- the executor follows a reasonable subset of it
- the reviewer critiques a stale or partial view
- the final answer no longer matches the user's actual intent

## Better Default

Use agents when the work benefits from:

- independent search coverage
- context isolation
- adversarial review
- uncertain exploration

Use tools when the work is:

- bounded
- repeatable
- easy to test
- mostly deterministic

Do not turn every tool into a persona. A command, script, validator, formatter, or parser is usually stronger as a tool than as a role-playing agent.

## Scanner Implication

`hermescheck` should not warn merely because a project has multiple agents.

It should warn when a project combines:

- many role-labeled agents
- serial handoff language
- pipeline-style delegation
- weak evidence merging back to a single owner of intent

The finding is architectural, not moral. It asks the maintainer to re-check whether the system is doing real parallel reasoning or just acting out an org chart.
