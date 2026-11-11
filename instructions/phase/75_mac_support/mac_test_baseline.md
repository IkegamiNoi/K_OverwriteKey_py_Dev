# macOS のテストの基準線（phase 75 task_07・2026-11-12）

暫定 57 §7 の「段階 ② の完了時の基準線」。以降のタスクは、この表より失敗が増えないこと・担当分が減ることで確認する。

## 計測環境

macOS 27.2 / arm64・Homebrew の Python 3.13.18・Tk 9.1.0（aqua）・pyobjc 13.0。`.venv` はリポジトリルート（`../../../.venv/bin/python`）。
macOS の backend はスタブ（フックは `OSError`・キーの解決と送信・マウスは `NotImplementedError`・窓系は `False` / 空）。

## 結果

| | 実行 | 失敗 | エラー | skip |
|---|---|---|---|---|
| tests（`-m unittest discover -s tests`） | 1924 | 6 | 10 | 28 |
| tests_ui（モジュールごとに別プロセス・下記） | 1270 | 64 | 14 | 0 |

- tests の skip 28 = 既存 16 + task_07 で追加 12（Windows の `keyboard_backend` の 2 モジュール・Windows の Tk keycode 2 件・Windows のパスの意味〔`\` 区切り・大文字小文字の同一視〕8 件）。
- 追加した skip 12 件はいずれも Windows の実装・Windows のパスの意味の検証で、Mac では再有効化しない。Mac の実装（tap・`TkKeyTranslator`）は task_08・task_09 で別にテストを足す。
- tests_ui の数は task_07 の修正（Control → `primary_modifier`・sashwidth）を反映した値。`test_minimize_grab_custody` の失敗 25 件を含む。

## tests_ui の流し方（Mac）

- **通しで流さない**: `discover -s tests_ui` を 1 プロセスで流すと、実行順に依存して `test_grid_editor_window` の `destroy` で Tk が Segmentation fault で落ちる（単独では落ちない）。
- **モジュールごとに別プロセスで流す**: `for f in tests_ui/test_*.py; do ../../../.venv/bin/python -m unittest tests_ui.$(basename $f .py); done`
- **除外するモジュール**（止まる・モーダルを出す）:
  - `test_task06_keymap_management_ui`・`test_capture_ime_entries`・`test_keyboard_window_left_right` — スタブのキー検証で「不明なキー名」のモーダルが出る（task_09 まで）
  - `test_minimize_grab_custody` — 失敗 25 件、または止まる（揺れる・task_11 まで）
- 上の数は、計測用に messagebox を自動応答にした実行器（リポジトリ外）で除外せずに測った値。

## 残る失敗と担当

### tests

| モジュール | 件数 | 原因 | 担当 |
|---|---|---|---|
| `test_input_gateway_drag` / `_screen_grid` / `_scroll` | 15 | マウス・カーソルのスタブが `NotImplementedError` | task_11 |
| `test_third_party` | 1 | 同梱の第三者ライセンスの表が Windows のビルドの Python 3.14.6 | task_13 |

### tests_ui

| モジュール | 失敗 / エラー | 原因 | 担当 |
|---|---|---|---|
| `test_task06_keymap_management_ui` | 8 / 3 | スタブのキー検証（不明なキー名・`NotImplementedError`） | task_09 |
| `test_keymap_list_operations` | 3 / 0 | 同上（不明なキー名） | task_09 |
| `test_task05_overlap_ui` | 2 / 0 | 同上（キーマップの編集の検証） | task_09 |
| `test_app_ui_flows` | 3 / 0 | キーの解決（`ctrl+c` が空） | task_09 |
| `test_action_dialog_key_hold`・`test_keyboard_window_scan_code` | 2 / 0・2 / 0 | Tk の keycode からのテンキーの識別（Windows の keycode 前提・Mac の `TkKeyTranslator` で再判定） | task_09 |
| `test_keyboard_window_left_right` | 0 / 1 | 左右の修飾キーの識別（`right ctrl`） | task_09 |
| `test_capture_ime_entries` | 1 / 0 | キー取得と IME（Q4 の入力ソースの切替） | task_09 |
| `test_prohibited_assign_keys_ui` | 1 / 0 | 割り当て禁止のキーの判定（キーの識別） | task_09 |
| `test_screen_grid_overlay` | 4 / 9 | モニタ一覧が空・クリック透過（スタブ） | task_11 |
| `test_minimize_grab_custody` | 25 / 0 | aqua では最小化で入れ子の transient が隠れない（decisions 2026-11-12） | task_11 |
| `test_modal_grab` | 4 / 0 | モーダルの grab が残る（aqua の窓の扱いの差と見られる） | task_11 で調査 |
| `test_pane_window_width_persistence` | 4 / 0 | 窓の自動幅の値の差（1046 と 1000 等） | 要調査 |
| `test_full_view_panes` | 1 / 0 | ペインの幅の値の差（381 と 541） | 要調査 |
| `test_full_view_scroll_areas` | 1 / 0 | スクロールバーの表示の判定 | 要調査 |
| `test_keyboard_key_text` | 1 / 0 | キーの文字の大きさ（フォントの寸法） | 要調査 |
| `test_hover_tooltip` | 1 / 0 | ツールチップの表示の状態 | 要調査 |
| `test_call_view_compact` | 0 / 1 | `KeyError: 'compact'` | 要調査 |
| `test_child_save_dialog` | 1 / 0 | 文言・表示の差（差分の 1 行） | 要調査 |

「要調査」は Tk 9 / aqua の窓・フォントの差と見られるが原因を確かめていない（10 件）。担当はユーザー判断で決める。
