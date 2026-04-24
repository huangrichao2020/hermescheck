# Stateful Agent

A Stateful Agent is not a model that magically remembers. The model core is still stateless between calls. The runtime becomes stateful when it can reconstruct enough evidence to continue work correctly.

The useful formula is:

```text
Stateful Agent = context replay + environment state + side-effect log + idempotent recovery
```

## Three Layers

### Context Replay

The transcript, session history, tool calls, tool outputs, and compacted summaries are the replay tape. On a new turn, the runtime can load the tape and understand what had been planned, attempted, completed, or interrupted.

Context replay is necessary, but it is not enough. A transcript can say "delete the archive," but only the filesystem can prove whether the archive is already gone.

### Environment Is The State

Agent work often changes the outside world: files move, commits appear, servers restart, package versions publish, tickets update, databases mutate.

That environment is part of the agent's state. After interruption, the recovery loop should inspect the real workspace, filesystem, server, database, queue, or remote API before deciding whether to retry, skip, or advance.

This is the line between a chatbot and an agent runtime. The chatbot remembers text. The agent can verify the scene.

### System Wakeup

An interrupted run needs an explicit wakeup instruction: resume the interrupted task, skip small talk, read the replay tape, inspect the environment, and continue from the next safe checkpoint.

The wakeup instruction should not blindly re-run the last command. It should trigger recovery logic.

## Hermes Angle

Hermes Agent already has many surfaces that can make this real: SessionDB, command history, skills, gateway activity, cron jobs, tool environments, and deployment files. A Hermes fork should make clear which of those surfaces are replay tape, which are durable environment state, and which side effects need idempotent resume.

This matters for gateway messages, scheduled jobs, tool execution, package updates, and long-running local agent work. A resumed Hermes run should first check the scene, then continue.

## Recovery Contract

A project that claims Stateful Agent behavior should document these answers:

- What transcript or session store is replayed?
- Which environment surfaces count as durable state?
- Where are tool results, command outputs, and irreversible side effects recorded?
- Which operations are idempotent, retry-safe, or guarded by idempotency keys?
- On resume, what evidence makes the agent skip completed work?
- What evidence makes the agent retry failed or missing work?

## Scanner Implication

`hermescheck` treats Stateful Agent as an OS-level recovery primitive.

It flags Hermes forks that mention context replay, resumable runs, or interrupted turns but do not name environment state, side-effect logs, and idempotent recovery. A strong Hermes runtime should recover from the physical state of the work, not only from what the conversation says happened.

Related runtime references:

- LangGraph durable execution: https://docs.langchain.com/oss/python/langgraph/durable-execution
- OpenAI Agents SDK sessions: https://openai.github.io/openai-agents-js/guides/sessions/
- OpenAI conversation state: https://developers.openai.com/api/docs/guides/conversation-state
