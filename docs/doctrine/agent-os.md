# Agent As Operating System

The strongest architecture metaphor for modern agents is not "agent as employee." It is "agent runtime as operating system."

The model is computation. The harness is the kernel. Tools are syscalls. Context is memory. RAG and skills are mounted storage. Workers and subagents are processes or threads. A mature agent system should make those boundaries visible.

## Mapping

| OS Concept | Agent Concept | What `hermescheck` Should Ask |
|------------|---------------|--------------------------|
| Process / thread | Agent / subagent / worker | Are workers isolated, cancellable, and communicating explicitly? |
| System call | Tool use / function calling | Is there a small syscall table with declared capabilities? |
| Virtual memory | Context window / memory / summaries | Is there a hot/cold paging policy and a page-fault path? |
| Cache / swap | Short-term memory / long-term archive | Can the runtime swap in the exact old detail instead of reloading everything? |
| Scheduler | Harness / orchestrator | Are timeouts, priorities, budgets, and cancellation explicit? |
| VFS / mount point | RAG / skills / knowledge | Can the agent address external knowledge through one resource namespace? |
| Ring boundary | Sandbox / approval / isolation | Is high-agency execution separated from normal reasoning? |

## Design Principles

Keep the kernel small. The orchestrator should own scheduling, permissions, state transitions, and recovery. It should not become a pile of business logic.

Treat context as scarce memory. A context compactor that only summarizes is closer to lossy logging than memory management. Stronger systems track what is hot, what is cold, what is pinned, and how an old detail returns when needed.

Treat tools as syscalls. A tool is a controlled hole through the reasoning boundary. It should have a declared capability surface: read, write, execute, network, secrets, workspace mutation, and external side effects.

Treat RAG as mounted storage. Skills, docs, GitHub references, notes, and vector stores should not require separate routing instincts. They should be addressable through stable mount points such as `/workspace`, `/memory`, `/skills`, `/knowledge/github`, and `/knowledge/docs`.

Treat scheduling as a product feature. User-visible work should not be starved by background jobs, long tools, heartbeats, or stuck workers. Priority, timeout, cancellation, and queue visibility are architecture primitives.

## Scanner Implication

The `os_architecture` scanner looks for projects that already have agent OS symptoms but do not name the matching OS primitive:

- memory and context compaction without paging
- tool calling without a syscall or capability table
- workers and queues without fairness controls
- RAG, skills, and docs without semantic mount points

The finding is not saying "build a full OS." It is saying the project has crossed the line where OS vocabulary becomes the cleanest way to reduce internal drag.
