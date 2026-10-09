# phase.md

## フェーズ名

キーの押下 / 解放アクション（key_press_release_actions）

## フェーズの目的

出力シーケンスにキー（またはマウスのボタン）を押したままにする行と離す行（種類 `key_hold`）を加え、押したままのキーを止まる経路すべてで自動で離す安全策と、押下中の表示を入れる。
**domain / application / infrastructure / presentation。アクションの JSON に種類 `key_hold`（`edge` / `value` / `button` / `x` / `y`）を追加（後方互換・読込の正規化は変えない）。**

- 起票元: [idea_23](../../backlog/idea_23_key_press_release_actions.md)（2026-09-18 ユーザー要望・2026-10-09 着手決定）。
- 主入力（暫定仕様）: [35_key_press_release_actions.md](../../history/35_key_press_release_actions.md)（v0.3・ユーザー確定済 2026-10-10。§4.4・§6 は task_01 の probe の結果で見直す）
- モード: **暫定仕様先行モード**。番号対応: phase 51 / 暫定 35 / decisions 51。

## 確定（ユーザー 2026-10-09〜10）

暫定 35 §2 の 1〜13 が正（本書に再掲しない）。要点: 押下をまたいで押したままでよい / 止まる経路すべてで離す（停止の行の区切り・戻す・呼び出し先の末尾・押下の合間は離さない）/
種類 1 つで押す・離すを選ぶ / 単キー + マウスのボタン（座標の指定も可）/ 最上段の末尾・一時停止・先頭へで離す / 実行を終えるエラーは知らせる前に離す / 押下中をステータス欄に表示。

## スコープ

### 含む

- 暫定 35 §3〜§8 の実装とテスト（データ §3・送信と押下中の記録 §4・自動で離す §5・UI §7・責務 §8）
- 実装前の probe（§6）と、その結果による本書の見直し
- 正本反映（暫定 35 §12）

### 含まない（後送り）

- 暫定 35 §11 のとおり（組み合わせを 1 行で・マウスの移動だけのアクション・再開で押し直す・text で離れたキーの押し直し・強制終了での解放）

## このフェーズで読むファイル

1. `instructions/history/35_key_press_release_actions.md`（全体）
2. 送信: `keyseq/infrastructure/input_gateway.py`（`press_key` / `release_key` / `validate_key_name` / `drag_mouse`）・`keyseq/application/action_executor.py:83-130, 183-230, 260-290`
3. 実行: `keyseq/application/sequence_runner/sequence_runner.py`（`_run_single_action`・`_cancel_pending_steps`）・`run_to_end.py`（`stop_run_to_end`・一時停止）・`input_acceptance.py`（`discard_paused`）・`call_wait.py`（`_fail_single_call`）・`linked_call.py`（`_propagate_linked_completion`）・`wait_stop.py`・`keyseq/application/sequence_steps.py`（`advance` の末尾と回り込み）・`keyseq/application/app_state.py:53`（`reset_indices`）
4. 状態を消す契機の呼び出し元（presentation・task_04 で解放の置き場を決める材料）: `controllers/config_io/keymap_set_io.py:78, 571, 619, 664, 700`・`config_io/trigger_set_file_io.py:288`・`keymap_panel/keymap_panel_controller.py:325, 455`・`trigger_panel/effective_row_transition.py`・`trigger_panel/trigger_row_edit.py:118`
5. 停止の入口（presentation）: `keyseq/presentation/controllers/hook_controller.py:158-195`・`keyseq/presentation/app.py`（`perform_action` の配線・`on_close` :648・ステータス）
6. domain・UI: `keyseq/domain/config.py`（`format_action_list_item`）・`keyseq/domain/sequence_control.py`・`keyseq/presentation/dialogs/action_dialog.py`・`action_control_fields.py`（別モジュールの手本）・`keyseq/presentation/controllers/action_list_rendering.py`
7. 正本: `instructions/common/spec_detail/data_schema.md` §5.11・`features.md` §4.2.1〜4.2.10・`key_input.md` §7.7

## タスク

- task_01: probe（暫定 35 §6 の 1〜3: 合成の修飾キーを押したままのトリガー判定・text / 改行 / バックスペースへの影響・左右の ctrl / alt の押し離し）。安全な送り先（テスト用の Tk の入力欄）で `.venv` の小スクリプトを走らせて実測し、結果で §4.4・§6 を見直す（違えばユーザー確認）。メイン + verifier
- task_02: domain — 種類 `key_hold` の定数・検証（`edge` / `value` / `button` / `x` / `y` の実行時エラーの判定）・一覧の書式（1 関数）とテスト（§3・§7 の書式）
- task_03: infrastructure + application — InputGateway のマウスのボタンの押す / 離す（座標への移動・FAILSAFE）・押下中の集合 `HeldInputs`（同じキーの判定・送る前の記録・失敗時の補償）・ActionExecutor の `key_hold` の実行（持ち主の受け取り・止まる系のエラー・知らせる前の解放）とテスト（§4・§8）
- task_04: application — 自動で離す入口（§5 の表: 連続実行の終わり・一時停止・破棄・待機の取り消し・先頭へ・状態を消す契機〔キー変更は旧キーの分〕・末尾の時点・連動の末尾・実行を終えるエラー）と runner から持ち主を渡す配線とテスト（§5）。
  **状態を消す契機の解放は application 側で受ける**（presentation の各呼び出し元に解放を書き足さず、状態を消す application の処理〔`AppState.reset_indices`・トリガーの状態の消去等〕から解放の口を呼ぶ。入口の実体は task_04 の起票時に特定する。`_cancel_pending_steps` は `sequence_runner.py:195` と `wait_stop.py:36` の 2 か所にあるため実体を特定する）
- task_05: presentation — ダイアログの `key_hold` の入力欄（別モジュール）・一覧 / 省略表示 / 呼び出し先の表示枠の書式・ステータス欄の押下中の表示・フック停止 / キーマップ一時停止 / アプリ終了の解放の配線とテスト（§5・§7）。**実装後にユーザーの実機目視**
- task_06: 統合確認（tests / tests_ui / smoke・deep-reviewer + codex-reviewer）と**ユーザーの実機目視**（暫定 35 §10 の 8〜11）
- task_07: 正本反映（暫定 35 §12 の昇格・凍結）・`decisions_archive/51_key_press_release_actions.md`・decisions.md の索引・current.md の完了記載・idea_23 を INDEX_done へ・`/refactor_check`

## レビュー方針

- 各タスク: `reviewer`（5 観点）・既存テスト（tests / tests_ui / smoke）の通過を完了条件に含める
- 重点: 押したままのキーが**どの止まる経路でも残らないか**（§5 の入口を通る全経路・知らせる前に離すか）/ 離さない契機（停止の行・戻す・押下の合間・呼び出し先の末尾）で離していないか /
  同じキーの判定（左右・表記違い）/ キー変更で旧キーの分を離すか / 送信の失敗の補償 / 持ち主（最上段）の受け渡しが呼び出し・連動・有効な行の交代で正しいか / 既存の種類の挙動（hotkey・text の value・エラーの止まる系 / 止まらない系）を変えていないか /
  スレッド（解放は UI スレッド）/ テストが実際の入力を送らないか（偽の gateway）・実 `config/` を汚さないか
- 統合確認（task_06）: `deep-reviewer` + `codex-reviewer` / 完了判定前（task_07）: `deep-reviewer` + `codex-adversarial-reviewer`
- 実機目視（ユーザー）: task_05・task_06（テキストエディタでの範囲選択・各停止経路での解放・マウスのドラッグ・押下中の表示）
