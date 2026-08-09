# task_04_individual_save_target

## 目的

**個別プリセットの保存先を決め、プリセットマネージャの書込先を切り替える**
（暫定仕様 08 **§2【G】【B】【H】【O】 / §3-3**・受入条件 **5 / 11**）。
task_03 で読込側は個別／グローバルへ分岐するようになったが、**個別ファイルへ書く経路がまだ無い**。
本タスクでそれを通す。

**レイヤ制約**: **application（保存先の算出 + 保存 API）+ presentation（書込先の受け渡し）**。
**domain 不変・読込側（task_03 の到達点）不変・保存カスケード不変**。
**UI（チェックや保存先表示）は task_05**。本タスクは**内部の配線まで**。

## 対象範囲

### 1. `keyseq/application/config_service/save_path_resolution.py` — 既定パスの算出

`default_trigger_set_path`（`:163-178`）と**同じ流儀**で、個別プリセットの既定パスを返す関数を追加する:

```python
def default_individual_hotkey_presets_path(service, keymap_set_path: str, *, config_root: str) -> str:
```

- ファイル名は **`slugify_file_stem(keymap_set の stem)`**、空になったら**フォールバック `default`**
  （`default_trigger_set_path` と同じ `stem or "default"` の形）。
- 置き場は **`user/hotkey_presets/` 直下**（`ConfigService.HOTKEY_PRESETS_RELATIVE_PATH` の
  **ディレクトリ部分**を使う。**新しい定数を増やすかは実装者判断**だが、
  `"hotkey_presets"` の文字列をこの関数の外へ散らさないこと）。
- 返すのは **`_resolve_config_relative_path` を通した解決済みパス**（`default_trigger_set_path` と同じ）。
- **既存ファイルの有無を考慮しない**（衝突を避けて別名へ逃がさない。正本 §5.6 と同じ）。
- **`split_base_dir` は取らない**（個別プリセットは子ファイルではないため。§2【B】）。

> **注意**: グローバル既定は `user/hotkey_presets/**global**/default.json`（task_01）なので、
> stem が `default` でも**衝突しない**。これが phase 09 で `global/` を切った理由。

### 2. `keyseq/application/config_service/__init__.py` — 保存 API

現在の `save_global_hotkey_presets`（`:467-482`）に対し、**保存先を選べる形**にする。
**どちらの形でもよい**が、**呼び出し側が「個別かグローバルか」を決めて渡す**こと:

- 案 a: `save_hotkey_presets(presets, *, config_root, stored_path)` を新設し、
  `save_global_hotkey_presets` をその薄いラッパにする（**task_03 の読み出し側と同じ構造**）
- 案 b: `save_global_hotkey_presets` に省略可能な保存先引数を足す

**推奨は案 a**（読み出し側で `load_hotkey_presets_file` / `load_global_hotkey_presets` の
2 段構えにしたので、保存側も対称になる）。

- **例外は握り潰さない**（現行どおり送出。成否への変換は presentation の責務）。
- 書き出す形は不変（`{"hotkey_presets": safe_deepcopy(presets)}`）。
- 保存先は **`resolve_config_path` で解決**してから `repository.save_json` へ渡す（現行どおり）。

### 3. `keyseq/application/config_service/split_loading.py` — 保存先の決定（読み出しと対称に）

runtime から**書込先の保存表記パス**を返す関数を追加する（**判定は task_03 の
`resolve_individual_hotkey_presets_path` を再利用**する）:

```python
def resolve_hotkey_presets_save_path(service, runtime, *, config_root, keymap_set_path) -> str:
```

- **個別指定が有効**（task_03 の判定が非空）… **その保存表記パス**を返す
- **個別指定 ON だがパスが未設定**（＝ ON にした直後で、まだ実体もパスも無い）…
  **既定パスを算出して返す**（§1 の関数。**`to_config_relative_or_absolute` で
  config 相対の保存表記へ**戻す。正本 §5.7）
- **個別指定 OFF**（フラグ無しを含む）… **空文字**を返す（＝グローバルへ）
- **config 外の個別パスは無効**として OFF と同じ扱い（task_03 の判定に含まれている）

> 置き場は `split_loading.py` でなく `save_path_resolution.py` でもよい（実装者判断）。
> **要件は「読込の判定と同じ規則を使い、判定ロジックを二重化しないこと」**。

### 4. `keyseq/presentation/` — 書込先の受け渡し

- **`HotkeyPresetsIo.write_global_presets`** を、**保存先を受け取る形**へ変える
  （名前を `write_presets` 等へ改める場合は `config_io/__init__.py` の `__all__` も更新）。
  **成否 bool を返す契約と `messagebox.showerror` の扱いは不変**。
- **`App.save_hotkey_presets`** が、`self.data` と `self.keymap_set_path` から**保存先を決めて**渡す
  （決定ロジック自体は §3 の application 側 API を呼ぶ。**presentation で組み立てない**）。
- **保存に成功したら、確定した保存表記パスを `self.data["hotkey_presets_path"]` へ反映**する
  （ON にした直後に既定パスが決まるケース。次の keymap_set 保存で payload に載る）。
  **フラグ（`hotkey_presets_individual`）はここでは変えない**（切替は task_05）。
- **失敗時は `self.data` を一切変更しない**（現行契約を維持）。

### 設計メモ / 制約

- **【H】実体は OK で初めて作る**。本タスクで「ON にしたらファイルを作る」処理を**足さない**。
- **【O】config 外へは書かない**（判定は task_03 の関数が担保。presentation で緩めない）。
- **保存側では正規化しない**（正本 §5.10.2。正規化は読み出し側 1 箇所）。
- **保存カスケードは引き続きプリセットを書かない**（正本 §5.10.3）。
- **キーの値を勝手に消さない**（OFF でも `hotkey_presets_path` は保持。task_02 の【N】）。

## 含まない

- **切替 UI（チェック・保存先表示・OK/キャンセルの契約）** → **task_05**
- **Import の強制 OFF・別名保存時の複製** → **task_06**
- 読込側の変更（task_03 の到達点）/ 保存カスケードの変更 / 正本の更新（**task_08**）
- 「ON にした時点でファイルを作る」実装（**仕様で不採用**）

## 確認

`.venv` の python で実行（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。実測は `verifier`。

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests` が **pass**（基準線 **216** + 追加分）
- `-m unittest discover -s tests_ui` が **pass**（基準線 **186** + 追加分）
- `-m tests.smoke_app` が pass

### テスト（追加まで実装範囲。**実行は依頼しない**）

**`tests/test_config_service.py`**:

1. **既定パスの算出**: keymap_set が `user/keymap_sets/main.json` なら
   個別既定は **`user/hotkey_presets/main.json`**。
   **stem が空になる名前**ではフォールバック `default.json`（＝ `user/hotkey_presets/default.json`）。
   **グローバル既定（`user/hotkey_presets/global/default.json`）と衝突しない**ことを値で確認。
2. **保存先の決定**: 個別 ON + パスあり → **そのパス** / 個別 ON + パス無し → **既定パス**（保存表記）/
   OFF またはフラグ無し → **空文字（グローバル）** / **config 外のパス → 空文字**。
3. **保存 API**: 指定した保存先へ `{"hotkey_presets": ...}` が書かれる。
   **例外はそのまま送出**される（`repository.save_json` を差し替えて確認）。
4. **往復**: 個別 ON で保存 → **task_03 の解決順序で読み戻せる**（同じ内容が runtime に載る）。

**`tests_ui/test_app_ui_flows.py`**（既存の `save_hotkey_presets` 系テストの近くへ）:

5. **個別 ON の runtime** で `App.save_hotkey_presets` を呼ぶと、**個別ファイルへ書かれる**
   （グローバルファイルは**更新されない**ことも確認）。
6. **成功時に `app.data["hotkey_presets_path"]` が確定した保存表記へ反映**される
   （ON + パス無しから呼んだケース）。**フラグは変わらない**。
7. **失敗時**（保存 API が例外）に **`app.data` が一切変わらない**（パスもプリセットも）。
   `messagebox.showerror` が呼ばれる（**モーダルは必ず patch する**）。

## 完了条件

- 上記確認がすべて pass し、**`reviewer` 採用**（観点: 保存先の決定が **application 側 1 箇所**か
  〔presentation で組み立てていないか〕/ **判定ロジックが task_03 と二重化していない**か /
  **ON でファイルを作っていない**か【H】/ config 外へ書けないか / 失敗時に `data` を汚さないか /
  保存側で正規化していないか / グローバル既定と衝突しないか）。
- **実機目視は本タスクでは行わない**（**task_07** でまとめて実施）。
