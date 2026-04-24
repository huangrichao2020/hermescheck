# Architecture Era Score

`hermescheck` gives each scanned project a social, comparable architecture-era score.

The score is not a security grade. It is a runtime maturity signal: how far the project has evolved from raw prompt stuffing toward an agent operating system.

## Methodology Gate

Methodology is the foundation of information density.

Skills and MCP tools can execute work, but methodology lets an agent carry a high-density concept in very few tokens. A good methodology is closer to a compressed operating principle than to a long instruction file.

Example:

```text
[主体] + [动作] + [场景] + [风格] + [构图] + [光线] + [细节]
```

That seven-dimension frame is more valuable than a pile of loose image-prompt tips. It gives the agent a compact way to ask the right questions before generating output.

Scoring rule:

- If methodology is missing, the project is capped at 青铜时代, even if it has many tools, skills, or runtime pieces.
- If methodology is present, the project can enter 青铜时代 and above, then OS primitives decide how far it goes.

## Era Ladder

| Era | Score Range | Meaning |
|-----|-------------|---------|
| 石器时代 | 0-19 | Linear prompt stuffing, manual summaries, and little visible runtime structure |
| 青铜时代 | 20-34 | Basic facts, skills, or tools exist, but boundaries remain rough |
| 铁器时代 | 35-49 | Memory, tools, and skills are becoming maintainable subsystems |
| 蒸汽机时代 | 50-64 | Scheduling, compaction, RAG, and external knowledge appear, but efficiency still comes from piling on machinery |
| 内燃气时代 | 65-79 | Runtime power improves through scheduler, syscall, paging, or VFS primitives |
| 新能源时代 | 80-91 | Most agent OS primitives are present and reduce internal drag |
| 人工智能时代 | 92-100 | The runtime can evolve: impression pointers, page faults, capability tables, fair scheduling, semantic mounts, and traces are visible |

## What Raises The Score

The score rewards concrete runtime primitives:

- methodology layer
- agent runtime or harness
- tool/syscall boundary
- fact memory
- skill memory
- context compaction
- semantic paging
- page-fault recovery
- impression cues
- impression pointers
- scheduler/workers
- fair scheduling controls
- capability table
- semantic VFS
- traces/evals
- stateful recovery
- environment-as-state

## What Lowers The Score

Findings subtract points. The largest deductions come from architecture gaps that create internal drag:

- methodology layer is missing, which caps the era at 青铜时代
- context memory lacks paging policy
- impression memory or impression pointers are missing
- scheduler lacks fairness controls
- tool syscalls lack an explicit capability table
- knowledge surfaces lack semantic VFS
- context replay exists without a Stateful Agent recovery contract
- orchestration sprawl or role-play handoffs dominate the runtime

## Why This Is Social

The score produces a shareable line such as:

> This agent project is in the 蒸汽机时代 (58/100).

That line is intentionally simple. It lets maintainers compare projects, celebrate upgrades, and talk about architecture without drowning in scanner details.

The serious part is the evidence underneath: `strengths`, `next_milestones`, and `evidence_refs` explain why the project got that era and what would move it forward.
