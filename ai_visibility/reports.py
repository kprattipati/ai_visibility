from __future__ import annotations

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
    rank = scores.index(target) + 1
    total_firms = len(scores)

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
        f"{target_business} ranked **#{rank} of {total_firms}** firms tested, "
        f"scoring **{target.visibility_score(total_prompts)}/100** for AI recommendation visibility.",
        f"The leading firm scored **{top.visibility_score(total_prompts)}/100** "
        f"and appeared in the top 3 results on **{top.top_three_mentions}/{total_prompts}** prompts.",
        "",
        "## Leaderboard",
        "",
        "| Rank | Business | Score | Mentions | Recommendations | Top-3 Mentions |",
        "|---:|---|---:|---:|---:|---:|",
    ]

    for r, score in enumerate(scores, start=1):
        lines.append(
            "| {rank} | {business} | {score} | {mentions} | {recommendations} | {top_three} |".format(
                rank=r,
                business=score.business.name,
                score=score.visibility_score(total_prompts),
                mentions=score.mentions,
                recommendations=score.recommendations,
                top_three=score.top_three_mentions,
            )
        )

    lines.extend(["", "## Priority Actions", ""])
    for action in _priority_actions(area, target, top, rank, total_firms, total_prompts):
        lines.append(f"- {action}")

    return "\n".join(lines) + "\n"


def _priority_actions(
    area: PracticeArea,
    target: BusinessScore,
    top: BusinessScore,
    rank: int,
    total_firms: int,
    total_prompts: int,
) -> list[str]:
    actions: list[str] = []
    score = target.visibility_score(total_prompts)
    top_score = top.visibility_score(total_prompts)
    gap = round(top_score - score, 1)

    if score == 0:
        actions.append(
            "Your firm did not appear in any AI recommendation results tested. "
            "The most likely cause is low authority signals — AI systems cannot confidently surface firms "
            "without visible credentials, reviews, or directory presence."
        )
        actions.append(
            f"Priority: establish a clear, indexable presence for {', '.join(area.customer_language[:3])} "
            "before competitors widen this gap further."
        )
    elif rank == 1:
        actions.append(
            f"Your firm leads this market with a {score}/100 score. "
            "Focus on maintaining top-3 placement consistency across prompt types."
        )
    else:
        actions.append(
            f"You are {gap} points behind the market leader (#{1}) and ranked #{rank} of {total_firms}. "
            "The gap is driven primarily by top-3 placement frequency — you are being mentioned but not ranked first."
        )

    if target.top_three_mentions < top.top_three_mentions:
        top3_gap = top.top_three_mentions - target.top_three_mentions
        actions.append(
            f"Top-3 placement gap: the leading firm appeared in the top 3 on {top.top_three_mentions}/{total_prompts} prompts; "
            f"you appeared on {target.top_three_mentions}/{total_prompts}. "
            "Closing this requires stronger trust signals that AI systems weight for position, not just inclusion."
        )

    actions.append(
        f"Build or strengthen content explicitly covering: {', '.join(area.customer_language[:4])}. "
        "These map directly to the prompt types AI systems use when answering recommendation queries."
    )

    for signal in area.evidence_signals[:3]:
        actions.append(f"Verify your firm has visible, third-party-confirmable evidence for: {signal}.")

    actions.append(
        "Make attorney credentials, bar admissions, and service areas easy for AI crawlers to parse — "
        "structured data (LegalService, LocalBusiness schema) accelerates this."
    )

    return actions
