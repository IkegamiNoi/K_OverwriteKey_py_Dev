# task_05_integration_recheck

## 目的

Phase α（task_01〜04）の変更を**通しで検証**し、受入条件 §8 の 1〜8 をすべて満たすことを確定する。
**新規の挙動変更は行わない**。既存の担保状況を対応表で確認し、**穴が空いている 2 点にだけ回帰テストを追加**する。

- 根拠: 暫定仕様 [04](../../../history/04_keymap_set_new_and_default_dir.md) §8 / **受入条件 7・8**。
- **レイヤ制約**: **production コードは変更しない**（テストのみ）。実装差分が必要と判断したら
  **手を入れず報告する**（仕様判断が必要なため）。
- 複数タスクを跨ぐ統合タスクのため、レビューは `deep-reviewer` + Codex レビューを併用する
  （`.claude/rules/agent_selection.md`）。

## 受入条件の担保状況（起票時に確認済み・実装者はこの表を前提にする）

| # | 受入条件 | 担保 |
|---|---|---|
| 1 | 新規作成直後は path 空・「保存」で別名保存 | `test_new_config_success` / `test_save_keymap_set_empty_path_delegates_to_save_as` / `test_save_as_empty_path_uses_default_initialfile`。**ただし 3 者が分離しており連結経路が未担保** → **G1 で追加** |
| 2 | 起動時にディレクトリ骨格が作られ、初回 Save As の初期ディレクトリが `config/user/keymap_sets/` | `tests_ui/test_startup_dir_skeleton.py`（`ensure_split_config_dirs` 呼び出し + 起動時無保存）。**`suggest_keymap_set_dialog_dir("")` は「存在しない場合の fallback」しか固定していない** → **G2 で追加** |
| 3 | Import 成功後は path 空・保存は別名保存 | `test_import_config_success` / `test_import_config_success_clears_nonempty_keymap_set_path`（空化）+ G1（空パス→別名保存の連結）で充足 |
| 4 | stored セット不在時は無言で空起動・path 空 | `test_load_startup_and_config_empty_when_stored_path_missing` / `..._swallows_load_exception_and_falls_back` |
| 5 | 新規 config.json に `prompt_if_missing` が含まれない | `tests/test_config_service.py`（task_04 追加分）/ `test_write_startup_omits_prompt_if_missing_without_existing_value` / `test_set_startup_keymap_set_writes_only_keymap_set_path` |
| 6 | 既存 `prompt_if_missing` 付き config.json でも起動・保存が正常（残置許容） | `tests/test_config_service.py`（既存値保持）/ `tests_ui/test_startup_font_characterization.py::test_load_startup_settings_preserves_unknown_keys_through_save`（無修正 pass）|
| 7 | 非変更経路の回帰なし（既存パスへの上書き保存 / 読込 / 別名保存 / Import / Export） | `test_save_keymap_set_nonempty_path_saves_to_current_path`（`save_as.assert_not_called()` 済）/ `test_save_keymap_set_to_*` 3 本 / `test_load_keymap_set_from_*` 4 本 / `test_save_as_nonempty_path_uses_current_filename_initialfile` / `test_import_config_*` 5 本 / `test_export_config_*` 3 本 → **追加不要** |
| 8 | `tests` / `tests_ui` / smoke が pass | 本タスクの「確認」節（verifier 実測） |

## 対象範囲（テストのみ・追加 2 本）

### G1. `tests_ui/test_config_io_characterization_keymap_set_startup.py`（+1）

**新規作成 → 保存 が別名保存ダイアログへ到達する連結**を固定する（受入 1・3 の核心）。

- `_silence_refresh()` と既存の patch 作法を流用し、`new_config()` を実際に実行する
  （`confirm_save_if_dirty` は clean 状態なので追加 patch 不要。必要なら既存テストに倣う）。
- 続けて `save_keymap_set(show_success_dialog=False)` を呼ぶ。**`save_as` は patch しない**
  （連結の確認が目的）。`tkinter.filedialog.asksaveasfilename` を patch して選択パスを返し、
  `save_keymap_set_to` を patch する。
- 検証: ① `new_config` 後に `keymap_set_path == ""` ② `asksaveasfilename` が **1 回呼ばれる**
  ③ その `initialfile == "keymap_set.json"` ④ `save_keymap_set_to` が**ダイアログで選ばれたパス**で
  呼ばれる（`flash_message="別名で保存しました。"`）。
- `suggest_keymap_set_dialog_dir` / `suggest_keymap_set_dialog_path` は既存テストと同様に patch してよい
  （initialdir の実値検証は G2 が担当するため、ここでは検証しない）。

### G2. `tests/test_config_paths.py`（+1）

**`suggest_keymap_set_dialog_dir("")` が、`config/user/keymap_sets/` が実在するとき当該ディレクトリを返す**
ことを固定する（受入 2 の後半。既存 `test_suggest_dialog_dir_falls_back` は不在時の fallback のみ）。

- 既存 `setUp` の `tempfile` 構成を流用し、`os.makedirs(self.paths.preferred_keymap_sets_dir())` してから
  `suggest_keymap_set_dialog_dir("")` が `preferred_keymap_sets_dir()` と一致することを検証する。
- 既存テスト（`test_suggest_dialog_dir_falls_back`）は**変更しない**。

## 含まない

- **production コードの変更全般**（本タスクはテスト追加と検証のみ）。修正が必要なら報告して止める。
- 受入 7 への追加テスト（上表のとおり既存で充足。**重ねて追加しない**）。
- 正本反映（`data_schema.md` / `codebase_map.md`）・暫定仕様 04 の凍結・`decisions_archive/05`・
  `current.md` 更新・`/refactor_check`（すべて **task_06**）。
- 子ファイル共有・複数セット独立化（**Phase β**）/ 起動時のファイル選択 UX（スコープ外）。

## 確認

python は**リポジトリルートの `.venv`** を使う（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
※テストの実行は verifier が行うため、実装側は実行しなくてよい。

1. `-m compileall -q keyseq main.py tests_ui` — clean
2. `-m unittest discover -s tests` — 全 pass（89 件 + G2 の 1 件 = **90 件。減らないこと**）
3. `-m unittest discover -s tests_ui` — 全 pass（84 件 + G1 の 1 件 = **85 件。減らないこと**）
4. `-m tests.smoke_app` — pass
5. `git diff --stat` に **`keyseq/` 配下のファイルが 1 つも含まれない**こと（テストのみの差分）

### 実機目視（ユーザー依頼・本タスクで実施）

phase.md「レビュー方針」の 6 項目:

1. 新規作成 → 「保存」で**別名保存ダイアログが出る**（初期ファイル名 `keymap_set.json`・
   初期ディレクトリ `config/user/keymap_sets/`）
2. 既存セットを開いた状態の「保存」は**ダイアログなしで上書き**される
3. 別名保存の初期ディレクトリ・ファイル名（1 と同じ観点を別名保存ボタンから）
4. Import 後に「保存」を押すと**別名保存になる**（元セットを上書きしない）
5. 起動時に stored セットが無い場合、**無言で空起動**する
6. 既存の `prompt_if_missing` 付き `config/config.json` で**起動・保存が正常**

## 完了条件

- 上記確認 1〜5 が pass。
- **実機目視 6 項目をユーザーが実施し、結果を報告済み**であること。
- レビュー: **`deep-reviewer` + Codex レビュー（`codex-reviewer`）を併用**し、いずれも完了可であること
  （統合タスクのため単独 `reviewer` では完了としない）。
