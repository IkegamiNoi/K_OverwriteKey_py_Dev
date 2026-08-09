# task_01_move_global_presets_path

## 目的

グローバルプリセットの**既定パスを `user/hotkey_presets/global/default.json` へ移す**
（暫定仕様 08 **§2【G】**・受入条件 **9 / 17**）。個別プリセットを
`user/hotkey_presets/<stem>.json`（直下）へ置くため、**グローバルと個別が同じパスに衝突しない**
状態を先に作る。

**レイヤ制約**: **application 限定**（`config_service` の定数 1 つ + ディレクトリ骨格）。
**domain / presentation は不変**。読込・保存のロジックそのものは変えない
（既定値を参照している経路が自動的に新パスを見るようになるだけ）。

## 対象範囲

### 1. `keyseq/application/config_service/__init__.py`

- **`HOTKEY_PRESETS_RELATIVE_PATH`（`:24`）を
  `os.path.join("user", "hotkey_presets", "global", "default.json")` へ変更**する。
- **`ensure_split_config_dirs`（`:425-432`）へ
  `os.path.join(config_root, "user", "hotkey_presets", "global")` の作成を追加**する
  （既存の `user/hotkey_presets` の作成は**残す**。個別ファイルの置き場になるため）。
  追加位置は既存の `hotkey_presets` の直後にする。

### 設計メモ / 制約

- **互換フォールバック読みは実装しない**（暫定仕様【G】で**移行は手動**と確定済み）。
  旧既定 `user/hotkey_presets/default.json` を自動で読む処理を**足さないこと**。
- `load_global_hotkey_presets_path`（`split_loading.py:50`）は既にこの定数を既定値として
  参照しているため、**読み出し側のコードは変更不要**。
- config.json に `hotkey_presets_path` が**明示されている場合はそちらが優先**される
  （既定値の変更は明示値に効かない）。これは仕様どおりで、移行手順の 2 段目が対応する。
  **本タスクでは移行手順の文書化はしない**（正本反映は task_08）。
- **`save_global_hotkey_presets` の保存先も自動的に新パスになる**（同じ読み出し API を使うため）。
  ここも変更不要。

## 対象外（やらないこと）

- keymap_set 側のスキーマ追加（`hotkey_presets_individual` / `hotkey_presets_path`）→ **task_02**
- 解決順序（個別 → グローバル）→ **task_03**
- 個別ファイルの既定パス算出 → **task_04**
- 切替 UI → **task_05** / Import の強制 OFF・別名保存の複製 → **task_06**
- 移行手順の正本への明記 → **task_08**
- 旧パスからのフォールバック読み・自動移行（**仕様で不採用**）

## 確認

`.venv` の python で実行（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。実測は `verifier`。

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests` が **pass**（基準線 **203**）
- `-m unittest discover -s tests_ui` が **pass**（基準線 **186**）
- `-m tests.smoke_app` が pass

### テスト（追加・更新まで実装範囲。**実行は依頼しない**）

**更新（既定パスをハードコードしている箇所のみ）**。**アサーションは緩めない**:

1. `tests/test_config_service.py:77` — round-trip でプリセットファイルが**作られないこと**を見ている
   （phase 08 task_05 の成果）。パスを新既定へ更新する。
   **可能なら `service.HOTKEY_PRESETS_RELATIVE_PATH` を使う形にして、次の変更に追随させる**。
2. `tests/test_save_plan.py:209 / 229 / 235 / 340` — 保存カスケードがプリセットを書かないことを
   見ている 4 箇所。同上（新既定パス、または定数参照へ）。
3. `tests/test_config_service.py::EnsureSplitConfigDirsTest`（`:1442-1460`）の
   検証対象リストへ **`os.path.join("user", "hotkey_presets", "global")` を追加**する。

> `HOTKEY_PRESETS_RELATIVE_PATH` を参照している箇所（`tests/test_config_service.py` の
> `GlobalHotkeyPresetsPathTest` 系 / `tests_ui/test_app_ui_flows.py:263` /
> `tests_ui/test_config_io_characterization_keymap_set_startup.py:138`）は**自動追随するので変更不要**。
> ただし実際に落ちる場合は報告すること。

**追加**:

4. `load_global_hotkey_presets_path` が、config.json に `hotkey_presets_path` が無いとき
   **`user/hotkey_presets/global/default.json` を返す**（新既定の固定）。
5. **旧既定パス（`user/hotkey_presets/default.json`）にファイルがあっても読まれない**
   （＝自動フォールバックが無いことの固定。組込既定が残る）。

## 完了条件

- 上記確認がすべて pass し、**`reviewer` 採用**（観点: 定数と骨格の変更のみに収まっているか /
  **互換フォールバックを足していないか** / `user/hotkey_presets` 直下の作成を消していないか /
  読込・保存ロジックへ波及していないか / 既存テストの更新がアサーション緩和になっていないか）。
- **実機目視は本タスクでは行わない**（**task_07** でまとめて実施）。
  ※ 開発環境の `config/user/hotkey_presets/default.json` は、この変更以降**参照されなくなる**。
  手元で動かす場合は `global/` へ移すこと（移行手順の 1 段目）。
