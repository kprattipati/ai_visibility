import tempfile
import unittest
from pathlib import Path

from ai_visibility.data import get_city, get_practice_area
from ai_visibility.models import Business, EngineAnswer, Recommendation
from ai_visibility.scoring import score_answers
from ai_visibility.storage import VisibilityStore


class StructuredRecommendationTest(unittest.TestCase):
    def test_scoring_uses_structured_reasons(self) -> None:
        businesses = [Business("Alpha Law"), Business("Beta Law")]
        answer = EngineAnswer(
            engine="test",
            prompt="Who should I hire?",
            text='{"recommendations":[]}',
            recommendations=(
                Recommendation(1, "Beta Law", "strong local proof", "medium"),
                Recommendation(2, "Alpha Law", "clear practice pages", "medium"),
            ),
        )

        scores = score_answers(businesses, [answer])
        beta = next(score for score in scores if score.business.name == "Beta Law")
        alpha = next(score for score in scores if score.business.name == "Alpha Law")

        self.assertEqual(beta.top_three_mentions, 1)
        self.assertIn("strong local proof", beta.reasons)
        self.assertIn("clear practice pages", alpha.reasons)

    def test_storage_round_trips_structured_recommendations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = VisibilityStore(Path(tmp) / "visibility.db")
            try:
                city = get_city("Houston")
                area = get_practice_area("personal injury")
                store.init_schema()
                market_id = store.get_or_create_market(city, area)
                prompt_ids = store.upsert_prompts(market_id, ["Who should I hire?"])
                answer = EngineAnswer(
                    engine="test",
                    prompt="Who should I hire?",
                    text='{"recommendations":[]}',
                    recommendations=(
                        Recommendation(1, "Beta Law", "strong local proof", "medium"),
                    ),
                )
                store.save_answer(market_id, prompt_ids["Who should I hire?"], answer, "abc")
                cached = store.cached_answer(prompt_ids["Who should I hire?"], "test", "abc")
            finally:
                store.close()

            self.assertIsNotNone(cached)
            self.assertEqual(cached.recommendations[0].business_name, "Beta Law")
            self.assertEqual(cached.recommendations[0].reason, "strong local proof")


if __name__ == "__main__":
    unittest.main()
