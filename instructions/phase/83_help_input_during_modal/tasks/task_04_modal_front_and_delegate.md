# task_04_modal_front_and_delegate

## 目的

暫定仕様 [63](../../../history/63_help_follows_front_dialog.md)（v0.5）のうち、ヘルプの付け替えを支える `modal.py` の口と grab の持ち主の解決を作る（§3.1・§3.2・§3.6 の入力先・§5）。
ヘルプ側の付け替え（task_05）はまだ作らない。本タスクだけでは画面の動きは変わらない（新しい口を呼ぶ側がまだ無い・grab の代わりの持ち主になる窓がまだ無い）。
**presentation 限定（`modal.py`・`controllers/config_io/choice_dialog.py`・`dialogs/grid_editor_window.py`）・domain / application / infrastructure 不変・JSON スキーマ不変**。

## 対象範囲（presentation の modal と呼び出し 2 か所）

### `keyseq/presentation/modal.py`

1. **台帳のいちばん手前の変化を知らせる口**（§3.2）
   - `set_modal_front_listener(callback: Callable[[], None] | None) -> None`（`set_modal_presence_listener` と同じ形・登録先は 1 つ）と、呼び出し `_notify_modal_front_changed()`（例外は `logging.getLogger(__name__).exception(...)` で記録して吸収・`_notify_modal_presence_changed` と同じ形）
   - 呼ぶ時点: `grab_modal` で台帳に入れて**存在の通知を済ませたあと** / `restore_grab` で台帳から外したあと、**grab を前の持ち主へ戻す処理まで済ませた最後**に、**どの return の経路でも 1 回**（`try` / `finally` 等で早期 return を含めて必ず通す）
2. **付け替えの対象外の印**（§3.1）
   - `grab_modal(..., help_follow: bool = True)` を足す（キーワード専用）。偽の窓を覚えておく
   - `front_modal() -> tk.Toplevel | None`: 台帳を末尾から見て、`winfo_exists()` が真で `help_follow` が偽でない最初の窓を返す。無ければ `None`（`tk.TclError` の窓は飛ばす）
3. **台帳の窓ごとの最後の入力先**（§3.2・§3.6）
   - `grab_modal` で、初期の入力先（`focus` 引数・省略時は窓自身）を覚える
   - 窓に `<FocusIn>` を `add="+"` で足し、`event.widget` が窓自身でなく、その窓の中の部品（`event.widget.winfo_toplevel() is window`）なら最後の入力先を更新する
   - `last_input(window: tk.Misc) -> tk.Misc | None`: 覚えている部品を返す（無い・破棄済みなら `None`）。台帳から外れた窓の記録は消す
4. **grab の代わりの持ち主の解決**（§5）
   - `mark_grab_delegate(window: tk.Toplevel) -> None`: 「grab を一時的に預かるだけの窓（ヘルプ）」として印を付ける（task_05 でヘルプが呼ぶ）。`modal.py` から help を import しない
   - `resolve_grab_holder(holder: tk.Misc | None) -> tk.Misc | None`: `holder` が印の付いた窓なら、その `master` をたどって印の無い窓を返す（`master` が無い・破棄済みなら `None`）。印が無ければ `holder` をそのまま返す
   - 使う所: ① `grab_modal` の前の持ち主（`previous = resolve_grab_holder(current_holder())`）② `_deferred_check` の `holder = app.grab_current()`（解決した窓を `_custody_window` に入れる・解決した窓で `winfo_viewable()` を見る。印の付いた窓が grab を持っていたら、その窓の grab は `grab_release()` で外す）③ `_restore_modal_focus` の `window = app.grab_current()`（解決した窓で台帳を照合する）

### `keyseq/presentation/controllers/config_io/choice_dialog.py`

- `_grab_holder`（66〜73 行）で `holder = modal.resolve_grab_holder(app.grab_current())` とする（解決できなければ App）

### `keyseq/presentation/dialogs/grid_editor_window.py`

- 70 行の `grab_modal(self, parent, focus=self.canvas)` に `help_follow=False` を足す

### 設計メモ / 制約

- 新しい関数は `modal.py` の既存の関数（`grab_modal` / `restore_grab` / `_deferred_check` / `_restore_modal_focus`）に最小の差分で差し込む。`grab_modal` はすでに長いので、足す処理は別の小さな関数に分けて呼ぶ
- 既存の挙動は変えない: 印の付いた窓も対象外の窓も無いとき、既存のテストの期待値はすべてそのまま通ること
- 「知らせる口」は登録が無ければ何もしない

### テスト

- 新規 `tests_ui/test_modal_front.py`（実 Tk・`tests_ui/test_modal_grab.py` の `make_window` と setUp / tearDown を手本にする）:
  - 知らせる口: `grab_modal` で 1 回呼ばれる / 存在の通知より後に呼ばれる / 破棄で 1 回呼ばれる（前の持ち主へ戻す経路・`previous is None` の経路・開いた順と違う順で閉じた経路のそれぞれ）/ 登録を外すと呼ばれない / 呼んだ先の例外で `grab_modal` も破棄も止まらない
  - `front_modal`: 台帳の末尾を返す / `help_follow=False` の窓を飛ばす / 破棄済みを飛ばす / 空なら `None`
  - `last_input`: 開いた直後は `focus` 引数（省略時は窓自身）/ 窓の中の部品へ `focus_set` して `update()` すると更新 / 窓自身へのフォーカスでは更新しない / 別の窓の部品では更新しない / 台帳から外れると `None`
  - `resolve_grab_holder` と `mark_grab_delegate`: 印が無ければそのまま / 印の窓は `master` / 印の窓が入れ子でもたどる / `None` は `None`
  - 印の付いた窓が grab を持つ状態で `grab_modal` した新しい窓を破棄すると、grab は印の窓の `master`（ダイアログ）へ戻る
- `tests_ui/test_minimize_grab_custody.py` に 1 件足す（既存のテストの後ろ・新しいメソッドとして）: 印の付いた窓（ダイアログの子の Toplevel）が grab を持つ状態で最小化の預かりが走ると、`_custody_window` はダイアログになり、復元でダイアログが grab を持つ（既存のテストの最小化の再現の仕方を手本にする）
- `tests_ui/test_choice_dialog.py` に 1 件足す: 印の付いた窓が grab を持つとき `_grab_holder` はその `master` を返す
- 期待値を変える既存のテスト: なし

## 読むファイル

- `keyseq/presentation/modal.py`（全体）
- `keyseq/presentation/controllers/config_io/choice_dialog.py:20-75`
- `keyseq/presentation/dialogs/grid_editor_window.py:60-75`
- `tests_ui/test_modal_grab.py:1-60, 440-480`（手本）
- `tests_ui/test_minimize_grab_custody.py:1-120`（最小化の再現の手本）
- `tests_ui/test_choice_dialog.py`（`_grab_holder` のテストの手本）
- `instructions/history/63_help_follows_front_dialog.md` §3.1・§3.2・§3.6・§5

## 含まない

- ヘルプの付け替え・状態の控えと復元・`install_grab_handoff` の掛け直し・ヘルプへの `mark_grab_delegate` の呼び出し（task_05）
- 統合確認と実機目視（task_06）
- 正本・`codebase_map.md` の更新（task_07）

## 確認

- verifier（Mac）: `compileall` clean / `unittest discover -s tests` 全 pass / tests_ui は `test_modal_front`・`test_modal_grab`・`test_nested_modal_grab`・`test_minimize_grab_custody`・`test_choice_dialog`・`test_dialog_escape_binding`・`test_child_save_dialog`・`test_welcome_window`・`test_dialog_help_buttons`・`test_help_grab_handoff` をモジュール指定で pass / `-m tests.smoke_app` OK
- 新しいテストが上の項目をすべて含む

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視: 本タスクでは不要（画面の動きは変わらない）。task_06 でまとめて行う

## 結果

- 実装（2026-11-27）: `codex-delegating-implementer`（Sol medium・テストの追加を Luna のサブエージェントへ委譲 = 自己申告）
- メインの軽微修正 2 点: ①`_deferred_check` で代わりの持ち主（ヘルプ）の grab を外すのを「預かると決まったあと」へ移す（預からずに return する経路で grab がどこにも残らなかった）②既存テスト `tests_ui/test_modal_grab.py:382・401`（`bind` が 1 回だけの前提）を、`<Destroy>` の bind が 1 つだけであることを確かめる形に変更（`<FocusIn>` の bind が足されるため・確かめる内容は不変）
- verifier（Mac）: compileall clean / tests 2247 pass（skip 35）/ tests_ui 11 モジュール pass（test_modal_front 11 件）/ smoke OK
- reviewer = **採用**（必須なし）。参考: 二重呼び出しで bind・台帳・通知が増えないテスト / `_deferred_check` でダイアログ表示中は印の窓の grab を外さないテスト（任意）/ `modal.py` 475 行・`grab_modal` 80 行超は元からで `/refactor_check` の候補
- **完了**（2026-11-27）

