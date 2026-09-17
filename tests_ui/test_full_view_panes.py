"""フル表示の幅配分を実際の Tk ウィジェットで確認する（フック開始なし）。"""
import tkinter as tk
from tkinter import font as tkfont
import unittest
from unittest.mock import patch

from keyseq.presentation.app import App
from keyseq.presentation import app as app_module
from keyseq.presentation import theme
from keyseq.presentation.pane_width_rules import SASH_WIDTH


class FullViewPanesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        base_sizes = dict(theme._BASE_FONT_SIZES)
        cls.addClassCleanup(cls._restore_base_sizes, base_sizes)
        for target, name, value in (
            (app_module.StartupIo, "write_startup", True),
            (app_module.ConfigService, "save_startup", None),
        ):
            patcher = patch.object(target, name, return_value=value)
            patcher.start()
            cls.addClassCleanup(patcher.stop)
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
            cls.app.pane_layout.cancel_window_width_save()
            cls.app.update()
        finally:
            cls.app.destroy()

    def setUp(self) -> None:
        self.view = self.app.full_view
        self.panes = self.view.panes
        self.boxes = (self.view.keymap_box, self.view.trigger_box, self.view.sequence_box)
        self.app.update()
        self.saved_geometry = self.app.geometry()
        self.saved_delta = self.app._ui_font_delta_pt
        self.saved_minsize = self.app.wm_minsize()
        self.saved_options = [
            {name: self.panes.panecget(box, name) for name in ("width", "minsize", "stretch")}
            for box in self.boxes
        ]
        self.saved_sashes = [self.panes.sash_coord(index) for index in range(2)]
        writer = patch.object(self.app.startup_io, "write_startup", return_value=True)
        writer.start()
        self.addCleanup(writer.stop)
        # addCleanup は setUp 内の失敗時にも実行され、書込パッチより先に復元する。
        self.addCleanup(self._restore_layout)

    def _restore_layout(self) -> None:
        try:
            self.app._apply_font_delta(self.saved_delta)
        finally:
            self.app.geometry(self.saved_geometry)
            for box, options in zip(self.boxes, self.saved_options):
                self.panes.paneconfigure(box, **options)
            self.app.update()
            for index, (x, y) in enumerate(self.saved_sashes):
                self.panes.sash_place(index, x, y)
            self.app.update()
            self.app.minsize(*self.saved_minsize)
            self.app.pane_layout.cancel_window_width_save()

    def _resize(self, width: int, height: int | None = None) -> None:
        self.app.geometry(f"{width}x{height or self.app.winfo_height()}")
        self.app.update()

    def test_01_structure_and_sash_width(self) -> None:
        self.assertIsInstance(self.panes, tk.PanedWindow)
        self.assertEqual(tuple(map(str, self.panes.panes())), tuple(map(str, self.boxes)))
        self.assertEqual(
            [str(self.panes.panecget(box, "stretch")) for box in self.boxes],
            ["never", "always", "never"],
        )
        self.assertEqual(int(self.panes.cget("sashwidth")) + 2 * int(self.panes.cget("sashpad")), 12)
        self.assertEqual(int(self.panes.cget("borderwidth")), 0)
        self.assertFalse(self.panes.tk.getboolean(self.panes.cget("showhandle")))

    def test_02_default_layout_matches_original(self) -> None:
        self.assertEqual(self.app.winfo_width(), 780)
        required = sum(box.winfo_reqwidth() for box in self.boxes) + 2 * SASH_WIDTH
        self.assertGreaterEqual(
            self.panes.winfo_width(), required,
            "初期幅780では3枠の要求幅と境界線が収まらない（フォント・DPIを確認）",
        )
        keymap, trigger, sequence = self.boxes
        self.assertEqual(keymap.winfo_width(), keymap.winfo_reqwidth())
        self.assertEqual(trigger.winfo_x(), keymap.winfo_x() + keymap.winfo_width() + 12)
        self.assertEqual(trigger.winfo_width(), trigger.winfo_reqwidth())
        self.assertEqual(sequence.winfo_x(), trigger.winfo_x() + trigger.winfo_width() + 12)
        self.assertEqual(sequence.winfo_x() + sequence.winfo_width(), self.panes.winfo_width())

    def test_03_only_trigger_stretches_with_window(self) -> None:
        # 標準幅のトリガーが既に最小幅の場合でも -40 を検査できる余裕を作る。
        self._resize(self.app.winfo_width() + 80)
        baseline = self.app.winfo_width()
        widths = [box.winfo_width() for box in self.boxes]
        list_width = self.view.trigger_box.trigger_list.winfo_width()
        minimum = self.app.pane_layout.measure_min_widths().trigger
        self.assertGreaterEqual(widths[1] - 40, minimum)
        for delta in (120, -40):
            with self.subTest(delta=delta):
                self._resize(baseline + delta)
                self.assertEqual(self.boxes[0].winfo_width(), widths[0])
                self.assertEqual(self.boxes[2].winfo_width(), widths[2])
                self.assertEqual(self.boxes[1].winfo_width(), widths[1] + delta)
                self.assertEqual(self.view.trigger_box.trigger_list.winfo_width(), list_width + delta)

    def test_04_lists_expand_with_panes(self) -> None:
        trigger_list = self.view.trigger_box.trigger_list
        before = trigger_list.winfo_width()
        self._resize(self.app.winfo_width() + 160)
        self.assertEqual(trigger_list.winfo_width(), before + 160)
        keymap = self.view.keymap_box
        before = keymap.keymap_listbox.winfo_width()
        self.panes.paneconfigure(keymap, width=keymap.winfo_width() + 40)
        self.app.update()
        self.assertEqual(keymap.keymap_listbox.winfo_width(), before + 40)

    def test_05_minimum_widths_fit_children_at_each_font_size(self) -> None:
        listings = (
            self.view.keymap_box.keymap_listbox,
            self.view.trigger_box.trigger_list, self.view.sequence_box.action_list,
        )
        for delta in (-2, 0, 2):
            with self.subTest(font_delta=delta):
                self.app._apply_font_delta(delta)
                mins = self.app.pane_layout.measure_min_widths()
                widths = (mins.keymap, mins.trigger, mins.sequence)
                extra = self.app.winfo_width() - self.panes.winfo_width()
                for box, width in zip(self.boxes, widths):
                    self.panes.paneconfigure(box, minsize=width, width=width)
                # 最小幅の合計まで狭められるよう、フォント変更で設定されたウィンドウ最小幅を解除する。
                self.app.minsize(1, 1)
                self._resize(sum(widths) + 2 * SASH_WIDTH + extra, self.app.winfo_reqheight())
                for box, listing, width in zip(self.boxes, listings, widths):
                    self.assertEqual(box.winfo_width(), width)
                    font = tkfont.Font(root=self.app, font=listing.cget("font"))
                    self.assertGreaterEqual(listing.winfo_width(), font.measure("0") * 10)
                    self._assert_children_fit(box, listing)

    def _assert_children_fit(self, parent: tk.Misc, listing: tk.Listbox) -> None:
        for child in parent.winfo_children():
            # 一覧と一覧だけを包むフレームの要求幅は26文字のまま維持する。
            if child is not listing and child is not listing.master:
                self.assertTrue(child.winfo_ismapped(), str(child))
                self.assertGreaterEqual(child.winfo_width(), child.winfo_reqwidth(), str(child))
                self.assertGreaterEqual(child.winfo_x(), 0, str(child))
                self.assertLessEqual(child.winfo_x() + child.winfo_width(), parent.winfo_width(), str(child))
            self._assert_children_fit(child, listing)

    def test_06_action_list_alias_is_preserved(self) -> None:
        self.assertIs(self.view.action_list, self.view.sequence_box.action_list)
