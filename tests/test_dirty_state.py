import unittest

from keyseq.application.config_service import ConfigService
from keyseq.application.keymap_service import KeymapService
from keyseq.infrastructure.json_repository import JsonRepository
from keyseq.presentation.dirty_state import DirtyStateTracker


class DirtyStateTrackerTest(unittest.TestCase):
    def setUp(self):
        self.config_service = ConfigService(JsonRepository())
        self.keymap_service = KeymapService()
        self.data = {
            "triggers": [{"key": "f1", "actions": []}],
            "keymaps": [{"id": "km1", "label": "Main", "mappings": {}}],
            "active_keymap_id": "km1",
        }
        self.calls = []
        self.tracker = DirtyStateTracker(
            get_data=lambda: self.data,
            keymap_service=self.keymap_service,
            config_service=self.config_service,
            on_change=lambda: self.calls.append(True),
        )

    def test_set_dirty_true_sets_config_dirty(self):
        self.tracker.set_dirty(True)
        self.assertTrue(self.tracker.is_dirty)
        self.assertTrue(self.tracker.config_dirty)
        self.assertTrue(self.tracker.has_unsaved_changes())
        self.assertEqual(len(self.calls), 1)

    def test_set_dirty_config_dirty_false_does_not_set_config_dirty(self):
        self.tracker.set_dirty(True, config_dirty=False)
        self.assertTrue(self.tracker.is_dirty)
        self.assertFalse(self.tracker.config_dirty)
        # 個別ダーティが無ければ未保存ではない
        self.assertFalse(self.tracker.has_unsaved_changes())

    def test_mark_sequence_dirty_marks_target_and_individual(self):
        target = self.data["triggers"][0]
        self.tracker.mark_sequence_dirty(target)
        self.assertTrue(target[self.config_service.INTERNAL_SEQUENCE_DIRTY])
        self.assertFalse(self.tracker.config_dirty)
        self.assertTrue(self.tracker.has_individual_dirty())
        self.assertTrue(self.tracker.has_unsaved_changes())

    def test_mark_keymap_dirty_marks_target_and_individual(self):
        target = self.data["keymaps"][0]
        self.tracker.mark_keymap_dirty(target)
        self.assertTrue(target[self.config_service.INTERNAL_KEYMAP_DIRTY])
        self.assertTrue(self.tracker.has_individual_dirty())

    def test_clear_individual_dirty_flags_resets_internal_keys(self):
        self.tracker.mark_trigger_set_dirty()
        self.tracker.trigger_set_imported = True
        self.tracker.mark_sequence_dirty(self.data["triggers"][0])
        self.tracker.mark_keymap_dirty(self.data["keymaps"][0])
        self.assertTrue(self.tracker.has_individual_dirty())

        self.tracker.clear_individual_dirty_flags()
        self.assertFalse(self.tracker.trigger_set_dirty)
        self.assertFalse(self.tracker.trigger_set_imported)
        self.assertFalse(self.data["triggers"][0][self.config_service.INTERNAL_SEQUENCE_DIRTY])
        self.assertFalse(self.data["triggers"][0][self.config_service.INTERNAL_SEQUENCE_IMPORTED])
        self.assertFalse(self.data["keymaps"][0][self.config_service.INTERNAL_KEYMAP_DIRTY])
        self.assertFalse(self.data["keymaps"][0][self.config_service.INTERNAL_KEYMAP_IMPORTED])
        self.assertFalse(self.tracker.has_individual_dirty())


if __name__ == "__main__":
    unittest.main()
