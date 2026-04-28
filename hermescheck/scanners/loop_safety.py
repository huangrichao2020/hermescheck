"""Deprecated loop-safety scanner.

Loop-detector checks were removed from the default standard. Large agent
codebases often contain loop, retry, scheduler, and tool-call vocabulary even
when the actual runtime behavior is healthy. Treat stuck-loop handling as an
operational reflection and incident-response practice, not a static regex
finding.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List


def scan_loop_safety(target: Path) -> List[Dict[str, Any]]:
    """Return no findings; kept only for import compatibility."""

    return []
