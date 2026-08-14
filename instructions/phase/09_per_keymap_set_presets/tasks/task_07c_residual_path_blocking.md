# task_07c_residual_path_blocking

## 目的

**`hotkey_presets_individual` キーを持たない keymap_set では、残置している
`hotkey_presets_path` も引き継がない**（暫定仕様 08 **§2【§3-5】/ §3-2 / §3-5**〔v0.8 で追加〕・
受入条件 **3**）。

task_07 の実機目視で発現した不具合の是正。phase 08 以前の keymap_set には
**旧グローバルパス `user/hotkey_presets/default.json`** が残っており、v0.7 までは
**フラグだけ OFF に倒してパスは runtime へ載せていた**ため、**初回 ON + OK の保存先が残置パス**に
なっていた（stem 由来の名前にならない / 同じ残置パスを持つ複数セットが 1 ファイルを無警告共有する /
`global/` 配下でも現行グローバルと同一でもないため **task_07b の【O4】でも捕まらない**）。

**レイヤ制約**: **application 限定**。**presentation 不変・domain 不変・スキーマ不変・
保存先算出（task_04）不変・【O3】【O4】不変**。

## 対象範囲（application 限定・1 ファイル）

### 1. `keyseq/application/config_service/split_loading.py` — `build_runtime_data_from_split`

`:240-249` の「keymap_set から runtime へ引き継ぐキー」のうち、**`hotkey_presets_path` だけを
条件付きにする**。

- **`hotkey_presets_individual` キーが keymap_set に存在しない場合、`hotkey_presets_path` を
  runtime へ載せない**（`new_default_data()` 由来の**空文字のまま**にする。Import の強制 OFF
  〔`clear_individual_hotkey_presets`〕と同じ値）。
- **判定はキーの有無**（`"hotkey_presets_individual" in keymap_set`）で行う。
  **フラグが `false` でもキーがあればパスは載せる**（【N】の「OFF でもパス保持・再 ON で同じファイルへ
  戻る」を壊さないため）。**フラグ自体の判定は従来どおり値**（キーが無ければ false）。
- 他のキー（`HOOK_KEY_FIELDS` / `keyboard_layout` 等）の引き継ぎは**変えない**。

### 設計メモ / 制約

- **落とす場所は `build_runtime_data_from_split` の 1 箇所だけ**。
  - **`domain/config.py` の `ensure_config_compatibility` へ入れない**。あちらは runtime 全般の
    正規化で、**メモリ上の runtime は常に 2 キーを持つ**ため、入れると
    「OFF + パス保持」（【N】）まで潰れる。
  - **`load_legacy_runtime_data`（Import 経路）にも入れない**。task_06 の
    `clear_individual_hotkey_presets` が既に強制 OFF + 空文字にしている。
- **`hotkey_presets_individual` の移行規則（フラグ無しは常に OFF）は既に実装済み**（task_02）。
  本タスクは**パス側だけ**を追加で塞ぐ。
- **キーの値を書き換えるのは runtime 側だけ**。keymap_set ファイルは読むだけで、
  **本タスクでは保存も移行も行わない**（次に保存されたとき payload が空文字を書く＝既存の挙動）。
- **フラグキーを持つ keymap_set で `hotkey_presets_path` を手編集した場合は、引き続き記録どおり
  使う**（暫定仕様 v0.8 の既知の制約。値のブラックリスト化は §4 で却下済み）。

## 含まない

- **config 外パスの読み出し許容**（暫定仕様 v0.8【O2】）→ **task_07d**
- **トグル時の一覧の読み直し・破棄確認・OFF での書き込み**（v0.8【I】【H2 撤回】）→ **task_07e**
- 既存 keymap_set ファイルの**自動書き換え・移行ツール**（読み込み時に runtime で無視するだけ）
- 正本 `spec_detail/` への反映・`codebase_map.md` 更新 → **task_08**

## 確認

`.venv` の python で実行（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。実測は `verifier`。

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests` が **pass**（基準線 **229** + 追加分）
- `-m unittest discover -s tests_ui` が **pass**（基準線 **206** + 追加分）
- `-m tests.smoke_app` が pass

### テスト（追加まで実装範囲。**実行は依頼しない**）

**`tests/test_config_service.py`**:

1. **残置パスの遮断**: `hotkey_presets_individual` **キー無し** + `hotkey_presets_path` =
   `user/hotkey_presets/default.json` の keymap_set を読むと、**runtime の `hotkey_presets_path` が空文字**・
   **`hotkey_presets_individual` が false**・**プリセットはグローバル由来**になる。
2. **【N】の保持**: `hotkey_presets_individual` = **false（キーあり）** + `hotkey_presets_path` =
   `user/hotkey_presets/main.json` を読むと、**パスが保持される**。
3. **ON は従来どおり**: フラグ true + パスありで、**そのパスから読む**（task_03 の既存挙動が壊れていない）。
4. **保存先算出**: 1 の runtime に対し `resolve_hotkey_presets_save_path(..., individual=True)` が
   **`user/hotkey_presets/<keymap_set の stem>.json`** を返す（残置パスではない）。

**`tests_ui/test_app_ui_flows.py`**:

5. 1 の状態の App で `save_hotkey_presets(..., individual=True)` を呼ぶと、
   **`user/hotkey_presets/<stem>.json` が新規作成**され、**旧グローバル `user/hotkey_presets/default.json` が
   作られない / 変更されない**。

## 完了条件

- 上記確認がすべて pass し、**`reviewer` 採用**（観点: 判定が**キーの有無**か〔値ではない〕/
  **false + キーありでパスが保持される**か〔【N】〕/ 落とす場所が `build_runtime_data_from_split` の
  1 箇所に留まっているか〔domain・Import 経路へ波及していないか〕/ 他キーの引き継ぎを変えていないか /
  後続タスク（07d / 07e / 08）の先取りがないか）。
- **実機目視は task_07 の観点リスト（項目 2）でまとめて実施**する（本タスクでは行わない）。
