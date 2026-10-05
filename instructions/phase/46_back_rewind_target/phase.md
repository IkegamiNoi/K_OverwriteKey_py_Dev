# phase.md

## フェーズ名

戻す・先頭への対象トリガー指定（back_rewind_target）

## フェーズの目的

出力シーケンスの戻す（`back`）・先頭へ（`rewind`）に、対象のトリガーを 1 つ固定で指定するオプションを加える。指定があれば直前のトリガーに関係なく指定先を戻す / 先頭へ移す。
**domain / application / presentation の全レイヤ。JSON は `back` / `rewind` の行に任意キー `target` を足す（無ければ従来どおり直前のトリガー・後方互換）。**

- 起票元: ユーザー要望（2026-10-06・「戻る系のシーケンスを指定のトリガーにだけ使えるようにしたい」）。
- 主入力（暫定仕様）: [32_back_rewind_target.md](../../history/32_back_rewind_target.md)（v0.3・ユーザー確定済 2026-10-06）
- モード: **暫定仕様先行モード**。番号対応: phase 46 / 暫定 32 / decisions 46。

## 確定（ユーザー 2026-10-06）

暫定 32 §2 のとおり。要点: 対象の固定（直前のトリガーに関係なく指定先）・指定は 1 つ・参照中の印等の既存規則をそのまま適用・
OK 時に未選択 / 参照先なし / 自分自身 / 戻す・先頭へだけのトリガーを拒否・表示 `[back] → f5`・キー変更で `target` を追従・参照先なしは呼び出しと同じ表記・
待機 / 処理中 / 一時停止の検査と 2 回押しの破棄を先に行い、戻す段が無ければ戻さず選択も移さない（案 A・不便なら案 B を再検討）。

## スコープ

### 含む

- `target` の 3 状態（無い / 空 / あり）の判定・一覧の表示（§3・§6）
- 実行時の対象の決定（§4）
- 編集ダイアログのチェックボックス・ドロップダウンの流用・操作の切替・OK 時の拒否（§5）
- キー変更での `target` の追従（§2）
- 正本反映（§10）

### 含まない（後送り）

- 暫定 32 §9 のとおり（複数のトリガーの指定・「直前のトリガーが指定先のときだけ動く」意味・省略表示での編集）
- 空の履歴で破棄したときに選択を移す案 B（使ってみて不便なら再検討）

## このフェーズで読むファイル

1. 暫定 `instructions/history/32_back_rewind_target.md`（全文）
2. 正本 `features.md` §4.1（キー変更の追従）・§4.2.6・§4.2.10・§4.6（一覧の表示形式・出力シーケンスの編集）/ `data_schema.md` §5.11.6
3. `keyseq/domain/sequence_control.py:165-200`・`keyseq/domain/call_graph.py`
4. `keyseq/application/sequence_history.py:193-300`（`apply_control` ・ `_back_origin` ・ `_control_group` ・ `_restore_press_group`）・`keyseq/application/sequence_runner/input_acceptance.py:120-210`
5. `keyseq/presentation/dialogs/action_control_fields.py`・`keyseq/presentation/controllers/trigger_panel/action_edit.py`（`call_check` の配線）
6. `keyseq/presentation/controllers/trigger_panel/trigger_row_edit.py:120-145`・`trigger_panel_controller.py`（`_resolve_call_target`）
7. `instructions/common/codebase_map.md`「出力シーケンスの制御アクション」節

## タスク

- task_01: domain — `target` の 3 状態の判定・一覧の表示（§6）・戻す / 先頭へ用の OK 時の検査（§5 の 4 文言・呼び出しの検査とは別関数）・
  キー変更の書き換え（§2。`rename_call_targets` の「call の target だけ」の契約を変えるなら改名か別関数）・複製 / 貼り付けで `target` が保たれることのテスト（§3） —
  **完了**（2026-10-06。codex-implementer・新規 `domain/control_target.py`・reviewer 採用〔軽微: 1 行の back/rewind 以外は拒否しない境界テスト・型注釈 → メインで追記〕・tests 1300 / tests_ui 824 / smoke pass）
- task_02: application — `apply_control` の対象の決定（§4: `target` あり / 空 / 無い・判定の順序・直前のトリガー不変）。
  2 回押しの対象が T になることはテストで担保（`input_acceptance.py` は変更不要の見込み）
- task_03: presentation — 編集ダイアログ（チェック・ドロップダウンの流用・OFF でグレー・操作の切替・拒否）・キー変更の書き換えの配線・
  表示の解決（一覧・省略表示の「次に実行」の要約・呼び出し先の表示枠。`_resolve_call_target` 経由を含む）
- task_04: 正本反映（暫定 32 §10 の昇格・凍結。`data_schema.md` §5.11.6 は空の `target` の文言を呼び出しと行を分けて書く）・`codebase_map.md`・
  `decisions_archive/46_back_rewind_target.md`・current.md の完了記載・`/refactor_check`。起票元 idea なし

## レビュー方針

- 各タスク: `reviewer`（5 観点）・既存テスト（tests / tests_ui / smoke）の通過を完了条件に含める
- 重点: `target` の無い既存の戻す / 先頭への挙動が変わらないか / 呼び出しの検査・表示・書き換えの既存の契約（`call` の `target` だけ）を壊していないか /
  直前のトリガーを更新しないか / ダイアログの共有ウィジェットの切替で状態が漏れないか
- 完了判定前に `deep-reviewer` + `codex-adversarial-reviewer`
- 実機目視（ユーザー）: task_03（ダイアログ・表示・実行の動き）
