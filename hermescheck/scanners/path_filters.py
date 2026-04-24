"""Shared path filters for scanner inputs."""

from __future__ import annotations

import re
from pathlib import Path

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
    if any(skip_dir.lower() in lowered_parts for skip_dir in skip_dirs):
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
