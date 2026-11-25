# task_03_integration_and_visual_check

## 目的

task_01〜02 を通しで確かめる（統合確認）。暫定 61 §7 の受け入れ条件のうち、実機でしか確かめられないもの（§7-2・4・7b・Caps Lock・Windows の key_hold の Shift）をユーザーの目視で確かめる。
**コード変更なし**（指摘で直す必要が出たら枝番タスクを起票する）。

## 対象範囲（確認のみ）

### 統合確認

- 自動テスト: task_02 の完了時点で tests 2292（skip 9）/ tests_ui 1334 / smoke が pass（Windows・verifier）。この後に変更が無ければ再実行しない。
- レビュー（`.claude/rules/agent_selection.md` の統合の行）: `deep-reviewer` と `codex-reviewer` に、task_01〜02 の差分（`2fa77e03..HEAD` の keyseq / tests / tests_ui）を通しで見てもらう。

### 実機目視（ユーザー・Windows と macOS）

置換先 `A` のキーマップを 1 つ用意して確かめる（例: `F1` → `A`。キーボードUI で `F1` の枠を選び、Shift を押しながら `A` を押して記録）。

1. 記録と表示: Shift + A で記録すると枠に「A」と出る。Shift なしの A で記録し直すと「a」と出る（§7-4）。
2. 送信: メモ帳 / テキストエディットで `F1` を押すと「A」が出る。Shift を押しながら `F1` でも「A」。Ctrl（Mac は Command）を押しながら `F1` で、`Ctrl+A`（全選択）になる（§7-2）。
3. 小文字の置換先（`F2` → `a`）の動きが今までと同じ（§7-3）。
4. key_hold で Shift を押したままにして（key_hold の押す / 離すのトリガーを使う）、置換先 `A` と phase 74 の記号（例: `!`）を送ると、Shift が余分に押し直されず、key_hold を離すと Shift も離れる（§7-7b。Mac が今回の変更の対象・Windows は従来のままで足さないことの確認）。
5. Caps Lock ON で `F1` を押したときに出る文字を記録する（Windows は「a」、Mac は「A」の見込み・補正はしない）。

## 読むファイル

- [暫定 61](../../../history/61_uppercase_replacement_target.md) §4・§5・§7
- [task_01](task_01_uppercase_target_save_and_send.md)・[task_02](task_02_keyboard_ui_record_and_display.md)

## 含まない

- 正本・`codebase_map.md`・decisions_archive・current.md の完了記載（task_04）
- コードの修正（必要なら枝番タスク）

## 確認

- deep-reviewer・codex-reviewer の結果と採否（指摘の採否はユーザー確認）
- 実機目視 1〜5 の結果（Windows・macOS のそれぞれ。Mac で確かめられない場合はその旨）

## 完了条件

- 統合レビューの指摘の採否が決まり、採用分が直っている（枝番タスク）。
- 実機目視 1〜4 が OK、5 の結果が記録されている。**reviewer 採用**（本タスクはコード変更なしのため、統合レビューの結果の記録の整合を reviewer が確かめる）。

## 結果（2026-11-25 完了）

- 統合レビュー = deep-reviewer 修正して採用 / codex-reviewer P3 × 3（テストの検出力のみ）→ 採用分は task_03a（56b3c8dc）で対応
- 実機目視 = ユーザー報告「目視 OK」（NG なし・OS 別の内訳と 5 の実際の文字は未報告 → 正本には「見込み」・macOS は未確認と書く）
- reviewer 採用（記録の整合）
