"""Scan for token-heavy agent context assembly and missing thrift controls."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from hermescheck.scanners.path_filters import iter_source_files, should_skip_path

SCAN_EXTENSIONS = {
    ".py",
    ".ts",
    ".js",
    ".mjs",
    ".cjs",
    ".tsx",
    ".jsx",
    ".md",
    ".txt",
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
    "temp",
}
MAX_FILE_BYTES = 300_000
GENERICAGENT_BASELINE_TOKENS = 30_000
VERY_LARGE_CONTEXT_TOKENS = 100_000

AGENT_RUNTIME_RE = re.compile(r"\b(?:agent|agent loop|orchestrator|subagent|tool_call|llm|chat|model)\b|智能体", re.I)
TOKEN_CONTEXT_RE = re.compile(
    r"\b(?:max[_ -]?context[_ -]?tokens|max[_ -]?(?:context|tokens)|context[_ -]?(?:window|length|tokens|limit)|"
    r"token[_ -]?(?:budget|limit)|input[_ -]?tokens)\b",
    re.I,
)
NUMBER_WITH_UNIT_RE = re.compile(r"(?<![\w.])([0-9][0-9_,.]*)\s*([kKmM万]?)(?:\s*(?:tokens?|context))?")
FULL_HISTORY_RE = re.compile(
    r"\b(?:full[_ -]?(?:history|context|transcript)|all[_ -]?(?:messages|history|memory|context)|"
    r"entire[_ -]?(?:history|conversation|repo|repository|workspace|context)|conversation[_ -]?history|"
    r"session[_ -]?history|chat[_ -]?history|transcript|load[_ -]?all|read[_ -]?all|include[_ -]?all)\b",
    re.I,
)
BULK_FILE_RE = re.compile(
    r"\b(?:rglob\s*\(\s*['\"]\*\*|\bglob\s*\(\s*['\"]\*\*/|walk\s*\(|os\.walk|read_text\s*\(|"
    r"readFileSync\s*\(|readFile\s*\(|load_all_files|read_repository|scan_workspace)\b",
    re.I,
)
PROMPT_ASSEMBLY_RE = re.compile(
    r"\b(?:prompt|messages|context|system[_ -]?prompt|chat|completion|llm|model|createChatCompletion|responses\.create)\b",
    re.I,
)
LOCAL_BUDGET_RE = re.compile(
    r"\b(?:token[_ -]?budget|max[_ -]?(?:tokens|chars|messages|context)|char(?:acter)?[_ -]?limit|"
    r"truncate|trim|prune|top[_ -]?k|retrieval[_ -]?budget|summary|summarize|compact|compression|"
    r"page[_ -]?table|paging|lru|cache|content[_ -]?hash|skill|sop|workflow|layered[_ -]?memory|"
    r"right knowledge|relevant knowledge|less noise)\b|(?:分层记忆|省\s*token|极致省\s*Token|技能|经验固化)",
    re.I,
)
GENERICAGENT_THRIFT_RE = re.compile(
    r"(?:<\s*30k|不到\s*30k|30k context|fraction of the 200k|200k.?1m|layered memory|"
    r"\bL[0-4]\b|crystalliz(?:e|es|ing)|skill tree|direct recall|right knowledge|less noise|"
    r"minimal toolset|9 atomic tools|~100[- ]line agent loop|token efficient|极致省\s*Token|分层记忆|"
    r"固化为\s*Skill|下次同类任务直接调用|关键信息始终在场)",
    re.I,
)


def _should_skip(path: Path) -> bool:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return True
    except OSError:
        return True
    return should_skip_path(path, SKIP_DIRS)


def _read_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except (OSError, PermissionError):
        return []


def _line_ref(path: Path, lineno: int) -> str:
    return f"{path}:{lineno}"


def _parse_token_number(raw: str, unit: str) -> int | None:
    normalized = raw.replace(",", "").replace("_", "")
    try:
        value = float(normalized)
    except ValueError:
        return None
    multiplier = 1
    if unit.lower() == "k":
        multiplier = 1_000
    elif unit.lower() == "m":
        multiplier = 1_000_000
    elif unit == "万":
        multiplier = 10_000
    return int(value * multiplier)


def _nearby_context(lines: list[str], lineno: int, *, radius: int = 4) -> str:
    return "\n".join(lines[max(0, lineno - radius - 1) : min(len(lines), lineno + radius)])


def _collect_refs(files: list[Path]) -> dict[str, list[str]]:
    refs = {
        "agent": [],
        "large_context": [],
        "full_history": [],
        "bulk_prompt": [],
        "thrift": [],
        "budget": [],
    }

    for fp in files:
        lines = _read_lines(fp)
        if not lines:
            continue
        path_text = "/".join(fp.parts)
        for lineno, line in enumerate(lines, start=1):
            ref = _line_ref(fp, lineno)
            text = f"{path_text}\n{line}"
            if AGENT_RUNTIME_RE.search(text):
                refs["agent"].append(ref)
            if GENERICAGENT_THRIFT_RE.search(line):
                refs["thrift"].append(ref)
            if LOCAL_BUDGET_RE.search(line):
                refs["budget"].append(ref)

            if TOKEN_CONTEXT_RE.search(line):
                for match in NUMBER_WITH_UNIT_RE.finditer(line):
                    token_count = _parse_token_number(match.group(1), match.group(2))
                    if token_count is not None and token_count > GENERICAGENT_BASELINE_TOKENS:
                        refs["large_context"].append(ref)
                        break

            context = _nearby_context(lines, lineno)
            if FULL_HISTORY_RE.search(line) and PROMPT_ASSEMBLY_RE.search(context):
                if not LOCAL_BUDGET_RE.search(context):
                    refs["full_history"].append(ref)
            if BULK_FILE_RE.search(line) and PROMPT_ASSEMBLY_RE.search(context):
                if not LOCAL_BUDGET_RE.search(context):
                    refs["bulk_prompt"].append(ref)

    return refs


def _max_context_tokens(files: list[Path]) -> int:
    max_tokens = 0
    for fp in files:
        for line in _read_lines(fp):
            if not TOKEN_CONTEXT_RE.search(line):
                continue
            for match in NUMBER_WITH_UNIT_RE.finditer(line):
                token_count = _parse_token_number(match.group(1), match.group(2))
                if token_count is not None:
                    max_tokens = max(max_tokens, token_count)
    return max_tokens


def _evidence(refs: dict[str, list[str]], *keys: str, limit: int = 10) -> list[str]:
    evidence: list[str] = []
    for key in keys:
        evidence.extend(refs[key][: max(1, limit // max(1, len(keys)))])
    return evidence[:limit]


def scan_token_usage(target: Path) -> List[Dict[str, Any]]:
    files = [
        fp
        for fp in iter_source_files(target)
        if fp.is_file() and fp.suffix.lower() in SCAN_EXTENSIONS and not _should_skip(fp)
    ]
    refs = _collect_refs(files)
    max_context_tokens = _max_context_tokens(files)
    thrift_signal_count = len(refs["thrift"]) + len(refs["budget"])
    findings: List[Dict[str, Any]] = []

    if refs["large_context"] and thrift_signal_count < 3:
        severity = "critical" if max_context_tokens >= VERY_LARGE_CONTEXT_TOKENS else "high"
        findings.append(
            {
                "severity": severity,
                "title": "Large context window used as default token budget",
                "symptom": (
                    f"Detected context/token limits above the {GENERICAGENT_BASELINE_TOKENS:,}-token thrift baseline "
                    f"(largest observed: {max_context_tokens:,}) without enough layered-memory or reuse controls."
                ),
                "user_impact": (
                    "Large context defaults can turn every turn into an expensive prompt, increase latency, and make "
                    "the agent depend on brute-force context stuffing instead of high-density recall."
                ),
                "source_layer": "token_usage",
                "mechanism": "Static scan for large context-window constants versus GenericAgent-style thrift controls.",
                "root_cause": (
                    "The project appears to treat model context capacity as the operating budget instead of keeping "
                    "a small hot context with layered memory, retrieval budgets, and reusable skills."
                ),
                "evidence_refs": _evidence(refs, "large_context", "budget", "thrift"),
                "confidence": 0.76,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Adopt a token-thrift budget similar to GenericAgent: keep hot context near or below 30K tokens, "
                    "use layered memory, top-k retrieval budgets, summary/page-table recall, and crystallize repeated "
                    "workflows into skills instead of replaying long history."
                ),
            }
        )

    prompt_bloat_refs = refs["full_history"] + refs["bulk_prompt"]
    if len(prompt_bloat_refs) >= 2 and thrift_signal_count < 3:
        findings.append(
            {
                "severity": "high",
                "title": "Full-history prompt assembly lacks token budget",
                "symptom": (
                    f"Found {len(prompt_bloat_refs)} full-history, load-all, or bulk-file prompt assembly sites without "
                    "nearby trim, top-k, summary, or token-budget controls."
                ),
                "user_impact": (
                    "Agents that keep replaying complete transcripts, memories, or workspaces burn tokens on stale "
                    "context and can bury the current task under irrelevant old state."
                ),
                "source_layer": "token_usage",
                "mechanism": "Line-proximity scan for all-history/all-files context assembly near LLM prompt construction.",
                "root_cause": "Prompt assembly is coupled to raw storage surfaces instead of a budgeted relevance layer.",
                "evidence_refs": _evidence(refs, "full_history", "bulk_prompt", "budget"),
                "confidence": 0.72,
                "fix_type": "code_change",
                "recommended_fix": (
                    "Put a token budget in the prompt builder: cap messages and characters, retrieve top-k relevant "
                    "memories/files, summarize cold history, and keep raw archives behind an explicit page-fault path."
                ),
            }
        )

    has_agent_surface = len(refs["agent"]) >= 3
    has_token_risk = bool(refs["large_context"] or prompt_bloat_refs)
    if has_agent_surface and has_token_risk and thrift_signal_count < 2:
        findings.append(
            {
                "severity": "high",
                "title": "Token-efficient memory/skill reuse strategy missing",
                "symptom": (
                    "Detected an agent/LLM runtime with token-heavy context signals, but too few markers for layered "
                    "memory, skill reuse, retrieval budgets, compaction, paging, or cache-based recall."
                ),
                "user_impact": (
                    "Without a thrift layer, the agent pays repeatedly for the same context and loses the GenericAgent "
                    "advantage: small hot context, direct recall, less noise, and lower hallucination pressure."
                ),
                "source_layer": "token_usage",
                "mechanism": "Repository-level comparison of agent runtime signals, token-heavy context signals, and thrift controls.",
                "root_cause": (
                    "The architecture does not visibly crystallize repeated work into reusable skills or route context "
                    "through layered memory before calling the model."
                ),
                "evidence_refs": _evidence(refs, "agent", "large_context", "full_history", "thrift", limit=12),
                "confidence": 0.68,
                "fix_type": "architecture_change",
                "recommended_fix": (
                    "Add an explicit token-efficiency layer: L0-L4 or equivalent memory tiers, reusable skill/SOP recall, "
                    "retrieval budgets, context compaction, and metrics that fail reviews when hot prompts exceed budget."
                ),
            }
        )

    return findings
