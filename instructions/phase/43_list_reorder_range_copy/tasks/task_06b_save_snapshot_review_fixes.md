# task_06b_save_snapshot_review_fixes

## 目的

task_06 + 06a の完了判定前レビュー（deep-reviewer 修正要・2026-10-03）で採用した 2 件を直す（暫定 30 v0.6 §5.4・§10-9）。
- **M1**: 個別保存は、保存先のパスを選ぶダイアログ（`trigger_set_file_io.py:36-65`）が固定（`save_trigger_set_to_path` の先頭）より前に出る。
  その間にアクティブが別の一覧へ変わると、別の一覧を A 用に選んだパスへ書きうる → 固定を保存の入口（パスのダイアログより前）へ移す
- **L2**: 一括保存・個別保存とも、ダイアログ中に行が変わると照合より前の計画の組み立て（`child_save_plan.py:89` の `targets[child_id]` 等）が例外になり、
  「保存失敗: 生の識別子（区切り文字入り）」が出る → 例外時に照合が不一致なら中止の文言（`SAVE_TARGET_CHANGED_MESSAGE`）に差し替える

**presentation 限定（config_io の 2 ファイル）。application / domain 不変・スキーマ不変。**

## 対象範囲（presentation 限定）

### `keyseq/presentation/controllers/config_io/trigger_set_file_io.py`

- `save_trigger_set_file` / `save_trigger_set_file_as` の**先頭**（パスのダイアログより前）で `capture_active(self._app.data)` を取り、`save_trigger_set_to_path(path, save_target=...)` へ渡す
- `save_trigger_set_to_path(self, path: str, save_target: SaveTargetSnapshot | None = None)`: 渡されなければ従来どおり先頭で取る（既存の呼び出し・テストとの互換）。照合の位置は今のまま
- `except` 節: 固定があり `snapshot_matches` が False なら、`保存失敗` の代わりに中止と同じ表示（`_set_flash_message(SAVE_TARGET_CHANGED_MESSAGE, auto_clear=False)` + `messagebox.showwarning("保存", ...)`）にして `False` を返す。一致していれば従来の `保存失敗` 表示

### `keyseq/presentation/controllers/config_io/keymap_set_io.py`

- `save_keymap_set_to` の `except` 節: 上と同じ（`save_target` が取れていて不一致なら中止の表示に差し替え。固定前の例外〔`save_target` 未定義〕は従来どおり）
- 中止の表示（flash + showwarning）は 2 ファイルで同じ処理になるため、`save_target_snapshot.py` に表示を持たせず、各ファイル内の小さなメソッドにまとめてよい（tkinter を `save_target_snapshot.py` へ入れない）

### テスト（追加・修正まで・tests_ui/test_config_io_characterization.py）

- 個別保存（M1）: `save_trigger_set_file_as` で、パスのダイアログ（`filedialog.asksaveasfilename` を patch）の中でアクティブなキーマップを別の一覧へ切り替えてからパスを返す →
  ファイルが書かれない・どちらの一覧も差し替わらない・中止の文言・`False`。`save_trigger_set_file`（`io_dialogs.choose_save_path_with_collision` を patch）でも同様
- 一括保存（L2）: 子ファイルの保存ダイアログの中で行を足して（または並べ替えて）**古い選択**を返し、計画の組み立てで例外が出る状況 → 「保存失敗」ではなく中止の文言・書き込みなし・`showerror` は呼ばれない
- 照合が一致しているときの例外は従来どおり「保存失敗」になる（既存テストで担保されていれば追加不要）

## 読むファイル

- `keyseq/presentation/controllers/config_io/trigger_set_file_io.py:1-90`
- `keyseq/presentation/controllers/config_io/keymap_set_io.py:110-195`
- `keyseq/presentation/controllers/config_io/save_target_snapshot.py`（全体）
- `tests_ui/test_config_io_characterization.py` の task_06a で足した 2 件（`test_bulk_save_aborts_when_trigger_rows_change_in_child_dialog` と個別保存の中止のテスト）

## 含まない

- キーマップの個別保存（`keymap_file_io.py`）への固定と照合（保留 L1）
- 識別子の番号の厳密化・表示名の共通化（除外 L3・L4）
- §5.4 の文言の調整（ユーザー判断 L8・task_09）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest tests_ui.test_config_io_characterization tests.test_save_target_snapshot tests.test_per_keymap_bulk_save` が全 pass
- `-m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass

## 完了条件

- 上記確認 pass・**reviewer 採用**（06+06a の deep-reviewer + Codex レビューは実施済。本タスクはその修正）。
- 実機目視は task_06・06a の分とまとめて実施（同じキーの 2 行の保存 → 読込・`（N 行目）`・`▶` が保たれる）。
