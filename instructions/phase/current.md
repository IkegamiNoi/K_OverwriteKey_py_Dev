# Current Phase

このファイルは、現在どのフェーズ定義を読むべきかを示すためのルーティングファイルです。
**完了フェーズの要約はここに蓄積しない**（`.claude_data/state/decisions.md`「アーカイブ索引」+
`decisions_archive/<phase>.md` が正）。

## 現在の参照先

- 現在フェーズは**未確定**。次フェーズ開始時に `/phase_start` で起票し、ここを差し替える。
- テンプレート導入前の経緯・過去仕様は `instructions/history/archive/` を参照（凍結済み）。
  過去のリファクタ計画・提案書（01〜04）は `instructions/modified_proposal/`（次採番 05）。

## 次採番

- 次フェーズは **`01_<topic>`**（欠番が出た場合はここに明記し、再利用しない）。

## 次フェーズ候補（参考）

（`instructions/backlog/INDEX.md` の idea から着手候補を 1〜3 件リンクする）

## 別タスク化候補

（継続保留、ソース変更を伴う細かい負債。`/refactor_check` からの追記先もここ）

- 計画04 W7 の次期課題（app.py の「どの責務分類にも属さない残留ロジック」。app.py は 489 行で目安 300 行を超過）:
  `validate_hotkey` の実装本体(~31行) を domain/application へ移し App は薄い委譲に /
  `_load_startup_settings`(~17行) を ConfigIoController・ConfigPaths へ / `_coerce_font_delta`(~10行) を theme.py 等へ /
  `set_ui_font_delta`(~17行) の責務混在（フォント適用+永続化+フラッシュ）を切り出し
- 計画04 W5 の対象外で残存した生やし: `views/status_bar.py` の `app.runtime_status_frame` / `app.status_bar`
- 計画04 の暫定措置: View の `trigger_list` alias（full/compact）は tests_ui が
  `app.<view>.trigger_list` を参照するため残置中。テスト側の参照経路を見直せば解消可能

## 作業開始時の指示

Claude は作業開始時に、このファイルで指定された参照先の `phase.md` を必ず読んでください。
次フェーズ未確定時はユーザーに方針確認すること。

## フェーズ完了時の指示

- 正本反映タスクの完了後、フェーズを完了扱いにする前に `/refactor_check`
  （`.claude/commands/refactor_check.md`）を実行し、リファクタ要否の判定結果を完了報告に含めること。
- フェーズ完了時は本ファイルの「現在の参照先」を差し替え、**旧フェーズの要約行は削除する**
  （要約は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` へ集約。ここに残さない）。

起票元 idea があるフェーズは、`instructions/backlog/INDEX.md` の該当行を完了 / クローズ状態に
更新して `instructions/backlog/INDEX_done.md` へ移動すること
（チェックリストは `.claude/rules/task_execution.md`「フェーズ完了時」）。

## 新フェーズ作成時の更新ルール

新しいフェーズ用フォルダを作成した場合は、`## 現在の参照先` を新フェーズの `phase.md` に更新してください。
フォルダ名は `instructions/phase/` 直下で**連番プレフィックス付き**（`NN_<topic>`）にしてください。
起票手順は `/phase_start`（`.claude/commands/phase_start.md`）に従うこと。

## 注意

このファイルには、実装順序・タスク詳細・チェック内容・完了フェーズの経緯を書かないでください。
それらは各フェーズフォルダ内の `phase.md` および `decisions_archive/<phase>.md` に記載してください。
