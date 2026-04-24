# Target Agent Self-Review

`hermescheck` should not pretend that regex scanners understand every agent architecture.

The right model is a two-pass audit:

1. The target agent reviews itself with local context, source knowledge, runtime conventions, and project-specific methodology.
2. `hermescheck` runs its built-in static scanners as a stable external baseline.
3. The final report keeps both views visible: what the project says about itself, what the generic scanner sees, where they agree, and where a human should inspect the gap.

This turns `hermescheck` from a blunt scanner into an audit protocol.

## Why This Matters

Generic regex scanners are useful because they are cheap, reproducible, and language-light. They are bad at knowing intent.

A target agent often knows things the scanner cannot know:

- which provider implementation is intentional, not a hidden LLM path
- which memory surfaces are hot, cold, archived, or generated fixtures
- which tool wrapper is the real syscall boundary
- which workflow really completes file creation, index update, card creation, anchor mapping, pointer registration, and acceptance
- which docs are doctrine and which docs are stale examples

The target agent can also lie to itself. That is why `hermescheck` still runs the external scan.

## Methodology

Ask the target agent to produce a small self-review JSON before running `hermescheck`.

The self-review should be high-density and evidence-backed. It is not a marketing paragraph. It should say:

- what the target agent believes its architecture really is
- which scanner findings are likely true
- which scanner findings are likely false positives
- what its next improvement plan is
- what evidence path supports each claim

## Workflow

```bash
# 1. Ask the target agent to create self_review.json using the template below.

# 2. Run hermescheck with the self-review attached.
hermescheck . \
  --profile personal \
  --self-review self_review.json \
  -o audit_results.json \
  -r audit_report.md

# 3. Read the final report.
# The Target Agent Self-Review section should appear before raw findings.
```

## Template

```json
{
  "methodology_version": "target-agent-self-review.v1",
  "agent_name": "MyAgent",
  "summary": "I inspected my own source tree before hermescheck ran. My main loop lives in src/agent.py; tools are routed through src/tools/registry.py; memory is split into facts, skills, and impressions.",
  "claims": [
    {
      "title": "Provider implementations are intentional extension points",
      "evidence": "src/providers/openai.py",
      "recommendation": "If hermescheck flags this as hidden LLM usage, treat it as provider-aware false-positive evidence."
    }
  ],
  "risks": [
    {
      "title": "Completion closure can stop after file creation and index update",
      "evidence": "src/memory/write_memory.py",
      "recommendation": "Require file creation -> index update -> impression card -> anchor mapping -> pointer registration -> acceptance."
    }
  ],
  "false_positive_notes": [
    {
      "title": "Test fixture API keys are dummy strings",
      "evidence": "tests/fixtures/secrets.py",
      "recommendation": "Downgrade security severity unless the value is live or copied from production."
    }
  ],
  "improvement_plan": [
    {
      "title": "Add impression pointers",
      "evidence": "docs/memory.md",
      "recommendation": "Represent reusable recall as topic_anchor + semantic_hash + pointer_ref."
    }
  ],
  "confidence": 0.75
}
```

## Prompt

```text
请先按 hermescheck 的 target-agent-self-review 方法论审计你自己的源码和工作区，生成 self_review.json。不要只说文件是否创建，要检查完整闭环：文件创建 -> 索引更新 -> 印象卡片 -> 锚点映射 -> 指针注册 -> 验收。然后运行 hermescheck . --profile personal --self-review self_review.json，最后把你的自检结论、hermescheck 静态扫描结论、二者冲突点和下一步优化计划合成一份报告。
```

## Rule

The self-review does not override `hermescheck` findings. It contextualizes them.

When the target agent and `hermescheck` disagree, the report should treat that disagreement as a useful audit object:

- the scanner may be too generic
- the target agent may be rationalizing a real architecture smell
- the project may need clearer doctrine so future agents do not need to infer intent
