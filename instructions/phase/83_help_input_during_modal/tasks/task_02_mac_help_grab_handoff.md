# task_02_mac_help_grab_handoff

## 目的

macOS で、ダイアログの「?」（Welcome の「ヘルプを開く」を含む）から開いたヘルプを操作できるようにする。
ヘルプが前面にある間は grab をヘルプへ移し、前面でなくなったら親のダイアログへ戻す（案 D）。
根拠 = 正本 `features.md` §4.6「ヘルプの窓」の **例外（macOS）**（2026-11-26 改訂）・実測 = [task01_measurement.md](../task01_measurement.md) §8。
**presentation（help）+ infrastructure（os_backend の窓の契約と 2 実装に 1 メソッドずつ）・domain / application 不変・JSON スキーマ不変**。Windows の挙動は変えない。

## 対象範囲（presentation の help と os_backend の窓の契約）

### 手順 0（メインセッション・実装の前）

- 素の tkinter で、ヘルプ役の窓を **transient にしない**（master = ダイアログだけ）形で案 D が成り立つかを Mac で確かめる（task01_measurement.md §8 の D-2 と同じ操作）。結果を §9 として追記する
- 成り立たなければ実装に進まず、止めてユーザーへ相談する（正本は transient にしない前提）

### `keyseq/infrastructure/os_backend/contracts.py` / `macos/window_backend.py` / `windows/backend.py`

- `WindowBackend` に `hands_grab_to_active_child_window(self) -> bool: ...` を足す（`detaches_deep_transients_during_minimize` の隣）。macOS = `True` / Windows = `False`

### `keyseq/presentation/help/` の grab の受け渡し

- 新規 `help/grab_handoff.py` に `install_grab_handoff(help_window: tk.Toplevel, dialog: tk.Toplevel) -> None` を置く。`get_backend().window.hands_grab_to_active_child_window()` が偽なら何もしない
  - ヘルプの `<Activate>`（`event.widget is help_window` のときだけ）: `help_window.grab_current()` が `dialog` なら `help_window.grab_set()`
  - ヘルプの `<Deactivate>`（同上）: grab の保持者がヘルプなら `dialog.grab_set()`
  - ヘルプの `<Destroy>`（同上）: grab の保持者がヘルプか `None` で、`dialog` が存在し表示中なら `dialog.grab_set()`
  - `tk.TclError` は吸収する（破棄中の窓）。ほかの例外は握りつぶさない
- `help_window_controller.py` の `open_for_dialog`: 新しく作った窓（`_create_window(dialog)`）にだけ `install_grab_handoff(window, dialog)` を掛ける（再利用の `_raise_window` では掛け直さない）
- `welcome/welcome_window.py` の `_open_help`（初回の Welcome が `HelpWindow` を直接作る経路）: 作った直後に `install_grab_handoff(self._help_window, self)` を掛ける

### 設計メモ / 制約

- `modal.py` は変えない。ヘルプは `grab_modal` の台帳（`_active_modals`）に入れない（`is_modal_active()`・フックの停止・最小化の預かりの対象を変えないため）
- ヘルプに `transient` を付けない（正本 §4.6。Mac で transient の子は親より常に上になりダイアログが隠れるおそれ）
- `bind` は `add="+"` で足す（`HelpWindow` の既存の `<Destroy>` を消さない）

### テスト（tests / tests_ui）

- `tests/test_os_backend_contracts.py`: 契約の引数が `["self"]`・Windows = False（`test_detaches_deep_transients_during_minimize_contract` と同じ形）
- `tests/test_macos_window_backend.py`: macOS = True
- 新規 `tests_ui/test_help_grab_handoff.py`（実 Tk・backend は差し替え）:
  - 真のとき: `<Activate>` を `event_generate` で送るとヘルプへ grab が移る / `<Deactivate>` でダイアログへ戻る / ヘルプを破棄するとダイアログへ戻る / ダイアログ以外が grab を持つときは `<Activate>` で奪わない
  - 偽のとき: `<Activate>` を送っても grab はダイアログのまま
  - `open_for_dialog` の新規作成で掛かり、同じダイアログでの再利用では二重に掛からない（`<Activate>` 1 回で grab_set が 1 回）
- 期待値を変える既存のテスト: なし（既存の `tests_ui/test_dialog_help_buttons.py`・`test_help_window.py`・`test_welcome_window.py` は無変更で通ること）

## 読むファイル

- `keyseq/presentation/help/help_window_controller.py`（全体）
- `keyseq/presentation/help/help_button.py`（全体）
- `keyseq/presentation/welcome/welcome_window.py:150-175`（`_open_help`）
- `keyseq/infrastructure/os_backend/contracts.py:98-110` / `macos/window_backend.py:40-50` / `windows/backend.py:48-58`
- `tests/test_os_backend_contracts.py:38-52` / `tests/test_macos_window_backend.py:1-30`（契約テストの手本）
- `tests_ui/test_dialog_help_buttons.py:70-100`（実 App とダイアログ・ヘルプの作り方の手本）
- `tests_ui/test_minimize_grab_custody.py:95-120`（backend のメソッドの差し替え方の手本 = `get_backend().window` の該当メソッドを `patch.object` で真偽に固定）
- `instructions/common/spec_detail/features.md:1049-1062`

## 含まない

- `modal.py`・メニューから開くヘルプ（App が親）の挙動
- 正本・`codebase_map.md` の更新と記録（task_03）
- Windows の挙動の変更

## 確認

- 標準検証（verifier・Mac）: `compileall` clean / `unittest discover -s tests` 全 pass / tests_ui は `test_help_grab_handoff`・`test_dialog_help_buttons`・`test_help_window`・`test_welcome_window`・`test_modal_grab`・`test_nested_modal_grab`・`test_minimize_grab_custody` をモジュール指定で pass / `-m tests.smoke_app` OK
- 実機目視（Mac・ユーザーまたはメイン）: アクションの編集の「?」と Welcome の「ヘルプを開く」で、①ヘルプの絞り込み欄に入力できる ②タブ・見出し・閉じるボタンが効く ③ダイアログへ戻って入力できる（切り替えの 1 回目は前面にするだけ）④App 本体は操作できない ⑤ヘルプを閉じたあとダイアログを操作できる ⑥入れ子のダイアログ（2 段）の「?」でも①〜⑤ ⑦別のアプリへ切り替えて戻っても①〜⑤ ⑧App の最小化 → 復元のあとも操作できる
- 実機目視（Windows・ユーザー）: task_01 §5 の 1〜3 が今までどおりできる

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視: 本タスクで実施（Mac・Windows）

## 結果

- 手順 0（2026-11-26・メイン）: transient なしで成り立つ（[task01_measurement.md](../task01_measurement.md) §9）。クリックした窓が上に出る。実装へ進める
- 実装（2026-11-26）: `codex-delegating-implementer`（Sol medium・サブエージェントは未使用 = 自己申告）
- verifier（Mac）: compileall clean / tests 2247 pass（skip 35）/ tests_ui 7 モジュール中 `test_welcome_window` の 1 件が失敗 / smoke OK
  - 失敗 = `test_help_is_single_child_on_guide_tab_and_closes_with_welcome`（`tests_ui/test_welcome_window.py:132` の「開いた直後も grab は Welcome」）。Mac では開いたヘルプが前面になり、仕様どおり grab がヘルプへ移るため。受け渡しのない前提のテストなので、このテストだけ `hands_grab_to_active_child_window` を偽に固定（メインの軽微修正・期待値は不変）。修正後 `test_welcome_window` + `test_help_grab_handoff` 21 件 pass
- reviewer = **採用**（必須修正なし）。参考: Welcome の初回経路に掛かることを直接確かめるテストはない（実機目視で確認）/ 最小化でヘルプが隠れるかは実機依存（目視 ⑧）/ task_03 で `codebase_map.md` に `hands_grab_to_active_child_window` と `help/grab_handoff.py` を反映する
- 実機目視（2026-11-26・ユーザー）: Mac ①〜⑧・Windows とも問題なし
- 目視で見つかった別件（ユーザー報告）: ヘルプを開いたあとに別のダイアログを開くと、Mac・Windows ともヘルプが操作できなくなる（対応前の Mac と同じ状態）→ 扱いはユーザーと相談中
