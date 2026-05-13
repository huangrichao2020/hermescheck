"""Scan for the architecture separations described by how-to-agent."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from hermescheck.scanners.path_filters import iter_source_files, should_skip_path

SCAN_EXTENSIONS = {".py", ".ts", ".js", ".tsx", ".jsx", ".md", ".txt", ".yaml", ".yml", ".toml", ".json"}
SKIP_DIRS = {".git", ".github", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "coverage"}
SKIP_FILENAMES = {"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "poetry.lock", "uv.lock"}
MAX_FILE_BYTES = 250_000

SIGNAL_PATTERNS = {
    "agent_runtime": re.compile(
        r"\b(?:agent|agent[_ -]?loop|orchestrator|planner|tool[_ -]?router|tool[_ -]?call|"
        r"function[_ -]?call|memory|skill|gateway|feishu|lark|slack|weixin|scheduler|subagent|llm)\b|"
        r"(?:智能体|工具调用|记忆|技能|飞书|微信)",
        re.IGNORECASE,
    ),
    "long_task_channel": re.compile(
        r"\b(?:feishu|lark|slack|discord|telegram|weixin|chat|rich[-_ ]?text|message[_ -]?update|"
        r"stream(?:ing)?|chunk|progress|status|long[-_ ]?running|append[-_ ]?only|event[_ -]?trail)\b|"
        r"(?:飞书|富文本|消息更新|长任务|进度流|状态流|事件流)",
        re.IGNORECASE,
    ),
    "stream_separation": re.compile(
        r"\b(?:progress[_ -]?stream|status[_ -]?stream|conclusion[_ -]?stream|final[_ -]?stream|"
        r"separate[_ -]?(?:stream|message|output)|append[-_ ]?only[_ -]?(?:event|trail)|"
        r"raw[_ -]?output.*rendered[_ -]?output|rendered[_ -]?output.*raw[_ -]?output)\b|"
        r"(?:进度流|状态流|结论流|分离输出|分开.{0,12}(?:消息|流)|原始输出|渲染输出)",
        re.IGNORECASE,
    ),
    "knowledge_surface": re.compile(
        r"\b(?:memory|memories|skill|skills|session[_ -]?history|archive|reflection|fact|facts|"
        r"procedure|runbook|knowledge|cold[_ -]?archive|current[_ -]?facts?)\b|"
        r"(?:记忆|技能|会话历史|归档|冷归档|事实|流程|知识)",
        re.IGNORECASE,
    ),
    "authority_boundary": re.compile(
        r"\b(?:authoritative|source[_ -]?of[_ -]?truth|current[_ -]?facts?|active[_ -]?memory|"
        r"cold[_ -]?archive|searchable[_ -]?archive|not[_ -]?default[_ -]?memory|"
        r"session[_ -]?history.*not.*instruction|provenance|freshness|retirement)\b|"
        r"(?:权威来源|当前事实|活跃记忆|冷归档|可搜索归档|默认记忆|新鲜度|退役规则)",
        re.IGNORECASE,
    ),
    "self_evolution": re.compile(
        r"\b(?:self[-_ ]?evolution|self[-_ ]?improv|self[-_ ]?modif|skill[_ -]?(?:evolve|evolution)|"
        r"reflection|post[_ -]?turn|auto[-_ ]?apply|ratchet)\b|(?:自我进化|自改|技能进化|棘轮|反思)",
        re.IGNORECASE,
    ),
    "evolution_governance": re.compile(
        r"\b(?:proposal|evidence|risk[_ -]?(?:level|classification)|validation[_ -]?plan|rollback[_ -]?plan|"
        r"apply[_ -]?gate|human[_ -]?gate|consent[_ -]?gate|high[_ -]?risk|post[-_ ]?change[_ -]?audit)\b|"
        r"(?:提案|证据|风险等级|验证计划|回滚计划|应用门禁|人类门禁|高风险|变更后审计)",
        re.IGNORECASE,
    ),
    "sidecar_surface": re.compile(
        r"\b(?:sidecar|telemetry|audit|watcher|monitor|subagent|external[_ -]?cli|worker|plugin|"
        r"fallback|background[_ -]?task|daemon|service)\b|(?:旁路|遥测|审计|子代理|外部 CLI|守护进程)",
        re.IGNORECASE,
    ),
    "core_sidecar_boundary": re.compile(
        r"\b(?:primary[_ -]?(?:runtime|path)|core[_ -]?path|single[_ -]?(?:runtime|intent[_ -]?owner)|"
        r"bounded|fail[-_ ]?soft|non[-_ ]?blocking|optional[_ -]?helper|one[_ -]?primary[_ -]?runtime)\b|"
        r"(?:主运行路径|核心路径|单一意图所有者|有边界|失败不阻塞|非阻塞|可选助手)",
        re.IGNORECASE,
    ),
    "dependency_surface": re.compile(
        r"\b(?:dependabot|dependency[_ -]?(?:alert|audit|security|hygiene)|vulnerabilit(?:y|ies)|"
        r"npm[_ -]?audit|runtime[_ -]?dependencies|lockfile|patched[_ -]?version|scanner[_ -]?lag)\b|"
        r"(?:依赖告警|依赖治理|漏洞告警|运行时依赖|锁文件|扫描延迟)",
        re.IGNORECASE,
    ),
    "dependency_hygiene": re.compile(
        r"\b(?:runtime[_ -]?dependenc(?:y|ies).*first|bridge.*next|docs?.*last|website.*last|"
        r"blast[_ -]?radius|closest[_ -]?available[_ -]?test|scanner[_ -]?lag|patched[_ -]?version)\b|"
        r"(?:运行时依赖.{0,24}先|bridge.{0,24}再|docs?.{0,24}最后|website.{0,24}最后|影响面|扫描延迟)",
        re.IGNORECASE,
    ),
    "completion_surface": re.compile(
        r"\b(?:done|complete|completion|verify|validation|test|log|status|commit|push|live[_ -]?service|"
        r"working[_ -]?tree|handoff|evidence)\b|(?:完成|验证|测试|日志|状态|提交|推送|工作区|交接|证据)",
        re.IGNORECASE,
    ),
    "completion_evidence": re.compile(
        r"\b(?:tests? passed|focused[_ -]?checks?|live[_ -]?service.*(?:healthy|running)|"
        r"systemd.*active|gateway[_ -]?state.*running|origin/.+\.\.\..+=?\s*0\s+0|"
        r"working[_ -]?tree.*clean|unrelated[_ -]?dirty|evidence[_ -]?closure|next[_ -]?agent.*find)\b|"
        r"(?:测试通过|服务健康|正在运行|工作区干净|无关改动|证据闭环|下一个 agent.{0,12}找到)",
        re.IGNORECASE,
    ),
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


def _collect_refs(target: Path) -> dict[str, list[str]]:
    refs = {key: [] for key in SIGNAL_PATTERNS}
    for fp in iter_source_files(target, skip_dirs=SKIP_DIRS):
        if not fp.is_file() or _should_skip(fp) or fp.suffix.lower() not in SCAN_EXTENSIONS:
            continue
        try:
            lines = fp.read_text(encoding="utf-8", errors="ignore").splitlines()
        except (OSError, PermissionError):
            continue
        for lineno, line in enumerate(lines, start=1):
            ref = f"{fp}:{lineno}"
            for key, pattern in SIGNAL_PATTERNS.items():
                if pattern.search(line):
                    refs[key].append(ref)
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


def _has_agent_surface(refs: dict[str, list[str]]) -> bool:
    return (
        len(refs["agent_runtime"]) >= 3
        or bool(refs["long_task_channel"])
        or bool(refs["self_evolution"])
        or len(refs["knowledge_surface"]) >= 3
        or (bool(refs["sidecar_surface"]) and bool(refs["agent_runtime"]))
    )


def scan_architecture_separation(target: Path) -> List[Dict[str, Any]]:
    """Return findings for missing how-to-agent architecture separations."""

    refs = _collect_refs(target)
    if not _has_agent_surface(refs):
        return []

    findings: List[Dict[str, Any]] = []

    if refs["long_task_channel"] and not refs["stream_separation"]:
        findings.append(
            {
                "severity": "medium",
                "title": "Long-running channel output lacks stream separation",
                "symptom": (
                    "Detected long-running chat or platform-output signals without a visible separation between "
                    "progress/status output and final conclusion output."
                ),
                "user_impact": (
                    "Adapters that keep editing one platform message can hit message-update limits, lose progress "
                    "evidence, or make final answers hard to recover after long tool runs."
                ),
                "source_layer": "architecture_separation",
                "mechanism": "Scan for long-running channel/rendering signals versus progress/conclusion/event-trail separation.",
                "root_cause": "The interaction layer appears to own too much runtime state instead of rendering bounded streams.",
                "evidence_refs": _evidence(refs, "long_task_channel", "stream_separation"),
                "confidence": 0.68,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Split channel output into a progress stream and a conclusion stream. For very long tasks, add an "
                    "append-only event trail or artifact so platform edit limits do not become runtime state loss."
                ),
            }
        )

    if len(refs["knowledge_surface"]) >= 3 and not refs["authority_boundary"]:
        findings.append(
            {
                "severity": "medium",
                "title": "Knowledge authority boundary is unclear",
                "symptom": (
                    "Detected memory, skill, session, or archive surfaces without a clear current-facts versus "
                    "history/archive authority boundary."
                ),
                "user_impact": (
                    "A target agent may treat stale session history, old skill proposals, and active instructions as "
                    "equally current, causing obsolete behavior to re-enter daily context."
                ),
                "source_layer": "architecture_separation",
                "mechanism": "Scan for knowledge surfaces versus source-of-truth, active-memory, and cold-archive signals.",
                "root_cause": "The knowledge plane does not visibly separate active authority from searchable history.",
                "evidence_refs": _evidence(refs, "knowledge_surface", "authority_boundary"),
                "confidence": 0.69,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Define which files or stores are current facts, which are procedures/skills, which are searchable "
                    "session history, and which are cold archives loaded only on demand."
                ),
            }
        )

    if refs["self_evolution"] and not refs["evolution_governance"]:
        findings.append(
            {
                "severity": "medium",
                "title": "Self-evolution lacks proposal and rollback governance",
                "symptom": (
                    "Detected self-evolution or reflection signals without proposal, evidence, risk, validation, "
                    "rollback, or apply-gate language."
                ),
                "user_impact": (
                    "Self-improvement can become silent self-modification: useful lessons may land without proof, "
                    "risk classification, or a way to reverse the change."
                ),
                "source_layer": "architecture_separation",
                "mechanism": "Scan for self-evolution signals versus proposal/evidence/risk/validation/rollback controls.",
                "root_cause": "The evolution loop is not visibly separated from ordinary task execution.",
                "evidence_refs": _evidence(refs, "self_evolution", "evolution_governance"),
                "confidence": 0.7,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Put self-evolution behind a ratchet: observation -> proposal -> evidence -> risk classification "
                    "-> validation plan -> rollback plan -> apply gate -> post-change audit."
                ),
            }
        )

    if refs["sidecar_surface"] and not refs["core_sidecar_boundary"]:
        findings.append(
            {
                "severity": "medium",
                "title": "Runtime sidecars lack primary-path boundary",
                "symptom": (
                    "Detected sidecars, workers, telemetry, or background helpers without clear primary runtime path, "
                    "bounded behavior, or fail-soft semantics."
                ),
                "user_impact": (
                    "Sidecars can quietly become a second runtime, bypassing the main planner, permission boundary, "
                    "or failure policy."
                ),
                "source_layer": "architecture_separation",
                "mechanism": "Scan for sidecar/helper signals versus primary-path, bounded, and fail-soft language.",
                "root_cause": "The runtime mechanism stack does not visibly distinguish core execution from optional helpers.",
                "evidence_refs": _evidence(refs, "sidecar_surface", "core_sidecar_boundary"),
                "confidence": 0.66,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Name the primary runtime path and make sidecars bounded, optional, and fail-soft. Sidecars should "
                    "report evidence, not silently own planning, permissions, or user-visible conclusions."
                ),
            }
        )

    if refs["dependency_surface"] and not refs["dependency_hygiene"]:
        findings.append(
            {
                "severity": "low",
                "title": "Dependency work lacks runtime-risk triage",
                "symptom": (
                    "Detected dependency-alert or vulnerability signals without a visible policy for ordering fixes "
                    "by runtime blast radius and scanner-lag verification."
                ),
                "user_impact": (
                    "Dependency remediation can turn into a broad upgrade sweep that mixes runtime packages, optional "
                    "bridges, docs tooling, and scanner lag into one risky change."
                ),
                "source_layer": "architecture_separation",
                "mechanism": "Scan for dependency-alert signals versus runtime-first and closest-test remediation policy.",
                "root_cause": "Dependency hygiene is not visibly separated from feature work or docs-build maintenance.",
                "evidence_refs": _evidence(refs, "dependency_surface", "dependency_hygiene"),
                "confidence": 0.6,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Document dependency remediation order: runtime dependencies first, optional bridges next, docs or "
                    "website tooling last; verify each group with the closest test and distinguish GitHub scanner lag "
                    "from unfixed lockfiles."
                ),
            }
        )

    if refs["completion_surface"] and not refs["completion_evidence"]:
        findings.append(
            {
                "severity": "low",
                "title": "Completion claims lack live evidence closure",
                "symptom": (
                    "Detected completion or verification language without concrete evidence that tests, live service "
                    "state, git state, or handoff/findability were checked."
                ),
                "user_impact": (
                    "The agent may report completion after editing files while the live service, remote branch, user "
                    "channel, or next-agent retrieval path is still unproven."
                ),
                "source_layer": "architecture_separation",
                "mechanism": "Scan for completion language versus tests, logs, live status, git, and next-agent evidence.",
                "root_cause": "The workflow does not visibly separate code completion from confidence-producing evidence.",
                "evidence_refs": _evidence(refs, "completion_surface", "completion_evidence"),
                "confidence": 0.58,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Define closure as evidence: focused checks, live status or logs when runtime changed, clean git "
                    "state, pushed commits when requested, and a pointer that lets the next agent find the method."
                ),
            }
        )

    return findings
