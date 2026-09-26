# task_09: 提案書 14 の実施（ホットキープリセット 9 関数を `hotkey_presets_files.py` へ切り出す）

## 目的

提案書 [14](../../../modified_proposal/14_refactor_config_service_split.md) 項目 1 を実施する（ユーザー承認 2026-09-27・phase 36 末の追加タスク）。
`keyseq/application/config_service/split_loading.py:71-297` のホットキープリセット関連 9 関数を、同パッケージの新モジュール
`keyseq/application/config_service/hotkey_presets_files.py` へ**挙動を変えずに**移す。

## 読むファイル

1. `instructions/modified_proposal/14_refactor_config_service_split.md`
2. `keyseq/application/config_service/split_loading.py:1-30`（import）/ `:71-297`（移動対象）/ `_load_runtime_keyboard_layouts_and_hotkey_presets`（呼び出し元）
3. 呼び出し元の該当行のみ: `keyseq/application/config_service/__init__.py`（`split_loading.` で検索・11 箇所）/ `keyseq/application/config_service/orphan_scan.py:84` /
   `tests/test_config_service.py`（337 / 398 / 563 / 1518 / 1552 行付近）
4. `tests/test_config_service_contracts.py:14-18`（`INTERNAL_MODULE_NAMES`）

## 実装対象

- 移動する 9 関数: `load_global_hotkey_presets_path` / `load_hotkey_presets_file` / `load_global_hotkey_presets` / `resolve_individual_hotkey_presets_path` /
  `resolve_individual_hotkey_presets_read_path` / `resolve_hotkey_presets_save_path` / `individual_hotkey_presets_save_rejection_reason` /
  `describe_individual_hotkey_presets_overwrite` / `describe_hotkey_presets_source`。
  - 関数名・シグネチャ・本体は**無変更**（移動のみ）。9 関数の間の相互呼び出しもそのまま。
  - 新モジュールの import は 9 関数が使うものだけ。`os.path` は `import os` + ドット記法。**`split_loading` と `__init__` を import しない**。
- 呼び出し元を `split_loading.<名前>` → `hotkey_presets_files.<名前>` に差し替える:
  `__init__.py`（`from . import ...` にも追加）/ `orphan_scan.py` / `split_loading.py` 内の呼び出し（`split_loading` から新モジュールを import）/ `tests/test_config_service.py` の直接呼び出し 5 箇所（import も追随）。
- `split_loading.py` から 9 関数を削除し、不要になった import を整理（ほかで使っていないことを確認のうえ）。**再輸出は置かない**。
- `tests/test_config_service_contracts.py` の `INTERNAL_MODULE_NAMES` に `"hotkey_presets_files"` を追加（アルファベット順）。

## 対象外

- 9 関数の中身の変更・改名 / 他の関数・ファイルの変更 / テストの期待値の変更 / `codebase_map.md`（メインが反映）。
- **テストの実行**（実測は verifier）。

## 完了条件

- `split_loading.py` 約 560 行・新モジュール約 240 行。compile / tests（674・skip 7）/ tests_ui（576）/ smoke が pass（verifier 実測）。
- reviewer レビュー（無変更の移動・呼び出し元の差し替え漏れなし・循環なし・再輸出なし）を通過。
