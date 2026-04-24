"""CLI entry point for hermescheck."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from hermescheck import __version__
from hermescheck.audit import run_audit, save_results
from hermescheck.config import AuditConfig, should_fail_for_threshold
from hermescheck.contribute import (
    CONTRIBUTION_LAYERS,
    prepare_contribution_bundle,
    publish_bundle_to_upstream,
)
from hermescheck.report import generate_report
from hermescheck.sarif import generate_sarif, save_sarif
from hermescheck.schema import validate_report
from hermescheck.self_review import load_self_review

KNOWN_COMMANDS = {"audit", "report", "validate", "contribute"}


def _normalize_argv(argv: Sequence[str]) -> list[str]:
    normalized = list(argv)
    if normalized and not normalized[0].startswith("-") and normalized[0] not in KNOWN_COMMANDS:
        return ["audit", *normalized]
    return normalized


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hermescheck",
        description="Audit the architecture and health of any AI agent system or LLM-integrated project.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"hermescheck {__version__}")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    audit_parser = subparsers.add_parser("audit", help="Run audit against target directory")
    audit_parser.add_argument("target", help="Path to agent project directory")
    audit_parser.add_argument("-o", "--output", default="audit_results.json", help="Output JSON file")
    audit_parser.add_argument("-r", "--report", default="audit_report.md", help="Output markdown report")
    audit_parser.add_argument("--sarif", help="Optional SARIF output path for GitHub code scanning")
    audit_parser.add_argument(
        "--self-review",
        help="Optional target-agent self-review JSON generated before hermescheck static scanning",
    )
    audit_parser.add_argument(
        "--profile",
        default="personal",
        choices=["personal", "enterprise", "personal_development", "enterprise_production"],
        help="Audit strictness profile",
    )
    audit_parser.add_argument(
        "--fail-on",
        default="none",
        choices=["none", "low", "medium", "high", "critical"],
        help="Exit non-zero when a finding at or above this severity exists",
    )
    audit_parser.add_argument("-q", "--quiet", action="store_true", help="Suppress progress output")
    audit_parser.set_defaults(func=cmd_audit)

    report_parser = subparsers.add_parser("report", help="Generate report from JSON results")
    report_parser.add_argument("input", help="Input JSON results file")
    report_parser.add_argument("-o", "--output", help="Output markdown file (prints to stdout if omitted)")
    report_parser.set_defaults(func=cmd_report)

    validate_parser = subparsers.add_parser("validate", help="Validate audit results against schema")
    validate_parser.add_argument("input", help="JSON results file to validate")
    validate_parser.set_defaults(func=cmd_validate)

    contribute_parser = subparsers.add_parser("contribute", help="Prepare and upstream self-scan contributions")
    contribute_subparsers = contribute_parser.add_subparsers(dest="contribute_command", help="Contribution commands")

    prepare_parser = contribute_subparsers.add_parser(
        "prepare",
        help="Create a local contribution bundle from audit results or a target directory",
    )
    prepare_parser.add_argument("input", help="Audit JSON file or target directory to scan")
    prepare_parser.add_argument("--output-dir", help="Where to write the contribution bundle")
    prepare_parser.add_argument(
        "--profile",
        default="personal",
        choices=["personal", "enterprise", "personal_development", "enterprise_production"],
        help="Audit profile when the input is a target directory",
    )
    prepare_parser.add_argument("-q", "--quiet", action="store_true", help="Suppress progress output")
    prepare_parser.set_defaults(func=cmd_contribute_prepare)

    pr_parser = contribute_subparsers.add_parser(
        "pr",
        help="Open a fork-based upstream PR from a prepared contribution bundle",
    )
    pr_parser.add_argument("bundle", help="Path to a bundle directory created by `hermescheck contribute prepare`")
    pr_parser.add_argument("--owner-consent", action="store_true", help="Confirm the agent owner approved publication")
    pr_parser.add_argument(
        "--public-safe", action="store_true", help="Confirm the contribution is safe for public release"
    )
    pr_parser.add_argument("--repo", default="huangrichao2020/hermescheck", help="Upstream repository to target")
    pr_parser.add_argument("--ready", action="store_true", help="Create a ready-for-review PR instead of a draft")
    pr_parser.add_argument("--title", help="Override the suggested PR title")
    pr_parser.add_argument("--mission-alignment", help="Override the mission alignment paragraph")
    pr_parser.add_argument("--why-generalizes", help="Override the generalization explanation")
    pr_parser.add_argument("--evidence-summary", help="Override the evidence summary paragraph")
    pr_parser.add_argument(
        "--layer",
        action="append",
        choices=[layer.lower().replace(" ", "-") for layer in CONTRIBUTION_LAYERS],
        help="Override the affected layer list",
    )
    pr_parser.set_defaults(func=cmd_contribute_pr)
    return parser


def cmd_audit(args: argparse.Namespace) -> int:
    """Run audit against target directory."""

    config = AuditConfig.from_profile(args.profile, fail_on=args.fail_on)
    self_review = load_self_review(args.self_review) if args.self_review else None
    results = run_audit(args.target, config=config, self_review=self_review, verbose=not args.quiet)
    save_results(results, args.output)
    generate_report(results, args.report)

    if args.sarif:
        save_sarif(generate_sarif(results), args.sarif)

    if not args.quiet:
        print(f"\n📋 Results: {args.output}")
        print(f"📄 Report: {args.report}")
        if args.sarif:
            print(f"🛡️  SARIF: {args.sarif}")

    if should_fail_for_threshold(results, args.fail_on):
        if not args.quiet:
            print(f"❌ Failing because findings met the --fail-on {args.fail_on} threshold.")
        return 1
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Generate markdown report from JSON results."""

    with open(args.input, encoding="utf-8") as handle:
        results = json.load(handle)

    errors = validate_report(results)
    if errors:
        print("⚠️  Schema validation errors:")
        for error in errors:
            print(f"  - {error}")
        print()

    markdown = generate_report(results)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(markdown)
        print(f"Report saved to: {args.output}")
    else:
        print(markdown)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate audit results against schema."""

    with open(args.input, encoding="utf-8") as handle:
        results = json.load(handle)

    errors = validate_report(results)
    if errors:
        print(f"❌ Schema validation failed ({len(errors)} errors):")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("✅ Schema validation passed")
    return 0


def cmd_contribute_prepare(args: argparse.Namespace) -> int:
    """Create a local contribution bundle."""

    bundle_dir = prepare_contribution_bundle(
        args.input,
        output_dir=args.output_dir,
        profile=args.profile,
        quiet=args.quiet,
    )
    if not args.quiet:
        print(f"🧭 Contribution bundle: {bundle_dir}")
        print(f"📝 Review summary: {bundle_dir / 'SUMMARY.md'}")
        print(f"📬 Draft PR body: {bundle_dir / 'PULL_REQUEST_BODY.md'}")
    return 0


def cmd_contribute_pr(args: argparse.Namespace) -> int:
    """Publish a prepared contribution bundle to the upstream repository."""

    try:
        layers = None
        if args.layer:
            layers = [layer.replace("-", " ").title() for layer in args.layer]
            layers = ["Contribution Flow" if layer == "Contribution Flow" else layer for layer in layers]
        pr_url = publish_bundle_to_upstream(
            args.bundle,
            owner_consent=args.owner_consent,
            public_safe=args.public_safe,
            repo=args.repo,
            draft=not args.ready,
            title_override=args.title,
            mission_alignment=args.mission_alignment,
            why_generalizes=args.why_generalizes,
            evidence_summary=args.evidence_summary,
            layers=layers,
        )
    except Exception as exc:  # pragma: no cover - CLI error surface
        print(f"❌ {exc}")
        return 1

    print(f"✅ Pull request created: {pr_url}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(_normalize_argv(list(argv if argv is not None else sys.argv[1:])))
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
