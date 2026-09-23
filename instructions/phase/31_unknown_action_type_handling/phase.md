# phase.md

## フェーズ名

種類が不正なアクションの実行（unknown_action_type_handling）

## フェーズの目的

アクション要素の `type` が **無い / 空 / 未知 / 非文字列**のとき、`value` を文字列として前面アプリへ入力してしまう挙動をやめ、
**何も送らず実行時エラーとして通知し、シーケンスをそこで止める**。

**application 限定（`action_executor.py` / `sequence_runner.py`）+ presentation は委譲 1 行（`app.py` の `_perform_action` が戻り値を返す）・
JSON スキーマ不変**。読込時の正規化・一覧表示・編集ダイアログは変えない。

- 起票元: [idea_35](../../backlog/idea_35_unknown_action_type_handling.md)（phase 30 で案 B として分離・完了判定前レビュー high の対処）。
- 主入力（暫定仕様）: [24_unknown_action_type_handling.md](../../history/24_unknown_action_type_handling.md)（**v0.5・ユーザー確定済**）。
- モード: **暫定仕様先行モード**。番号対応: phase 31 / 暫定 24 / decisions 31。

## 確定（ユーザー 2026-09-24）

暫定仕様 24 §2 が正。要点:

- **案 B**: 種類が不正なアクションは何も送らず通知する。**案 X（読込時の要素除去）は採らない**。
- **通知 = 既存の `show_action_error`（案 b）**。原因・種類・ラベルは最終行「エラー:」の文（暫定 24 §3.5）。presentation の通知処理は変えない。
- **シーケンスは止める（案 S）**: run_to_end は停止 / 単発は index を進めない。executor が「送った / 送らなかった」を返す。
  **hotkey 検証エラー・`x` / `y` 不正の進み方は変えない**。
- 通知へ渡す `action` は `type` を文字列化したコピー（暫定 24 §3.2）。
- **`type` の無いアクションへの互換措置はしない**。
- 通知の表示中の入力は既知の制約として受容（暫定 24 §3.6）。

## スコープ

### 含む

- `keyseq/application/action_executor.py`: 種類の判定（非文字列でも例外にしない）・通知・戻り値（暫定 24 §3.1 / §3.2 / §3.5）。
- `keyseq/application/sequence_runner.py`: 戻り値を受けて run_to_end を止める / 単発の index を進めない・`perform_action` の型（§3.2）。
- `keyseq/presentation/app.py:495` `_perform_action`: executor の戻り値を返す（1 行）。
- 単体テスト（executor の種類分岐 / 本物の executor × runner の組み合わせ / 実際の `show_action_error` に非文字列 `type` を通す）。
- フェーズ末: 正本 `data_schema.md` §5.11.1 / §5.11.5 への昇格（暫定 24 §4）・`codebase_map.md`・暫定 24 の凍結。

### 含まない（後送り）

- 暫定 24 §7 の全項目（案 X / 一覧表示・ダイアログの変更 / 通知へのトリガーキー・行番号 / 通知中の実行禁止 /
  `x` / `y` 不正時の進み方 / `value` の型規則 / 読込時の警告）。
- `hook_controller.py` の `show_action_error` の変更（文言・型防御とも）。

## このフェーズで読むファイル

1. 主入力 [暫定仕様 24](../../history/24_unknown_action_type_handling.md)（§2 / §3 / §6）
2. `keyseq/application/action_executor.py`（全体・165 行）
3. `keyseq/application/sequence_runner.py`（全体・156 行）
4. `keyseq/presentation/app.py:100-115`（コールバックの結線）/ `:179-185`（runner の生成）/ `:495-496`（`_perform_action`）
5. `keyseq/presentation/controllers/hook_controller.py:235-253`（`show_action_error`・読むだけ）
6. `tests/test_action_executor_drag.py`（executor テストの組み立ての手本）
7. `keyseq/domain/config.py:144-158`（`normalize_actions`・受け入れ条件 1 の正規化経由ケース）

## タスク

- task_01: executor — 種類の判定・`on_action_error` への通知（`type` を文字列化したコピー）・「送った / 送らなかった」の戻り値 + 単体テスト — **完了**（2026-09-24）
- task_02: runner — 戻り値で run_to_end を止める / 単発の index を進めない・`perform_action` の型・`app.py` の委譲 + 組み合わせテスト
- task_03: 正本反映と記録（暫定 24 §4 を `data_schema.md` §5.11.1 / §5.11.5 へ昇格・`codebase_map.md` / 暫定 24 を凍結 /
  decisions_archive/31 / current.md / idea_35 → INDEX_done / `/refactor_check`）

## レビュー方針

- 共通観点は `.claude/rules/review.md`。
- **本フェーズ固有**:
  - **不正な種類で `input_gateway` が一切呼ばれないか**（send guard にも入らない）。
  - **既存経路の進み方が不変か**（hotkey 検証エラー・`x` / `y` 不正・送信例外は従来どおり index が進み run_to_end は続く）。
    戻り値の「送った」を取り違えていないか。
  - **通知へ渡す `action` が元データを書き換えていないか**・非文字列 `type` で通知側が落ちないか。
  - runner の停止が `reentry_guard` / `_select_trigger` / 予約の取り消しと矛盾しないか（停止の重複が無害か）。
  - 依存方向（application は presentation を import しない。通知は注入コールバック経由のみ）。
