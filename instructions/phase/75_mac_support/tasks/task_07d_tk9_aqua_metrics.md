# task_07d_tk9_aqua_metrics

## 目的

`mac_test_baseline.md` の「要調査」10 件（tests_ui）を、原因ごとにアプリ側・テスト側で直す（調査 2026-11-12・ユーザー判断 2026-11-12）。
Mac（Tk 9.1 aqua）の既定フォント `.AppleSystemUIFont` は Windows より幅・高さが大きく、Windows のフォントでの数値を前提にしたテストと画面の一部が合わない。また aqua では `<Configure>` と表示の順序、`-topmost` の効き方が Windows と違う。

**レイヤ制約**: presentation とテストのみ。domain / application / infrastructure 不変・JSON スキーマ不変。
**Windows の動作不変**: 下記 3 の既定の高さは Windows では 820 のまま（中身が収まっているため）・4 のフォントの切替は aqua のときだけ。

## 対象範囲

### アプリ側（presentation）

1. **コンパクト表示の初期の高さ**（`test_call_view_compact` の `KeyError: 'compact'`）
   - 実測: aqua では `trigger_panes` の `<Configure>`（高さ 291）が `winfo_ismapped() == 0` の時点で届き、`schedule_layout`（`compact_pane_layout.py:50`）が何もせず、以後呼ばれない。
   - `CompactPaneLayout.install()` で `trigger_panes` に `<Map>` も束ね、`schedule_layout()` を呼ぶ（`_on_configure` と同じく `add="+"`）。既存の条件・処理は変えない。
2. **ツールチップの最前面**（`test_hover_tooltip.test_tooltip_toplevel_is_topmost`）
   - 実測: aqua では `overrideredirect` の窓に表示前に `-topmost` を設定すると無視され（0）、表示後に設定すると効く（1）。
   - `hover_tooltip.py:44-50` の表示処理で、ラベルを pack した後に `window.update_idletasks()` してから `wm_attributes("-topmost", True)` をもう一度設定する（表示前の設定は残す・例外は従来どおり吸収）。
3. **既定の窓の高さを中身に合わせる**（`test_full_view_scroll_areas.test_default_height_fits_and_minimum_height_keeps_contents_reachable`・ユーザー判断）
   - 起動時の既定の高さを `max(820, 中身が収まる高さ)` にする。中身が収まる高さ = `measure_window_min_height(app)` の計算のうち、メイン領域の下限 `ceil(H / 2)` を `H`（`measure_main_area_basis_height(app)`）に置き換えた値（3 枠がスクロールバーなしで収まる高さ）。画面の高さ（`wm_maxsize()`）を上限にする（作業領域は OS の API が要るため使わない。画面を超える高さは `features.md:594` で保証外・reviewer R1 を受けて改訂）。
   - 適用は起動時の初期の幅の適用（`PaneLayoutController.apply_initial_widths`）で 1 回だけ。最大化中・最小化中は変えない。フォントの変更・表示の切替では行わない（既存の最小の高さの規則〔`features.md:588-593`〕はそのまま）。高さは保存しない（従来どおり）。
   - 関数は `pane_measure.py` に `measure_window_fit_height(app) -> int` として足す（30 行以内）。
4. **キーの文字のフォント**（`test_keyboard_key_text.test_home_label_stays_on_one_line_at_unit_27`・ユーザー判断）
   - 実測: `.AppleSystemUIFont` は仕様の下限 7px（`features.md:709`）でも「Home」が 22px で、1u = 27px のキーの内側（約 21px）に収まらない。Helvetica は 7px で 20px。
   - `keyboard_window.py:457` の `font_family` を、aqua のときは `"Helvetica"`、それ以外は従来どおり `TkDefaultFont` の family にする。判定と名前は `tk_platform.py` に `key_label_font_family(widget) -> str` として置く（`is_aqua` を使う）。仕様の下限・縮小の規則（`keyboard_key_text.py`）は変えない。

### テスト側（Windows のフォントでの数値を前提にしていたもの・アプリは仕様どおり）

5. **窓の幅の保存と復元**（`test_pane_window_width_persistence` の 4 件）: Mac ではヘッダの必要幅（＝窓の最小幅）が 1046 で、保存幅 1000 は最小幅未満のためアプリが 1046 に広げる（仕様どおり）。保存幅・期待値を「`max(保存幅, header_window_width)`」で求める形にするか、保存幅を最小幅より大きい値に取る（Windows で同じ検証になること）。`0 != -46` の 1 件も同じ原因かを確かめて同じく直す。
6. **既定のペイン幅**（`test_full_view_panes.test_02_default_layout_matches_original`）: Mac では 780 基準の残り幅でシーケンス枠が最小幅（342）に引き上げられ、トリガー枠が「要求幅 + (窓幅 − 780)」にならない（`pane_width_rules.default_pane_widths` の仕様どおり）。期待値を `default_pane_widths` の結果（最小幅への引き上げを含む）から求める形にする。
7. **省略表示のツールチップ**（`test_child_save_dialog.test_dialog_binds_tooltips_for_all_cells_but_shows_only_ellipsized_text`）: テストが幅 80px を固定で渡しており、Mac のフォントでは短い行の種類のラベルも省略される。幅を、短い方の文字が収まり長い方が収まらない値（フォントで測った値）にする。

### テストの追加

- 1: `install()` が `<Map>` にも束ねることの単体テスト（Mock）
- 3: `measure_window_fit_height` が `H` を使うこと・`apply_initial_widths` で既定の高さが `max(820, fit)` になり画面の高さで頭打ちになること（Mock で測定値を差し替える）
- 4: `key_label_font_family` が aqua で `Helvetica`・それ以外で `TkDefaultFont` の family（`tests/test_tk_platform.py`）

## 読むファイル

- `keyseq/presentation/controllers/compact_pane_layout.py:25-60`
- `keyseq/presentation/hover_tooltip.py:30-60`
- `keyseq/presentation/controllers/pane_layout/pane_measure.py:1-60`・`pane_layout_controller.py:76-110`（`apply_initial_widths`）・`keyseq/presentation/app.py:160-168`
- `keyseq/presentation/keyboard_window.py:450-460`・`keyseq/presentation/tk_platform.py`
- テスト: `tests_ui/test_call_view_compact.py:300-341`・`test_hover_tooltip.py:150-160`・`test_full_view_scroll_areas.py:60-95`・`test_keyboard_key_text.py:126-145`・`test_pane_window_width_persistence.py:60-165`・`test_full_view_panes.py:90-115`・`test_child_save_dialog.py:790-845`
- `instructions/common/spec_detail/features.md:585-605,700-712`

## 含まない

- 最小化の入れ子の transient（task_11）・`test_modal_grab`（task_11 で調査）
- キーの識別・スタブのキー検証による失敗（task_09）
- フォント全体（UI の既定フォント）の変更

## 確認

**Mac**（`../../../.venv/bin/python`。tests_ui は通しで流さない）:

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- 追加したテストが pass
- `-m unittest discover -s tests` の失敗・エラーが基準線（失敗 6・エラー 10）から増えない
- `-m tests.smoke_app` が pass
- tests_ui の `test_call_view_compact`・`test_hover_tooltip`・`test_full_view_scroll_areas`・`test_keyboard_key_text`・`test_pane_window_width_persistence`・`test_full_view_panes`・`test_child_save_dialog` を 1 モジュールずつ流し、失敗・エラーが 0
- 基準線の他の pane・keyboard 系（`test_pane_widths_persistence`・`test_pane_drag_and_window_min`・`test_full_view_header_width`・`test_compact_sequence_view`・`test_keyboard_window_*`）が基準線より悪化しない
- `main.py` を起動し: フル表示の各枠にスクロールバーが出ない高さで開く・コンパクト表示に切り替えて下の枠が適切な高さで出る・キーボードUIを最小の大きさにして「Home」等の文字がキーに収まる・ツールチップがキーボードUIの上に出る（ユーザー目視）

**Windows**: 次に Windows で標準検証 4 種を行う機会にまとめて実施する（既定の高さ 820・キーの文字のフォント・ツールチップが従来どおり）。
- 2026-11-13 実施（M1）: compile clean・tests 1997 件 失敗 0 / エラー 0 / skip 7・tests_ui 1271 件 失敗 0 / エラー 0・smoke OK（verifier）。目視 OK（ユーザー）

## 完了条件

- 上記確認 pass・`mac_test_baseline.md` の「要調査」の行を更新・**reviewer 採用**。
  - 2026-11-12 実施: compile clean・追加テスト pass・tests 1939 件 失敗 6 / エラー 10 / skip 28（基準線どおり）・smoke OK・対象 tests_ui 7 モジュール 失敗 0・pane / compact / keyboard 系は基準線どおり（verifier）。reviewer 修正して採用（R1 = 高さの上限を「画面の高さ」に文書統一・R2 = `test_full_view_panes` の独立検証を復元 → 単独で OK）。目視 ①〜④ OK（ユーザー。④ はダイアログの「?」ボタンのツールチップがキーボードUIの後ろに隠れないことで確認）。
- 実機目視: Mac は本タスクで実施（ユーザー）。
