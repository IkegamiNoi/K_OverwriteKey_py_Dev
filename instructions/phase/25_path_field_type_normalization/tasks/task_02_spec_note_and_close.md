# task_02_spec_note_and_close

## 目的

phase 25 の**正本反映と記録**（フェーズ最終タスク）。task_01 / task_01b で実装が §5.1
「型不正の共通規則」へ追従したことを受け、**パス系フィールドにも同規則が適用される**ことを
正本の該当節へ明記し、判断履歴・ルーティング・起票元 idea のクローズまでを行う。

レイヤ制約: **文書作業のみ**。コード変更なし。
**§5.1 の規定そのものは変更しない**（フィールドを限定していないため、パス系も既に対象）。

## 対象範囲（文書のみ）

### instructions/common/spec_detail/data_schema.md

1. **§5.5（split 読込）へ型の規定を追記**（`:140` 付近の箇条書きの末尾）。
   - `keymap_set` が持つ `trigger_set_path` / `active_keymap_path` / `keymaps[].path` /
     `keymaps[].switch_key` の型は **§5.1「型不正の共通規則」に従う**。
   - **非文字列は空扱い = 未指定と同じ**（参照しない / スイッチキーを登録しない）。
   - `keymaps[]` の要素は dict と、**旧記法の文字列**の両方を受ける（現状の実装どおり・明文化のみ）。
   - `switch_key` は**キー名なので trim + 小文字化**、パスは **trim のみ**（小文字化しない。§5.7）。
2. **§5.7（パス保存ルール）へ 1 行追記**（`:230` の「本節は保存経路・読込経路の両方に適用する」の直後）。
   - **パス値の型が不正な場合は §5.1 に従う**（非文字列は空扱い）。
   - **パスは小文字化しない**（同一性判定の正規化〔`normcase`〕は比較専用であり、
     記録する表記は大文字小文字を保持する）ことを明記する。
3. **`external_keyboard_layouts` の型**について、記述している節があればそこへ 1 行
   （`:96` 付近の §5.4 に `orphan_sweep_scan_dirs` の記述がある。同様の書き方に揃える）。
   該当節が無ければ §5.5 の追記に含める。

### instructions/common/codebase_map.md

4. phase 24 で追記した「JSON 読込時の型正規化」の項へ、**パス系も対象になったこと**と
   **参照突合経路（`reference_scan.py`）も同じ関数を通ること**を追記する。
   **パスは `coerce_label`、キー名は `coerce_key_name`** という使い分けも 1 行で書く。

### .claude_data/state/decisions_archive/25_path_field_type_normalization.md（新規）

5. phase 25 の判断履歴を集約する（`decisions_archive/24_...md` の書式に倣う）。
   記載する判断: ①案 A 採用と**案 B（現状維持 + 未定義と明記）を採らなかった理由**
   （§5.1 を後から緩めることになり `spec_change_workflow.md` の禁止事項に当たる）
   ②直接改訂モードを選んだ理由（§5.1 がフィールドを限定しておらず仕様変更が不要）
   ③**パスとキー名の使い分け**（パスを小文字化しない）④task_01b を追加した経緯
   （完了後レビューで参照突合経路の取りこぼしを検出）⑤現状監査の結果（例外はゼロ・実害の内訳）。

### .claude_data/state/decisions.md

6. 「アーカイブ索引」へ 1 行追加する。

### instructions/phase/current.md

7. 「現在の参照先」の phase 25 項を**完了記載**へ更新し、「直近の一連の作業が扱っている領域」を
   phase 25 の内容へ差し替える（完了フェーズはリンクのみ・要約は書かない）。
   次採番（phase 26 / decisions 26）は task_01 で更新済のため**再変更しない**。

### instructions/backlog/INDEX.md / INDEX_done.md

8. idea_25 の行を完了状態（→ phase 25 / 完了日）へ更新し、`INDEX_done.md` へ**移動**する。

### instructions/phase/25_.../phase.md

9. 「タスク」一覧へ完了状態を反映する（task_01 / task_01b / task_02）。

## 読むファイル

- `instructions/common/spec_detail/data_schema.md` §5.1（`:21-44`）/ §5.4（`:96` 付近）/
  §5.5（`:140-149`）/ §5.7（`:219-232`）
- `instructions/common/codebase_map.md` の「JSON 読込時の型正規化」の項（phase 24 で追記した箇所）
- `.claude_data/state/decisions_archive/24_json_type_normalization.md`（書式の手本・冒頭のみ）
- `.claude_data/state/decisions.md`「アーカイブ索引」節
- `instructions/phase/current.md`「現在の参照先」「フェーズ完了時の指示」
- `instructions/backlog/INDEX.md` の idea_25 行 / `INDEX_done.md` の末尾

## 含まない

- コードの変更（task_01 / task_01b で完了）
- **`startup_io.py:18` の `keymap_set_path`**（config.json の生値を読むが **presentation 層**で、
  phase.md が presentation 不変と宣言しているため対象外）。**残件として記録に残す**
- `orphan_scan.py` / `quarantine.py`（生 JSON を直接読む箇所ではない）
- `button` 非文字列（`action_executor.py:119`・実行時の別レイヤ・phase 22 からの候補）
- `coerce_label` の改名
- main へのマージ（ユーザーが行う）

## 確認

1. §5.5 / §5.7 の追記が実装（task_01 / task_01b）の挙動と一致すること。
   特に **`switch_key` は小文字化され、パスは小文字化されない**という非対称が正しく書けていること。
2. **§5.1 の規定本文が変更されていないこと**（追記は参照のみ）。
3. `decisions.md` の索引リンクが実在ファイルを指すこと。
4. `INDEX.md` に idea_25 の行が残っていないこと / `INDEX_done.md` に移っていること。
5. `/refactor_check` を実行し、判定結果（要否・根拠 M1〜M6）を完了報告に含めること。
6. 静的確認: `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui`

## 完了条件

- 上記確認 1〜6 が pass・**reviewer 採用**（観点: 正本の記述と実装の整合・記録の漏れ・
  既存節との矛盾）。
- 実機目視: **不要**（UI 変更なし）。
- 本タスク完了をもって phase 25 を完了とする。
