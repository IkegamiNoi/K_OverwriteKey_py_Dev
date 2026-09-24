# task_02_per_keymap_bulk_save

## 目的

構成セットの**一括保存**をキーマップ単位のトリガー一覧へ切り替える（暫定仕様 25 §4.2・§4.4・§5.1・§5.3〔1 点目〕・§5.4〔親の変更〕・§5.5〔trigger_set の既定名〕）。
task_01b の暫定（アクティブ分だけを旧形式の 1 trigger_set として書く）を解消し、**全キーマップのトリガー一覧を保存し、
keymap ファイルが `trigger_set_path` で参照する**形にする。

**JSON スキーマ変更（書込み側）**。application（保存計画の検証・payload・実行・保存後反映）と presentation（一覧ダイアログの行・
計画の組立・未保存の管理）に跨る。**§4.2 と §4.4 は同時に入れる**（§4.4 の「移行したら `""`」は §4.2 の「移行先は必ず書かれる」が前提。
片方だけだと旧参照が失われる）。

## 対象範囲

### 識別子

- **trigger_set の実体**: runtime で同一オブジェクトの `triggers` を持つキーマップ群を 1 実体とし、識別子 = その実体を持つ**最初のキーマップ（一覧順）の id**。
  保存計画の `(CHILD_TRIGGER_SET, key)` の key はこの id（空文字を使わない）。
- **sequence**: 識別子 = （trigger_set 実体の識別子, trigger key）。保存計画の key は文字列のまま、
  区切りに `"\x1f"` を使う合成キーとし、組立 / 分解の関数を 1 箇所に置く（区切り文字はキーマップ id・trigger key に現れない前提。
  現れた場合の扱い〔拒否 or エスケープ〕は実装判断でよいが黙って取り違えないこと）。
- application / presentation の「trigger_set は 1 つ」決め打ち箇所（`save_plan.py:28` の既定 key、`child_save_plan.py:38`、
  `save_plan_execution.py` の空以外 key の拒否、`split_payloads.py` / `save_path_resolution.py` のトップレベル内部キー参照、
  `child_save_rows.py` / `child_save_dialog.py` / `keymap_set_io.py` の `(CHILD_TRIGGER_SET, "")` 参照）を実体単位へ改める。

### payload・既定保存先・衝突回避（application）

- `split_payloads.py`:
  - trigger_set の payload を**実体ごと**に作る（トリガー 0 件かつ source_path が空の実体はファイルを作らず、参照は `""`・暫定 §5.1）。
  - **keymap ファイルの payload に `trigger_set_path` を追加**（`build_keymap_file_payload`）。値はその実体の保存先（§5.7 の表記）。
  - trigger_set の `_parent_refs` の親 = **keymap ファイル**（keymap_set ではない。§5.4）。sequence の親 = trigger_set（不変）。keymap の親 = keymap_set（不変）。
  - 組立順: keymap の保存先を先に確定 → trigger_set の既定名・親 → keymap の内容（`trigger_set_path` を含む）。
  - keymap_set payload の `trigger_set_path` は §4.4 の決定表で書く（`_legacy_trigger_set.state` = `none` / `migrated` / `same` → `""`、`unused` → 旧値を保持）。
- `save_path_resolution.py`: **trigger_set の既定保存先 = 親 keymap（実体の識別子のキーマップ）の保存先ファイルの stem**（`trigger_sets/` 配下）。
  既存 source_path があればそれを使う（現行どおり）。トップレベルの `_trigger_set_source_path` は参照しない。
- **衝突回避は保存計画全体**: sequence 同士・trigger_set 同士の `used_paths` を実体ごとではなく計画全体で共有する（暫定 §5.1）。

### 検証・実行・保存後反映（application）

- `save_plan_execution.py`:
  - **依存の 3 段化**: trigger_set の保存先が変わる（新規作成・別名保存・source_path と異なる解決先）のに、親 keymap の計画が SKIP なら依存エラー
    （既存の sequence → trigger_set と同じ扱い・`allow_deferred_index` の規則も同じ）。
  - 保存後、各キーマップ要素の trigger_set 内部キー（source_path / parent_refs）を更新し、共有実体では同じ値を全要素へ反映する。
  - **トップレベルの `_trigger_set_source_path` / `_trigger_set_parent_refs`（task_01b の暫定）の生成・参照をやめる**。
    保存成功で `_legacy_trigger_set` を `{"state": "none", ...}` 相当へ更新する（再保存で旧値を書き戻さないため）。`unused` はそのまま。

### presentation

- `child_save_rows.py` / `child_save_dialog.py`: trigger_set の行を**実体ごと**に出す（行の表示名に親キーマップの表示名を含める）。
  sequence の行も合成キーで扱い、表示名にキーマップが分かるようにする。共有状況の比較対象は trigger_set = 保存予定の親 keymap のパス。
- `child_save_plan.py`: 実体ごとの trigger_set 行・合成キーの sequence 行で計画を組む。
- `keymap_set_io.py`: 依存確認・保存先変更時の再計算・上書き確認・保存後の反映・未保存のクリアを実体単位へ（現行の単一 trigger_set の処理を一般化）。
- **§4.2 移行先**:
  - 読込で `_legacy_trigger_set.state == "migrated"` なら、移行先キーマップを未保存（keymap の dirty）にし、構成セットも未保存にする。
  - 一括保存の一覧ダイアログで、移行先キーマップの行は**「保存しない」を選べない**（保存 / 別名保存のみ）。
    個別「キーマップを保存」で移行先だけを書いた場合は keymap_set を未保存のまま残す。
- `dirty_state.py`: trigger_set の未保存状態（dirty / imported / source_path）を**実体ごと**に持つ（キーマップ要素の内部キー
  `_trigger_set_dirty` / `_trigger_set_imported` / `_trigger_set_source_path` を正とし、共有実体は同値に揃える）。
  既存のメソッド名（`mark_trigger_set_dirty` 等）は残し、**対象の実体を省略したらアクティブキーマップの実体**を対象にする
  （呼び出し元〔trigger_panel_controller / sequence_file_io / trigger_set_file_io〕の変更を最小にするため）。

### テスト（追加・更新）

- 既存テストの期待値更新はスキーマ変更（実体ごとの行・合成キー・keymap の `trigger_set_path`・親 = keymap）によるもののみ。アサーションを緩めない。
- 新規（往復テストを先に書く・暫定 §12）:
  1. **旧形式を読込 → 無編集で保存 → 再読込**でトリガーが残る。keymap ファイルに `trigger_set_path`・keymap_set の `trigger_set_path` は `""`。
  2. 移行後、**別のキーマップをアクティブにしてから保存 → 再読込**しても旧トリガー一覧は移行先に付いたまま。
  3. 移行先キーマップの行で「保存しない」を選べない（計画組立 / ダイアログ）。
  4. 2 つのキーマップが**同じ trigger_set を共有** → 保存計画で行は 1 つ・保存後も両方の keymap が同じパスを参照・二重化しない。
  5. 別キーマップに同じ trigger key の**新規** sequence → 別ファイルに保存される（上書きし合わない）。
  6. トリガー 0 件・source_path なしのキーマップ → trigger_set ファイルを作らず `trigger_set_path` は `""`。
  7. `unused` の構成セットを保存 → keymap_set の `trigger_set_path` に旧値が残る。
  8. trigger_set を別名保存にし親 keymap を「保存しない」→ 依存エラー（または既存規則どおりの確認）。
  9. trigger_set の `_parent_refs` に親 keymap のパスが入る。

### 設計メモ / 制約

- 現行の単一 trigger_set の処理（依存確認の 4 択・上書き確認・延期された索引更新）を**実体ごとに一般化**し、規則を変えない。
- トップレベル内部キーを残した互換分岐を作らない（task_01b の暫定を撤去するのが本タスクの目的）。
- 個別保存（trigger_set_file_io / keymap_file_io / sequence_file_io）は**アクティブキーマップの実体を対象に動き続けること**だけを保つ
  （規則の変更は task_03）。

## 読むファイル

- `instructions/history/25_trigger_list_per_keymap.md` §4.2・§4.4・§5.1・§5.3・§5.4・§5.5（該当節のみ）
- `keyseq/application/save_plan.py`（全体）/ `keyseq/presentation/controllers/config_io/child_save_plan.py`（全体）
- `keyseq/application/config_service/split_payloads.py`（全体）/ `save_path_resolution.py:1-180`
- `keyseq/application/config_service/save_plan_execution.py`（全体）
- `keyseq/presentation/controllers/config_io/child_save_rows.py`（全体）/ `child_save_dialog.py:1-60, 200-300`
- `keyseq/presentation/controllers/config_io/keymap_set_io.py:60-150, 160-530, 640-710`
- `keyseq/presentation/controllers/dirty_state.py`（全体）
- `keyseq/domain/keymap_triggers.py`（全体）/ `keyseq/application/config_service/split_loading.py:320-420`（読込側の内部キーの置き方）
- 手本のテスト: `tests/test_save_plan.py:1-80` / `tests/test_child_save_rows.py:1-60`

## 含まない

- source_path を持たない子を常に行へ出す（§5.2）/ 移行した trigger_set の `_parent_refs` の特別扱いと後処理（§5.4 の移行部分）/
  keymap の既定ファイル名（label・構成セット stem）と「同名既存ファイル → 別名保存」の trigger_set 除外撤廃（§5.5）/
  keymap 別名保存時の trigger_set 既定名の再計算と「keymap を保存しない → 旧値・未保存マークを残す」（§5.3 の 2・3 点目）（**task_02b**）
- 個別保存・個別読込の規則（**task_03**）/ 参照辿り・孤児棚卸し（task_04）/ 入力判定（task_05）/ UI（task_06）/ 改名（task_07）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq` clean
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` 全 pass（skip 7 据え置き）
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` 全 pass
- `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` pass
- `git grep -n '"triggers"' -- keyseq/presentation` が 0 件
- `git grep -n 'INTERNAL_TRIGGER_SET_SOURCE_PATH\|INTERNAL_TRIGGER_SET_PARENT_REFS' -- keyseq` の残存箇所を報告（トップレベル runtime を読む箇所が残っていないこと）
- 期待値を更新した既存テストの一覧と理由を報告に含める

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_06 以降でまとめて実施。
