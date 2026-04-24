"""Scan agent projects through an operating-system architecture lens."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from hermescheck.scanners.path_filters import should_skip_path

SCAN_EXTENSIONS = {
    ".py",
    ".ts",
    ".js",
    ".tsx",
    ".jsx",
    ".md",
    ".yaml",
    ".yml",
    ".toml",
    ".json",
}
SKIP_DIRS = {
    ".git",
    ".github",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    "coverage",
    "locales",
}
SKIP_FILENAMES = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
    "poetry.lock",
    "uv.lock",
}
MAX_FILE_BYTES = 250_000

PATTERNS = {
    "kernel": re.compile(
        r"\b(?:harness|orchestrator|scheduler|kernel|agent loop|react loop|main loop)\b", re.IGNORECASE
    ),
    "memory": re.compile(
        r"\b(?:context|memory|summary|compact|compression|rag|vector|embedding|history)\b", re.IGNORECASE
    ),
    "paging": re.compile(
        r"\b(?:page table|page fault|paging|swap(?: in| out)?|lru|hot data|cold data|heat score|ttl|recency|pin(?:ned)?)\b",
        re.IGNORECASE,
    ),
    "tool_syscall": re.compile(
        r"\b(?:tool use|tool call|tool_call|function calling|function_call|execute[_ -]?shell(?:_command)?|shell command|subprocess|system call|syscall)\b",
        re.IGNORECASE,
    ),
    "capability": re.compile(
        r"\b(?:syscall table|capability|capabilities|cap_[a-z0-9_]+|permission matrix|seccomp)\b",
        re.IGNORECASE,
    ),
    "scheduler": re.compile(
        r"\b(?:worker|swarm|queue|task|job|heartbeat|cron|scheduler|delegate|subagent)\b", re.IGNORECASE
    ),
    "fairness": re.compile(
        r"\b(?:time slice|timeslice|deadline|budget|priority|preempt|context switch|yield|cancel|cancellation|backpressure)\b",
        re.IGNORECASE,
    ),
    "semantic_storage": re.compile(
        r"\b(?:knowledge|skills?|rag|vector[_ -]?store|vectordb|embedding|docs?|notes?|github|resources?)\b",
        re.IGNORECASE,
    ),
    "vfs": re.compile(r"\b(?:vfs|virtual file|mount|mount point|resource path|semantic fs)\b", re.IGNORECASE),
    "context_replay": re.compile(
        r"\b(?:context replay|conversation replay|transcript replay|session replay|chat history|"
        r"stored conversation|conversation history|runstate|run state|previous_response_id|conversation id)\b|"
        r"(?:上下文回放|录像带|聊天记录|会话历史|读档)",
        re.IGNORECASE,
    ),
    "environment_state": re.compile(
        r"\b(?:environment state|environment is the state|filesystem state|file system state|workspace state|"
        r"working tree|server state|durable filesystem|durable workspace|persistent workspace|on-disk state)\b|"
        r"(?:环境即状态|环境状态|现场|服务器文件|硬盘|物理生效)",
        re.IGNORECASE,
    ),
    "side_effect_log": re.compile(
        r"\b(?:side[-_ ]?effect log|action log|operation log|audit log|journal|write[-_ ]?ahead|"
        r"commit log|trajectory|tool result|command output|execution record)\b|"
        r"(?:副作用记录|动作日志|操作日志|执行记录|工具结果|命令输出)",
        re.IGNORECASE,
    ),
    "idempotent_recovery": re.compile(
        r"\b(?:idempotent recovery|idempotent resume|retry[-_ ]?safe|resumable run|resume after interruption|"
        r"interrupted run|wake[-_ ]?up instruction|system interrupt|recovery checkpoint|durable execution)\b|"
        r"(?:幂等恢复|幂等续接|自动续接|唤醒指令|中断恢复|恢复检查点)",
        re.IGNORECASE,
    ),
    "llm_cli_worker": re.compile(
        r"\b(?:llm cli|cli agent|external llm|external code tool|coding agent cli|qwen[-_ ]?code|"
        r"qwen|codex|claude|gemini|opencode)\b.{0,80}\b(?:cli|command|subprocess|worker|spawn|process|pool)\b|"
        r"\b(?:subprocess\.run|subprocess\.Popen|create_subprocess_exec)\b.{0,120}\b(?:qwen|codex|claude|gemini|opencode)\b|"
        r"(?:外部\s*LLM|代码\s*CLI|CLI\s*进程池|命令行\s*worker|拉起\s*qwen|拉起\s*codex|拉起\s*claude)",
        re.IGNORECASE,
    ),
    "task_envelope": re.compile(
        r"\b(?:task json|task file|task envelope|work order|handoff file|job spec|delegation spec|"
        r"structured task|task manifest)\b|(?:任务\s*JSON|任务文件|任务信封|工作单|交接文件|结构化任务)",
        re.IGNORECASE,
    ),
    "cli_result_capture": re.compile(
        r"\b(?:stdout|stderr|exit code|returncode|capture_output|completedprocess|standard output|"
        r"process output|worker result)\b|(?:标准输出|标准错误|退出码|返回码|捕获输出|worker\s*结果)",
        re.IGNORECASE,
    ),
    "cli_process_control": re.compile(
        r"\b(?:process pool|worker pool|timeout|deadline|concurrency|semaphore|queue|cancel|cancellation|"
        r"asyncio\.create_subprocess_exec|subprocess\.run\(.{0,80}timeout)\b|(?:进程池|worker\s*池|超时|并发|取消|队列)",
        re.IGNORECASE,
    ),
}


@dataclass
class SignalSet:
    refs: dict[str, list[str]]

    def count(self, key: str) -> int:
        return len(self.refs.get(key, []))

    def evidence(self, *keys: str, limit: int = 8) -> list[str]:
        evidence_refs: list[str] = []
        seen: set[str] = set()
        for key in keys:
            for ref in self.refs.get(key, []):
                if ref not in seen:
                    evidence_refs.append(ref)
                    seen.add(ref)
                if len(evidence_refs) >= limit:
                    return evidence_refs
        return evidence_refs


def _should_skip(path: Path) -> bool:
    if path.name.lower() in SKIP_FILENAMES:
        return True
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return True
    except OSError:
        return True
    return should_skip_path(path, SKIP_DIRS)


def _collect_signals(target: Path) -> SignalSet:
    refs: dict[str, list[str]] = {key: [] for key in PATTERNS}
    files = [target] if target.is_file() else sorted(target.rglob("*"))
    for fp in files:
        if not fp.is_file() or _should_skip(fp) or fp.suffix not in SCAN_EXTENSIONS:
            continue

        try:
            lines = fp.read_text(encoding="utf-8", errors="ignore").splitlines()
        except (OSError, PermissionError):
            continue

        for lineno, line in enumerate(lines, start=1):
            for key, pattern in PATTERNS.items():
                if pattern.search(line):
                    refs[key].append(f"{fp}:{lineno}")
    return SignalSet(refs=refs)


def scan_os_architecture(target: Path) -> List[Dict[str, Any]]:
    signals = _collect_signals(target)
    findings: List[Dict[str, Any]] = []

    if signals.count("memory") >= 5 and signals.count("paging") < 2:
        findings.append(
            {
                "severity": "high",
                "title": "Context memory lacks paging policy",
                "symptom": (
                    f"Found {signals.count('memory')} memory/context/RAG markers but only "
                    f"{signals.count('paging')} paging-policy markers."
                ),
                "user_impact": (
                    "Without a hot/cold memory policy, context compression becomes a one-way summary step. "
                    "Agents either keep too much in prompt or lose details with no page-fault path to recover them."
                ),
                "source_layer": "os_memory",
                "mechanism": "OS-lens scan for memory, context compaction, RAG, and paging vocabulary.",
                "root_cause": (
                    "The project appears to manage context as linear text instead of virtual memory with active pages, "
                    "archived pages, and targeted swap-in."
                ),
                "evidence_refs": signals.evidence("memory", "paging"),
                "confidence": 0.7,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Introduce a context page table: active prompt pages, short-term memory pages, and long-term "
                    "archive pages. Add retrieval-triggered page faults so old details can be swapped back in on demand."
                ),
            }
        )

    if signals.count("tool_syscall") >= 3 and signals.count("capability") < 2:
        findings.append(
            {
                "severity": "medium",
                "title": "Tool syscalls lack explicit capability table",
                "symptom": (
                    f"Found {signals.count('tool_syscall')} tool/system-call markers but only "
                    f"{signals.count('capability')} capability or sandbox markers."
                ),
                "user_impact": (
                    "Tools are the agent equivalent of syscalls. If their permissions are implicit, it becomes hard "
                    "to reason about which calls can read, write, execute, access network, or mutate workspace state."
                ),
                "source_layer": "os_syscall",
                "mechanism": "OS-lens scan for tool/function-calling surfaces versus capability/sandbox vocabulary.",
                "root_cause": "The tool boundary appears to be described by code paths rather than a small syscall table.",
                "evidence_refs": signals.evidence("tool_syscall", "capability"),
                "confidence": 0.66,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Document a syscall table for tools. Give each tool explicit capabilities such as read, write, "
                    "execute, network, secrets, and workspace mutation, then map approval or sandbox behavior to them."
                ),
            }
        )

    if signals.count("scheduler") >= 5 and signals.count("fairness") < 2:
        findings.append(
            {
                "severity": "high",
                "title": "Agent scheduler lacks fairness controls",
                "symptom": (
                    f"Found {signals.count('scheduler')} worker/task/scheduler markers but only "
                    f"{signals.count('fairness')} timeout, priority, or budget markers."
                ),
                "user_impact": (
                    "Long-running tool calls or background workers can starve short user-visible tasks when the "
                    "runtime has no visible time slicing, priorities, cancellation, or budget accounting."
                ),
                "source_layer": "os_scheduler",
                "mechanism": "OS-lens scan for worker/swarm/queue/task surfaces versus fairness controls.",
                "root_cause": "The runtime appears to schedule work, but the scheduling policy is not explicit in code or docs.",
                "evidence_refs": signals.evidence("scheduler", "fairness"),
                "confidence": 0.69,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Add scheduler policy before adding more workers: per-task timeouts, user-command priority, "
                    "background-task budgets, cancellation, and a visible queue state for stuck or starved work."
                ),
            }
        )

    if signals.count("semantic_storage") >= 5 and signals.count("vfs") < 2:
        findings.append(
            {
                "severity": "medium",
                "title": "Knowledge surfaces lack semantic VFS",
                "symptom": (
                    f"Found {signals.count('semantic_storage')} knowledge/RAG/skill/storage markers but only "
                    f"{signals.count('vfs')} mount or VFS markers."
                ),
                "user_impact": (
                    "When local files, skills, docs, GitHub knowledge, and vector stores use separate access paths, "
                    "agents need custom routing logic instead of one predictable address space."
                ),
                "source_layer": "os_vfs",
                "mechanism": "OS-lens scan for knowledge and retrieval surfaces versus virtual filesystem vocabulary.",
                "root_cause": "External knowledge appears to be integrated as special-case retrieval rather than mounted storage.",
                "evidence_refs": signals.evidence("semantic_storage", "vfs"),
                "confidence": 0.64,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Define semantic mount points such as /workspace, /memory, /skills, /knowledge/github, and "
                    "/knowledge/docs. Let the agent use one resource addressing model while adapters handle storage."
                ),
            }
        )

    replay_markers = signals.count("context_replay") + signals.count("idempotent_recovery")
    if replay_markers >= 2 and (
        signals.count("environment_state") < 1
        or signals.count("side_effect_log") < 1
        or signals.count("idempotent_recovery") < 1
    ):
        findings.append(
            {
                "severity": "high",
                "title": "Stateful Agent recovery contract incomplete",
                "symptom": (
                    f"Found {signals.count('context_replay')} context-replay markers and "
                    f"{signals.count('idempotent_recovery')} resume/recovery markers, but only "
                    f"{signals.count('environment_state')} environment-state markers and "
                    f"{signals.count('side_effect_log')} side-effect log markers."
                ),
                "user_impact": (
                    "An agent that can replay chat history but cannot verify real workspace/server state may repeat "
                    "irreversible tool work or skip necessary recovery after an interrupted turn."
                ),
                "source_layer": "stateful_recovery",
                "mechanism": (
                    "OS-lens scan for context replay, durable environment state, side-effect logs, and idempotent resume."
                ),
                "root_cause": (
                    "The project appears to describe continuation as conversation memory, but not as a full stateful "
                    "runtime contract grounded in the actual environment and recorded side effects."
                ),
                "evidence_refs": signals.evidence(
                    "context_replay", "idempotent_recovery", "environment_state", "side_effect_log"
                ),
                "confidence": 0.68,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Define a Stateful Agent recovery contract: replay the transcript, inspect durable filesystem or "
                    "server state, read a side-effect/action log, then resume through idempotent checkpoints so completed "
                    "work is not repeated."
                ),
            }
        )

    if signals.count("llm_cli_worker") >= 2 and (
        signals.count("task_envelope") < 1
        or signals.count("cli_result_capture") < 1
        or signals.count("cli_process_control") < 1
    ):
        findings.append(
            {
                "severity": "medium",
                "title": "LLM CLI worker contract incomplete",
                "symptom": (
                    f"Found {signals.count('llm_cli_worker')} external LLM CLI worker markers, but only "
                    f"{signals.count('task_envelope')} task-envelope markers, "
                    f"{signals.count('cli_result_capture')} result-capture markers, and "
                    f"{signals.count('cli_process_control')} process-control markers."
                ),
                "user_impact": (
                    "Calling Qwen, Codex, Claude, or other LLM CLIs through shell processes is powerful, but without "
                    "a structured task file, captured stdout/stderr/exit status, and timeout/concurrency controls, "
                    "the master agent cannot reliably audit, retry, or summarize worker output."
                ),
                "source_layer": "llm_cli_workers",
                "mechanism": (
                    "OS-lens scan for external LLM/code CLI workers versus task envelopes, result capture, and "
                    "process-pool controls."
                ),
                "root_cause": (
                    "The project appears to treat external LLM CLIs as ad hoc shell calls rather than as bounded worker "
                    "processes with a clear input/output contract."
                ),
                "evidence_refs": signals.evidence(
                    "llm_cli_worker", "task_envelope", "cli_result_capture", "cli_process_control"
                ),
                "confidence": 0.66,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Define an LLM CLI worker contract: write a Task JSON file, spawn the CLI with timeout and "
                    "concurrency limits, capture stdout/stderr/exit code, and merge the worker result through the "
                    "master agent's normal context and observability pipeline."
                ),
            }
        )

    return findings
