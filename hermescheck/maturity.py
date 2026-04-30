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
    "permission_policy": re.compile(
        r"\b(?:blocklist|denylist|allowlist|whitelist|auto[-_ ]?approved|needs[_ -]?approval|"
        r"read[_ -]?scope|write[_ -]?scope|path[_ -]?scope|temp[_ -]?scope)\b",
        re.IGNORECASE,
    ),
    "memory_lifecycle": re.compile(
        r"\b(?:memory[_ -]?type|identity|preference|goal|habit|decision|constraint|episode|reflection|"
        r"confidence|overlap|dedupe|active|durable|ttl|decay|reinforce|retention|top[_ -]?k|retrieval[_ -]?budget)\b",
        re.IGNORECASE,
    ),
    "memory_retrieval_i18n": re.compile(
        r"\b(?:cjk|unicode61|ngram|bi[-_ ]?gram|tri[-_ ]?gram|custom[_ -]?tokenizer|like[_ -]?fallback|"
        r"multilingual[_ -]?retrieval|reindex|rebuild[_ -]?index)\b|(?:中文检索|中文分词|多语言检索)",
        re.IGNORECASE,
    ),
    "rag_governance": re.compile(
        r"\b(?:rag|retrieval[_ -]?augmented|knowledge[_ -]?base|vector[_ -]?(?:store|db)|embedding|"
        r"chunk[_ -]?(?:size|overlap)|rerank|hybrid[_ -]?search|bm25|top[_ -]?k|retrieval[_ -]?budget)\b",
        re.IGNORECASE,
    ),
    "token_efficiency": re.compile(
        r"(?:<\s*30k|不到\s*30k|30k context|token[_ -]?(?:efficient|budget)|context[_ -]?budget|"
        r"layered memory|right knowledge|less noise|crystalliz(?:e|es|ing)|skill tree|direct recall|"
        r"\bL[0-4]\b|top[_ -]?k|retrieval[_ -]?budget|page[_ -]?table|极致省\s*Token|分层记忆|"
        r"关键信息始终在场|固化为\s*Skill|下次同类任务直接调用)",
        re.IGNORECASE,
    ),
    "external_signal": re.compile(
        r"\b(?:external[_ -]?signal|signal[_ -]?(?:intake|screening)|upstream|reference[_ -]?project|"
        r"competitor|benchmark|issue|pull request|pr|release note|production log|user feedback|github trend)\b|"
        r"(?:外部信号|信号筛选|热门项目|用户反馈|线上日志|上游项目)",
        re.IGNORECASE,
    ),
    "dissection_learning": re.compile(
        r"\b(?:source[_ -]?reading|read[_ -]?source|code archaeology|architecture review|directory tree|"
        r"entrypoint|main loop|core class|adr|design doc|decision record|boundary analysis)\b|"
        r"(?:解剖学习|读源码|目录结构|主入口|核心类|设计决策|边界分析)",
        re.IGNORECASE,
    ),
    "pattern_extraction": re.compile(
        r"\b(?:pattern[_ -]?extraction|extract(?:ed)? pattern|design pattern|reusable pattern|generalize|"
        r"generalization|not copy|not copied|not a code copy|anti[_ -]?copy)\b|"
        r"(?:提取模式|设计模式|举一反三|不是照搬|不照搬|不是代码副本)",
        re.IGNORECASE,
    ),
    "constraint_adaptation": re.compile(
        r"\b(?:constraint[_ -]?adapt(?:ation)?|fit constraints|local constraints|zero heavy dependencies|"
        r"no heavy dependenc(?:y|ies)|lightweight|2gb ram|bounded resource|integrate with existing)\b|"
        r"(?:约束适配|本地约束|零重型依赖|轻量|2GB|融入已有)",
        re.IGNORECASE,
    ),
    "safe_landing": re.compile(
        r"\b(?:small[_ -]?step|minimal implementation|independent module|isolated module|try/except|"
        r"fail[_ -]?soft|non[_ -]?intrusive|feature flag|rollback|bounded change)\b|"
        r"(?:小步落地|最小实现|独立模块|不侵入|可回滚|失败不影响)",
        re.IGNORECASE,
    ),
    "verification_closure": re.compile(
        r"\b(?:verification[_ -]?loop|validation loop|eval|regression test|smoke test|acceptance|"
        r"self[_ -]?test|test passed|post[_ -]?change review|retro|lesson learned)\b|"
        r"(?:验证闭环|回归测试|烟测|验收|复盘|教训)",
        re.IGNORECASE,
    ),
    "hands_on_validation": re.compile(
        r"\b(?:hands[_ -]?on|real[_ -]?world|live[_ -]?(?:run|test|endpoint|tool call)|"
        r"end[_ -]?to[_ -]?end|e2e|practical[_ -]?(?:run|validation)|manual[_ -]?acceptance|"
        r"worked example|validated with real|production[_ -]?like|satisfied)\b|"
        r"(?:实战|跑通|真实(?:调用|端点|工具)|端到端|实际验证|真实验证|满意后|验满意)",
        re.IGNORECASE,
    ),
    "learning_assetization": re.compile(
        r"\b(?:asseti[sz]ation|crystalliz(?:e|es|ed|ing)|teachback|methodology artifact|"
        r"skill package|skill card|procedure skill|impression fragment|impression snippet|"
        r"memory imprint|lesson card|runbook artifact|reusable playbook)\b|"
        r"(?:资产化|固化|沉淀|方法论.{0,24}技能.{0,24}印象|技能包|技能卡|印象片段|"
        r"印象碎片|工作手册|交接手册|可复用流程)",
        re.IGNORECASE,
    ),
    "semantic_vfs": re.compile(
        r"\b(?:vfs|virtual file|mount point|resource path|semantic fs|/knowledge|/skills|/memory)\b", re.IGNORECASE
    ),
    "daemon_lifecycle": re.compile(
        r"\b(?:graceful[_ -]?restart|safe[_ -]?restart|drain|active[_ -]?(?:agents|jobs|runs)|"
        r"restart[_ -]?barrier|checkpoint|resume|post[_ -]?restart|gateway[_ -]?state|old pid|new pid)\b",
        re.IGNORECASE,
    ),
    "plugin_sandbox": re.compile(
        r"\b(?:plugin|function|pipe|valves|exec\s*\(|dynamic[_ -]?import|sandbox|allowed[_ -]?packages|"
        r"package[_ -]?allowlist|plugin[_ -]?permission|plugin[_ -]?scope)\b",
        re.IGNORECASE,
    ),
    "remote_tool_boundary": re.compile(
        r"\b(?:mcp|model[_ -]?context[_ -]?protocol|openapi|swagger|tool[_ -]?server|remote[_ -]?tool|"
        r"trusted[_ -]?servers|schema[_ -]?version|schema[_ -]?validation|allowed[_ -]?servers)\b",
        re.IGNORECASE,
    ),
    "middleware_observability": re.compile(
        r"\b(?:pipeline|middleware|filter|inbound|outbound|raw[_ -]?message|transformed[_ -]?message|"
        r"audit[_ -]?log|filter[_ -]?order|fail[_ -]?(?:open|closed))\b",
        re.IGNORECASE,
    ),
    "observability": re.compile(
        r"\b(?:trace|tracing|telemetry|span|eval|evaluation|reward|cost tracking|logger|logging|"
        r"audit[_ -]?log|event[_ -]?log|run[_ -]?log|operation[_ -]?log|heartbeat|status[_ -]?update)\b|"
        r"(?:运行日志|审计日志|操作日志|事件日志|心跳|状态中转)",
        re.IGNORECASE,
    ),
    "evidence_logging": re.compile(
        r"\b(?:before[_ -]?after|before/after|evidence|evidence_refs?|changed_files?|commands?_run|"
        r"stdout|stderr|exit[_ -]?code|returncode|diff|snapshot|verification|smoke[_ -]?test|"
        r"health[_ -]?check|acceptance)\b|(?:前后对比|证据|验收|验证|烟测|健康检查|命令输出|退出码)",
        re.IGNORECASE,
    ),
    "handoff_workbook": re.compile(
        r"\b(?:handoff|hand[-_ ]?over|runbook|workbook|work[_ -]?manual|operations[_ -]?manual|"
        r"playbook|sop|WORK_LOG|HANDOFF|postmortem|lesson learned)\b|"
        r"(?:交接手册|工作手册|运维手册|接手手册|交接文档|工作日志|复盘|经验沉淀)",
        re.IGNORECASE,
    ),
    "stateful_recovery": re.compile(
        r"\b(?:stateful agent|context replay|conversation replay|transcript replay|resumable run|"
        r"resume after interruption|idempotent recovery|idempotent resume|wake[-_ ]?up instruction|"
        r"system interrupt|durable execution|recovery checkpoint)\b|"
        r"(?:Stateful Agent|上下文回放|录像带|自动续接|唤醒指令|中断恢复|幂等恢复|恢复检查点)",
        re.IGNORECASE,
    ),
    "restart_session_recall": re.compile(
        r"\b(?:restart[_ -]?recall|startup[_ -]?recall|cold[-_ ]?start[_ -]?(?:recall|context)|"
        r"post[_ -]?restart[_ -]?(?:recall|memory|context)|recent[_ -]?(?:session|conversation|chat|"
        r"history|transcript)[_ -]?(?:recall|context|replay)|load[_ -]?recent[_ -]?(?:sessions|"
        r"history|messages)|list_recent_sessions|get_session_messages)\b|"
        r"(?:重启恢复.{0,24}(?:会话|记忆|上下文)|启动恢复.{0,24}(?:会话|记忆|上下文)|"
        r"最近.{0,12}会话.{0,12}(?:恢复|召回|注入)|近期.{0,12}会话.{0,12}(?:恢复|召回|注入))",
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

EVOLUTION_SIGNAL_KEYS = (
    "external_signal",
    "dissection_learning",
    "pattern_extraction",
    "constraint_adaptation",
    "safe_landing",
    "verification_closure",
    "hands_on_validation",
    "learning_assetization",
)

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
    "permission_policy": 9,
    "memory_lifecycle": 10,
    "memory_retrieval_i18n": 7,
    "rag_governance": 8,
    "token_efficiency": 10,
    "external_signal": 4,
    "dissection_learning": 5,
    "pattern_extraction": 5,
    "constraint_adaptation": 5,
    "safe_landing": 5,
    "verification_closure": 6,
    "hands_on_validation": 6,
    "learning_assetization": 7,
    "semantic_vfs": 8,
    "daemon_lifecycle": 7,
    "plugin_sandbox": 8,
    "remote_tool_boundary": 8,
    "middleware_observability": 7,
    "observability": 7,
    "evidence_logging": 8,
    "handoff_workbook": 6,
    "stateful_recovery": 10,
    "restart_session_recall": 12,
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
    "permission_policy": "permission policy",
    "memory_lifecycle": "memory lifecycle governance",
    "memory_retrieval_i18n": "multilingual memory retrieval",
    "rag_governance": "RAG governance",
    "token_efficiency": "token-efficient context layer",
    "external_signal": "external signal intake",
    "dissection_learning": "source-level learning",
    "pattern_extraction": "pattern extraction",
    "constraint_adaptation": "constraint adaptation",
    "safe_landing": "small-step landing",
    "verification_closure": "verification closure",
    "hands_on_validation": "hands-on validation",
    "learning_assetization": "learning assetization",
    "semantic_vfs": "semantic VFS",
    "daemon_lifecycle": "daemon lifecycle safety",
    "plugin_sandbox": "plugin sandbox policy",
    "remote_tool_boundary": "remote tool boundary",
    "middleware_observability": "middleware observability",
    "observability": "traces/evals",
    "evidence_logging": "before/after evidence logging",
    "handoff_workbook": "handoff/workbook habit",
    "stateful_recovery": "stateful recovery",
    "restart_session_recall": "restart session recall",
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
    "permission_policy": "把高权限工具纳入 blocklist、allowlist、needs-approval 和 read/write scope 的分层权限模型。",
    "memory_lifecycle": "给长期记忆增加类型、检索预算、冲突合并、active/durable 生命周期、衰减和证据指针。",
    "memory_retrieval_i18n": "给 FTS/SQLite 记忆检索增加 CJK-safe tokenizer、fallback、reindex 和多语言回归测试。",
    "rag_governance": "给 RAG 增加 chunk、retrieval budget、rerank、ingestion 状态和 full-context 预算约束。",
    "token_efficiency": "学习 GenericAgent 的省 token 路线：<30K 热上下文、分层记忆、skill 复用、top-k/page-table 召回和成本指标。",
    "self_evolution_loop": (
        "建立自我进化闭环：外部信号、源码解剖、模式提取、约束适配、小步落地、验证复盘、实战跑通和资产化沉淀。"
    ),
    "external_signal": "建立外部信号筛选，只学习能解决当前未解决问题的项目、issue、PR、benchmark 或线上反馈。",
    "dissection_learning": "把学习对象读到源码层：目录结构、入口、主循环、核心类、ADR/DESIGN 和模块边界。",
    "pattern_extraction": "把学到的内容提炼成可复用设计模式，而不是复制代码或追逐新技术名词。",
    "constraint_adaptation": "每个模式先过本地约束：资源预算、零重型依赖、已有架构、权限边界和维护成本。",
    "safe_landing": "先做独立最小实现，用 try/except、feature flag 或 fail-soft 边界保护主循环。",
    "verification_closure": "每轮进化必须留下测试、eval、smoke、验收或复盘证据，证明它真的变好。",
    "hands_on_validation": "学会新能力后必须实战跑通：真实端点、真实工具或端到端场景验证，而不是只读文档。",
    "learning_assetization": "满意后把经验资产化：沉淀方法论、可复用 skill/runbook、印象片段和证据指针。",
    "semantic_vfs": "把 skills、RAG、docs、GitHub、notes 挂到统一 semantic VFS 地址空间。",
    "daemon_lifecycle": "给常驻 agent 增加 active-work 检查、graceful drain、checkpoint/resume 和 post-restart health 验证。",
    "plugin_sandbox": "给可执行插件增加 sandbox、依赖 pin/allowlist、权限 scope 和用户/管理员信任边界。",
    "remote_tool_boundary": "给 MCP/OpenAPI 远程工具增加 server allowlist、auth、schema pinning、timeout 和高权限审批。",
    "middleware_observability": "给请求/响应 pipeline 增加顺序声明、raw/transformed 审计、失败策略和冲突测试。",
    "observability": "保留 traces/evals，让 agent 的进化可以被复盘和比较。",
    "evidence_logging": "给每次行动留下 before/after evidence：前置状态、动作、stdout/stderr/exit code、变更文件和验证结果。",
    "handoff_workbook": "把运行经验写成交接手册或工作手册：启动、重启、日志位置、状态文件、验收命令和常见坑。",
    "stateful_recovery": "把自动续接做成 Stateful Agent 契约：context replay + environment state + side-effect log + idempotent recovery。",
    "restart_session_recall": "把重启恢复升级成近期会话召回：冷启动后读最近几次会话，只作为背景恢复包注入，不当作新指令。",
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
    "Channel gateway lacks multi-worker responsiveness": 9,
    "Tool syscalls lack explicit capability table": 8,
    "High-agency tools lack layered permission policy": 5,
    "Memory system lacks lifecycle governance": 10,
    "Memory retention lacks active-rule GC policy": 9,
    "Memory FTS lacks CJK-safe retrieval path": 9,
    "Memory retrieval lacks multilingual regression tests": 5,
    "RAG pipeline lacks retrieval governance": 9,
    "RAG full-context mode lacks context budget": 6,
    "Agent lacks self-evolution capability": 12,
    "Evolution process lacks constraint adaptation": 7,
    "Evolution loop lacks verification closure": 10,
    "Learning loop lacks hands-on validation": 10,
    "Learning loop lacks reusable assetization": 9,
    "Knowledge surfaces lack semantic VFS": 7,
    "Daemon restart lacks active-work drain protocol": 9,
    "Self-restart can kill its own control plane": 25,
    "Restart recovery loses recent session memory": 17,
    "Permission policy is not enforced on all dispatch paths": 9,
    "Executable plugin system lacks sandbox policy": 4,
    "Plugin dependency installation lacks supply-chain policy": 8,
    "Remote tool server lacks trust-boundary policy": 9,
    "Remote tool schema is not pinned or versioned": 6,
    "High-agency remote tools lack approval boundary": 5,
    "LLM pipeline mutates messages without audit trail": 3,
    "LLM pipeline order is implicit": 1,
    "LLM pipeline lacks filter failure policy": 1,
    "Stateful Agent recovery contract incomplete": 8,
    "LLM CLI worker contract incomplete": 7,
    "Internal orchestration sprawl detected": 2,
    "Memory freshness / generation confusion detected": 6,
    "Role-play handoff orchestration detected": 2,
    "Large context window used as default token budget": 18,
    "Full-history prompt assembly lacks token budget": 14,
    "Token-efficient memory/skill reuse strategy missing": 16,
    "Runtime logs lack before/after evidence": 10,
    "Operational handoff/workbook habit missing": 8,
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


SEVERITY_PENALTIES = {"critical": 12, "high": 5, "medium": 2, "low": 0}
PENALTY_CAP = 70


def _finding_penalty_breakdown(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    breakdown: list[dict[str, Any]] = []
    for finding in findings:
        title = finding.get("title", "")
        severity = finding.get("severity", "low")
        title_penalty = FINDING_PENALTIES.get(title, 0)
        severity_penalty = SEVERITY_PENALTIES.get(severity, 0)
        total_penalty = title_penalty + severity_penalty
        if total_penalty <= 0:
            continue
        breakdown.append(
            {
                "title": title,
                "severity": severity,
                "source_layer": finding.get("source_layer", "unknown"),
                "title_penalty": title_penalty,
                "severity_penalty": severity_penalty,
                "total_penalty": total_penalty,
                "evidence_refs": list(finding.get("evidence_refs", []))[:3],
                "recommended_fix": finding.get("recommended_fix", ""),
            }
        )
    breakdown.sort(key=lambda item: (-item["total_penalty"], item["severity"], item["title"]))
    return breakdown


def _finding_penalty(findings: list[dict[str, Any]]) -> int:
    penalty = 0
    severity_penalty = {"critical": 12, "high": 5, "medium": 2, "low": 0}
    for finding in findings:
        title = finding.get("title", "")
        penalty += FINDING_PENALTIES.get(title, 0)
        penalty += severity_penalty.get(finding.get("severity", "low"), 0)
    return min(penalty, PENALTY_CAP)


def score_maturity(target: Path, findings: list[dict[str, Any]]) -> dict[str, Any]:
    """Return a comparable social maturity score for an agent project."""

    signal_refs = _collect_signal_refs(target)
    detected = {key: refs for key, refs in signal_refs.items() if refs}
    raw_points = sum(SIGNAL_POINTS[key] for key in detected)
    signal_points = [
        {
            "key": key,
            "label": SIGNAL_LABELS[key],
            "points": SIGNAL_POINTS[key],
            "evidence_refs": refs[:3],
        }
        for key, refs in detected.items()
    ]
    signal_points.sort(key=lambda item: (-item["points"], item["label"]))
    penalty_breakdown = _finding_penalty_breakdown(findings)
    uncapped_penalty = sum(item["total_penalty"] for item in penalty_breakdown)
    penalty = _finding_penalty(findings)
    base_score = max(0, min(100, raw_points))
    capped_raw_points = base_score
    has_methodology = "methodology" in detected
    methodology_cap_applied = False
    score_caps: list[dict[str, Any]] = []
    if has_methodology:
        base_score = max(base_score, 20)
    else:
        methodology_cap_applied = base_score > 34
        if methodology_cap_applied:
            score_caps.append(
                {
                    "gate": "methodology",
                    "before": capped_raw_points,
                    "after": 34,
                    "reason": "No explicit methodology layer was detected, so the pre-penalty score is capped at bronze-age ceiling.",
                }
            )
        base_score = min(base_score, 34)
    has_self_evolution = all(key in detected for key in EVOLUTION_SIGNAL_KEYS)
    self_evolution_cap_applied = False
    if not has_self_evolution:
        self_evolution_cap_applied = base_score > 65
        if self_evolution_cap_applied:
            score_caps.append(
                {
                    "gate": "self_evolution",
                    "before": base_score,
                    "after": 65,
                    "reason": "The complete self-evolution loop was not detected, so the pre-penalty score is capped at combustion-age ceiling.",
                }
            )
        base_score = min(base_score, 65)
    score = max(0, min(100, base_score - penalty))
    era = _era_for_score(score)

    strengths = [SIGNAL_LABELS[key] for key in SIGNAL_POINTS if key in detected]
    if has_self_evolution:
        strengths.append("self-evolution loop")
    missing_milestones = [
        MILESTONES[key]
        for key in (
            "methodology",
            "self_evolution_loop",
            "paging",
            "page_fault",
            "stateful_recovery",
            "restart_session_recall",
            "environment_state",
            "llm_cli_workers",
            "task_envelope",
            "impression_pointer",
            "memory_lifecycle",
            "memory_retrieval_i18n",
            "rag_governance",
            "token_efficiency",
            "fairness",
            "capability_table",
            "permission_policy",
            "daemon_lifecycle",
            "plugin_sandbox",
            "remote_tool_boundary",
            "middleware_observability",
            "semantic_vfs",
            "observability",
            "evidence_logging",
            "handoff_workbook",
            "external_signal",
            "dissection_learning",
            "pattern_extraction",
            "constraint_adaptation",
            "safe_landing",
            "verification_closure",
            "hands_on_validation",
            "learning_assetization",
        )
        if (key != "self_evolution_loop" and key not in detected)
        or (key == "self_evolution_loop" and not has_self_evolution)
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
        "capped_raw_points": capped_raw_points,
        "pre_penalty_score": base_score,
        "penalty": penalty,
        "uncapped_penalty": uncapped_penalty,
        "penalty_cap": PENALTY_CAP,
        "era_key": era.key,
        "era_name": era.name,
        "era_description": era.description,
        "share_line": f"这个 Agent 项目处于 {era.name}（{score}/100）：{era.description}",
        "score_formula": (
            f"min(100, raw_points={raw_points}) -> capped/gated pre_penalty={base_score}; "
            f"minus penalty=min({uncapped_penalty}, cap={PENALTY_CAP})={penalty}; final={score}"
        ),
        "signal_points": signal_points,
        "penalty_breakdown": penalty_breakdown,
        "score_caps": score_caps,
        "methodology_gate": {
            "detected": has_methodology,
            "cap_applied": methodology_cap_applied,
            "note": (
                "已发现方法论层，项目具备进入青铜以上时代的地基。"
                if has_methodology
                else "未发现清晰方法论层，时代评分封顶在青铜时代。"
            ),
        },
        "self_evolution_gate": {
            "detected": has_self_evolution,
            "cap_applied": self_evolution_cap_applied,
            "note": (
                "已发现完整自我进化闭环，项目具备持续吸收外部信号并验证改造的能力。"
                if has_self_evolution
                else "未发现完整自我进化闭环，时代评分封顶在内燃气时代。"
            ),
        },
        "strengths": strengths,
        "next_milestones": missing_milestones[:5],
        "evidence_refs": evidence_refs,
    }
