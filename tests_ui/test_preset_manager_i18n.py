import unittest
from unittest.mock import patch

from keyseq.presentation.dialogs.preset_manager import format_preset_manager_source_labels


class PresetManagerI18nTests(unittest.TestCase):
    def test_source_labels_translate_when_requested(self):
        def translate(key, **params):
            return f"{key}:{params.get('path', '')}"

        with patch("keyseq.presentation.dialogs.preset_manager.tr", side_effect=translate):
            labels = format_preset_manager_source_labels(
                individual_for_save=False,
                individual_state="external_missing",
                displayed_source="builtin",
                individual_path="",
                default_individual_path="individual.json",
                global_path="global.json",
                keymap_set_saved=False,
            )

        self.assertEqual(labels, (
            "preset_manager.destination.global:global.json",
            "preset_manager.source.external_missing_disabled:individual.json / "
            "preset_manager.source.global_fallback:",
            "preset_manager.individual_unavailable:",
        ))
