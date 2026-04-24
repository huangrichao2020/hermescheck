"""Prepare and upstream self-scan contribution bundles."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from hermescheck.audit import run_audit
from hermescheck.config import AuditConfig

BUNDLE_VERSION = "hermescheck.contribution.v1"
DEFAULT_UPSTREAM_REPO = "huangrichao2020/hermescheck"
DEFAULT_BUNDLE_ROOT = Path(".hermescheck") / "contributions"
CONTRIBUTION_LAYERS = ("Doctrine", "Contract", "Scanner", "Contribution Flow", "Governance")


class CommandError(RuntimeError):
    """Raised when an external command exits unsuccessfully."""

    def __init__(self, *, args: list[str], returncode: int, stdout: str, stderr: str) -> None:
        super().__init__(f"Command failed ({returncode}): {' '.join(args)}")
        self.args_list = args
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def slugify(value: str) -> str:
    """Return a filesystem- and branch-safe slug."""

    lowered = value.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug or "contribution"


def ensure_gh_available() -> None:
    """Fail early when GitHub CLI is unavailable."""

    if shutil.which("gh"):
        return
    raise RuntimeError("GitHub CLI `gh` is required for `hermescheck contribute pr`.")


def _run_command(args: list[str], cwd: str | None = None) -> str:
    """Run an external command and return trimmed stdout."""

    completed = subprocess.run(
        args,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise CommandError(
            args=args,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
    return completed.stdout.strip()


def _load_audit_results(source: str, *, profile: str, quiet: bool) -> dict[str, Any]:
    source_path = Path(source)
    if source_path.is_file() and source_path.suffix == ".json":
        return json.loads(source_path.read_text(encoding="utf-8"))
    if source_path.is_dir():
        config = AuditConfig.from_profile(profile)
        return run_audit(str(source_path), config=config, verbose=not quiet)
    raise FileNotFoundError("Expected an audit JSON file or a target directory for `hermescheck contribute prepare`.")


def _build_slug(results: dict[str, Any]) -> str:
    target_name = Path(results["scope"]["target_name"]).name or "agent"
    primary_mode = results["executive_verdict"]["primary_failure_mode"]
    date_prefix = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{date_prefix}-{slugify(target_name)}-{slugify(primary_mode)[:40]}".strip("-")


def _summarize_findings(results: dict[str, Any], *, limit: int = 5) -> list[dict[str, Any]]:
    summary = []
    for finding in results.get("findings", [])[:limit]:
        summary.append(
            {
                "title": finding["title"],
                "severity": finding["severity"],
                "symptom": finding["symptom"],
                "recommended_fix": finding["recommended_fix"],
            }
        )
    return summary


def _build_bundle(results: dict[str, Any], *, source: str) -> dict[str, Any]:
    slug = _build_slug(results)
    target_name = results["scope"]["target_name"]
    primary_mode = results["executive_verdict"]["primary_failure_mode"]
    maturity = results.get("maturity_score", {})
    upstream_path = f"contributions/self-scan/{slug}"
    short_target = Path(target_name).name or "agent-project"

    return {
        "bundle_version": BUNDLE_VERSION,
        "created_at": datetime.now().isoformat(),
        "mode": "self-scan",
        "source": {
            "input": str(source),
            "target_name": target_name,
            "profile": results["scan_metadata"]["profile"],
            "overall_health": results["executive_verdict"]["overall_health"],
            "architecture_era": maturity.get("era_name", "Unknown"),
            "architecture_score": maturity.get("score", 0),
        },
        "suggested": {
            "slug": slug,
            "title": f"[self-scan] {short_target}: {primary_mode}",
            "branch": f"self-scan/{slug}",
            "upstream_repo": DEFAULT_UPSTREAM_REPO,
            "upstream_path": upstream_path,
            "commit_message": f"docs: add self-scan contribution for {short_target}",
        },
        "contribution": {
            "layers": ["Scanner"],
            "mission_alignment": (
                "This self-scan contribution turns a real-world agent architecture finding "
                "into reusable open source doctrine, scanner signal, or governance guidance."
            ),
            "why_generalizes": (
                "The findings in this bundle should be reviewed for patterns that may affect "
                "other agent projects with similar orchestration, provider, or safety structure."
            ),
            "evidence_summary": (
                f"Primary failure mode: {primary_mode}. Overall health: "
                f"{results['executive_verdict']['overall_health']}. Architecture era: "
                f"{maturity.get('era_name', 'Unknown')} ({maturity.get('score', 'N/A')}/100)."
            ),
            "validation": (
                "The source project was scanned with hermescheck and the resulting structured report "
                "was converted into this contribution bundle."
            ),
            "owner_consent": False,
            "public_safe": False,
        },
        "audit_snapshot": {
            "primary_failure_mode": primary_mode,
            "most_urgent_fix": results["executive_verdict"]["most_urgent_fix"],
            "maturity_score": maturity,
            "severity_summary": results["severity_summary"],
            "top_findings": _summarize_findings(results),
        },
    }


def render_bundle_summary(bundle: dict[str, Any]) -> str:
    """Render a human-readable summary for the bundle."""

    lines = [
        f"# Self-Scan Contribution Bundle: {bundle['suggested']['slug']}",
        "",
        f"**Target**: `{bundle['source']['target_name']}`",
        f"**Profile**: `{bundle['source']['profile']}`",
        f"**Overall Health**: `{bundle['source']['overall_health']}`",
        f"**Architecture Era**: `{bundle['source']['architecture_era']}` ({bundle['source']['architecture_score']}/100)",
        f"**Suggested Upstream Repo**: `{bundle['suggested']['upstream_repo']}`",
        f"**Suggested Branch**: `{bundle['suggested']['branch']}`",
        "",
        "## Mission Alignment",
        "",
        bundle["contribution"]["mission_alignment"],
        "",
        "## Why This Generalizes",
        "",
        bundle["contribution"]["why_generalizes"],
        "",
        "## Evidence Summary",
        "",
        bundle["contribution"]["evidence_summary"],
        "",
        "## Top Findings",
        "",
    ]

    for finding in bundle["audit_snapshot"]["top_findings"]:
        lines.extend(
            [
                f"- **[{finding['severity'].upper()}] {finding['title']}**",
                f"  {finding['symptom']}",
            ]
        )

    lines.extend(
        [
            "",
            "## Validation",
            "",
            bundle["contribution"]["validation"],
            "",
        ]
    )
    return "\n".join(lines)


def render_pr_body(bundle: dict[str, Any], *, owner_consent: bool, public_safe: bool) -> str:
    """Render a PR body that satisfies repository governance checks."""

    checked_layers = set(bundle["contribution"]["layers"])
    public_flag = "x" if public_safe else " "
    consent_flag = "x" if owner_consent else " "

    def mark(label: str) -> str:
        return "x" if label in checked_layers else " "

    return "\n".join(
        [
            "## Mission Alignment",
            "",
            bundle["contribution"]["mission_alignment"],
            "",
            "## Contribution Mode",
            "",
            "- [x] Self-scan contribution",
            "- [ ] Maintainer improvement",
            "- [ ] Docs or governance change",
            "",
            "## Layers Changed",
            "",
            f"- [{'x' if mark('Doctrine') == 'x' else ' '}] Doctrine",
            f"- [{'x' if mark('Contract') == 'x' else ' '}] Contract",
            f"- [{'x' if mark('Scanner') == 'x' else ' '}] Scanner",
            f"- [{'x' if mark('Contribution Flow') == 'x' else ' '}] Contribution Flow",
            f"- [{'x' if mark('Governance') == 'x' else ' '}] Governance",
            "",
            "## Owner Consent",
            "",
            f"- [{consent_flag}] The agent owner explicitly agreed that this contribution may be published upstream.",
            "",
            "## Public Safety",
            "",
            f"- [{public_flag}] No secrets, credentials, proprietary code dumps, customer data, or internal-only materials are included.",
            f"- [{public_flag}] Examples and evidence have been minimized and generalized for public release.",
            "",
            "## Why This Generalizes",
            "",
            bundle["contribution"]["why_generalizes"],
            "",
            "## Evidence",
            "",
            bundle["contribution"]["evidence_summary"],
            "",
            "## Validation",
            "",
            bundle["contribution"]["validation"],
        ]
    )


def prepare_contribution_bundle(
    source: str,
    *,
    output_dir: str | None = None,
    profile: str = "personal",
    quiet: bool = False,
) -> Path:
    """Create a local self-scan contribution bundle."""

    results = _load_audit_results(source, profile=profile, quiet=quiet)
    bundle = _build_bundle(results, source=source)
    output_root = Path(output_dir) if output_dir else DEFAULT_BUNDLE_ROOT
    bundle_dir = output_root / bundle["suggested"]["slug"]
    bundle_dir.mkdir(parents=True, exist_ok=True)

    (bundle_dir / "bundle.json").write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    (bundle_dir / "SUMMARY.md").write_text(render_bundle_summary(bundle), encoding="utf-8")
    (bundle_dir / "PULL_REQUEST_BODY.md").write_text(
        render_pr_body(bundle, owner_consent=False, public_safe=False),
        encoding="utf-8",
    )
    return bundle_dir


def _load_bundle(bundle_dir: str | Path) -> tuple[Path, dict[str, Any]]:
    bundle_path = Path(bundle_dir)
    manifest_path = bundle_path / "bundle.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Bundle manifest not found: {manifest_path}")
    return bundle_path, json.loads(manifest_path.read_text(encoding="utf-8"))


def _resolve_login(command_runner: Callable[[list[str], str | None], str]) -> str:
    return command_runner(["gh", "api", "user", "--jq", ".login"], None).strip()


def _ensure_fork_exists(
    login: str,
    *,
    repo: str,
    command_runner: Callable[[list[str], str | None], str],
) -> None:
    try:
        command_runner(["gh", "repo", "view", f"{login}/hermescheck", "--json", "nameWithOwner"], None)
    except CommandError:
        command_runner(
            ["gh", "repo", "fork", repo, "--default-branch-only", "--remote=false"],
            None,
        )


def publish_bundle_to_upstream(
    bundle_dir: str | Path,
    *,
    owner_consent: bool,
    public_safe: bool,
    repo: str = DEFAULT_UPSTREAM_REPO,
    draft: bool = True,
    title_override: str | None = None,
    mission_alignment: str | None = None,
    why_generalizes: str | None = None,
    evidence_summary: str | None = None,
    layers: list[str] | None = None,
    command_runner: Callable[[list[str], str | None], str] = _run_command,
    workspace_root: str | Path | None = None,
) -> str:
    """Open a fork-based PR to the upstream hermescheck repository."""

    if not owner_consent:
        raise ValueError("Owner consent is required. Re-run with --owner-consent.")
    if not public_safe:
        raise ValueError("Public-safety confirmation is required. Re-run with --public-safe.")

    ensure_gh_available()
    bundle_path, bundle = _load_bundle(bundle_dir)
    bundle["contribution"]["owner_consent"] = True
    bundle["contribution"]["public_safe"] = True
    if mission_alignment:
        bundle["contribution"]["mission_alignment"] = mission_alignment
    if why_generalizes:
        bundle["contribution"]["why_generalizes"] = why_generalizes
    if evidence_summary:
        bundle["contribution"]["evidence_summary"] = evidence_summary
    if layers:
        bundle["contribution"]["layers"] = layers

    login = _resolve_login(command_runner)
    _ensure_fork_exists(login, repo=repo, command_runner=command_runner)

    managed_workspace = workspace_root is None
    if managed_workspace:
        temp_workspace = tempfile.TemporaryDirectory(prefix="hermescheck-contribute-")
        workspace = Path(temp_workspace.name)
    else:
        workspace = Path(workspace_root)
        workspace.mkdir(parents=True, exist_ok=True)
        temp_workspace = None

    try:
        clone_dir = workspace / "clone"
        command_runner(["gh", "repo", "clone", f"{login}/hermescheck", str(clone_dir), "--", "--depth=1"], None)
        command_runner(["git", "checkout", "-b", bundle["suggested"]["branch"]], str(clone_dir))

        upstream_path = clone_dir / bundle["suggested"]["upstream_path"]
        upstream_path.mkdir(parents=True, exist_ok=True)
        (upstream_path / "bundle.json").write_text(json.dumps(bundle, indent=2), encoding="utf-8")
        (upstream_path / "SUMMARY.md").write_text(render_bundle_summary(bundle), encoding="utf-8")

        pr_body_path = workspace / "PULL_REQUEST_BODY.md"
        pr_body_path.write_text(
            render_pr_body(bundle, owner_consent=True, public_safe=True),
            encoding="utf-8",
        )

        command_runner(["git", "add", str(upstream_path)], str(clone_dir))
        command_runner(
            ["git", "commit", "-m", bundle["suggested"]["commit_message"]],
            str(clone_dir),
        )
        command_runner(
            ["git", "push", "--set-upstream", "origin", bundle["suggested"]["branch"]],
            str(clone_dir),
        )

        pr_args = [
            "gh",
            "pr",
            "create",
            "--repo",
            repo,
            "--base",
            "main",
            "--head",
            f"{login}:{bundle['suggested']['branch']}",
            "--title",
            title_override or bundle["suggested"]["title"],
            "--body-file",
            str(pr_body_path),
        ]
        if draft:
            pr_args.append("--draft")

        return command_runner(pr_args, str(clone_dir)).strip()
    finally:
        if managed_workspace and temp_workspace is not None:
            temp_workspace.cleanup()
