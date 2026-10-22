# task_06_view_menu_texts

## 目的

メニュー・詳細表示 / 簡易表示・画面の枠・キーボードUI の画面に出る文言へ、暫定 51 の用語表・個別確定文・表記規則を当て、**D3 の「…」の付与 / 除去を全ファイルへ適用する**（§2・§2.2 C10〜C12・C14・§3.2 A14・§3.6・ユーザー確定済みの一覧 `tools/d3_ellipsis_list.md`）。
**presentation（views・screen_grid・キーボードUI）と domain/screen_grid の文言の文字列のみ。挙動不変・JSON スキーマ不変。**

## 対象範囲（担当ファイルの文字列・ファイル単位 + D3 は全ファイル）

**対象文字列の一覧 = `instructions/phase/68_ui_terminology/tools/task_06_strings.md`（196 件・実装前）**。全行を見て、当たる規則があれば置換する。
担当ファイル: `views/`（menu_bar・status_bar・full_view/・compact_view/）・`presentation/screen_grid/`・`domain/screen_grid/`・`dialogs/grid_editor_window.py`・`layout_delete_dialog.py`・`presentation/keyboard_window.py`・`keyboard_layouts.py`・`infrastructure/win32_window.py`。

主な置換（網羅は一覧と暫定 51 が正）:

- **menu_bar**: A19「別名で保存…」→「別名保存…」/ A13「例を復元」→「サンプル設定に戻す」/ A16〜A18「孤児ファイルの棚卸し…」「隔離の管理…」→「未使用ファイルの整理…」「退避したファイルの管理…」/ D3「参照元を掃除…」→「参照元を掃除」/ Import... / Export... は据え置き（D10）
- **A1・A5・C14**（`views/*/hook_frame.py`）:「このキーマップセットで個別指定する」→「この構成セットで個別指定する」・「フック停止トリガー: 」→「停止キー: 」・「確認して実行」→「選んでから実行」（`sequence_box.py:80` も）
- **A7**: 簡易表示の折りたたみ見出し「▸ シーケンス」は許容（据え置き）。`sequence_box.py:19`「出力シーケンス（選択中トリガーの内容）」は不変
- **A8**: 画面のリストの見出し「トリガー一覧（選択して編集）」「トリガー一覧」は**据え置き**（§2.1 Q2）
- **A11**: `keymap_box.py:47`「キーマップ変更」→「キーマップ編集」・`trigger_box.py:47`「トリガー変更」→「トリガー編集」（D3 で「…」も付く）
- **A14**: `full_view/display_frame.py:25`「省略表示」→「簡易表示」・`compact_view/display_frame.py:29`「フルに戻す」→「詳細表示」・「常に手前」→「最前面に表示」・「キーボードUIを常に手前」→「キーボードUIを最前面に表示」
- **A19**: 各欄のボタン「別名で保存」→「別名保存」
- **C10**: `domain/screen_grid/ops.py:27`「深くする」→「絞り込む」（内部名 `deepen` 不変）・その名前を出す画面 / メッセージ
- **C11**: `grid_editor_panel.py:67`「振り直し」→「キーを振り直す」
- **C12**: `grid_overlay_window.py:42` →「枠のウィンドウをクリック透過にできませんでした」
- **D11**: `keyboard_window.py:62`「Keyboard UI — 編集中: …」→「キーボードUI — 編集中: …」
- **D3（全ファイル）**: `tools/d3_ellipsis_list.md` の「案」の列どおりに付与 / 除去する（ユーザー確定 2026-10-23）。**担当外ファイルのボタン（`dialogs/preset_manager.py`・`quarantine_manage_dialog.py`・`file_frame.py` 等）も本タスクで「…」だけ変える**（語は各担当タスクで変更済みの前提）
- **§3.6 D1・D2・D4〜D9**: 担当ファイルの全文言に当てる（`keyboard_layouts.py` の外部レイアウト JSON の検査文にも D8 を当てる）

### 設計メモ / 制約

- 文字の幅: 固定幅のボタン（`file_frame.py` width=18・`sequence_box.py` 16・`preset_manager.py` 14）は「…」で溢れないかを tests_ui の既存の幅のテストで確認し、溢れるなら報告（幅の変更はしない）。
- 文言を検査している既存テスト（ヘッダの幅・ボタンを文言で探すもの等）は新しい文言へ追従させる（期待する挙動は変えない）。
- `hook_button_texts.py`（task_03）の取得 / 記録の文言は触らない。

## 読むファイル

1. `instructions/history/51_ui_terminology.md` の §2・§2.1 Q2・§2.2（C10〜C12・C14）・§3.1・§3.2（A14 ほか）・§3.6
2. `instructions/phase/68_ui_terminology/tools/task_06_strings.md`（対象一覧）・`tools/d3_ellipsis_list.md`（D3 の確定一覧）
3. 担当ファイル（一覧に出てくる行の周辺だけ）

## 含まない

- 前後差分と残存一覧（task_07）・正本反映と実機目視（task_08）
- B 項（内部名の表示名化）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests` / `-s tests_ui` 全 pass・`-m tests.smoke_app` OK
- `d3_ellipsis_list.md` の全行について、付与 / 除去 / 不変が実装と一致（一覧で報告）
- `extract_ja.py` を担当ファイルへ流し、「やめる語」が残っていない（残すものは据え置きの理由を報告）

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_08 でまとめて実施（ボタンの幅を含む）。
