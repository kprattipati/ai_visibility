import tempfile
import unittest
from pathlib import Path

from ai_visibility.data import get_city, get_practice_area
from ai_visibility.geo import scopes_for
from ai_visibility.prompts import generate_prompts
from ai_visibility.storage import VisibilityStore


class GeoPromptTest(unittest.TestCase):
    def test_zip_prompt_generation(self) -> None:
        city = get_city("Houston")
        area = get_practice_area("personal injury")
        scopes = scopes_for(city, "zip", zip_codes=["77002"])

        prompts = generate_prompts(city, area, limit=3, geo_scopes=scopes)

        self.assertTrue(all("77002" in prompt for prompt in prompts))

    def test_sample_prompt_generation_includes_city_and_local_prompts(self) -> None:
        city = get_city("Houston")
        area = get_practice_area("personal injury")
        scopes = scopes_for(city, "sample")

        prompts = generate_prompts(city, area, limit=90, geo_scopes=scopes)

        self.assertTrue(any("Houston, TX" in prompt for prompt in prompts))
        self.assertTrue(any("77002" in prompt for prompt in prompts))
        self.assertTrue(any("Heights" in prompt for prompt in prompts))

    def test_storage_records_prompt_geo_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "visibility.db"
            store = VisibilityStore(db_path)
            try:
                city = get_city("Houston")
                area = get_practice_area("personal injury")
                store.init_schema()
                market_id = store.get_or_create_market(city, area)
                store.upsert_prompts(
                    market_id,
                    ["Who are the best personal injury lawyers near ZIP code 77002 in Houston, TX?"],
                )
                row = store.connection.execute(
                    "SELECT geo_scope, geo_label FROM prompts LIMIT 1"
                ).fetchone()
            finally:
                store.close()

            self.assertEqual(row["geo_scope"], "zip")
            self.assertEqual(row["geo_label"], "77002")


if __name__ == "__main__":
    unittest.main()
