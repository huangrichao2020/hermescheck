from __future__ import annotations

import json
from pathlib import Path

from hermescheck import cli
from hermescheck.contribute import CommandError, publish_bundle_to_upstream


def _sample_audit_report(target_name: str = "/tmp/example-agent") -> dict:
    return {
        "schema_version": "hermescheck.report.v1",
        "scan_metadata": {
            "profile": "enterprise_production",
            "scan_timestamp": "2026-04-24T12:00:00",
            "scan_duration_seconds": 0.42,
            "scanner_count": 8,
        },
        "executive_verdict": {
            "overall_health": "high_risk",
            "primary_failure_mode": "Hidden or secondary LLM call detected",
            "most_urgent_fix": "Consolidate provider and hidden-repair call routing.",
        },
        "scope": {
            "target_name": target_name,
            "entrypoints": [f"{target_name}/main.py"],
            "channels": ["cli"],
            "model_stack": ["openai"],
            "time_window": "current_state",
            "layers_to_audit": ["tool_execution", "fallback_loops"],
        },
        "severity_summary": {
            "critical": 0,
            "high": 1,
            "medium": 0,
            "low": 0,
        },
        "maturity_score": {
            "score": 42,
            "raw_points": 50,
            "penalty": 8,
            "era_key": "iron_age",
            "era_name": "铁器时代",
            "era_description": "具备较清晰的工具、记忆和技能分层，开始可维护。",
            "share_line": "这个 Agent 项目处于 铁器时代（42/100）：具备较清晰的工具、记忆和技能分层，开始可维护。",
            "methodology_gate": {
                "detected": True,
                "cap_applied": False,
                "note": "已发现方法论层，项目具备进入青铜以上时代的地基。",
            },
            "strengths": ["agent runtime", "tool/syscall boundary"],
            "next_milestones": ["把线性 summary/compact 升级为 page table、LRU/hot-cold 和 swap-in。"],
            "evidence_refs": [f"{target_name}/main.py:1"],
        },
        "evidence_pack": [
            {
                "kind": "code",
                "source": "Hidden or secondary LLM call detected",
                "location": f"{target_name}/repair_pass.py:2",
                "summary": "Repair-pass LLM call outside the main loop.",
                "time_scope": "current_state",
            }
        ],
        "findings": [
            {
                "severity": "high",
                "title": "Hidden or secondary LLM call detected",
                "symptom": "Repair-pass LLM call found outside the main loop.",
                "user_impact": "Secondary calls may bypass safety and cost controls.",
                "source_layer": "llm_routing",
                "mechanism": "Repair-pass pattern plus LLM call pattern matched.",
                "root_cause": "Repair call is not declared as part of the primary loop.",
                "evidence_refs": [f"{target_name}/repair_pass.py:2"],
                "confidence": 0.82,
                "fix_type": "code_change",
                "recommended_fix": "Move repair behavior into declared orchestration or make it explicit.",
            }
        ],
        "conflict_map": [],
        "ordered_fix_plan": [
            {
                "order": 1,
                "goal": "Hidden or secondary LLM call detected",
                "why_now": "High-risk hidden routing should be reviewed first.",
                "expected_effect": "Restore a single explicit LLM path.",
            }
        ],
    }


def test_contribute_prepare_creates_bundle_from_audit_results(tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.json"
    output_root = tmp_path / "bundles"
    audit_path.write_text(json.dumps(_sample_audit_report()), encoding="utf-8")

    exit_code = cli.main(
        [
            "contribute",
            "prepare",
            str(audit_path),
            "--output-dir",
            str(output_root),
            "--quiet",
        ]
    )

    assert exit_code == 0
    bundle_dirs = [path for path in output_root.iterdir() if path.is_dir()]
    assert len(bundle_dirs) == 1

    bundle_dir = bundle_dirs[0]
    bundle = json.loads((bundle_dir / "bundle.json").read_text(encoding="utf-8"))
    assert bundle["bundle_version"] == "hermescheck.contribution.v1"
    assert bundle["source"]["target_name"] == "/tmp/example-agent"
    assert bundle["suggested"]["upstream_repo"] == "huangrichao2020/hermescheck"
    assert bundle["contribution"]["owner_consent"] is False
    assert (bundle_dir / "SUMMARY.md").exists()
    assert (bundle_dir / "PULL_REQUEST_BODY.md").exists()


def test_contribute_pr_requires_owner_consent(tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.json"
    output_root = tmp_path / "bundles"
    audit_path.write_text(json.dumps(_sample_audit_report()), encoding="utf-8")
    cli.main(
        [
            "contribute",
            "prepare",
            str(audit_path),
            "--output-dir",
            str(output_root),
            "--quiet",
        ]
    )
    bundle_dir = next(path for path in output_root.iterdir() if path.is_dir())

    exit_code = cli.main(
        [
            "contribute",
            "pr",
            str(bundle_dir),
            "--public-safe",
        ]
    )

    assert exit_code == 1


def test_publish_bundle_to_upstream_uses_fork_based_pr_flow(tmp_path: Path, monkeypatch) -> None:
    audit_path = tmp_path / "audit.json"
    output_root = tmp_path / "bundles"
    audit_path.write_text(json.dumps(_sample_audit_report()), encoding="utf-8")
    cli.main(
        [
            "contribute",
            "prepare",
            str(audit_path),
            "--output-dir",
            str(output_root),
            "--quiet",
        ]
    )
    bundle_dir = next(path for path in output_root.iterdir() if path.is_dir())

    calls: list[tuple[list[str], str | None]] = []
    workspace_root = tmp_path / "workspace"

    def fake_run_command(args: list[str], cwd: str | None = None) -> str:
        calls.append((args, cwd))

        if args[:4] == ["gh", "api", "user", "--jq"]:
            return "mockuser\n"
        if args[:3] == ["gh", "repo", "view"]:
            raise CommandError(args=args, returncode=1, stdout="", stderr="not found")
        if args[:3] == ["gh", "repo", "fork"]:
            return ""
        if args[:3] == ["gh", "repo", "clone"]:
            clone_dir = Path(args[4])
            clone_dir.mkdir(parents=True, exist_ok=True)
            (clone_dir / ".git").mkdir()
            return ""
        if args[:2] == ["git", "checkout"]:
            return ""
        if args[:2] == ["git", "add"]:
            return ""
        if args[:2] == ["git", "commit"]:
            return ""
        if args[:2] == ["git", "push"]:
            return ""
        if args[:3] == ["gh", "pr", "create"]:
            return "https://github.com/huangrichao2020/hermescheck/pull/999\n"

        raise AssertionError(f"Unexpected command: {args}")

    monkeypatch.setattr("hermescheck.contribute.ensure_gh_available", lambda: None)

    pr_url = publish_bundle_to_upstream(
        bundle_dir,
        owner_consent=True,
        public_safe=True,
        command_runner=fake_run_command,
        workspace_root=workspace_root,
    )

    assert pr_url == "https://github.com/huangrichao2020/hermescheck/pull/999"
    assert any(args[:3] == ["gh", "repo", "fork"] for args, _ in calls)
    assert any(
        args[:3] == ["gh", "pr", "create"] and "--head" in args and "mockuser:" in args[args.index("--head") + 1]
        for args, _ in calls
    )

    contribution_dirs = list((workspace_root / "clone" / "contributions" / "self-scan").iterdir())
    assert len(contribution_dirs) == 1
    contribution_dir = contribution_dirs[0]
    assert (contribution_dir / "bundle.json").exists()
    assert (contribution_dir / "SUMMARY.md").exists()


def test_prepare_bundle_prefers_real_issue_over_generated_asset_noise(tmp_path: Path) -> None:
    asset_dir = tmp_path / "src" / "console" / "assets"
    asset_dir.mkdir(parents=True)
    (asset_dir / "chunk-B4BG7PRW-Czrfivbn.js").write_text(
        "function x(){ exec(userInput) }\n",
        encoding="utf-8",
    )
    (tmp_path / "terminal_cmd.py").write_text(
        "import subprocess\nsubprocess.run(f'kill {pid}', shell=True)\n",
        encoding="utf-8",
    )

    output_root = tmp_path / "bundles"
    exit_code = cli.main(
        [
            "contribute",
            "prepare",
            str(tmp_path),
            "--profile",
            "enterprise",
            "--output-dir",
            str(output_root),
            "--quiet",
        ]
    )

    assert exit_code == 0
    bundle_dir = next(path for path in output_root.iterdir() if path.is_dir())
    bundle = json.loads((bundle_dir / "bundle.json").read_text(encoding="utf-8"))
    top_finding = bundle["audit_snapshot"]["top_findings"][0]
    assert top_finding["title"] == "Unsafe code execution: subprocess(shell=True)"
