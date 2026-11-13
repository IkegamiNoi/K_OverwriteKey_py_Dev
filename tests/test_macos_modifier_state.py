from __future__ import annotations

import unittest

from keyseq.infrastructure.os_backend.macos.modifier_state import ModifierState


class ModifierStateTests(unittest.TestCase):
    def test_flags_changed_tracks_each_side_independently(self) -> None:
        state = ModifierState()

        self.assertEqual(state.on_flags_changed(56, 0x02), ("down",))
        self.assertEqual(state.on_flags_changed(60, 0x02 | 0x04), ("down",))
        self.assertEqual(state.on_flags_changed(56, 0x04), ("up",))
        self.assertEqual(state.on_flags_changed(60, 0), ("up",))

    def test_unmapped_flags_changed_key_returns_none(self) -> None:
        state = ModifierState()
        for keycode in (63, 57, 0):
            with self.subTest(keycode=keycode):
                self.assertIsNone(state.on_flags_changed(keycode, 0xFFFFFFFF))

    def test_suppressed_down_also_suppresses_matching_up(self) -> None:
        state = ModifierState()

        self.assertEqual(state.on_flags_changed(56, 0x02), ("down",))
        self.assertTrue(state.mark_suppressed(56, True))
        self.assertEqual(state.on_flags_changed(56, 0), ("up",))
        self.assertTrue(state.mark_suppressed(56, False))
        self.assertFalse(state.mark_suppressed(56, False))

    def test_passed_down_also_passes_matching_up(self) -> None:
        state = ModifierState()

        self.assertEqual(state.on_flags_changed(60, 0x04), ("down",))
        self.assertFalse(state.mark_suppressed(60, False))
        self.assertEqual(state.on_flags_changed(60, 0), ("up",))
        self.assertFalse(state.mark_suppressed(60, True))

    def test_right_shift_remains_when_left_shift_is_suppressed(self) -> None:
        state = ModifierState()
        state.on_flags_changed(56, 0x02)
        self.assertTrue(state.mark_suppressed(56, True))
        state.on_flags_changed(60, 0x02 | 0x04)

        rewritten = state.rewrite_flags(0x02 | 0x04 | 0x20000)
        self.assertEqual(rewritten, 0x04 | 0x20000)

    def test_suppressed_command_is_removed_from_later_key_flags(self) -> None:
        state = ModifierState()
        state.on_flags_changed(55, 0x08)
        self.assertTrue(state.mark_suppressed(55, True))

        flags = 0x08 | 0x100000 | 0x08  # Command device and common bits
        self.assertEqual(state.rewrite_flags(flags), 0)

    def test_non_modifier_flags_survive_rewrite(self) -> None:
        state = ModifierState()
        state.on_flags_changed(55, 0x08)
        state.mark_suppressed(55, True)

        non_modifier = 0x10000 | 0x800000 | 0x4000
        self.assertEqual(state.rewrite_flags(0x08 | 0x100000 | non_modifier), non_modifier)

    def test_flags_are_unchanged_without_suppressed_modifier(self) -> None:
        state = ModifierState()
        flags = 0x08 | 0x20000 | 0x10000 | 0x800000
        self.assertEqual(state.rewrite_flags(flags), flags)

    def test_left_shift_bit_is_removed_while_forwarding_right_shift_change(self) -> None:
        state = ModifierState()
        state.on_flags_changed(56, 0x02)
        state.mark_suppressed(56, True)

        flags = 0x02 | 0x04 | 0x20000
        state.on_flags_changed(60, flags)
        self.assertEqual(state.rewrite_flags(flags), 0x04 | 0x20000)

    def test_all_eight_modifier_device_bits_determine_transitions(self) -> None:
        for vk, bit in ((55, 0x08), (54, 0x10), (56, 0x02), (60, 0x04),
                        (58, 0x20), (61, 0x40), (59, 0x01), (62, 0x2000)):
            with self.subTest(vk=vk):
                state = ModifierState()
                self.assertEqual(state.on_flags_changed(vk, bit), ("down",))
                state.mark_suppressed(vk, True)
                self.assertEqual(state.rewrite_flags(0x1E0000 | bit), 0)
                self.assertEqual(state.on_flags_changed(vk, 0x1E0000), ("up",))
                self.assertTrue(state.mark_suppressed(vk, False))

    def test_clear_resets_physical_and_suppression_records(self) -> None:
        state = ModifierState()
        state.on_flags_changed(56, 0x02)
        state.mark_suppressed(56, True)
        state.clear()

        flags = 0x02 | 0x20000
        self.assertEqual(state.rewrite_flags(flags), flags)
        self.assertEqual(state.on_flags_changed(56, 0x02), ("down",))
        self.assertFalse(state.mark_suppressed(56, False))


if __name__ == "__main__":
    unittest.main()
