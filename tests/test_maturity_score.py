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
                "loop_detector with max_iterations, retry_budget, circuit_breaker, same_args hash, and ask_to_continue",
                "syscall table with capabilities and permission matrix",
                "permission policy uses blocklist, allowlist, needs_approval, read_scope, write_scope, and temp_scope",
                "memory_type identity preference goal habit decision constraint episode reflection with top_k retrieval_budget confidence overlap dedupe active durable ttl decay",
                "external signal intake reads upstream issues PRs benchmarks and user feedback; source-level learning reads directory tree entrypoint main loop core class ADR and boundary analysis; pattern extraction turns design patterns into reusable patterns not copied code; constraint adaptation checks local constraints zero heavy dependencies lightweight 2GB RAM fit; small-step landing uses independent modules try/except fail-soft rollback; verification loop runs regression test smoke test acceptance and retro; hands-on live tool call validates the real endpoint; the lesson is crystallized into a methodology artifact, procedure skill, and impression fragment",
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
    assert "self-evolution loop" in score["strengths"]
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
                "loop_detector with max_iterations, retry_budget, circuit_breaker, same_args hash, and ask_to_continue",
                "syscall table with capabilities and permission matrix",
                "permission policy uses blocklist, allowlist, needs_approval, read_scope, write_scope, and temp_scope",
                "memory_type identity preference goal habit decision constraint episode reflection with top_k retrieval_budget confidence overlap dedupe active durable ttl decay",
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
    assert score["uncapped_penalty"] >= score["penalty"]
    assert score["pre_penalty_score"] <= score["capped_raw_points"]
    penalties = {item["title"]: item for item in score["penalty_breakdown"]}
    assert penalties["Impression pointers missing"]["total_penalty"] == 14
    assert penalties["Agent scheduler lacks fairness controls"]["total_penalty"] == 13
    assert score["score_formula"]


def test_maturity_score_heavily_penalizes_suicidal_self_restart(tmp_path: Path) -> None:
    (tmp_path / "agent_os.md").write_text(
        "\n".join(
            [
                "methodology: always-on gateway runtime safety checklist",
                "agent loop harness with tool_call and function_call",
                "graceful_restart drain active_agents checkpoint resume post_restart health_check",
            ]
        ),
        encoding="utf-8",
    )
    findings = [
        {"title": "Self-restart can kill its own control plane", "severity": "critical"},
    ]

    score = score_maturity(tmp_path, findings=findings)

    penalties = {item["title"]: item for item in score["penalty_breakdown"]}
    assert penalties["Self-restart can kill its own control plane"]["title_penalty"] == 25
    assert penalties["Self-restart can kill its own control plane"]["severity_penalty"] == 12
    assert penalties["Self-restart can kill its own control plane"]["total_penalty"] == 37
    assert score["score"] <= score["pre_penalty_score"] - 37


def test_maturity_score_penalizes_restart_without_recent_session_recall(tmp_path: Path) -> None:
    (tmp_path / "agent_os.md").write_text(
        "\n".join(
            [
                "methodology: always-on gateway runtime safety checklist",
                "agent loop harness with session history, memory, checkpoint, resume, and post_restart health_check",
            ]
        ),
        encoding="utf-8",
    )
    findings = [
        {"title": "Restart recovery loses recent session memory", "severity": "high"},
    ]

    score = score_maturity(tmp_path, findings=findings)

    penalties = {item["title"]: item for item in score["penalty_breakdown"]}
    assert penalties["Restart recovery loses recent session memory"]["title_penalty"] == 17
    assert penalties["Restart recovery loses recent session memory"]["severity_penalty"] == 5
    assert penalties["Restart recovery loses recent session memory"]["total_penalty"] == 22


def test_maturity_score_rewards_runtime_safety_governance(tmp_path: Path) -> None:
    (tmp_path / "runtime_safety.md").write_text(
        "\n".join(
            [
                "methodology: always-on agent runtime safety checklist",
                "loop_detector enforces max_iterations, retry_budget, circuit_breaker, same_args hash, timeout, and ask_to_continue",
                "permission policy includes blocklist, allowlist, auto-approved safe commands, needs_approval, read_scope, write_scope, and temp_scope",
                "memory_type identity preference goal decision constraint episode reflection with top_k retrieval_budget, confidence, overlap, dedupe, active durable ttl decay, and retention",
            ]
        ),
        encoding="utf-8",
    )

    score = score_maturity(tmp_path, findings=[])

    assert "permission policy" in score["strengths"]
    assert "memory lifecycle governance" in score["strengths"]
    assert any("page table" in milestone for milestone in score["next_milestones"])


def test_maturity_score_rewards_stateful_agent_primitives(tmp_path: Path) -> None:
    (tmp_path / "stateful_agent.md").write_text(
        "\n".join(
            [
                "methodology: recovery rubric for Stateful Agent runtime behavior",
                "context replay restores conversation history after an interrupted run",
                "restart recall loads recent session history after cold start and injects it as background context",
                "environment is the state: filesystem state, workspace state, and server state are inspected first",
                "side-effect log stores tool result and command output for idempotent recovery checkpoints",
            ]
        ),
        encoding="utf-8",
    )

    score = score_maturity(tmp_path, findings=[])

    assert "stateful recovery" in score["strengths"]
    assert "restart session recall" in score["strengths"]
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


def test_maturity_score_caps_projects_without_self_evolution_at_combustion(tmp_path: Path) -> None:
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
                "loop_detector with max_iterations, retry_budget, circuit_breaker, same_args hash, and ask_to_continue",
                "syscall table with capabilities and permission matrix",
                "permission policy uses blocklist, allowlist, needs_approval, read_scope, write_scope, and temp_scope",
                "memory_type identity preference goal decision constraint episode reflection with top_k retrieval_budget confidence overlap dedupe active durable ttl decay",
                "semantic VFS mount point /knowledge/docs and /skills resource path",
                "trace spans, eval, reward, telemetry",
            ]
        ),
        encoding="utf-8",
    )

    score = score_maturity(tmp_path, findings=[])

    assert score["era_key"] == "combustion_age"
    assert score["score"] == 65
    assert score["self_evolution_gate"]["detected"] is False
    assert score["self_evolution_gate"]["cap_applied"] is True
    assert any("自我进化闭环" in milestone for milestone in score["next_milestones"])


def test_maturity_score_rewards_self_evolution_loop(tmp_path: Path) -> None:
    (tmp_path / "evolution.md").write_text(
        "\n".join(
            [
                "methodology: self-evolution review rubric",
                "external signal intake watches upstream projects, issues, PRs, benchmarks, and user feedback",
                "source-level learning reads directory tree, entrypoint, main loop, core class, ADR, and boundary analysis",
                "pattern extraction keeps reusable design patterns, not copied code",
                "constraint adaptation checks local constraints, zero heavy dependencies, lightweight fit, and 2GB RAM",
                "small-step landing uses independent modules, try/except, fail-soft integration, and rollback",
                "verification loop runs regression test, smoke test, acceptance, and retro",
                "hands-on validation runs a live tool call against a real endpoint",
                "learning assetization crystallizes the result into a methodology artifact, procedure skill, and impression fragment",
            ]
        ),
        encoding="utf-8",
    )

    score = score_maturity(tmp_path, findings=[])

    assert score["self_evolution_gate"]["detected"] is True
    assert score["self_evolution_gate"]["cap_applied"] is False
    assert "self-evolution loop" in score["strengths"]
    assert "external signal intake" in score["strengths"]
    assert "verification closure" in score["strengths"]
    assert "hands-on validation" in score["strengths"]
    assert "learning assetization" in score["strengths"]
