# phase.md

## フェーズ名

UI 文言の用語統一（ui_terminology）

## フェーズの目的

UI の文言を 1 概念 1 語に揃え、個別の不自然な表現と表記ゆれを直す。今後のヘルプ作成・多言語対応・Mac 対応の土台になる用語表を正本に置く。
**対象は利用者の目に触れる文字列（presentation・application・domain）。文字列の置換が基本で挙動は変えない。例外 = はい / いいえ の確認 3 か所をボタン名で選ぶ共通ダイアログへ替える（分岐は現状どおり）と、旧形式移行で今後作るキーマップのラベル。JSON スキーマ不変（既存キーの削除・意味変更なし）。**

- 起票元: ユーザー要望（2026-10-22・現状の UI 文言を一覧化して表現を見直したい）。
- 主入力（暫定仕様）: [51_ui_terminology.md](../../history/51_ui_terminology.md)（v0.7・ユーザー確定済）
- モード: **暫定仕様先行モード**。番号対応: phase 68 / 暫定 51 / decisions 68。

## 確定（ユーザー 2026-10-22〜23）

- 用語表 A1〜A20（構成セット / キーマップ / キー置換・置換元キー / 停止キー / 切替キー / 出力シーケンス / トリガーセット / 読込・読み込む / 記録・取得 / 編集 / 共通・構成セット専用・既定プリセット / サンプル設定 / 簡易表示・詳細表示・最前面に表示 / 上位・索引は具体名 / 未使用ファイルの整理 / 退避 / 回・記録 / 別名保存 / トリガーキー）（暫定 51 §2・§2.1）
- 個別の表現 C1〜C16（§2.2）・はい / いいえ の確認 3 か所のボタン名ダイアログ化（§3.5）・表記規則 D1〜D11 と優先順位（§3.6）
- 内部名の表示名化（B 項）は含めない（§2.1 Q1）

## スコープ

### 含む

- 暫定 51 §3.1 の対象の文言への §2・§2.2・§3.2〜§3.4・§3.6 の適用（行ごとの列挙は暫定 51 が正）
- §3.5 の共通確認ダイアログ（`controllers/config_io/` 内）と 3 か所の差し替え・テスト
- 文言を検査している既存テストの追従（tests / tests_ui）
- 実装前後の文言の抽出差分と残存一覧（§6-1）・実機目視（§6-6）・正本反映（§8）・暫定 51 の凍結

### 含まない（後送り）

- 文言の外部化（定数化・辞書化）・多言語化・Mac 対応・ヘルプ作成（暫定 51 §7）
- B 項（種類の内部名 `hotkey` / `mouse_click` 等の表示名化）・専門語「キーボードUI」「フック」「参照元の掃除」等（ヘルプで定義）
- docstring・コメント・ログ専用の文言・計画書の用語
- 暫定 51 §3.1・§3.2 の据え置き（ファイル名・フォルダ名・JSON キー・保存済みの値〔移行ラベルは今後作る分だけ変える〕/「名前変更」・座標の「取得」・「キーマップ一時停止 / 再開」・「読む」・画面のリストの見出し「トリガー一覧」等。据え置きの正は暫定 51）

## このフェーズで読むファイル

1. 主入力: `instructions/history/51_ui_terminology.md`（各タスクは担当範囲の節と §3.1・§3.6 だけ読む）
2. 抽出の道具と実装前の一覧: `instructions/phase/68_ui_terminology/tools/extract_ja.py`・`tools/baseline_ja_strings.md`（コミット `2ea8b54` 時点・1196 件 / 101 ファイル）
3. 各タスクの対象ファイル（タスク定義で列挙。暫定 51 の `ファイル:行` が起点）
4. task_01 のみ: `features.md`「モーダルダイアログの作法」・`key_input.md` §7.2・`keyseq/presentation/controllers/config_io/hotkey_presets_io.py:45-90`・`tests_ui/test_config_io_characterization.py:431-483`
5. 正本反映（最終タスク）: 暫定 51 §8 の列挙 + 旧ラベルの正本全体の再検索結果

## タスク

**ファイル単位で担当を 1 つに決める**。各タスクは担当ファイルの対象の文言すべてに §2・§2.2・§3.2〜§3.4・§3.6（D3 の「…」の付与 / 除去を除く）を当てる
（括弧内の規則は主なものの例示。担当ファイルにある他の規則の文言も漏らさない）。**各タスク定義で担当ファイルを `tools/baseline_ja_strings.md` と突き合わせて網羅を確認する**。
下の列挙に無い `keyseq/` のファイルは、内容が最も近いタスクの定義時に割り当てる（task_07 の前後差分で未着手のファイルが無いことを確認する）。

- task_01: はい / いいえ の確認をボタン名の共通ダイアログへ（暫定 51 §3.5・C15）・テスト（tests_ui）。担当 = 新しい共通ダイアログ・`io_dialogs.py:15〜17`・`child_save_dialog.py:250〜278`・`keymap_set_io.py:732〜738` の確認部分だけ（残りの文言は task_02）
- task_02: 保存・読込・子ファイル保存の文言（A1・A7〜A9・A13・**A15・§3.4 の置換表と `{親の種類名}` の引数追加**・A19・C6・C7・未保存確認の操作名・Q5 の移行ラベル）。
  担当 = `controllers/config_io/` の keymap_file_io・trigger_set_file_io・sequence_file_io・keymap_set_io・child_save_*・io_dialogs・save_target_snapshot・startup_io /
  `application/config_service/` の `__init__`・child_file_io・keymap_save_plan・save_plan_execution・split_loading（:50・:381）/ `application/save_plan.py` / `app.py:123〜124`
- task_03: キーマップ・トリガー・停止 / 切替 / 置換のキーの文言（A2〜A6・A10・A11・A15 の「上位の割り当て」・A20・C9・C13）。
  担当 = `controllers/keymap_panel/`（keymap_add_flow を含む・C8）・`controllers/trigger_panel/`（trigger_panel_controller の :256 を含む）・`hook_controller.py`・`key_capture.py`・`layout_controller.py`・
  `app.py`（:123〜124 以外）・`application/keymap_switch_batch.py`・`hotkey_service.py`・`hook_coordinator.py`・`action_executor.py`・`presentation/hook_button_texts.py`・
  `dialogs/keymap_edit_dialog.py`・`keymap_switch_batch_dialog.py`・`trigger_dialog.py`（C16 を含む）
- task_04: 出力シーケンスとアクションの文言（C1〜C5・C14 以外の出力シーケンス系・D8・D9 の中心）。
  担当 = `dialogs/action_dialog.py`・`action_*_fields.py`・`preset_dialog.py` / `application/` の sequence_steps・call_context・sequence_runner/・sequence_history・file_line_*・held_inputs・key_repeat・screen_grid_session / `domain/`（screen_grid/ を除く）/ `infrastructure/input_gateway.py`
- task_05: プリセット・未使用ファイルの整理・退避・参照元の掃除・構成セットの履歴の文言（A12・A11 の `preset_manager.py:350`・A16〜A18・M9 のフォルダ）。
  担当 = `dialogs/preset_manager.py`・`hotkey_presets_io.py`・`orphan_sweep_*`・`quarantine_*`・`reference_cleanup_*`・`keymap_set_history_*`・`config_service/keymap_set_history.py`
- task_06: 表示・メニュー・画面の枠・キーボードUI の文言（A14・C10〜C12・C14・D11 と、**`menu_bar.py` の A9・A13・A16〜A18・A19**・`views/*/hook_frame.py` の A1・A5・C14）。
  担当 = `views/`（menu_bar・status_bar・full_view/・compact_view/）・`screen_grid/`・`domain/screen_grid/`・`dialogs/grid_editor_window.py`・`layout_delete_dialog.py`・`keyboard_window.py`・`keyboard_layouts.py`・`infrastructure/win32_window.py` +
  **D3 の「…」を付ける / 外すメニュー・ボタンの一覧表を、実装より前にタスク定義の段階で作りユーザー確認を経てから全ファイルへ適用**（暫定 51 §3.6）
- task_07: 実装後の抽出と前後差分・残存一覧（§6-1・理由付き）・統合確認（tests / tests_ui / smoke）・統合レビュー
- task_07a: 統合レビューの指摘のうちユーザー確定分（A21 アクティブなキーマップ・全角括弧の前の空白・再計算確認の「どうしますか？」・確認ダイアログの「別名保存…」）と読込の揃え（2026-10-24 追加）
- task_08: 実機目視（§6-6）・正本反映（§8・新ファイル `spec_detail/ui_terms.md` の要否はユーザー確認）・暫定 51 凍結・`decisions_archive/68_ui_terminology.md`・decisions.md の索引・current.md の完了記載・`/refactor_check`・完了判定前レビュー（deep-reviewer + codex-adversarial-reviewer）

## レビュー方針

- 各タスク: `reviewer`（5 観点）・既存テスト（tests / tests_ui / smoke）の通過を完了条件に含める
- 文言タスク（task_02〜06）の重点: 暫定 51 の個別確定文・用語表どおりか / 据え置き（§3.2・§2.1）を誤って置換していないか / §3.6 の優先順位（語は個別確定文、表記は D1〜D6 を後から）/ 差し込み `{...}` 前後の空白の判定 / 保存値・JSON キー・ファイル名を変えていないか / ログ専用・docstring を触っていないか / テストの意図を変えずに文言だけ追従しているか
- task_01 重点: 3 か所の分岐・既定ボタン・× / Esc が §3.5 の表どおり / フックの停止と解除がちょうど 1 回（ネスト含む）/ 親が grab 中の窓 / 入力先とキー操作 / 差し替え可能な呼び出し口
