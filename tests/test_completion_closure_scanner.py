from __future__ import annotations

from pathlib import Path

from hermescheck.scanners.completion_closure import scan_completion_closure


def test_completion_closure_flags_file_and_index_without_memory_closure(tmp_path: Path) -> None:
    (tmp_path / "memory_writer.py").write_text(
        "\n".join(
            [
                "from pathlib import Path",
                "def save_memory(name, content):",
                "    Path('memory').mkdir(exist_ok=True)",
                "    Path('memory').joinpath(name).write_text(content)",
                "    update_index(name)",
                "    return 'task complete'",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text(
        "Flow: create file -> update index -> done.\n",
        encoding="utf-8",
    )

    findings = scan_completion_closure(tmp_path)

    assert len(findings) == 1
    assert findings[0]["title"] == "Completion closure gap detected"
    assert findings[0]["severity"] == "high"
    assert "impression card" in findings[0]["symptom"]
    assert "pointer registration" in findings[0]["symptom"]


def test_completion_closure_accepts_full_reusable_memory_flow(tmp_path: Path) -> None:
    (tmp_path / "memory_flow.md").write_text(
        "\n".join(
            [
                "Flow: file creation -> index update -> impression card -> anchor mapping -> pointer registration -> acceptance.",
                "Create file in memory/pages.",
                "Update index and manifest.",
                "Create an impression card for quick recall.",
                "Add anchor mapping from topic to semantic anchor.",
                "Register pointer_ref and pointer_type in the page table entry.",
                "Acceptance criteria: next time the agent can find and reuse this memory quickly.",
            ]
        ),
        encoding="utf-8",
    )

    assert scan_completion_closure(tmp_path) == []
