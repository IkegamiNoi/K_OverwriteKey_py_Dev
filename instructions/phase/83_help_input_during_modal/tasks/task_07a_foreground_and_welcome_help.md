# task_07a_foreground_and_welcome_help

## 目的

phase 83 の完了判定前レビューで採用したコードの指摘 2 件を直す（decisions_archive/83 の「【task_07】完了判定前レビュー」）。
**presentation 限定（`modal.py`・`welcome/welcome_window.py`）・JSON スキーマ不変**。

## 対象範囲

### `keyseq/presentation/modal.py`

- `is_own_process_foreground()` を、`get_backend().window.foreground_own_window()` が `None` でないかで判定する形に変える（Windows・macOS とも、このプロセスの窓が前面と確かに言えるときだけ値を返す。前面の窓が分からないときは偽）。例外の扱い（`AttributeError` / `OSError` / `tk.TclError` / `ValueError` は偽）は今のまま。`WindowBackend.is_own_process_foreground` は変えない（ほかの用途で使っている）

### `keyseq/presentation/welcome/welcome_window.py`

- `_open_help` の、初回の Welcome で既存のヘルプを前に出す分岐（今は `deiconify()` → `lift()` → `focus_set()`）:
  - 表示中（`wm_state() == "normal"`）なら `deiconify` しない（`lift` と `focus_set` だけ）
  - 最小化・非表示（`iconic` / `withdrawn`）なら、`tk_platform.is_aqua(self)` が偽なら今どおり `deiconify()`。真なら古いヘルプを破棄し、新しい分岐と同じ形（`HelpWindow(...)` → `install_grab_handoff`）で作り直す
  - どちらのあとも今どおり `select_tab("guide")`

### テスト

- `tests_ui/test_modal_front.py` か新しいテストに足す: `foreground_own_window` が `None` のとき `modal.is_own_process_foreground()` は偽・値があれば真・例外なら偽（`get_backend().window` のメソッドを `patch.object` で固定）
- `tests_ui/test_welcome_window.py` に足す（新しいメソッドとして・既存の `test_help_is_single_child_on_guide_tab_and_closes_with_welcome` の作り方を手本に）: ①表示中のヘルプで「ヘルプを開く」をもう一度押すと `deiconify` が呼ばれない ②最小化したヘルプで押すと、`is_aqua` が偽なら同じ窓のまま `deiconify` され `normal`、真なら別の窓に作り直され `normal`・古い窓は破棄・Welcome の子のヘルプは 1 つ
- 期待値を変える既存のテスト: なし（`is_own_process_foreground` を `patch` している既存のテストは、関数ごと差し替えているので影響しない）

## 読むファイル

- `keyseq/presentation/modal.py:120-145`・`keyseq/presentation/welcome/welcome_window.py:1-20, 160-180`・`keyseq/presentation/tk_platform.py`
- `keyseq/infrastructure/os_backend/windows/win32_window.py:228-252`・`macos/window_backend.py:125-170`（判定の意味の確認）
- `tests_ui/test_modal_front.py`・`tests_ui/test_welcome_window.py:120-160`（手本）

## 含まない

- 文書の修正（task_07）・付け替えの作り（Codex 1 は残存リスク）

## 確認

- verifier（Mac）: `compileall` / tests / tests_ui の `test_modal_front`・`test_welcome_window`・`test_help_follow`・`test_help_window`・`test_dialog_help_buttons`・`test_help_grab_handoff`・`test_modal_app_foreground`・`test_minimize_grab_custody` をモジュール指定で / smoke

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視: 不要（task_06 で Welcome と付け替えを確認済み。初回の Welcome の最小化からの開き直しは自動テストで確かめる）

## 結果

- 実装（2026-11-28）: `codex-implementer`（Luna high）。メインが差分を確認（範囲どおり）
- verifier（Mac）: compileall clean / tests 2247 pass / tests_ui 9 モジュール（`test_modal_front` 12・`test_welcome_window` 17・`test_help_follow` 26・`test_help_window` 26・`test_dialog_help_buttons` 13・`test_help_grab_handoff` 6・`test_modal_app_foreground` 8・`test_minimize_grab_custody` 39・`test_app_ui_flows` 105）pass・segfault なし / smoke OK
- reviewer = **修正して採用** → メインの軽微修正: `welcome_window.py` の最小化の判定を `!= "normal"` から `in ("iconic", "withdrawn")` へ（Mac で最大化したヘルプを開くたびに作り直さない・定義どおり）・import の並び。修正後 `tests_ui.test_welcome_window` 17 件 pass（メインが実行）
- **完了**（2026-11-28）
