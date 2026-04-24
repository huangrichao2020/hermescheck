from __future__ import annotations

from pathlib import Path

from hermescheck.scanners.impression_memory import scan_impression_memory


def test_impression_memory_flags_fact_and_skill_system_without_impressions(tmp_path: Path) -> None:
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    (memory_dir / "facts.md").write_text(
        "\n".join(
            [
                "fact: user lives near Hangzhou Normal University in Yuhang",
                "preference: concise Chinese replies",
                "session history stores conversation chunks",
            ]
        ),
        encoding="utf-8",
    )
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    (skills_dir / "github_pr_skill.md").write_text(
        "\n".join(
            [
                "skill: upstream PR workflow",
                "procedure: branch, commit, push, open PR",
                "runbook: respond to review comments",
            ]
        ),
        encoding="utf-8",
    )

    findings = scan_impression_memory(tmp_path)

    assert len(findings) == 1
    assert findings[0]["title"] == "Impression memory layer missing"
    assert "retrieval hints" in findings[0]["recommended_fix"]


def test_impression_memory_accepts_associative_impression_chunks(tmp_path: Path) -> None:
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    (memory_dir / "facts.md").write_text(
        "fact: user lives near Hangzhou Normal University in Yuhang\npreference: concise replies\n",
        encoding="utf-8",
    )
    (memory_dir / "impressions.md").write_text(
        "\n".join(
            [
                "impression: Yuhang Hangzhou Normal University to West Lake Longxiangqiao",
                "topic_anchor: route to Longxiangqiao from Yuhang",
                "route hint: Line 5 is the concept cue; retrieve exact transfer details only when needed.",
                "pointer_type: vector_id",
                "pointer_ref: vec_hangzhou_metro_88392",
                "semantic_hash: yuhang-westlake-line5",
                "status: IN_MIND",
                "linked concepts: Hangzhou, metro, West Lake, Longxiangqiao",
            ]
        ),
        encoding="utf-8",
    )
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    (skills_dir / "travel_skill.md").write_text(
        "skill: query current route details\nprocedure: verify live transit before departure\n",
        encoding="utf-8",
    )

    assert scan_impression_memory(tmp_path) == []


def test_impression_memory_flags_impressions_without_pointers(tmp_path: Path) -> None:
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    (memory_dir / "facts.md").write_text(
        "fact: user lives near Hangzhou Normal University in Yuhang\npreference: concise replies\n",
        encoding="utf-8",
    )
    (memory_dir / "impressions.md").write_text(
        "\n".join(
            [
                "impression: Yuhang to Longxiangqiao",
                "route hint: Line 5 feels like the right first route.",
                "linked concepts: Hangzhou, metro, West Lake",
            ]
        ),
        encoding="utf-8",
    )
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    (skills_dir / "travel_skill.md").write_text(
        "skill: query current route details\nprocedure: verify live transit before departure\n",
        encoding="utf-8",
    )

    findings = scan_impression_memory(tmp_path)

    assert len(findings) == 1
    assert findings[0]["title"] == "Impression pointers missing"
    assert "ImpressionPage" in findings[0]["recommended_fix"]
