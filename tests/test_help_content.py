"""Tests for bundled help content parsing and validation."""

import json
from pathlib import Path
import tempfile
import unittest

import keyseq
from keyseq.presentation.help.help_targets import DIALOG_TARGETS
from keyseq.presentation.help.bundled_paths import (
    bundled_root,
    help_content_dir,
    help_content_path,
    license_path,
    third_party_dir,
)
from keyseq.presentation.help.help_content import (
    HelpBlock,
    HelpCategory,
    HelpContent,
    HelpItem,
    find_text_issues,
    item_plain_text,
    load_help_content,
    parse_help_content,
)


GUIDE_IDS = [
    "intro", "keymap_set", "keymap", "trigger", "sequence", "hook",
    "view_mode", "keyboard_ui", "screen_grid", "preset", "cleanup",
]
GUIDE_TITLES = [
    "はじめに", "構成セットとファイル", "キーマップ", "トリガー", "出力シーケンス",
    "フック", "表示の切替", "キーボードUI", "カーソルグリッド", "プリセット", "ファイルの整理",
]
FAQ_IDS = ["trouble", "limits", "save_files", "key_input"]


def valid_data() -> dict[str, object]:
    return {"format": 1, "tabs": {"guide": [], "faq": []}}


def category(identifier: str = "guide", *, items: list[object] | None = None) -> dict[str, object]:
    return {"id": identifier, "title": "見出し", "items": items or []}


class HelpContentTest(unittest.TestCase):
    def test_dialog_targets_exist_in_bundled_guide(self) -> None:
        result = load_help_content()
        self.assertIsNotNone(result.content, result.error)
        assert result.content is not None
        identifiers = {category.id for category in result.content.guide}
        identifiers.update(item.id for category in result.content.guide
                           for item in category.items)
        for target in DIALOG_TARGETS:
            with self.subTest(target=target):
                self.assertIn(target, identifiers)

    def test_bundled_content_loads_with_expected_outline(self) -> None:
        result = load_help_content()
        self.assertIsNotNone(result.content)
        self.assertEqual(result.error, "")
        assert result.content is not None
        self.assertEqual(find_text_issues(result.content), [])
        self.assertEqual([item.id for item in result.content.guide], GUIDE_IDS)
        self.assertEqual([item.title for item in result.content.guide], GUIDE_TITLES)
        self.assertEqual([item.id for item in result.content.faq], FAQ_IDS)
        self.assertTrue(all(group.items for group in (*result.content.guide, *result.content.faq)))

    def test_version_and_bundled_paths(self) -> None:
        root = bundled_root()
        self.assertEqual(keyseq.__version__, "0.1.0")
        self.assertTrue(license_path().is_file())
        self.assertTrue(help_content_path().is_file())
        self.assertTrue(help_content_dir().is_relative_to(root))
        self.assertTrue(help_content_path().is_relative_to(root))
        self.assertTrue(license_path().is_relative_to(root))
        self.assertTrue(third_party_dir().is_relative_to(root))

    def test_parse_rejects_invalid_root_format_and_tabs(self) -> None:
        for data in ([], {"format": 2, "tabs": {}}, {"format": True, "tabs": {}},
                     {"format": 1}, {"format": 1, "tabs": {"guide": "bad", "faq": []}}):
            with self.subTest(data=data), self.assertRaises(ValueError):
                parse_help_content(data)

    def test_parse_rejects_empty_ids_bad_prefix_and_duplicates_across_tabs(self) -> None:
        cases = []
        data = valid_data()
        data["tabs"] = {"guide": [category("")], "faq": []}
        cases.append(data)
        data = valid_data()
        data["tabs"] = {"guide": [category(items=[{"id": "else.name", "title": "x", "body": []}])], "faq": []}
        cases.append(data)
        data = valid_data()
        data["tabs"] = {"guide": [category("same")], "faq": [category("same")]}
        cases.append(data)
        data = valid_data()
        duplicate_item = {"id": "guide.same", "title": "x", "body": []}
        data["tabs"] = {"guide": [category(items=[duplicate_item, duplicate_item])], "faq": []}
        cases.append(data)
        for data in cases:
            with self.subTest(data=data), self.assertRaises(ValueError):
                parse_help_content(data)

    def test_parse_rejects_bad_body_type_and_list_items(self) -> None:
        for body in ([{"type": "image"}], [{"type": "list", "items": []}],
                     [{"type": "list", "items": ["ok", 3]}]):
            data = valid_data()
            data["tabs"] = {"guide": [category(items=[{"id": "guide.one", "title": "x", "body": body}])], "faq": []}
            with self.subTest(body=body), self.assertRaises(ValueError):
                parse_help_content(data)

    def test_parse_builds_dataclasses_and_ignores_unknown_keys(self) -> None:
        data = {"format": 1, "unknown": True, "tabs": {
            "guide": [{"id": "guide", "title": "見出し", "items": [{
                "id": "guide.one", "title": "項目", "body": [
                    {"type": "p", "text": "段落", "unused": 1},
                    {"type": "list", "items": ["一", "二"]},
                ], "unused": "ignored",
            }]}], "faq": [], "unused": []}}
        result = parse_help_content(data)
        self.assertEqual(result.guide[0].items[0], HelpItem(
            "guide.one", "項目", (HelpBlock("p", "段落"), HelpBlock("list", items=("一", "二")))
        ))
        self.assertEqual(result.guide[0], HelpCategory("guide", "見出し", result.guide[0].items))
        self.assertEqual(result.faq, ())

    def test_load_returns_reason_for_io_json_utf8_and_schema_failures(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            missing = base / "missing.json"
            bad_json = base / "bad.json"
            bad_utf8 = base / "utf8.json"
            bad_schema = base / "schema.json"
            bad_json.write_text("{", encoding="utf-8")
            bad_utf8.write_bytes(b"\xff")
            bad_schema.write_text(json.dumps({"format": 9}), encoding="utf-8")
            for path in (missing, bad_json, bad_utf8, bad_schema):
                with self.subTest(path=path):
                    result = load_help_content(path)
                    self.assertIsNone(result.content)
                    self.assertTrue(result.error)

    def test_item_plain_text_joins_blocks_and_list_entries(self) -> None:
        item = HelpItem("guide.one", "題", (
            HelpBlock("p", "段落"), HelpBlock("list", items=("一", "二")), HelpBlock("p", "末尾")
        ))
        self.assertEqual(item_plain_text(item), "段落\n一\n二\n末尾")

    def test_text_issue_detection(self) -> None:
        def content(text: str) -> HelpContent:
            return HelpContent((HelpCategory("g", text, (
                HelpItem("g.x", "項目", (HelpBlock("p", text),)),
            )),), ())

        for invalid in ("が", "ｶﾞ", "\u3099"):
            with self.subTest(invalid=invalid):
                self.assertTrue(find_text_issues(content(invalid)))
        self.assertEqual(find_text_issues(content("日本語 ß ㍿")), [])


if __name__ == "__main__":
    unittest.main()
