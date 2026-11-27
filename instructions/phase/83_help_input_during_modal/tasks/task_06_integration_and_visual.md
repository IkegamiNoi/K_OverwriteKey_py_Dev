# task_06_integration_and_visual

## 目的

phase 83（task_02・task_04・task_05）の変更をまとめて確かめる。暫定仕様 [63](../../../history/63_help_follows_front_dialog.md)（v0.5）§7 の受け入れ条件 A1〜A15 と、task_02 の Mac の grab の受け渡しの両方を、統合の検証・2 つのレビュー・実機目視で確かめる。
あわせて、task_05 の reviewer が参考に挙げた「最小化したヘルプを開き直す経路のテストが無い」を、テストの追加で埋める。
**本体の挙動は変えない**（足すのはテストだけ。レビューで直す必要が出たら、止めて task_06a として起票する）。

## 対象範囲

### 1. テストの追加（実装 = codex-implementer）

- `tests_ui/test_help_follow.py` に新しいメソッドとして 1 件足す: ダイアログの子のヘルプを `iconify()` → `update()` → `open_for_dialog(同じダイアログ, …)`（またはメニューの `open`）→ `update()` のとき、①`app.help.window` は 1 つで `wm_state() == "normal"` ②絞り込みの文字・タブ・開いた見出しが保たれる ③古い窓は破棄されている ④`deiconify` は呼ばれない（`HelpWindow.deiconify` を `patch` で包んで回数を数える・作り直しの中の表示は `apply_state` 経由なので、`_raise_window` から呼ばれないことを確かめる形でよい）

### 2. 統合の検証（verifier・Mac）

- `compileall` / `unittest discover -s tests` / tests_ui は**全モジュールをモジュールごとに別プロセス**（`instructions/phase/75_mac_support/mac_test_baseline.md` の「tests_ui の流し方」・1 モジュール 600 秒で打ち切り）/ `-m tests.smoke_app`
- 件数を phase 82 の基準（tests 2244・tests_ui 80 モジュール 1339 件・失敗 0）と比べ、減っていないことを確かめる

### 3. レビュー（統合・複数タスクを跨ぐ差分）

- `deep-reviewer`（Claude）と `codex-reviewer`（Codex の標準レビュー）。対象 = phase 83 の差分（`git diff 5368be1f..HEAD -- keyseq tests tests_ui`・暫定 63・task01_measurement.md）
- 採否はユーザー。直すものがあれば task_06a として起票する

### 4. 実機目視（ユーザー・Mac / Windows）

`main.py` を worktree から起動して、次を確かめる（暫定 63 §7・task01_measurement.md §13）:

1. メニューからヘルプを開く → アクションの追加を開く → ヘルプの絞り込み欄に入力できる・見出しとタブが効く（A1）
2. アクションの追加の「?」でヘルプを開く → 「プリセット編集…」を開く → ヘルプを操作できる（A2）
3. プリセット編集を閉じる → ヘルプは残り、アクションの追加に戻って操作できる（A3）。ヘルプが一瞬消えて出直すのが気になるか（§2 確認事項 2）
4. 付け替えの前後で、絞り込みの文字・タブ・開いた見出し・スクロール・窓の位置が保たれる（A4）
5. ダイアログを開いた直後・入れ子を閉じた直後に打った文字が、ダイアログの欄に入る（A14）。ヘルプはダイアログを覆わない（A5）
6. ダイアログの間、App 本体は操作できない（A6）
7. 保存の確認などのメッセージボックス・カーソルグリッドの編集窓ではヘルプが付け替わらない（A7）
8. ヘルプを × で閉じてからダイアログを開閉しても、ヘルプは出てこない（A8）
9. Welcome（初回起動・メニューから開き直し）のヘルプ（A9）
10. ほかのアプリを前面にしている間にダイアログが開閉しても、フォーカスを奪わない（A15・確かめられる範囲で）
11. 最後のダイアログを閉じたあと、App 本体へキー入力が届くか（task01_measurement.md §13 の 4）
12. ヘルプを最小化 → 「?」かメニューで開き直すと、通常の状態で出る（task_05 のクラッシュ対策）
13. 終了の確認を取り消したあとも、ヘルプは操作できる（A10）

## 読むファイル

- `instructions/history/63_help_follows_front_dialog.md` §3〜§7
- `instructions/phase/83_help_input_during_modal/tasks/task_05_help_follow.md`（「結果」）
- `tests_ui/test_help_follow.py`（テストの追加の手本）

## 含まない

- 本体の修正（必要になったら task_06a）
- 正本・`codebase_map.md` の更新・暫定 63 の凍結・spike の削除・`/refactor_check`（task_07）
- Python の `ApplePersistenceIgnoreState` を戻すこと（task_06 の検証のあと・ユーザーの許可を取ってから）

## 確認

- 1 のテストを含め、2 の検証がすべて pass（失敗があれば今回の変更との関係を切り分けて記録）
- deep-reviewer と codex-reviewer の結果を記録し、採否をユーザーが決めている
- 4 の目視 1〜13 の結果（Mac / Windows）を記録している

## 完了条件

- 上記確認を満たし、**reviewer 採用**（1 のテストの追加分）
- 実機目視: 本タスクで実施（ユーザー）

## 結果

- 1. テストの追加（2026-11-27）: `codex-implementer` が `tests_ui/test_help_follow.py` に `test_reopening_iconic_help_recreates_instead_of_deiconify` を追加（クラスの末尾・確認項目 ①〜⑤ すべて・メインが差分で確認）
- 2. 統合の検証（verifier・Mac・画面のロックなし）: compileall clean / tests 2247 pass（skip 35・phase 82 の 2244 から +3）/ tests_ui 83 モジュール 1380 件・失敗 0・**エラー 2**・打ち切り / クラッシュなし（phase 82 の 1339 件から増）/ smoke OK
  - エラー 2 = `tests_ui/test_app_ime_shutdown.py` の `test_close_restores_after_hook_stop_before_destroy`・`test_restore_runs_if_hook_stop_raises`。テストの仮の App（`SimpleNamespace`）に `help` が無く、task_05 で足した `App.on_close` の `self.help.stop_following()`（`app.py:946`）で AttributeError → task_06a で直す
- 3. レビュー: deep-reviewer = **修正要**（H1 = 付け替えのあとのフォーカスの戻しが本番では動かない〔`is_app_foreground` はメイン窓が前面かの判定〕・M1〜M7・L1〜L6）/ codex-reviewer = 4 件（P1 = H1 と同じ・P2 × 2・P3）。採否はユーザーの判断待ち（推奨 = H1・M1・M2・Codex P2 × 2・P3・L2 を task_06a で直し、暫定 63 を v0.6 に改訂 / M3 = Mac だけ / M4 = App を元に戻したときに付け替える / M5 = 目視 11 で決める / M6・M7・正本の書き換え箇所は task_07）
- task_06a（2026-11-27・完了）で採用分を修正。修正後の統合の検証（Mac）: tests 2247 / tests_ui 84 モジュール 1388 件・失敗 0・エラー 0 / smoke OK
- 目視に追加（task_06a の reviewer の参考 ①）: 14. ヘルプを最小化 → 開き直す・タブを切り替える、を何度か繰り返しても落ちない（Mac）
- 残り: 4 の実機目視（ユーザー・Mac / Windows）

