# task_05_refactor

## 目的

提案書 [29](../../../modified_proposal/29_refactor_uppercase_replacement_target.md)（phase 81 の `/refactor_check` で推奨・2026-11-25 ユーザー承認「提案書 29 を実施」）の R1・R2 を行う。**挙動は変えない**（リファクタのみ）。

## 対象範囲

1. R1: `keyseq/domain/config.py` に `is_uppercase_mapping_target(value: str) -> bool`（`len(value) == 1 and "A" <= value <= "Z"`）を足し、次の 7 か所の同じ式をこの関数の呼び出しに置き換える。
   - `keyseq/domain/config.py:139`（`normalize_mapping_target` の中）
   - `keyseq/infrastructure/os_backend/macos/keyboard_backend.py:188`
   - `keyseq/infrastructure/os_backend/windows/keyboard_backend.py:193`・`:230`・`:242`・`:260`
   - `keyseq/presentation/keyboard_window.py:471`
   - `keyboard_window.py:633` の `"a" <= key <= "z"`（記録時の小文字の判定）は意味が違うので**変えない**。
2. R2: `windows/keyboard_backend.py` に `_keyboard_name(send: KeySend) -> str`（大文字なら `send.key.lower()`、それ以外は `send.key`）を置き、press_send / release_send の同じ式（`:230`・`:242`）をこの補助の呼び出しにする。
3. テスト: `tests/test_domain_config.py` の `MappingTargetNormalizationTest` の最後に `is_uppercase_mapping_target` の小さなテストを 1 つ足す（`"A"`・`"Z"` は真、`"a"`・`"AB"`・`""`・`"Ａ"`〔全角〕・`"1"` は偽）。既存テストの期待値は変えない。

**既存テストの途中に差し込まない。apply_patch で編集し、Python で書き換えない。** 再輸出・互換用の別名は作らない。

## 読むファイル

- 提案書 29
- 上の 4 つのソースファイルの該当行の前後
- `tests/test_domain_config.py` の `MappingTargetNormalizationTest`

## 含まない

- 挙動の変更・正本の更新（`codebase_map.md` の 1 行の追記はメインが行う）・他のリファクタ

## 確認

- verifier（Windows・tests_ui は 1 本ずつ・`taskkill` 禁止）: `compileall` clean / `unittest discover -s tests` 全 pass / tests_ui の `test_keyboard_key_text`・`test_keyboard_window_scan_code` pass / smoke pass
- `grep -rn '"A" <=' keyseq` が `domain/config.py` の 1 件だけ

## 完了条件

- 上記確認 pass・**reviewer 採用**。Mac の backend のテストは Windows 上のモックで流れる分を確かめる（Mac 実機での再実行は任意・ユーザー）。

## 結果（2026-11-25 完了）

- codex-implementer（Luna high・1 回・メイン修正なし）。`is_uppercase_mapping_target` に一本化（`grep '"A" <=' keyseq` = `domain/config.py` の 1 件）・`_keyboard_name` を press / release で使用・単体テスト 1 件追加・`codebase_map.md` に 1 句
- verifier: compileall clean / tests 2296（skip 9）/ tests_ui 2 モジュール 19 件 / smoke pass。reviewer 採用（挙動不変・依存方向は既存と同じ向き）
