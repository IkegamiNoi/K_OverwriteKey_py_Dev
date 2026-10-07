# phase.md

## フェーズ名

ステータスの見切れのツールチップ（status_truncation_tooltip）

## フェーズの目的

ステータス欄（フック / キーマップ / 選択中のトリガーの状態）とステータスバー（左: ファイル状態 / 中央: 一時メッセージ）の文言が見切れているとき、マウスを乗せると全文をツールチップで出す。
子ファイル保存ダイアログ専用のツールチップを presentation 層の共有部品へ昇格して両方から使う。
**presentation 限定・domain / application 不変・JSON スキーマ不変・config.json 不変。**

- 起票元: [idea_40](../../backlog/idea_40_status_truncation_tooltip.md)（2026-10-07・phase 48 実機目視時のユーザー要望）。
- 主入力（暫定仕様）: なし（直接改訂モード）。正本 `features.md` の §4.5「一時的な案内」（:394）・§4.6「省略表示のウィンドウ」の「ステータスの行数の固定」（:482）へ task_02 で追記する（「欄は 1 行化・ツールチップだけ改行入りの元の文言」の差を明記し、:482 と矛盾に読めないようにする）。
- モード: **直接改訂モード**（presentation の 1 機能・正本は局所・タスク 2）。番号対応: phase 49 / 暫定なし / decisions 49。

## 確定（ユーザー 2026-10-07）

1. **対象 = フル表示・省略表示の両方**の、ステータス欄・ステータスバーの左（ファイル状態）・中央（一時メッセージ）。**見切れているときだけ**出す（見切れていなければマウスを乗せても出さない）
2. **出す文言 = 1 行化する前の元の全文（改行を残す）**。省略表示の欄は従来どおり（phase 48）: ステータス欄は 2 行のまま各値〔フック状態・キーマップ・選択・次の行〕の中の改行を空白に / ステータスバーは全体を 1 行に。ツールチップだけ改行を含む元の形で出す。フル表示は欄の文言と同じ
   （理由: 1 行化は欄の高さを固定するためだけのもの・改行と空白を区別できる・複数行のメッセージが読みやすい。縦に長くなり得るのは受容）
3. **ツールチップを出している間に文言が変わったら、新しい全文へ追従する**（開いたまま中身を差し替える）。見切れなくなった・文言が空になったら閉じる
4. 出し方・閉じ方は子ファイル保存ダイアログのツールチップと同じ（マウスが入ったら出す・出たら / クリックで閉じる・マウス位置の右下）（メイン判断・既存の作法の踏襲）

## スコープ

### 含む

- 子ファイル保存ダイアログの `_bind_tooltip` を presentation 層直下の共有モジュールへ昇格（子ファイル保存ダイアログの挙動は不変）。文言の差し替え（確定 3）に対応する形にする
- ステータス欄・ステータスバー 2 か所への適用・元の全文の受け渡し（省略表示の 1 行化の前の文言）とテスト
- 既存テストの追随（`tests_ui/test_child_save_dialog.py` の `_bind_tooltip` の差し替え箇所。旧位置に転送用の口を残さない＝恒久的な互換レイヤーの禁止）
- 正本 `features.md`・`codebase_map.md` への追記

### 含まない（後送り）

- ステータス以外のラベル・一覧へのツールチップ（キーボード選択のドロップダウン・ボタン等）
- ステータス欄の折り返し・横スクロール・幅の自動調整
- 表示までの遅延（ホバーしてから一定時間後に出す）の導入

## このフェーズで読むファイル

1. `keyseq/presentation/controllers/config_io/child_save_dialog.py:113-188`（`_add_text_cell`・`_bind_tooltip`）
2. `keyseq/presentation/views/status_bar.py`（全体）・`keyseq/presentation/ui_vars.py`（`status_var` / `file_status_var` / `flash_message_var`）
3. `keyseq/presentation/app.py:306-345`（`_update_file_status`・`_status_bar_text`・`_refresh_status_bar`・`_set_flash_message`・`_clear_flash_message`）
4. `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py:405-440`（`update_status`・省略表示の 1 行化）・`keyseq/presentation/status_text.py`
5. テスト: `tests_ui/test_child_save_dialog.py:788-830, 1306-1340`（ツールチップの検査の流儀）・`tests_ui/test_compact_window.py`（省略表示のステータスの検査）
6. 正本 `features.md` §4.5（一時的な案内）・§4.6「省略表示のウィンドウ」・「子ファイル保存ダイアログ」のツールチップの条項

## タスク

- task_01: presentation — ツールチップの共有化（子ファイル保存ダイアログは挙動不変）・ステータス欄 / ステータスバーへの適用（見切れ判定・元の全文・表示中の追従）とテスト・`codebase_map.md` の該当行。**実装後にユーザーの実機目視** — **完了**（2026-10-07・ユーザー実機目視 OK・codex-delegating-implementer〔Luna サブエージェント使用〕・reviewer 完了可〔N1 = 全文の書き込みの変数名を文字列で組み立てない → メインで修正〕。検証で子ファイル保存ダイアログのテスト 1 件の追随漏れ〔文言が callable になった〕をメインで修正。tests 1325 / tests_ui 890 / smoke pass）
- task_02a: presentation — 完了判定前レビューの指摘対応（乗せている間に見切れたら出す・誤って閉じても復帰〔Codex 敵対的 medium・deep-reviewer L1〕/ ツールチップを最前面に〔deep-reviewer M1〕/ 終了時の trace_remove の例外の吸収〔L5〕）とテスト。**実装後にユーザーの実機目視（常に最前面オンを含む）** — **実装・検証済・実機目視待ち**（2026-10-07・codex-implementer・reviewer 修正要〔範囲外のマウス追従＝窓を動かす部分を除外〕→ メインで修正。検証でテストの後始末〔乗せた状態の解除漏れ〕をメインで修正。変異検査: 修正前の refresh で「狭めると出る」は落ちる / Codex の順序の統合テストは修正前でも通る＝実機相当では再現せず・復帰の仕組みは単体テストで確認。tests 1325 / tests_ui 895 / smoke pass）
- task_02: 正本反映（`features.md` へ確定 1〜4・`codebase_map.md`）・`decisions_archive/49_status_truncation_tooltip.md`・decisions.md のアーカイブ索引・current.md の完了記載・idea_40 を INDEX_done へ・`/refactor_check`

## レビュー方針

- 各タスク: `reviewer`（5 観点）・既存テスト（tests / tests_ui / smoke）の通過を完了条件に含める
- 重点: 子ファイル保存ダイアログのツールチップが従来どおり（見切れたセルだけ・全文）/ 見切れ判定がフォント変更・窓の幅の変更・フル ⇔ 省略の切替で正しい /
  省略表示で欄は 1 行・ツールチップは改行入りの全文 / 一時メッセージの自動消去（4 秒）・実行の進行で文言が変わったとき追従・閉じる / ツールチップの Toplevel が残らない（窓を閉じる・表示切替）
- 完了判定前に `deep-reviewer` + `codex-adversarial-reviewer`
- 実機目視（ユーザー）: task_01（フル・省略で幅を狭めて乗せる・見切れていなければ出ない・一時メッセージの表示中・実行中の追従）
