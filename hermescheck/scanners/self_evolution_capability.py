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
}

EVOLUTION_KEYS = (
    "external_signal",
    "dissection_learning",
    "pattern_extraction",
    "constraint_adaptation",
    "safe_landing",
    "verification_closure",
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
                    f"Detected an agent runtime surface, but only {len(present)} of 6 evolution-loop stages "
                    f"were visible ({present_summary})."
                ),
                "user_impact": (
                    "The agent can execute tasks, but it has no durable way to learn from external projects, extract "
                    "patterns, adapt them to local constraints, land changes safely, and verify the result."
                ),
                "source_layer": "self_evolution",
                "mechanism": (
                    "Repository scan for the evolution rhythm: external signal -> source dissection -> pattern "
                    "extraction -> constraint adaptation -> small-step landing -> verification closure."
                ),
                "root_cause": "The project appears to treat improvement as ad hoc development rather than a closed-loop capability.",
                "evidence_refs": _evidence(refs, "agent_runtime", *EVOLUTION_KEYS),
                "confidence": 0.71,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Add a lightweight self-evolution loop: define signal screening, source-level learning, pattern "
                    "extraction, local constraint adaptation, independent minimal modules, try/except or fail-soft "
                    "integration, and a test/eval/retro closure for every learning cycle."
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

    return findings
