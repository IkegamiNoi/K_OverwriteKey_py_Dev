# task_01_restore_focus_on_map

## 目的

アプリを最小化から復元したとき（App の `<Map>`）、grab の返却の直後に、**最内の表示中モーダルの最後のフォーカス先へ
`focus_set`** する（暫定仕様 23 **§3.1-1〜6・§3.2**）。あわせて暫定仕様 **§5 の単体検査 ①〜⑨** を追加する。

レイヤ制約: **presentation 限定**（`keyseq/presentation/modal.py`）+ `tests_ui/`。domain / application・スキーマは不変。
**`deiconify` / `lift` / `focus_force` は呼ばない**（既存テスト a4 を維持）。

## 対象範囲（presentation + tests_ui）

### 1. keyseq/presentation/modal.py

- **フォーカス復帰の関数を切り出す**（例: `_restore_modal_focus(app: tk.Misc) -> None`）。§3.1-2 の定義で窓を決める:
  - `app.grab_current()` を取得（`TclError` / `KeyError` なら何もしない＝stdlib ダイアログ等）。
  - それが**台帳 `_active_modals` に同一性（`is`）で含まれ**、`winfo_exists()` かつ `winfo_viewable()` なら対象
    （判定は `restore_grab` と同じく `is`。`TclError` なら何もしない）。
  - **§3.1-6: 最小化中に `grab_modal` された窓なら何もしない**（下記の記録に含まれる）。
  - 対象なら `target = window.focus_lastfor() or window` へ `target.focus_set()`。**`TclError` / `KeyError` を握る**（§3.1-5）。
- `return_custody`（`install_minimize_grab_custody` 内）は**どの経路でも最後に `_restore_modal_focus(app)` を呼ぶ**
  （App 以外の `<Map>` の早期 return〔`event.widget is not app`〕は除く）。預かりが空の早期 return（`:38-39`）・
  別の窓が grab 中（`:46-47`）・`grab_current()` 解決不能（`:43-45`）の各経路も、フォーカス復帰の呼び出しは通す形に整理する。
  **grab の返却の挙動（どの窓へ・いつ `grab_set` するか）は変えない**。
- **§3.1-6 の記録**: `grab_modal` が `_app_minimized` の間に呼ばれた窓を、モジュール状態（例: `_opened_while_minimized: list[tk.Toplevel]`。
  台帳と同じく同一性で扱う）へ記録し、`restore_grab`（`<Destroy>`）で除く。**二重呼び出し・預かり中の窓の早期 return 経路では記録しない**
  （フォーカス要求も出していないため）。記録の追加位置は `_active_modals.append(window)` の近く。
- **関数はおおむね 30 行以内**（`return_custody` は現在 27 行。戻し先の決定は `_restore_modal_focus` 側へ出す）。
- `codebase_map.md` の更新は**本タスクでは行わない**（task_03）。

### 2. tests_ui/test_minimize_grab_custody.py

- `setUp` で新しいモジュール状態（§3.1-6 の記録）も `_patch(modal, "<名前>", [])` で独立させる（既存 3 状態と同じ形）。
- 追加する検査（暫定仕様 §5 の ①〜⑨。**期待値はダイアログごとの具体 widget で固定**し、`focus_lastfor()` の戻り値を期待値にしない）:
  - ① **預かりあり**: `ActionDialog` を開く → `_minimize` → 復元 → `value_entry.focus_set` が 1 回（`patch.object(..., wraps=...)`）。
  - ② **預かりなし**: `transient` を付けない `tk.Toplevel` + `ttk.Entry` を `modal.grab_modal(window, focus=entry)`（`parent` なし）で開く →
    `app.iconify()` しても表示されたまま（預かりが起きない）→ 復元 → `entry.focus_set` が 1 回。
    **この組み立てで預かりが起きないことを `modal._custody_window is None` で確認**してから復元する（起きた場合は組み立てを見直す）。
  - ③ **別の窓が grab 中（a6 相当）**: a6 と同じ組み立て（`other` は台帳外）→ 復元 → `dialog.value_entry.focus_set` 0 回・
    `other` 側にも `focus_set` を出さない。
  - ④ **最小化中に新しいモーダルを開いて閉じた（a9 相当）**: 復元 → 元の `ActionDialog` の `value_entry.focus_set` が 1 回。
  - ⑤ **預かった窓と新しいモーダルを両方閉じた（a10 相当）**: 復元 → 外側の `ActionDialog` の `value_entry.focus_set` が 1 回。
  - ⑥ **grab 保持者が解決不能（a5 相当）**: 復元 → `focus_set` 0 回。
  - ⑦ **台帳に無い窓**: ③で兼ねてよい（`other` は `grab_modal` を通していない）。兼ねる場合はテスト名 / docstring に明記。
  - ⑧ **最小化中に `grab_modal` した窓**: `ActionDialog` を開いて `_minimize` → `tk.Toplevel` + `ttk.Entry` を
    `modal.grab_modal(child, focus=entry)` で開く（**開いた後で** `entry.focus_set` / `child.focus_set` を wraps で patch）→ 復元 →
    **どちらも 0 回**（開いたときの要求を上書きしない）。
  - ⑨ **最後のフォーカス先**: `ActionDialog` を開く → `action_label_entry.focus_set()` + `update()` で初期フォーカス先と別の欄へ移す →
    `_minimize` → 復元 → **`action_label_entry.focus_set` が 1 回・`value_entry.focus_set` は 0 回**。
  - **ネスト 3 段**（a2 と同じ組み立て）: 復元後に 3 窓とも `winfo_viewable()`・最内（上書き確認）への `focus_set` が 1 回・
    外側 2 窓の窓自身へは出ない。docstring に「OS フォーカスが無い環境ではアクティブ化の経路を通らない。最終確認は実機目視」と注記。
- 既存 13 件（a1〜a13）は**変更しない**。特に **a4 の `deiconify` / `lift` / `focus_force` 0 回**を維持。
- 実 Tk の到達検査（`focus_get()` 依存）は**本タスクでは追加しない**（task_02 で要否を判断）。

### 設計メモ / 制約

- `focus_set` は `patch.object(widget, "focus_set", wraps=widget.focus_set)` で計数する。patch は**復元の直前**にかけ、
  開く時点（`grab_modal` の初期フォーカス）の呼び出しを数えない。
- ⑨で `action_label_entry.focus_set()` を呼んだ後、テスト環境でアプリが OS フォーカスを持たなくても `focus_lastfor()` は
  その widget を返す見込み（Tk は Toplevel ごとに最後のフォーカス先を記録する）。**期待どおりにならない場合は実装を止めて報告**
  （テストを緩めない）。
- 例外の握り方は既存の `modal.py` に合わせる（`except (tk.TclError, KeyError)`）。

## 読むファイル

1. `instructions/history/23_focus_restore_after_minimize.md` の **§3 / §5**
2. `keyseq/presentation/modal.py`（全体・133 行）
3. `tests_ui/test_minimize_grab_custody.py`（全体・321 行。`setUp` / `_minimize` / `_action` / a2・a5・a6・a9・a10 の組み立て）
4. `keyseq/presentation/dialogs/action_dialog.py:48-49` / `:59-62` / `:120-135`（`value_entry` / `action_label_entry` / `grab_modal` 呼び出し）

## 含まない

- 正本 `features.md` / `codebase_map.md` の更新・暫定仕様の凍結（**task_03**）。
- 実 Tk の到達検査・統合確認・実機目視（**task_02**）。
- 最小化を伴わない再アクティブ化（`<FocusIn>` / `<Activate>` の結線）・閉じた後のフォーカス。
- `grab_modal` の初期フォーカス（phase 28）の変更。
- python の実行（Codex は実行できない。実測は `verifier`）。

## 確認

`.venv` の python（`..\..\..\.venv\Scripts\python.exe`）で `verifier` が実施する。

1. `python -m compileall -q keyseq` clean。
2. `python -m unittest tests_ui.test_minimize_grab_custody -v` 全 pass（既存 13 件 + 追加分）。
3. **変異検査**（一時編集のみ・`git checkout` / `git stash` は使わない）:
   a. `return_custody` から `_restore_modal_focus` の呼び出しを外す → ①④⑤⑨・ネスト 3 段が赤。
   b. `focus_lastfor()` を使わず常に初期フォーカス先相当（窓自身）へ戻す → ⑨が赤。
   c. §3.1-6 の除外を外す → ⑧が赤。
   d. 台帳の判定を外す → ③（⑦）が赤。
4. `python -m unittest tests_ui.test_nested_modal_grab tests_ui.test_modal_grab tests_ui.test_dialog_initial_focus` pass。
5. `python -m unittest discover -s tests` 556 ran OK（skipped 7）。
6. `python -m unittest discover -s tests_ui` 全 pass（509 + 追加分）。
7. `python -m tests.smoke_app` が `SMOKE OK`。

## 完了条件

- 上記確認 pass・**`reviewer` 採用**。
- 実機目視は **task_02 でまとめて実施**（本タスクでは行わない）。

## 差し戻し（v0.4・2026-09-23）

初回実装の実測（`verifier`）で**既存 a2・a3 と新規 b10 が落ちた**（実 App の 3 段ネストで、`<Map>` 内の即時 `focus_set` が
一番外側のアクション編集を非表示のまま残す）。暫定仕様 23 を **v0.4** へ改訂（ユーザー確定）。次の 2 点を直す:

1. **フォーカス復帰は `after_idle` で予約する**（§3.1-4）。`return_custody` の `finally` で `_restore_modal_focus(app)` を直接呼ばず、
   `app.after_idle(<フォーカス復帰>)` で予約する。**戻し先は予約が実行された時点で決める**（`_restore_modal_focus` の中身はそのまま）。
   grab の返却（`grab_set`）は `<Map>` 内で即時のまま変えない。
2. **最小化中に開いた窓の記録はその回の復元まで**（§3.1-6）。予約したフォーカス復帰の処理の最後で `_opened_while_minimized` を空にする
   （例外時も空にする）。**追加テスト**: ⑧の窓を開いたまま**もう一度**最小化 → 復元すると、その窓の `focus_lastfor()` 先へ `focus_set` が 1 回出る。
- テスト側: 復元後のアサートの前に `after_idle` が処理されること（`_restore_app` の `update()` で処理される見込み。されない場合は
  `update()` を足す。**アサートは弱めない**）。**変異検査**: `after_idle` を外して即時に戻すと **a2・a3・b10 が赤**になること。

## 完了記録（2026-09-23）

- **状態 = 完了**。実装 = `codex-implementer`（初回 + v0.4 差し戻し）。`modal.py`: `_restore_modal_focus` を切り出し、
  `return_custody` の `finally` で **`app.after_idle` へ予約**（grab の返却は `<Map>` 内で即時のまま）/
  `_opened_while_minimized` を記録し、復帰処理の最後で空にする。テスト = b1〜b6・b8〜b11（23 件）。
- **経緯**: 初回（`<Map>` 内で即時 `focus_set`）で既存 a2・a3 + b10 が赤 → 実 App の 3 段ネストで**外側の窓が非表示のまま**になる退行を
  メインが probe で再現（素の Tk では再現せず）→ `after_idle` で解消を確認 → 暫定仕様 v0.4（ユーザー確定）→ 差し戻し。
  追加テスト b11 は**テストの組み立て**（未マップの entry へのフォーカス要求は OS フォーカスの無い環境で保留のまま残り、
  `focus_lastfor()` が窓自身を返す）で落ちたため、メインが `grab_modal` の前に `update()` を 1 行追加（実装は無変更）。
- 実測（`verifier`）: compile clean / `test_minimize_grab_custody` 23 OK（複数回）/ **変異検査 5 種**
  （予約削除 → b1・b2・b4・b5・b9・b10・b11 赤 / **即時呼び出しへ戻す → a2・a3・b10 赤** / `focus_lastfor` 無視 → b9 ほか赤 /
  最小化中の除外を外す → b8 赤 / 記録の消去を外す → b11 赤）/ 関連 47 OK / `tests` 556 OK（skipped 7）/
  `tests_ui` **519 OK ×3** / smoke OK。
- レビュー = `reviewer` **完了可**（初回・差し戻し後とも。参考: `return_custody` 30 行ちょうど / 記録は復元サイクル単位で消える /
  `<Map>` 連続時の予約重複は冪等で安全）。
- 付記: 途中の 1 回の `tests_ui` 一括で `test_dialog_escape_binding` が 11 件落ちたが、以後の一括 3 回・単体で再発せず（本差分は
  実行順で後ろのモジュールのみ・因果経路なし）。phase 28 の Escape / フック再開 family の揺れとして記録のみ。
