import tempfile
import unittest
from pathlib import Path

from ai_visibility.config import load_provider_config
from ai_visibility.engines import MockEngineClient, build_engine_client


class ConfigTest(unittest.TestCase):
    def test_loads_mock_engine_from_config(self) -> None:
        config = load_provider_config("config/providers.json")

        self.assertEqual(config.default_engine, "mock")
        self.assertEqual(config.engine("mock").provider, "mock")

    def test_builds_mock_engine(self) -> None:
        engine = build_engine_client("mock", "config/providers.json")

        self.assertIsInstance(engine, MockEngineClient)

    def test_disabled_provider_fails_fast(self) -> None:
        with self.assertRaisesRegex(ValueError, "disabled"):
            build_engine_client("gemini", "config/providers.json")

    def test_config_can_be_copied_and_changed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "providers.json"
            path.write_text(
                """
                {
                  "default_engine": "mock",
                  "engines": {
                    "mock": {"provider": "mock", "enabled": true}
                  }
                }
                """,
                encoding="utf-8",
            )

            config = load_provider_config(path)

            self.assertEqual(config.engine().provider, "mock")


if __name__ == "__main__":
    unittest.main()
