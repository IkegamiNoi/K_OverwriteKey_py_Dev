# idea_70_layout_physical_type_field.md

## 概要

**キーレイアウトの JSON に「どの配列として作ったか」（例: `jis` / `ansi` / `iso`）を書く任意の項目を設け、macOS の JIS の判別をその項目で行う。** 今はキーの有無から推測しており、ユーザーが作ったレイアウトで外れ得る。項目が無い既存ファイルは今の推測で判別する（後方互換）。

## 起票経緯（2026-11-25）

出所: idea_63（キー名の表示の `\` と ¥）の相談の際のユーザーの提案。表示の切り替えはレイアウト JSON の新しい項目で持たせるため配列の判別は不要と整理し、判別の改善は本 idea へ分離した。

## 現状

- 判別を使うのは macOS だけ。`keyseq/infrastructure/os_backend/macos/key_table.py:118` の `is_jis_layout` は、レイアウトのキーに `yen` か `ro` があれば JIS とみなし、JIS だけのキーの番号（¥・ろ・英数・かな）を名前に直す表（`JIS_KEY_TABLE`）を使う。
- 呼び出しは `layout_controller.py:229` → `set_layout_key_ids`（`contracts.py:48`・macOS `keyboard_backend.py:90`）。Windows の `set_layout_key_ids`（`keyboard_backend.py:160`）は走査コードで名前が決まるため判別に使わない。
- 外れる例: JIS の物理キーボード用で ¥・ろ のキーを省いたレイアウト / JIS でないレイアウトに `yen` の名前のキーを置いたもの。

## 提案（方向性・要設計）

- レイアウト JSON の最上位に任意の項目（名前は要設計。例 `physical_layout`）を足す。値が `jis` なら JIS、それ以外の既知の値なら JIS でない、無い・不明なら今の推測。
- backend へ渡すものをキー ID の集合から判別結果（または項目の値）へ変えるか、両方を渡すかを決める。
- 同梱の見本（jis.json・jis_mac.json 等）に項目を書くか。既に入れてある利用者のファイルは書き換わらない点の扱い。

## 想定スコープ

- 含む: レイアウト JSON の読み込み（presentation の `keyboard_layouts.py`）・macOS の判別・正本（`features.md` のレイアウト JSON 節・`key_input.md`）・テスト。
- 含まない: Windows のキー解決・idea_63 の表示の切り替え。
- 仕様変更あり（JSON の任意キーの追加。既存キーは不変）。
