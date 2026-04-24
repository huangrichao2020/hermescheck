# Self-Scan Contributions

This directory is the upstream landing zone for fork-based self-scan contribution bundles.

Each contribution bundle should live under:

- `contributions/self-scan/<bundle-slug>/bundle.json`
- `contributions/self-scan/<bundle-slug>/SUMMARY.md`

These bundles are not treated as blindly trusted truth. They are review artifacts that help maintainers convert real-world agent findings into:

- doctrine improvements
- contract design improvements
- scanner tuning
- framework packs
- governance refinements

The preferred way to create a bundle is:

```bash
hermescheck contribute prepare audit_results.json
```

Then, after owner consent and public-safety review:

```bash
hermescheck contribute pr .hermescheck/contributions/<bundle-slug> \
  --owner-consent \
  --public-safe
```

The resulting PR should come from a fork and target `huangrichao2020/hermescheck`.
