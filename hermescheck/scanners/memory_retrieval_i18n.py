"""Scan for memory retrieval stacks that rely on FTS without multilingual safeguards."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from hermescheck.scanners.path_filters import iter_source_files, should_skip_path

SCAN_EXTENSIONS = {".py", ".ts", ".js", ".tsx", ".jsx", ".md", ".yaml", ".yml", ".toml", ".json", ".sql"}
SKIP_DIRS = {".git", ".github", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "coverage"}
MAX_FILE_BYTES = 250_000

FTS_RE = re.compile(
    r"\b(?:fts5|full[-_ ]?text search|MATCH|unicode61|sqlite[_ -]?fts|[A-Za-z0-9_]+_fts)\b",
    re.IGNORECASE,
)
UNICODE61_RE = re.compile(r"\bunicode61\b", re.IGNORECASE)
MULTILINGUAL_RE = re.compile(
    r"\b(?:cjk|chinese|japanese|korean|multilingual|i18n|unicode|locale|non[-_ ]?english)\b|"
    r"(?:中文|汉字|漢字|日文|韩文|韓文|多语言|多語言)",
    re.IGNORECASE,
)
SAFE_RETRIEVAL_RE = re.compile(
    r"\b(?:ngram|bi[-_ ]?gram|tri[-_ ]?gram|jieba|janome|mecab|kuromoji|sentencepiece|"
    r"custom[_ -]?tokenizer|tokenize_for_fts|fts_match_query|like[_ -]?fallback|fallback[_ -]?like|"
    r"embedding[_ -]?fallback|semantic[_ -]?fallback|vector[_ -]?fallback|reindex|rebuild[_ -]?index)\b",
    re.IGNORECASE,
)
MULTILINGUAL_TEST_RE = re.compile(
    r"(?:中文回复|后端|用户偏好|多语言|cjk|unicode61|ngram|trigram|fts.*中文|中文.*fts|"
    r"japanese|korean|non[-_ ]?english)",
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
    refs = {key: [] for key in ("fts", "unicode61", "multilingual", "safe", "tests")}
    files = list(iter_source_files(target))
    for fp in files:
        if not fp.is_file() or _should_skip(fp) or fp.suffix not in SCAN_EXTENSIONS:
            continue
        try:
            lines = fp.read_text(encoding="utf-8", errors="ignore").splitlines()
        except (OSError, PermissionError):
            continue
        is_test_file = "test" in fp.name.lower() or "tests" in {part.lower() for part in fp.parts}
        for lineno, line in enumerate(lines, start=1):
            ref = f"{fp}:{lineno}"
            if FTS_RE.search(line):
                refs["fts"].append(ref)
            if UNICODE61_RE.search(line):
                refs["unicode61"].append(ref)
            if MULTILINGUAL_RE.search(line):
                refs["multilingual"].append(ref)
            if SAFE_RETRIEVAL_RE.search(line):
                refs["safe"].append(ref)
            if is_test_file and MULTILINGUAL_TEST_RE.search(line):
                refs["tests"].append(ref)
    return refs


def _evidence(refs: dict[str, list[str]], *keys: str, limit: int = 9) -> list[str]:
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


def scan_memory_retrieval_i18n(target: Path) -> List[Dict[str, Any]]:
    refs = _collect_refs(target)
    if not refs["fts"]:
        return []

    findings: List[Dict[str, Any]] = []
    has_multilingual_exposure = bool(refs["unicode61"] or refs["multilingual"])
    if has_multilingual_exposure and not refs["safe"]:
        findings.append(
            {
                "severity": "high",
                "title": "Memory FTS lacks CJK-safe retrieval path",
                "symptom": (
                    "Detected SQLite/full-text memory retrieval with unicode or multilingual signals, but no visible "
                    "CJK-safe tokenizer, ngram index, LIKE fallback, embedding fallback, or reindex path."
                ),
                "user_impact": (
                    "A memory system can appear to store Chinese or other non-space-delimited language memories while "
                    "failing to retrieve them by natural query, making long-term memory unreliable in real chats."
                ),
                "source_layer": "memory_retrieval_i18n",
                "mechanism": "Repository scan for FTS5/unicode61 usage versus multilingual tokenization and fallback retrieval safeguards.",
                "root_cause": "The retrieval layer appears to depend on a tokenizer that may not segment CJK text into searchable terms.",
                "evidence_refs": _evidence(refs, "fts", "unicode61", "multilingual", "safe"),
                "confidence": 0.74,
                "fix_type": "code_change",
                "recommended_fix": (
                    "Add a multilingual retrieval path: CJK ngram tokenization or a language-aware tokenizer, safe FTS "
                    "MATCH query construction, LIKE or semantic fallback, index rebuild/migration, and regression tests "
                    "for Chinese short phrases and punctuation."
                ),
            }
        )

    if has_multilingual_exposure and refs["safe"] and not refs["tests"]:
        findings.append(
            {
                "severity": "medium",
                "title": "Memory retrieval lacks multilingual regression tests",
                "symptom": (
                    "The memory retrieval stack has multilingual or CJK handling signals, but no visible tests for "
                    "non-English retrieval behavior."
                ),
                "user_impact": (
                    "Tokenizer and fallback changes can silently regress, causing stored memories to disappear for "
                    "Chinese, Japanese, Korean, or mixed-language queries."
                ),
                "source_layer": "memory_retrieval_i18n",
                "mechanism": "Repository scan for multilingual retrieval safeguards versus test fixtures or assertions.",
                "root_cause": "The project appears to rely on implementation patterns without locking them down in regression tests.",
                "evidence_refs": _evidence(refs, "fts", "safe", "multilingual"),
                "confidence": 0.68,
                "fix_type": "test_change",
                "recommended_fix": (
                    "Add retrieval tests for short CJK phrases, mixed English/CJK queries, punctuation-heavy queries, "
                    "and old-record reindex behavior."
                ),
            }
        )

    return findings
