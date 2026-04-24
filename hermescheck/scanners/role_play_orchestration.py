"""Scan for company-org role play and serial handoff orchestration."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from hermescheck.scanners.path_filters import should_skip_path

SCAN_EXTENSIONS = {".py", ".ts", ".js", ".tsx", ".jsx", ".md", ".yaml", ".yml", ".toml"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "coverage"}

ROLE_PATTERNS = {
    "manager": re.compile(
        r"\b(?:manager|supervisor|coordinator|pm|product manager|project manager)\b|(?:总管|主管|经理|产品经理|项目经理)",
        re.IGNORECASE,
    ),
    "planner": re.compile(r"\b(?:planner|architect|designer|strategist)\b|(?:规划师|架构师|设计师)", re.IGNORECASE),
    "builder": re.compile(
        r"\b(?:coder|developer|engineer|executor|worker|implementer)\b|(?:开发者|工程师|执行者)", re.IGNORECASE
    ),
    "reviewer": re.compile(
        r"\b(?:reviewer|critic|qa|tester|verifier|auditor)\b|(?:审核|评审|测试|质检|验证者)", re.IGNORECASE
    ),
    "researcher": re.compile(r"\b(?:researcher|analyst|investigator)\b|(?:研究员|分析师|调研员)", re.IGNORECASE),
}

AGENT_ROLE_RE = re.compile(
    r"(?:\b\w+\s+agent\b|\bagent\s+(?:role|team|crew|department)\b|(?:智能体|代理)\s*(?:角色|团队|部门))",
    re.IGNORECASE,
)
AGENT_CONTEXT_RE = re.compile(
    r"(?:agent|subagent|multi[_ -]?agent|swarm|crew|tool\s+role|handoff|pipeline|chain|智能体|代理|多智能体|交接|接棒|流水线)",
    re.IGNORECASE,
)
HANDOFF_RE = re.compile(
    r"(?:handoff|hand[-_ ]?off|pass(?:es|ed)?\s+to|relay|pipeline|chain|next\s+agent|transfer\s+to|"
    r"接棒|交接|移交|传给|下一个\s*(?:agent|智能体|代理)|流水线|串行|部门)",
    re.IGNORECASE,
)
TOOL_AS_AGENT_RE = re.compile(
    r"(?:tool|script|command|function|workflow|工具|脚本|命令|函数|流程).{0,32}(?:agent|智能体|代理)",
    re.IGNORECASE,
)


def _should_skip(path: Path) -> bool:
    return should_skip_path(path, SKIP_DIRS)


def scan_role_play_orchestration(target: Path) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    role_refs: dict[str, list[str]] = {key: [] for key in ROLE_PATTERNS}
    handoff_refs: list[str] = []
    agent_role_refs: list[str] = []
    tool_as_agent_refs: list[str] = []

    files = [target] if target.is_file() else sorted(target.rglob("*"))
    for fp in files:
        if not fp.is_file() or _should_skip(fp) or fp.suffix not in SCAN_EXTENSIONS:
            continue

        try:
            lines = fp.read_text(encoding="utf-8", errors="ignore").splitlines()
        except (OSError, PermissionError):
            continue

        for lineno, line in enumerate(lines, start=1):
            ref = f"{fp}:{lineno}"
            has_agent_context = bool(AGENT_CONTEXT_RE.search(line))
            if has_agent_context:
                for role, pattern in ROLE_PATTERNS.items():
                    if pattern.search(line):
                        role_refs[role].append(ref)
            if AGENT_ROLE_RE.search(line):
                agent_role_refs.append(ref)
            if HANDOFF_RE.search(line):
                handoff_refs.append(ref)
            if TOOL_AS_AGENT_RE.search(line):
                tool_as_agent_refs.append(ref)

    present_roles = {role: refs for role, refs in role_refs.items() if refs}
    role_count = len(present_roles)
    role_refs_total = sum(len(refs) for refs in present_roles.values())
    handoff_count = len(handoff_refs)

    if role_count < 3 or handoff_count < 2:
        return findings

    severity = "high" if role_count >= 4 and handoff_count >= 3 else "medium"
    role_summary = ", ".join(sorted(present_roles))
    evidence_refs: list[str] = []
    for refs in present_roles.values():
        evidence_refs.extend(refs[:1])
    evidence_refs.extend(handoff_refs[:3])
    evidence_refs.extend(agent_role_refs[:2])
    evidence_refs.extend(tool_as_agent_refs[:2])

    findings.append(
        {
            "severity": severity,
            "title": "Role-play handoff orchestration detected",
            "symptom": (
                f"Found {role_refs_total} role markers across {role_count} role categories ({role_summary}) "
                f"and {handoff_count} serial handoff markers."
            ),
            "user_impact": (
                "Agent systems that mirror company departments often look organized while losing context at each "
                "handoff. The result is local progress with global confusion: plans, reviews, and execution drift apart."
            ),
            "source_layer": "orchestration",
            "mechanism": "Repository-wide scan for role-labeled agents combined with handoff/pipeline language.",
            "root_cause": (
                "The design appears to model agent collaboration as a serial org chart instead of one intent owner "
                "forking independent exploration and merging evidence."
            ),
            "evidence_refs": evidence_refs[:10],
            "confidence": 0.68,
            "fix_type": "architecture_change",
            "recommended_fix": (
                "Keep one agent or loop responsible for the full user intent. Use subagents for independent evidence "
                "gathering or context isolation, then merge results back to the intent owner. Convert stable, bounded "
                "steps into tools instead of giving every tool a role identity."
            ),
        }
    )
    return findings
