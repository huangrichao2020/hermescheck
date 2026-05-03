from __future__ import annotations

from pathlib import Path

from hermescheck.audit import run_audit
from hermescheck.config import AuditConfig
from hermescheck.scanners.capability_policy import scan_capability_policy
from hermescheck.scanners.daemon_lifecycle import scan_daemon_lifecycle
from hermescheck.scanners.loop_safety import scan_loop_safety
from hermescheck.scanners.memory_lifecycle import scan_memory_lifecycle
from hermescheck.scanners.memory_retrieval_i18n import scan_memory_retrieval_i18n


def _titles(findings: list[dict]) -> list[str]:
    return [finding["title"] for finding in findings]


def test_loop_safety_scanner_is_disabled_for_large_codebases(tmp_path: Path) -> None:
    (tmp_path / "agent.py").write_text(
        "\n".join(
            [
                "def agent_loop(task):",
                "    while True:",
                "        tool_call('shell', task)",
                "        function_call('repair', task)",
                "        retry_provider(task)",
            ]
        ),
        encoding="utf-8",
    )

    assert scan_loop_safety(tmp_path) == []


def test_loop_safety_stays_disabled_even_with_detector_terms(tmp_path: Path) -> None:
    (tmp_path / "agent.py").write_text(
        "\n".join(
            [
                "MAX_STEPS = 20",
                "def agent_loop(task):",
                "    for step in range(MAX_STEPS):",
                "        if loop_detector.seen_same_args(args_hash(task)):",
                "            ask_to_continue(task)",
                "        tool_call('shell', task, timeout=30)",
                "        retry_with_backoff(task, retry_budget=3)",
            ]
        ),
        encoding="utf-8",
    )

    assert scan_loop_safety(tmp_path) == []


def test_loop_safety_ignores_partial_tool_path_observation(tmp_path: Path) -> None:
    (tmp_path / "agent.py").write_text(
        "\n".join(
            [
                "def _invoke_tool(name, args):",
                "    loop_detector.record(name, args)",
                "    return dispatch_tool(name, args)",
                "",
                "def _run_single_tool_call(name, args):",
                "    result = dispatch_tool(name, args)",
                "    return result",
            ]
        ),
        encoding="utf-8",
    )

    assert scan_loop_safety(tmp_path) == []


def test_loop_safety_ignores_scheduled_work_markers(tmp_path: Path) -> None:
    (tmp_path / "scheduler.ts").write_text(
        "\n".join(
            [
                "export function runDaemon() {",
                "  setInterval(() => scheduler.enqueue(job), 1000)",
                "  heartbeat.tick()",
                "  cron.schedule('* * * * *', task)",
                "  workerQueue.push(backgroundTask)",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    assert scan_loop_safety(tmp_path) == []


def test_capability_policy_flags_high_agency_agent_without_layers(tmp_path: Path) -> None:
    (tmp_path / "agent.py").write_text(
        "\n".join(
            [
                "import subprocess, os, requests",
                "class Agent:",
                "    def tool_call(self, command):",
                "        subprocess.run(command, shell=True)",
                "        os.system(command)",
                "        requests.post(url, json=data)",
            ]
        ),
        encoding="utf-8",
    )

    findings = scan_capability_policy(tmp_path)

    assert "High-agency tools lack layered permission policy" in _titles(findings)


def test_capability_policy_accepts_layered_policy(tmp_path: Path) -> None:
    (tmp_path / "policy.py").write_text(
        "\n".join(
            [
                "BLOCKLIST = ['rm -rf /', 'sudo *']",
                "AUTO_APPROVED = {'ls', 'cat', 'git status'}",
                "NEEDS_APPROVAL = {'git push', 'npm publish', 'docker *'}",
                "READ_SCOPE = ['/workspace']",
                "WRITE_SCOPE = ['/workspace/output']",
                "def agent_tool_call(command):",
                "    require_approval(command)",
                "    subprocess.run(command, shell=True)",
                "    os.system(command)",
                "    requests.post(url, json=data)",
            ]
        ),
        encoding="utf-8",
    )

    assert scan_capability_policy(tmp_path) == []


def test_capability_policy_flags_partial_dispatch_enforcement(tmp_path: Path) -> None:
    (tmp_path / "agent.py").write_text(
        "\n".join(
            [
                "import subprocess, os, requests",
                "BLOCKLIST = ['sudo *', 'rm -rf /']",
                "AUTO_APPROVED = {'ls'}",
                "NEEDS_APPROVAL = {'git push'}",
                "READ_SCOPE = ['/workspace']",
                "",
                "class Agent:",
                "    def _invoke_tool(self, command):",
                "        decision = PermissionEngine().check_permission(command)",
                "        if decision.denied:",
                "            return decision.reason",
                "        return subprocess.run(command, shell=True)",
                "",
                "    def _run_single_tool_call(self, command):",
                "        os.system(command)",
                "        requests.post(url, json={'command': command})",
            ]
        ),
        encoding="utf-8",
    )

    findings = scan_capability_policy(tmp_path)

    assert "Permission policy is not enforced on all dispatch paths" in _titles(findings)


def test_memory_lifecycle_flags_memory_without_governance(tmp_path: Path) -> None:
    (tmp_path / "memory.py").write_text(
        "\n".join(
            [
                "class MemoryStore:",
                "    def remember(self, memory): self.memories.append(memory)",
                "    def recall(self, query): return self.vector_store.search(query)",
                "    def summarize_history(self): return self.summary",
                "    def save_profile(self, profile): self.profile = profile",
                "    def save_preference(self, preference): self.preference = preference",
                "    def load_facts(self): return self.facts",
                "    def reflect(self): return self.reflection",
            ]
        ),
        encoding="utf-8",
    )

    findings = scan_memory_lifecycle(tmp_path)

    assert "Memory system lacks lifecycle governance" in _titles(findings)


def test_memory_lifecycle_accepts_typed_budgeted_decay_memory(tmp_path: Path) -> None:
    (tmp_path / "memory_design.md").write_text(
        "\n".join(
            [
                "Memory types: identity, preference, goal, project, habit, decision, constraint, episode, reflection.",
                "Retrieval uses FTS5 and top_k=5 with a token_budget and character_limit.",
                "Each memory has confidence; conflicts are resolved by confidence, overlap, merge, and dedupe.",
                "Active memories can become durable after reinforcement; TTL, decay, retention, prune, and dismissed state exist.",
                "Each record keeps pointer_ref, source_ref, topic_anchor, semantic_hash, and page fault swap in metadata.",
                "Memory GC keeps only rules/facts that still need to be followed; delete completed-work notes after landing.",
                "The agent can remember, recall, summarize history, and update profile facts.",
            ]
        ),
        encoding="utf-8",
    )

    assert scan_memory_lifecycle(tmp_path) == []


def test_memory_lifecycle_flags_missing_active_retention_gc(tmp_path: Path) -> None:
    (tmp_path / "memory_policy.md").write_text(
        "\n".join(
            [
                "Memory types: identity, preference, goal, project, habit, decision, constraint, episode, reflection.",
                "Retrieval uses FTS5 and top_k=5 with a token_budget and character_limit.",
                "Each memory has confidence; conflicts are resolved by confidence, overlap, merge, and dedupe.",
                "Active memories can become durable after reinforcement; TTL, decay, retention, prune, and archive exist.",
                "Each record keeps pointer_ref, source_ref, topic_anchor, semantic_hash, and page fault swap in metadata.",
                "The agent can remember task progress, completed_work notes, finished task summaries, and session outcomes.",
                "Memory recall loads profile facts, preferences, reflection summaries, and history into the agent.",
                "The second brain memory store saves facts and episode summaries for future sessions.",
            ]
        ),
        encoding="utf-8",
    )

    findings = scan_memory_lifecycle(tmp_path)

    assert "Memory retention lacks active-rule GC policy" in _titles(findings)
    finding = next(f for f in findings if f["title"] == "Memory retention lacks active-rule GC policy")
    assert finding["severity"] == "high"
    assert "delete or skip the completed-work memory" in finding["recommended_fix"]


def test_memory_retrieval_i18n_flags_unicode61_without_cjk_fallback(tmp_path: Path) -> None:
    (tmp_path / "second_brain.py").write_text(
        "\n".join(
            [
                "def init_memory(conn):",
                "    conn.execute(\"CREATE VIRTUAL TABLE memories_fts USING fts5(summary, detail, tokenize='unicode61')\")",
                "    # 中文偏好 and multilingual memory should be searchable.",
                "",
                "def search_memory(conn, query):",
                "    return conn.execute('SELECT * FROM memories_fts WHERE memories_fts MATCH ?', (query,)).fetchall()",
            ]
        ),
        encoding="utf-8",
    )

    findings = scan_memory_retrieval_i18n(tmp_path)

    assert "Memory FTS lacks CJK-safe retrieval path" in _titles(findings)


def test_memory_retrieval_i18n_accepts_runtime_cjk_fallback_without_audit_test_scope(tmp_path: Path) -> None:
    (tmp_path / "second_brain.py").write_text(
        "\n".join(
            [
                "def tokenize_for_fts(text):",
                "    # CJK ngram tokenizer for 中文检索",
                "    return build_trigram_tokens(text)",
                "",
                "def search_memory(conn, query):",
                "    match = fts_match_query(query)",
                "    rows = conn.execute('SELECT * FROM memories_fts WHERE memories_fts MATCH ?', (match,)).fetchall()",
                "    return rows or like_fallback(query)",
            ]
        ),
        encoding="utf-8",
    )

    assert scan_memory_retrieval_i18n(tmp_path) == []


def test_memory_retrieval_i18n_accepts_cjk_fallback_with_tests(tmp_path: Path) -> None:
    (tmp_path / "second_brain.py").write_text(
        "\n".join(
            [
                "def tokenize_for_fts(text):",
                "    # CJK ngram tokenizer for 中文检索",
                "    return build_trigram_tokens(text)",
                "",
                "def search_memory(conn, query):",
                "    match = fts_match_query(query)",
                "    rows = conn.execute('SELECT * FROM memories_fts WHERE memories_fts MATCH ?', (match,)).fetchall()",
                "    return rows or like_fallback(query)",
            ]
        ),
        encoding="utf-8",
    )
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_memory_i18n.py").write_text(
        "def test_chinese_memory_retrieval(): assert search('中文回复？？()')\n",
        encoding="utf-8",
    )

    assert scan_memory_retrieval_i18n(tmp_path) == []


def test_runtime_scanners_skip_test_and_fixture_paths(tmp_path: Path) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "agent.test.ts").write_text(
        "\n".join(
            [
                "export async function fixtureAgent() {",
                "  await execute_shell('rm -rf /tmp/example')",
                "  await function_call('admin_browser_evaluate')",
                "}",
            ]
        ),
        encoding="utf-8",
    )
    fixtures_dir = tmp_path / "fixtures"
    fixtures_dir.mkdir()
    (fixtures_dir / "dangerous-agent.ts").write_text(
        "export const safe_commands = ['rm -rf /tmp/example']\n",
        encoding="utf-8",
    )

    assert scan_capability_policy(tmp_path) == []


def test_daemon_lifecycle_flags_restart_without_drain(tmp_path: Path) -> None:
    (tmp_path / "gateway.py").write_text(
        "\n".join(
            [
                "class GatewayDaemon:",
                "    def run_forever(self):",
                "        heartbeat.tick()",
                "",
                "    def restart(self):",
                "        old_pid = read_pid_file()",
                "        terminate(old_pid)",
                "        spawn_gateway_replace()",
            ]
        ),
        encoding="utf-8",
    )

    findings = scan_daemon_lifecycle(tmp_path)

    assert "Daemon restart lacks active-work drain protocol" in _titles(findings)


def test_daemon_lifecycle_flags_suicidal_self_restart(tmp_path: Path) -> None:
    (tmp_path / "gateway.py").write_text(
        "\n".join(
            [
                "import subprocess",
                "class GatewayDaemon:",
                "    def run_forever(self):",
                "        heartbeat.tick()",
                "",
                "    def restart_from_inside_active_turn(self):",
                "        subprocess.run(",
                "            'systemctl stop hermes-gateway && sleep 2 && systemctl start hermes-gateway',",
                "            shell=True,",
                "        )",
            ]
        ),
        encoding="utf-8",
    )

    findings = scan_daemon_lifecycle(tmp_path)
    by_title = {finding["title"]: finding for finding in findings}

    assert by_title["Self-restart can kill its own control plane"]["severity"] == "critical"


def test_daemon_lifecycle_accepts_externalized_self_restart_handoff(tmp_path: Path) -> None:
    (tmp_path / "gateway.py").write_text(
        "\n".join(
            [
                "import subprocess",
                "class GatewayDaemon:",
                "    def safe_restart(self):",
                "        active_agents = gateway_state.active_agents",
                "        wait_for_idle(active_agents)",
                "        drain_job_queue()",
                "        checkpoint_sessions_for_resume()",
                "        load_recent_session_recall(limit=5, source='feishu')",
                "        subprocess.run(['systemd-run', '--on-active=2s', 'systemctl', 'restart', 'hermes-gateway.service'])",
                "        post_restart_health_check(status='connected')",
            ]
        ),
        encoding="utf-8",
    )

    assert scan_daemon_lifecycle(tmp_path) == []


def test_daemon_lifecycle_accepts_drain_recovery_and_verification(tmp_path: Path) -> None:
    (tmp_path / "gateway.py").write_text(
        "\n".join(
            [
                "class GatewayDaemon:",
                "    def safe_restart(self):",
                "        active_agents = gateway_state.active_agents",
                "        wait_for_idle(active_agents)",
                "        drain_job_queue()",
                "        checkpoint_sessions_for_resume()",
                "        inject_startup_recall_context(load_recent_sessions(limit=5))",
                "        old_pid = read_pid_file()",
                "        restart_barrier(old_pid)",
                "        post_restart_health_check(status='connected')",
            ]
        ),
        encoding="utf-8",
    )

    assert scan_daemon_lifecycle(tmp_path) == []


def test_daemon_lifecycle_flags_restart_without_recent_session_recall(tmp_path: Path) -> None:
    (tmp_path / "gateway.py").write_text(
        "\n".join(
            [
                "class GatewayDaemon:",
                "    def run_forever(self):",
                "        # always on gateway service",
                "        service_heartbeat.tick()",
                "",
                "    def restart(self):",
                "        active_agents = gateway_state.active_agents",
                "        wait_for_idle(active_agents)",
                "        drain_job_queue()",
                "        checkpoint_sessions_for_resume()",
                "        old_pid = read_pid_file()",
                "        restart_barrier(old_pid)",
                "        post_restart_health_check(status='connected')",
                "        session_store.save_message(user_message)",
            ]
        ),
        encoding="utf-8",
    )

    findings = scan_daemon_lifecycle(tmp_path)
    by_title = {finding["title"]: finding for finding in findings}

    assert by_title["Restart recovery loses recent session memory"]["severity"] == "high"
    assert (
        "bounded recent-session recall packet"
        in by_title["Restart recovery loses recent session memory"]["recommended_fix"]
    )


def test_new_runtime_scanners_are_enabled_in_personal_audits(tmp_path: Path) -> None:
    (tmp_path / "agent.py").write_text(
        "\n".join(
            [
                "import subprocess, os, requests",
                "def agent_loop(task):",
                "    while True:",
                "        tool_call('shell', task)",
                "        function_call('repair', task)",
                "        subprocess.run(task.command, shell=True)",
                "        os.system(task.command)",
                "        requests.post(url, json=task.data)",
            ]
        ),
        encoding="utf-8",
    )

    results = run_audit(str(tmp_path), config=AuditConfig.from_profile("personal"), verbose=False)
    titles = [finding["title"] for finding in results["findings"]]

    assert "High-agency tools lack layered permission policy" in titles
