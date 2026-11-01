"""Keep application-creating tests independent of the host language setting."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
APP_CALL = re.compile(r"\bApp\s*\(")


class TestLanguagePinTest(unittest.TestCase):
    def test_every_app_test_module_fixes_language(self) -> None:
        test_roots = (ROOT / "tests", ROOT / "tests_ui")
        for test_root in test_roots:
            for path in test_root.rglob("test_*.py"):
                if path.name == Path(__file__).name:
                    continue
                source = path.read_text(encoding="utf-8-sig")
                if APP_CALL.search(source):
                    with self.subTest(path=path.relative_to(ROOT)):
                        self.assertIn("fix_language(", source)


if __name__ == "__main__":
    unittest.main()
