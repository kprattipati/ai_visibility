from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_PATH = Path("config/providers.json")


@dataclass(frozen=True)
class EngineSettings:
    name: str
    provider: str
    enabled: bool
    api_key_env: str | None = None
    model: str | None = None


@dataclass(frozen=True)
class ProviderConfig:
    default_engine: str
    engines: dict[str, EngineSettings]

    def engine(self, name: str | None = None) -> EngineSettings:
        engine_name = name or self.default_engine
        try:
            settings = self.engines[engine_name]
        except KeyError as exc:
            choices = ", ".join(sorted(self.engines))
            raise ValueError(f"Unknown engine '{engine_name}'. Available engines: {choices}") from exc
        if not settings.enabled:
            raise ValueError(f"Engine '{engine_name}' is disabled in the provider config.")
        return settings


def load_provider_config(path: str | Path | None = None) -> ProviderConfig:
    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    engines = {
        name: _engine_settings(name, value)
        for name, value in raw.get("engines", {}).items()
    }
    if not engines:
        raise ValueError(f"No engines configured in {config_path}")
    return ProviderConfig(
        default_engine=raw.get("default_engine", "mock"),
        engines=engines,
    )


def _engine_settings(name: str, value: dict[str, Any]) -> EngineSettings:
    return EngineSettings(
        name=name,
        provider=value["provider"],
        enabled=bool(value.get("enabled", False)),
        api_key_env=value.get("api_key_env"),
        model=value.get("model"),
    )
