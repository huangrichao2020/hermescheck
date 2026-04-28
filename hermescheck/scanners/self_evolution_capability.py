"""Scan agent projects for a closed-loop self-evolution capability."""

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
        r"\b(?:agent|agent[_ -]?loop|orchestrator|subagent|tool[_ -]?call|function[_ -]?call|memory|"
        r"scheduler|rag|mcp|plugin|skill|llm)\b|(?:智能体|工具调用|记忆|技能)",
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
}

EVOLUTION_KEYS = (
    "external_signal",
    "dissection_learning",
    "pattern_extraction",
    "constraint_adaptation",
    "safe_landing",
    "verification_closure",
    "hands_on_validation",
    "learning_assetization",
)


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
    files = list(iter_source_files(target))
    for fp in files:
        if not fp.is_file() or _should_skip(fp) or fp.suffix not in SCAN_EXTENSIONS:
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


def scan_self_evolution_capability(target: Path) -> List[Dict[str, Any]]:
    refs = _collect_refs(target)
    has_agent_surface = len(refs["agent_runtime"]) >= 4 or any(refs[key] for key in EVOLUTION_KEYS)
    if not has_agent_surface:
        return []

    present = [key for key in EVOLUTION_KEYS if refs[key]]
    findings: List[Dict[str, Any]] = []

    if len(present) < 3:
        present_summary = ", ".join(present) if present else "none"
        findings.append(
            {
                "severity": "high",
                "title": "Agent lacks self-evolution capability",
                "symptom": (
                    f"Detected an agent runtime surface, but only {len(present)} of {len(EVOLUTION_KEYS)} evolution-loop stages "
                    f"were visible ({present_summary})."
                ),
                "user_impact": (
                    "The agent can execute tasks, but it has no durable way to learn from external projects, extract "
                    "patterns, adapt them to local constraints, land changes safely, verify the result in practice, "
                    "and turn the lesson into reusable methodology, skills, and impression fragments."
                ),
                "source_layer": "self_evolution",
                "mechanism": (
                    "Repository scan for the evolution rhythm: external signal -> source dissection -> pattern "
                    "extraction -> constraint adaptation -> small-step landing -> verification closure -> "
                    "hands-on validation -> reusable assetization."
                ),
                "root_cause": "The project appears to treat improvement as ad hoc development rather than a closed-loop capability.",
                "evidence_refs": _evidence(refs, "agent_runtime", *EVOLUTION_KEYS),
                "confidence": 0.71,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Add a lightweight self-evolution loop: define signal screening, source-level learning, pattern "
                    "extraction, local constraint adaptation, independent minimal modules, try/except or fail-soft "
                    "integration, test/eval/retro closure, a real hands-on validation run, and durable methodology, "
                    "skill, and impression assets for every learning cycle."
                ),
            }
        )
        return findings

    if (refs["external_signal"] or refs["dissection_learning"] or refs["pattern_extraction"]) and (
        not refs["constraint_adaptation"] or not refs["safe_landing"]
    ):
        findings.append(
            {
                "severity": "medium",
                "title": "Evolution process lacks constraint adaptation",
                "symptom": (
                    "Detected project-learning or pattern-extraction signals without both local constraint adaptation "
                    "and small-step landing controls."
                ),
                "user_impact": (
                    "Learning from strong projects can turn into copy-paste architecture drift if the agent does not "
                    "force each idea through local constraints, resource budgets, and minimal safe implementation."
                ),
                "source_layer": "self_evolution",
                "mechanism": "Repository scan for learning signals versus local-constraint and safe-landing signals.",
                "root_cause": "The learning workflow appears to capture ideas before proving they fit this runtime.",
                "evidence_refs": _evidence(
                    refs,
                    "external_signal",
                    "dissection_learning",
                    "pattern_extraction",
                    "constraint_adaptation",
                    "safe_landing",
                ),
                "confidence": 0.68,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Before integrating learned designs, require a fit check: problem solved, local constraints, no "
                    "heavy dependency by default, independent module first, bounded integration point, and rollback path."
                ),
            }
        )

    if present and not refs["verification_closure"]:
        findings.append(
            {
                "severity": "high",
                "title": "Evolution loop lacks verification closure",
                "symptom": "Detected self-improvement or learning workflow signals without test/eval/acceptance closure.",
                "user_impact": (
                    "The agent may keep changing itself based on plausible lessons, but without a verification loop it "
                    "cannot distinguish real improvement from accumulated complexity."
                ),
                "source_layer": "self_evolution",
                "mechanism": "Repository scan for learning and adaptation signals versus tests, evals, smoke checks, or retros.",
                "root_cause": "The evolution loop stops at implementation instead of closing with evidence.",
                "evidence_refs": _evidence(refs, *EVOLUTION_KEYS),
                "confidence": 0.7,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Make every evolution cycle end with a verification artifact: focused regression test, smoke test, "
                    "eval, acceptance note, or retro that records what changed and what failed."
                ),
            }
        )

    if present and not refs["hands_on_validation"]:
        findings.append(
            {
                "severity": "high",
                "title": "Learning loop lacks hands-on validation",
                "symptom": "Detected self-improvement or learning workflow signals without a real practice run.",
                "user_impact": (
                    "The agent may claim it learned a capability after reading docs or source, but without an actual "
                    "live run it can preserve an untested story instead of an operational skill."
                ),
                "source_layer": "self_evolution",
                "mechanism": "Repository scan for learning-loop signals versus hands-on, live endpoint, e2e, or real-tool validation language.",
                "root_cause": "The learning workflow appears to stop at conceptual understanding or tests, not practical capability proof.",
                "evidence_refs": _evidence(refs, *EVOLUTION_KEYS),
                "confidence": 0.7,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Require every new capability to pass one realistic hands-on run before it is considered learned. "
                    "Record the command, endpoint/tool used, result, failure mode, and acceptance note."
                ),
            }
        )

    if present and not refs["learning_assetization"]:
        findings.append(
            {
                "severity": "high",
                "title": "Learning loop lacks reusable assetization",
                "symptom": "Detected self-improvement or learning workflow signals without methodology, skill, or impression asset closure.",
                "user_impact": (
                    "A successful one-off learning run can disappear after the session. The next agent may repeat the "
                    "same exploration instead of directly recalling the verified procedure."
                ),
                "source_layer": "self_evolution",
                "mechanism": (
                    "Repository scan for learning-loop signals versus durable methodology artifacts, skill packages, "
                    "runbooks, impression fragments, or memory imprints."
                ),
                "root_cause": "The learning workflow does not promote verified experience into reusable long-term assets.",
                "evidence_refs": _evidence(refs, *EVOLUTION_KEYS),
                "confidence": 0.72,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "After the hands-on run is accepted, produce three assets: a compact methodology, a reusable skill "
                    "or runbook, and a short impression fragment with pointers back to the evidence."
                ),
            }
        )

    return findings
