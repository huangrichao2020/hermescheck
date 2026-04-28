# hermescheck 1.2.5 Release Notes

`hermescheck` 1.2.5 recalibrates static execution-risk findings for Hermes
Agent and similar stateful agent runtimes.

## Highlights

- Static matches for `exec()`, `eval()`, `compile()`, `os.system()`,
  `subprocess(shell=True)`, and `new Function()` are now medium-risk review
  findings instead of automatic critical findings.
- Enterprise high-agency capability checks now distinguish regex-level markers
  from confirmed unsafe dispatch paths.
- Plugin-loader guidance now recommends scoped policy instead of blanket
  removal of Python runtime helpers such as `open()`, `getattr()`, and imports.
- Maturity-score penalties for plugin sandbox, high-agency tool policy, and
  high-agency remote tools were reduced to match the new severity model.
- The VS Code extension version is aligned to `1.2.5`.

## Why It Matters

Hermes-style agents often need controlled command execution, plugin loading,
file access, imports, and third-party library internals. Treating every
dangerous function or shell marker as critical makes reports harder to act on
and can push implementers toward brittle sandboxes.

The new model keeps the signal, but lowers the default severity until the
review can confirm the full chain: untrusted input, reachable execution path,
missing isolation, and meaningful blast radius.

## Validation

```bash
uv run ruff check hermescheck tests
uv run ruff format --check hermescheck tests
uv run pytest tests -q
uv run python -m hermescheck --version
uv build
uv run twine check dist/hermescheck-1.2.5.tar.gz \
  dist/hermescheck-1.2.5-py3-none-any.whl
```
