# task_02b_save_safety_and_naming

## 目的

task_02 で切り替えた一括保存に、暫定仕様 25 の残りの保存規則を入れる:
§5.2（source_path を持たない子を常に行へ）/ §5.3 の 2・3 点目（keymap 別名保存時の trigger_set 既定名の再計算・keymap「保存しない」時の扱い）/
§5.4 の移行時の扱い（移行した trigger_set の所有判定と、keymap_set 上書き保存成功後の後処理）/
§5.5（keymap の既定ファイル名・「同名既存ファイル → 別名保存」の trigger_set 除外撤廃）。

**JSON スキーマ不変**（task_02 で確定済み）。application（既定名・親参照の後処理）と presentation（行・計画の既定規則・共有状況判定）。

## 対象範囲

### §5.2 source_path を持たない子は常に行へ

- `keyseq/presentation/controllers/config_io/child_save_rows.py`: keymap / trigger_set / sequence のうち
  **source_path を持たない（空文字）子は dirty でなくても一覧ダイアログの行に出す**（トリガー 0 件・source なしでファイルを作らない trigger_set 実体は除く＝§5.1）。
- `child_save_plan.py:87`（行に無い子は既定保存先が実在すれば SKIP）: 上記により source_path なしの子は必ず行に出るため、
  この既定 SKIP に落ちないこと。行に出ている子の既定アクションは現行の共有状況判定に従う。
- 既定アクションの決定は現行の規則（§5.8.4 の表 + 優先規則）を使う。

### §5.3 の 2・3 点目

- keymap を**別名保存**に選び直したら、その keymap を親とする**ファイル未作成（source_path なし）の trigger_set** の既定名を
  新しい keymap 保存先の stem で再計算する（`keymap_set_io.py` の「保存先変更時の再計算」経路。既存の上書き確認〔§5.8.5〕を適用）。
- keymap を「保存しない」と明示選択した場合（移行先を除く・§4.2）: その keymap の `trigger_set_path` は旧値（source のファイルの値）のまま・
  keymap の未保存マークも残す。**その keymap の trigger_set の保存先が変わる場合は task_02 の依存エラー（3 段）が先に働く**ことを確認し、
  変わらない場合は trigger_set / sequence の保存はそのまま行ってよい。

### §5.4 移行した trigger_set の `_parent_refs`

- `_legacy_trigger_set.state == "migrated"` の構成セットの**初回保存**（`_legacy_trigger_set` の状態で判定。task_02 で保存成功後に `none` へ更新済み）:
  - **共有状況の判定**（`child_save_rows`）: 移行した trigger_set の `_parent_refs` に移行元 keymap_set（`_legacy_trigger_set` を持つ現在の keymap_set パス）が
    あれば、それを「現在の親」として扱う（「別の構成」に倒さない → 単独所有 / 共有中）。
  - **書込み時**: 移行先 keymap のパスを `_parent_refs` に**加えるだけ**（移行元 keymap_set は残す）。
  - **後処理**: keymap_set を**移行元と同じパスへ上書き保存し成功した後**に限り、その trigger_set ファイルの `_parent_refs` から移行元 keymap_set を除く
    （JSON を読み直してから除去・書き戻し。既存の参照元の掃除〔`parent_refs_cleanup.py` の除去処理〕の書き方に倣う）。
    別名保存・途中の書込み失敗・後処理の失敗では除かない（失敗は握りつぶさず保存結果の警告として扱う。既存の後処理の失敗の扱いに揃える）。
  - これは正本 §5.8.1「除去は参照元の掃除のみ」の例外（暫定 §5.4 に明記済み）。

### §5.5 既定ファイル名と除外撤廃

- `keyseq/application/config_service/save_path_resolution.py`:
  - `resolve_keymap_file_base_name` の優先順位を **source_path（現行条件）→（`label` が空なら構成セットの stem / `label` があれば `label`）→ `id` → `keymap`** に変える。
    構成セットの stem は保存先 keymap_set パスの stem（未設定なら `id` へ）。同一計画内の衝突は現行の連番回避。
  - `default_trigger_set_path` の引数名 `keymap_set_path` を実態（親 keymap の保存先）に合わせて **`parent_keymap_path`** へ改名する（task_02 reviewer 参考指摘）。
- `child_save_rows.py:202-208` の `SHARE_NEW_COLLIDES` 補正の対象に **CHILD_TRIGGER_SET を加える**（trigger_set の除外を撤廃）。
- 個別「トリガー一覧を保存」のフォールバック名（§5.5 末尾）は task_03 で扱う（本タスクでは触らない）。

### テスト（追加・更新）

- 既存テストの期待値更新は既定名の変更（keymap の既定ファイル名が id → label / 構成セット stem）と除外撤廃によるもののみ。アサーションを緩めない。
- 新規:
  1. 自動作成キーマップ・Import した子（source_path なし）が、既定保存先に**同名の既存ファイル**があっても行に出て、既定が別名保存になる（黙って SKIP にならない）。
  2. keymap の既定名: label 空 → 構成セット stem（複数あれば連番）/ label あり → label / 構成セット未設定 → id。
  3. trigger_set の既定名が同名既存ファイルと衝突 → 既定が別名保存（除外撤廃）。
  4. keymap を別名保存に選び直す → ファイル未作成の trigger_set の既定名が追従。
  5. keymap を「保存しない」→ keymap ファイルの `trigger_set_path` は旧値・未保存マークが残る。
  6. 移行した trigger_set の初回保存: 共有状況が「別の構成」にならない / 書込み後 `_parent_refs` に keymap が加わり移行元 keymap_set も残る /
     keymap_set 上書き保存成功後の後処理で移行元が除かれる / 別名保存では除かれない / 書込み失敗では除かれない。

### 設計メモ / 制約

- §5.8.4 の既存の表・優先規則は変えず、対象（trigger_set の追加・移行時の「現在の親」扱い）だけを広げる。
- 後処理は保存計画の最後（keymap_set・startup の書込み後）に置き、失敗しても保存自体は成功扱い（既存の best-effort の範囲規定〔§5.8.6〕に揃える）。

## 読むファイル

- `instructions/history/25_trigger_list_per_keymap.md` §5.2〜§5.5（該当節のみ）
- `instructions/common/spec_detail/data_schema/5_08_04_share_state.md` / `5_08_01_parent_refs.md`（除去の規約）
- `keyseq/presentation/controllers/config_io/child_save_rows.py`（全体）/ `child_save_plan.py:40-100`
- `keyseq/application/config_service/save_path_resolution.py:1-200`
- `keyseq/application/config_service/save_plan_execution.py`（後処理の置き場所・保存成功後の反映）
- `keyseq/application/config_service/parent_refs_cleanup.py:1-80`（除去の書き方の手本）
- `keyseq/presentation/controllers/config_io/keymap_set_io.py:160-360`（保存先変更時の再計算）
- 手本のテスト: `tests/test_per_keymap_bulk_save.py:1-80` / `tests/test_child_save_rows.py:1-60`

## 含まない

- 個別保存・個別読込の規則（個別「トリガー一覧を保存」のフォールバック名を含む）（**task_03**）
- 参照辿り 3 段・孤児棚卸し・keymap_set の判別（task_04）/ 入力判定（task_05）/ UI（task_06）/ 改名（task_07）
- task_02 reviewer 参考の `keymap_set_io.py` set_dirty 判定の重複の一本化（挙動に影響しないため本フェーズでは扱わない）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq` clean
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` 全 pass（skip 7 据え置き）
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` 全 pass
- `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` pass
- `git grep -n '"triggers"' -- keyseq/presentation` が 0 件 / `git diff --stat -- instructions` が空
- 期待値を更新した既存テストの一覧と理由を報告に含める

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_06 以降でまとめて実施。
