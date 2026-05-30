import unittest

from ai_visibility.data import get_city, get_practice_area
from ai_visibility.engines import MockEngineClient
from ai_visibility.prompts import generate_prompts
from ai_visibility.reports import build_markdown_report
from ai_visibility.scoring import score_answers
from ai_visibility.seeds import sample_businesses


class WorkflowTest(unittest.TestCase):
    def test_audit_workflow_generates_target_report(self) -> None:
        city = get_city("Houston")
        area = get_practice_area("personal injury")
        prompts = generate_prompts(city, area, limit=8)
        businesses = sample_businesses(city.name, area.slug, "Example Injury Law")
        engine = MockEngineClient()

        answers = [engine.ask(prompt, businesses) for prompt in prompts]
        scores = score_answers(businesses, answers)
        report = build_markdown_report(
            city=city,
            area=area,
            target_business="Example Injury Law",
            answers=answers,
            scores=scores,
        )

        self.assertIn("AI Visibility Audit: Example Injury Law", report)
        self.assertIn("Personal Injury Attorney in Houston, TX", report)
        self.assertIn("Leaderboard", report)
        self.assertTrue(any(score.business.name == "Example Injury Law" for score in scores))


if __name__ == "__main__":
    unittest.main()
