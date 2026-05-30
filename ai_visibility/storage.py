from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from ai_visibility.data import City, PracticeArea
from ai_visibility.models import Business, BusinessScore, EngineAnswer, Recommendation


SCHEMA_VERSION = 1


@dataclass(frozen=True)
class StoredRun:
    id: int
    run_type: str
    market_id: int
    target_business_id: int
    created_at: str


class VisibilityStore:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")

    def close(self) -> None:
        self.connection.close()

    def init_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS markets (
                id INTEGER PRIMARY KEY,
                city TEXT NOT NULL,
                state TEXT NOT NULL,
                practice_area TEXT NOT NULL,
                practice_label TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(city, state, practice_area)
            );

            CREATE TABLE IF NOT EXISTS businesses (
                id INTEGER PRIMARY KEY,
                market_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                website TEXT,
                aliases_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                UNIQUE(market_id, name),
                FOREIGN KEY(market_id) REFERENCES markets(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS prompts (
                id INTEGER PRIMARY KEY,
                market_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                cluster TEXT NOT NULL DEFAULT 'general',
                geo_scope TEXT NOT NULL DEFAULT 'city',
                geo_label TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                UNIQUE(market_id, text),
                FOREIGN KEY(market_id) REFERENCES markets(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS engine_answers (
                id INTEGER PRIMARY KEY,
                market_id INTEGER NOT NULL,
                prompt_id INTEGER NOT NULL,
                engine TEXT NOT NULL,
                text TEXT NOT NULL,
                citations_json TEXT NOT NULL DEFAULT '[]',
                recommendations_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                UNIQUE(prompt_id, engine),
                FOREIGN KEY(market_id) REFERENCES markets(id) ON DELETE CASCADE,
                FOREIGN KEY(prompt_id) REFERENCES prompts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS engine_answer_cache (
                id INTEGER PRIMARY KEY,
                market_id INTEGER NOT NULL,
                prompt_id INTEGER NOT NULL,
                engine TEXT NOT NULL,
                candidate_signature TEXT NOT NULL,
                text TEXT NOT NULL,
                citations_json TEXT NOT NULL DEFAULT '[]',
                recommendations_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                UNIQUE(prompt_id, engine, candidate_signature),
                FOREIGN KEY(market_id) REFERENCES markets(id) ON DELETE CASCADE,
                FOREIGN KEY(prompt_id) REFERENCES prompts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY,
                run_type TEXT NOT NULL,
                market_id INTEGER NOT NULL,
                target_business_id INTEGER NOT NULL,
                engine TEXT NOT NULL,
                prompt_count INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(market_id) REFERENCES markets(id) ON DELETE CASCADE,
                FOREIGN KEY(target_business_id) REFERENCES businesses(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS business_scores (
                id INTEGER PRIMARY KEY,
                run_id INTEGER NOT NULL,
                business_id INTEGER NOT NULL,
                score REAL NOT NULL,
                mentions INTEGER NOT NULL,
                recommendations INTEGER NOT NULL,
                top_three_mentions INTEGER NOT NULL,
                citations_json TEXT NOT NULL DEFAULT '[]',
                reasons_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                UNIQUE(run_id, business_id),
                FOREIGN KEY(run_id) REFERENCES runs(id) ON DELETE CASCADE,
                FOREIGN KEY(business_id) REFERENCES businesses(id) ON DELETE CASCADE
            );
            """
        )
        self._ensure_prompt_geo_columns()
        self._ensure_answer_recommendation_columns()
        self.connection.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
            ("schema_version", str(SCHEMA_VERSION)),
        )
        self.connection.commit()

    def _ensure_prompt_geo_columns(self) -> None:
        columns = {
            str(row["name"])
            for row in self.connection.execute("PRAGMA table_info(prompts)").fetchall()
        }
        if "geo_scope" not in columns:
            self.connection.execute(
                "ALTER TABLE prompts ADD COLUMN geo_scope TEXT NOT NULL DEFAULT 'city'"
            )
        if "geo_label" not in columns:
            self.connection.execute(
                "ALTER TABLE prompts ADD COLUMN geo_label TEXT NOT NULL DEFAULT ''"
            )

    def _ensure_answer_recommendation_columns(self) -> None:
        for table in ("engine_answers", "engine_answer_cache"):
            columns = {
                str(row["name"])
                for row in self.connection.execute(f"PRAGMA table_info({table})").fetchall()
            }
            if "recommendations_json" not in columns:
                self.connection.execute(
                    f"ALTER TABLE {table} ADD COLUMN recommendations_json TEXT NOT NULL DEFAULT '[]'"
                )

    def get_or_create_market(self, city: City, area: PracticeArea) -> int:
        now = _now()
        self.connection.execute(
            """
            INSERT OR IGNORE INTO markets (city, state, practice_area, practice_label, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (city.name, city.state, area.slug, area.label, now),
        )
        self.connection.commit()
        row = self.connection.execute(
            """
            SELECT id FROM markets
            WHERE city = ? AND state = ? AND practice_area = ?
            """,
            (city.name, city.state, area.slug),
        ).fetchone()
        return int(row["id"])

    def upsert_businesses(self, market_id: int, businesses: list[Business]) -> dict[str, int]:
        now = _now()
        for business in businesses:
            self.connection.execute(
                """
                INSERT OR IGNORE INTO businesses
                    (market_id, name, website, aliases_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    market_id,
                    business.name,
                    business.website,
                    json.dumps(list(business.aliases)),
                    now,
                ),
            )
        self.connection.commit()
        rows = self.connection.execute(
            "SELECT id, name FROM businesses WHERE market_id = ?",
            (market_id,),
        ).fetchall()
        return {str(row["name"]): int(row["id"]) for row in rows}

    def upsert_prompts(self, market_id: int, prompts: list[str]) -> dict[str, int]:
        now = _now()
        for prompt in prompts:
            geo_scope, geo_label = _geo_for_prompt(prompt)
            self.connection.execute(
                """
                INSERT OR IGNORE INTO prompts
                    (market_id, text, cluster, geo_scope, geo_label, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (market_id, prompt, _cluster_for_prompt(prompt), geo_scope, geo_label, now),
            )
            self.connection.execute(
                """
                UPDATE prompts
                SET cluster = ?, geo_scope = ?, geo_label = ?
                WHERE market_id = ? AND text = ?
                """,
                (_cluster_for_prompt(prompt), geo_scope, geo_label, market_id, prompt),
            )
        self.connection.commit()
        rows = self.connection.execute(
            "SELECT id, text FROM prompts WHERE market_id = ?",
            (market_id,),
        ).fetchall()
        return {str(row["text"]): int(row["id"]) for row in rows}

    def cached_answer(
        self,
        prompt_id: int,
        engine: str,
        candidate_signature: str = "",
    ) -> EngineAnswer | None:
        row = self.connection.execute(
            """
            SELECT
                p.text AS prompt,
                a.engine,
                a.text,
                a.citations_json,
                a.recommendations_json
            FROM engine_answer_cache a
            JOIN prompts p ON p.id = a.prompt_id
            WHERE a.prompt_id = ? AND a.engine = ? AND a.candidate_signature = ?
            """,
            (prompt_id, engine, candidate_signature),
        ).fetchone()
        if row is None:
            return None
        return EngineAnswer(
            engine=str(row["engine"]),
            prompt=str(row["prompt"]),
            text=str(row["text"]),
            citations=tuple(json.loads(str(row["citations_json"]))),
            recommendations=_recommendations_from_json(str(row["recommendations_json"])),
        )

    def save_answer(
        self,
        market_id: int,
        prompt_id: int,
        answer: EngineAnswer,
        candidate_signature: str = "",
    ) -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO engine_answer_cache
                (
                    market_id,
                    prompt_id,
                    engine,
                    candidate_signature,
                    text,
                    citations_json,
                    recommendations_json,
                    created_at
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                market_id,
                prompt_id,
                answer.engine,
                candidate_signature,
                answer.text,
                json.dumps(list(answer.citations)),
                _recommendations_to_json(answer.recommendations),
                _now(),
            ),
        )
        self.connection.commit()

    def create_run(
        self,
        run_type: str,
        market_id: int,
        target_business_id: int,
        engine: str,
        prompt_count: int,
    ) -> StoredRun:
        created_at = _now()
        cursor = self.connection.execute(
            """
            INSERT INTO runs
                (run_type, market_id, target_business_id, engine, prompt_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (run_type, market_id, target_business_id, engine, prompt_count, created_at),
        )
        self.connection.commit()
        return StoredRun(
            id=int(cursor.lastrowid),
            run_type=run_type,
            market_id=market_id,
            target_business_id=target_business_id,
            created_at=created_at,
        )

    def save_scores(
        self,
        run_id: int,
        business_ids: dict[str, int],
        scores: list[BusinessScore],
        total_prompts: int,
    ) -> None:
        now = _now()
        for score in scores:
            business_id = business_ids[score.business.name]
            self.connection.execute(
                """
                INSERT OR REPLACE INTO business_scores
                    (
                        run_id,
                        business_id,
                        score,
                        mentions,
                        recommendations,
                        top_three_mentions,
                        citations_json,
                        reasons_json,
                        created_at
                    )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    business_id,
                    score.visibility_score(total_prompts),
                    score.mentions,
                    score.recommendations,
                    score.top_three_mentions,
                    json.dumps(sorted(score.citations)),
                    json.dumps(score.reasons),
                    now,
                ),
            )
        self.connection.commit()

    def answer_count(self) -> int:
        row = self.connection.execute("SELECT COUNT(*) AS count FROM engine_answer_cache").fetchone()
        return int(row["count"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _cluster_for_prompt(prompt: str) -> str:
    lowered = prompt.lower()
    for marker in ("car accident", "truck accident", "slip and fall", "custody", "green card", "visa"):
        if marker in lowered:
            return marker
    if "review" in lowered:
        return "reviews"
    if "consultation" in lowered:
        return "consultation"
    return "general"


def _geo_for_prompt(prompt: str) -> tuple[str, str]:
    lowered = prompt.lower()
    marker = "zip code "
    if marker in lowered:
        start = lowered.index(marker) + len(marker)
        return "zip", prompt[start : start + 5]
    neighborhood_markers = (
        "downtown",
        "heights",
        "galleria",
        "uptown",
        "koreatown",
        "west los angeles",
        "loop",
        "lincoln park",
        "arcadia",
        "ahwatukee",
        "brooklyn",
        "queens",
        "manhattan",
    )
    for marker_value in neighborhood_markers:
        if marker_value in lowered:
            return "neighborhood", marker_value
    return "city", ""


def _recommendations_to_json(recommendations: tuple[Recommendation, ...]) -> str:
    return json.dumps(
        [
            {
                "rank": item.rank,
                "business_name": item.business_name,
                "reason": item.reason,
                "confidence": item.confidence,
            }
            for item in recommendations
        ]
    )


def _recommendations_from_json(value: str) -> tuple[Recommendation, ...]:
    try:
        raw = json.loads(value)
    except json.JSONDecodeError:
        return ()
    if not isinstance(raw, list):
        return ()
    items: list[Recommendation] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        business_name = item.get("business_name")
        reason = item.get("reason")
        if not isinstance(business_name, str) or not isinstance(reason, str):
            continue
        items.append(
            Recommendation(
                rank=int(item.get("rank", len(items) + 1)),
                business_name=business_name,
                reason=reason,
                confidence=str(item.get("confidence", "medium")),
            )
        )
    return tuple(items)
