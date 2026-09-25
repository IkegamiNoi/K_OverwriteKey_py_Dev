# task_04_reference_scan_three_levels

## 目的

孤児ファイルの棚卸し（正本 §5.8.9）と参照元の掃除（§5.8.1）の参照辿りを、キーマップ単位のトリガー一覧に合わせる（暫定仕様 25 §6「参照辿り・孤児棚卸し」/ §3.1 末尾「keymap_set の判別」）。
**未移行の構成セットのトリガー一覧・新形式の keymap が参照するトリガー一覧のどちらも孤児として隔離されない**ことが最重要（誤って隔離 → 削除でデータ消失）。

**JSON スキーマ不変**。application（`config_service/reference_scan.py` / `orphan_scan.py` / `parent_refs_cleanup.py`）に限定。presentation の表示・文言は変えない。

## 対象範囲

### `reference_scan.py`（参照集合の構築）

- 参照辿りを **keymap_set → keymap → trigger_set → sequence の 3 段**にする:
  - keymap_set の `keymaps[]` 参照先の **keymap ファイルの内容を読み**、その `trigger_set_path` を trigger_set の参照に加える（読込は既存の `_load_source` とキャッシュ・理由コード付きの「読めなかった参照側」の仕組みを流用）。
  - trigger_set → sequence は現行どおり。
- **旧形式の keymap_set の `trigger_set_path` も参照として数え続ける**（未移行の構成セットのトリガー一覧を孤児にしない）。空文字は無視（現行どおり）。
- 読めなかった keymap は既存の「読めなかった参照側（理由コード付き）」として扱う（新しい理由コードは作らない。既存の区分で足りなければ報告で指摘する）。
- **keymap_set の判別**（`_is_keymap_set`・98-105）: keymap ファイルも `trigger_set_path` を持つようになったため、`trigger_set_path` の有無だけで keymap_set と判定しない。
  **`mappings` キーを持つ JSON は keymap_set と判定しない**（keymap ファイルの識別子。keymap_set は `mappings` を持たない）。その上で従来のキー（`keymaps` / `active_keymap_path` / `hotkey_presets_path` / `trigger_set_path`）のいずれかを持てば keymap_set とする（旧形式で `trigger_set_path` しか持たない keymap_set を取りこぼさない）。

### `orphan_scan.py`（保護対象・候補判定）

- **保護対象**（`collect_protected_paths`）に、現在の runtime の**全キーマップ**の trigger_set（キーマップ要素の `_trigger_set_source_path`）と、その全トリガーの sequence の source_path を含める（task_02 時点はアクティブ実体のみ）。共有実体は重複を除く。
- 候補の形状検証（`orphan_scan.py:14` の表）は変えない（keymap ファイルに `trigger_set_path` が増えても keymap 候補の判定に影響しないことをテストで確認）。

### `parent_refs_cleanup.py`（参照元の掃除）

- 列挙対象（`_iter_child_paths`）を runtime の**全キーマップ**の trigger_set と全 sequence に広げる（task_02 時点はアクティブ実体のみ）。共有実体は 1 回だけ。
- **保護対象の親**（`_protected_parent_path`）: trigger_set の親は keymap（そのキーマップ要素の保存先）、sequence の親は trigger_set。keymap の親は現在の keymap_set（現行どおり）。
  移行した trigger_set の `_parent_refs` に残る移行元 keymap_set（task_02b の後処理前の状態）は、現在の keymap_set 自身なら保護対象として扱う（実在するので除去されない既存規則のままでよい。挙動を確認するテストを足す）。

### テスト（追加・更新）

- 既存テストの期待値更新は、参照が 3 段になったこと・保護対象が全キーマップに広がったことによるもののみ。アサーションを緩めない。テスト補助で runtime を書き換えない。キーマップ 0 個のフィクスチャを作らない。
- 新規:
  1. 新形式: keymap_set → keymap（`trigger_set_path` あり）→ trigger_set → sequence が参照集合に入る（孤児にならない）。
  2. 旧形式: keymap_set の `trigger_set_path` だけが指すトリガー一覧・その sequence が参照集合に入る。
  3. 新旧混在（keymap 側参照と keymap_set 側の旧参照が別ファイル）→ 両方が参照集合に入る。
  4. 読めない keymap ファイル → 理由コード付きで「読めなかった参照側」に出る・その keymap が指すはずの trigger_set は参照集合に入らない（既存の「壊れた親 = 無傷の子が消えるリスク」の警告の対象になる）。
  5. `mappings` と `trigger_set_path` を持つ keymap ファイルが keymap_set と判定されない / `trigger_set_path` だけを持つ旧形式 keymap_set は keymap_set と判定される。
  6. 保護対象・参照元の掃除の列挙に、アクティブ以外のキーマップの trigger_set と sequence が含まれる・共有実体は重複しない。

## 読むファイル

- `instructions/history/25_trigger_list_per_keymap.md` §3.1・§6（該当節のみ）
- `instructions/common/spec_detail/data_schema/5_08_09_orphan_sweep.md`（参照集合・保護対象・読めない参照側の節のみ）/ `5_08_01_parent_refs.md`（掃除の節のみ）
- `keyseq/application/config_service/reference_scan.py`（全体）/ `orphan_scan.py`（全体）/ `parent_refs_cleanup.py`（全体）
- `keyseq/domain/keymap_triggers.py`（`iter_trigger_sets` 等）
- 手本のテスト: `tests/test_reference_scan.py:1-80` / `tests/test_orphan_scan.py:1-80` / `tests/test_parent_refs_cleanup.py:1-80`

## 含まない

- 棚卸し・掃除の UI（ダイアログ・文言）の変更
- 入力判定（task_05）/ キーマップ管理 UI（task_06）/ 改名（task_07）/ `instructions/` 配下の編集（task_08）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq` clean
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` 全 pass（skip 7 据え置き）
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` 全 pass（ハングしないこと）
- `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` pass
- `git status --short -- instructions` は本タスク定義のみ
- 期待値を更新した既存テストの一覧と理由を報告に含める

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_06 以降でまとめて実施（棚卸しダイアログで孤児に出ないことの確認を含める）。
