"""Scan for workflows that stop at local file/index completion without a reusable closure."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from hermescheck.scanners.path_filters import should_skip_path

SCAN_EXTENSIONS = {".py", ".ts", ".js", ".tsx", ".jsx", ".md", ".txt", ".yaml", ".yml", ".toml", ".json"}
SKIP_DIRS = {".git", ".github", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "coverage", "locales"}
SKIP_FILENAMES = {"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "poetry.lock", "uv.lock"}
MAX_FILE_BYTES = 250_000

SIGNAL_PATTERNS = {
    "file_create": re.compile(
        r"\b(?:create file|write file|save file|mkdir|touch|open\(.*[\"']w|write_text|writeFile)\b|(?:创建文件|写入文件|落地文件)",
        re.IGNORECASE,
    ),
    "index_update": re.compile(
        r"\b(?:update index|index update|registry|manifest|catalog|toc|table of contents)\b|(?:更新索引|索引更新|目录|清单|注册表)",
        re.IGNORECASE,
    ),
    "impression_card": re.compile(
        r"\b(?:impression card|memory card|summary card|cue card|concept card)\b|(?:印象卡片|记忆卡片|概念卡片)",
        re.IGNORECASE,
    ),
    "anchor_mapping": re.compile(
        r"\b(?:anchor mapping|semantic anchor|topic_anchor|anchor map|concept anchor)\b|(?:锚点映射|语义锚点|主题锚点)",
        re.IGNORECASE,
    ),
    "pointer_register": re.compile(
        r"\b(?:pointer register|register pointer|pointer_ref|pointer_type|vector_id|page table entry)\b|(?:指针注册|注册指针|页表项)",
        re.IGNORECASE,
    ),
    "acceptance": re.compile(
        r"\b(?:acceptance|acceptance criteria|done criteria|verify|validation|self[-_ ]?test|reusable|can find|next time)\b|(?:验收|验收标准|完成标准|验证|可复用|下次.*找到)",
        re.IGNORECASE,
    ),
    "premature_done": re.compile(
        r"\b(?:done|completed|task complete|finished|success)\b|(?:完成|已完成|任务完成|成功)", re.IGNORECASE
    ),
}

REQUIRED_CLOSURE = ("impression_card", "anchor_mapping", "pointer_register", "acceptance")


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
    files = [target] if target.is_file() else sorted(target.rglob("*"))
    for fp in files:
        if not fp.is_file() or _should_skip(fp) or fp.suffix not in SCAN_EXTENSIONS:
            continue

        path_text = "/".join(fp.parts)
        path_ref = f"{fp}:1"
        for key, pattern in SIGNAL_PATTERNS.items():
            if pattern.search(path_text):
                refs[key].append(path_ref)

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


def _evidence(refs: dict[str, list[str]]) -> list[str]:
    evidence_refs: list[str] = []
    seen: set[str] = set()
    for key in ("file_create", "index_update", "premature_done", *REQUIRED_CLOSURE):
        for ref in refs[key][:3]:
            if ref not in seen:
                evidence_refs.append(ref)
                seen.add(ref)
    return evidence_refs[:10]


def scan_completion_closure(target: Path) -> List[Dict[str, Any]]:
    refs = _collect_refs(target)
    has_local_progress = bool(refs["file_create"]) and bool(refs["index_update"])
    if not has_local_progress:
        return []

    missing = [key for key in REQUIRED_CLOSURE if not refs[key]]
    if not missing:
        return []

    severity = "high" if refs["premature_done"] and len(missing) >= 2 else "medium"
    missing_labels = {
        "impression_card": "impression card",
        "anchor_mapping": "anchor mapping",
        "pointer_register": "pointer registration",
        "acceptance": "acceptance criteria",
    }
    missing_summary = ", ".join(missing_labels[key] for key in missing)

    return [
        {
            "severity": severity,
            "title": "Completion closure gap detected",
            "symptom": (
                "Found file-creation and index-update signals, but the reusable memory closure is incomplete. "
                f"Missing: {missing_summary}."
            ),
            "user_impact": (
                "An agent can falsely conclude the task is done after creating files or updating an index, while the "
                "future retrieval path is still broken. Next time, the project may not be able to find, reuse, or "
                "verify the work."
            ),
            "source_layer": "completion_closure",
            "mechanism": "Repository scan for create/index workflows versus impression card, anchor, pointer, and acceptance signals.",
            "root_cause": (
                "The workflow appears point-complete rather than surface-complete: it checks whether something was "
                "written, not whether it can be found and reused later."
            ),
            "evidence_refs": _evidence(refs),
            "confidence": 0.7,
            "fix_type": "architecture_change",
            "recommended_fix": (
                "Define completion as a closure: file creation -> index update -> impression card -> anchor mapping "
                "-> pointer registration -> acceptance. The final check should ask whether the next agent can quickly "
                "find and reuse the result, not only whether a file exists."
            ),
        }
    ]
