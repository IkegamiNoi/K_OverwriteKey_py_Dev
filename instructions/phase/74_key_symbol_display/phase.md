# phase.md

## フェーズ名

記号キーのキー名の表示（key_symbol_display）

## フェーズの目的

キー置換先などの記号キーを `bar` のような単語ではなく `|` などの記号で表示する。**主はキーボードUIのキー置換の枠。domain に変換の表を置き presentation から使う。保存する名前は変えない（JSON スキーマ不変）。**

- 起票元: ユーザー要望（2026-11-08・phase 73 の起票中に別件として分離）。
- 主入力（暫定仕様）: なし（直接改訂モード）。正本 = `instructions/common/spec_detail/features.md` §4.6「記号キーのキー名の表示」。
- モード: **直接改訂モード**。番号対応: phase 74 / 暫定なし / decisions 74。

## 確定（ユーザー 2026-11-09）

- 保存する名前は変えず、画面に出すときだけ記号へ変換する。
- 主 = キーボードUIのキー置換の枠。ついで = トリガー一覧・出力シーケンス一覧の key_hold。hotkey の一覧と入力欄は対象外。
- キーボードUIの優先順 = レイアウトの `key_display_names` → 記号の表 → キー名。
- 表は 35 個（正本の表のとおり。JIS の `yen` `¥`・`ro` `\` を含む）。配列固有のキーは `key_display_names` に書く。

## スコープ

### 含む

- 変換の表と変換の純関数（domain）
- キーボードUIのキー置換の枠・トリガー一覧・key_hold の一覧への適用とテスト
- `codebase_map.md` の更新

### 含まない（後送り）

- 保存するキー名の変更・記録の変更（`period` 等とフックの名前の不一致は idea_45 の領域）
- hotkey の一覧・入力欄・キーマップ編集のキー置換一覧・切替 / 停止 / トグルキーの欄
- トリガー一覧と key_hold の一覧への `key_display_names` の適用

## このフェーズで読むファイル

1. `instructions/common/spec_detail/features.md` の「キーの文字」と「記号キーのキー名の表示」
2. `keyseq/domain/config.py:115-117,460-465`
3. `keyseq/domain/key_hold.py:119-139`
4. `keyseq/presentation/keyboard_window.py:461-464`

## タスク

- task_01: 変換の表と 3 箇所への適用・テスト
- task_01b: キーボードUIの置換先の Shift+¥ / Shift+ろ を `bar` / `underscore` で保存（ユーザー判断 2026-11-09・実機目視で判明）+ 表に `minus` を追加（36 個）
- task_01c: キー置換の送信先が Shift の要る文字なら Shift 付きで送る（ユーザー判断 2026-11-09・実機目視で判明）
- task_02: 統合確認・実機目視・記録（`codebase_map.md`・`decisions_archive/74`・`current.md`・`/refactor_check`）

## レビュー方針

共通観点（`.claude/rules/review.md`）に加え、保存値・送信・記録の経路に変換が混ざっていないこと、hotkey の表示が変わっていないことを確認する。
