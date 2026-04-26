# HermesCheck

Run Hermes Agent architecture and runtime health checks from VS Code.

## Usage

1. Install the `hermescheck` CLI:

   ```bash
   pip install hermescheck
   ```

2. Open a Hermes Agent checkout or fork in VS Code.
3. Run `HermesCheck: Audit Workspace` from the command palette.

The extension writes JSON and Markdown audit outputs to a temporary directory
and opens the Markdown report after the scan completes.

## Settings

- `hermescheck.executable`: path to the `hermescheck` CLI.
- `hermescheck.profile`: audit profile passed to the CLI.
