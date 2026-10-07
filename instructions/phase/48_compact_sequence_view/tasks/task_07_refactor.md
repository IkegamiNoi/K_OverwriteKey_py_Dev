# task_07_refactor

## 目的

[提案書 20](../../../modified_proposal/20_refactor_compact_sequence_view.md) の項目 1・2 を実施する（ユーザー承認 2026-10-07・このフェーズ末で実施）。
**presentation 限定・挙動不変のリファクタ**（配置の順序・保存の内容・待ち時間を変えない）。

## 対象範囲（presentation 限定・挙動不変）

### 項目 1: `keyseq/presentation/controllers/call_view_controller.py`

- `host.key == "compact"` の分岐（:77・:89・:104・:155・:194 付近）を、置き場ごとの**配置役**へ寄せる。
  `_CallViewHost` に配置役を持たせ（例: フィールド `layout`）、フル表示は今の処理（`on_font_changed` の測り直し・`_set_minimums`・`_schedule_layout`・イベントの bind・枠を足すときの minsize と `_ensure_desired`）を担う小さな配置役、
  省略表示は `CompactPaneLayout`（`app.compact_pane_layout`）の `schedule_layout` / `on_font_changed` へ委ねる配置役にする。名前は内容を表すもの（雑多名禁止）
- 完了の目安: `grep -c 'host.key == "compact"' call_view_controller.py` が 0〜1。`compact_pane_layout.py` が読む `call_view.hosts["compact"]`・`call_view.desired` の口は変えない
- **配置の予約の順序を変えない**（`_render_host` で欄を足した後に予約する等。phase 48 task_05a の「欄の高さが Tk の都合で戻る」不具合の再発防止）

### 項目 2: `keyseq/presentation/controllers/compact_window_controller.py` / `pane_layout/pane_layout_controller.py`

- `pane_layout_controller.py:20` の `WINDOW_WIDTH_SAVE_DELAY_MS` を `WINDOW_SIZE_SAVE_DELAY_MS` へ改名し、`compact_window_controller.py:107` の `after(500, …)` をこの定数の参照へ（値 500 のまま）。テスト側の参照があれば追随

### テスト

- 挙動不変のため新規テストは原則不要。改名・構造変更で参照が壊れるテストだけ追随する（期待値は変えない）

## 読むファイル

- `instructions/modified_proposal/20_refactor_compact_sequence_view.md`
- `keyseq/presentation/controllers/call_view_controller.py`・`compact_pane_layout.py`（全体）
- `keyseq/presentation/controllers/compact_window_controller.py:95-131`・`pane_layout/pane_layout_controller.py:15-25, 225-260`
- `grep -rn "WINDOW_WIDTH_SAVE_DELAY_MS\|_CallViewHost\|hosts\[" keyseq tests tests_ui` の結果の箇所

## 含まない

- 正本・codebase_map の更新（メインが task_07 完了時に行う）
- deep-reviewer の保留 L8（閉じたときの `_drag_heights`）・その他の挙動変更

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests tests_ui` clean
- tests・tests_ui 全体・`-m tests.smoke_app` pass（件数が task_06a 後と同じ）。実 `config/` を汚さない
- `grep -c 'host.key == "compact"'` が 0〜1 / `grep -rn "after(500" keyseq/presentation/controllers` が 0 件

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視: なし（挙動不変）
