# task_05_preset_sweep_texts

## 目的

プリセット・未使用ファイルの整理・退避・参照元の掃除・構成セットの履歴の画面に出る文言へ、暫定 51 の用語表・行ごとの置換表・表記規則を当てる（§2 A12・A16〜A18・§3.2 A11〔`preset_manager.py:350`〕・A12・A16〜A18 の表・§3.6）。
**presentation と application（画面に出る文言）の文字列のみ。挙動不変・JSON スキーマ不変・フォルダ名 / ID 表示は据え置き。**

## 対象範囲（担当ファイルの文字列・ファイル単位）

**対象文字列の一覧 = `instructions/phase/68_ui_terminology/tools/task_05_strings.md`（198 件・実装前）**。全行を見て、当たる規則があれば置換する。
担当ファイル: `dialogs/preset_manager.py`・`controllers/config_io/hotkey_presets_io.py`・`orphan_sweep_*`（text・io・dialog）・`quarantine_*`（text・io・dialog）・`reference_cleanup_*`（text・io・dialog）・`keymap_set_history_*`（text・io・dialog）・`application/config_service/keymap_set_history.py`。

主な置換（網羅は一覧と暫定 51 が正）:

- **A12**: §3.2 A12 の列挙（`preset_manager.py:34・45・50・51・56-57・60・62・64`・`hotkey_presets_io.py:33・38・42・53`・`orphan_sweep_text.py:10`）。チェックボックス「この構成セット専用にする」・「config 外」は据え置き
- **A11**: `preset_manager.py:350` の失敗題「変更できません」→「編集できません」
- **A16〜A18・M9**: §3.2 A16〜A18 の行ごとの置換表どおり（「ディレクトリ」→「フォルダ」・「走査」→「探す」を含む）。ダイアログの題「孤児ファイルの棚卸し」→「未使用ファイルの整理」・「隔離の管理」→「退避したファイルの管理」・ボタン「棚卸しを実行」→「整理を実行」・`reference_cleanup_text.py:48`
- **A8**: 種別名の「トリガー一覧」（`orphan_sweep_text.py:8`・`reference_cleanup_text.py:8`）→「トリガーセット」/ `orphan_sweep_text.py:38` の「構成セット / トリガー一覧」→「構成セット / トリガーセット」
- **§3.6 D1・D2・D4〜D9・D11**: 担当ファイルの全文言に当てる（細則どおり。`{n} 件`→`{n}件` 等の差し込み前後・列そろえの 2 空白は対象外）。**D3 は当てない（task_06。「復元する…」「削除する…」の「…」も task_06）**

### 設計メモ / 制約

- 据え置き: 退避の回の ID 表示（`unit_id`）・フォルダ名・パス・ログ専用の文言・docstring・コメント。
- `keymap_set_history_text.py` の「＋分類を追加」等のボタンは「…」を付けない（task_06 の一覧で確定済み）。本タスクでは語・表記だけ。
- 文言を検査している既存テスト（`tests/test_orphan_sweep_text.py`・`test_reference_cleanup_text.py`・`tests_ui/test_orphan_sweep_flow.py` ほか）は新しい文言へ追従させる（期待する挙動は変えない）。

## 読むファイル

1. `instructions/history/51_ui_terminology.md` の §2（A8・A12・A16〜A18）・§3.1・§3.2（A11・A12・A16〜A18 の表）・§3.6
2. `instructions/phase/68_ui_terminology/tools/task_05_strings.md`（対象一覧）
3. 担当ファイル（一覧に出てくる行の周辺だけ）

## 含まない

- メニューの「孤児ファイルの棚卸し…」「隔離の管理…」（`menu_bar.py` = task_06）
- 「…」の付与 / 除去（task_06）・前後差分（task_07）・正本反映と実機目視（task_08）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests` / `-s tests_ui` 全 pass・`-m tests.smoke_app` OK
- `extract_ja.py` を担当ファイルへ流し、「やめる語」（孤児・棚卸し・隔離・実行単位・マニフェスト・ディレクトリ・グローバル・個別プリセット 等）が残っていない（残すものは据え置きの理由を報告）

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_08 でまとめて実施。
