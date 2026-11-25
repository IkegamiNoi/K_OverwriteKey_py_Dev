# idea_69_mac_premod_lost_on_mapped_send.md

## 概要

**macOS で、フックの開始・再開より前から押している Command 等の修飾が、キー置換の送信イベントに付かないことがある**（静的な推論・未実測）。
例: Command を押したままフックを開始して `F1` → `a` を押すと、`Command+a` ではなく `a` が送られる見込み。

## 起票経緯（2026-11-25）

phase 81 のフェーズ完了判定前の Codex 敵対的レビュー（指摘 1・medium）。phase 81 で変えた箇所ではなく、送るイベントの修飾を組み立てる処理の以前からの性質のため、phase 81 では直さず分離した（ユーザー判断「推奨どおり」）。

## 現状

- 送るイベントのフラグ = タップが観測した物理の修飾 + 送信済みの修飾（`keyseq/infrastructure/os_backend/macos/keyboard_backend.py` の `_send`・`event_tap.py:178` `physical_modifiers`）。物理のフラグ（`CGEventSourceFlagsState`）から補うのは `mac_shift` の Shift だけ。
- タップが観測した修飾の記録は、タップの開始前の押下を取り込まない見込み（未確認）。一方、gateway の「押されている」の判定（`is_ctrl_alt_win_down`）は物理のフラグを読むため、Shift を足さない判断と送るフラグが食い違い得る（phase 81 の大文字では `Command+F1` → `a` になり得る）。
- 正本: `key_input.md` §7.9「修飾キー」・§7.4「キー置換の送信の Shift」。

## 提案（方向性・要設計）

- まず実機で再現を確かめる（Command を押したまま「開始（フックON）」→ 置換のキー）。
- 再現すれば、タップの開始・復帰時に押下済みの物理の修飾を取り込む、または Shift の追加の判断と送るフラグを同じ状態から決める。

## 想定スコープ

- infrastructure（macOS の backend とタップ）のみの見込み。JSON スキーマは不変。Windows は対象外。
