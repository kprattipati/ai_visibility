from __future__ import annotations

import re

from ai_visibility.models import Business, BusinessScore, EngineAnswer


RECOMMENDATION_WORDS = ("recommend", "consider", "compare", "reputable", "trusted", "known for")


def score_answers(businesses: list[Business], answers: list[EngineAnswer]) -> list[BusinessScore]:
    scores = {business.name: BusinessScore(business=business) for business in businesses}
    for answer in answers:
        if answer.recommendations:
            _score_structured_answer(scores, businesses, answer)
            continue
        lower_text = answer.text.lower()
        top_three_text = "\n".join(answer.text.splitlines()[:4]).lower()
        for business in businesses:
            if _contains_business(answer.text, business):
                score = scores[business.name]
                score.mentions += 1
                if any(word in lower_text for word in RECOMMENDATION_WORDS):
                    score.recommendations += 1
                if _contains_business(top_three_text, business):
                    score.top_three_mentions += 1
                for citation in answer.citations:
                    if _slug(business.name) in citation:
                        score.citations.add(citation)
                reason = _extract_reason(answer.text, business)
                if reason:
                    score.reasons.append(reason)
    return sorted(
        scores.values(),
        key=lambda score: score.visibility_score(len(answers)),
        reverse=True,
    )


def _score_structured_answer(
    scores: dict[str, BusinessScore],
    businesses: list[Business],
    answer: EngineAnswer,
) -> None:
    for recommendation in answer.recommendations:
        business = _find_business(businesses, recommendation.business_name)
        if business is None:
            continue
        score = scores[business.name]
        score.mentions += 1
        score.recommendations += 1
        if recommendation.rank <= 3:
            score.top_three_mentions += 1
        if recommendation.reason:
            score.reasons.append(recommendation.reason)
        for citation in answer.citations:
            if _slug(business.name) in citation:
                score.citations.add(citation)


def _contains_business(text: str, business: Business) -> bool:
    for term in business.match_terms:
        pattern = r"\b" + re.escape(term.lower()) + r"\b"
        if re.search(pattern, text.lower()):
            return True
    return False


def _find_business(businesses: list[Business], name: str) -> Business | None:
    for business in businesses:
        if _contains_business(name, business) or _contains_business(business.name, Business(name)):
            return business
    return None


def _extract_reason(text: str, business: Business) -> str | None:
    for line in text.splitlines():
        if _contains_business(line, business) and " - " in line:
            return line.split(" - ", 1)[1].strip()
    return None


def _slug(value: str) -> str:
    return value.lower().replace(" ", "-")
