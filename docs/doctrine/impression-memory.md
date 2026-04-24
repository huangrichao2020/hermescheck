# Impression Pointer Memory

Advanced agents need more than facts and skills.

Facts answer: "What is true?"

Skills answer: "How do I do this procedure?"

Impressions answer: "What does this remind me of, what tiny cue is enough right now, and where do I fault in the details if the cue is not enough?"

## Core Claim

An impression chunk is a lightweight associative memory. The stronger form is an **ImpressionPage**: a semantic anchor plus a pointer back to raw memory, files, vector entries, or skills.

The important idea is not "store a shorter summary." The important idea is "store a symbolic pointer."

Example:

> I live near Hangzhou Normal University in Yuhang. If I want to visit Longxiangqiao near West Lake, I do not need to memorize the whole Hangzhou metro map. I only need the impression that Line 5 can get me there. That cue is enough to start the trip and recover the details on demand.

This is the missing middle layer in many agent systems: not the whole metro map, not a rigid travel procedure, but a tiny route pointer.

## Three Memory Types

| Memory Type | Purpose | Example | Failure When Overused |
|-------------|---------|---------|-----------------------|
| Fact memory | Store assertions and preferences | "User lives near Hangzhou Normal University in Yuhang" | Becomes a database of disconnected claims |
| Skill memory | Store reusable procedures | "How to create an upstream PR" | Becomes rigid SOP execution |
| Impression pointer memory | Store associative cue plus retrieval pointer | "Yuhang to West Lake: Line 5, details at vec_88392" | Becomes vague if cue has no pointer or unsafe if treated as truth |

Impressions should be used as retrieval hints, not final evidence. The pointer is what keeps them honest.

## ImpressionPage Shape

An ImpressionPage should stay small enough to fit in the active prompt, but strong enough to recover the exact detail later:

```json
{
  "page_id": "imp_hz_line5_longxiangqiao",
  "topic_anchor": "Yuhang Hangzhou Normal University to West Lake Longxiangqiao",
  "cue": "Line 5 is the route hint",
  "semantic_hash": "yuhang-westlake-line5",
  "pointer_type": "vector_id",
  "pointer_ref": "vec_88392",
  "activation_level": 0.84,
  "last_accessed": 1777046400,
  "status": "IN_MIND"
}
```

Good ImpressionPages are:

- short
- associative
- connected to concepts
- pointer-backed
- easy to invalidate
- useful without deep retrieval when the cue is enough

They should not pretend to be:

- exact historical logs
- verified facts
- complete task procedures
- immutable user preferences

## Runtime Flow

Encoding:

The user explains a long route or a repeated project pattern. The agent does not keep the whole raw text in prompt. It writes raw detail to memory or vector storage, then keeps an ImpressionPage in the active page table:

```text
[impression] Yuhang <-> Longxiangqiao: Line 5
pointer_ref: vec_88392
```

Reasoning:

The user asks, "I am in Yuhang, how do I get to West Lake?" The active impression is enough. No deep retrieval is needed; the agent can answer from the cue.

Page fault:

The user asks, "Does Line 5 have elevators at the station?" The cue is not enough. The agent follows `pointer_ref` to fault in exact station facility data.

## Agent OS Mapping

In OS terms, an ImpressionPage is a page-table entry with a semantic anchor.

It is not raw memory. It is not the swapped page itself. It is the compact pointer that lets the runtime decide whether a cue is sufficient or whether to fault in a heavier page.

This is why it is stronger than summary-based paging:

- summary paging stores compressed text
- impression pointer paging stores a semantic anchor plus an address
- page fault retrieves the authoritative detail only when needed

## Scanner Implication

`hermescheck` should warn in two cases:

- a project has fact memory and skill memory but no sign of impression chunks
- a project has impression-like cues but no sign of pointers, page-table entries, or page-fault recovery

The warning does not mean every project needs a complex memory OS. It means the project may be missing the layer that turns isolated records into fast conceptual recall without stuffing the prompt with raw maps.
