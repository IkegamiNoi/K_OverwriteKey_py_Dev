# task_09_refactor

## 目的

`/refactor_check` の提案書 [13](../../../modified_proposal/13_refactor_trigger_list_per_keymap.md) の項目 1・2 を実施する（ユーザー承認 2026-09-27・実施形態 (a) phase 34 の追加タスク）。
**挙動不変**（エラーメッセージ・保存ファイルのバイト列・UI の見た目も変えない）。**既存テストのアサーションは変えない**（変えてよいのは patch 先のモジュールパスの文字列だけ）。

## 対象範囲

### 項目 1: 内部キーの直値を定数参照へ（M6）

- `keyseq/domain/keymap_triggers.py`: `INTERNAL_TRIGGER_SET_DIRTY` / `INTERNAL_TRIGGER_SET_IMPORTED` に並べて
  `INTERNAL_TRIGGER_SET_SOURCE_PATH = "_trigger_set_source_path"` / `INTERNAL_TRIGGER_SET_PARENT_REFS = "_trigger_set_parent_refs"` を足す（値は既存と同一）。
- 直値を定数参照へ: `keyseq/domain/config.py:199-200, 301-302, 306-307` 付近 / `keyseq/application/config_service/split_loading.py:504,506` 付近 /
  `keyseq/application/config_service/__init__.py:781` 付近（既に import している `INTERNAL_TRIGGER_SET_DIRTY` 等を使う）。
  `ConfigService.INTERNAL_TRIGGER_SET_SOURCE_PATH` / `_PARENT_REFS`（既存のクラス属性）は、domain の定数を参照する形に揃えてよい（値は不変）。
- 確認: `git grep -n '"_trigger_set_' -- keyseq` が定数定義の行だけになること。

### 項目 2: キーマップの追加フローを切り出す（M1）

- `file_organization_rules.md` の親フォルダ方式で、`keyseq/presentation/controllers/keymap_panel_controller.py` を
  **`keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py`** へ移し、追加フロー（`add_keymap` / `add_imported_keymap` /
  `_collect_missing_switch_edits` / `_prompt_keymap_edit` / `_validate_addition_key` / `_apply_pending_switch_edits` / `_append_keymap` / `_restore_active_keymap` 相当）を
  **`keyseq/presentation/controllers/keymap_panel/keymap_add_flow.py`** のクラス（例 `KeymapAddFlow`）へ切り出す。コントローラの公開メソッド
  （`add_keymap` / `add_imported_keymap` 等、他所から呼ばれるもの）は名前を変えずに残し、中身は委譲にする。
- 同じ親フォルダに `__init__.py`（再輸出は公開面の定義として可・`file_organization_rules.md` の注記）。**旧パス `controllers/keymap_panel_controller.py` は残さない**（恒久互換レイヤー禁止）。
  参照元（`keyseq/presentation/app.py:29` ほか `git grep` で見つかるもの）を新パスへ一括で差し替える。
- テストの patch 先文字列（`keyseq.presentation.controllers.keymap_panel_controller.messagebox` / `.KeymapEditDialog`）を新パスへ追随させる。
  追加フローのテストで patch している `messagebox` / `KeymapEditDialog` は、**切り出し先のモジュール**を patch しないと効かなくなる点に注意（計画07 の経験）。
- `instructions/common/codebase_map.md` は本タスクでは編集しない（メインがフェーズ完了時にまとめて更新する）。

## 読むファイル

- 提案書 13（全体）/ `.claude/rules/file_organization_rules.md`
- `keyseq/presentation/controllers/keymap_panel_controller.py`（全体）/ `keyseq/presentation/controllers/pane_layout/`（親フォルダ方式の既存例・`__init__.py` のみ）
- `keyseq/domain/keymap_triggers.py:1-20` / 項目 1 の対象行の前後
- テスト: `git grep -n "keymap_panel_controller" -- tests tests_ui` で見つかる行

## 含まない

- 提案書 13 に無いリファクタ（M2 の巨大関数・`config_service/__init__.py` の分割は別タスク化候補のまま）/ 挙動の変更 / `instructions/` 配下の編集

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq` clean / `tests` 669 pass（skip 7）/ `tests_ui` 576 pass（`timeout 900`）/ `tests.smoke_app` pass
- `git diff --stat -- tests tests_ui` の変更は patch 先文字列の置換だけ（アサーションの変更なし）
- `git grep -n "controllers.keymap_panel_controller\b\|controllers/keymap_panel_controller.py" -- keyseq tests tests_ui` が 0 件
- `wc -l` で `keymap_panel/keymap_panel_controller.py` が 500 行前後以下

## 完了条件

- 上記確認 pass・**reviewer 採用**。実機目視は不要（挙動不変）。
