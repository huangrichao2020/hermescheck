"""Shared path filters for scanner inputs."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Iterator, Optional, Set

# Default directories to skip during file collection.
DEFAULT_SKIP_DIRS: Set[str] = {
    ".git",
    ".github",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    "coverage",
    "temp",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".cache",
    ".omx",
    ".tox",
    ".eggs",
}

# Pre-computed lowercase skip dirs for fast O(1) lookup during os.walk.
_DEFAULT_SKIP_DIRS_LOWER: Set[str] = {s.lower() for s in DEFAULT_SKIP_DIRS}

# Default file extensions to include (source files only).
DEFAULT_EXTENSIONS: Set[str] = {
    ".py",
    ".ts",
    ".js",
    ".tsx",
    ".jsx",
    ".md",
    ".toml",
    ".yaml",
    ".yml",
    ".json",
    ".sh",
    ".bash",
    ".cfg",
    ".ini",
    ".txt",
}


def iter_source_files(
    target: Path,
    *,
    skip_dirs: Optional[Set[str]] = None,
    extensions: Optional[Set[str]] = None,
    max_files: int = 0,
) -> Iterator[Path]:
    """Efficiently walk a directory tree, yielding only relevant source files.

    Instead of ``target.rglob("*")`` which traverses every file and directory,
    this function prunes skip-dirs early (during os.walk) and only yields files
    with matching extensions. This is typically 5–10x faster on large projects.

    Args:
        target: Root directory to scan (or a single file path).
        skip_dirs: Directory names to prune. Defaults to DEFAULT_SKIP_DIRS.
        extensions: File extensions to include. Defaults to DEFAULT_EXTENSIONS.
            Empty set means include all files.
        max_files: Stop after yielding this many files (0 = unlimited).

    Yields:
        Path objects for each matching file.
    """
    if target.is_file():
        yield target
        return

    # Pre-compute lowercase skip set once, not per-directory.
    if skip_dirs is not None:
        skip_lower = _DEFAULT_SKIP_DIRS_LOWER | {s.lower() for s in skip_dirs}
    else:
        skip_lower = _DEFAULT_SKIP_DIRS_LOWER

    exts = extensions or DEFAULT_EXTENSIONS

    count = 0
    for dirpath, dirnames, filenames in os.walk(target):
        # Prune skipped directories in-place to prevent os.walk from descending.
        dirnames[:] = [d for d in dirnames if d.lower() not in skip_lower and not d.endswith(".egg-info")]

        for fname in filenames:
            if exts and not fname.lower().endswith(tuple(ext.lower() for ext in exts)):
                continue

            fp = Path(dirpath) / fname
            if looks_generated_asset(fp):
                continue

            yield fp
            count += 1
            if max_files and count >= max_files:
                return


GENERATED_ASSET_DIR_HINTS = {
    "assets",
    "_assets",
    "static",
    "generated",
    "vendor",
}

HASHED_BUNDLE_RE = re.compile(
    r"^(?:chunk|blockdiagram|vendor|runtime|mermaid|graph|worker|index|app|main)"
    r"-[a-z0-9_-]{6,}(?:-[a-z0-9_-]{4,})*(?: \d+)?\.(?:js|cjs|mjs)$",
    re.IGNORECASE,
)
GENERIC_HASHED_ASSET_RE = re.compile(
    r"^[a-z0-9_.-]+-[a-z0-9_-]{8,}(?: \d+)?\.(?:js|cjs|mjs|css|map)$",
    re.IGNORECASE,
)
MINIFIED_JS_RE = re.compile(r".*\.min\.(?:js|cjs|mjs)$", re.IGNORECASE)


def should_skip_path(path: Path, skip_dirs: set[str]) -> bool:
    """Return True when a path should be ignored by behavior-focused scanners."""

    lowered_parts = {part.lower() for part in path.parts}
    all_skip_dirs = _DEFAULT_SKIP_DIRS_LOWER | {skip_dir.lower() for skip_dir in skip_dirs}
    if any(skip_dir in lowered_parts for skip_dir in all_skip_dirs):
        return True
    return looks_generated_asset(path)


def looks_generated_asset(path: Path) -> bool:
    """Detect generated or minified front-end asset bundles."""

    lowered_parts = {part.lower() for part in path.parts}
    name = path.name

    if MINIFIED_JS_RE.match(name):
        return True

    if not any(part in GENERATED_ASSET_DIR_HINTS for part in lowered_parts):
        return False

    return bool(HASHED_BUNDLE_RE.match(name) or GENERIC_HASHED_ASSET_RE.match(name))
