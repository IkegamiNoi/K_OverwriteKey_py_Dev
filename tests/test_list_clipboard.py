import unittest

from keyseq.presentation.list_clipboard import CLIP_ACTIONS, ListClipboard


class ListClipboardTest(unittest.TestCase):
    def test_copy_and_paste_are_independent_copies(self):
        source = [{"type": "text", "value": "before", "nested": [1]}]
        clipboard = ListClipboard()

        clipboard.copy(CLIP_ACTIONS, source)
        source[0]["value"] = "edited"
        first_paste = clipboard.paste(CLIP_ACTIONS)
        first_paste[0]["nested"].append(2)

        self.assertEqual(clipboard.paste(CLIP_ACTIONS), [
            {"type": "text", "value": "before", "nested": [1]},
        ])

    def test_wrong_kind_returns_none(self):
        clipboard = ListClipboard()
        clipboard.copy(CLIP_ACTIONS, [{"type": "text"}])

        self.assertIsNone(clipboard.paste("triggers"))

    def test_clear_removes_stored_items(self):
        clipboard = ListClipboard()
        clipboard.copy(CLIP_ACTIONS, [{"type": "text"}])
        clipboard.clear()

        self.assertIsNone(clipboard.paste(CLIP_ACTIONS))


if __name__ == "__main__":
    unittest.main()
