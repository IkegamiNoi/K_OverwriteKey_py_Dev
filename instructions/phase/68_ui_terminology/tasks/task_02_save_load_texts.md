# task_02_save_load_texts

## 目的

保存・読込・子ファイル保存まわりの画面に出る文言へ、暫定 51 の用語表・個別確定文・表記規則を当てる（§2・§2.1 Q5・§2.2 C6・C7・§3.1〜§3.4・§3.6）。
**presentation（config_io・app.py の起動時読込）と application（config_service・save_plan の画面に出る例外文）の文字列。挙動不変・JSON スキーマ不変。**
例外は §3.4 の `{親の種類名}` を渡すための最小の引数追加と、Q5 の移行ラベル（今後作る値だけ）。

## 対象範囲（担当ファイルの文字列・ファイル単位）

**対象文字列の一覧 = `instructions/phase/68_ui_terminology/tools/task_02_strings.md`（193 件・実装前）**。この一覧の全行を見て、当たる規則があれば置換する（無ければ触らない）。
担当ファイル: `controllers/config_io/` の keymap_file_io・trigger_set_file_io・sequence_file_io・keymap_set_io・child_save_*（columns・dialog・plan・rows）・io_dialogs・save_target_snapshot・startup_io /
`application/config_service/` の `__init__`・child_file_io・keymap_save_plan・save_plan_execution・split_loading / `application/save_plan.py` / `presentation/app.py:123-124`。

主な置換（網羅は一覧と暫定 51 が正）:

- **A1**: `keymap_set_io.py:102`「別名で保存（keymap_set）」→「別名保存（構成セット）」・:553「keymap_set.json を読込」→「構成セットを読み込む」・:676・:711・`split_loading.py:50`（→「構成セットの読み込みに失敗しました。」）・`save_plan_execution.py:270`（文中の keymap_set）
- **A7・A8・A2**: 文中の語として使う `sequence` / `trigger_set` / `keymap`（例 `keymap_file_io.py:201`・`save_plan_execution.py:423-458`・`save_plan.py:26-59`・`child_file_io.py:22・76`・`config_service/__init__.py:141・233`）→ 出力シーケンス / トリガーセット / キーマップ。「トリガー一覧」が trigger_set 1 ファイル分の意味のもの（§3.3 (a)）→ トリガーセット（`trigger_set_file_io.py` の題・通知・失敗文・`keymap_set_io.py:175・246・444・478・503・598`・`save_target_snapshot.py:14`・`child_save_rows.py:169`・`child_save_dialog.py:294`）
- **A9**: 題「キーマップを読込」「出力シーケンスを読込」「トリガー一覧を読込」→「〜を読み込む」/「読込できません」→「読み込めません」/ 文中の名詞「〜の読込に失敗」→「〜の読み込みに失敗」（`app.py:124` を含む）/ 体言ラベル・複合語（読込・読込失敗・読込先）は据え置き
- **A13**: `keymap_set_io.py:648-668` の「例の復元」「例の設定に戻します」等（§3.2 A13。未保存確認の操作名は「サンプル設定の復元」）
- **A15・§3.4**: 表のとおり（`*_file_io.py` の「上位の索引…」・`child_save_rows.py:81・83・85` の `{親の種類名}`・`child_save_dialog.py:187-189`・`keymap_set_io.py:176・246`）。
  `child_save_rows.py:75` `share_text_for` に行の種別（`kind`）を渡す引数を足し、`:287` の呼び出し元から渡す。親の種類名 = キーマップ行 → 構成セット / トリガーセット行 → キーマップ / 出力シーケンス行 → トリガーセット
- **A19**: 「別名で保存」→「別名保存」（題・確認文「別名で保存しますか？」→「別名保存しますか？」・通知「別名で保存しました。」→「別名保存しました。」・`child_save_dialog.py:283`）
- **C6**: `child_save_dialog.py:170`・`child_save_plan.py:56`・`save_plan_execution.py:431` →「移行対象には「保存しない」を選べません。」
- **C7**: `keymap_file_io.py:46`・`sequence_file_io.py:16` →「読み込んだキーマップです。」「読み込んだ出力シーケンスです。」（後続は A19 で「別名保存しますか？」）
- **未保存確認の操作名**: `keymap_set_io.py:648`「例の復元」→「サンプル設定の復元」・:672「起動時に読むJSONの変更」→「起動時に読む構成セットの変更」・`trigger_set_file_io.py:202`「トリガー一覧読込」→「トリガーセット読込」
- **Q5**: `split_loading.py:381` のラベル `旧トリガー一覧（{stem}）` →「旧トリガーセット（{stem}）」（今後作る値だけ。保存済みの値を書き換える処理は入れない）
- **§3.6 D1〜D9・D11**: 担当ファイルの全文言に当てる（優先順位と差し込み前後の規則は §3.6 の細則）。**D3（「…」の付与 / 除去）は当てない（task_06）**。D10（Import / Export の文字列）は据え置き

### 設計メモ / 制約

- **据え置き**（§3.1・§3.2）: パス表示・`startup.json`・`config.json`・フォルダ名・JSON キー・ログ専用の文言・docstring・コメント。体言の「読込」。結果通知の「変更しました」。
- task_01 で替えた確認 3 か所（`io_dialogs.py` の衝突確認・`child_save_dialog.py` の再計算確認・`keymap_set_io.py` の保存先の確認）の本文・ボタンは task_01 で確定済み。触らない。
- `child_save_dialog.py:183` の長い説明文は A19・A15・§3.4・D 規則を当てる（「索引」→「保存先の記録」）。
- 文言を検査している既存テスト（tests / tests_ui）は新しい文言へ追従させる。**期待する挙動・分岐は変えない**。テストのファイルは grep（旧文言）で網羅確認する。

## 読むファイル

1. `instructions/history/51_ui_terminology.md` の §2・§2.1 Q5・§2.2 C6・C7・§3.1・§3.2（A1・A7〜A9・A13・A19・未保存確認の操作名）・§3.3・§3.4・§3.6
2. `instructions/phase/68_ui_terminology/tools/task_02_strings.md`（対象一覧）
3. 担当ファイル（一覧に出てくる行の周辺だけ）
4. `keyseq/presentation/controllers/config_io/child_save_rows.py:70-90・280-290`（引数追加）

## 含まない

- 担当外ファイルの文言（キーマップ・トリガーのパネル = task_03 / アクション = task_04 / プリセット・整理・退避・履歴 = task_05 / メニュー・表示 = task_06）
- 「…」の付与 / 除去（task_06）・前後差分の確認（task_07）・正本反映と実機目視（task_08）
- 保存済みの移行ラベルの書き換え・B 項（内部名の表示名化）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `child_save_rows` の `share_text_for` の 3 種別 × 共有状況のテスト（既存の追従 + 親の種類名の分岐を各 1 件）pass
- `-m unittest discover -s tests` / `-s tests_ui` 全 pass・`-m tests.smoke_app` OK
- `extract_ja.py` を担当ファイルへ流し、`task_02_strings.md` と比べて「やめる語」（暫定 51 §2）が担当ファイルに残っていない（残すものは据え置きの理由を報告）

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_08 でまとめて実施。
