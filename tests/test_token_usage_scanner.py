from __future__ import annotations

from pathlib import Path

from hermescheck.audit import run_audit
from hermescheck.config import AuditConfig
from hermescheck.maturity import score_maturity
from hermescheck.scanners.token_usage import scan_token_usage
from hermescheck.schema import validate_report


def _titles(findings: list[dict]) -> list[str]:
    return [finding["title"] for finding in findings]


def test_token_usage_flags_large_context_without_thrift_controls(tmp_path: Path) -> None:
    (tmp_path / "agent.py").write_text(
        "\n".join(
            [
                "MAX_CONTEXT_TOKENS = 200_000",
                "class Agent:",
                "    def chat(self, conversation_history):",
                "        messages = list(conversation_history)",
                "        return self.llm.chat(messages=messages, max_context_tokens=MAX_CONTEXT_TOKENS)",
            ]
        ),
        encoding="utf-8",
    )

    findings = scan_token_usage(tmp_path)
    titles = _titles(findings)

    assert "Large context window used as default token budget" in titles
    assert "Full-history prompt assembly lacks token budget" in titles


def test_token_usage_accepts_genericagent_style_thrift_design(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "\n".join(
            [
                "Token Efficient: <30K context window, not 200K-1M brute force context.",
                "Layered Memory: L0 meta rules, L1 insight index, L2 facts, L3 task skills, L4 session archive.",
                "Each task crystallizes into a skill tree entry for direct recall on the next similar task.",
                "Retrieval uses top_k=5, token_budget=6000, page_table recall, and right knowledge in scope.",
                "The agent loop is a ~100-line agent loop with a minimal toolset and less noise.",
            ]
        ),
        encoding="utf-8",
    )

    assert scan_token_usage(tmp_path) == []


def test_token_usage_flags_bulk_repository_prompt_without_budget(tmp_path: Path) -> None:
    (tmp_path / "prompt_builder.ts").write_text(
        "\n".join(
            [
                "export async function buildPrompt(root: string, chatHistory: Message[]) {",
                "  const context = [];",
                "  for (const file of glob('**/*')) {",
                "    context.push(readFileSync(file, 'utf8'));",
                "  }",
                "  return model.chat({ messages: [...chatHistory, { role: 'system', content: context.join('\\n') }] });",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    titles = _titles(scan_token_usage(tmp_path))

    assert "Full-history prompt assembly lacks token budget" in titles


def test_token_usage_findings_heavily_penalize_maturity(tmp_path: Path) -> None:
    (tmp_path / "agent_design.md").write_text(
        "\n".join(
            [
                "Methodology checklist, agent loop, tool_call, scheduler, memory, RAG, vector store.",
                "Capability table, permission policy, daemon lifecycle, plugin sandbox, remote MCP boundary.",
                "Stateful Agent recovery, environment state, LLM CLI worker task envelope.",
                "External signal, source reading, pattern extraction, constraint adaptation, safe landing, verification closure.",
            ]
        ),
        encoding="utf-8",
    )
    raw = score_maturity(tmp_path, findings=[])
    penalized = score_maturity(
        tmp_path,
        findings=[
            {
                "title": "Large context window used as default token budget",
                "severity": "critical",
            },
            {
                "title": "Token-efficient memory/skill reuse strategy missing",
                "severity": "high",
            },
        ],
    )

    assert penalized["penalty"] >= 45
    assert penalized["score"] <= raw["score"] - 30


def test_token_usage_scanner_is_enabled_and_schema_valid(tmp_path: Path) -> None:
    (tmp_path / "agent.py").write_text(
        "\n".join(
            [
                "MAX_CONTEXT_TOKENS = 1_000_000",
                "def run_agent(chat_history):",
                "    messages = all_messages + chat_history",
                "    return llm.chat(messages=messages, max_context_tokens=MAX_CONTEXT_TOKENS)",
            ]
        ),
        encoding="utf-8",
    )

    results = run_audit(str(tmp_path), config=AuditConfig.from_profile("personal"), verbose=False)
    titles = _titles(results["findings"])

    assert validate_report(results) == []
    assert "Large context window used as default token budget" in titles
