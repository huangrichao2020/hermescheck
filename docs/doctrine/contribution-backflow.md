# Contribution Backflow

The preferred upstreaming model for `hermescheck` is:

`self-scan -> local review -> owner consent -> public-safe bundle -> fork PR -> upstream generalization`

This is the recommended `B` path for long-term governance.

## Why Fork-Based PRs

Fork-based contributions are the right default because they:

- preserve contributor control
- keep upstream review explicit
- avoid forcing write access or direct-PR automation
- reduce the risk of accidental private-data publication
- fit public open source governance better than direct repository writes

## Self-Scan Backflow Flow

1. An external agent project loads `hermescheck` and scans itself.
2. The agent or maintainer reviews the report locally.
3. They decide what is worth generalizing into `hermescheck`.
4. The agent owner explicitly consents before anything public is prepared.
5. A contribution bundle is created with only public-safe, minimal evidence.
6. The contributor opens a fork-based PR to `huangrichao2020/hermescheck`.
7. The upstream PR explains:
   - the pattern
   - why it generalizes
   - which layer it improves
   - what tests/docs were added

## What Should Flow Back

Good upstream candidates include:

- a false positive that can be generalized away
- a true positive pattern seen repeatedly across projects
- a framework-specific interpretation rule
- doctrine improvements that sharpen vocabulary or review judgment
- governance improvements that improve contribution quality

## What Should Not Flow Back

Do not upstream:

- raw customer code
- proprietary prompts or datasets
- credentials or tokens
- internal URLs or environment topology
- project-specific churn that does not generalize

## CLI Surface

The current CLI surface is:

- `hermescheck contribute prepare`
- `hermescheck contribute pr --owner-consent`

`prepare` should build a local contribution bundle.

`pr` is opt-in and defaults to a fork-based upstream flow. It should never become a blind direct push to the canonical repository.

## Natural-Language Agent Flow

Many users will not run the contribution flow by hand. They will ask their own coding agent to do it.

Recommended prompt:

```text
请在当前项目安装并运行 hermescheck，用 personal profile 生成架构时代评分和报告；请总结 share_line、top findings、误报和可泛化优化建议；如果我确认 owner-consent 和 public-safe，请用 hermescheck contribute prepare 生成贡献包，并通过 fork-based PR 提交到 https://github.com/huangrichao2020/hermescheck。
```

The agent must still stop before publishing unless the owner explicitly confirms both `owner-consent` and `public-safe`.
