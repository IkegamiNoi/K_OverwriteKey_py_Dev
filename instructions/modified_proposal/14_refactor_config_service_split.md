# 14_refactor_config_service_split.md

phase 36（config_service の分割と巨大関数の分割）の `/refactor_check`（2026-09-27）で「推奨」となった項目。**挙動不変**（エラーメッセージ・保存ファイルのバイト列も変えない）。
PHASE_BASE = `1b37653`。判定の詳細は `decisions_archive/36_config_service_split.md`。**ユーザー承認前に実施しない。**

## 判定の根拠

| 記号 | 該当 |
|---|---|
| M1 | `config_service/split_loading.py` 666 → 787（+121）。増分は `build_runtime_data_from_split` を補助関数 8 つへ分けたことによる（phase 36 task_03） |

M2〜M6 は該当なし（verifier 実測）。`split_payloads.py` の既存の 80 行超の関数 2 つ（`build_keymap_payloads` 100 行 / `build_trigger_set_payloads` 106 行）は
phase 36 で未変更のため本提案に含めず、`current.md`「別タスク化候補」へ送る。

## 項目 0: 安全網の確認

- 対象領域は既存テストでカバー済み: `tests/test_config_service.py`（全体のホットキープリセットの読込・個別プリセットの保存先・上書き確認・出所の表示）/
  `tests/test_per_keymap_triggers_load.py` / `tests_ui` のホットキープリセット IO / `tests.smoke_app`。
- 完了条件（共通）: `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests`（674 / skip 7）・`discover -s tests_ui`（576）・`-m tests.smoke_app` が全 pass。
  テストの変更は**呼び出し先モジュール名の差し替えと `INTERNAL_MODULE_NAMES` への追加だけ**（期待値は変えない）。

## 項目 1: ホットキープリセットのファイル解決・読込を `split_loading.py` から切り出す（M1）

- 対象: `keyseq/application/config_service/split_loading.py:71-297` の 9 関数
  （`load_global_hotkey_presets_path` / `load_hotkey_presets_file` / `load_global_hotkey_presets` / `resolve_individual_hotkey_presets_path` /
  `resolve_individual_hotkey_presets_read_path` / `resolve_hotkey_presets_save_path` / `individual_hotkey_presets_save_rejection_reason` /
  `describe_individual_hotkey_presets_overwrite` / `describe_hotkey_presets_source`。約 227 行）
- 問題: `split_loading.py`（split 構成の読込）に、ホットキープリセットの保存先の決定・上書き確認・出所の表示という**読込以外の責務**が同居し、787 行になっている。
- 変更: 同パッケージの新モジュール `config_service/hotkey_presets_files.py` へ移す（`service` を第 1 引数に取る module 関数のまま・名前も同じ）。
  - 呼び出し元を差し替える: `config_service/__init__.py`（11 箇所）/ `orphan_scan.py:84` / `split_loading.py` 内（`_load_runtime_keyboard_layouts_and_hotkey_presets`）/
    `tests/test_config_service.py`（337 / 398 / 563 / 1518 / 1552 行付近の直接呼び出し 5 箇所）。
  - `split_loading.py` に再輸出は置かない（恒久互換レイヤー禁止）。
  - 新モジュールは `split_loading` と `__init__` を import しない（`split_loading` → 新モジュールの一方向）。`os.path` はドット記法を保つ。
  - `tests/test_config_service_contracts.py` の `INTERNAL_MODULE_NAMES` に `"hotkey_presets_files"` を追加。`codebase_map.md` の表に 1 行追加。
- 見込み: `split_loading.py` 787 → 約 560 行 / 新モジュール 約 240 行。
- リスク / 戻し方: 関数本体は無変更の移動のみ。戻すのは移動の逆（呼び出し元の差し替えを戻す）。依存: なし。

## 実施タイミング（ユーザー選択）

(a) phase 36 末の追加タスク（`task_09_refactor`）/ (b) 次フェーズ前の独立ミニフェーズ、のいずれか。
