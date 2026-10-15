# task_01_left_right_lookup

## 目的

キーボードUI で左右の修飾キー（Shift・Ctrl・Alt・Windows）の枠を左右別のキー名で引き、表示・色・編集・右クリックのクリア・編集中の強調とタイトルを枠ごとにする（暫定 43 §3.1・§3.2・§3.4・§5-1〜5）。
**presentation 限定（`keyboard_window.py`）・domain / application / 入力の経路 不変・JSON スキーマ不変。**

## 対象範囲（presentation・キーボードUI の対応表 + テスト）

### `keyseq/presentation/keyboard_window.py`

- `_LOOKUP_KEY_BY_ID`（:27-35）の修飾キーの 8 行を暫定 43 §3.1 の表のとおりにする:
  `shift_l` → `shift` / `shift_r` → `right shift` / `ctrl_l` → `ctrl` / `ctrl_r` → `right ctrl` / `alt_l` → `alt` / `alt_r` → `right alt` / `windows_l` → `left windows` / `windows_r` → `right windows`
- 修飾キー以外の行（`grave` 等）は変えない。`alt_gr` の行・禁止の色は**このタスクでは足さない**（task_02・task_03）
- `redraw`・`_key_bounds`・`_begin_edit`・`_on_canvas_right_click`・`_update_title` はこの対応表を通したキー名を使っているので、対応表の変更だけで枠ごとになることを確かめる（追加の変更が要れば最小限）

### テスト（新規 `tests_ui/test_keyboard_window_left_right.py`）

作法 = `tests_ui/test_task06_keymap_management_ui.py:125-146`（`app.layout.open_keyboard_window()` → `app.layout.keyboard_window`）。App はクラスで共有・`write_startup` / 保存系はパッチして config を書かない。
既定レイアウト（`keyboard_layouts.py` の組み込み・左右の修飾キーの id を持つ）で確かめる:
1. 左右の枠のキー名: `_key_bounds` に `ctrl` と `right ctrl`・`shift` と `right shift`・`alt` と `right alt`・`left windows` と `right windows` がそれぞれ別に入り、`windows` という共通名は入らない
2. 表示: アクティブなキーマップに `ctrl` → `a` と `right ctrl` → `b` を入れて描き直すと、左の枠の文言が `a`・右の枠の文言が `b`（`_display_map` と、各枠の矩形の中の文字を canvas から読むか、`_key_bounds` の座標で区別して確かめる）
3. 編集: 右 Ctrl の枠の座標で左クリック → `_editing_source_key == "right ctrl"`・タイトルが `編集中: right ctrl` を含む。キーを押して割り当てる（既存の割り当ての経路 `_on_key_press` → `assign_keymap_from_keyboard_ui`）と、キーマップに `right ctrl` の割り当てができ、`ctrl` は変わらない
4. 右クリック: `ctrl` と `right ctrl` の両方がある状態で右 Ctrl の枠を右クリック → `right ctrl` だけ消え `ctrl` は残る
5. 既存の割り当ての扱い: `ctrl` / `shift` / `alt` の割り当ては左の枠だけに出る / 元キー `windows` の割り当てはどの枠の文言にも出ない
- 各テストは `addCleanup` でキーマップのデータ・キーボードUI を元へ戻す（閉じる）

### 設計メモ / 制約

- 既存テスト（`test_task05_overlap_ui.py:242-247`・`test_task06_keymap_management_ui.py:138-146`・`test_trigger_effective_row.py:158-162`）は `_display_map` / `_kind_map` を通常のキーで見ている。通らなければ実装側を直す（期待の書き換えはしない）
- 入力の経路（`input_router`）・取得（`tk_keys`）・キーマップの照合は変えない

## 読むファイル

1. `instructions/history/43_keyboard_ui_left_right_modifiers.md` §3.1・§3.2・§3.4
2. `keyseq/presentation/keyboard_window.py`（全体）
3. `keyseq/presentation/keyboard_layouts.py:80-125`（既定レイアウトの修飾キーの行）
4. `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py:606-650`（割り当て・クリアの入口）
5. `tests_ui/test_task06_keymap_management_ui.py:1-60,125-146`（テストの作法）

## 含まない

- 割り当て禁止（禁止の色・編集しない・入口の拒否・切替キー）（task_02）
- 標準の id `alt_gr`・`de.json`（task_03）/ `jis.json` の追加（task_04）
- 正本反映（task_06）

## 確認

（実行は verifier・`.venv` python）
- `compileall -q keyseq main.py tests tests_ui` clean
- `tests_ui/test_keyboard_window_left_right.py` pass（上記 1〜5）
- `tests_ui/test_task05_overlap_ui.py`・`test_task06_keymap_management_ui.py`・`test_trigger_effective_row.py`・`test_app_ui_flows.py` が書き換えなしで pass
- `unittest discover -s tests` / `-s tests_ui` / `-m tests.smoke_app` 全 pass（件数が減っていない）

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視は task_04 でまとめて実施
