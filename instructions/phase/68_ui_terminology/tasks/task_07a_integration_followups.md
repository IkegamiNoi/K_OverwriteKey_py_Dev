# task_07a_integration_followups

## 目的

task_07 の統合レビュー（deep-reviewer）の指摘のうち、ユーザー確定済み（2026-10-24・暫定 51 v0.8）のものと判断不要の揃えを反映する。
**presentation / application / domain の画面に出る文言の文字列のみ。挙動不変・JSON スキーマ不変。**

## 対象範囲

1. **A21「アクティブなキーマップ」**: `keymap_panel_controller.py:641`・`trigger_row_edit.py:48・99` の「アクティブキーマップの」→「アクティブなキーマップの」（docstring `domain/keymap_triggers.py:1` は対象外）
2. **D1 細則（全角括弧の前に空白を入れない）**: `domain/key_hold.py:124`「 （リピート）」→「（リピート）」・`domain/mouse_scroll.py:99`「 （生）」→「（生）」・`domain/sequence_control.py:202・222` の `{display_name} （…）` →`{display_name}（…）`。他に `" （"`・`} （` の形が画面に出る文字列にあれば同様（ログ専用・docstring は対象外）
3. **C15 の本文**: `child_save_dialog.py` の再計算確認（`confirm_recalculated_overwrite`）の本文の末尾に、空行を挟んで「どうしますか？」を足す
4. **D3「別名保存…」**: `io_dialogs.py`（同名ファイルの確認）・`child_save_dialog.py`（再計算の確認・子ファイル保存の依存確認 :236 付近）の「別名保存」ボタン →「別名保存…」（choices の id は不変）
5. **A9 の揃え（統合レビュー 低 4）**: `application/action_executor.py:168・186`「ファイル読込の仕組みが未設定です」→「ファイルの読み込みの仕組みが未設定です」・`:193`「ファイル読込の結果が正しくありません」→「ファイルの読み込み結果が正しくありません」
6. 上記を検査している既存テスト（tests / tests_ui）の追従。**変えた文字列は空白・括弧・「…」だけの変更も含めて 1 つずつ旧文言の断片（`" （リピート）"`・`" （生）"`・`（呼び出し先なし）` の前の空白・`"別名保存"` の完全一致・`アクティブキーマップ`・`ファイル読込の`）で tests / tests_ui を検索して直す**

### 設計メモ / 制約

- D4: 行末のコロンは `:\n` のまま。
- choice_dialog の choices の id・既定・cancel は変えない（文字だけ）。

## 読むファイル

1. `instructions/history/51_ui_terminology.md` の §2 A21・§3.5（v0.8 の追記）・§3.6 D1
2. 上記の対象ファイル（該当行の周辺だけ）

## 含まない

- 実機目視・正本反映（task_08）。統合レビューの低 8（`_PARENT_KIND_LABELS` のフォールバック）は除外（種別は 3 つだけ）

## 確認

- compileall clean・tests / tests_ui 全 pass・smoke OK（verifier）
- 実装後に `tools/extract_ja.py` を流し直し `tools/after_ja_strings.md` を更新

## 完了条件

- 上記確認 pass・**reviewer 採用**。
