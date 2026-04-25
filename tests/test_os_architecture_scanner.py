from __future__ import annotations

from pathlib import Path

from hermescheck.scanners.os_architecture import scan_os_architecture


def _titles(findings: list[dict]) -> list[str]:
    return [finding["title"] for finding in findings]


def test_os_architecture_flags_missing_agent_os_primitives(tmp_path: Path) -> None:
    (tmp_path / "react_agent.py").write_text(
        "\n".join(
            [
                "class ReactAgent:",
                "    def agent_loop(self):",
                "        context = self.context_compact(self.history)",
                "        memory = self.memory_manager.load_memory()",
                "        summary = self.memory_manager.summarize(context)",
                "        rag = self.vector_store.search(embedding=context)",
                "        self.execute_shell_command(command)",
                "        self.tool_call('execute_shell', command)",
                "        self.function_call(tool_name, args)",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "swarm.py").write_text(
        "\n".join(
            [
                "class Swarm:",
                "    def run(self):",
                "        self.worker_queue.add(task)",
                "        self.delegate_to_subagent(task)",
                "        self.scheduler.submit(job)",
                "        self.heartbeat.tick()",
                "        self.cron.enqueue(task)",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "knowledge.md").write_text(
        "\n".join(
            [
                "The agent loads skills.",
                "Docs are pulled from a separate adapter.",
                "GitHub resources use another path.",
                "Notes live in a different store.",
                "Knowledge and vector_store entries are routed separately.",
                "RAG and embeddings are separate from workspace files.",
            ]
        ),
        encoding="utf-8",
    )

    findings = scan_os_architecture(tmp_path)
    titles = _titles(findings)

    assert "Context memory lacks paging policy" in titles
    assert "Tool syscalls lack explicit capability table" in titles
    assert "Agent scheduler lacks fairness controls" in titles
    assert "Knowledge surfaces lack semantic VFS" in titles


def test_os_architecture_accepts_explicit_paging_capabilities_and_mounts(tmp_path: Path) -> None:
    (tmp_path / "runtime.md").write_text(
        "\n".join(
            [
                "The harness owns an agent loop with context, memory, RAG, vector store, embedding, and history.",
                "Context is tracked through a page table, hot data, cold data, LRU, and page fault swap in.",
                "Tool use and function calling go through a syscall table with capabilities and sandbox policy.",
                "Workers use a scheduler queue with timeout, priority, budget, preempt, and cancellation.",
                "Knowledge, skills, docs, GitHub resources, and notes are exposed through VFS mount points.",
                "The semantic filesystem provides /workspace, /memory, /skills, and /knowledge/docs resource paths.",
            ]
        ),
        encoding="utf-8",
    )

    assert scan_os_architecture(tmp_path) == []


def test_os_architecture_flags_incomplete_stateful_recovery_contract(tmp_path: Path) -> None:
    (tmp_path / "runtime.md").write_text(
        "\n".join(
            [
                "The agent supports context replay from chat history after an interrupted run.",
                "A system interrupt injects a wake-up instruction so a resumable run can continue.",
                "The design stops at conversation memory and never explains how real-world changes are verified.",
            ]
        ),
        encoding="utf-8",
    )

    findings = scan_os_architecture(tmp_path)

    assert "Stateful Agent recovery contract incomplete" in _titles(findings)


def test_os_architecture_accepts_stateful_recovery_contract(tmp_path: Path) -> None:
    (tmp_path / "runtime.md").write_text(
        "\n".join(
            [
                "Stateful Agent recovery starts with context replay from conversation history.",
                "The runner reads environment state from filesystem state, workspace state, and server state.",
                "Every tool result is stored in a side-effect log with command output and action log entries.",
                "Resume after interruption uses idempotent recovery checkpoints before the next tool call.",
            ]
        ),
        encoding="utf-8",
    )

    assert scan_os_architecture(tmp_path) == []


def test_os_architecture_flags_incomplete_llm_cli_worker_contract(tmp_path: Path) -> None:
    (tmp_path / "delegation.md").write_text(
        "\n".join(
            [
                "The master agent can spawn qwen as an external LLM CLI worker.",
                "It also shells out to codex command workers for code edits.",
                "The design does not define a structured input file or process lifecycle controls.",
            ]
        ),
        encoding="utf-8",
    )

    findings = scan_os_architecture(tmp_path)

    assert "LLM CLI worker contract incomplete" in _titles(findings)


def test_os_architecture_accepts_llm_cli_worker_contract(tmp_path: Path) -> None:
    (tmp_path / "delegation.md").write_text(
        "\n".join(
            [
                "The master agent owns a CLI process pool for external LLM CLI workers: qwen, codex, and claude.",
                "Each worker receives a Task JSON task envelope with context, files, and acceptance criteria.",
                "The worker stdin receives a natural-language prompt generated from that task envelope, not raw JSON.",
                "The supervisor captures stdout, stderr, exit code, returncode, and process output.",
                "Worker pool execution uses timeout, concurrency, cancellation, and queue controls.",
            ]
        ),
        encoding="utf-8",
    )

    assert scan_os_architecture(tmp_path) == []


def test_os_architecture_flags_cli_worker_without_prompt_contract(tmp_path: Path) -> None:
    (tmp_path / "delegation.md").write_text(
        "\n".join(
            [
                "The master agent owns a CLI process pool for external LLM CLI workers: qwen, codex, and claude.",
                "It spawns qwen and codex command workers for bounded code tasks.",
                "Each worker receives a Task JSON task envelope with context, files, and acceptance criteria.",
                "The supervisor captures stdout, stderr, exit code, returncode, and process output.",
                "Worker pool execution uses timeout, concurrency, cancellation, and queue controls.",
            ]
        ),
        encoding="utf-8",
    )

    findings = scan_os_architecture(tmp_path)

    assert "LLM CLI worker contract incomplete" in _titles(findings)
