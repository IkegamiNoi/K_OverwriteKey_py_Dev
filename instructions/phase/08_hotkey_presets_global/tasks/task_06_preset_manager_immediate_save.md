# task_06_preset_manager_immediate_save

## 目的

プリセットマネージャの編集結果を、**config.json が指すグローバルプリセットファイルへ即時保存**する
（暫定仕様 07 **§2 指摘③ / §3**・受入条件 **3**）。task_05 で保存カスケードから書出を外したため、
本タスクで**プリセットの唯一の書き手**が確定する。

**契約**（phase 07 の `write_global_hook_keys` と同じ）: **成否を返す**。
**保存に失敗したら編集内容を失わず・確定もしない**（ダイアログを閉じない・runtime も更新しない）。

**レイヤ制約**: **application に保存 API を 1 本追加**（`config_service`）+ **presentation に
書込コントローラと配線**。**domain 不変・スキーマ不変**・読込側（task_02 / task_04 の到達点）不変・
保存カスケード（task_05 の到達点）不変。

## 対象範囲

### 1. `keyseq/application/config_service/__init__.py` — 保存 API の新設

`apply_global_defaults` の直後に追加する。

```python
def save_global_hotkey_presets(self, presets: list[Any], *, config_root: str) -> None:
    """config.json が指すグローバルプリセットファイルへ書き出す。"""
```

- 保存先は `split_loading.load_global_hotkey_presets_path(self, config_root=config_root)`
  （task_01 の既定補完付き API）→ **`self.resolve_config_path(path, config_root)` で解決**してから渡す。
  **生の相対値を `os.path` 系へ直接渡さない**（cwd 基準解決の事故防止）。
- 書き出す形は**読み出しと対称**にする: `{"hotkey_presets": safe_deepcopy(presets)}`
  （根キーは `hotkey_presets`）。
- **例外は握り潰さない**（失敗はそのまま送出する。成否の判定は presentation 側の責務）。
  ※ `apply_global_defaults` の「例外を投げない」契約は**読み出し側のみ**。混同しないこと。

### 2. `keyseq/presentation/controllers/config_io/hotkey_presets_io.py`（新規）

`config_io` パッケージの既存 IO モジュール（`trigger_set_file_io.py` 等）と同じ形にする。

```python
class HotkeyPresetsIo:
    def __init__(self, app) -> None:
        self._app = app

    def write_global_presets(self, presets: list) -> bool:
        """グローバルプリセットへ即時保存する（成否を返す）。"""
```

- `self._app.config_service.save_global_hotkey_presets(presets, config_root=self._app.config_root)` を呼ぶ。
- 成功なら `True`。失敗は `except Exception as e:` で受け、
  **`messagebox.showerror("プリセット保存失敗", str(e))` を出して `False`** を返す
  （`startup_io.write_startup` と同じ形。**握り潰さない**）。
- `config_io/__init__.py` の import / `__all__` へ `HotkeyPresetsIo` を追加する。

### 3. `keyseq/presentation/app.py` — 配線と確定点

- `self.startup_io = StartupIo(self)`（`:147` 付近）の並びへ
  **`self.hotkey_presets_io = HotkeyPresetsIo(self)`** を追加する。
- **`App.save_hotkey_presets(self, presets: list) -> bool` を新設**する:
  - `self.hotkey_presets_io.write_global_presets(presets)` を呼ぶ。
  - **成功したときだけ** `self.data["hotkey_presets"] = presets` を反映して `True` を返す。
  - 失敗なら **`self.data` を変更せず** `False` を返す。
- **`open_preset_manager`（`:407-413`）から `self.dirty_tracker.set_dirty(True)` を削除**する
  （プリセットは keymap_set の一部ではなくなったため、**dirty を汚さない**）。
  変更時の `_set_flash_message("プリセットを更新しました。")` は**残す**。

### 4. `keyseq/presentation/dialogs.py` — 確定点を即時保存へ

`PresetManagerDialog.on_ok`（`:505-508`）を次のとおり変える。

- 現在の `self.parent.data["hotkey_presets"] = self._temp` の**直接代入をやめ**、
  **`self.parent.save_hotkey_presets(self._temp)` を呼ぶ**。
- **戻り値が `True` のときだけ `self.destroy()`**。`False` なら**閉じない**
  （`self._temp` はそのまま ＝ 編集内容を失わず再試行できる。受入条件 3）。
- 古いコメント「※保存自体は親の保存ボタンで行う運用」は**実態と食い違うので更新する**。
- ダイアログから `config_service` / `repository` / `os.path` を直接触らないこと
  （presentation → App → controller → application の順を守る）。

### 設計メモ / 制約

- **新規ファイルを 1 つ増やす理由**: `config_io/` は**ファイル種別ごとの IO モジュール**で構成されており
  （`keymap_file_io` / `sequence_file_io` / `trigger_set_file_io` / `startup_io`）、
  プリセットファイルは `startup_io`（= config.json 専用）にも `keymap_set_io` にも属さない。
  App へ直接 file IO と `messagebox` を持ち込む方が責務違反になる。
- **`ensure_split_config_dirs` は呼ばなくてよい**（`JsonRepository.save_json` が
  親ディレクトリを作る）。呼び出しを増やさないこと。
- **読込側・カスケードは触らない**。プリセットの書き手はこの経路だけにする。
- 保存の成功後に**再読込はしない**（`apply_global_defaults` を呼ばない）。編集結果がそのまま runtime。

## 含まない

- 保存失敗時の**退避・バックアップ**（暫定仕様 §3-2「既知の制約」で持たないと確定済み）
- **破損したプリセットファイルの検知・保護**（上書きするのが現仕様）
- プリセット編集 UI の刷新（ボタン構成・入力ダイアログ・バリデーションは現状のまま）
- 読込側（`split_loading` / `apply_global_defaults` / 入口台帳）・保存カスケードの変更
- keymap_set 側 `hotkey_presets_path` の能動削除（仕様上禁止）
- 統合確認・実機目視 → **task_07** / 正本反映 → **task_08**

## 確認

`.venv` の python で実行（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。実測は `verifier`。

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests` が **pass**（基準線 **190** + 追加分）
- `-m unittest discover -s tests_ui` が **pass**（基準線 **181** + 追加分）
- `-m tests.smoke_app` が pass

### テスト（追加まで実装範囲。**実行は依頼しない**）

**`tests/test_config_service.py`**:

1. `save_global_hotkey_presets` が **config.json の `hotkey_presets_path` が指すファイル**へ
   `{"hotkey_presets": [...]}` の形で書く（未設定なら既定 `user/hotkey_presets/default.json`）。
2. 保存 → `load_global_hotkey_presets` で**同じ内容が読み戻せる**（往復・空リストを含む）。
3. 保存が失敗する状況（`repository.save_json` が例外を投げるよう差し替え）で
   **例外がそのまま送出される**（application は握り潰さない）。

**`tests_ui`**（既存ファイルの構成に合わせて配置。新規クラスでよい）:

4. `App.save_hotkey_presets` が**成功時に `app.data["hotkey_presets"]` を更新して `True`** を返す。
5. **失敗時（`config_service.save_global_hotkey_presets` が例外）に `app.data` を変更せず `False`**
   を返し、`messagebox.showerror` が呼ばれる（**モーダルは必ず patch する**）。
6. **受入条件 3**: `PresetManagerDialog.on_ok` が**失敗時にダイアログを閉じない**
   （`destroy` が呼ばれない／`_temp` が保持される）ことと、**成功時は閉じる**こと。
7. `open_preset_manager` でプリセットを変更しても **dirty が立たない**。

- **モーダルの罠**: 保存経路の例外は `messagebox.showerror` になり、テストではモーダルで
  永久ブロックする。tests_ui の該当ファイルには `setUp` の **fail-fast ガード**があるので、
  新しいモーダルを増やす場合は同じガードを足すこと
  （`test_child_save_dialog` / `test_config_io_characterization` /
  `test_config_io_characterization_keymap_set_startup` を参照）。

## 完了条件

- 上記確認がすべて pass し、**`reviewer` 採用**（観点: 受入条件 3 の達成〔失敗時に編集内容を失わない・
  確定しない〕/ プリセットの書き手がこの経路だけか / 依存方向〔dialog → App → controller → application〕/
  application が例外を握り潰していないか / dirty を汚していないか /
  読込側・カスケード・domain へ波及していないか / 新規モジュールが過剰でないか）。
- **実機目視は本タスクでは行わない**（**task_07** でまとめて実施）。
