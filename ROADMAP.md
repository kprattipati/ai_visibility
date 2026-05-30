# Build Roadmap

## Phase 1: Sellable Manual Audit

Goal: produce credible AI visibility reports for one legal market at a time.

Build:

- Prompt library for legal practice areas.
- Competitor universe builder.
- Multi-run benchmark runner.
- Markdown/PDF report output.
- Manual evidence review checklist.

Use the mock engine for workflow testing, then plug in real engines one by one.

Recommended first paid pilot:

- Practice area: personal injury attorneys.
- Cities: Houston, Phoenix, Chicago, Los Angeles, New York.
- Prompt count: 75-150 per city.
- Output: audit report plus 30-day retest.

## Phase 2: Real Engine Adapters

Add compliant clients behind `EngineClient`:

- Gemini / Google AI surfaces where available.
- ChatGPT / OpenAI API.
- Perplexity or another answer engine with citations.

Store raw answers and citations so results can be audited later.

## Phase 3: Evidence Graph

Collect evidence for each firm:

- Website pages.
- Google Business Profile facts.
- Review themes.
- Legal directories such as Avvo, Justia, FindLaw, Super Lawyers, and Martindale-Hubbell.
- State bar profile.
- Local press and awards.
- Structured data.

Turn those signals into a gap analysis against the firms that are most often recommended.

## Phase 4: Customer Product

Only after the audit motion works:

- Customer dashboard.
- Monthly tracking.
- Competitor alerts.
- Evidence recommendations.
- Agency-facing exports.
- Retest workflow after changes are implemented.

## Key Metrics

- Recommendation Rate: share of prompts where the firm is actively recommended.
- Top-3 Rate: share of prompts where the firm appears in the first three recommendations.
- Citation Strength: how often the firm is backed by trustworthy sources.
- Intent Coverage: which customer needs trigger mentions.
- Competitor Gap: distance from the leading firm in the same city/practice area.
