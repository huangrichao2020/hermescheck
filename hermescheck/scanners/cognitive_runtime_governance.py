"""Scan cognitive runtime layers for boundaries, budgets, and reflection governance."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from hermescheck.scanners.path_filters import iter_source_files, should_skip_path

SCAN_EXTENSIONS = {".py", ".ts", ".js", ".tsx", ".jsx", ".md", ".yaml", ".yml", ".toml", ".json"}
SKIP_DIRS = {".git", ".github", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "coverage"}
MAX_FILE_BYTES = 250_000

COGNITIVE_RE = re.compile(
    r"\b(?:cognitive[_ -]?(?:layer|depth|routing|decision)|classify[_ -]?cognitive|"
    r"input[_ -]?layer|visible[_ -]?output[_ -]?layer|processing[_ -]?mode|"
    r"runtime[_ -]?rule|L[0-5]\b)\b|(?:认知|深度路由|层级处理)",
    re.IGNORECASE,
)
BOUNDARY_RE = re.compile(
    r"\b(?:boundary|visible[_ -]?output|do not dump|do not expand|stop[_ -]?level|"
    r"ephemeral|current API call|current turn|memory/context layers|"
    r"deterministic|conservative|separate concerns)\b|(?:边界|可见输出|当前轮次|保守)",
    re.IGNORECASE,
)
REFLECTION_RE = re.compile(
    r"\b(?:post[_ -]?turn[_ -]?reflection|reflection[_ -]?episode|dream[_ -]?cycle|"
    r"pain[_ -]?score|next[_ -]?action|lesson|episode|AGENT_LEARNINGS|"
    r"reflect(?:ion|ed)?)\b|(?:回合后反思|复盘|梦境循环|经验沉淀)",
    re.IGNORECASE,
)
REFLECTION_GOVERNANCE_RE = re.compile(
    r"\b(?:schema[_ -]?version|confidence|importance|compact|truncate|limit|bounded|"
    r"not promote|does not promote|admission|lock|flock|dedupe|source|session[_ -]?id)\b|"
    r"(?:入库|压缩|截断|置信度|不直接提升|加锁|去重)",
    re.IGNORECASE,
)
MECHANISM_STACK_RE = re.compile(
    r"\b(?:LoopDetector|ReviewMechanism|InternalizationMechanism|ResilienceMechanism|"
    r"ContextSandbox|runtime[_ -]?mechanisms?|loop[_ -]?detector|review[_ -]?mechanism|"
    r"internalization|resilience|context[_ -]?sandbox)\b|"
    r"(?:运行时机制|防死循环|因果归因|成功模式内化|韧性执行|上下文沙盒)",
    re.IGNORECASE,
)
BUDGET_RE = re.compile(
    r"\b(?:MAX_[A-Z0-9_]+|max[_ -]?(?:calls|history|steps|turns|tokens|bytes|size)|"
    r"threshold|budget|timeout|ttl|window|bounded|deque|maxlen|limit|cap)\b|"
    r"(?:预算|阈值|上限|窗口|有界)",
    re.IGNORECASE,
)
FAIL_SOFT_RE = re.compile(
    r"\b(?:fail[_ -]?(?:soft|open)|best[_ -]?effort|try\s*:|except|catch|"
    r"non[_ -]?intrusive|observe[_ -]?only|observational|sidecar|does not block|"
    r"do not block|failure.*(?:skip|ignored)|silent(?:ly)? skip)\b|"
    r"(?:旁路观察|失败不影响|不拦截|静默跳过)",
    re.IGNORECASE,
)
GOVERNANCE_LADDER_RE = re.compile(
    r"\b(?:cognitive[_ -]?governance|durable[_ -]?cognition|cognitive[_ -]?store|"
    r"trace|episode|candidate[_ -]?claim|verified[_ -]?fact|transferable[_ -]?knowledge|"
    r"procedure|identity|nourishment|L5[_ -]?(?:human|behavior|diary)|DIKWP|"
    r"write[_ -]?once.*route[_ -]?many|attention[_ -]?gate|context[_ -]?assembly|"
    r"feedback[_ -]?capture|durable[_ -]?cognition[_ -]?update)\b|"
    r"(?:认知治理|持久认知|入库门禁|注意力门禁|候选声明|已验证事实|滋养|人类真实行为)",
    re.IGNORECASE,
)
PURPOSE_RE = re.compile(
    r"\b(?:purpose|purpose[_ -]?detection|goal|success[_ -]?criterion|feedback[_ -]?standard|"
    r"why[_ -]?act|what[_ -]?counts[_ -]?as[_ -]?success)\b|(?:目的|目标|成功标准|反馈标准)",
    re.IGNORECASE,
)
ADMISSION_STORE_RE = re.compile(
    r"\b(?:admission[_ -]?(?:gate|store|control)|pending[_ -]?(?:admission|candidate)|"
    r"promote|promotion|explicit[_ -]?(?:confirmation|consent)|provenance|freshness|"
    r"retirement[_ -]?rule|current[_ -]?fact|user[_ -]?approved|confidence)\b|"
    r"(?:入库|待确认|显式确认|提升|证据来源|新鲜度|退役规则|当前事实|用户批准)",
    re.IGNORECASE,
)
CRON_REPORT_RE = re.compile(
    r"\b(?:cron|scheduled[_ -]?(?:task|job|report)|daily[_ -]?brief|morning[_ -]?report|"
    r"nightly[_ -]?(?:dream|review)|dream[_ -]?(?:admission|cycle)|channel[_ -]?report)\b|"
    r"(?:定时任务|定时报表|日报|晨报|夜间梦境|梦境入库)",
    re.IGNORECASE,
)
CRON_MEMORY_RE = re.compile(
    r"\b(?:hot[_ -]?(?:channel[_ -]?)?memory|same[_ -]?day[_ -]?(?:memory|context)|"
    r"source\s*=\s*[\"']cron|source['\"]?\s*:\s*[\"']cron|target[_ -]?day|"
    r"admitted[_ -]?items|skipped[_ -]?reasons|pending[_ -]?cognition)\b|"
    r"(?:热记忆|当天记忆|同日上下文|跳过原因|待入库认知)",
    re.IGNORECASE,
)
DIARY_L5_RE = re.compile(
    r"\b(?:L5|diary|voice[_ -]?(?:input|dictation)|lived[_ -]?day|real[_ -]?behavior|"
    r"body[_ -]?state|energy|emotion(?:al)?[_ -]?arc|what[_ -]?happened[_ -]?today|"
    r"raw[_ -]?diary)\b|(?:日记|语音输入|真实行为|身体状态|能量|情绪)",
    re.IGNORECASE,
)
DIARY_BOUNDARY_RE = re.compile(
    r"\b(?:raw[_ -]?(?:diary|text).*local|local[_ -]?(?:only|private)|private[_ -]?by[_ -]?default|"
    r"admitted[_ -]?summar(?:y|ies)|approved[_ -]?summar(?:y|ies)|not.*permanent[_ -]?identity|"
    r"must[_ -]?not.*identity|evidence[_ -]?only|one[_ -]?day[_ -]?mood)\b|"
    r"(?:原始日记.*本地|默认私有|批准摘要|不得成为永久身份|一天情绪)",
    re.IGNORECASE,
)
DEVICE_OS_RE = re.compile(
    r"\b(?:device|mac|laptop|battery|sleep|wake|offline|online|network|launchd|launchctl|systemd|"
    r"gateway restart|process restart|reconnect)\b|(?:设备|断网|联网|睡眠|唤醒|电池|重启|重连)",
    re.IGNORECASE,
)
RUST_SUBSTRATE_RE = re.compile(
    r"\b(?:rust|rust bridge|ipc|protocol contract|substrate|ffi|sqlite helper)\b|(?:底层\s*Rust|Rust\s*底座)",
    re.IGNORECASE,
)
PYTHON_RUNTIME_RE = re.compile(
    r"\b(?:python runtime|python execution|tool dispatch|prompt assembly|scheduler|runtime prompt|context assembler)\b|"
    r"(?:Python\s*执行层|工具调度|提示组装|上下文组装)",
    re.IGNORECASE,
)
STORE_SURFACE_RE = re.compile(
    r"\b(?:sqlite|jsonl|file store|memory store|vector store|hot memory|archive|admitted cognition|pending cognition)\b|"
    r"(?:存储层|热记忆|归档|正式认知|待准入)",
    re.IGNORECASE,
)
BRAIN_WIKI_RE = re.compile(
    r"\b(?:brain|wiki|knowledge page|architecture manual|gbrain|second brain)\b|(?:脑|知识库|架构手册)",
    re.IGNORECASE,
)
FEISHU_SURFACE_RE = re.compile(
    r"\b(?:feishu|lark|group chat|bot reaction|message reaction|chat scope)\b|(?:飞书|群聊|表情反应)",
    re.IGNORECASE,
)
FEISHU_CLI_RE = re.compile(
    r"\b(?:feishu cli|lark-cli|document token|doc token|workspace identity|as bot|as user)\b|"
    r"(?:飞书\s*CLI|文档\s*token|机器人身份|用户身份)",
    re.IGNORECASE,
)
WHOLE_SYSTEM_CONTRACT_RE = re.compile(
    r"\b(?:whole[-_ ]system|cross[-_ ]layer|impact matrix|impact review|source of truth|authority contract|"
    r"infrastructure layer|affected layers|background[-_ ]loop behavior|user[-_ ]visible behavior|"
    r"restart/offline|offline failure|restart failure|failure mode)\b|"
    r"(?:整体架构|全局架构|跨层|影响矩阵|事实源|权威来源|基础设施层|用户可见行为|后台循环|离线失败|重启失败)",
    re.IGNORECASE,
)


def _should_skip(path: Path) -> bool:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return True
    except OSError:
        return True
    return should_skip_path(path, SKIP_DIRS)


def _collect_refs(target: Path) -> dict[str, list[str]]:
    refs = {
        key: []
        for key in (
            "cognitive",
            "boundary",
            "reflection",
            "reflection_governance",
            "mechanism_stack",
            "budget",
            "fail_soft",
            "governance_ladder",
            "purpose",
            "admission_store",
            "cron_report",
            "cron_memory",
            "diary_l5",
            "diary_boundary",
            "device_os",
            "rust_substrate",
            "python_runtime",
            "store_surface",
            "brain_wiki",
            "feishu_surface",
            "feishu_cli",
            "whole_system_contract",
        )
    }
    for fp in iter_source_files(target):
        if not fp.is_file() or _should_skip(fp) or fp.suffix not in SCAN_EXTENSIONS:
            continue
        try:
            lines = fp.read_text(encoding="utf-8", errors="ignore").splitlines()
        except (OSError, PermissionError):
            continue
        for lineno, line in enumerate(lines, start=1):
            ref = f"{fp}:{lineno}"
            if COGNITIVE_RE.search(line):
                refs["cognitive"].append(ref)
            if BOUNDARY_RE.search(line):
                refs["boundary"].append(ref)
            if REFLECTION_RE.search(line):
                refs["reflection"].append(ref)
            if REFLECTION_GOVERNANCE_RE.search(line):
                refs["reflection_governance"].append(ref)
            if MECHANISM_STACK_RE.search(line):
                refs["mechanism_stack"].append(ref)
            if BUDGET_RE.search(line):
                refs["budget"].append(ref)
            if FAIL_SOFT_RE.search(line):
                refs["fail_soft"].append(ref)
            if GOVERNANCE_LADDER_RE.search(line):
                refs["governance_ladder"].append(ref)
            if PURPOSE_RE.search(line):
                refs["purpose"].append(ref)
            if ADMISSION_STORE_RE.search(line):
                refs["admission_store"].append(ref)
            if CRON_REPORT_RE.search(line):
                refs["cron_report"].append(ref)
            if CRON_MEMORY_RE.search(line):
                refs["cron_memory"].append(ref)
            if DIARY_L5_RE.search(line):
                refs["diary_l5"].append(ref)
            if DIARY_BOUNDARY_RE.search(line):
                refs["diary_boundary"].append(ref)
            if DEVICE_OS_RE.search(line):
                refs["device_os"].append(ref)
            if RUST_SUBSTRATE_RE.search(line):
                refs["rust_substrate"].append(ref)
            if PYTHON_RUNTIME_RE.search(line):
                refs["python_runtime"].append(ref)
            if STORE_SURFACE_RE.search(line):
                refs["store_surface"].append(ref)
            if BRAIN_WIKI_RE.search(line):
                refs["brain_wiki"].append(ref)
            if FEISHU_SURFACE_RE.search(line):
                refs["feishu_surface"].append(ref)
            if FEISHU_CLI_RE.search(line):
                refs["feishu_cli"].append(ref)
            if WHOLE_SYSTEM_CONTRACT_RE.search(line):
                refs["whole_system_contract"].append(ref)
    return refs


def _evidence(refs: dict[str, list[str]], *keys: str, limit: int = 10) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for key in keys:
        for ref in refs.get(key, []):
            if ref not in seen:
                out.append(ref)
                seen.add(ref)
            if len(out) >= limit:
                return out
    return out


def scan_cognitive_runtime_governance(target: Path) -> List[Dict[str, Any]]:
    refs = _collect_refs(target)
    findings: List[Dict[str, Any]] = []
    infra_keys = (
        "device_os",
        "rust_substrate",
        "python_runtime",
        "store_surface",
        "brain_wiki",
        "feishu_surface",
        "feishu_cli",
        "cron_report",
    )
    infra_hits = [key for key in infra_keys if refs[key]]

    if refs["cognitive"] and not refs["boundary"]:
        findings.append(
            {
                "severity": "medium",
                "title": "Cognitive routing lacks visible-output boundary",
                "symptom": (
                    "Detected cognitive depth or layer routing, but no visible boundary between internal processing "
                    "depth and what the agent is allowed to surface to the user."
                ),
                "user_impact": (
                    "A depth router can make answers feel over-explained, under-explained, or unexpectedly abstract if "
                    "it does not define where visible output should stop for each turn."
                ),
                "source_layer": "cognitive_runtime",
                "mechanism": (
                    "Repository scan for cognitive-layer routing signals versus visible-output layer, runtime rule, "
                    "ephemeral context, or explicit boundary language."
                ),
                "root_cause": (
                    "The runtime appears to classify thought depth before declaring the separation between internal "
                    "reasoning depth, memory loading, and user-visible answer shape."
                ),
                "evidence_refs": _evidence(refs, "cognitive", "boundary"),
                "confidence": 0.63,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Make the depth router return both processing depth and visible output boundary. Keep the block "
                    "ephemeral to the current turn and state that memory/context loading remains a separate concern."
                ),
            }
        )

    if refs["reflection"] and not refs["reflection_governance"]:
        findings.append(
            {
                "severity": "high",
                "title": "Post-turn reflection lacks memory admission governance",
                "symptom": (
                    "Detected post-turn reflection or episode capture without schema, confidence, compaction, "
                    "locking, source, or admission-control signals."
                ),
                "user_impact": (
                    "Automatic reflection can flood long-term memory with low-confidence stories, duplicate lessons, "
                    "or raw user content that later gets mistaken for durable truth."
                ),
                "source_layer": "cognitive_runtime",
                "mechanism": (
                    "Repository scan for reflection/episode writing versus bounded fields, schema version, confidence, "
                    "compaction, locking, and explicit promotion policy."
                ),
                "root_cause": (
                    "The learning loop appears to persist turn reflections before defining how they are compacted, "
                    "scored, locked, and later promoted or ignored."
                ),
                "evidence_refs": _evidence(refs, "reflection", "reflection_governance"),
                "confidence": 0.68,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Record post-turn reflection as structured episode data with schema_version, source, session id, "
                    "confidence, importance/pain score, compact previews, and file/DB locking. Do not promote it "
                    "directly into semantic memory; let a later review or dream cycle decide."
                ),
            }
        )

    if refs["governance_ladder"] and (not refs["purpose"] or not refs["admission_store"]):
        missing = []
        if not refs["purpose"]:
            missing.append("Purpose detection")
        if not refs["admission_store"]:
            missing.append("admission gate")
        findings.append(
            {
                "severity": "medium",
                "title": "Cognitive governance lacks Purpose/admission boundary",
                "symptom": (
                    f"Detected cognitive-governance ladder concepts, but missing {' and '.join(missing)} signals."
                ),
                "user_impact": (
                    "Raw traces, episodes, claims, facts, skills, and identity rules can collapse into one memory pile, "
                    "so stale or low-authority material may steer future behavior."
                ),
                "source_layer": "cognitive_runtime",
                "mechanism": (
                    "Repository scan for trace/episode/claim/fact/knowledge/procedure/identity/L5/DIKWP signals "
                    "versus Purpose and admission-store controls."
                ),
                "root_cause": (
                    "The runtime names cognition layers before declaring the goal that selects relevant information "
                    "and the gate that promotes candidates into durable authority."
                ),
                "evidence_refs": _evidence(refs, "governance_ladder", "purpose", "admission_store"),
                "confidence": 0.64,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Route every durable cognition update through Purpose detection, attention gating, candidate "
                    "classification, and an admission store. Promote only explicit, sourced, fresh, useful candidates "
                    "into facts, knowledge, procedures, identity, nourishment, or L5 summaries."
                ),
            }
        )

    if (refs["governance_ladder"] or refs["cognitive"]) and len(infra_hits) >= 4 and not refs["whole_system_contract"]:
        findings.append(
            {
                "severity": "medium",
                "title": "Cognitive architecture lacks whole-system impact matrix",
                "symptom": (
                    "Detected cognitive architecture plus multiple infrastructure surfaces "
                    f"({', '.join(infra_hits[:6])}), but no whole-system impact matrix, source-of-truth contract, "
                    "or restart/offline failure-mode review."
                ),
                "user_impact": (
                    "A local cognition fix may look correct in one tool or prompt while breaking continuity across "
                    "Feishu, CLI document evidence, sqlite/wiki authority, Rust/Python boundaries, cron, dream, "
                    "or device reconnect behavior."
                ),
                "source_layer": "cognitive_runtime",
                "mechanism": (
                    "Repository scan for cognitive-governance signals plus device/Rust/Python/store/brain/wiki/"
                    "Feishu/CLI/cron surfaces versus whole-system impact, source-of-truth, and restart/offline "
                    "review language."
                ),
                "root_cause": (
                    "The architecture treats cognition as a local memory/runtime feature before naming the "
                    "cross-layer system that actually carries user context and agent continuity."
                ),
                "evidence_refs": _evidence(refs, "governance_ladder", "cognitive", *infra_keys, limit=12),
                "confidence": 0.66,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Add a whole-system cognitive impact matrix covering input, execution, storage, retrieval, "
                    "cognition, evolution, and operations layers. For non-trivial changes, require affected layers, "
                    "source-of-truth movement, user-visible behavior, background-loop behavior, and restart/offline "
                    "failure modes before implementation."
                ),
            }
        )

    if refs["cron_report"] and not refs["cron_memory"]:
        findings.append(
            {
                "severity": "medium",
                "title": "Scheduled cognition reports bypass hot memory admission",
                "symptom": (
                    "Detected cron, scheduled report, or dream-cycle signals without same-day hot memory, target-day, "
                    "pending cognition, admitted items, or skipped-reason signals."
                ),
                "user_impact": (
                    "A scheduled report may be delivered and then immediately forgotten, or a nightly dream pass may "
                    "silently mutate durable memory without a visible admission trail."
                ),
                "source_layer": "cognitive_runtime",
                "mechanism": (
                    "Repository scan for scheduled cognition/reporting concepts versus hot-channel memory and "
                    "dream-admission bookkeeping."
                ),
                "root_cause": (
                    "Scheduled cognition appears to be treated as output rather than as same-day evidence that must "
                    "be routed through the same admission store as interactive turns."
                ),
                "evidence_refs": _evidence(refs, "cron_report", "cron_memory"),
                "confidence": 0.62,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Write cron reports into same-day hot channel memory with source='cron', task/report metadata, "
                    "and target_day. Let dream review list admitted items and skipped reasons instead of silently "
                    "updating durable cognition."
                ),
            }
        )

    if refs["diary_l5"] and not refs["diary_boundary"]:
        findings.append(
            {
                "severity": "medium",
                "title": "L5 diary input lacks privacy and identity boundary",
                "symptom": (
                    "Detected diary, voice-input, L5, or real-behavior signals without local/private raw-text, admitted "
                    "summary, or non-identity-boundary language."
                ),
                "user_impact": (
                    "Private lived-day material can be exported, over-generalized, or turned into permanent user "
                    "identity from one emotional day."
                ),
                "source_layer": "cognitive_runtime",
                "mechanism": (
                    "Repository scan for L5 diary/real-behavior concepts versus privacy, summary admission, and "
                    "identity-retirement boundaries."
                ),
                "root_cause": (
                    "The runtime recognizes diary-like input but does not visibly distinguish raw private evidence "
                    "from user-approved summaries or durable identity."
                ),
                "evidence_refs": _evidence(refs, "diary_l5", "diary_boundary"),
                "confidence": 0.63,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Keep raw diary text local and private by default. Promote only user-approved summaries, and "
                    "explicitly prevent one-day moods, failures, or impulses from becoming permanent identity."
                ),
            }
        )

    if refs["mechanism_stack"] and (not refs["budget"] or not refs["fail_soft"]):
        missing = []
        if not refs["budget"]:
            missing.append("bounded budgets")
        if not refs["fail_soft"]:
            missing.append("fail-soft integration")
        findings.append(
            {
                "severity": "medium",
                "title": "Runtime mechanism stack lacks sidecar safety policy",
                "symptom": (
                    "Detected loop/review/internalization/resilience/context-sandbox style runtime mechanisms, "
                    f"but missing {', '.join(missing)}."
                ),
                "user_impact": (
                    "A mechanism stack that is meant to observe and improve the agent can itself become the source of "
                    "latency, memory growth, or blocked tool execution if it is not bounded and fail-soft."
                ),
                "source_layer": "cognitive_runtime",
                "mechanism": (
                    "Repository scan for runtime mechanism stacks versus max/threshold/budget controls and sidecar "
                    "failure handling."
                ),
                "root_cause": (
                    "The runtime appears to add reflective control mechanisms before establishing their resource "
                    "limits and whether their failure can affect the main user task."
                ),
                "evidence_refs": _evidence(refs, "mechanism_stack", "budget", "fail_soft"),
                "confidence": 0.61,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Keep runtime mechanisms as bounded sidecars: max calls/history/window limits, output compression "
                    "caps, timeouts, and try/except fail-soft integration that can warn but not block the main tool path."
                ),
            }
        )

    return findings
