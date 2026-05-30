import tempfile
import unittest
from pathlib import Path

from ai_visibility.cli import _run_with_storage
from ai_visibility.data import get_city, get_practice_area
from ai_visibility.prompts import generate_prompts
from ai_visibility.seeds import sample_businesses
from ai_visibility.storage import VisibilityStore


class StorageTest(unittest.TestCase):
    def test_second_run_reuses_cached_answers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "visibility.db"
            city = get_city("Houston")
            area = get_practice_area("personal injury")
            prompts = generate_prompts(city, area, limit=5)
            businesses = sample_businesses(city.name, area.slug, "Example Injury Law")

            _run_with_storage(
                db_path=str(db_path),
                run_type="test",
                city=city,
                area=area,
                target_business="Example Injury Law",
                prompts=prompts,
                businesses=businesses,
                force_refresh=False,
            )
            first_store = VisibilityStore(db_path)
            try:
                first_count = first_store.answer_count()
            finally:
                first_store.close()

            _run_with_storage(
                db_path=str(db_path),
                run_type="test",
                city=city,
                area=area,
                target_business="Example Injury Law",
                prompts=prompts,
                businesses=businesses,
                force_refresh=False,
            )
            second_store = VisibilityStore(db_path)
            try:
                second_count = second_store.answer_count()
            finally:
                second_store.close()

            self.assertEqual(first_count, 5)
            self.assertEqual(second_count, first_count)


if __name__ == "__main__":
    unittest.main()
