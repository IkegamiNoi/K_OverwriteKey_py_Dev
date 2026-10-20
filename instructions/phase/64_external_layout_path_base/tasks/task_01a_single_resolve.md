# task_01a_single_resolve

## 目的

完了判定前の Codex 敵対的レビューの指摘（中・2026-10-21 ユーザー採用）への対応。`normalize_external_keyboard_layouts` がパスの解決を 2 回重ねており、`config_root` が相対パス（例 `config`）のときに読み込むたびに `config/` が増える（`_resolve_config_relative_path` で `config/user/…` にした値を `to_config_relative_or_absolute` がもう一度 `config_root` へ結合する）。
**application 限定（`split_loading.py` の 1 か所）+ テスト。挙動は config_root が絶対パスのとき不変。**

## 対象範囲（application 限定 + テスト）

### `keyseq/application/config_service/split_loading.py` — `normalize_external_keyboard_layouts`（:558-559）

- `service._resolve_config_relative_path(stored_path, config_root)` を経由せず、`service.to_config_relative_or_absolute(stored_path, config_root)` に**解決前の `stored_path` を直接渡す**（解決は 1 回だけ）。不要になった `resolved_path` 変数は削除。

### テスト

- `tests/test_config_service.py`（既存の `test_external_layout_paths_use_config_root_and_are_idempotent` の近く）: `config_root` が相対（`"config"` と `"./config"`）で、入力 `user/keylayout/jis.json` を 3 回続けて通しても `user/keylayout/jis.json` のまま。
- `tests/test_layout_controller_registration.py`: `config` 外の絶対パス（tempdir の別フォルダ）を登録すると、`/` 区切りの絶対パスで記録される（deep-reviewer 指摘 4・低）。

## 読むファイル

1. `keyseq/application/config_service/split_loading.py:540-562`（編集対象）
2. `keyseq/application/config_service/__init__.py:742-780`（`to_config_relative_or_absolute` / `_resolve_config_relative_path`）
3. `tests/test_config_service.py` の `test_external_layout_paths_use_config_root_and_are_idempotent`（手本）
4. `tests/test_layout_controller_registration.py`（全体・追加先）

## 含まない

- 単一 JSON の取り込み（`keymap_set_io.py:614`）の正規化（受容・ユーザー判断 2026-10-21）
- 正本・文書の更新（task_02）
- 他のパス（keymaps 等）の解決

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` clean
- 追加テスト pass・`-m unittest discover -s tests` 全 pass・`-m unittest discover -s tests_ui` 全 pass（単独実行）・`-m tests.smoke_app` pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視: 不要（`config_root` が絶対の通常経路では挙動不変。task_01 の目視で確認済み）。
