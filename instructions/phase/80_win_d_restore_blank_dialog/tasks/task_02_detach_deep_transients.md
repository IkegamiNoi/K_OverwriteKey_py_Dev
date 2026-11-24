# task_02_detach_deep_transients

## 目的

Windows で App を最小化して戻すと、transient の連鎖で 3 段目以降のモーダル（アクションの追加・編集 → プリセット管理 →
プリセットの追加・編集 / 上書き確認）の中身が白いまま描かれない（Tk が中身の HWND を失う・[task01_measurement.md](../task01_measurement.md)）。
正本 `features.md` §4.6「モーダルダイアログの作法」の最小化の項の **例外（Windows）**（1170 行前後・phase 80 で追加）を実装する。
**presentation（`modal.py`）+ OS バックエンドの窓の契約に 1 つ足すだけ・domain / application 不変・JSON スキーマ不変**。

## 対象範囲（presentation + os_backend の窓の契約）

### `keyseq/infrastructure/os_backend/contracts.py` / `windows/backend.py` / `macos/window_backend.py`

- `WindowBackend` に `detaches_deep_transients_during_minimize(self) -> bool` を追加（`releases_topmost_during_modal` と同じ形）。
  Windows = `True` / macOS = `False`（Mac は既に台帳の窓をすべて隠して表示し直している・Mac の挙動は変えない）。
- 同じ Protocol を実装するテスト用の偽バックエンドがあれば同じメソッドを足す（`grep -rn "def releases_topmost_during_modal" tests tests_ui` で確かめる）。

### `keyseq/presentation/modal.py`

計測で成功した手順（記録の X-4）をそのまま実装する。OS の差は上のメソッドだけで分け、Windows 固有の処理を直書きしない。

1. **深さの判定**: 台帳の窓から `wm_transient()` を辿り、App に着くまでの段数を数える（App の直接の transient = 1）。
   段数 3 以上を対象とする。辿れない・App に着かない窓は対象外（既存 `_belongs_to_app` と同じ上限 32 段・例外は対象外として扱う）。
2. **最小化（`_deferred_check`）**: 既存の処理の後、バックエンドが `True` を返し App が `iconic` のとき、台帳の窓のうち対象を
   **開いた順**に: 元の transient の親（パス名）を記録 → `wm_transient("")` → `withdraw()` → `_hidden_by_minimize` に無ければ加える。
   `_hidden_by_minimize` は**開いた順**を保つ（既存の Mac の経路と同じ並び）。記録が既にある（再入）なら重ねて記録しない。
   既存の grab の預かり（`_custody_window`）の判定は変えない。
3. **復元（`_deferred_return`）**: 既存の表示し直し（`deiconify`）と `_return_grab` はそのまま先に行う（transient なしで表示し、grab を戻す）。
   その後、記録があれば `app.after(_REATTACH_DELAY_MS, ...)`（定数 300）で付け直す:
   各窓が存在し、記録した親も存在すれば `wm_transient(親)`。付け直した直後に `wm_state()` が `withdrawn` なら `deiconify()`。
   窓か親が無ければその窓は何もしない（最小化の間に閉じた窓・正本「最小化の間に閉じた窓には何もしない」）。付け直したら記録を消す。
4. **付け直す前にまた最小化された**（`_take_custody` が走った）ときは、予約した付け直しを取り消し、記録は残す（外したまま）。
   次の最小化の判定で二重に記録しない。次の復元で同じ手順で付け直す。
5. モジュールの状態を 1 つ足す場合は既存の `_hidden_by_minimize` 等と同じくモジュール変数とし、`tests_ui/test_minimize_grab_custody.py` の `setUp` の patch 一覧へ加える。

### `tests_ui/test_minimize_grab_custody.py`（テストの追加）

実 App で アクション → プリセット管理（`transient_parent=action`）→ プリセット追加（`PresetDialog(manager, ...)`）を開き、
`self.app.iconify()` / `self.app.deiconify()` と `update()`・付け直しの待ち（`after` で 300ms 超を待つ）で確かめる。
バックエンドの新メソッドは `True` / `False` を patch して OS に依らず流れるようにする。

- 3 段・`True`: 最小化の間は追加の transient が空・復元と待ちの後に transient = プリセット管理・3 枚とも viewable・grab = 追加
- 3 段・`True`・Windows のときだけ（`sys.platform == "win32"`）: 復元後に `ctypes.windll.user32.IsWindow(add.winfo_id())` が真（中身の窓が残る）
- 2 段（App → プリセット管理 → プリセット追加 = 追加は 2 段目）・`True`: 最小化の間も transient を外さない
- 3 段・`False`: transient を外さない（既存の挙動のまま）
- 3 段・`True`・最小化の間に追加を閉じる: 復元で例外が出ない・grab はプリセット管理へ戻る（既存の戻し先の規則）
- 3 段・`True`・付け直す前にもう一度最小化 → 復元: 付け直しが 1 回で済み、transient = プリセット管理
- 既存テスト（A1〜A13・B・C 系）は変えずに通ること

## 読むファイル

- `keyseq/presentation/modal.py:1-217`（編集対象・台帳 / `_belongs_to_app` / `_deferred_check` / `_take_custody` / `_return_custody` / `_deferred_return` / `_return_grab`）
- `keyseq/infrastructure/os_backend/contracts.py:93-110`・`windows/backend.py:47-75`・`macos/window_backend.py:40-80`（編集対象）
- `tests_ui/test_minimize_grab_custody.py:1-116`（編集対象・手本の作り方）
- `keyseq/presentation/dialogs/action_dialog.py:666-670`・`preset_manager.py:75-90`・`preset_dialog.py:13-45`（再現の窓の作り方）
- `instructions/common/spec_detail/features.md:1163-1175`（例外の条文）
- `instructions/phase/80_win_d_restore_blank_dialog/task01_measurement.md`（X-1〜X-4 の失敗と成功）

## 含まない

- 正本・`codebase_map.md` の更新（メインが task_02 の完了時に `codebase_map.md` の modal.py の節を更新 / 記録は task_03）
- Mac の挙動の変更・3 段目以降を作るときの transient の付け方の変更（案 Y・除外）
- 付け直しで withdrawn になる機構の解明・待ち時間の最小化

## 確認

- verifier: `compileall` clean / `unittest discover -s tests` 全 pass / `unittest discover -s tests_ui` 全 pass（**単独実行**）/ `-m tests.smoke_app` pass
- 上の追加テスト 6 件が pass、既存の `test_minimize_grab_custody` の全件が pass
- 実機目視（ユーザー・Windows）: アクションの追加・編集 → プリセット編集… → 追加 を開いたまま、①Win+D → タスクバーのクリック ②Win+D 2 回 ③タイトルバーの最小化 → タスクバー で、
  追加が描かれる・3 枚とも出る・追加に入力でき、他の窓は操作できない・追加が管理の前にある（戻って少し後）。上書き確認でも ①を 1 回

## 完了条件

- 上記確認 pass・**reviewer 採用**（観点に task01_measurement.md「task_02 で確かめること」の正本 §4.6 の条項との組み合わせを含める）
- 実機目視は本タスクで実施（ユーザー）
- 実装エージェント = `codex-implementer`（修正箇所が具体的）
