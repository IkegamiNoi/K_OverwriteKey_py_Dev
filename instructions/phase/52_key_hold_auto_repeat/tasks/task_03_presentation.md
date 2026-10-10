# task_03_presentation

## 目的

暫定 36 の presentation 部分: App の配線・知らせの前の停止と表示中の抑止（§4.8・§2-7〜8）・ダイアログの「リピートする」チェック（§5）。
application（`KeyRepeater` / `HeldInputs` / `ActionExecutor`・task_02）と domain の書式（task_01）は変えない。JSON は `repeat` を書く / 消すだけ。**実装後にユーザーの実機目視**（暫定 36 §8 の 12〜14）。

## 対象範囲

### App の配線 `keyseq/presentation/app.py`
- `KeyRepeater(after=self.after, after_cancel=self.after_cancel, get_timing=keyboard_repeat_timing)` を 1 つ作り（`infrastructure/input_gateway.py` のモジュール関数を注入）、
  `HeldInputs(..., repeater=..., on_repeat_error=...)` に渡す（`app.key_repeater` として参照できるように）。`on_repeat_error` は既存の知らせの口 `self.hook.show_action_error("", action, message)` へ
- 既存の `on_change` の配線・`on_close` の `release_all`（予約もここで止まる）は変えない

### 知らせの前の停止と表示中の抑止（§4.8）
- 知らせのダイアログを出す口で、出す前に `key_repeater.begin_suppress()`、閉じた後（finally）に `end_suppress()` を呼ぶ（入れ子は `KeyRepeater` が数える）。対象:
  `HookController.show_action_error`（`hook_controller.py:307`・多重表示の抑止で表示しない場合は呼ばない）と、`ActionExecutor` の `on_runtime_error`（`app.py:137` の `messagebox.showerror`）
- 呼び出しは presentation の小さな口（例: `with app.repeat_suppressed():` の context manager を App か hook_controller に 1 つ）にまとめ、2 か所から使う。`key_repeater` が無い（テスト等）場合は何もしない

### ダイアログ `keyseq/presentation/dialogs/action_key_hold_fields.py` / `action_dialog.py`
- 「リピートする」チェックボックス（`BooleanVar`）と注記「（修飾キーは除く）」を足す。**動作が「押す」かつ対象が「キー」のときだけ表示**（動作のコンボ・対象の切替で表示を切り替える。動作のコンボに選択時のバインドを足す）
- 初期値: 既存の key_hold の押す + キーの行を開いたら `repeat is True`（domain の `wants_repeat`）のときだけ ON。**それ以外（新規・別の種類から・離す / マウスの行を開いた）は ON**。ダイアログ内で切り替えても値は保つ
- OK 時（`action_dialog.py:230-250` の key_hold の組み直し）: 押す + キーの行は `repeat` を常に書く（`True` / `False`）。離す・マウスの行には書かない
- ダイアログの高さは中身に合わせて伸び縮みする既存の作法に従う（チェックの表示 / 非表示）

### テスト（tests_ui。実入力を送らない・実 `config/` を汚さない = App を作るテストは `tests_ui/test_keymap_set_history_flow.py:17-34` の ExitStack 手法。`save_json` を全体差し替えして一時フォルダへの書き込みまで止めない）
- App: `key_repeater` があり `HeldInputs` に注入されている・`get_timing` が `keyboard_repeat_timing`
- 抑止: `show_action_error` の表示中（`messagebox.showerror` を差し替えて中で確かめる）は `begin_suppress` 済みで、閉じた後に解除・表示中に `start` しても開始しない・多重表示の抑止で表示しないときは呼ばない / `on_runtime_error` も同じ
- `on_repeat_error` が `show_action_error` へ届く
- ダイアログ: 押す + キーのときだけチェックが見える（動作・対象の切替）・初期値（新規 ON・別の種類から ON・離す / マウスの行から ON・既存の押す + キーで `repeat` 無し / `False` は OFF・`True` は ON）・保存で `repeat` を書く / 離す・マウスでは書かない
- 一覧の書式 ` (リピート)` がフル表示・省略表示・呼び出し先の表示枠で出る（task_01 の書式が届くこと）

## 読むファイル

- `instructions/history/36_key_hold_auto_repeat.md` §4.8・§5・§6
- `keyseq/presentation/app.py:115-140, 240-250, 660-680`・`controllers/hook_controller.py:300-330`
- `keyseq/presentation/dialogs/action_key_hold_fields.py`（全体）・`dialogs/action_dialog.py:160-260`
- `keyseq/application/key_repeat.py`・`keyseq/domain/key_hold.py`（`wants_repeat`）
- `tests_ui/test_action_dialog_key_hold.py`・`tests_ui/test_key_hold_presentation.py`（手本）

## 含まない

- application・domain の変更（task_01・02）・正本の改訂（task_05）

## 確認

- 上記テスト（実行は verifier）・reviewer（5 観点）
- **ユーザーの実機目視（ホスト OS）**: 暫定 36 §8 の 12（メモ帳で `a` が連続して入り離すで止まる）・13（押したままでフック停止・ダイアログ・アプリ終了で止まる）・14（shift と組み合わせて `A` が連続）
