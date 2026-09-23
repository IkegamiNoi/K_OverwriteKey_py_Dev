# task_01b_conditional_focus_force

## 目的

task_02 の実機目視①（Win+D → タスクバーから復元 → Escape）が不合格だった。復元時に OS がメイン窓をアクティブにする時点では
grab が預かり中で、Tk がフォーカスを持たないため `focus_set` が効かない（暫定仕様 23 **§1.2 測定 4**）。
v0.5（ユーザー確定）の **§3.1-3 条件つき `focus_force`** と **§3.2 の前面判定関数（FFI 契約つき）** を実装し、§5 ⑩〜⑭を追加する。

- **presentation 限定**（`keyseq/presentation/modal.py`）+ `tests_ui`。domain / application / スキーマは不変。
- task_01 の実装（§3.1-1〜6・`after_idle` 予約・`_opened_while_minimized`）は**変えない**。追加のみ。

## 対象範囲（presentation + tests_ui 限定）

### 1. `keyseq/presentation/modal.py`

1. **前面判定の非公開関数** `_is_app_foreground(app: tk.Misc) -> bool`（§3.2）:
   - OS の前面窓 HWND が `int(app.wm_frame(), 16)` と一致すれば `True`。
   - 取得は**専用の `ctypes.WinDLL("user32")`** の `GetForegroundWindow` を使い、**`argtypes = []` / `restype = ctypes.wintypes.HWND`** を設定する。
     **共有の `ctypes.windll.user32` の属性は変更しない**（`infrastructure/input_gateway.py` と共有しているため）。
     関数オブジェクトの生成は初回呼び出し時に 1 回（モジュール内でキャッシュ）でよい。生成部分は検査 ⑭ から型の設定を確認できるよう
     小さな非公開関数に分けてよい（例 `_foreground_window_fn()`）。
   - 戻り値 `None`（NULL）→ `False`。例外（`AttributeError` / `OSError` / `tk.TclError` / `ValueError`）→ `False`（非 Windows を含む）。
2. **`_restore_modal_focus` への追加**（§3.1-3）: 既存の `target.focus_set()` の**直後**に、
   `app.focus_get() is None` **かつ** `_is_app_foreground(app)` のときだけ **同じ `target` へ `focus_force()`**。
   - 既存の早期 return（台帳外・最小化中に開いた窓・非表示・破棄済み）より**後ろ**に置く＝それらの窓では決して呼ばれない（§5 ⑬）。
   - 既存の `try` / `except (tk.TclError, KeyError)` / `finally`（記録の消去）の内側に置く。**別の `after` / `after_idle` 予約を増やさない**。
   - `lift` / `deiconify` は呼ばない。

### 2. `tests_ui/test_minimize_grab_custody.py`（既存に追加・既存検査は弱めない）

1. **クラス共通の既定**: `setUp` で `modal._is_app_foreground` を **`False` を返すよう差し替える**（実 OS の前面状態でテスト結果が変わらないように。
   既存 a4 は「前面 = 偽」の条件でそのまま成立する）。個別テストで上書きする。
2. 追加（期待値は**具体 widget**。`ActionDialog` なら `value_entry`。`focus_lastfor()` の戻り値を期待値にしない）:
   - ⑩ 前面 = 真・`app.focus_get()` = `None`（`patch.object`）→ `value_entry` へ **`focus_force` 1 回**・`focus_set` 1 回・
     app / dialog の `lift` / `deiconify` 0 回。
   - ⑪ 前面 = 真・`focus_get()` が widget を返す → `focus_force` 0 回（`focus_set` は 1 回）。
   - ⑫ 前面 = 偽・`focus_get()` = `None` → `focus_force` 0 回（§6-6⑤相当）。
   - ⑬ 前面 = 真・`None` でも、§3.1-2 で触らない窓（台帳外の grab 保持者 = b3 の組み立て / 最小化中に開いた窓 = b8 の組み立て）では
     `focus_force` 0 回。
   - `focus_get` の差し替えは**予約した処理が走る `_restore_app()` の間だけ**有効にする（他の検査へ漏らさない）。

### 3. `tests_ui/test_modal_app_foreground.py`（新規・⑭。App を作らない小さな検査）

- 偽の app（`wm_frame()` が `"0x..."` を返すだけのオブジェクト）と、`_foreground_window_fn`（または同等）の差し替えで:
  一致 → 真 / 不一致 → 偽 / **最上位ビットが立つ値**（例 `0x80001234`）で一致 → 真 / 戻り値 `None` → 偽 /
  取得で `OSError` → 偽 / `wm_frame()` が `TclError` → 偽。
- **型の設定**: 実際に生成した関数オブジェクトの `restype is ctypes.wintypes.HWND` かつ `argtypes == []`（非 Windows は `skipUnless`）。
- **共有の `ctypes.windll.user32.GetForegroundWindow` の `restype` を変えていない**こと（生成前後で同一。非 Windows は skip）。

### 設計メモ / 制約

- **即時 `focus_set` / 即時 `focus_force` に戻さない**（§3.1-4。`after_idle` の予約の中で行う）。
- `focus_force` の条件に「前面 = 自アプリのメイン窓」を必ず含める（無条件の `focus_force` は他アプリから入力を奪う・§6-6⑤）。
- `ctypes` を使うのは presentation でこの 1 箇所（§3.2）。`infrastructure/input_gateway.py` へ寄せない・触らない。
- `_restore_modal_focus` はおおむね 30 行以内を保つ（判定は `_is_app_foreground` 側へ出す）。

## 読むファイル

- `instructions/history/23_focus_restore_after_minimize.md` の **§1.2 測定 4 / §3.1-3 / §3.2 / §5（⑩〜⑭と変異検査）**
- `keyseq/presentation/modal.py`（全体・162 行）
- `tests_ui/test_minimize_grab_custody.py:15-95`（組み立て）/ `:147-166`（a4）/ `:325-432`（b1・b3・b8 の形）
- `keyseq/infrastructure/input_gateway.py:1-50`（共有 `windll` の使い方の確認のみ。編集しない）

## 含まない

- 統合確認・二次レビュー・実機目視の再実施 = **task_02（再開）**。
- 正本反映（§3.1-3 の条件つき `focus_force` / §3.1-6 / §7 の残存リスク）・凍結・`decisions_archive/29` = **task_03**。
- 最小化を伴わない再アクティブ化でのフォーカス復帰（§7）/ TOCTOU の対策（§7 で受容済）/ M1 の対処（§7 で記録のみ）。
- grab 預かり（phase 17）の見直し・`input_gateway.py` の変更。

## 確認

`.venv` の python（`..\..\..\.venv\Scripts\python.exe`）で `verifier` が実施する（Codex には python 実行を依頼しない）。

1. `python -m compileall -q keyseq` clean。
2. `python -m unittest tests_ui.test_minimize_grab_custody tests_ui.test_modal_app_foreground -v` 全 pass（既存 23 件 + 追加分）。
3. **変異検査**（スクラッチのコピー上で行い worktree を汚さない）:
   a. `focus_force` の分岐を外す → ⑩赤。 b. 条件 (b)（前面判定）を外す → ⑫赤。 c. 条件 (a)（`focus_get() is None`）を外す → ⑪赤。
   d. `restype` の設定を外す → ⑭の型検査が赤。 e. 早期 return より前へ `focus_force` を移す → ⑬赤。
4. `python -m unittest tests_ui.test_nested_modal_grab tests_ui.test_modal_grab tests_ui.test_dialog_initial_focus` pass。
5. `python -m unittest discover -s tests` 556 ran OK（skipped 7）。
6. `python -m unittest discover -s tests_ui` 全 pass（519 + 追加分）。
7. `python -m tests.smoke_app` が `SMOKE OK`。

## 完了条件

- 上記確認 pass・**`reviewer` 採用**。
- 実機目視は **task_02 の再開でまとめて実施**（①〜⑦を最初から。②は 3 段目まで開く）。
