"""Architecture-era scoring for social, comparable hermescheck reports."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from hermescheck.scanners.path_filters import should_skip_path

SCAN_EXTENSIONS = {".py", ".ts", ".js", ".tsx", ".jsx", ".md", ".txt", ".yaml", ".yml", ".toml", ".json"}
SKIP_DIRS = {".git", ".github", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "coverage", "locales"}
SKIP_FILENAMES = {"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "poetry.lock", "uv.lock"}
MAX_FILE_BYTES = 250_000


@dataclass(frozen=True)
class EraBand:
    key: str
    name: str
    min_score: int
    description: str


ERA_BANDS = (
    EraBand("stone_age", "石器时代", 0, "线性 prompt 和手工压缩为主，缺少稳定的 agent OS 原语。"),
    EraBand("bronze_age", "青铜时代", 20, "开始有事实、技能或工具，但边界和调度仍比较粗糙。"),
    EraBand("iron_age", "铁器时代", 35, "具备较清晰的工具、记忆和技能分层，开始可维护。"),
    EraBand("steam_age", "蒸汽机时代", 50, "出现调度、分页、压缩、外部知识等工程化能力，但效率仍靠堆结构。"),
    EraBand(
        "combustion_age", "内燃气时代", 65, "具备较强 runtime 动力系统，开始有 syscall、scheduler、paging 或 VFS 意识。"
    ),
    EraBand("new_energy_age", "新能源时代", 80, "OS 原语较完整，能用更低内耗管理记忆、工具、调度和知识挂载。"),
    EraBand("ai_age", "人工智能时代", 92, "具备可进化的 agent OS：印象指针、缺页换入、能力表、调度公平性和优化闭环。"),
)

SIGNAL_PATTERNS = {
    "methodology": re.compile(
        r"\b(?:methodology|doctrine|principles|rubric|checklist|anti[-_ ]?slop|information density|"
        r"prompt framework|review framework|design framework|quality framework|reference protocol)\b|"
        r"(?:方法论|方法框架|评审框架|检查清单|信息密度|反\s*slop|七维框架|"
        r"主体.{0,24}动作.{0,24}场景|风格.{0,24}构图.{0,24}光线|构图.{0,24}光线.{0,24}细节)",
        re.IGNORECASE,
    ),
    "agent_runtime": re.compile(
        r"\b(?:agent|react loop|agent loop|harness|orchestrator|swarm|subagent)\b|智能体", re.IGNORECASE
    ),
    "tool_syscalls": re.compile(
        r"\b(?:tool_call|tool use|function calling|function_call|execute_shell|subprocess|syscall)\b", re.IGNORECASE
    ),
    "fact_memory": re.compile(r"\b(?:facts?|preference|profile|entity|metadata)\b|(?:事实|偏好|画像)", re.IGNORECASE),
    "skill_memory": re.compile(
        r"\b(?:skills?|procedure|workflow|runbook|sop|playbook)\b|(?:技能|流程|经验)", re.IGNORECASE
    ),
    "linear_compaction": re.compile(
        r"\b(?:summary|summarize|compact|compression|previous_summary|context_compact)\b|(?:摘要|压缩)", re.IGNORECASE
    ),
    "paging": re.compile(
        r"\b(?:page table|page entry|paging|lru|hot data|cold data|swap(?: in| out)?)\b|(?:页表|分页|换入|换出)",
        re.IGNORECASE,
    ),
    "page_fault": re.compile(
        r"\b(?:page fault|deep dive|swap in|swap-in|fault in)\b|(?:缺页|深挖|换入)", re.IGNORECASE
    ),
    "impression": re.compile(
        r"\b(?:impression|cue|semantic hint|route hint|concept map|mental map)\b|(?:印象|联想|概念路标)", re.IGNORECASE
    ),
    "impression_pointer": re.compile(
        r"\b(?:topic_anchor|semantic_hash|pointer_ref|pointer_type|activation_level|in_mind|subconscious)\b|"
        r"(?:语义锚点|激活层级|潜意识)",
        re.IGNORECASE,
    ),
    "scheduler": re.compile(
        r"\b(?:scheduler|worker queue|task queue|cron|heartbeat|delegate|subagent)\b", re.IGNORECASE
    ),
    "fairness": re.compile(
        r"\b(?:time slice|timeslice|priority|budget|preempt|cancel|cancellation|backpressure|deadline)\b", re.IGNORECASE
    ),
    "capability_table": re.compile(
        r"\b(?:syscall table|capability|capabilities|cap_[a-z0-9_]+|permission matrix|seccomp)\b", re.IGNORECASE
    ),
    "semantic_vfs": re.compile(
        r"\b(?:vfs|virtual file|mount point|resource path|semantic fs|/knowledge|/skills|/memory)\b", re.IGNORECASE
    ),
    "observability": re.compile(
        r"\b(?:trace|tracing|telemetry|span|eval|evaluation|reward|cost tracking)\b", re.IGNORECASE
    ),
    "stateful_recovery": re.compile(
        r"\b(?:stateful agent|context replay|conversation replay|transcript replay|resumable run|"
        r"resume after interruption|idempotent recovery|idempotent resume|wake[-_ ]?up instruction|"
        r"system interrupt|durable execution|recovery checkpoint)\b|"
        r"(?:Stateful Agent|上下文回放|录像带|自动续接|唤醒指令|中断恢复|幂等恢复|恢复检查点)",
        re.IGNORECASE,
    ),
    "environment_state": re.compile(
        r"\b(?:environment state|environment is the state|filesystem state|file system state|workspace state|"
        r"working tree|server state|durable filesystem|durable workspace|persistent workspace|on-disk state|"
        r"side[-_ ]?effect log|action log|operation log|journal|tool result|command output)\b|"
        r"(?:环境即状态|环境状态|现场|服务器文件|硬盘|物理生效|副作用记录|动作日志|操作日志)",
        re.IGNORECASE,
    ),
    "llm_cli_workers": re.compile(
        r"\b(?:llm cli|cli agent|external llm|external code tool|coding agent cli|qwen[-_ ]?code|"
        r"qwen|codex|claude|gemini|opencode|process pool|worker pool)\b.{0,80}"
        r"\b(?:cli|command|subprocess|worker|spawn|process|pool)\b|"
        r"(?:外部\s*LLM|代码\s*CLI|CLI\s*进程池|命令行\s*worker|拉起\s*qwen|拉起\s*codex|拉起\s*claude)",
        re.IGNORECASE,
    ),
    "task_envelope": re.compile(
        r"\b(?:task json|task file|task envelope|work order|handoff file|job spec|delegation spec|"
        r"stdout|stderr|exit code|returncode|capture_output|process output)\b|"
        r"(?:任务\s*JSON|任务文件|任务信封|工作单|标准输出|退出码|捕获输出)",
        re.IGNORECASE,
    ),
    "cli_prompt_contract": re.compile(
        r"\b(?:natural language prompt|natural-language prompt|prompt text|worker prompt|stdin prompt|"
        r"to_prompt|task file path|read this task file|do not send raw json|not raw json|no raw json)\b|"
        r"(?:自然语言\s*Prompt|自然语言提示|worker\s*提示词|stdin\s*提示词|不要裸(?:扔|传)\s*JSON|不能裸(?:扔|传)\s*JSON)",
        re.IGNORECASE,
    ),
}

SIGNAL_POINTS = {
    "methodology": 12,
    "agent_runtime": 5,
    "tool_syscalls": 8,
    "fact_memory": 6,
    "skill_memory": 7,
    "linear_compaction": 5,
    "paging": 10,
    "page_fault": 8,
    "impression": 8,
    "impression_pointer": 12,
    "scheduler": 8,
    "fairness": 8,
    "capability_table": 8,
    "semantic_vfs": 8,
    "observability": 7,
    "stateful_recovery": 10,
    "environment_state": 8,
    "llm_cli_workers": 8,
    "task_envelope": 7,
    "cli_prompt_contract": 4,
}

SIGNAL_LABELS = {
    "methodology": "methodology layer",
    "agent_runtime": "agent runtime",
    "tool_syscalls": "tool/syscall boundary",
    "fact_memory": "fact memory",
    "skill_memory": "skill memory",
    "linear_compaction": "context compaction",
    "paging": "semantic paging",
    "page_fault": "page-fault recovery",
    "impression": "impression cues",
    "impression_pointer": "impression pointers",
    "scheduler": "scheduler/workers",
    "fairness": "fair scheduling",
    "capability_table": "capability table",
    "semantic_vfs": "semantic VFS",
    "observability": "traces/evals",
    "stateful_recovery": "stateful recovery",
    "environment_state": "environment-as-state",
    "llm_cli_workers": "LLM CLI workers",
    "task_envelope": "task envelope",
    "cli_prompt_contract": "CLI prompt contract",
}

MILESTONES = {
    "methodology": "先沉淀高信息密度方法论：维度框架、检查清单、反 slop 规则和示例，而不是只堆 skill/MCP。",
    "paging": "把线性 summary/compact 升级为 page table、LRU/hot-cold 和 swap-in。",
    "page_fault": "给被压缩或归档的细节加 page fault/deep-dive 恢复路径。",
    "impression_pointer": "把 impression cue 升级成 topic_anchor + semantic_hash + pointer_ref。",
    "fairness": "为 worker/tool/subagent 增加 priority、budget、cancel 和 backpressure。",
    "capability_table": "把工具边界整理成 syscall/capability table，而不是散落在代码里。",
    "semantic_vfs": "把 skills、RAG、docs、GitHub、notes 挂到统一 semantic VFS 地址空间。",
    "observability": "保留 traces/evals，让 agent 的进化可以被复盘和比较。",
    "stateful_recovery": "把自动续接做成 Stateful Agent 契约：context replay + environment state + side-effect log + idempotent recovery。",
    "environment_state": "把 filesystem/server/workspace 状态纳入可验证状态模型，恢复时先读取现场再决定下一步。",
    "llm_cli_workers": "把 Qwen/Codex/Claude 等外部 CLI 当作 bounded worker process，而不是临时 shell 魔法。",
    "task_envelope": "用 Task JSON + stdout/stderr/exit code + timeout/concurrency 控制定义 CLI worker 的输入输出契约。",
    "cli_prompt_contract": "Task JSON 用于审计和任务文件，传给 Qwen/Codex stdin 的应是自然语言 Prompt 或任务文件引用。",
}

FINDING_PENALTIES = {
    "Context memory lacks paging policy": 10,
    "Impression memory layer missing": 10,
    "Impression pointers missing": 12,
    "Agent scheduler lacks fairness controls": 8,
    "Tool syscalls lack explicit capability table": 8,
    "Knowledge surfaces lack semantic VFS": 7,
    "Stateful Agent recovery contract incomplete": 8,
    "LLM CLI worker contract incomplete": 7,
    "Internal orchestration sprawl detected": 6,
    "Memory freshness / generation confusion detected": 6,
    "Role-play handoff orchestration detected": 5,
}


def _should_skip(path: Path) -> bool:
    if path.name.lower() in SKIP_FILENAMES:
        return True
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return True
    except OSError:
        return True
    return should_skip_path(path, SKIP_DIRS)


def _collect_signal_refs(target: Path) -> dict[str, list[str]]:
    refs = {key: [] for key in SIGNAL_PATTERNS}
    files = [target] if target.is_file() else sorted(target.rglob("*"))
    for fp in files:
        if not fp.is_file() or _should_skip(fp) or fp.suffix not in SCAN_EXTENSIONS:
            continue
        path_text = "/".join(fp.parts)
        try:
            lines = fp.read_text(encoding="utf-8", errors="ignore").splitlines()
        except (OSError, PermissionError):
            continue

        for key, pattern in SIGNAL_PATTERNS.items():
            if pattern.search(path_text):
                refs[key].append(f"{fp}:1")

        for lineno, line in enumerate(lines, start=1):
            for key, pattern in SIGNAL_PATTERNS.items():
                if pattern.search(line):
                    refs[key].append(f"{fp}:{lineno}")
    return refs


def _era_for_score(score: int) -> EraBand:
    era = ERA_BANDS[0]
    for band in ERA_BANDS:
        if score >= band.min_score:
            era = band
    return era


def _finding_penalty(findings: list[dict[str, Any]]) -> int:
    penalty = 0
    severity_penalty = {"critical": 12, "high": 5, "medium": 2, "low": 0}
    for finding in findings:
        title = finding.get("title", "")
        penalty += FINDING_PENALTIES.get(title, 0)
        penalty += severity_penalty.get(finding.get("severity", "low"), 0)
    return min(penalty, 45)


def score_maturity(target: Path, findings: list[dict[str, Any]]) -> dict[str, Any]:
    """Return a comparable social maturity score for an agent project."""

    signal_refs = _collect_signal_refs(target)
    detected = {key: refs for key, refs in signal_refs.items() if refs}
    raw_points = sum(SIGNAL_POINTS[key] for key in detected)
    penalty = _finding_penalty(findings)
    score = max(0, min(100, raw_points - penalty))
    has_methodology = "methodology" in detected
    methodology_cap_applied = False
    if has_methodology:
        score = max(score, 20)
    else:
        methodology_cap_applied = score > 34
        score = min(score, 34)
    era = _era_for_score(score)

    strengths = [SIGNAL_LABELS[key] for key in SIGNAL_POINTS if key in detected]
    missing_milestones = [
        MILESTONES[key]
        for key in (
            "methodology",
            "paging",
            "page_fault",
            "stateful_recovery",
            "environment_state",
            "llm_cli_workers",
            "task_envelope",
            "impression_pointer",
            "fairness",
            "capability_table",
            "semantic_vfs",
            "observability",
        )
        if key not in detected
    ]

    evidence_refs: list[str] = []
    seen: set[str] = set()
    for key in SIGNAL_POINTS:
        for ref in detected.get(key, [])[:2]:
            if ref not in seen:
                evidence_refs.append(ref)
                seen.add(ref)
            if len(evidence_refs) >= 12:
                break
        if len(evidence_refs) >= 12:
            break

    return {
        "score": score,
        "raw_points": raw_points,
        "penalty": penalty,
        "era_key": era.key,
        "era_name": era.name,
        "era_description": era.description,
        "share_line": f"这个 Agent 项目处于 {era.name}（{score}/100）：{era.description}",
        "methodology_gate": {
            "detected": has_methodology,
            "cap_applied": methodology_cap_applied,
            "note": (
                "已发现方法论层，项目具备进入青铜以上时代的地基。"
                if has_methodology
                else "未发现清晰方法论层，时代评分封顶在青铜时代。"
            ),
        },
        "strengths": strengths,
        "next_milestones": missing_milestones[:5],
        "evidence_refs": evidence_refs,
    }
