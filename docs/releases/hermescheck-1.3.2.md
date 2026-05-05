# hermescheck 1.3.2 Release Notes

`hermescheck` 1.3.2 focused on making audits finish reliably on real-world
checkouts with large dependency, environment, and generated-output directories.

## Headline

This release prunes large skipped directories across scanner families, keeping
the audit focused on runtime source paths instead of spending time in
`node_modules/`, `.venv/`, build outputs, or generated assets.

## What Changed

- Applied shared path filtering to more scanners so dependency and environment
  directories are skipped consistently.
- Reduced scan time and report noise on large agent repositories.
- Added schema coverage for skipped-directory reporting.
- Clarified VS Code extension troubleshooting around audit scope and large
  directories.
- Updated package and extension metadata to `1.3.2`.

## Why It Matters

Architecture audits should complete on the repository a maintainer actually
has, not just on a small curated fixture. Version 1.3.2 made `hermescheck` more
practical for large Hermes-style worktrees by pruning directories that do not
belong in the runtime audit surface.

