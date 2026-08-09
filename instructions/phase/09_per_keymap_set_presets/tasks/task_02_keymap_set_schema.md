# task_02_keymap_set_schema

## 目的

keymap_set 側に**個別プリセットのスキーマ**を用意する（暫定仕様 08 **§2 / §3-1 / §3-5**・
受入条件 **3 / 10 / 11**）。

1. **`hotkey_presets_individual`（bool・既定 false）** を追加する
2. **`hotkey_presets_path` の payload 生成を復活させる**（phase 08 で止めたキーを、個別パスとして再利用）
3. **移行規則**: **フラグを持たない既存 keymap_set は常に OFF**（**値で判定**）

**レイヤ制約**: **domain（既定値・互換化）+ application（runtime への取り込み・payload 生成）**。
**presentation は不変**。**読込側の解決順序（個別 → グローバル）はまだ変えない**（task_03）。
本タスク時点では 2 キーが**往復するだけ**で、プリセットの読込先は依然グローバル 1 本。

## 対象範囲

### 1. `keyseq/domain/config.py`

- **`DEFAULT_CONFIG` へ 2 キーを追加**する（`hook_keys_individual` の並びに合わせる）:
  - `"hotkey_presets_individual": False`
  - `"hotkey_presets_path": ""`
- **`ensure_config_compatibility` へ正規化を追加**する（`hook_keys_individual` の行の近くに置く）:
  - `hotkey_presets_individual` … **真偽値のときだけその値・それ以外は `False`**
    （`bool()` で潰さない。手編集の `"false"` のような文字列が True になるのを防ぐ）
  - `hotkey_presets_path` … **文字列なら `strip()`・それ以外は `""`**
- **`resolve_hook_keys_individual` を流用しない**（あれは「フラグ無し + 非空なら ON」の
  移行判定であり、本キーでは**残置パスが個別指定として復活してしまう**。§3-5）。
  専用の純関数を作るかインラインにするかは実装者判断でよいが、**判定は値のみ**で行うこと。

### 2. `keyseq/application/config_service/split_loading.py`

- `build_runtime_data_from_split` の**キーコピーのループ**（`:90-97` 付近）へ
  **`hotkey_presets_individual` と `hotkey_presets_path` を追加**する
  （`if key in keymap_set` の既存パターンに乗せる。**キーが無ければ runtime の既定＝OFF / 空**）。
- **`hook_keys_individual` のような専用の解決行は足さない**（移行判定を通さない ＝ §3-5）。
- **プリセットの読込先はこのタスクでは変更しない**（`load_global_hotkey_presets` のまま）。

### 3. `keyseq/application/config_service/split_payloads.py`

- `build_keymap_set_payload` の返却 dict へ 2 キーを追加する。**挿入位置は次のとおり**
  （`trigger_set_path` の直後 = phase 08 以前に `hotkey_presets_path` があった位置）:

  ```
  trigger_set_path
  hotkey_presets_path          ← 追加
  hotkey_presets_individual    ← 追加
  active_keymap_path
  keymaps
  hook_stop_key
  ...
  ```

- 値の作り方:
  - `hotkey_presets_individual` … runtime の値を**真偽値のときだけ採用・それ以外は `False`**
  - `hotkey_presets_path` … runtime の値を文字列化して `strip()`。
    **OFF でも空文字化しない**（暫定仕様【N】。hook キーのように「OFF なら常に `""`」に**しない**）
- **パス表記の変換はしない**（runtime が保持している表記のまま書く）。
  個別パスの算出・`to_config_relative_or_absolute` の適用は **task_04** の担当。

### 設計メモ / 制約

- **`build_keymap_set_payload` は固定キー集合**なので、追加箇所は上記 1 箇所で一意。
- **保存 JSON のキー順は特性テストが固定している**
  （`tests/test_save_plan.py::test_saved_keymap_set_json_keeps_stable_key_order`）。
  上記の順序へ**期待値を更新**すること（**順序を変えるのは今回の追加分だけ**）。
- **既存キーの能動削除はしない**。
- runtime に 2 キーが載ることで、`tests_ui` の**スタブ dict 比較**（`new_empty_data` を
  `{"empty": True}` へ差し替える類）や `assertEqual(self.app.data, {...})` が落ちる可能性がある。
  落ちたら**テスト側を追従**させる（実装ではなくテストの更新が正しい）。

## 含まない

- **解決順序（個別 → 読めなければグローバル）** → **task_03**
- **config 外パスの無効化** → **task_03**
- **個別ファイルの既定パス算出・保存先の切替** → **task_04**
- **切替 UI** → **task_05** / **Import の強制 OFF・別名保存の複製** → **task_06**
- 正本 `instructions/common/` の更新 → **task_08**

## 確認

`.venv` の python で実行（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。実測は `verifier`。

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests` が **pass**（基準線 **204** + 追加分）
- `-m unittest discover -s tests_ui` が **pass**（基準線 **186**。更新が要る場合は件数と理由を報告）
- `-m tests.smoke_app` が pass

### テスト（追加・更新まで実装範囲。**実行は依頼しない**）

**更新**:

1. `tests/test_save_plan.py::test_saved_keymap_set_json_keeps_stable_key_order` の
   `expected_key_order` へ **`hotkey_presets_path` / `hotkey_presets_individual` を上記位置で追加**。
   **他のキーの順序は動かさない**。
2. 同ファイルの `test_none_and_empty_plan_have_equivalent_output` の**期待 dict** に 2 キーを追加。

**追加**:

3. **移行規則（受入条件 3）**: `hotkey_presets_individual` を**持たない** keymap_set
   （`hotkey_presets_path` に**非空の値が残っている**もの）を読み込むと、
   runtime の `hotkey_presets_individual` が **`False`** になる。
   → **残置パスが個別指定として復活しない**ことを値で固定する。
4. フラグが **`true`** の keymap_set を読み込むと runtime が `True` になり、
   `hotkey_presets_path` も runtime へ入る（往復の確認）。
5. **真偽値でない `hotkey_presets_individual`**（`"true"` / `1` / `None`）は **`False`** になる。
6. **OFF のまま保存しても `hotkey_presets_path` が空文字化されない**（【N】）。
   ON / OFF の両方で payload に 2 キーが出ることを確認する。
7. `ensure_config_compatibility` が 2 キーを正規化する（非文字列パス → `""` / 非真偽フラグ → `False`）。

## 完了条件

- 上記確認がすべて pass し、**`reviewer` 採用**（観点: **移行判定に
  `resolve_hook_keys_individual` を流用していないか**〔最重要〕/ 判定が**値のみ**か /
  OFF でパスを空文字化していないか / **キー順の変更が追加分だけ**か /
  読込側の解決順序・presentation へ波及していないか / 既存テストの更新がアサーション緩和でないか）。
- **実機目視は本タスクでは行わない**（**task_07** でまとめて実施）。
