# task_07a_adversarial_fixes

## 目的

完了判定前レビュー（Codex 敵対的 high 2・deep-reviewer M2 / L1）の修正（暫定 35 v0.9 §2-21・§2-22）。JSON 不変。

## 対象範囲

### 1. 停止後に予約済みの入力を実行しない（§2-21）
- `keyseq/presentation/controllers/hook_controller.py` の `on_input_event`（:286〜）: `after(0)` で予約したコールバックの**実行時**に、
  `TriggerAction` と `SendKeyAction` は `self.hook_active and self.custom_input_enabled` が偽なら実行しない（`execute_router_action` を呼ばない）。
  `StopHookAction` / `ToggleModeAction` / `SelectKeymapAction` は従来どおり実行する
- 判定は presentation の予約の口で行う（`ActionExecutor` に UI の状態を持ち込まない）

### 2. 解放の送信が失敗したものを集合に残す（§2-22）
- `keyseq/application/held_inputs.py` の `_release_records`（:140〜）: 送信が成功したものだけ `_remove` する（例外のものは集合に残し、例外は従来どおり集めて返す）
- 同 `_press`（:96〜）: 補償の離すが例外なら集合に残す（成功したときだけ `_remove`）。元の送信の例外は従来どおり送出
- `release_key` / `release_mouse`（行の離す）は既に「例外なら残す」なので変えない
- `keyseq/application/action_executor.py` の `_write_text`（:237〜）: 失敗時の `release_keyboard()` の例外の一覧を捨てず、`execute` の text の分岐（:111〜116）で `_report_held_error` のメッセージに「解放エラー」として含める（例外に添えて送出する・戻り値で渡す等、最小の形で）

### テスト
- tests: `_release_records` で 1 つの離すが失敗すると、それだけ集合に残り他は外れる・次の `release_all` で送り直して外れる / `_press` の補償の離すが失敗すると集合に残る /
  text の失敗時に他の持ち主の離すが失敗すると、その例外がエラーの知らせに含まれ、そのキーは集合に残る / 既存テストで「失敗しても外れる」を期待しているものは §2-22 に合わせて追随
- tests_ui: フック停止の後（`hook_active = False`）・キーマップ一時停止中に、予約済みの `TriggerAction` / `SendKeyAction` のコールバックを実行しても `execute_router_action` が呼ばれない。`StopHookAction` 等は呼ばれる
- 実際の入力を送らない（gateway を差し替える）。実 `config/` を汚さない（既存の App を作るテストの作法に従う・`save_json` の全体差し替えで一時フォルダへの書き込みまで止めない）

## 読むファイル

- `instructions/history/35_key_press_release_actions.md` §2-21〜22・§4.3・§5
- `keyseq/application/held_inputs.py`（全体）・`keyseq/application/action_executor.py:95-130, 199-256`
- `keyseq/presentation/controllers/hook_controller.py:150-175, 280-300`
- `tests/test_held_inputs.py`・`tests/test_action_executor_key_hold.py`・`tests_ui/` の hook_controller の既存テスト

## 含まない

- §2-23（呼び出し先の中の停止の行の一時停止で離さない）は今の実装のまま（正本への記載のみ・task_07）
- 正本の改訂（task_07 でメインが行う）

## 確認

- 上記テスト（実行は verifier）・reviewer（5 観点）
