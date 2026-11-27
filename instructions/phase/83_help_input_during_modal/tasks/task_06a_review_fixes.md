# task_06a_review_fixes

## 目的

task_06 の統合レビュー（deep-reviewer 修正要・codex-reviewer 4 件）でユーザーが採用した指摘と、統合の検証で出たエラー 2 件を直す。
根拠 = 暫定仕様 [63](../../../history/63_help_follows_front_dialog.md) **v0.6**（§2 の v0.6 の項・§3.2・§3.3・§3.4・§3.6・§3.7・§4.3）・decisions.md の「【task_06】統合レビュー」。
**presentation 限定（`help/`・`modal.py`）・domain / application / infrastructure 不変・JSON スキーマ不変**。

## 対象範囲

### `keyseq/presentation/modal.py`

- `is_own_process_foreground() -> bool` を足す（`is_app_foreground` の隣）。`get_backend().window.is_own_process_foreground()` を呼び、`AttributeError` / `OSError` / `tk.TclError` / `ValueError` は偽にする。`is_app_foreground`（メイン窓が前面か）は変えない（最小化から戻したときのフォーカスの規則用）

### `keyseq/presentation/help/help_window_controller.py`

1. **フォーカスの判定（H1）**: `_place_window` の `modal.is_app_foreground(self.app)` を `modal.is_own_process_foreground()` に替える（v0.6 §3.6）
2. **下に置く・入力先を戻すのは付け替えのときだけ（M1）**: `_replace` / `_build` に `follow: bool` を渡す。`_follow` からの作り直しだけ `follow=True` で `_place_window` を呼ぶ。`_open_for_owner`（メニュー・「?」）と最小化からの作り直しでは呼ばない（v0.6 §3.6）
3. **予約し直しの条件（M2・codex P2）**: `_replace` の最初に「いちばん手前の持ち主」（`self._owner()`）を覚え、終わったあと（成功・失敗とも）に今の `self._owner()` と違えば `on_modal_front_changed()` を呼ぶ。今の「窓の親が持ち主と違えば」の判定（`_refollow_if_owner_changed`）はやめる（「?」で持ち主でないダイアログを明示したヘルプを動かさないため・v0.6 §3.3）
4. **最小化からの作り直しで控えを先に書き換えない（codex P3）**: `_recreate_shown` は `self._state` を書き換えず、「通常の表示」にした控えを `_replace` → `_build` へ引数で渡す。成功したときだけ控えが新しくなる（`_replace` の最後の `_save_state`）。失敗したら控えは元のまま（v0.6 §3.4・§3.7）
5. **Tk の deiconify の対策は Mac だけ（M3）**: `_raise_window` は、表示中なら `deiconify` しない（両 OS）。最小化・非表示のとき、`presentation/tk_platform.is_aqua(window)` が真なら作り直し（`_recreate_shown`）、偽なら `deiconify()`（v0.6 §3.7）
6. **App の最小化の間は付け替えを待つ（M4）**: `_follow` は、`self.app.wm_state()` が `iconic` / `withdrawn` なら付け替えず「待っている」を覚える。App の `<Map>`（`event.widget is self.app` のときだけ・`add="+"`・コントローラの作成時に 1 回 bind）で、待っていれば `on_modal_front_changed()` を呼ぶ（v0.6 §3.2）
7. **控える時点（codex P2）**: 絞り込みの文字・タブ・見出しの開閉と選択が変わったときは、その場で `_save_state(window)`（`_restoring` の間は捨てる）。窓の `<Configure>` / `<Map>` / `<Unmap>` とスクロールは今どおり `_schedule_save`（after_idle）（v0.6 §4.3）
- 関数はおおむね 30 行以内（`_build` が長ければ分ける）。ファイルは 300 行以内を目安

### `keyseq/presentation/help/help_window.py` / `help_tab_view.py`

- 7 のため、知らせを 2 つに分ける: 中身の変化（絞り込み・タブ・見出しの開閉と選択）= 既存の `on_state_changed` / 窓とスクロールの変化（`<Configure>`・`<Map>`・`<Unmap>`・`yscrollcommand`）= 新しいキーワード専用引数 `on_view_changed: Callable[[], None] | None = None`。省略時の動きは今と同じ
- `HelpTabView` も同じく、スクロールだけ別の知らせにする

### テスト

- `tests_ui/test_help_follow.py`:
  - `modal.is_app_foreground` を `patch` している所（目安 `:409・426・433`）を `modal.is_own_process_foreground` に替える（期待値の意味は同じ）
  - 新しいメソッドとして足す: ①新しく開く（メニュー・「?」）ときは `lower` も `focus_force` も呼ばれない（M1）②付け替えでは `is_own_process_foreground` が真なら `last_input` へ `focus_force`、偽なら呼ばない（H1）③作り直しの最中に持ち主が変わる（`HelpWindow` の作成を `patch` して、その中で別のダイアログを `grab_modal`）と、成功・失敗とも終わったあとで付け替えが予約される（M2）④「?」で持ち主でないダイアログを明示して開いたヘルプは、`update()` を回しても動かない（codex P2）⑤絞り込みを変えた直後（`update()` を挟まず）に親のダイアログを破棄しても、出直したヘルプの絞り込みは新しい文字（codex P2）⑥最小化からの作り直しを失敗させる（`_build` を `patch` で例外）と、古い窓は最小化のまま残り、控えの `window_state` は `iconic` のまま（codex P3）⑦`tk_platform.is_aqua` を偽に `patch` すると、最小化したヘルプを開き直したとき `deiconify` が使われ作り直さない（同じ窓のまま）・真なら作り直す（M3）⑧App が最小化の間（`wm_state` を `patch` で `iconic`）は付け替えず、App の `<Map>` を `event_generate` すると付け替わる（M4）
  - 既存の `test_reopening_iconic_help_recreates_instead_of_deiconify`（task_06 で追加）は、Mac 以外でも通るよう `tk_platform.is_aqua` を真に固定する
- `tests_ui/test_minimize_grab_custody.py`: task_04 で足したテスト（代わりの持ち主が grab を持つ状態で最小化の預かり）の代わりの持ち主を、本番のヘルプと同じく `transient` なしにする（L2）。それで期待どおりにならなければ、直さずに理由を報告する
- `tests_ui/test_app_ime_shutdown.py`: 2 件の仮の App（`SimpleNamespace`・目安 `:20-27`・`:40-53`）に `help=SimpleNamespace(stop_following=lambda: None, close=lambda: None)` を足す。`trace.mock_calls` の期待値は変えない（統合の検証のエラー 2 件）
- 期待値を変える既存のテスト: 上の `test_help_follow.py` の `patch` の差し替えだけ

## 読むファイル

- `keyseq/presentation/help/help_window_controller.py`（全体）・`help_window.py`（全体）・`help_tab_view.py:1-60, 120-160`
- `keyseq/presentation/modal.py:120-140`・`keyseq/presentation/tk_platform.py`・`keyseq/infrastructure/os_backend/contracts.py:98-110`
- `tests_ui/test_help_follow.py`（全体）・`tests_ui/test_minimize_grab_custody.py`（task_04 で足したテスト）・`tests_ui/test_app_ime_shutdown.py:1-60`
- `instructions/history/63_help_follows_front_dialog.md` §3.2〜§3.7・§4.3

## 含まない

- 正本・`codebase_map.md` の更新・暫定 63 の凍結（task_07）
- 実機目視（task_06 の 4 の 1〜13・本タスクのあとにまとめて行う）
- Welcome の初回のヘルプ（L1）・最前面のときの重なり（L3）・Cmd+H で隠している間（L5）

## 確認

- verifier（Mac）: `compileall` / `unittest discover -s tests` / tests_ui の全モジュールをモジュールごとに別プロセス（task_06 の 2 と同じ）/ smoke。task_06 の結果（tests 2247・tests_ui 1380・エラー 2）より失敗が増えず、エラー 2 が消えている

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視: task_06 の 4 でまとめて行う

## 結果

- 実装（2026-11-27）: `codex-delegating-implementer`（Sol medium・サブエージェントは未使用 = 自己申告）。メインが差分を確認（`deiconify` を新しく足したのは Windows の分岐だけ・窓のイベントの中で窓の状態を読まない・コントローラ 296 行・`_build` を `_prepare_window` へ分割）
- verifier（Mac・画面のロックなし）: compileall clean / tests 2247 pass（skip 35）/ tests_ui 84 モジュール 1388 件（重複を除く）・失敗 0・エラー 0・打ち切り / クラッシュなし（`test_help_follow` 26 件は 3 回とも pass・`test_app_ime_shutdown` のエラー 2 件は解消）/ smoke OK
- reviewer = **採用**（必須なし）。参考: ①`<<NotebookTabChanged>>` はその場で控える（`export_state` が `wm_state` / `geometry` を読む）ので、ttk の Notebook がこの知らせを窓の表示の途中で出すと Tk 9.1 のクラッシュの経路が残りうる（未確認・verifier 3 回では落ちない）→ task_06 の目視で、ヘルプの最小化 → 開き直し・タブの切り替えを繰り返して確かめる ②`select_tab` の知らせが重複しうる（害なし）③`on_view_changed` の省略時の扱いが 2 か所に重複（参考）
- **完了**（2026-11-27）

