# Completion Closure

Agents often confuse local progress with reusable completion.

The bad pattern:

```text
file created -> index updated -> done
```

This is point-based work. It sees the file and the index, then declares success.

The better pattern:

```text
file creation -> index update -> impression card -> anchor mapping -> pointer registration -> acceptance
```

This is surface-based work. It asks whether the next agent can find, understand, and reuse the result.

## Why This Matters

An agent that works by intuition sees the local point:

- a file exists
- an index changed
- the command returned success

It misses the surrounding surface:

- is there an impression card?
- is the concept anchored?
- is there a pointer back to the raw detail?
- is the result discoverable next time?
- did we define acceptance as reuse, not just file existence?

The completion signal is fake if the next agent cannot quickly find and reuse the work.

## Methodology Role

Methodology is not a restriction on freedom. It is navigation for freedom.

It provides:

- acceptance criteria: "Can the next agent find this?"
- workflow shape: receive -> parse -> align -> implement -> index -> card -> verify
- counterexamples: stopping after file creation and index update is incomplete

## Scanner Implication

`hermescheck` should warn when a project has file creation and index update flows but lacks the closure signals that make the work reusable:

- impression card
- anchor mapping
- pointer registration
- acceptance criteria

This catches the common failure where an agent finishes the first two steps and calls the task done.
