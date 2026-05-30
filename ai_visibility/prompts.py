from __future__ import annotations

from ai_visibility.data import City, PracticeArea
from ai_visibility.geo import GeoScope, city_scope


PROMPT_TEMPLATES: tuple[str, ...] = (
    "Who are the best {practice} lawyers in {city}?",
    "Recommend a {practice} attorney in {city} for a {need} case.",
    "Which {city} law firms are known for {need} matters?",
    "What {practice} lawyers in {city} have strong reviews?",
    "I need a trusted {practice} attorney near {city}. Who should I consider?",
    "Compare the top {practice} law firms in {city}.",
    "Which {practice} attorneys in {city} offer a clear consultation process?",
    "Who is a good {practice} lawyer in {city} for someone who wants practical guidance?",
    "What are the most reputable {practice} attorneys serving {city}?",
    "Which local {practice} law firms in {city} are commonly recommended?",
)


def generate_prompts(
    city: City,
    area: PracticeArea,
    limit: int | None = None,
    geo_scopes: list[GeoScope] | None = None,
) -> list[str]:
    prompts: list[str] = []
    scopes = geo_scopes or [city_scope(city)]
    for scope in scopes:
        for template in PROMPT_TEMPLATES:
            if "{need}" in template:
                for need in area.customer_language[:4]:
                    prompts.append(
                        template.format(
                            practice=area.slug,
                            city=scope.query_text,
                            need=need,
                        )
                    )
            else:
                prompts.append(
                    template.format(
                        practice=area.slug,
                        city=scope.query_text,
                    )
                )
    return prompts[:limit] if limit else prompts
