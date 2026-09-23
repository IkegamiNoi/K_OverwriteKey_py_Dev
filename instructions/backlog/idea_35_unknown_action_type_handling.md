# idea_35_unknown_action_type_handling.md

## 概要

**空 / 未知のアクション `type`**（誤字 `"hotky"` や、phase 30 で空扱いになる非文字列）を実行したとき、
**今は `value` を文字入力してしまう**。想定外の文字が前面の窓へ入る代わりに、
**何も送らずエラー通知する**（`x` / `y` 不正時と同じ扱い）ことを検討する。
あわせて、**空 `type` の解釈が executor（text）とダイアログ（hotkey）で食い違う**点を揃える。

## 起票経緯（2026-09-23）

[phase 30](../phase/30_action_and_internal_key_type_coercion/phase.md) の起票時に
「空 / 未知の `type` の実行時挙動」が正本に未規定と判明。ユーザー判断で
**phase 30 は案 A（現行挙動を §5.11 に明文化）**、本件（案 B = エラー通知化）は idea として分離した。
層跨ぎ・挙動変更・タスク 3 以上見込みのため、直接改訂モードに収まらない。

## 現状

- 実行: `keyseq/application/action_executor.py:50-64` の `execute` は `hotkey` / `text` / `mouse_click` 以外を
  すべて `self._write_text(str(value))`（`:64`）へ流す = **text と同じ動き**
- 一覧表示: `keyseq/domain/config.py:337` は未知の `type` で `value` を表示する
- 編集ダイアログ: `keyseq/presentation/dialogs/action_dialog.py:115` は
  `(initial.get("type") or "hotkey")` = **空 `type` を hotkey とみなす**。未知の文字列はそのまま `type_var` に入る
- エラー通知: `keyseq/presentation/controllers/hook_controller.py:241` が `type` を読んでメッセージを組み立てる
- 正本: `data_schema.md` §5.11.1 に「`type` が無い / 空 / 上表以外なら `value` を文字列入力」を phase 30 で明文化済
- **【phase 30 で増えた経路・2026-09-23 追記】非文字列の `type`**（例 `{"type": ["hotkey"], "value": "alt+f4"}`）は、
  phase 30 以前は `.strip()` の `AttributeError` で**何も送られなかった**（`sequence_runner.py:65` は例外を捕まえない）。
  phase 30 の読込時正規化で `""` になり、**`value` を文字列として前面アプリへ入力する**ようになった。
  phase 30 完了判定前の `codex-adversarial-reviewer`（high）/ `deep-reviewer`（M4）の指摘。
  **ユーザー判断で phase 30 は現状維持（案 Y）とし、対処は本 idea で決める**（2026-09-23）

## 提案（方向性・要設計）

- **案 B（起票時の方向性）**: 空 / 未知の `type` は**何も送らず実行時エラーとして報告**する
  （§5.11.2 の `x` / `y` 不正時と同型）。
- **案 X（非文字列だけを先に塞ぐ小案）**: 非文字列の `type` を持つ要素を**読込時に要素ごと除去**する
  （§5.1「空になると要素が成立しない場合は除去」を当てはめる）。何も送られず一覧表示でも落ちない。
  壊れたアクションは次の保存でファイルから消える。変更は §5.11.1 の文言 + `normalize_actions` の 1〜2 行 + テストで、
  **単独なら直接改訂モードで足りる**。案 B と一緒にやるか、X だけ先に切り出すかも着手時に決める。
- 詰める論点:
  - エラー通知の出し方・文言（`_on_runtime_error` 経由か、`hook_controller` の送信エラーダイアログか）
  - 一覧表示で何を見せるか（`value` のままか、不正を示す表記か）
  - ダイアログで開いたときの扱い（空 → hotkey の既定を残すか / 未知値を選択欄へ入れない等）
  - **互換**: 誤字 `type` で現在動いているシーケンスが止まる。読込時の警告や移行の要否
- 着手時は**暫定仕様先行モード**（`.claude/rules/spec_change_workflow.md`）。phase 30 で確定する
  §5.11 の現行挙動の条項を**厳しくする方向の改訂**になる。

## 想定スコープ

- 含む: `action_executor.py` / `domain/config.py`（一覧表示）/ `action_dialog.py` / 通知経路 + テスト、
  正本 `data_schema.md` §5.11 の改訂
- 含まない: `type` 以外のフィールドの型規則（phase 30 で対応）、アクション種別の追加（idea_23）
- 影響レイヤ: application / domain / presentation。**仕様変更あり・挙動変更あり**
