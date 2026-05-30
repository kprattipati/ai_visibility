# CLAUDE.md

## Project Overview

This project is an early MVP for **ARI: Agentic Recommendation Index**.

ARI benchmarks how likely AI assistants and answer engines are to recommend a local business compared with competitors in the same city, category, and geographic service area. The initial use case is local SMB visibility in AI-mediated search and recommendation flows.

The product hypothesis:

> As search becomes more conversational and recommendation-driven, SMBs will need to know whether AI systems recommend them, which competitors appear more often, and what evidence/signals they need to improve their inclusion rate.

The first customer-facing product should be an **AI visibility snapshot** for cold outreach, followed by a paid deeper audit.

## Starting Market

Initial vertical:

- Personal injury law firms

Initial city:

- Houston, TX

Current seeded competitor set:

- The Ammons Law Firm, LLP
- Bankston & Associates
- Blizzard Law, PLLC
- The Lanier Law Firm
- Arnold & Itkin LLP
- The Krist Law Firm, P.C.
- The Sher Law Firm, PLLC
- Sorey & Hoover, LLP
- Sorrels Law
- Baumgartner Law Firm
- Stephen Boutros, LTD.
- HURTINTEXAS.COM Law Firm
- Leo & Oginni Personal Injury Lawyers, PLLC
- Shariff Injury Lawyers
- Simon & O'Rourke Car Accident & Personal Injury Lawyers

## Stack

- Language: Python 3
- Dependencies: standard library only for now
- CLI: `argparse`
- Storage: SQLite via Python `sqlite3`
- API calls: standard-library `urllib`
- Tests: `unittest`
- Current model provider support:
  - `mock`: implemented
  - `openai`: implemented through the Responses API
  - `perplexity`: config placeholder only
  - `claude`: config placeholder only
  - `gemini`: config placeholder only

Provider config lives in:

```text
config/providers.json
```

Do not put raw API keys in config. Use environment variables such as:

```bash
export OPENAI_API_KEY="..."
```

## Current Build Status

Done:

- Seeded top U.S. cities and legal practice areas.
- Generates high-intent buyer prompts for legal-service recommendations.
- Supports geographic prompt scopes:
  - city
  - sample city/neighborhood/ZIP mix
  - neighborhood
  - ZIP code
- Has a mock engine for no-cost pipeline testing.
- Has an OpenAI engine adapter.
- Stores benchmark state in SQLite.
- Caches model answers by:
  - prompt
  - engine
  - candidate competitor set
- Scores firms with an AI visibility score using:
  - mention rate
  - recommendation rate
  - top-3 mention rate
  - citation rate
- Produces Markdown audit reports.
- Extracts structured recommendation reasons through `Recommendation` objects.
- Includes tests for config, workflow, storage, geo prompts, and structured recommendations.

In progress / next:

- Run real OpenAI snapshots against the Houston personal-injury competitor list.
- Create a lighter one-page cold-email teaser report.
- Add real source/evidence collection for each firm.
- Add Perplexity, Claude, and Gemini adapters.
- Improve report sections for:
  - intent clusters
  - ZIP/neighborhood gaps
  - competitor reason summaries
  - recommended actions
- Build a small credibility website before larger outreach.

## Common Commands

List markets:

```bash
python3 -m ai_visibility.cli list-markets
```

Generate ZIP-specific prompts:

```bash
python3 -m ai_visibility.cli generate-prompts \
  --city Houston \
  --practice-area "personal injury" \
  --geo-scope zip \
  --zip-code 77002 \
  --limit 5
```

Run a cheap mock benchmark:

```bash
python3 -m ai_visibility.cli monthly-index \
  --engine mock \
  --db data/visibility.db \
  --city Houston \
  --practice-area "personal injury" \
  --business "The Ammons Law Firm, LLP" \
  --geo-scope city \
  --limit 12 \
  --out reports/houston-mock.md
```

Run an OpenAI snapshot:

```bash
export OPENAI_API_KEY="..."

PYTHONDONTWRITEBYTECODE=1 python3 -m ai_visibility.cli monthly-index \
  --engine openai \
  --db data/visibility.db \
  --city Houston \
  --practice-area "personal injury" \
  --business "The Ammons Law Firm, LLP" \
  --geo-scope city \
  --limit 12 \
  --force-refresh \
  --out reports/houston-openai-snapshot.md
```

Run tests:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests
```

## Conventions

- Keep the project dependency-light until there is a clear need.
- Do not commit generated runtime artifacts:
  - `data/`
  - `reports/`
  - `__pycache__/`
- Do not commit raw API keys or customer-sensitive data.
- Prefer small, testable modules over large framework code.
- Preserve the CLI-first workflow until the cold-email validation loop works.
- Treat free outreach reports as snapshots, not definitive market benchmarks.
- Use 10-15 prompts for cold-email snapshots.
- Reserve 50-150 prompts and multi-engine runs for paid/deeper audits.
- Keep model adapters behind `EngineClient`.
- Cache every paid model answer.
- When changing the candidate competitor list, ensure cache keys remain candidate-set aware.
- Prefer structured JSON/objects for model outputs over prose parsing.

## Product Notes

The cold-email wedge should not overclaim. Good language:

> We ran a controlled AI visibility snapshot for Houston personal injury attorneys and measured how often each firm appeared in recommendation-style answers.

Avoid claiming:

- guaranteed AI ranking improvement
- definitive market rank from a tiny prompt sample
- causal proof before evidence collection exists

The near-term validation question:

> Do law firms care enough to reply when shown a concrete AI recommendation visibility gap?
