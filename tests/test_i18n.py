"""Catalog behavior without an App or a real user configuration."""

import ast
from concurrent.futures import ThreadPoolExecutor
import json
from string import Formatter
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from keyseq.shared.i18n import (
    available_languages, current_language, fix_language, reset_for_tests,
    resolve_language, set_language, tr, tr_in,
)

fix_language("ja")


class I18nTest(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.locales = Path(folder.name)
        reset_for_tests(self.locales)
        self.addCleanup(self.restore_language)
        self.write("ja", {"both": "JA", "ja_only": "Japanese", "bad": "valid"})
        self.write("en", {"both": "EN", "en_only": "English", "bad": 42})
        self.write("fr", {"both": "FR"})

    @staticmethod
    def restore_language() -> None:
        reset_for_tests()
        fix_language("ja")

    def write(self, code: str, values: dict, name: object = "Name") -> None:
        data = {"_meta": {"name": name}, **values}
        (self.locales / f"{code}.json").write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8",
        )

    def test_default_before_language_selection_is_ja(self) -> None:
        self.assertEqual(current_language(), "ja")
        self.assertEqual(tr("both"), "JA")

    def test_selected_then_en_then_ja_then_key(self) -> None:
        set_language("fr")
        self.assertEqual(tr("both"), "FR")
        self.assertEqual(tr("en_only"), "English")
        self.assertEqual(tr("ja_only"), "Japanese")
        with self.assertLogs(level="WARNING"):
            self.assertEqual(tr("unknown"), "unknown")

    def test_ja_takes_priority_over_en(self) -> None:
        set_language("ja")
        self.assertEqual(tr("both"), "JA")
        self.assertEqual(tr("en_only"), "English")

    def test_missing_key_warns_once_across_languages(self) -> None:
        with patch("logging.warning") as warning:
            self.assertEqual(tr("missing"), "missing")
            self.assertEqual(tr_in("en", "missing"), "missing")
            warning.assert_called_once()
        reset_for_tests(self.locales)
        with patch("logging.warning") as warning:
            tr("missing")
            warning.assert_called_once()

    def test_formatting_and_positional_only_names(self) -> None:
        self.write("ja", {
            "greeting": "Hello {name}", "key_param": "{key}",
            "lang_param": "{lang}", "brace": "literal {", "broken": "{name",
        })
        self.write("en", {"lang_param": "{lang}"})
        self.assertEqual(tr("greeting", name="Alice"), "Hello Alice")
        self.assertEqual(tr("key_param", key="x"), "x")
        self.assertEqual(tr_in("en", "lang_param", lang="x"), "x")
        self.assertEqual(tr("brace"), "literal {")
        for key in ("greeting", "broken"):
            with self.subTest(key=key), self.assertLogs(level="WARNING"):
                self.assertEqual(tr(key, unused="x"), self.read_ja()[key])

    def read_ja(self) -> dict:
        return json.loads((self.locales / "ja.json").read_text(encoding="utf-8"))

    def test_nonstring_value_falls_back_for_that_key_only(self) -> None:
        set_language("en")
        self.assertEqual(tr("bad"), "valid")
        self.assertEqual(tr("both"), "EN")

    def test_fix_blocks_set_and_tr_in_does_not_change_language(self) -> None:
        fix_language("ja")
        set_language("en")
        self.assertEqual(tr_in("en", "both"), "EN")
        self.assertEqual(current_language(), "ja")
        self.assertEqual(tr("both"), "JA")
        reset_for_tests(self.locales)
        set_language("en")
        self.assertEqual(current_language(), "en")

    def test_available_languages_order_and_validation(self) -> None:
        self.write("pt-br", {}, "Portuguese")
        self.write("aa", {}, "First")
        for code in ("UPPER", "_hidden", "a--b", "-bad", "bad-"):
            self.write(code, {})
        self.write("bad-meta", {}, 3)
        for code, contents in (("broken", "{"), ("array", "[]"),
                               ("no-meta", "{}"), ("meta-array", '{"_meta": []}')):
            (self.locales / f"{code}.json").write_text(contents, encoding="utf-8")
        (self.locales / "utf8.json").write_bytes(b"\xff")
        with self.assertLogs(level="WARNING"):
            self.assertEqual(available_languages(), [
                ("ja", "Name"), ("en", "Name"), ("aa", "First"),
                ("fr", "Name"), ("pt-br", "Portuguese"),
            ])

    def test_invalid_catalog_is_excluded_from_translation(self) -> None:
        self.write("fr", {"both": "invalid catalog"}, None)
        with self.assertLogs(level="WARNING"):
            self.assertEqual(tr_in("fr", "both"), "EN")

    def test_missing_en_and_invalid_ja_return_key(self) -> None:
        (self.locales / "en.json").unlink()
        (self.locales / "ja.json").write_text("[]", encoding="utf-8")
        with self.assertLogs(level="WARNING"):
            self.assertEqual(tr_in("en", "both"), "both")

    def test_resolve_saved_values(self) -> None:
        for value in (None, 1, True, [], {}, "unknown", "JA", ""):
            with self.subTest(value=value):
                self.assertEqual(resolve_language(value), "en")
        for value in ("ja", "en", "fr"):
            self.assertEqual(resolve_language(value), value)
        self.assertEqual(current_language(), "ja")

    def test_loads_lazily_and_caches_per_language(self) -> None:
        self.write("ja", {"both": "before first use"})
        self.assertEqual(tr("both"), "before first use")
        self.write("ja", {"both": "after first use"})
        self.assertEqual(tr("both"), "before first use")
        self.assertEqual(tr_in("en", "both"), "EN")

    def test_concurrent_first_reads(self) -> None:
        with ThreadPoolExecutor(max_workers=8) as executor:
            values = list(executor.map(lambda _: tr("both"), range(32)))
        self.assertEqual(values, ["JA"] * 32)

    def test_bundled_catalogs_have_valid_keys_placeholders_and_names(self) -> None:
        reset_for_tests()
        self.assertEqual(available_languages(), [("ja", "日本語"), ("en", "English")])
        root = Path(__file__).resolve().parents[1] / "keyseq/shared/i18n/locales"
        ja = json.loads((root / "ja.json").read_text(encoding="utf-8"))
        en = json.loads((root / "en.json").read_text(encoding="utf-8"))
        self.assertTrue(en.keys() <= ja.keys())
        formatter = Formatter()
        for key in en.keys() - {"_meta"}:
            with self.subTest(key=key):
                ja_fields = {name for _, name, _, _ in formatter.parse(ja[key]) if name is not None}
                en_fields = {name for _, name, _, _ in formatter.parse(en[key]) if name is not None}
                self.assertEqual(ja_fields, en_fields)
        for catalog in (ja, en):
            self.assertIsInstance(catalog["_meta"]["name"], str)
            self.assertTrue(all(isinstance(value, str) for key, value in catalog.items()
                                if key != "_meta"))
        for key, value in ja.items():
            if key == "_meta":
                continue
            with self.subTest(key=key):
                params = {name: "VALUE" for _, name, _, _ in formatter.parse(value)
                          if name is not None}
                self.assertEqual(tr(key, **params), value.format_map(params))

    def test_shared_imports_only_standard_library_or_relative_modules(self) -> None:
        root = Path(__file__).resolve().parents[1] / "keyseq/shared/i18n"
        for path in root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                for name in names:
                    with self.subTest(path=path, module=name):
                        self.assertFalse(name == "keyseq" or name.startswith("keyseq."))


if __name__ == "__main__":
    unittest.main()
