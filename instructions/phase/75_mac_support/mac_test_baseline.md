# macOS のテストの基準線（phase 75 task_07・2026-11-12 / 段階 ② の区切りで再計測 2026-11-13）

暫定 57 §7 の「段階 ② の完了時の基準線」。以降のタスクは、この表より失敗が増えないこと・担当分が減ることで確認する。

## 計測環境

macOS 27.2 / arm64・Homebrew の Python 3.13.18・Tk 9.1.0（aqua）・pyobjc 13.0。`.venv` はリポジトリルート（`../../../.venv/bin/python`）。
macOS の backend はスタブ（フックは `OSError`・キーの解決と送信・マウスは `NotImplementedError`・窓系は `False` / 空）。

## 結果

| | 実行 | 失敗 | エラー | skip |
|---|---|---|---|---|
| tests（`-m unittest discover -s tests`） | 1940 | 6 | 10 | 28 |
| tests_ui（79 モジュールをモジュールごとに別プロセス・下記） | 1271 | 55 | 13 | 0 |

- tests の skip 28 = 既存 16 + task_07 で追加 12（Windows の `keyboard_backend` の 2 モジュール・Windows の Tk keycode 2 件・Windows のパスの意味〔`\` 区切り・大文字小文字の同一視〕8 件）。
- 追加した skip 12 件はいずれも Windows の実装・Windows のパスの意味の検証で、Mac では再有効化しない。Mac の実装（tap・`TkKeyTranslator`）は task_08・task_09 で別にテストを足す。
- 再計測は task_07e の後（HEAD 63de3d93）。task_07 時点（tests 1924・tests_ui 1270 / 64 / 14）から、tests は task_07b・07c・07d・07e のテストの追加分だけ増え、tests_ui は task_07d で失敗 9・エラー 1 が解消。タイムアウト・クラッシュは 0。`test_minimize_grab_custody` の失敗 25 件を含む。

## tests_ui の流し方（Mac）

- **通しで流さない**: `discover -s tests_ui` を 1 プロセスで流すと、実行順に依存して `test_grid_editor_window` の `destroy` で Tk が Segmentation fault で落ちる（単独では落ちない）。
- **モジュールごとに別プロセスで流す**: `for f in tests_ui/test_*.py; do ../../../.venv/bin/python -m unittest tests_ui.$(basename $f .py); done`
- **除外するモジュール**（止まる・モーダルを出す）:
  - `test_task06_keymap_management_ui`・`test_capture_ime_entries`・`test_keyboard_window_left_right` — スタブのキー検証で「不明なキー名」のモーダルが出る（task_09 まで）
  - `test_minimize_grab_custody` — 失敗 25 件、または止まる（揺れる・task_11 まで）
- 上の数は、計測用に messagebox を自動応答にした実行器（リポジトリ外）で除外せずに測った値。実行器の要点: `tkinter.messagebox` の `show*` を `"ok"`・`ask*` を真（`askretrycancel` のみ偽）に差し替え、`sys.path` に cwd を足し、`unittest.defaultTestLoader.loadTestsFromName("tests_ui.<m>")` を流して件数と失敗の ID を出す。モジュールごとに `timeout 600` で別プロセス。

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
| `test_keymap_list_operations` | 3 / 0 | 1 件は同上（貼り付けの検証で `showerror` が 2 回）。2 件（`test_shift_range_commit_activates_underline_row`・`test_refused_singleton_drag_restores_selection_and_active_underline`）は合成のマウスイベント（Shift・B1 の state つき）での選択が期待と違う（aqua の `event_generate` の差と見られる・未確定。task_07e の前から同じ） | task_09（2 件は要調査） |
| `test_task05_overlap_ui` | 2 / 0 | 同上（キーマップの編集の検証） | task_09 |
| `test_app_ui_flows` | 3 / 0 | キーの解決（`ctrl+c` が空） | task_09 |
| `test_action_dialog_key_hold`・`test_keyboard_window_scan_code` | 2 / 0・2 / 0 | Tk の keycode からのテンキーの識別（Windows の keycode 前提・Mac の `TkKeyTranslator` で再判定） | task_09 |
| `test_keyboard_window_left_right` | 0 / 1 | 左右の修飾キーの識別（`right ctrl`） | task_09 |
| `test_capture_ime_entries` | 1 / 0 | キー取得と IME（Q4 の入力ソースの切替） | task_09 |
| `test_prohibited_assign_keys_ui` | 1 / 0 | 割り当て禁止のキーの判定（キーの識別） | task_09 |
| `test_screen_grid_overlay` | 4 / 9 | モニタ一覧が空・クリック透過（スタブ） | task_11 |
| `test_minimize_grab_custody` | 25 / 0 | aqua では最小化で入れ子の transient が隠れない（decisions 2026-11-12） | task_11 |
| `test_modal_grab` | 4 / 0 | モーダルの grab が残る（aqua の窓の扱いの差と見られる） | task_11 で調査 |

task_07 時点の「要調査」7 モジュール（失敗 9・エラー 1。窓の自動幅・ペイン幅・スクロールバー・キーの文字の大きさ・ツールチップ・コンパクト表示・省略表示）は Tk 9 / aqua の窓・フォントの差で、task_07d で解消した（再計測で 0）。
