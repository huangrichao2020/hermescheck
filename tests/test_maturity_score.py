from __future__ import annotations

from pathlib import Path

from hermescheck.maturity import score_maturity


def test_maturity_score_marks_linear_compaction_as_stone_age(tmp_path: Path) -> None:
    (tmp_path / "base_memory_manager.py").write_text(
        "\n".join(
            [
                "def compact_memory(messages):",
                "    previous_summary = summarize(messages[:20])",
                "    return previous_summary",
            ]
        ),
        encoding="utf-8",
    )

    score = score_maturity(tmp_path, findings=[])

    assert score["era_key"] == "stone_age"
    assert score["era_name"] == "石器时代"
    assert "context compaction" in score["strengths"]
    assert score["methodology_gate"]["detected"] is False
    assert any("page table" in milestone for milestone in score["next_milestones"])


def test_maturity_score_rewards_agent_os_primitives(tmp_path: Path) -> None:
    (tmp_path / "agent_os.md").write_text(
        "\n".join(
            [
                "agent loop harness with tool_call and function_call",
                "methodology: seven-dimension review framework with anti-slop checklist",
                "facts, preferences, skills, workflow, context_compact, summary",
                "page table, paging, LRU, hot data, cold data, swap in",
                "page fault and deep dive retrieval",
                "impression cue with topic_anchor, semantic_hash, pointer_type, pointer_ref, activation_level",
                "scheduler worker queue with priority, budget, cancellation, backpressure",
                "syscall table with capabilities and permission matrix",
                "semantic VFS mount point /knowledge/docs and /skills resource path",
                "trace spans, eval, reward, telemetry",
            ]
        ),
        encoding="utf-8",
    )

    score = score_maturity(tmp_path, findings=[])

    assert score["era_key"] == "ai_age"
    assert score["era_name"] == "人工智能时代"
    assert score["score"] >= 92
    assert score["methodology_gate"]["detected"] is True
    assert "impression pointers" in score["strengths"]
    assert "semantic VFS" in score["strengths"]


def test_maturity_score_caps_projects_without_methodology_at_bronze(tmp_path: Path) -> None:
    (tmp_path / "agent_os.md").write_text(
        "\n".join(
            [
                "agent loop harness with tool_call and function_call",
                "facts, preferences, skills, workflow, context_compact, summary",
                "page table, paging, LRU, hot data, cold data, swap in",
                "page fault and deep dive retrieval",
                "impression cue with topic_anchor, semantic_hash, pointer_type, pointer_ref, activation_level",
                "scheduler worker queue with priority, budget, cancellation, backpressure",
                "syscall table with capabilities and permission matrix",
                "semantic VFS mount point /knowledge/docs and /skills resource path",
                "trace spans, eval, reward, telemetry",
            ]
        ),
        encoding="utf-8",
    )

    score = score_maturity(tmp_path, findings=[])

    assert score["era_key"] == "bronze_age"
    assert score["score"] == 34
    assert score["methodology_gate"]["detected"] is False
    assert score["methodology_gate"]["cap_applied"] is True


def test_maturity_score_methodology_unlocks_bronze_floor(tmp_path: Path) -> None:
    (tmp_path / "methodology.md").write_text(
        "\n".join(
            [
                "七维框架: [主体] + [动作] + [场景] + [风格] + [构图] + [光线] + [细节]",
                "反 slop 检查清单: 每个维度必须回答一个高信息密度问题。",
            ]
        ),
        encoding="utf-8",
    )

    score = score_maturity(tmp_path, findings=[])

    assert score["era_key"] == "bronze_age"
    assert score["score"] == 20
    assert "methodology layer" in score["strengths"]


def test_maturity_score_does_not_unlock_methodology_for_loose_dimension_words(tmp_path: Path) -> None:
    (tmp_path / "notes.md").write_text(
        "\n".join(
            [
                "主体需要清楚。",
                "动作可以更具体。",
                "场景还没决定。",
            ]
        ),
        encoding="utf-8",
    )

    score = score_maturity(tmp_path, findings=[])

    assert score["methodology_gate"]["detected"] is False
    assert "methodology layer" not in score["strengths"]


def test_maturity_score_penalizes_architecture_findings(tmp_path: Path) -> None:
    (tmp_path / "agent_os.md").write_text(
        "\n".join(
            [
                "agent loop with context memory skills workflow",
                "impression cue but no pointer page table",
                "scheduler worker queue",
            ]
        ),
        encoding="utf-8",
    )
    findings = [
        {"title": "Impression pointers missing", "severity": "medium"},
        {"title": "Agent scheduler lacks fairness controls", "severity": "high"},
    ]

    score = score_maturity(tmp_path, findings=findings)

    assert score["penalty"] > 0
    assert score["score"] < score["raw_points"]


def test_maturity_score_rewards_stateful_agent_primitives(tmp_path: Path) -> None:
    (tmp_path / "stateful_agent.md").write_text(
        "\n".join(
            [
                "methodology: recovery rubric for Stateful Agent runtime behavior",
                "context replay restores conversation history after an interrupted run",
                "environment is the state: filesystem state, workspace state, and server state are inspected first",
                "side-effect log stores tool result and command output for idempotent recovery checkpoints",
            ]
        ),
        encoding="utf-8",
    )

    score = score_maturity(tmp_path, findings=[])

    assert "stateful recovery" in score["strengths"]
    assert "environment-as-state" in score["strengths"]


def test_maturity_score_rewards_llm_cli_worker_primitives(tmp_path: Path) -> None:
    (tmp_path / "cli_workers.md").write_text(
        "\n".join(
            [
                "methodology: CLI worker delegation rubric",
                "The master agent uses a CLI process pool to spawn qwen, codex, and claude command workers.",
                "Each external LLM CLI receives a Task JSON task envelope and returns stdout, stderr, and exit code.",
                "The worker stdin receives a natural-language prompt generated from that task envelope, not raw JSON.",
                "The supervisor captures process output with timeout and concurrency controls.",
            ]
        ),
        encoding="utf-8",
    )

    score = score_maturity(tmp_path, findings=[])

    assert "LLM CLI workers" in score["strengths"]
    assert "task envelope" in score["strengths"]
    assert "CLI prompt contract" in score["strengths"]
