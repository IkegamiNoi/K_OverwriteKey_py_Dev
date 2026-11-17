# task_11f_message_box_parent

## 目的

messagebox（presentation の 171 か所・parent ありは 9 か所）を 1 つの入口に通し、Mac で次を満たす。暫定 57 §5.4 の表の「メッセージの窓」の行（**v0.19・ユーザー承認が前提**）に従う。

1. **parent を補う**: parent を渡していない呼び出しに、いちばん内側の表示中のモーダル（なければ表示中のメイン）を parent として渡す。aqua では parent つき = その窓に付くシート（窓と同じレベル）・parent なし = アプリ全体のアラート（レベル 8）で、最前面のメイン（19）の後ろに出る（task_11e の実測）。
2. **エラーを前面に**（ユーザー要件 2026-11-17）: showerror / showwarning は、出す前にアプリを前面にする（他のアプリを操作中でも、その背面に隠れて止まった原因が分からなくならないように）。
3. **最前面の窓の後ろに出ない**: メッセージの窓を出している間は、モーダルと同じく、メイン・ヘルプ・ライセンス・キーボードUIの最前面を外す（task_11e の仕組みに乗る）。

- 変更は presentation（新規 `message_box.py`・呼び出し元の import の 1 行・`modal.py`・`layout_controller.py`・`app.py`）と infrastructure（契約・Windows / macOS の backend）。domain / application は変えない。
- **Windows の動作は変えない**（前面化・最前面を外すのは backend の判定で Mac だけ。parent を補うのは両 OS 共通〔Windows の Tk は parent 省略時も "." が親なので、メインが親のときは同じ〕）。

## 調査の結果（codex-explorer・メインが件数を確認 2026-11-17）

- `from tkinter import messagebox` の直接呼び出しだけ（既存のラッパー・別名なし）。関数は showerror 97・showinfo 49・askyesno 15・showwarning 9・askyesnocancel 1。
- 他のアプリを操作中に出うる経路: `hook_controller.py`（フックの開始・停止の失敗 `:156`・`:231` は `after(0)` で showerror・権限の案内・過負荷・tap の障害・送信エラー `:405`・`:422`・`:450`・`:510`）。いずれも parent なし。
- テストは各モジュールの `messagebox` の名前（`patch("keyseq....messagebox.showerror")`）か `tkinter.messagebox` を差し替える形が約 190 か所。

## 対象範囲

### 新規 `keyseq/presentation/message_box.py`

- `showerror` / `showwarning` / `showinfo` / `askyesno` / `askyesnocancel` / `askokcancel` / `askquestion` / `askretrycancel` を、`tkinter.messagebox` と同じ署名（`title=None, message=None, **options`）で提供する（呼び出し元の書き方を変えないため）。
- 中身は共通の 1 関数: ①`parent` が無ければ補う（`modal` の台帳のいちばん内側で `winfo_exists()` と `winfo_viewable()` が真の窓 → なければ既定のルートが表示中ならそれ → どれも無ければ渡さない）②showerror / showwarning なら `get_backend().window.bring_app_to_front()` ③`modal` のメッセージの窓の出入りを知らせる（下）④**呼び出し時点の** `tkinter.messagebox.<fn>` を呼ぶ（テストの `patch.object(tkinter.messagebox, ...)` が効くように、関数の参照を import 時に固定しない）⑤終わったら（例外でも）出入りを戻す。
- 関数はおおむね 30 行以内。日本語の文字列を置かない。

### 呼び出し元（presentation 配下で `from tkinter import messagebox` している全ファイル）

- `from tkinter import messagebox` を `from keyseq.presentation import message_box as messagebox` に置き換える（1 行だけ。呼び出しの行は変えない）。presentation 以外（あれば）は対象外として報告する。

### `keyseq/presentation/modal.py`

- メッセージの窓の数（`_message_boxes: int`）と `enter_message_box()` / `leave_message_box()` を足す。`is_modal_active()` は「台帳が空でない or メッセージの窓がある」にし、空 ↔ 空でないが変わったときだけ既存の通知（`_notify_modal_presence_changed`）を呼ぶ。

### `keyseq/presentation/app.py`・`keyseq/presentation/controllers/layout_controller.py`

- App は今どおり（`_on_modal_presence_changed` → `_apply_always_on_top`。`_apply_always_on_top` は `resync_keyboard_topmost` も呼ぶ）。
- キーボードUIの最前面: `apply_keyboard_topmost` の値を「チェック and not 監視で外している and not（`modal.is_modal_active()` and backend の `releases_topmost_during_modal()`）」にする。`resync_keyboard_topmost` が開いている / 有効でないと早く戻る分岐はそのまま。

### `keyseq/infrastructure/os_backend/contracts.py`・`windows/backend.py`・`macos/backend.py`

- `WindowBackend.bring_app_to_front(self) -> bool`。Windows = 何もせず True。macOS = `NSApplication.sharedApplication().activateIgnoringOtherApps_(True)` して True・例外は False（ログ 1 回）。

### 設計メモ / 制約

- Tk のメッセージの窓は表示中、Tk の `after` の予約が走らない（Mac のアラートの run loop・メインの実測）。キーボードUIの最前面の監視（`_watch_topmost_tick`）は表示中に動かないので、出す前に③の通知で外しておく必要がある。
- parent が最小化中・withdraw 中のときはシートが見えないので、表示中の窓だけを parent にする（無ければ parent なし = アプリ全体のアラート。②で前面に出る）。
- 既存の parent つき 9 か所はそのまま（補わない）。

## 読むファイル

- `keyseq/presentation/modal.py`（全体）
- `keyseq/presentation/app.py:370-380`・`:725-760`
- `keyseq/presentation/controllers/layout_controller.py:95-130`
- `keyseq/presentation/controllers/hook_controller.py:150-160`（`after(0)` で出す例）
- `keyseq/infrastructure/os_backend/contracts.py:90-130`・`macos/backend.py` の `MacWindowBackend`（`releases_topmost_during_modal` の流儀）・`windows/backend.py:40-60`
- `tests_ui/test_keymap_set_history_flow.py:205-220`（`parent=dialog` を kwargs で確かめる例）

## 含まない

- 割り当て禁止の文言 → task_11d
- ダイアログを開いたままメインを閉じられる件 → idea_59
- ステータスバーへの振り分けの見直し（実行中の知らせを messagebox にするかどうか）

## 確認

- Mac（`../../../.venv/bin/python`）: compileall clean / `-m unittest discover -s tests` が基準線どおり（2122 件前後・失敗 1）/ tests_ui を 1 本ずつ（`test_modal_grab`・`test_minimize_grab_custody`・`test_app_ui_flows`・`test_help_window`・`test_keymap_set_history_flow`・`test_config_io_characterization_keymap_set_startup`・`test_first_launch_flow`・`test_task06_keymap_management_ui`・`test_welcome_window`）が失敗 0 / smoke pass。
- `tests/` に `message_box` のテストを足す（Tk なし・`tkinter.messagebox` と `modal` と backend を patch）: parent を補う順（内側の表示中のモーダル → 表示中のルート → なし）・既存の parent は変えない・showerror / showwarning だけ `bring_app_to_front`・出入りの通知が例外でも戻る・呼び出し時点の `tkinter.messagebox` を使う。
- `tests_ui/test_modal_grab.py`: メッセージの窓の出入りで `is_modal_active` と通知が空 ↔ 空でないのときだけ動く。
- 静的テスト 1 件（`tests/`）: presentation 配下に `from tkinter import messagebox` が `message_box.py` 以外に無い。
- 既存テストが壊れたら、テストの差し替え先が `tkinter.messagebox` で kwargs を厳密に見ているものに限ってテストを直す（実装の仕様は変えない）。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視（Mac・本タスクで実施）:
  1. メインの「最前面に表示」をオンにして「未保存があります」の確認を出すと、メインに付いて前面に出る。
  2. 「キーボードUIを最前面に表示」をオンにしてエラーを出すと、キーボードUIの前に出る。閉じるとキーボードUIが最前面に戻る。
  3. 別のアプリ（テキストエディットなど）を操作中に、フックの開始の失敗などのエラーが出ると、アプリが前面に来てエラーが見える（再現の手順はメインが用意する）。
  4. ダイアログの中から出る確認（例: プリセット管理の削除の確認）がそのダイアログに付いて出る。
- `codebase_map.md` を追従する（メイン）。

## 起票レビュー（reviewer「修正して採用」2026-11-17）の反映 — 上の記述に優先する

- **H1（既存テスト）**: 各モジュールの `messagebox` を差し替えるテスト（`patch("keyseq....messagebox.<fn>")`・`patch.object(<module>.messagebox, ...)`）は、全モジュールの `messagebox` が同じ `message_box` になるので生き残る。壊れうるのは `patch.object(tkinter.messagebox, ...)`（tests_ui で約 68 か所）のうち、parent が足されて kwargs を受けない・厳密に見るもの（例: `tests_ui/test_config_io_characterization.py:625,1426,1780` の `side_effect=lambda *args: ...`）。直し方は `lambda *args, **kwargs` にする / assert の parent を `ANY` にする、に限る（実装の仕様は変えない）。洗い出しは tests_ui を 1 本ずつ流して行う。
  - テストの実行でアプリの前面化（本物の `activateIgnoringOtherApps_`）が走らないように、tests_ui の Tk を使うテストでは `bring_app_to_front` が呼ばれても無害であることを確かめる。フォーカスを奪って他のテストを壊すなら、`message_box` のテストと tests_ui の共通の setUp で backend の `bring_app_to_front` を patch する（メインが判断）。
- **M1（import）**: `from tkinter import messagebox, ttk` などの複合 import が約 12 ファイルある（presentation で messagebox を import するのは 28 ファイル）。messagebox を除いた import を残し、`from keyseq.presentation import message_box as messagebox` を 1 行足す。presentation の外は `main.py:2,19`（起動エラー・ルートなし）だけで対象外。静的テストは `keyseq/presentation` を走査し、`from tkinter import ... messagebox ...` と `import tkinter.messagebox` の両方を見る。
- **M2（キーボードUI）**: `layout_controller.py` に `from keyseq.presentation import modal` を足し、`apply_keyboard_topmost`（`:119-127`）の値に条件を足す（監視の tick が上げ直すのも防げる）。Windows は `releases_topmost_during_modal()` が False で不変。v0.19 の行で v0.18 の「キーボードUIの最前面は grab の間は外れる」を「モーダルまたはメッセージの窓がある間は外す」に置き換える。
- **M3（parent を補う細部）**: 台帳は後ろが内側なので `reversed(_active_modals)` で探す。ルートは `tkinter._default_root`（private 名・`message_box` の中だけで使う）を `winfo_viewable()` で見る（最小化中は偽）。`winfo_exists()` / `winfo_viewable()` の `TclError` は parent なしへ落とす。`kwargs.get("parent") is None` なら補う（`None` を明示した呼び出しも補う）。
- **M4（順序）**: ③の出入り → ②の前面化 → 呼び出し、の順に固定。`leave_message_box` は `try/finally` で、数は負にしない。
- **L1**: `activateIgnoringOtherApps_` は macOS 14 以降で非推奨（動作はする）と backend のコメントに書く。最小化中は前面化しても窓は戻らない（アプリ全体のアラートとして見える）。
- **L2**: 含まないに「simpledialog / filedialog の parent の補完」を足す。目視 3 の再現手順はメインが用意する（フックの開始の失敗を起こす等）。目視に「ダイアログの中の確認を出した後にメインをクリックしても確認が前に出る」を足す。
- **実装の順**: ①`message_box` + import の置き換え + `modal` の出入り → ②`app` / `layout_controller` の条件 → ③`bring_app_to_front`。読むファイルに `layout_controller.py:101-130`・`tests_ui/test_config_io_characterization.py:620-630`・`tests_ui/test_pane_widths_persistence.py:215-225` を足す。

- **完了（2026-11-17）**: verifier（落ちた 2 本はメインがテストの setUp と実装の例外の受け方で対応）・reviewer 修正して採用（BOM の読み込み・kwargs を受けない lambda をメインが反映）・Mac 目視 1〜4 OK。
