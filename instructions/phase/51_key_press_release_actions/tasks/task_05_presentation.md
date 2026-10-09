# task_05_presentation

## 目的

`key_hold` の画面側（暫定 35 §5・§7・§8）: アクション編集ダイアログの入力欄・省略表示の要約の書式・ステータス欄の押下中の表示・`HeldInputs` の配線と、フック停止 / キーマップ一時停止 / アプリ終了での解放。
**presentation 中心**（表示名のための domain の小さな関数 1 つと、`HeldInputs.display_names` の表示名をそれに合わせる変更を含む）。application の離す入口（task_04）・送信（task_03）は変えない。JSON 不変。**実装後にユーザーの実機目視**。

## 対象範囲

### 配線 `keyseq/presentation/app.py`
- `HeldInputs(self.input_gateway, on_change=...)` を 1 つ作り、`ActionExecutor(..., held_inputs=...)` と `SequenceRunner(..., held_inputs=...)` の両方へ同じものを渡す（`app.held_inputs` として参照できるように）
- `on_change` は UI スレッドでステータスを更新する（`after` で UI スレッドへ・既存の `trigger_panel.update_status` を呼ぶ）
- `on_close`: `finally` の中で（フック停止が失敗しても）`held_inputs.release_all()` してから `restore_ime_now` / `destroy`（§5「アプリ終了」）
- 構成セットの読込等（`reset_listeners`）は task_04 の `on_runtime_reset` で離れるので追加しない（二重に登録しない）

### 解放の配線 `keyseq/presentation/controllers/hook_controller.py`
- `stop_hook`: 既存の停止処理（`stop_run_to_end` / `cancel_pending_waits` / フックの停止）の後に `held_inputs.release_all()`（UI 編集中の一時停止〔ダイアログ〕・アプリ終了の前処理もこの経路）。解放の例外は既存のエラー表示の口で知らせる（空なら何もしない）
- `toggle_custom_input_enabled`: 一時停止にするとき（`custom_input_enabled = False` の分岐）に `held_inputs.release_all()`

### 表示名 `keyseq/domain/key_hold.py` + `keyseq/application/held_inputs.py`
- domain に `held_display_name(kind: str, name: str) -> str`（キーボード = キー名そのまま・マウス = `マウス左` / `マウス右` / `マウス中`）を足し、`format_key_hold_value` のボタン表示と共有する
- `HeldInputs.display_names` はこの関数で作る（今の `マウスleft` → `マウス左`）。既存テストの期待値（`マウスleft`）は追随

### ステータス欄（§2-9・§7）`controllers/trigger_panel/trigger_panel_controller.py` の `update_status`
- 押下中があるとき「押下中: shift, マウス左」（押した順）を足す。フル表示 = 既存の 1 行の末尾に ` / 押下中: ...`。省略表示 = 1 行目（フック / キーマップ）の末尾に ` / 押下中: ...`（ツールチップの全文にも同じ。1 行化の既存の作法に従う）。押下中が無ければ何も足さない

### 一覧の書式（§7）
- 省略表示の要約 `controllers/action_list_rendering.py` の `format_next_action_summary`: `key_hold` を `format_action_list_item`（task_02）と同じ書式にする（system / file_line と同じく `format_action_list_item` に任せる）。フル表示の一覧・呼び出し先の表示枠が `format_action_list_item` を使っていることを確認し、使っていない経路があれば同じ書式へ

### アクション編集ダイアログ（§7）
- 新規 `keyseq/presentation/dialogs/action_key_hold_fields.py`（`action_control_fields.py` と同じ作りの別モジュール）: 「押す / 離す」の選択（既定 押す）・対象「キー / マウスのボタン」・キー名の入力と「記録」（hotkey の記録と同じ要領で **1 キーだけ**取得）/ ボタン（左 / 右 / 中）と「座標を指定する」チェック + X / Y（mouse_click の入力欄と座標の取得手段を流用）
- `action_dialog.py`: 種類の候補に `key_hold` を加え（すべての文脈で出す）、選んだときこの入力欄を出す・既存の値で開く・OK 時に `domain.key_hold.parse_key_hold` が文字列（エラー）を返す入力は拒否して理由を出す（キーボードは `validate_key_name` でも検査）・結果の dict を組み立てる（`type` / `edge` / `value` か `button`〔+ `x` / `y`〕/ `label`）
- 種類の表示名は既存の候補の書き方に合わせる（既存が種類名そのままなら `key_hold`）

### テスト
- tests（unit）: `held_display_name`・`HeldInputs.display_names` の追随・ステータスの文言の組み立て（関数に切り出せるなら unit で）
- tests_ui: ダイアログで key_hold の行を作る / 編集する（キー・マウス・座標あり）・不正な入力の拒否・一覧と省略表示の書式・押下中の表示（偽の gateway を差して `held_inputs` を操作）・`stop_hook` / キーマップ一時停止 / `on_close` で `release_all` が呼ばれる。**実際のキー入力・マウス操作を送らない**（gateway を差し替える）。App を作るテストは既存の `tests_ui/test_keymap_set_history_flow.py:17-34` の ExitStack 手法で実 `config/` を汚さない

## 読むファイル

- `instructions/history/35_key_press_release_actions.md` §5・§7・§8
- `keyseq/presentation/app.py:115-245, 585-600, 648-665`・`controllers/hook_controller.py:150-200`
- `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py:409-445`・`controllers/action_list_rendering.py`
- `keyseq/presentation/dialogs/action_dialog.py`（全体）・`action_control_fields.py`（別モジュールの手本）
- `keyseq/domain/key_hold.py`・`keyseq/application/held_inputs.py`
- `tests_ui/test_action_dialog_control.py`（ダイアログのテストの手本）・`tests_ui/test_keymap_set_history_flow.py:17-34`

## 含まない

- application の離す入口・送信の変更（task_03・04）
- 正本の改訂（task_07）

## 確認

- 上記テスト（実行は verifier: compileall・tests・tests_ui・smoke）
- reviewer（5 観点）
- **ユーザーの実機目視**（暫定 35 §10 の 8〜11 の一部: ダイアログで作る・テキストエディタで単発の範囲選択・押下中の表示・ダイアログを開くと離れる）
