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
