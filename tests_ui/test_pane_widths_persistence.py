"""希望幅の保存・復元を実際の Tk で確認する（task_04、フック開始なし）。"""
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from keyseq.presentation import theme
from keyseq.presentation import app as app_module
from keyseq.presentation.app import App
from keyseq.presentation.pane_width_rules import PANE_WIDTHS_KEY, SASH_WIDTH, PaneWidths


class PaneWidthsPersistenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sizes = dict(theme._BASE_FONT_SIZES)
        cls.addClassCleanup(cls._restore_base_sizes, sizes)
        loader = patch.object(app_module.ConfigService, "load_startup", return_value={})
        loader.start()
        try:
            cls.app = App()
        finally:
            loader.stop()
        cls.addClassCleanup(cls._destroy_app)
        cls.app.update()

    @classmethod
    def _restore_base_sizes(cls, sizes: dict[str, int]) -> None:
        theme._BASE_FONT_SIZES.clear()
        theme._BASE_FONT_SIZES.update(sizes)

    @classmethod
    def _destroy_app(cls) -> None:
        try:
            cls.app.update()
        finally:
            cls.app.destroy()

    def setUp(self) -> None:
        self.layout = self.app.pane_layout
        self.view = self.app.full_view
        self.panes = self.view.panes
        self.boxes = (self.view.keymap_box, self.view.trigger_box, self.view.sequence_box)
        self.app.update()
        self.saved = {
            "geometry": self.app.geometry(), "delta": self.app._ui_font_delta_pt,
            "minsize": self.app.wm_minsize(), "desired": self.layout.desired,
            "min_widths": self.layout.min_widths, "pending": self.layout._remeasure_pending,
            "startup": self.app._startup_settings, "startup_path": self.app.startup_path,
            "auto_width": self.layout._auto_window_width,
            "options": [
                {name: self.panes.panecget(box, name) for name in ("width", "minsize")}
                for box in self.boxes
            ],
        }
        saver = patch.object(self.app.config_service, "save_startup")
        self.save_startup = saver.start()
        self.addCleanup(saver.stop)
        self.writer = patch.object(self.app.startup_io, "write_startup", return_value=True)
        self.write_startup = self.writer.start()
        self.addCleanup(self.writer.stop)
        self.addCleanup(self._restore)
        self.app._apply_font_delta(0)
        self._set_desired(PaneWidths(self.layout.min_widths.keymap, self.layout.min_widths.sequence))
        self.app.geometry(f"{self.app.winfo_width() + 200}x{self.app.winfo_height()}")
        self.app.update()
        # ドラッグの余地を作る準備の拡幅は、ユーザー操作の幅として保存対象にしない（暫定仕様16 §3-8）。
        self.layout._auto_window_width = self.app.winfo_width()
        self.write_startup.reset_mock()

    def _restore(self) -> None:
        saved = self.saved
        try:
            self.layout.desired = saved["desired"]
            self.app._apply_font_delta(saved["delta"])
        finally:
            self.app._startup_settings = saved["startup"]
            self.app.startup_path = saved["startup_path"]
            self.layout.min_widths = saved["min_widths"]
            self.layout._remeasure_pending = saved["pending"]
            self.layout._drag = None
            self.layout._auto_window_width = saved["auto_width"]
            self.app.minsize(*saved["minsize"])
            self.app.geometry(saved["geometry"])
            for box, options in zip(self.boxes, saved["options"]):
                self.panes.paneconfigure(box, **options)
            self.app.update()

    def _set_desired(self, desired: PaneWidths) -> None:
        self.layout.desired = desired
        self.layout.apply_layout()
        self.app.update()

    def _drag(self, sash: int, dx: int) -> None:
        x = self.panes.sash_coord(sash)[0] + SASH_WIDTH // 2
        y = self.panes.winfo_height() // 2
        self.panes.event_generate("<Button-1>", x=x, y=y)
        self.assertIsNotNone(self.layout._drag)
        self.panes.event_generate("<B1-Motion>", x=x + dx, y=y)
        self.app.update()
        self.panes.event_generate("<ButtonRelease-1>", x=x + dx, y=y)
        self.app.update()

    def _payload(self) -> dict:
        desired = self.layout.desired
        return {PANE_WIDTHS_KEY: {"keymap": desired.keymap, "sequence": desired.sequence}}

    def test_01_each_sash_saves_desired_once_on_release(self) -> None:
        for sash, dx in ((0, 30), (1, -30)):
            with self.subTest(sash=sash):
                before = self.layout.desired
                self.write_startup.reset_mock()
                x = self.panes.sash_coord(sash)[0] + SASH_WIDTH // 2
                y = self.panes.winfo_height() // 2
                self.panes.event_generate("<Button-1>", x=x, y=y)
                self.assertIsNotNone(self.layout._drag)
                self.panes.event_generate("<B1-Motion>", x=x + dx, y=y)
                self.app.update()
                self.write_startup.assert_not_called()
                self.panes.event_generate("<ButtonRelease-1>", x=x + dx, y=y)
                self.app.update()
                self.assertNotEqual(self.layout.desired, before)
                self.write_startup.assert_called_once_with(self._payload())

    def test_02_non_sash_click_does_not_save(self) -> None:
        before = self.layout.desired
        trigger = self.view.trigger_box
        x = trigger.winfo_x() + trigger.winfo_width() // 2
        y = self.panes.winfo_height() // 2
        self.panes.event_generate("<Button-1>", x=x, y=y)
        self.assertIsNone(self.layout._drag)
        self.panes.event_generate("<ButtonRelease-1>", x=x, y=y)
        self.app.update()
        self.assertEqual(self.layout.desired, before)
        self.write_startup.assert_not_called()

    def test_02_unchanged_sash_does_not_save(self) -> None:
        before = self.layout.desired
        for sash in (0, 1):
            with self.subTest(sash=sash):
                self._drag(sash, 0)
                self.assertEqual(self.layout.desired, before)
                self.write_startup.assert_not_called()

    def test_02_blocked_drag_keeps_below_minimum_desired_without_save(self) -> None:
        desired = PaneWidths(1, self.layout.desired.sequence)
        self._set_desired(desired)
        self.assertEqual(self.view.keymap_box.winfo_width(), self.layout.min_widths.keymap)
        self._drag(0, -50)
        self.assertEqual(self.view.keymap_box.winfo_width(), self.layout.min_widths.keymap)
        self.assertEqual(self.layout.desired, desired)
        self.write_startup.assert_not_called()

    def test_03_font_expansion_does_not_replace_saved_keymap_desired(self) -> None:
        before = self.layout.desired
        self.app._apply_font_delta(2)
        self.app.update()
        self.assertGreater(self.layout.min_widths.keymap, before.keymap)
        self.assertEqual(self.view.keymap_box.winfo_width(), self.layout.min_widths.keymap)
        self.write_startup.reset_mock()  # フォント設定自体の保存を除く。
        self._drag(1, -30)
        self.assertEqual(self.layout.desired.keymap, before.keymap)
        self.assertNotEqual(self.layout.desired.sequence, before.sequence)
        self.write_startup.assert_called_once_with(self._payload())

    def test_04_failed_write_keeps_new_desired_without_retry_on_same_position(self) -> None:
        before = self.layout.desired
        self.write_startup.return_value = False
        self._drag(0, 30)
        desired = self.layout.desired
        self.assertNotEqual(desired, before)
        self.assertEqual(desired.keymap, self.view.keymap_box.winfo_width())
        self.write_startup.assert_called_once_with(self._payload())
        self._drag(0, 0)
        self.assertEqual(self.layout.desired, desired)
        self.write_startup.assert_called_once_with(self._payload())

    def test_05_drag_save_preserves_existing_startup_keys(self) -> None:
        existing = {
            "ui_font_delta_pt": 2, "orphan_sweep_scan_dirs": ["user/keymaps"],
            "keymap_set_path": "user/keymap_sets/current.json",
        }
        self.app._startup_settings = dict(existing)
        self.writer.stop()  # 実 write_startup を通し、ディスク書込だけを差し替える。
        self._drag(0, 30)
        self.save_startup.assert_called_once()
        payload = self.save_startup.call_args.args[1]
        for key, value in existing.items():
            self.assertEqual(payload[key], value)
        self.assertEqual(payload[PANE_WIDTHS_KEY], self._payload()[PANE_WIDTHS_KEY])

    def _restore_initial(self, startup: object) -> PaneWidths:
        self.app._startup_settings = startup
        self.layout.apply_initial_widths()
        self.app.update()
        self.write_startup.assert_not_called()
        self.save_startup.assert_not_called()
        return self.layout.desired

    def test_06_valid_saved_widths_restore_desired_and_display_without_write(self) -> None:
        mins = self.layout.min_widths
        expected = PaneWidths(mins.keymap + 20, mins.sequence + 20)
        actual = self._restore_initial({PANE_WIDTHS_KEY: {
            "keymap": expected.keymap, "sequence": expected.sequence,
        }})
        self.assertEqual(actual, expected)
        self.assertEqual(self.view.keymap_box.winfo_width(), expected.keymap)
        self.assertEqual(self.view.sequence_box.winfo_width(), expected.sequence)

    def test_06_invalid_saved_widths_use_missing_key_defaults_without_write(self) -> None:
        expected = self._restore_initial({})
        invalid = [None, [], "300", 300, {}, {"keymap": 300}, {"sequence": 300}]
        for side in ("keymap", "sequence"):
            for value in (True, False, "300", 300.0, 0, -1):
                invalid.append({"keymap": 300, "sequence": 300, side: value})
        with patch("tkinter.messagebox.showerror") as showerror:
            for raw in invalid:
                with self.subTest(raw=raw):
                    self.assertEqual(self._restore_initial({PANE_WIDTHS_KEY: raw}), expected)
            showerror.assert_not_called()

    def test_06_non_dict_or_missing_startup_uses_defaults_without_write(self) -> None:
        expected = self._restore_initial({})
        for startup in (None, [], "invalid", True, 300):
            with self.subTest(startup=startup):
                self.assertEqual(self._restore_initial(startup), expected)
        del self.app._startup_settings
        self.layout.apply_initial_widths()
        self.app.update()
        self.assertEqual(self.layout.desired, expected)
        self.write_startup.assert_not_called()
        self.save_startup.assert_not_called()

    def test_06_below_minimum_saved_widths_only_raise_display_without_write(self) -> None:
        actual = self._restore_initial({PANE_WIDTHS_KEY: {"keymap": 1, "sequence": 1}})
        self.assertEqual(actual, PaneWidths(1, 1))
        self.assertEqual(self.view.keymap_box.winfo_width(), self.layout.min_widths.keymap)
        self.assertEqual(self.view.sequence_box.winfo_width(), self.layout.min_widths.sequence)

    def test_07_keymap_set_save_preserves_widths_in_payload_and_file(self) -> None:
        widths = {"keymap": 300, "sequence": 400}
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, "user", "keymap_sets", "saved.json")
            _, startup = self.app.config_service.save_runtime_data(
                path, self.app.config_service.new_default_data(),
                config_root=root, startup_data={PANE_WIDTHS_KEY: widths},
            )
            self.assertEqual(startup[PANE_WIDTHS_KEY], widths)
            with open(os.path.join(root, "config.json"), encoding="utf-8") as file:
                self.assertEqual(json.load(file)[PANE_WIDTHS_KEY], widths)


class PaneWidthsStartupRestoreTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sizes = dict(theme._BASE_FONT_SIZES)
        cls.addClassCleanup(cls._restore_base_sizes, sizes)
        writer = patch.object(app_module.StartupIo, "write_startup", return_value=True)
        cls.write_startup = writer.start()
        cls.addClassCleanup(writer.stop)
        saver = patch.object(app_module.ConfigService, "save_startup")
        cls.save_startup = saver.start()
        cls.addClassCleanup(saver.stop)
        screen = patch.object(App, "winfo_screenwidth", return_value=100000)
        screen.start()
        cls.addClassCleanup(screen.stop)
        cls.expected = cls._measure_saved_widths()
        startup = {PANE_WIDTHS_KEY: {
            "keymap": cls.expected.keymap, "sequence": cls.expected.sequence,
        }}
        with patch.object(app_module.ConfigService, "load_startup", return_value=startup):
            cls.app = App()
        cls.addClassCleanup(cls._destroy_app)
        cls.app.update()

    @classmethod
    def _measure_saved_widths(cls) -> PaneWidths:
        # 測定用 App は復元を検証する App より先に破棄する。
        with patch.object(app_module.ConfigService, "load_startup", return_value={}):
            probe = App()
        try:
            probe.update()
            defaults = probe.pane_layout.desired
            return PaneWidths(defaults.keymap + 40, defaults.sequence + 40)
        finally:
            try:
                probe.update()
            finally:
                probe.destroy()

    @classmethod
    def _restore_base_sizes(cls, sizes: dict[str, int]) -> None:
        theme._BASE_FONT_SIZES.clear()
        theme._BASE_FONT_SIZES.update(sizes)

    @classmethod
    def _destroy_app(cls) -> None:
        try:
            cls.app.update()
        finally:
            cls.app.destroy()

    def test_startup_restores_saved_widths_without_write(self) -> None:
        layout = self.app.pane_layout
        view = self.app.full_view
        self.assertGreaterEqual(self.expected.keymap, layout.min_widths.keymap)
        self.assertGreaterEqual(self.expected.sequence, layout.min_widths.sequence)
        self.assertEqual(layout.desired, self.expected)
        self.assertEqual(view.keymap_box.winfo_width(), self.expected.keymap)
        self.assertEqual(view.sequence_box.winfo_width(), self.expected.sequence)
        self.write_startup.assert_not_called()
        self.save_startup.assert_not_called()


if __name__ == "__main__":
    unittest.main()
