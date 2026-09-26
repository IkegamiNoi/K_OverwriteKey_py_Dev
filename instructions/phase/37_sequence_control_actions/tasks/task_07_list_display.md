# task_07_list_display

## 目的

暫定仕様 26 §11.3・§11.4（一覧の表示と色分け）を実装し、phase 37 の UI 変更をまとめて実機目視できる状態にする。
- 出力シーケンスの一覧に、ループの周回（実行中は `2/3`・非実行中は `×3`）とカウンターの現在値（`(=5)`）を表示する。
  値は task_01 の `format_action_list_item(..., loop_iteration=, counters=)` に runtime の値を渡して作る（§4.5・domain は変更しない）。
- ネストの色分け: ループの始まりから終わりまでの行の背景を、その行を囲む最も内側のループの深さの色にする（ループ行は自分のループの色・外は色なし・
  対応崩れの行は色なし）。深さ → 色は `loop_depth_style`（青 / 緑 / 橙 × 薄 / 中 / 濃）。選択行はリストボックスの選択色が優先（既定のまま）。
- 省略表示のステータス（「次に実行」の要約）も同じ表示名を使う。
- 周回・カウンターの値は、ステップの実行後と一覧の再描画時に更新される（runner は既に実行後に `select_trigger` → `refresh_actions` を呼ぶ）。

**presentation 中心**。application は runtime 値の読み取り口の追加だけ。domain・runner は変更しない。

## 対象範囲（presentation 中心・application は読み取り口のみ）

### `keyseq/application/app_state.py`

- `loop_iterations_for(trigger_set_id: str, key: str) -> dict[int, int]`: その（trigger_set_id, key）の周回スタックから「始まりの添字 → 周回数」を返す（読み取りのみ・lock 下でコピー）。

### `keyseq/presentation/controllers/action_list_rendering.py`（新規）

`trigger_panel_controller.py`（699 行）へ描画の詳細を足さないため、一覧 1 行の文字列と背景色を作る部分を置く。
- 色の表: `loop_depth_style` の `(hue, shade)` → 背景色（hex）。黒い文字が読める明るさに留める。目安:
  青 `#DCEBFF` / `#C2DBFF` / `#A8CBFF`、緑 `#DDF3DD` / `#C4E8C4` / `#ABDDAB`、橙 `#FFEBD2` / `#FFDDB3` / `#FFCF94`（薄 / 中 / 濃）。
- `build_action_rows(actions, *, loop_iterations: Mapping[int, int], counters: Mapping[str, int]) -> list[tuple[str, str | None]]`:
  各行の（表示文字列, 背景色 or None）を返す。文字列は `format_action_list_item(i, a, loop_iteration=loop_iterations.get(i), counters=counters)`、
  色は `analyze_loops(actions).depth[i]` → `loop_depth_style` → 表（深さ 0・対応崩れ行は None）。
- `format_next_action_summary(index, action, *, loop_iterations, counters) -> str`: 省略表示の要約。`format_action_list_item` と同じ表示名を使う
  （既存種別の要約の文字列は現行と同じになること。mouse_click のドラッグ表示・ラベルの有無の差が出る場合は、現行の要約の文字列を保つ方を優先する）。

### `keyseq/presentation/controllers/trigger_panel_controller.py`

- `refresh_actions`: `build_action_rows` で行を挿入し、背景色があれば `action_list.itemconfigure(i, background=color)`。
  runtime 値は `self._app.state.loop_iterations_for(<アクティブな trigger_set_id>, key)` と `self._app.state.counters` から取る
  （アクティブな trigger_set_id は既存の取り方〔`self._app.keymap_service.get_active_trigger_set_id(self._app.data)` 等〕に合わせる）。
- `get_next_action_summary`: 行の文字列作りを `format_next_action_summary` へ置き換える（位置の求め方は現行のまま）。
- それ以外の処理（位置補正・選択表示・ボタン同期）は変えない。

### テスト

- `tests/test_app_state_loop_iterations.py`（新規・または既存の AppState テストへ追記）: 周回スタックからの対応表・未登録は空。
- `tests_ui/test_action_list_rendering.py`（新規）: `build_action_rows`（周回の実行中 / 非実行中・カウンター値・深さ 1〜9 の色・ループ外と対応崩れは None・既存種別の文字列が不変）/
  `format_next_action_summary`（system / file_line・既存種別の要約が現行と同じ）/ `refresh_actions` で Listbox に背景色が付く（実 Tk の Listbox で `itemcget(i, "background")` を確認）。

### 設計メモ / 制約

- 色は背景だけに付ける（前景色は触らない）。選択色（`selectbackground`）は変えない。
- `action_list_rendering.py` は tkinter を import しない（文字列と色の値を返すだけ。`itemconfigure` はコントローラ側）。
- 表示の更新契機を新しく増やさない（既存の `refresh_actions` の呼び出しで足りる）。

## 読むファイル

- `instructions/history/26_sequence_control_actions.md` §4.5・§11.3・§11.4（仕様）
- `keyseq/domain/sequence_control.py`（`analyze_loops` / `loop_depth_style` / `format_control_value`）/ `keyseq/domain/config.py:404-450`（`format_action_list_item`）
- `keyseq/application/app_state.py`（編集対象・全体）
- `keyseq/presentation/controllers/trigger_panel_controller.py:170-240`（`refresh_actions` / 選択表示）/ `:280-345`（`update_status` / `get_next_action_summary`）
- `tests_ui/test_trigger_panel_controller_action_edit.py`（コントローラ UI テストの手本・先頭 80 行程度）

## 含まない

- 実行側・編集 UI の変更（task_02〜06 で完了済み）
- 正本・codebase_map（色値の記録を含む）→ task_08

## 確認

- 静的確認: `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests tests_ui` がエラー無し。
- 単体・UI: 追加したテストが全 pass。
- 退行: `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests`・`..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` が全 pass、
  `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` が pass。
- `grep -n "tkinter" keyseq/presentation/controllers/action_list_rendering.py` がヒットしないこと。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- **実機目視（ユーザー）**: phase 37 の UI をまとめて確認する（ループ・カウンター・待機・戻す / 先頭へ・file_line の作成と実行、「末尾に追加」、ループの対での追加 / 削除 / 移動、
  周回・カウンター値の表示、ネストの色分け）。目視の指摘は枝番タスクで対応する。
