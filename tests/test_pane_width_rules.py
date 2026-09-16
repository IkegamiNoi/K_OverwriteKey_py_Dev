import unittest
from dataclasses import FrozenInstanceError

from keyseq.presentation.pane_width_rules import (
    DEFAULT_LIST_CHARS,
    MIN_LIST_CHARS,
    PANE_WIDTHS_KEY,
    LayoutPlan,
    MinWidths,
    PaneWidths,
    clamp,
    default_pane_widths,
    drag_limits,
    list_row_width,
    parse_saved_pane_widths,
    resolve_layout,
    side_by_side_min_width,
    stacked_min_width,
    update_desired_after_drag,
)


class PaneWidthRulesTest(unittest.TestCase):
    def test_constants(self):
        """暫定仕様16 §2-5・§3-6 の文字数と保存キーを固定する。"""
        self.assertEqual(PANE_WIDTHS_KEY, "full_view_pane_widths")
        self.assertEqual(MIN_LIST_CHARS, 10)
        self.assertEqual(DEFAULT_LIST_CHARS, 26)

    def test_width_records_are_frozen(self):
        """暫定仕様16 §3-5・§3-7 の幅と計算結果を不変に保つ。"""
        for record in (PaneWidths(100, 200), MinWidths(100, 80, 120),
                       LayoutPlan(100, 200, 410, 500)):
            with self.subTest(record=record):
                with self.assertRaises(FrozenInstanceError):
                    record.keymap = 999

    def test_parse_valid_widths_without_clamping(self):
        """暫定仕様16 §3-6 の正の保存値は最小幅未満でも保持する。"""
        for keymap, sequence in ((200, 300), (1, 1)):
            with self.subTest(keymap=keymap, sequence=sequence):
                self.assertEqual(
                    parse_saved_pane_widths({"keymap": keymap, "sequence": sequence}),
                    PaneWidths(keymap, sequence),
                )

    def test_parse_rejects_non_dict(self):
        """暫定仕様16 §3-6 の非 dict は例外なく無視する。"""
        for raw in (None, [], [100, 200], "100"):
            with self.subTest(raw=raw):
                self.assertIsNone(parse_saved_pane_widths(raw))

    def test_parse_rejects_missing_keys(self):
        """暫定仕様16 §3-6 の片側欠落は組全体を無視する。"""
        for raw in ({}, {"keymap": 100}, {"sequence": 200}):
            with self.subTest(raw=raw):
                self.assertIsNone(parse_saved_pane_widths(raw))

    def test_parse_rejects_invalid_values_on_either_side(self):
        """暫定仕様16 §3-6 の型・正数検証を両側に適用する。"""
        for side in ("keymap", "sequence"):
            for value in (True, False, 1.0, "100", 0, -1, None):
                with self.subTest(side=side, value=value):
                    raw = {"keymap": 100, "sequence": 200}
                    raw[side] = value
                    self.assertIsNone(parse_saved_pane_widths(raw))

    def test_parse_accepts_extra_keys(self):
        """暫定仕様16 §3-6 の正常値は余分なキーがあっても採用する。"""
        raw = {"keymap": 100, "sequence": 200, "extra": False}
        self.assertEqual(parse_saved_pane_widths(raw), PaneWidths(100, 200))

    def test_list_row_includes_chrome_and_scrollbar(self):
        """暫定仕様16 §3-4 の一覧行は文字幅・枠線・スクロールバーを含む。"""
        self.assertEqual(list_row_width(8, 10, 6, 17), 103)

    def test_stacked_min_width_without_other_children(self):
        """暫定仕様16 §3-4 の縦並びは他の子が空でも計算する。"""
        self.assertEqual(stacked_min_width(100, [], 12, 90), 112)

    def test_stacked_min_width_when_list_is_widest(self):
        """暫定仕様16 §3-4 の縦並びで一覧が最広の場合を固定する。"""
        self.assertEqual(stacked_min_width(100, (80, 95), 12, 90), 112)

    def test_stacked_min_width_never_cuts_wider_suppress_checkbox(self):
        """暫定仕様16 §3-4 の最広チェックボックス切れを回帰防止する。"""
        width = stacked_min_width(100, (90, 177), 12, 150)
        self.assertEqual(width, 189)
        self.assertGreaterEqual(width, 177 + 12)

    def test_stacked_min_width_when_title_is_widest(self):
        """暫定仕様16 §3-4 の見出し幅は枠線込みの値で比較する。"""
        self.assertEqual(stacked_min_width(100, (120,), 12, 200), 200)

    def test_side_by_side_min_width_when_sum_is_widest(self):
        """暫定仕様16 §3-4 の横並びは子の幅と間隔・枠線を合計する。"""
        self.assertEqual(side_by_side_min_width(100, 80, 6, 12, 150), 198)

    def test_side_by_side_min_width_when_title_is_widest(self):
        """暫定仕様16 §3-4 の横並びでも見出しを切らない。"""
        self.assertEqual(side_by_side_min_width(100, 80, 6, 12, 220), 220)

    def test_default_pane_widths_normal(self):
        """暫定仕様16 §3-6 の既定幅は要求幅と残り幅から求める。"""
        self.assertEqual(
            default_pane_widths(800, 200, 180, 24, MinWidths(100, 80, 120)),
            PaneWidths(200, 396),
        )

    def test_default_keymap_minimum_does_not_change_remainder_formula(self):
        """暫定仕様16 §3-6 の残り幅は補正前の keymap_req で計算する。"""
        self.assertEqual(
            default_pane_widths(800, 90, 180, 24, MinWidths(100, 80, 120)),
            PaneWidths(100, 506),
        )

    def test_default_sequence_minimum_including_negative_remainder(self):
        """暫定仕様16 §3-6 の残り幅不足は負数でも最小幅へ引き上げる。"""
        for main_width in (500, 300):
            with self.subTest(main_width=main_width):
                self.assertEqual(
                    default_pane_widths(main_width, 200, 180, 24,
                                        MinWidths(100, 80, 120)),
                    PaneWidths(200, 120),
                )

    def test_drag_limits_and_clamp_normal(self):
        """暫定仕様16 §3-2 の可動範囲の内外と境界を固定する。"""
        limits = drag_limits(800, 100, 250, 80, 24)
        self.assertEqual(limits, (100, 446))
        for value, expected in ((99, 100), (100, 100), (200, 200),
                                (446, 446), (447, 446)):
            with self.subTest(value=value):
                self.assertEqual(clamp(value, *limits), expected)

    def test_drag_limits_collapse_when_space_is_insufficient(self):
        """暫定仕様16 §3-2 の幅不足では上限を下限に揃える。"""
        limits = drag_limits(400, 100, 250, 80, 24)
        self.assertEqual(limits, (100, 100))
        for value in (50, 100, 150):
            with self.subTest(value=value):
                self.assertEqual(clamp(value, *limits), 100)

    def test_clamp_returns_lower_bound_for_inverted_bounds(self):
        """暫定仕様16 §3-2 の逆転した上下限では下限を返す。"""
        for value in (0, 75, 200):
            with self.subTest(value=value):
                self.assertEqual(clamp(value, 100, 50), 100)

    def test_unchanged_drag_preserves_desired_object(self):
        """暫定仕様16 §3-5 の無効ドラッグで補正後の表示幅を保存しない。"""
        desired = PaneWidths(50, 70)
        for side in ("keymap", "sequence"):
            with self.subTest(side=side):
                self.assertIs(update_desired_after_drag(desired, side, 120, 120),
                              desired)

    def test_changed_drag_updates_only_selected_side(self):
        """暫定仕様16 §3-5 の有効ドラッグは選んだ側の希望幅だけ更新する。"""
        desired = PaneWidths(100, 200)
        for side, expected in (("keymap", PaneWidths(150, 200)),
                               ("sequence", PaneWidths(100, 150))):
            with self.subTest(side=side):
                result = update_desired_after_drag(desired, side, 120, 150)
                self.assertEqual(result, expected)
                self.assertIsNot(result, desired)
                self.assertEqual(desired, PaneWidths(100, 200))

    def test_invalid_drag_side_raises_even_without_width_change(self):
        """暫定仕様16 §3-5 の side 検証は表示幅が不変でも適用する。"""
        for after in (100, 150):
            with self.subTest(after=after):
                with self.assertRaises(ValueError):
                    update_desired_after_drag(PaneWidths(100, 200),
                                              "trigger", 100, after)

    def test_resolve_layout_all_required_boundaries(self):
        """暫定仕様16 §3-7 の収容・縮小順・最小幅・非縮小の8ケースを固定する。"""
        mins = MinWidths(100, 80, 120)
        cases = (
            ("fits", PaneWidths(200, 300), 700, 1000,
             LayoutPlan(200, 300, 620, 700)),
            ("grow_window", PaneWidths(200, 300), 500, 1000,
             LayoutPlan(200, 300, 620, 620)),
            ("exact_screen", PaneWidths(200, 300), 500, 620,
             LayoutPlan(200, 300, 620, 620)),
            ("one_pixel_over", PaneWidths(200, 300), 500, 619,
             LayoutPlan(200, 299, 619, 619)),
            ("shrink_keymap_after_sequence", PaneWidths(200, 300), 350, 400,
             LayoutPlan(160, 120, 400, 400)),
            ("minimums_exceed_screen", PaneWidths(200, 300), 250, 300,
             LayoutPlan(100, 120, 340, 340)),
            ("desired_below_minimums", PaneWidths(1, 2), 300, 1000,
             LayoutPlan(100, 120, 340, 340)),
            ("current_exceeds_screen", PaneWidths(200, 300), 900, 600,
             LayoutPlan(200, 280, 600, 900)),
        )
        for name, desired, current, screen, expected in cases:
            with self.subTest(case=name):
                original = PaneWidths(desired.keymap, desired.sequence)
                self.assertEqual(resolve_layout(desired, mins, 24, 16,
                                                current, screen), expected)
                self.assertEqual(desired, original)


if __name__ == "__main__":
    unittest.main()
