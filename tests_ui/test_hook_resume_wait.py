"""フック停止カウント待機ヘルパの決定的テスト。"""

import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from tests_ui.hook_resume_wait import wait_for_hook_pause_count


class HookResumeWaitTest(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.addCleanup(self.root.destroy)
        self.root.withdraw()
        self.count = 1
        self.app = SimpleNamespace(
            update=self.root.update,
            hook=SimpleNamespace(get_hook_pause_count=lambda: self.count),
        )

    def test_waits_for_delayed_resume(self):
        self.root.after(50, lambda: setattr(self, "count", 0))

        wait_for_hook_pause_count(self, self.app, 0)

        self.assertEqual(self.count, 0)

    def test_timeout_reports_expected_and_current_counts(self):
        with self.assertRaises(self.failureException) as raised:
            wait_for_hook_pause_count(self, self.app, 0, timeout=0.1)

        message = str(raised.exception)
        self.assertIn("expected=0", message)
        self.assertIn("current=1", message)

    def test_updates_even_when_count_already_matches(self):
        self.count = 0
        self.app.update = Mock(wraps=self.root.update)

        wait_for_hook_pause_count(self, self.app, 0)

        self.assertGreaterEqual(self.app.update.call_count, 1)


if __name__ == "__main__":
    unittest.main()
