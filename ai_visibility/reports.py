from __future__ import annotations

from collections import Counter
from datetime import date

from ai_visibility.data import City, PracticeArea
from ai_visibility.models import BusinessScore, EngineAnswer


def build_markdown_report(
    city: City,
    area: PracticeArea,
    target_business: str,
    answers: list[EngineAnswer],
    scores: list[BusinessScore],
) -> str:
    total_prompts = len(answers)
    target = next((score for score in scores if score.business.name == target_business), None)
    if target is None:
        raise ValueError(f"Target business was not included in benchmark: {target_business}")

    top = scores[0] if scores else target
    reason_counts = Counter(reason for score in scores[:5] for reason in score.reasons)
    missing_signals = _missing_signal_recommendations(area, target, top)

    lines = [
        f"# AI Visibility Audit: {target_business}",
        "",
        f"**Market:** {area.label} in {city.name}, {city.state}",
        f"**Generated:** {date.today().isoformat()}",
        f"**Prompts tested:** {total_prompts}",
        f"**Engines:** {', '.join(sorted({answer.engine for answer in answers}))}",
        "",
        "## Executive Summary",
        "",
        f"{target_business} scored **{target.visibility_score(total_prompts)}/100** for AI recommendation visibility in this market.",
        f"The leading benchmark firm scored **{top.visibility_score(total_prompts)}/100**.",
        "",
        "## Leaderboard",
        "",
        "| Rank | Business | Score | Mentions | Recommendations | Top-3 Mentions |",
        "|---:|---|---:|---:|---:|---:|",
    ]

    for rank, score in enumerate(scores, start=1):
        lines.append(
            "| {rank} | {business} | {score} | {mentions} | {recommendations} | {top_three} |".format(
                rank=rank,
                business=score.business.name,
                score=score.visibility_score(total_prompts),
                mentions=score.mentions,
                recommendations=score.recommendations,
                top_three=score.top_three_mentions,
            )
        )

    lines.extend(
        [
            "",
            "## Why Competitors Are Being Recommended",
            "",
        ]
    )
    if reason_counts:
        for reason, count in reason_counts.most_common(5):
            lines.append(f"- {reason} ({count} observed mentions)")
    else:
        lines.append("- No recommendation reasons were extracted.")

    lines.extend(
        [
            "",
            "## Priority Actions",
            "",
        ]
    )
    for action in missing_signals:
        lines.append(f"- {action}")

    lines.extend(
        [
            "",
            "## Sample Prompts",
            "",
        ]
    )
    for answer in answers[:5]:
        lines.append(f"- {answer.prompt}")

    return "\n".join(lines) + "\n"


def _missing_signal_recommendations(
    area: PracticeArea,
    target: BusinessScore,
    top: BusinessScore,
) -> list[str]:
    actions = [
        f"Build or strengthen pages that explicitly cover: {', '.join(area.customer_language[:4])}.",
        "Make attorney credentials, consultation process, and location served easy for AI systems to verify.",
        "Improve third-party evidence on legal directories and authoritative local sources.",
        "Ask satisfied clients for specific review language tied to the actual practice area, where ethically permitted.",
        "Add structured data for LegalService, LocalBusiness, reviews, attorneys, and service areas.",
    ]
    if target.mentions < top.mentions:
        actions.insert(0, "Close the recommendation gap by matching the evidence patterns visible on top competitor profiles.")
    for signal in area.evidence_signals[:3]:
        actions.append(f"Audit whether your firm has credible evidence for: {signal}.")
    return actions
