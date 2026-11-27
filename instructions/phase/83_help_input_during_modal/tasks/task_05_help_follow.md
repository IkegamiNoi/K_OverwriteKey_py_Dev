# task_05_help_follow

## 目的

暫定仕様 [63](../../../history/63_help_follows_front_dialog.md)（v0.5）の本体 = ヘルプを、いちばん手前のダイアログ（なければ App）の子へ作り直して付け替える（§3・§4・§5）。
task_04 の `modal.py` の口（`set_modal_front_listener`・`front_modal`・`last_input`・`mark_grab_delegate`・`resolve_grab_holder`）を使う。
**presentation 限定（`help/`・`modal.py` の小さな公開関数 1 つ・`app.py` の結線 2 か所）・domain / application / infrastructure 不変・JSON スキーマ不変**。

## 対象範囲（presentation の help と結線）

### `keyseq/presentation/help/help_window_controller.py`（中心）

- **持ち主** `_owner()`: `modal.front_modal()`、無ければ App（§3.1）
- **開く**: `open(tab)` は持ち主の子として作る・あれば再利用（App 固定をやめる・§3.3）。`open_for_dialog(dialog, tab, target_id)` は `dialog` が持ち主なら持ち主の子として再利用 / 作る。持ち主でなければ `dialog` の子として作り直す（新しい窓を先に作ってから古い窓を消す・失敗したら古い窓を残す）。タブ・飛び先・絞り込みを空にする今の動きは変えない
- **知らせの受け口** `on_modal_front_changed()`: その場では何もせず `after_idle` で `_follow()` を 1 回だけ予約する（予約中なら重ねない）。`_follow()` は実行時に持ち主を選び直す（§3.2）
- **付け替え** `_follow()`（§3.3〜§3.5）:
  - 止めている（`stop_following()` 後）・ヘルプが無く親と一緒に消えてもいないなら何もしない
  - ヘルプが**親と一緒に消えていた**（④）なら、控えから持ち主の子として作り直す
  - ヘルプがあって親が持ち主と違えば、持ち主の子として作り直し、古い窓を「②付け替えで外す」として消す
  - 実行中に再び呼ばれたら（`wait_visibility` の中のイベントループからの再入を含む）何もしない（再入を防ぐ・`task01_measurement.md` §13 の 1）
  - 例外は `logging.getLogger(__name__).exception(...)` で記録して吸収。作りかけの新しい窓は「③作り直しの失敗」として消し、古い窓と控えを残す
- **作る手順** `_build(owner)`（§3.4・§3.6・§4.2）:
  1. 控えから状態を戻す間は控えへ書き込まない（`_restoring` の間）
  2. `HelpWindow(owner, content, ..., initial_focus=False)`（作り直しでは初期フォーカスを入れない）→ 状態を戻す（§4.2 の順）→ 表示
  3. 持ち主がモーダルで、持ち主が表示中・App が最小化中でないときだけ: `wait_visibility()` で表示を待ち → `lower(owner)` → `modal.last_input(owner)` があり `modal.is_app_foreground(app)` が真なら、その部品へ `focus_force()`（§3.6）。持ち主が App・最小化中・表示されていないときはこの 3 つをしない（待ちが戻らないのを防ぐ・§13 の 1）
  4. `modal.mark_grab_delegate(window)`。持ち主がモーダルなら `install_grab_handoff(window, owner)`（task_02）
  5. 最前面は今の `apply_topmost()` を作った直後に呼ぶ
- **控え**（§4.1・§4.3）: コントローラが持つ辞書。ヘルプの窓から「状態が変わった」の知らせを受けて更新する（`_restoring` の間は捨てる）。控える物 = 位置と大きさ / 表示状態（通常・最小化）/ 選択中のタブ / 絞り込みの文字 / タブごとの開いた見出し・選択中の見出し・本文のスクロール位置。本文の読込に失敗した窓は、位置と大きさ・表示状態・絞り込みの文字だけ
- **窓の消え方の 4 区分**（§4.3）: 窓を消す前にコントローラが理由を付ける。①利用者の閉じ（×・Escape・`close()`）= 控えを捨て、付け替えない ②付け替えで外す ③作り直しの失敗 ④理由の無い破棄 = 親と一緒に消えた → 控えを残し、`_follow()` を予約する
- **本文**: 付け替え（②④）では読み直さず、最初に読んだ結果を使う。利用者が閉じたあとに新しく開くときは今どおり読み直す（既存の `test_help_window.py:452` の期待を変えない）
- **終了**: `stop_following()` を足す。呼ばれたあとは付け替えない（予約済みも実行しない）

### `keyseq/presentation/help/help_window.py` / `help_tab_view.py`

- `HelpWindow.__init__` に `initial_focus: bool = True`・`on_state_changed: Callable[[], None] | None = None`・`on_user_close: Callable[[], None] | None = None` をキーワード専用で足す（省略時は今と同じ動き・初回の Welcome の経路は無変更）
  - `initial_focus=False` なら `after_idle(self._initial_focus)` を予約しない
  - `on_user_close` があれば、×（`WM_DELETE_WINDOW`）と Escape の「閉じる」はそれを呼ぶ（無ければ今どおり `destroy()`）
  - 状態が変わったとき `on_state_changed` を呼ぶ: 絞り込みの変更・タブの切り替え（`<<NotebookTabChanged>>`）・見出しの開閉（`toggle` / `reveal` / `apply_filter` のあと）・本文のスクロール（`yscrollcommand` を包む）・窓の `<Configure>`（`event.widget is self` のとき）・`<Map>` / `<Unmap>`
- 状態の書き出しと復元: `HelpWindow.export_state() -> dict` / `apply_state(state: dict) -> None`、`HelpTabView.export_state() -> dict` / `apply_state(state: dict) -> None`。戻す順は §4.2（位置と大きさ → 絞り込み → タブごとの開いた見出し・選択中の見出し → 表示の更新 → 選択中のタブ → `update_idletasks()` のあとスクロール位置 → 表示状態）。`apply_filter` が `_open` を空にするので、見出しは絞り込みのあとに戻す

### `keyseq/presentation/modal.py`

- `is_app_foreground(app: tk.Misc) -> bool` を公開する（既存の `_is_app_foreground` の名前を変え、`_restore_modal_focus` の呼び出しも直す。中身は変えない）

### `keyseq/presentation/app.py`

- `self.help = HelpWindowController(self)`（337 行付近）のあと、`modal.set_modal_front_listener(self.help.on_modal_front_changed)` を `set_modal_presence_listener` の登録（392 行付近）と同じ所で登録する
- `on_close`（935 行付近）で `self.hook.begin_shutdown()` の直後に `self.help.stop_following()` を呼ぶ（保存の確認を取り消したときは呼ばれない位置・§3.2）

### 設計メモ / 制約

- `help_window_controller.py` は 300 行を超えそうなら、控えと作る手順を `help/` 内の別モジュール（例: `help/help_follow.py`）へ分けてよい（`.claude/rules/file_organization_rules.md` の Private）。雑多な名前は付けない
- ヘルプに `transient` を付けない。`modal.py` の台帳にヘルプを入れない
- 関数はおおむね 30 行以内

### テスト

- 新規 `tests_ui/test_help_follow.py`（実 Tk・`tests_ui/test_dialog_help_buttons.py` の実 App の作り方を手本・付け替えは `update()` で `after_idle` を回して確かめる）:
  - メニューから開いたヘルプ → `grab_modal` のダイアログを開く → ヘルプの `master` がそのダイアログ・`app.help.window` は 1 つ・古い窓は破棄（A1）
  - 「?」から開いたヘルプ → 入れ子のダイアログを開く → 入れ子の子へ（A2）。入れ子を閉じる → 1 つ前のダイアログの子として出直す（A3）。外側も閉じる → App の子（§2 確認事項 1）
  - 付け替えの前後で、タブ・絞り込みの文字・開いた見出し・選択中の見出し・位置と大きさ・最小化の状態が保たれる（A4）。スクロール位置は `yview()` の値で比べる
  - 付け替えのあと `modal.last_input(owner)` の部品へフォーカスを戻す（`focus_force` を `patch` して呼ばれたことと引数を確かめる）。`is_app_foreground` が偽なら呼ばない（A14・A15）。持ち主が App なら呼ばない
  - 作り直したヘルプは初期フォーカスを予約しない
  - `help_follow=False` のダイアログ（カーソルグリッドの編集窓の代わり）では付け替えない（A7）
  - 利用者がヘルプを閉じた（`close()`・Escape・×）あとにダイアログを開閉しても、ヘルプは出てこない（A8）
  - `stop_following()` のあとは付け替えない（A10）
  - 作り直しの途中の例外（`HelpWindow` の作成や `apply_state` を `patch` で失敗させる）で、古い窓が 1 つだけ残り、控えは残る。絞り込み欄のフックの再開はちょうど 1 回（A13）
  - 付け替えでは本文を読み直さない（`load_content` の呼び出し回数）
  - Mac の受け渡し: `hands_grab_to_active_child_window` を真に固定したとき、付け替えた窓に `install_grab_handoff` が新しい持ち主で掛かる。持ち主が App なら掛からない
- `tests_ui/test_help_window.py` / `tests/` に `HelpTabView` / `HelpWindow` の `export_state` / `apply_state` の往復のテストを足す（新しいメソッドとして）
- **期待値を変える既存のテスト**（暫定 63 §2 確認事項 1 = ダイアログを閉じてもヘルプは残り、持ち主の子へ移る。`update()` を挟んで付け替えを回してから確かめる形に直す）:
  - `tests_ui/test_dialog_help_buttons.py:157-158`（ダイアログを閉じるとヘルプが消え `help.window` が `None`）→ ヘルプは App の子として残る
  - `tests_ui/test_dialog_help_buttons.py:180-183`（同上・子ファイルの保存の流れ）→ 同上
  - `tests_ui/test_dialog_help_buttons.py:202-203`（同上・入れ子）→ 同上
  - `tests_ui/test_dialog_help_buttons.py:207-215`（別のダイアログの「?」で前のヘルプが消える）→ 2 つ目のダイアログが持ち主なら、ヘルプは持ち主の子に付け替わっていて「?」で再利用される。`second` を閉じたあとの期待も §3.5 に合わせる
  - `tests_ui/test_dialog_help_buttons.py:151`（メニューのヘルプが「?」で置き換わる）→ メニューのヘルプはダイアログを開いた時点で付け替わっているので、「?」は再利用になる。`old` が消えていることの期待は、付け替えで外れた窓として成り立つかを確かめて直す
  - 上の行番号は目安。同じ前提（ダイアログを閉じるとヘルプが閉じる・別の親のヘルプは消える）の期待がほかにもあれば、同じ規則で直し、直した `ファイル:行` を報告する

## 読むファイル

- `keyseq/presentation/help/help_window_controller.py` / `help_window.py` / `help_tab_view.py` / `grab_handoff.py`（全体）
- `keyseq/presentation/modal.py:28-100, 130-160`（task_04 の口と `_is_app_foreground`）
- `keyseq/presentation/app.py:330-345, 385-395, 930-970`
- `tests_ui/test_dialog_help_buttons.py:60-220`・`tests_ui/test_help_window.py:290-320, 430-500, 615-660`（手本と期待値の変更箇所）
- `instructions/history/63_help_follows_front_dialog.md` §2〜§5・§7
- `instructions/phase/83_help_input_during_modal/task01_measurement.md` §11〜§13（実測の要件）

## 含まない

- 統合確認と実機目視（task_06）
- 正本・`codebase_map.md` の更新と記録（task_07）
- 初回起動の Welcome の経路の変更（§3.1 の対象外）

## 確認

- verifier（Mac）: `compileall` clean / `unittest discover -s tests` 全 pass / tests_ui は `test_help_follow`・`test_help_window`・`test_dialog_help_buttons`・`test_help_grab_handoff`・`test_welcome_window`・`test_modal_front`・`test_modal_grab`・`test_nested_modal_grab`・`test_minimize_grab_custody`・`test_choice_dialog`・`test_child_save_dialog`・`test_app_ui_flows` をモジュール指定で pass / `-m tests.smoke_app` OK

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視: task_06 でまとめて行う

## 結果

- 実装（2026-11-27）: `codex-delegating-implementer`（Sol medium・新規テストと既存テストの修正を子 2 つへ分担 = 自己申告）。直した既存テスト = `tests_ui/test_dialog_help_buttons.py:150・163・191・215・226・235`（Codex の報告）。改名に合わせ `test_modal_app_foreground.py`・`test_minimize_grab_custody.py` の参照名も置換
- メインの修正: Codex は理由の無い破棄をすべて「親と一緒に消えた」として作り直し、`tests_ui/test_help_window.py:648` の期待値も「作り直す」へ変えていた → 暫定 63 §3.5（親が破棄されたときだけ作り直す）に合わせ、付け替えの時点で元の親が生きていれば控えを捨てて作り直さない形へ直し（`help_window_controller.py` の `_orphan_parent` / `_forget_closed`）、同テストの期待値を元（`destroy` でも × でも参照が消える）に戻した
- verifier 1 回目: `App.state` が `AppState` で上書きされていて `self.app.state()` が落ち、付け替えの経路が全滅 → `wm_state()` へ（コントローラ・`HelpWindow.export_state`）/ 新規テストに `fix_language("ja")` が無い（`tests/test_i18n_test_language_fixed.py`）→ 追加（メイン）
- verifier 2・3 回目: テストの差し替え先を `wm_state` に合わせた / スクロールは割合で戻すと表示の確定後の折り返しでずれる → 先頭に見えていた位置（`@0,0` の index）も控え、置き終えたあとに `HelpWindow.restore_scroll` で戻す（メイン）
- `tests_ui/test_minimize_grab_custody.py` の 2 件（`test_b1_system_action_restores_visible_type_combo_focus`・`test_deep_transient_restore_focuses_preset_add`・最小化から戻したあとのフォーカスが None）は、task_04 より前のコミット c9953b16 でも落ちる → phase 83 の変更と無関係。task_04 の検証（同日）では通っていたので、実行時の Mac の前面の状態（ユーザー不在の間）に左右される見込み（未確定・task_06 でユーザーが居るときに流し直す）
- verifier 4 回目: 先頭の位置は合う。新規テスト `test_follow_preserves_…` が末尾の割合（`yview()[1]`）も比べていたが、比べるタブは選ばれていない（高さが確定しない）ため不安定 → 末尾の比較を外した（仕様が保つのは先頭の位置・メイン）
- reviewer 1 回目 = 修正要（小修正 1 点で採用可）→ メインで反映: ①新しく開くときの初期フォーカス（Notebook）が消えていた退行 → 控えが無いときだけ `initial_focus=True`（作り直しは False のまま）・テスト 1 件追加 ②（参考の採用）作り直しの最中に持ち主が変わると知らせが空振りする → 作り直しの終わりに持ち主を確かめ直して予約し直す（`_refollow_if_owner_changed`）。参考 = `_build` 約 35 行・`test_help_follow.py` 457 行（テスト）・App が Tk ごと破棄された後の `after_idle`（通常は `stop_following` 後で通らない）
- 修正後の検証（2026-11-27 朝）: `test_help_follow`・`test_modal_front`・`test_app_ui_flows`・`test_child_save_dialog`・smoke が 180 秒で打ち切り、`test_help_grab_handoff` が AppKit ごと落ちた（exit 139）。原因は 2 つ: ①メインが足した `_refollow_if_owner_changed` が、作り直しの失敗（古い窓を残す）でも予約し直して失敗を繰り返していた → **作り直しに成功したときだけ確かめ直す形に直した（未検証）** ②**Mac の画面がロックされていた**（`ioreg` の `ScreenIsLocked`・ユーザー不在）→ ロック中は Tk の GUI テストが止まる・落ちる。help と無関係のモジュールも止まったのはこのため（推定）
- **残り**: 画面のロックを解いた状態で verifier を流し直す（tests・`test_help_follow` を 2 回・`test_help_window`・`test_dialog_help_buttons`・`test_help_grab_handoff`・`test_welcome_window`・`test_modal_front`・`test_app_ui_flows`・`test_child_save_dialog`・`test_minimize_grab_custody`〔既知の 2 件を含めロック解除後に通るか〕・smoke）→ pass なら reviewer の確認（修正 2 点の反映）→ `/task_commit`。**task_05 のコードは未コミット**（worktree に残っている）
