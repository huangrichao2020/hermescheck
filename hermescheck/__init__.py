"""hermescheck — Audit Hermes Agent architecture and runtime health.

The base model rarely fails. The wrapper architecture corrupts good answers into bad behavior.

Usage:
    from hermescheck import run_audit, generate_report

    results = run_audit("/path/to/your/agent/project")
    print(generate_report(results))
"""

__version__ = "1.2.4"

from hermescheck.audit import run_audit, save_results
from hermescheck.contribute import prepare_contribution_bundle, publish_bundle_to_upstream
from hermescheck.report import generate_report
from hermescheck.sarif import generate_sarif, save_sarif

__all__ = [
    "run_audit",
    "generate_report",
    "generate_sarif",
    "prepare_contribution_bundle",
    "publish_bundle_to_upstream",
    "save_results",
    "save_sarif",
]
