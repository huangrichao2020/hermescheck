"""Run hermescheck as a module with `python -m hermescheck`."""

from __future__ import annotations

import sys

from hermescheck.cli import main


if __name__ == "__main__":
    sys.exit(main())
