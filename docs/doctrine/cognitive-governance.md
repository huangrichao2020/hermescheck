# Cognitive Governance

`how-to-agent` now treats cognition as a governed runtime loop, not as a larger
memory folder. `hermescheck` should audit that loop where it affects production
agent behavior.

## Runtime Principle

Every input surface is evidence first:

- channel messages
- Feishu or Lark documents
- task logs
- tool output
- restart events
- scheduled reports
- user-authored notes
- L5 diary material

The runtime should not let those signals become durable authority directly.
They pass through Purpose detection, attention gating, context assembly,
response or action, feedback capture, and admission.

## Authority Ladder

Durable cognition should be classified by the right to influence future action:

- Trace: raw evidence of what happened.
- Episode: bounded task or conversation context.
- Claim: provisional statement that may be true.
- Fact: current verified assertion with provenance and freshness.
- Knowledge: reusable explanation or pattern.
- Procedure: executable skill, SOP, checklist, or runbook.
- Identity: slow-changing operating posture and policy.
- Nourishment: interaction principles that leave the user clearer and stronger.
- L5 behavior: user-authored real-life evidence such as diary or voice notes.

This ladder can align with DIKWP, but Purpose is the steering layer. Purpose
decides which data matters, which information is relevant, which knowledge
should be activated, and which feedback should revise future behavior.

## Admission Store

An agent may propose durable cognition, but promotion should be explicit:

1. The agent writes candidate items to a pending admission store.
2. The UI strips hidden machine blocks from visible user output.
3. A user-visible admission act promotes scoped pending candidates.
4. Promotion records layer, source, confidence, provenance, freshness, and
   retirement rule.

Facts, knowledge, procedures, identity, nourishment, and L5 summaries should
not share one undifferentiated memory pile.

## Scheduled Cognition

Cron reports and dream reviews are evidence too. A scheduled report should be
written into same-day hot channel memory before the next conversation, or the
agent can report something and forget it immediately.

Dream review is a formal admission mechanism. It should list admitted items,
skipped reasons, and the expected effect on future behavior.

## L5 Diary Boundary

Raw diary text, voice dictation, and lived-day material are private evidence by
default. They can inform the agent only through admitted summaries.

One-day moods, failures, impulses, or body-state notes must not become
permanent user identity. The scanner should flag diary ingestion that lacks
local/private raw-text handling, approved summaries, and non-identity
boundaries.

## Scanner Signals

The `cognitive_runtime_governance` scanner looks for four separations:

- cognitive depth routing versus visible-output boundaries
- reflection capture versus memory admission governance
- cognition ladders versus Purpose and admission gates
- scheduled reports, dream reviews, and L5 diary material versus their
  hot-memory, admission, privacy, and identity boundaries
