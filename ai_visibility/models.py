from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Business:
    name: str
    website: str | None = None
    aliases: tuple[str, ...] = ()

    @property
    def match_terms(self) -> tuple[str, ...]:
        return (self.name, *self.aliases)


@dataclass(frozen=True)
class Recommendation:
    rank: int
    business_name: str
    reason: str
    confidence: str = "medium"


@dataclass(frozen=True)
class EngineAnswer:
    engine: str
    prompt: str
    text: str
    citations: tuple[str, ...] = ()
    recommendations: tuple[Recommendation, ...] = ()


@dataclass
class BusinessScore:
    business: Business
    mentions: int = 0
    recommendations: int = 0
    top_three_mentions: int = 0
    citations: set[str] = field(default_factory=set)
    reasons: list[str] = field(default_factory=list)

    def visibility_score(self, total_prompts: int) -> float:
        if total_prompts == 0:
            return 0.0
        mention_rate = self.mentions / total_prompts
        recommendation_rate = self.recommendations / total_prompts
        top_three_rate = self.top_three_mentions / total_prompts
        citation_rate = min(len(self.citations), total_prompts) / total_prompts
        return round(
            100
            * (
                0.35 * mention_rate
                + 0.30 * recommendation_rate
                + 0.20 * top_three_rate
                + 0.15 * citation_rate
            ),
            1,
        )
