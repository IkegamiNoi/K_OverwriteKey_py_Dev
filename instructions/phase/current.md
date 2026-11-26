# Current Phase

このファイルは、現在どのフェーズ定義を読むべきかを示すためのルーティングファイルです。
**完了フェーズの要約はここに蓄積しない**（`.claude_data/state/decisions.md`「アーカイブ索引」+
`decisions_archive/<phase>.md` が正）。**例外は「直近の一連の作業が扱っている領域」の数行のみ**
（「フェーズ完了時の指示」節を参照）。

## 現在の参照先

- **アクティブなフェーズ = なし**（phase 82 は 2026-11-26 完了）。次フェーズはユーザー判断で `/phase_start`（候補は `../backlog/INDEX.md`）。
  **次採番 = phase 83 / 暫定 63 / decisions 83 / 提案書 30 / idea 72**（暫定 47 は idea_53 で保留中の番号）。
- 直近の一連の作業の領域 = スクロールの向きの反転（phase 82・`domain/mouse_scroll.py` の `ScrollInvert` / `coerce_scroll_invert` / `apply_scroll_invert`・`ActionExecutor` の `get_scroll_invert`・`App.set_scroll_invert` と設定 > スクロールの向き・config.json の `scroll_invert`・正本 `data_schema.md` §5.4・§5.11.10 / `features.md` §4.6・§4.8）。残件 = [idea_70](../backlog/idea_70_config_overwrite_on_multiple_instances.md)（多重起動で config.json が上書き）・[idea_71](../backlog/idea_71_unreadable_config_overwritten_on_save.md)（読めなかった config.json を次の保存で上書き）・残存リスク（実際の向き・macOS の遅延は実機目視のみ）は decisions_archive/82。
  それ以前の領域の残件は各 `decisions_archive/<phase>.md`（phase 81 = [idea_68](../backlog/idea_68_shift_layer_replacement_source.md)・[idea_69](../backlog/idea_69_mac_premod_lost_on_mapped_send.md) / phase 80 = [idea_67](../backlog/idea_67_win_d_with_os_file_dialog.md) / phase 75 = 検討段階の idea〔idea_45・59・60・63〜66〕ほか）。
- 直前の完了フェーズ = [phase 82](82_scroll_direction_setting/phase.md)（2026-11-26・判断は [decisions_archive/82](../../.claude_data/state/decisions_archive/82_scroll_direction_setting.md)・refactor_check 不要）。
- その前の完了フェーズ = [phase 81](81_uppercase_replacement_target/phase.md)（2026-11-25・判断は [decisions_archive/81](../../.claude_data/state/decisions_archive/81_uppercase_replacement_target.md)）。
- その前の完了フェーズ = [phase 80](80_win_d_restore_blank_dialog/phase.md)（2026-11-25・判断は [decisions_archive/80](../../.claude_data/state/decisions_archive/80_win_d_restore_blank_dialog.md)）。
- **それ以前の完了フェーズ**は `.claude_data/state/decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md` が正（要約はここに積まない）。2026-11-26 より前にここへ溜めていた要約と過去の「直近の領域」は [past_areas.md](past_areas.md)（凍結）。
- 台帳の置き場: 暫定仕様の一覧と状態 = [history/README.md](../history/README.md) / リファクタ提案書の一覧と実施状況 = [modified_proposal/INDEX.md](../modified_proposal/INDEX.md) / 別タスク化候補 = [backlog/deferred_tasks.md](../backlog/deferred_tasks.md) / idea = [backlog/INDEX.md](../backlog/INDEX.md)。
- テンプレート導入前の経緯・過去仕様は `instructions/history/archive/` を参照（凍結済み）。

## 次採番

- **phase**: 次は **`83_<topic>`**・decisions も **83**（欠番が出た場合はここに明記し、再利用しない）。
- **暫定仕様**（`instructions/history/NN_<topic>.md`・フェーズと独立採番）: 次は **`63_<topic>`**。**47 は idea_53 で保留中の番号**（再利用しない）。一覧と状態は [history/README.md](../history/README.md)。
- **リファクタ提案書**（`instructions/modified_proposal/NN_*.md`・独立採番）: 次は **`30_<topic>`**。**「計画09」は提案書を持たない**（`/spec_split` による正本の分割・規範は `.claude/skills/spec_split/SKILL.md`。提案書 09 とは別物）。提案書由来の計画はフェーズ番号を消費しない。一覧は [modified_proposal/INDEX.md](../modified_proposal/INDEX.md)。
- **idea**: 次は **`idea_72`**（`instructions/backlog/` のフォルダ実体が正・`/idea`）。

## 次フェーズ候補（参考）

（`instructions/backlog/INDEX.md` の idea から着手候補を 1〜3 件リンクする。
**完了した候補の履歴はここに残さない**〔完了 idea は `backlog/INDEX_done.md` が正〕）

- [idea_39](../backlog/idea_39_back_rewind_visible_trigger.md)（直前のトリガーの廃止ほか・phase 50 で一部取り込み済みの残り）

**保留中**（着手条件つき・トリガーが発生するまで着手しない）: [idea_04](../backlog/idea_04_font_settings_controller.md) /
[idea_06](../backlog/idea_06_individual_json_io_unification.md)。条件は `backlog/INDEX.md` の状態列が正。

## 別タスク化候補

[backlog/deferred_tasks.md](../backlog/deferred_tasks.md) に置く（`/refactor_check` の追記先もそちら・2026-11-26 に分離）。

## 作業開始時の指示

Claude は作業開始時に、このファイルで指定された参照先の `phase.md` を必ず読んでください。
次フェーズ未確定時はユーザーに方針確認すること。

## フェーズ完了時の指示

- 正本反映タスクの完了後、フェーズを完了扱いにする前に `/refactor_check`
  （`.claude/skills/refactor_check/SKILL.md`）を実行し、リファクタ要否の判定結果を完了報告に含めること。
- フェーズ完了時は本ファイルの「現在の参照先」を差し替える。**完了フェーズはリンクのみを残し、
  要約は書かない**（要約は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正）。
  代わりに「**直近の一連の作業が扱っている領域**」を数行で置き、**いま何の続きを見ているのか**と
  **その領域の残件**が分かるようにする（2026-09-08 のユーザー判断。過去フェーズの要約を並べない）。
- **完了フェーズのリンクは直近 3 件だけ**残し、4 件目は消す（索引が正のため移さない）。「直近の領域」は新しいフェーズの分に差し替え、前の領域の残件は「それ以前の領域の残件」の 1 行に idea 等のリンクだけ足す。
- **台帳は持ち主のファイルを更新する**（ここへ書き写さない・2026-11-26 ユーザー判断）: 暫定仕様の状態 = `instructions/history/README.md` / 提案書の状態 = `instructions/modified_proposal/INDEX.md` / 別タスク化候補 = `instructions/backlog/deferred_tasks.md` / idea = `instructions/backlog/INDEX.md`・`INDEX_done.md`。本ファイルは「次採番」節の番号だけ進める。

起票元 idea があるフェーズは、`instructions/backlog/INDEX.md` の該当行を完了 / クローズ状態に
更新して `instructions/backlog/INDEX_done.md` へ移動すること
（チェックリストは `.claude/rules/task_execution.md`「フェーズ完了時」）。

## 新フェーズ作成時の更新ルール

新しいフェーズ用フォルダを作成した場合は、`## 現在の参照先` を新フェーズの `phase.md` に更新してください。
フォルダ名は `instructions/phase/` 直下で**連番プレフィックス付き**（`NN_<topic>`）にしてください。
起票手順は `/phase_start`（`.claude/skills/phase_start/SKILL.md`）に従うこと。

## 注意

このファイルには、実装順序・タスク詳細・チェック内容・完了フェーズの経緯を書かないでください
（**「直近の一連の作業が扱っている領域」の数行だけは例外**。「フェーズ完了時の指示」節を参照）。
それらは各フェーズフォルダ内の `phase.md` および `decisions_archive/<phase>.md` に記載してください。
台帳（暫定仕様・提案書の一覧・別タスク化候補）も書かない（置き場は「現在の参照先」の「台帳の置き場」）。
