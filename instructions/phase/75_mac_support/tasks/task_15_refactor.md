# task_15_refactor

## 目的

phase 75 の `/refactor_check` で「推奨」になった提案書 28（`instructions/modified_proposal/28_refactor_mac_support.md`）の R1・R2 を行う（ユーザー判断 2026-11-22「phase 75 の追加タスク」）。

- **挙動は変えない**（ログ・例外・メッセージ・公開面〔`get_backend()`・`install_minimize_grab_custody(app)`〕は今のまま）。正本 `spec_detail/` は変えない。
- domain / application・JSON スキーマ・Windows の backend は変えない。

## 対象範囲（infrastructure の `os_backend/macos/` と presentation の `modal.py` だけ・ファイルの分割）

### R1: `keyseq/infrastructure/os_backend/macos/backend.py` を 1 クラス 1 ファイルへ

- 移す先（新規。keyboard / mouse / tk_key_translator は Windows の `windows/` と同じ名前）:
  - `keyboard_backend.py` = `MacKeyboardBackend` と、それだけが使う `_Hook`・`_normalize_key_name`・`_unicode_chunks`・`_EXTENDED_VKS`・`_REJECTED_WINDOWS_MODIFIER_NAMES`。**`_physical_flags` と `_PHYSICAL_FLAGS_FAILURE_LOGGED` もここに置く**（`MacWindowBackend.is_shift_down` / `is_ctrl_alt_win_down` も使うので、`window_backend.py` は `from .keyboard_backend import _physical_flags` で使う。global は keyboard_backend.py に 1 つだけ・コピーしない。keyboard は window を import しないので循環しない）
  - `mouse_backend.py` = `MacMouseBackend` / `window_backend.py` = `MacWindowBackend` と `_OVERLAY_ALPHA` / `tk_key_translator.py` = `MacTkKeyTranslator`（`from .keyboard_backend import MacKeyboardBackend` を使う）/ `ime_backend.py` = `MacImeBackend` / `app_identity.py` = `MacAppIdentity`
- `backend.py` には `create_backend()` と組み立てに要る import だけを残す。
- 中身はそのまま移す（名前・引数・処理・モジュールの定数を変えない）。モジュールの間の import が循環しないこと。
- **ロガー**: 各モジュールに `_LOG = logging.getLogger(__name__)` を置く（ロガーの名前はモジュールごとに変わるのを許す・ログの本文は変えない）。テストの `assertLogs` / `_LOG` の patch は、そのログを出すクラスのモジュールへ向け直す（例: `MacWindowBackend` のログは window_backend）。
- **`backend.py` から各クラスを再輸出しない**（旧パスの横流しの禁止・`file_organization_rules.md`）。`keyseq/`・`tests/`・`tests_ui/` の次をすべて新しいモジュールへ直す（**patch は「使う側のモジュール」の名前空間へ向ける**）:
  - 文字列 `"keyseq.infrastructure.os_backend.macos.backend.XXX"` の patch（`tests/` の `test_macos_ime_backend`・`test_macos_keyboard_backend`・`test_macos_tk_key_translator`・`test_macos_window_backend`・`test_os_backend_contracts`・`test_tk_keys` と `tests_ui/test_action_dialog_key_hold`。`ns_window_for` は window_backend・`EventTap` は keyboard_backend・`InputSourceAPI` と `_LOG` は ime_backend・`app_relaunch.relaunch_app` は app_identity・`create_backend` は backend のまま）
  - `from ...macos import backend` で `backend.MacXxx` / `backend.subprocess` / `backend.os` 等をモジュールの属性として参照する箇所・括弧つきの複数行の import
  - `patch.object(backend, "_PHYSICAL_FLAGS_FAILURE_LOGGED", ...)` は keyboard_backend モジュールへ
  - `tests/test_macos_keyboard_backend.py:139-150` の遅延 import のテストは、`sys.modules` から外すモジュールの並びに新しい 6 モジュールを足す（足さないとキャッシュのまま偽の pass になる）
- `codebase_map.md` で `os_backend/macos/backend.py` を指す箇所すべてを新しいファイル構成に合わせる。

### R2: `keyseq/presentation/modal.py` の `install_minimize_grab_custody` の入れ子の関数を外へ

- 入れ子の `belongs_to_app` / `deferred_check` / `take_custody` / `return_custody` / `deferred_return` を、`app` を最初の引数に取るモジュールの非公開関数（`_belongs_to_app(app, window)` 等）にする。
- `install_minimize_grab_custody(app)` は `install_minimize_preparation(app)` と 2 つの `bind` だけにする（`bind` の関数は `lambda event: _take_custody(app, event)` の形・`after(0, deferred_check)` は `after(0, lambda: _deferred_check(app))` の形）。
- モジュールの状態（`_app_minimized`・`_minimize_check_id`・`_restore_check_id`・`_custody_window`・`_hidden_by_minimize` 等の global）・処理の順・`after(0)` の予約は変えない。入れ子の関数の名前を参照しているテスト（`tests_ui/test_minimize_grab_custody.py`・`tests_ui/test_modal_grab.py`）は新しい関数へ直す。

## 読むファイル

1. 本書・`instructions/modified_proposal/28_refactor_mac_support.md`
2. `keyseq/infrastructure/os_backend/macos/backend.py`（全体）・`keyseq/infrastructure/os_backend/windows/`（分け方の手本・ファイル名だけ）
3. `keyseq/presentation/modal.py:1-185`
4. `grep -rn "macos.backend\|macos import backend" keyseq tests tests_ui` と `grep -rn "install_minimize_grab_custody\|deferred_check\|deferred_return\|take_custody\|return_custody" keyseq tests tests_ui` のヒット
5. `.claude/rules/file_organization_rules.md`

## 含まない

- 提案書 28 以外の整理・名前の変更・処理の改善（idea_66 の失敗経路の修正は含めない）。
- Windows の backend・`contracts.py` の変更。
- 正本 `spec_detail/` の変更。

## 確認

1. verifier（Windows）: compileall clean / `tests` 全件 失敗 0（`test_macos_*`・`test_os_backend_boundary`・`test_os_backend_contracts` を含む）/ `tests_ui` 全件 / smoke。
2. `grep -rnE "macos\.backend|macos import backend|backend\.Mac" keyseq tests tests_ui --include=*.py` のヒットが `create_backend` の参照と `os_backend/__init__.py` だけ。`macos/backend.py` は 80 行以下。`modal.py` に 80 行を超える関数が無い。
3. Mac（ユーザーの Mac の作業時）: `tests` 全件と `tests_ui` の `test_minimize_grab_custody`・`test_modal_grab`・`test_nested_modal_grab`（モジュール指定）・smoke。実機でフックの開始・置換・メニュー・ダイアログを開いたままの最小化と戻し。
4. Windows の目視: ダイアログを開いたままメインを最小化して戻す（入れ子のダイアログを含む）。

## 完了条件

- 確認 1〜4 が pass・**reviewer 採用**。
- 確認 3 は Mac で行うため、Windows 側の確認 1・2・4 と reviewer の後、Mac の作業時に確認 3 を行って完了とする。phase 75 は task_15 の完了で閉じる。
