# Layered Architecture

`hermescheck` should remain layered so it can grow without turning into a bag of heuristics.

## Layer 1: Doctrine

Defines:

- principles
- failure mode vocabulary
- risk framing
- fix order and trade-offs

This is the highest layer. If scanner behavior changes but doctrine stays implicit, the project becomes noisy and fragile.

## Layer 2: Contract

Defines what the scanned project says about itself.

Examples:

- where provider modules live
- where the main loop lives
- which memory writes are expected
- which tools are intentionally high-agency
- which controls exist: approval, sandbox, allowlist

Future work such as `hermescheck.yaml` belongs here.

## Layer 3: Scanner

Implements lightweight verification.

Examples:

- regex fallback
- Python AST rules
- JS/TS tree-sitter rules
- framework packs

The scanner layer should validate declared architecture and suspicious deviations. It should not guess everything from scratch.

## Layer 4: Contribution Flow

Turns local scan results into reusable upstream knowledge.

This layer should support:

- self-scan contribution bundles
- public-safe evidence extraction
- fork-based upstream PR generation
- structured claims about false positives, true positives, and missing patterns

## Layer 5: Governance

Keeps the project healthy and durable.

Examples:

- PR templates
- CODEOWNERS
- required review policy
- branch protections and status checks
- repo-level contribution rules

## Design Rule

Every substantial change should identify its primary layer.

If a change spans multiple layers, document that explicitly. The healthiest contributions usually move one layer directly and one adjacent layer in support.
