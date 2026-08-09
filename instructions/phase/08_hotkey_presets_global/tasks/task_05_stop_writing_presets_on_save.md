# task_05_stop_writing_presets_on_save

## 目的

keymap_set の**保存側**からプリセットを切り離す（暫定仕様 07 **§2 指摘②・④** / **§3**・
受入条件 **2 / 4**）。具体的には次の 2 つ:

1. **keymap_set payload から `hotkey_presets_path` の生成を停止**する（新規保存では書かない）。
2. **保存カスケードからプリセットファイルの書出を除外**する
   （`save_runtime_data` はプリセットを書かない ＝ **唯一の書き手はプリセットマネージャ**）。

**レイヤ制約**: **application 限定**（`config_service/split_payloads.py` と
`config_service/save_plan_execution.py`）。**domain / presentation は不変**。読込側（task_02・task_04 の到達点）も不変。
本タスクは**保存 JSON の形が変わる**（keymap_set からキーが 1 つ減る）。

## 対象範囲（application 限定・2 ファイル + テスト）

### 1. `keyseq/application/config_service/split_payloads.py`

- **`build_keymap_set_payload`（`:293-`）**
  - キーワード引数 **`hotkey_presets_path` を削除**する。
  - 返す dict から **`"hotkey_presets_path"` の行（`:337`）を削除**する。
    **他のキーの順序は一切変えない**（`trigger_set_path` の次が `active_keymap_path` になる）。
- **`build_split_payloads`（`:25-106`）**
  - `hotkey_presets_path` の算出（**`:39-43`**）を削除する。
  - `hotkey_presets_payload` の生成（**`:81-85`**）を削除する。
  - `build_keymap_set_payload(...)` 呼び出しから `hotkey_presets_path=` の受け渡し（**`:79`**）を削除する。
  - 返却 dict から **`"hotkey_presets_path"` と `"hotkey_presets"`（`:102-103`）を削除**する。
- 使われなくなった import / ローカル変数が出たら削除する（**それ以外の整形はしない**）。

### 2. `keyseq/application/config_service/save_plan_execution.py`

- **`:134-137` のプリセット書込（`service.repository.save_json(payloads["hotkey_presets_path"], payloads["hotkey_presets"])`）を削除**する。
  他の書込（sequences → trigger_set → keymaps → keymap_set → startup）の**順序は変えない**。
- `apply_saved_child_paths` にプリセット参照は無いので**触らない**。

### 設計メモ / 制約

- **`ConfigService.HOTKEY_PRESETS_RELATIVE_PATH` は削除しない**。task_01 の
  `load_global_hotkey_presets_path` が既定値として使っている。
- **`ensure_split_config_dirs` の `user/hotkey_presets` ディレクトリ作成は残す**
  （プリセットマネージャの保存先。task_06 が使う）。
- **既存 keymap_set に残る `hotkey_presets_path` の能動削除はしない**
  （`keymap_set.pop(...)` 等を書かない。`data_schema.md` の既存キー削除禁止。再保存で自然消滅する）。
- 読込側（`split_loading.py`）・`apply_global_defaults`・presentation は**この タスクでは変更しない**。

### 3. テスト（追加・更新まで実装範囲。**実行は依頼しない**）

**更新（`tests/test_save_plan.py`）** — 保存 JSON の変更に追随させる。**アサーションは緩めない**:

- `_build_keymap_set_payload`（`:77-85`）から `hotkey_presets_path=` の引数を外す。
- `test_saved_keymap_set_json_keeps_stable_key_order`（`:87`）の `expected_key_order` から
  **`"hotkey_presets_path"` を削除**する（**残りのキー順は不変**。この特性テストが保存 JSON の
  バイト安定性を固定している正本）。
- `test_none_and_empty_plan_have_equivalent_output`（`:135`）
  - 比較対象パス（`:142-149`）から `user/hotkey_presets/default.json` を外す。
  - 期待 dict（`:159-171`）から `"hotkey_presets_path"` を削除する。
  - プリセットファイルの内容を検証する箇所（**`:211-216`**）は、**「保存後にプリセットファイルが
    生成されていない」ことの確認へ置き換える**（受入条件 4）。
- `test_single_skip_omits_only_the_selected_child`（`:268`）の `:289-291`
  → **`assertTrue(os.path.exists(...))` を `assertFalse` へ**（子スキップに関わらず書かれない）。
- `test_writes_children_before_parent_and_startup`（`:568`）の期待パス列（`:576-586`）から
  **`user/hotkey_presets/default.json` を削除**する。

**追加（`tests/test_save_plan.py`）**:

1. **受入条件 4**: `save_runtime_data` を実行しても
   **`<config_root>/user/hotkey_presets/default.json` が作られない**
   （`runtime["hotkey_presets"]` に値がある状態で確認する）。
2. **既存のプリセットファイルが `save_runtime_data` で上書きされない**
   （事前に別内容のプリセットファイルを置き、保存後も内容が変わらないことを値で確認）。
3. **受入条件 2**: 保存された keymap_set.json に **`hotkey_presets_path` キーが無い**。
4. **後方互換（受入条件 5 の保存側）**: 既存の `hotkey_presets_path` を持つ keymap_set を
   読み込んでから保存し直すと、**例外なく完走し、再保存後の keymap_set からキーが消える**
   （＝能動削除ではなく生成停止による自然消滅であることを固定する）。

**`tests_ui`**: 保存フローの特性テストが `hotkey_presets` / `hotkey_presets_path` を前提に
していないか確認し、落ちる場合のみ期待値を更新する（**更新したファイル名とテスト名を報告に列挙**）。

## 含まない

- **プリセットマネージャの即時保存（成否付き）** → **task_06**
  （本タスク完了時点では「プリセットの書き手が一時的に居なくなる」中間状態になる。
  これは設計どおりであり、先取りして書き手を足さないこと）
- 読込側（`split_loading.py` / `apply_global_defaults` / 入口台帳）の変更 → task_02・task_04 で完了済
- keymap_set からの `hotkey_presets_path` の**能動削除**（仕様上禁止）
- `HOTKEY_PRESETS_RELATIVE_PATH` の削除 / `ensure_split_config_dirs` からの
  `user/hotkey_presets` 除去
- 統合確認・実機目視 → **task_07** / 正本反映 → **task_08**

## 確認

`.venv` の python で実行（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。実測は `verifier`。

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests` が **pass**（基準線 **186** ± 更新分 + 追加 4 件）
- `-m unittest discover -s tests_ui` が **pass**（基準線 **181**。更新が必要なら件数と理由を報告）
- `-m tests.smoke_app` が pass
- 追加テスト 1〜4 が存在し pass すること
- `grep` で **`keyseq/application/config_service/` 配下に
  `payloads["hotkey_presets"]` / `payloads["hotkey_presets_path"]` の参照が残っていない**こと
- 保存された keymap_set.json のキー順が `expected_key_order`（`hotkey_presets_path` を除いた 10 個）と
  一致すること

## 完了条件

- 上記確認がすべて pass し、**`reviewer` 採用**（観点: 受入条件 2・4 の達成 /
  keymap_set 側キーの**能動削除をしていない**か / 保存順序と残りのキー順を変えていないか /
  読込側・presentation・domain へ波及していないか / task_06 の先取り〔書き手の追加〕が無いか /
  既存テストの更新がアサーション緩和になっていないか）。
- **実機目視は本タスクでは行わない**（**task_07** でまとめて実施）。
