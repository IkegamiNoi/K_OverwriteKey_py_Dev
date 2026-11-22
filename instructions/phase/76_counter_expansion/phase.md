# phase.md

## フェーズ名

カウンター機能の拡張（counter_expansion）

## フェーズの目的

カウンターを「ファイルの行」の行番号以外にも使えるようにする。カウンターの行に任意の増やす量（負・0 も可）、カウンター名ごとの開始値（リセットはそこへ戻す）、カウンターの現在値を文字として入力する新しい種類「カウンターの値を入力」を加える。
**対象レイヤ = domain（保存形式・表示）・application（実効値・保留・実行）・config_service（構成セットの保存 / 読込）・presentation（編集ダイアログ・一覧）。JSON スキーマ = 任意キーの追加（行の `amount`・構成セットの `counter_starts`）と種類の追加（`counter_text`）。**

- 起票元: ユーザー要望（2026-11-22）。
- 主入力（暫定仕様）: [58_counter_expansion.md](../../history/58_counter_expansion.md)（v1.0・ユーザー確定済）
- モード: **暫定仕様先行モード**。番号対応: phase 76 / 暫定 58 / decisions 76。

## 確定（ユーザー 2026-11-22）

暫定 58 の §2（1〜12）が正。要点:

- 「カウンター +1」→「カウンター」（`counter_inc` の `amount`・既定 1・負 / 0 も可）。「カウンターを0に」→「カウンターリセット」（開始値へ戻す）。
- 開始値はカウンター名ごとに 1 つ・構成セットの `counter_starts`・ダイアログに今の値を出して上書き。未使用の名前の値 = 開始値。値が入った名前は開始値を変えても今の値のまま。
- 新しい種類 `counter_text`（「カウンターの値を入力」・現在値をそのまま入力・書式指定なし）。
- 受容: またがる保存の部分失敗（§3.6）・手書きの `amount` の互換例外（§3.5）。

## スコープ

### 含む

暫定 58 の §3〜§5（データモデル・実行の規定・UI）。

### 含まない（後送り）

暫定 58 の §8（条件分岐 = idea_37・値の表示欄と手での変更・counter_text の書式・使われない開始値の掃除・値の永続化）。

## このフェーズで読むファイル

1. `instructions/history/58_counter_expansion.md`（主入力）
2. `instructions/common/codebase_map.md` の「出力シーケンスの制御アクション（system / file_line・phase 37）」の節と、phase 45・50 の記述（呼び出し・選んでから実行の置き方）
3. `instructions/common/spec_detail/data_schema.md` §5.1〜5.3・§5.11.1・§5.11.6〜5.11.8、`features.md` §4.2・§4.2.2・§4.2.6・§4.2.8・§4.2.9・§4.6
4. `keyseq/domain/sequence_control.py`・`keyseq/domain/config.py`
5. `keyseq/application/app_state.py`・`sequence_steps.py`・`sequence_history.py`・`call_context.py`・`call_view.py`・`action_executor.py`・`sequence_runner/`（`linked_call.py`・`call_wait.py`・`call_run_to_end.py`・`run_to_end.py`・`send_wait.py`・`wait_stop.py`・`sequence_runner.py`）
6. `keyseq/application/config_service/split_loading.py`・`split_payloads.py`
7. `keyseq/presentation/dialogs/action_dialog.py`・`action_control_fields.py`・`controllers/trigger_panel/action_edit.py`・`controllers/action_list_rendering.py`・`app.py`・`controllers/config_io/keymap_set_io.py`
8. `keyseq/shared/i18n/locales/ja.json`・`en.json`・ヘルプ（`keyseq/presentation/help/content/help_ja.json`・`help_en.json`）

## タスク

1. task_01: **完了（2026-11-22・codex-implementer・reviewer 採用）** 保存形式 — `counter_starts` の正規化（§3.3 の順序）と構成セットの読込・保存・単一 JSON の Import / Export、`amount` の判定関数（domain）
2. task_02: **完了（2026-11-22・codex-delegating-implementer〔Sol medium〕・reviewer 採用）** 実行 — `AppState` の開始値と実効値の 1 関数・`amount` の反映・リセットを開始値へ・保留の型 `(op, name, amount)` を全経路で・無視された押下の巻き戻しで初めて入った名前を消す（§4）
3. task_03: **完了（2026-11-22・codex-implementer・reviewer 採用）** 新しい種類 `counter_text` — 実行（`ActionExecutor`）・種別の検証と文言・通知（§3.4）
4. task_04: 表示 — 一覧の書式（§5.3）・実効値と開始値を受ける書式の関数・呼び出し先の表示枠の写し・開始値の変更と構成セットの置き換えでの描き直し
5. task_05: 編集 UI — ダイアログ（増やす量・開始値・名前の変更での入れ替え・`counter_text` の種類の候補）・コントローラでの開始値の確定と未保存・候補の名前・構成セットを置き換える全経路での `AppState` への同期（サンプル設定に戻すを含む）・名称の文言（ja / en）とヘルプ（§5）
6. task_06: 統合確認 — 標準検証 4 種・受け入れ条件 §7 の照合・実機目視（ユーザー）
7. task_07: 正本反映 — 暫定 58 の昇格（§9）と凍結・`decisions_archive/76_counter_expansion.md`・`codebase_map.md`・`current.md` の完了記載・`/refactor_check`

## レビュー方針

- 各タスクは `reviewer`（`.claude/rules/review.md` の 5 観点）。task_06 は `deep-reviewer` + `codex-reviewer`、フェーズ完了判定前は `deep-reviewer` + `codex-adversarial-reviewer`。
- 本フェーズ固有の観点:
  - **実効値を通らない経路が残っていないか**（`counters.get(name, 0)` の直読み・保留の 2 要素の組の残り）。task_02 の受け入れ条件に経路ごとのテスト（暫定 58 §7.4・§7.5）を入れる
  - domain が `AppState` を読まない・application が presentation の構成セットのデータを読まない（依存方向・§4.1）
  - 既存データの互換（`amount` の無い行・`counter_starts` の無い構成セット・呼び出しの行の `step` を無視・§7.1）
  - 画面の文言は `ja.json` と `en.json` の両方・`ui_terms.md` の表記
