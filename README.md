# AI Recommendation Visibility MVP

This is a lightweight prototype for benchmarking whether AI/search assistants recommend a business against competitors in a local legal market.

The first wedge is **AI visibility benchmarking for law firms**, focused on:

- Personal injury attorneys
- Divorce / family law attorneys
- Immigration attorneys

across the five largest U.S. cities by 2025 Census estimate:

- New York, NY
- Los Angeles, CA
- Chicago, IL
- Houston, TX
- Phoenix, AZ

## What It Does

The MVP can:

1. Seed city/category markets.
2. Generate realistic high-intent buyer prompts.
3. Run a benchmark using a mock engine.
4. Extract business mentions from model answers.
5. Score recommendation visibility.
6. Generate a Markdown audit report.

The mock engine lets you test the full workflow without paying for model tokens. Real model integrations can be added behind the `EngineClient` interface.

## Quick Start

```bash
python3 -m ai_visibility.cli list-markets
python3 -m ai_visibility.cli generate-prompts --city "Houston" --practice-area "personal injury"
python3 -m ai_visibility.cli run-audit --city "Houston" --practice-area "personal injury" --business "Example Injury Law" --out reports/houston-personal-injury.md
```

Generate neighborhood or ZIP-targeted prompts:

```bash
python3 -m ai_visibility.cli generate-prompts \
  --city "Houston" \
  --practice-area "personal injury" \
  --geo-scope zip \
  --zip-code 77002 \
  --limit 5
```

## Cached Runs

Use SQLite to save prompt answers, scores, and run history:

```bash
python3 -m ai_visibility.cli init-db --db data/visibility.db

python3 -m ai_visibility.cli monthly-index \
  --db data/visibility.db \
  --city "Houston" \
  --practice-area "personal injury" \
  --business "Example Injury Law" \
  --out reports/houston-monthly-index.md

python3 -m ai_visibility.cli customer-check \
  --db data/visibility.db \
  --city "Houston" \
  --practice-area "personal injury" \
  --business "Example Injury Law" \
  --out reports/houston-customer-check.md
```

By default, `monthly-index` uses a sample of citywide, neighborhood, and ZIP-targeted prompts. `customer-check` defaults to citywide prompts unless you pass `--geo-scope neighborhood` or `--geo-scope zip`.

Stored runs reuse saved answers for the same market, prompt, and engine. Add `--force-refresh` when you intentionally want to overwrite cached answers.

Examples:

```bash
python3 -m ai_visibility.cli customer-check \
  --db data/visibility.db \
  --city "Houston" \
  --practice-area "personal injury" \
  --business "Example Injury Law" \
  --geo-scope zip \
  --zip-code 77002 \
  --out reports/houston-77002-check.md
```

## Engine Config

Provider settings live in:

```text
config/providers.json
```

The app uses `mock` by default. To run OpenAI, set your API key and choose the OpenAI engine:

```bash
export OPENAI_API_KEY="your-key"

python3 -m ai_visibility.cli monthly-index \
  --engine openai \
  --config config/providers.json \
  --db data/visibility.db \
  --city "Houston" \
  --practice-area "personal injury" \
  --business "Example Injury Law" \
  --limit 12 \
  --out reports/houston-openai-index.md
```

Perplexity, Claude, and Gemini are included as disabled config placeholders so their adapters can be added later without changing the benchmark pipeline.

## Product Direction

The customer-facing promise should be:

> See how often AI systems recommend your law firm, which competitors they trust more, and what evidence you need to earn inclusion.

The next major step is replacing the mock engine with live adapters for Gemini, ChatGPT, Perplexity, and Google AI surfaces where compliant access is available.
