from __future__ import annotations

from pathlib import Path

from hermescheck.scanners.code_execution import scan_code_execution
from hermescheck.scanners.hidden_llm import scan_hidden_llm_calls
from hermescheck.scanners.memory_patterns import scan_memory_patterns
from hermescheck.scanners.secrets import scan_secrets


def _titles(findings: list[dict]) -> list[str]:
    return [finding["title"] for finding in findings]


def test_re_compile_is_not_flagged_as_unsafe_code_execution(tmp_path: Path) -> None:
    (tmp_path / "regexes.py").write_text(
        "\n".join(
            [
                "import re",
                "EMAIL_RE = re.compile(r'[^@]+@[^@]+')",
            ]
        ),
        encoding="utf-8",
    )

    findings = scan_code_execution(tmp_path)

    assert "Unsafe code execution: compile(" not in _titles(findings)


def test_builtin_compile_remains_flagged(tmp_path: Path) -> None:
    (tmp_path / "danger.py").write_text(
        "compiled = compile(user_input, '<string>', 'exec')\n",
        encoding="utf-8",
    )

    findings = scan_code_execution(tmp_path)

    assert "Unsafe code execution: compile(" in _titles(findings)


def test_object_exec_methods_are_not_flagged_as_builtin_exec(tmp_path: Path) -> None:
    (tmp_path / "db.py").write_text(
        "\n".join(
            [
                "def query(session, statement):",
                "    return session.exec(statement).all()",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "sandbox.py").write_text(
        "result = await sandbox.exec('python3', 'setup_db.py', timeout=30)\n",
        encoding="utf-8",
    )

    findings = scan_code_execution(tmp_path)

    assert "Unsafe code execution: exec(" not in _titles(findings)


def test_generated_chunk_asset_is_skipped_for_code_execution(tmp_path: Path) -> None:
    asset_dir = tmp_path / "console" / "assets"
    asset_dir.mkdir(parents=True)
    (asset_dir / "chunk-B4BG7PRW-Czrfivbn.js").write_text(
        "function x(){ exec(userInput) }\n",
        encoding="utf-8",
    )

    findings = scan_code_execution(tmp_path)

    assert findings == []


def test_duplicated_hashed_asset_copy_is_skipped_for_code_execution(tmp_path: Path) -> None:
    asset_dir = tmp_path / "console" / "assets"
    asset_dir.mkdir(parents=True)
    (asset_dir / "cytoscape.esm-BQaXIfA_ 2.js").write_text(
        "function x(){ exec(userInput) }\n",
        encoding="utf-8",
    )

    findings = scan_code_execution(tmp_path)

    assert findings == []


def test_provider_implementation_is_not_treated_as_hidden_llm(tmp_path: Path) -> None:
    providers_dir = tmp_path / "providers"
    providers_dir.mkdir()
    (providers_dir / "openai_provider.py").write_text(
        "\n".join(
            [
                "class OpenAIProvider:",
                "    def generate(self, prompt):",
                "        return self.client.chat.completions.create(messages=[{'role': 'user', 'content': prompt}])",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text(
        "\n".join(
            [
                "from providers.openai_provider import OpenAIProvider",
                "def agent_loop(prompt):",
                "    provider = OpenAIProvider()",
                "    return provider.generate(prompt)",
            ]
        ),
        encoding="utf-8",
    )

    findings = scan_hidden_llm_calls(tmp_path)

    assert findings == []


def test_create_index_is_not_treated_as_hidden_llm_messages_create(tmp_path: Path) -> None:
    (tmp_path / "mongodb_session.py").write_text(
        "await self._messages.create_index([('session_id', 1), ('seq', 1)])\n",
        encoding="utf-8",
    )

    findings = scan_hidden_llm_calls(tmp_path)

    assert findings == []


def test_generated_chunk_asset_is_skipped_for_hidden_llm(tmp_path: Path) -> None:
    asset_dir = tmp_path / "console" / "assets"
    asset_dir.mkdir(parents=True)
    (asset_dir / "blockDiagram-VD42YOAC-Cb2bh-C5.js").write_text(
        "client.chat.completions.create(messages=[{'role':'user','content':'x'}])\n",
        encoding="utf-8",
    )

    findings = scan_hidden_llm_calls(tmp_path)

    assert findings == []


def test_repair_fallback_llm_call_is_still_flagged(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text(
        "def agent_loop(prompt):\n    return prompt\n",
        encoding="utf-8",
    )
    (tmp_path / "repair_pass.py").write_text(
        "\n".join(
            [
                "def repair_output(client, prompt):",
                "    repair_prompt = f'Repair this: {prompt}'",
                "    return client.chat.completions.create(messages=[{'role': 'user', 'content': repair_prompt}])",
            ]
        ),
        encoding="utf-8",
    )

    findings = scan_hidden_llm_calls(tmp_path)

    assert "Hidden or secondary LLM call detected" in _titles(findings)


def test_memory_admission_alone_is_not_flagged(tmp_path: Path) -> None:
    (tmp_path / "memory_manager.py").write_text(
        "\n".join(
            [
                "def save_to_memory(record):",
                "    memory_store(record)",
            ]
        ),
        encoding="utf-8",
    )

    findings = scan_memory_patterns(tmp_path)

    assert findings == []


def test_unbounded_memory_growth_is_still_flagged(tmp_path: Path) -> None:
    (tmp_path / "history.py").write_text(
        "\n".join(
            [
                "def append_message(history, message):",
                "    history.append(message)",
            ]
        ),
        encoding="utf-8",
    )

    findings = scan_memory_patterns(tmp_path)

    assert "Memory growth without apparent limit" in _titles(findings)


def test_fake_and_public_doc_keys_are_not_reported_as_real_secrets(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "docusaurus.config.js").write_text(
        "\n".join(
            [
                "algolia: {",
                "  // public key, safe to commit",
                '  apiKey: "adbd7686dceb1cd510d5ce20d04bf74c",',
                '  indexName: "docs",',
                "}",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text(
        'export DATABRICKS_TOKEN="dapi1234567890abcdef"\n',
        encoding="utf-8",
    )
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_transactions.py").write_text(
        '"openai_api_key": "sk-12345678901234567890"\n',
        encoding="utf-8",
    )

    findings = scan_secrets(tmp_path)

    assert findings == []


def test_recorded_cassettes_are_not_reported_as_real_secrets(tmp_path: Path) -> None:
    cassette_dir = tmp_path / "tests" / "models" / "cassettes" / "test_google"
    cassette_dir.mkdir(parents=True)
    (cassette_dir / "recording.yaml").write_text(
        "thoughtSignature: EtkBCtYBAXLI2nw30WDVpjR1pyPO7RX8irBHXj_Gr3vxDSk-rgwZCdVoqguEYP\n",
        encoding="utf-8",
    )

    findings = scan_secrets(tmp_path)

    assert findings == []


def test_real_looking_secret_is_still_reported(tmp_path: Path) -> None:
    (tmp_path / "settings.py").write_text(
        'OPENAI_API_KEY = "sk-liveproductiontokenabcdef123456"\n',
        encoding="utf-8",
    )

    findings = scan_secrets(tmp_path)

    assert "Hardcoded secret or API key detected" in _titles(findings)
