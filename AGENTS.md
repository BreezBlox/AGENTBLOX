# AGENTS.md

## Purpose
This workspace is configured for Codex-first eBay arbitrage workflows.
Use `ebay-arbitrage-plugin/` as the active system of record.

## Active Stack (Use These)
- Hub skill: `ebay-arbitrage-plugin/skills/ebay-arbitrage-hub/SKILL.md`
- Specialist skills:
  - `ebay-arbitrage-plugin/skills/listing-optimizer/SKILL.md`
  - `ebay-arbitrage-plugin/skills/sourcing-analyst/SKILL.md`
  - `ebay-arbitrage-plugin/skills/arbitrage-calculator/SKILL.md`
  - `ebay-arbitrage-plugin/skills/compliance-guardian/SKILL.md`
  - `ebay-arbitrage-plugin/skills/meta-improver/SKILL.md`
- Role agents: `ebay-arbitrage-plugin/agents/*/SKILL.md`
- Commands: `ebay-arbitrage-plugin/commands/*.md`
- Scripts: `ebay-arbitrage-plugin/scripts/*.py`

## Routing Rules
When user intent is unclear, route through hub first.

- "is this worth selling", "evaluate this deal":
  1) arbitrage-calculator
  2) sourcing-analyst
  3) listing-optimizer
  4) compliance-guardian
- "find supplier", "source this item": sourcing-analyst
- "optimize listing", "title/SEO/item specifics": listing-optimizer
- "policy/risk/vero": compliance-guardian
- "improve process/workflow": meta-improver

## Output Policy
- HTML dashboard is the canonical report artifact.
- Preferred generation path:
  - `python ebay-arbitrage-plugin/scripts/exact_match_pipeline.py <report.md> --output <report.html>`
- Report contracts expected:
  - run manifest: `ebay-arbitrage-plugin/reports/.runs/<run-id>/manifest.json`
  - evidence: `ebay-arbitrage-plugin/reports/.evidence/<run-id>/evidence.json`

## Sourcing Policy
- AliExpress-only for sourcing recommendations and source links.
- Do not propose Alibaba/1688/DHgate in new recommendations.

## Workspace Notes
- Legacy content is archived under `_archive/` and should not be used unless explicitly requested.
- Git hook path may be configured to `.githooks` to normalize staged report links.
