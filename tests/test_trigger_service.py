import unittest

from keyseq.application.trigger_service import TriggerService


class TriggerServiceTest(unittest.TestCase):
    def setUp(self):
        self.trigger = {"key": "f1", "actions": []}
        self.data = {
            "triggers": [self.trigger],
            "hook_stop_key": "f12",
            "hook_toggle_key": "f11",
        }

    def test_find_trigger_by_key_normalizes(self):
        self.assertIs(TriggerService.find_trigger_by_key(self.data, " F1 "), self.trigger)
        self.assertIsNone(TriggerService.find_trigger_by_key(self.data, "f2"))

    def test_key_exists_exclude_trigger(self):
        self.assertTrue(TriggerService.key_exists(self.data, "f1"))
        self.assertFalse(TriggerService.key_exists(self.data, "f1", exclude_trigger=self.trigger))

    def test_stop_and_toggle_conflict(self):
        self.assertTrue(TriggerService.is_stop_key_conflict(self.data, "F12"))
        self.assertFalse(TriggerService.is_stop_key_conflict(self.data, "f1"))
        self.assertTrue(TriggerService.is_toggle_key_conflict(self.data, "f11"))


if __name__ == "__main__":
    unittest.main()
