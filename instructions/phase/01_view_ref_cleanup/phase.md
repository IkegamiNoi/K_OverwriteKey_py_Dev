# phase.md

## フェーズ名

View 参照の後始末（view_ref_cleanup）

## フェーズの目的

計画04（Widget分割・フォルダ再編）で意図的に残した **View まわりの残存参照 2 件を解消する**。

- **対象レイヤ: presentation のみ**（+ 参照経路のみ tests_ui）
- **スキーマ変更: なし**（JSON・保存フォーマットに触れない）
- **挙動不変（文言・レイアウト・state 遷移を 1 文字も変えない）**。純粋な内部リファクタであり、
  正本仕様書（`instructions/common/spec_detail/`）の変更を伴わない

- 起票元: ユーザー要望（2026-07-17）。`instructions/phase/current.md`「別タスク化候補」の
  機械的後始末 2 件（計画04 W7 の次期課題のうち、設計判断を伴わないもの）。
- 主入力（暫定仕様）: なし（直接改訂モード）
- モード: **直接改訂モード**。番号対応: phase 01 / 暫定 なし / decisions は `.claude_data/state/decisions.md`
  に記録し、完了時に `decisions_archive/01_view_ref_cleanup.md` へ集約。

### モード選択の根拠

`.claude/rules/spec_change_workflow.md`「モードの選択」の直接改訂条件を**すべて**満たす
（局所的〔対象 4 ファイル・数行〕/ 文言確定済み / タスク 1〜2）。そもそも仕様変更が発生しないため、
暫定仕様書は不要。

## 確定（ユーザー 2026-07-17）

- 計画04 の次期課題は **1 件 1 フェーズにせず 3 フェーズに分割**する。順序は
  **本フェーズ（後始末）→ [idea_01](../../backlog/idea_01_hotkey_validation_to_domain.md)（hotkey 検証を domain へ）
  → [idea_02](../../backlog/idea_02_startup_font_settings_cleanup.md)（起動設定/フォント）**。
- 本フェーズは機械的・挙動不変の 2 件のみを扱う（設計判断を伴うものは idea へ分離済み）。
- フェーズ名は Claude 判断（`01_view_ref_cleanup`）。

## スコープ

### 含む

1. **`views/status_bar.py` の生やし解消**（`app.runtime_status_frame` / `app.status_bar` → ローカル変数化）
   - 計画04 W5 では「ボタン/入力ウィジェットの逆流ではない」として対象外にした残り。
   - 調査済み: この 2 属性は `build_status_area` 関数内でしか使われておらず**読み手なし**
     （W5 で処理した write-only 生やしと同型）。
2. **View の `trigger_list` alias 削除**（`full_view.py` / `compact_view.py` の
   `self.trigger_list = self.trigger_box.trigger_list`）+ tests_ui の参照経路変更
   - 計画04 W3/W4 で外部契約保持のために置いた暫定措置。W5 で production 側は
     `TriggerPanelController._trigger_lists`（登録方式）へ移行済みのため、
     **現在 alias に依存しているのは tests_ui のみ**。

### 含まない（後送り）

- [idea_01](../../backlog/idea_01_hotkey_validation_to_domain.md) / [idea_02](../../backlog/idea_02_startup_font_settings_cleanup.md) の内容
- **app.py の行数削減そのもの**（489 行 / 目安 300 行超過。本フェーズの 2 件は app.py をほぼ減らさない）
- **`action_list` の参照経路**（`app.full_view.action_list`。計画04 §1.3-2 の「App → View → Widget パス」を
  既に満たすため据え置きと判断済み。`decisions.md`【W3/W4】参照）
- 挙動・文言・レイアウト値・エラーメッセージの変更
- tests_ui の**アサーション**変更（参照経路の書き換えのみ可）

## このフェーズで読むファイル

実装時はこれ以外を広く読まないこと。

1. `keyseq/presentation/views/status_bar.py`（task_01 の対象。全 28 行）
2. `keyseq/presentation/views/full_view/full_view.py`（task_02: alias の所在）
3. `keyseq/presentation/views/compact_view/compact_view.py`（task_02: alias の所在）
4. `keyseq/presentation/views/full_view/trigger_box.py` / `views/compact_view/trigger_box.py`
   （`trigger_list` の所有者。登録呼び出しの確認）
5. `keyseq/presentation/controllers/trigger_panel_controller.py`
   （`_trigger_lists` 登録方式で動作し alias に依存していないことの確認）
6. `tests_ui/test_app_ui_flows.py`（40-41 行付近。参照経路変更の対象）
7. `.claude_data/state/decisions.md`「2026-07-15〜07-17 (計画04)」節
   （【W3/W4】alias を置いた経緯 /【W5】write-only 生やしの扱い）

## タスク

1. **task_01_status_bar_local_vars** — `views/status_bar.py` の `app.runtime_status_frame` /
   `app.status_bar` をローカル変数化し、App への生やしを削除する。
2. **task_02_remove_trigger_list_alias** — `full_view.py` / `compact_view.py` の `trigger_list` alias を削除し、
   `tests_ui/test_app_ui_flows.py` の参照経路を `app.<view>.trigger_box.trigger_list` へ変更する。
   （依存: task_01 とは独立だが、1 タスク 1 コミットのため順に実施）
3. **task_03_finalize_records** — 正本反映・記録タスク（最終）。
   `decisions.md` への判断記録 → `decisions_archive/01_view_ref_cleanup.md` へ集約 /
   `current.md` の完了記載・次採番更新（「別タスク化候補」から本フェーズ分を削除）/
   `/refactor_check` の実行と判定結果の完了報告への記載。
   ※ 起票元 idea が無いフェーズのため `backlog/INDEX.md` の更新は不要。

## レビュー方針

共通観点は `.claude/rules/review.md`（仕様適合性 / 依存方向 / 責務分離 / 不要変更 / チェック漏れ）。
本フェーズ固有の観点:

- **task_01**: 生やし削除前に「本当に読み手がいないか」を **grep で再確認**すること
  （調査時点では `build_status_area` 内のみ。App 属性を消すため、見落としは即 AttributeError）。
  ウィジェットの親子関係・pack/grid 引数・style・textvariable を 1 文字も変えないこと。
- **task_02**: production（`trigger_panel_controller`）が `_trigger_lists` 登録経由で動作し、
  **alias に依存していない**ことを確認してから削除すること。
  tests_ui は**参照経路のみ**変更し、**アサーションは変更しない**（`size()` の期待値等）。
- **共通**: 標準検証 4 項目（`.venv` python で compileall / tests / tests_ui / smoke。
  ベースライン = compile clean / tests 59 / tests_ui 9 / smoke pass）。
- **手動確認**（挙動不変の担保）: ステータスバー表示（ファイル状態 / 一時メッセージ / 「ステータス」欄）と、
  フル・省略両ビューでのトリガー一覧の表示・選択共有。
- 実装は `codex-implementer` へ委任（`.claude/rules/agent_selection.md`）。標準検証は `verifier`、
  コミットはメインセッション。
