# task_01_status_hook_state

## 目的

ステータス欄のフックの項目を `ON` / `OFF` / `一時停止` の 3 状態にし、キーマップの項目はアクティブな keymap の名前だけにする（暫定 42 §5）。
一時メッセージ（キーマップの削除・切替・変更なし）が使う `get_active_keymap_text` の文言は変えない。
**presentation 限定（trigger_panel / keymap_panel のコントローラ）・domain / application 不変・スキーマ不変。**

## 対象範囲（presentation のコントローラ 2 ファイル + テスト）

### `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py`

- 新しいメソッド `get_active_keymap_name(self) -> str` を足す: `keymap_service.get_active_keymap_label(data)` を返し、空なら `"(なし)"`。状態の付け足しはしない
- `get_active_keymap_text`（:592-600）は `get_active_keymap_name()` を使う形にしてよいが、**返す文言は今と同じ**（`<名前>（フック停止中）` / `<名前>（一時停止）` / `<名前>` / `(なし)`）

### `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py`

- `update_status`（:409-444）:
  - フックの項目 = `hook.hook_active` が偽なら `OFF`（`custom_input_enabled` に関係なく OFF が優先）/ 真で `hook.custom_input_enabled` が偽なら `一時停止` / それ以外 `ON`
  - キーマップの項目 = `self._app.keymap_panel.get_active_keymap_name()`（`get_active_keymap_text` を使わない）
  - 書式・項目の並び・省略表示の 2 行・`status_full_var` / `status_var` の使い分け・`one_line` の扱いは今のまま（文字列の中身だけが変わる）

### テスト

- `tests_ui/test_app_ui_flows.py`:
  - :138-142 `test_status_shows_hook_off` → `フック: OFF` と `キーマップ: {label}` を確かめ、`（フック停止中）` が含まれないことを確かめる
  - :144-160 `test_status_shows_keymap_paused_when_toggle_is_off` → フル / 省略の両方で `フック: 一時停止` と `キーマップ: {label}` を確かめ、`（一時停止）` が含まれないことを確かめる（`通常トリガー:` の否定は残す）
  - 追加: `hook_active` が偽かつ `custom_input_enabled` も偽のとき `フック: OFF`（OFF 優先）/ 両方真のとき `フック: ON`。元の値は `finally` で戻す（既存テストの作法どおり）
- ステータス欄を見るために `get_active_keymap_text` を差し替えているテストを `get_active_keymap_name` の差し替えへ直す:
  `tests_ui/test_status_tooltip.py:131,158,175,208`・`tests_ui/test_compact_window.py:269`（差し替える値・確かめる内容は今のまま）
- 単体テスト（`tests/`）: `get_active_keymap_text` の文言が今と同じであること（4 通り）と `get_active_keymap_name` の 2 通り（名前あり / `(なし)`）を、
  `tests_ui/test_sequence_control_review_fixes.py:80-100` と同様に `KeymapPanelController.__new__` + `SimpleNamespace` で組んで確かめる（新規ファイル `tests/test_keymap_status_text.py`）

### 設計メモ / 制約

- `tests_ui/test_sequence_control_review_fixes.py:100` の `get_active_keymap_text` の差し替えは一時メッセージ側（`activate_keymap_by_id`・`update_status` は Mock）なので**直さない**
- 一時メッセージの 3 箇所（`keymap_panel_controller.py:315,587,589`）は変えない
- フックの状態の判定を domain / application へ移さない（今と同じく presentation で `hook` の 2 つの印から組む）

## 読むファイル

1. `instructions/history/42_window_size_fit.md` §5
2. `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py:409-444`（`update_status`）
3. `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py:585-600`（`get_active_keymap_text` と呼び出し元）
4. `tests_ui/test_app_ui_flows.py:130-165`
5. `tests_ui/test_status_tooltip.py:125-215`・`tests_ui/test_compact_window.py:260-280`（差し替えの箇所）
6. `tests_ui/test_sequence_control_review_fixes.py:75-100`（コントローラの組み方の手本）

## 含まない

- 省略表示の Expander（task_02）/ フル表示のスクロール・最小の大きさ（task_03・task_04）
- 一時メッセージの文言の変更（暫定 42 §5 で変えない）
- 正本 `features.md` のステータス欄の書式の更新（task_06）

## 確認

（実行は verifier・`.venv` python）
- `compileall -q keyseq main.py tests tests_ui` clean
- `tests/test_keymap_status_text.py` pass（文言 4 通り + 名前 2 通り）
- `tests_ui/test_app_ui_flows.py`・`test_status_tooltip.py`・`test_compact_window.py` pass（3 状態・OFF 優先・名前だけ）
- `unittest discover -s tests` / `-s tests_ui` / `-m tests.smoke_app` 全 pass（件数が減っていない・tests 1656 / tests_ui 1047 以上）
- `grep -n "get_active_keymap_text" keyseq` で呼び出しが一時メッセージの 3 箇所だけ

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視は不要（文言のみ・自動テストで確認）。task_02 の実機目視の際に幅 270 の省略表示で `一時停止` が見えることをあわせて見てもらう
