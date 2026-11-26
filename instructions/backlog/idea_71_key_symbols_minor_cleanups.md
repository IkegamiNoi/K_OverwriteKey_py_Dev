# idea_71_key_symbols_minor_cleanups.md

## 概要

**phase 82（レイアウトの `key_symbols`）の統合レビューで挙がった軽い気づき 4 点（L1〜L4）を、まとめて整える。** どれも害は無く、優先度は低い。

## 起票経緯（2026-11-26）

出所: phase 82 task_04 の統合レビュー（deep-reviewer）の低の指摘。ユーザー判断で保留とし、優先度 低の idea として残す。

## 現状

- **L1 描き直しの二重**: レイアウトを変えると、キーボードUIを 2 回描き直す（`layout_controller.py` の sync の中の `refresh_keyboard_window` と、`refresh_triggers` の末尾の `refresh_keyboard_window`〔`trigger_panel_controller.py:258` 付近〕）。選んでいるレイアウトを削除したときは、両一覧も 2 回描き直す（`set_keyboard_layout_selection` と `delete_keyboard_layout` の末尾）。
- **L2 枠ごとの dict の生成**: `keyboard_window.py` の枠の文字の決め方が、キーの枠ごとに `key_symbol_map`（呼ぶたびに新しい dict を作るプロパティ・`keyboard_layouts.py`）を呼ぶ。
- **L3 書き方**: `call_view_controller.py` の `_render_rows` が、`getattr(self.app.trigger_panel, "_current_key_symbols", lambda: None)()` で別のコントローラの非公開の補助を防御的に呼ぶ。`TriggerPanelController._current_key_symbols` は例外を記録せずに捨てて `None` を返す。
- **L4 警告の名前**: 不正な `key_symbols` の警告は `display_name` をそのまま出す。表示名が重なったときにドロップダウンが付ける `[id]` とは揃っていない。

## 提案（方向性・要設計）

- L1: 描き直しの入口を 1 つにまとめるか、`refresh_triggers` からキーボードUIの描き直しを外せるかを確かめる。
- L2: 描く前に 1 回だけ dict を取り出してループで使う（または `KeyboardLayout` に dict を 1 度だけ作って持たせる）。
- L3: 表を取る補助をレイアウト側（`LayoutController`）に置き、両コントローラから公開の名前で呼ぶ。例外は `_LOG.exception` で記録してから `None`。
- L4: 警告の名前をドロップダウンの表示（`[id]` 付き）と同じ作り方にする。

## 想定スコープ

- 含む: presentation（`layout_controller.py`・`trigger_panel_controller.py`・`call_view_controller.py`・`keyboard_window.py`・`keyboard_layouts.py`）とテスト。
- 含まない: 表示の結果の変更（L4 の名前以外）・domain。
- 仕様変更: L4 だけ警告の文言の名前の作り方（`features.md` §4.6）。他は挙動不変。
