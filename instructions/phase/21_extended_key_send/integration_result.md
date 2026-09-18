# integration_result（phase 21: 拡張キーを拡張キーとして送る）

対象差分: `9428fea..HEAD`（task_01 = `3e43aea` / task_02b = `fc3d1c4`）。

## 統合確認（verifier・.venv python）

| 項目 | 結果 |
|---|---|
| `-m compileall -q keyseq main.py tests tests_ui` | clean |
| `-m unittest discover -s tests` | 460 ran OK（skipped 7・task_02b で +1） |
| `-m unittest discover -s tests_ui` | 438 ran OK |
| `-m tests.smoke_app` | SMOKE OK |

## 二次レビュー（task_02）

- `codex-reviewer`: 指摘なし。
- `deep-reviewer`: 完了可（条件付き）。ユーザー採否 =
  - **採用 → task_02b**: 指摘 1（拡張キーフラグを検証するテストが無く、フラグを外しても既存 8 本が通る）/
    指摘 8a（非公開 `keyboard._canonical_names` → 公開 `keyboard.normalize_name`）。
    変異検査でフラグを外すと追加テストのみ失敗することを確認。
  - **採用 → 実機目視に 2 項目追加**（下記 ⑥ ⑦）。
  - **記録のみ（保留）4 件**: ①送信途中の失敗で先行キーが OS へ出る ②`,` 区切り多段 hotkey は現状の検証で到達不能
    ③離す側の例外は最初の例外を優先 ④`requirements.txt` の `keyboard` がバージョン非固定。
- task_02b の `reviewer`: 採用。

## 実機目視（ユーザー・2026-09-19）

**全 7 項目 OK**。

1. hotkey `shift+right` を数回 → 範囲選択される。続けて `ctrl+c` でコピーできる … OK
2. hotkey `ctrl+shift+end` / `ctrl+shift+home` → 文末 / 文頭まで選択される … OK
3. キーマップで適当なキーを `right` / `end` へ割り当て、物理 Shift を押しながら押す → 範囲選択される … OK
4. 通常キーの hotkey（`ctrl+c` / `ctrl+v` / `enter` / `a` 等）・text アクション・マウスクリックが従来どおり … OK
5. フックの停止 / トグルキー・通常トリガーの抑止が従来どおり（送信したキーが自分のトリガーを誤起動しない） … OK
6. （追加）拡張キーをトリガー / キーマップ元 / 停止・トグルキーに割り当てた状態で同じキーを送る
   → 自己起動・自己停止しない … OK
7. （追加）`windows` / `menu` / 右 Alt / `num lock` / `print screen` を 1 回ずつ送る → 期待どおり … OK

> 新しい前提: 拡張キーは raw `keybd_event` で送るため `keyboard` の `is_replaying` による素通しが効かず、
> 自分が送った拡張キーがアプリのフックに届く。現状は send guard が先に素通しにするため挙動は不変
> （項目 6 で実機確認済）。

## リファクタ判定（`/refactor_check`）

**不要**（M1〜M6 該当なし。対象 = `keyseq/infrastructure/input_gateway.py` 1 ファイル）。

| 記号 | 測定値 |
|---|---|
| M1 | `input_gateway.py` 130 行（PHASE_BASE 63 行・+67）。600 行閾値に未達 |
| M2 | 最大は `send_hotkey` 約 23 行。80 行超なし |
| M3 | `press_key` / `release_key` の「拡張キー判定 → 分岐」が同型だが **2 箇所**（3 箇所目未発生） |
| M4 | 対象なし |
| M5 | 申し送りコメントの新規追加なし |
| M6 | 既存定数と同値の直値なし（`_EXTENDED_KEYS` の値は `key_identifiers.py` の既存定数と重複なし） |

## 完了判定前レビュー

- `codex-adversarial-reviewer`: **指摘なし（approve）**。キー表・拡張フラグ・押下 / 解放順・例外時の解放・`ctypes` の層閉じを Microsoft 公式ドキュメントと照合して確認。
- `deep-reviewer`: **条件付き完了可**（条件 = 完了処理の実施）。5 観点は仕様適合性・依存方向・責務分離・不要変更 OK。ユーザー採否 =
  - **採用 → task_02c**: 指摘 4（拡張キー経路のテストが「通常キー先・拡張キー最後・1 個」の形しかなく、実装を「通常キーを先にまとめて押す」形へ変えても既存 3 本が通る）。
  - **採用 → 文書修正**: 指摘 2（`codebase_map.md` の旧表記 `keyboard._canonical_names.normalize_name` → 公開 API）/ 指摘 7（`phase.md` のタスク一覧に task_02b・task_02c を追記）。
  - **記録のみ**: 指摘 3（send guard 解除と注入イベント到達のレース）/ 指摘 6（`right alt` と `alt gr` は欧州系配列では同一物理キーだが意図的に対象外）/ 指摘 5（canonical に無い OS 由来の名前は非拡張で送られうる・**経路の実在は未実測**）。
  - **保留 → 別タスク化候補**: 指摘 8（`register_key_hook` に呼び出し元なし = 差分外の既存デッドコード）。
  - **除外（参考）**: 指摘 9（`keybd_event` の失敗を検知しない。`keyboard` 側も同等）。

## task_02c（完了判定前レビュー採用分）

- `tests/test_input_gateway_send.py` に `test_order_with_leading_extended` を 1 本追加（production 変更なし）。
  `right ctrl+c`（拡張キーが先頭 + 通常キー）/ `right ctrl+insert`（拡張キー 2 個）の押す順・離す順を `mock_calls` の完全一致で固定。
- `verifier`: compile clean / `tests.test_input_gateway_send` 10 項目 OK / `tests` 461 OK / smoke OK。
  **変異検査**（押下順を「通常キー先」へ入替）で `test_order_with_leading_extended` のみ FAIL → 復元後に差分なしを確認。
- `reviewer`: **採用**（指摘なし）。
