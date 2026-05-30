from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from abc import ABC, abstractmethod

from ai_visibility.config import EngineSettings, load_provider_config
from ai_visibility.models import Business, EngineAnswer, Recommendation


class EngineClient(ABC):
    name: str

    @abstractmethod
    def ask(self, prompt: str, businesses: list[Business]) -> EngineAnswer:
        """Return an engine answer for one recommendation prompt."""


class MockEngineClient(EngineClient):
    name = "mock-llm"

    def ask(self, prompt: str, businesses: list[Business]) -> EngineAnswer:
        ranked = sorted(
            businesses,
            key=lambda business: _stable_rank(prompt, business.name),
            reverse=True,
        )
        chosen = ranked[:5]
        lines = [
            "Here are local firms I would compare based on visible reputation, specificity, and third-party proof:"
        ]
        recommendations: list[Recommendation] = []
        for index, business in enumerate(chosen, start=1):
            reason = _reason_for(prompt, business.name)
            lines.append(f"{index}. {business.name} - {reason}")
            recommendations.append(
                Recommendation(
                    rank=index,
                    business_name=business.name,
                    reason=reason,
                    confidence="medium",
                )
            )
        citations = tuple(
            f"https://example.com/evidence/{business.name.lower().replace(' ', '-')}"
            for business in chosen[:3]
        )
        return EngineAnswer(
            engine=self.name,
            prompt=prompt,
            text="\n".join(lines),
            citations=citations,
            recommendations=tuple(recommendations),
        )


class OpenAIEngineClient(EngineClient):
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://api.openai.com/v1/responses",
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.name = f"openai:{model}"

    def ask(self, prompt: str, businesses: list[Business]) -> EngineAnswer:
        business_list = "\n".join(f"- {business.name}" for business in businesses)
        payload = {
            "model": self.model,
            "instructions": (
                "You benchmark local law-firm recommendation visibility. "
                "Answer as a cautious consumer recommendation assistant. "
                "Only recommend firms from the provided candidate list. "
                "Rank up to 10 firms. For each firm, include a short reason tied to visible trust signals. "
                "Do not invent case results, credentials, reviews, or citations. "
                "Return only valid JSON. Do not wrap it in Markdown."
            ),
            "input": (
                f"User prompt:\n{prompt}\n\n"
                f"Candidate firms:\n{business_list}\n\n"
                "Return this JSON shape exactly: "
                "{"
                "\"recommendations\":["
                "{"
                "\"rank\":1,"
                "\"business_name\":\"Firm name from candidate list\","
                "\"reason\":\"Brief reason based only on visible/general trust signals\","
                "\"confidence\":\"low|medium|high\""
                "}"
                "]"
                "}"
            ),
        }
        request = urllib.request.Request(
            self.base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI request failed: HTTP {exc.code}: {detail}") from exc
        text = _response_text(body)
        recommendations = _parse_recommendations(text)
        return EngineAnswer(
            engine=self.name,
            prompt=prompt,
            text=text,
            citations=(),
            recommendations=tuple(recommendations),
        )


class UnsupportedEngineClient(EngineClient):
    def __init__(self, settings: EngineSettings) -> None:
        self.settings = settings
        self.name = f"{settings.provider}:{settings.model or settings.name}"

    def ask(self, prompt: str, businesses: list[Business]) -> EngineAnswer:
        raise NotImplementedError(
            f"Provider '{self.settings.provider}' is configured but not implemented yet."
        )


def build_engine_client(
    engine_name: str | None = None,
    config_path: str | None = None,
) -> EngineClient:
    config = load_provider_config(config_path)
    settings = config.engine(engine_name)
    if settings.provider == "mock":
        return MockEngineClient()
    if settings.provider == "openai":
        if not settings.api_key_env:
            raise ValueError("OpenAI engine requires api_key_env in provider config.")
        api_key = os.environ.get(settings.api_key_env)
        if not api_key:
            raise ValueError(
                f"Set {settings.api_key_env} before running the OpenAI engine."
            )
        if not settings.model:
            raise ValueError("OpenAI engine requires a model in provider config.")
        return OpenAIEngineClient(api_key=api_key, model=settings.model)
    return UnsupportedEngineClient(settings)


def _stable_rank(prompt: str, business_name: str) -> int:
    digest = hashlib.sha256(f"{prompt}|{business_name}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def _reason_for(prompt: str, business_name: str) -> str:
    options = (
        "strong review footprint and clear practice-area pages",
        "specific local content and visible attorney credentials",
        "directory presence plus evidence of relevant case experience",
        "clear consultation language and consistent business information",
        "third-party mentions that make the firm easier to verify",
    )
    index = _stable_rank(prompt, business_name) % len(options)
    return options[index]


def _response_text(body: dict) -> str:
    if isinstance(body.get("output_text"), str):
        return body["output_text"]
    parts: list[str] = []
    for item in body.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if isinstance(text, str):
                parts.append(text)
    if parts:
        return "\n".join(parts)
    return json.dumps(body, indent=2)


def _parse_recommendations(text: str) -> list[Recommendation]:
    try:
        payload = json.loads(_strip_json_fence(text))
    except json.JSONDecodeError:
        return []
    recommendations = payload.get("recommendations", [])
    if not isinstance(recommendations, list):
        return []
    parsed: list[Recommendation] = []
    for item in recommendations:
        if not isinstance(item, dict):
            continue
        business_name = item.get("business_name")
        reason = item.get("reason")
        if not isinstance(business_name, str) or not isinstance(reason, str):
            continue
        parsed.append(
            Recommendation(
                rank=_safe_rank(item.get("rank"), len(parsed) + 1),
                business_name=business_name,
                reason=reason,
                confidence=str(item.get("confidence", "medium")),
            )
        )
    return parsed


def _strip_json_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```json"):
        stripped = stripped.removeprefix("```json").strip()
    elif stripped.startswith("```"):
        stripped = stripped.removeprefix("```").strip()
    if stripped.endswith("```"):
        stripped = stripped.removesuffix("```").strip()
    return stripped


def _safe_rank(value, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback
