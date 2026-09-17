# idea_23_key_press_release_actions.md

## 概要

**出力シーケンスに「キーを押す（押しっぱなし）」「キーを離す」アクションを追加する**。
例: shift を押す → 矢印を複数回 → shift を離す / 修飾キーを押したままマウス操作をする。

## 起票経緯（2026-09-18）

出所: ユーザー要望。hotkey アクションで `shift+→` や `ctrl+shift+end` を送っても範囲選択にならない問題の解決策として提案された。
調査の結果、範囲選択の問題の原因は **`keyboard` ライブラリが矢印・Home・End 等を拡張キーフラグなしで送ること**と実機で確定した
（検証: `keyboard.send("shift+right")` は選択されず / 拡張キーフラグ付きの `keybd_event` は選択された）。
範囲選択の問題は拡張キー対応（phase 21 予定）で直すため、本 idea は**その修正では足りない用途がある場合**に着手する。

## 現状

- アクションの種類は `hotkey` / `text` / `mouse_click`（`keyseq/application/action_executor.py` の `execute`）。hotkey は押して離すまでを 1 回で送る（`InputGateway.send_hotkey` = `keyboard.send`）。
- 押す / 離すを個別に送る経路は、キーマップ送信の内部（`_send_mapped_key` = `press_key` → `release_key`）にだけある。
- 連続実行（run_to_end）の停止は `application/sequence_runner.py` の `stop_run_to_end`。

## 提案（方向性・要設計）

- アクション種別 `key_down` / `key_up`（値 = キー名）を追加し、アクション編集ダイアログで選べるようにする。
- **安全策が必須**: シーケンスの途中停止・フック停止・アプリ終了・例外時に、押したままのキーを必ず離す（押しっぱなしのキーが残ると OS 全体の入力が壊れる）。
  押下中のキーを記録し、停止経路で一括で離す案。
- 押したまま次のトリガーを待つ（1 回の実行をまたいで押しっぱなし）を許すかは要検討。
- 送信は拡張キー対応（phase 21）後の送信経路を使う。

## 想定スコープ

- application（ActionExecutor / SequenceRunner の停止経路）+ infrastructure（送信）+ presentation（アクション編集ダイアログ・一覧表示）。
- **JSON スキーマにアクション種別を追加する = 仕様変更フロー必須**（`data_schema.md` / `features.md`）。
- 優先度: 低（範囲選択は拡張キー対応で解決する見込み）。
