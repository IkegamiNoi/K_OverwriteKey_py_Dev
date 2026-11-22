# task_15_refactor

## 目的

phase 75 の `/refactor_check` で「推奨」になった提案書 28（`instructions/modified_proposal/28_refactor_mac_support.md`）の R1・R2 を行う（ユーザー判断 2026-11-22「phase 75 の追加タスク」）。

- **挙動は変えない**（ログ・例外・メッセージ・公開面〔`get_backend()`・`install_minimize_grab_custody(app)`〕は今のまま）。正本 `spec_detail/` は変えない。
- domain / application・JSON スキーマ・Windows の backend は変えない。

## 対象範囲（infrastructure の `os_backend/macos/` と presentation の `modal.py` だけ・ファイルの分割）

### R1: `keyseq/infrastructure/os_backend/macos/backend.py` を 1 クラス 1 ファイルへ

- 移す先（新規）:
  - `keyboard_backend.py` = `MacKeyboardBackend` と、それだけが使う `_Hook`・`_normalize_key_name`・`_physical_flags`・`_unicode_chunks`（他のクラスも使う関数があれば、使う側に合わせて置き場所を決め、完了報告に書く）
  - `mouse_backend.py` = `MacMouseBackend` / `window_backend.py` = `MacWindowBackend` / `tk_key_translator.py` = `MacTkKeyTranslator` / `ime_backend.py` = `MacImeBackend` / `app_identity.py` = `MacAppIdentity`
- `backend.py` には `create_backend()` と組み立てに要る import だけを残す。
- 中身はそのまま移す（名前・引数・処理・モジュールの定数を変えない）。モジュールの間の import が循環しないこと。
- **`backend.py` から各クラスを再輸出しない**（旧パスの横流しの禁止・`file_organization_rules.md`）。`keyseq/`・`tests/`・`tests_ui/` の import と `mock.patch` の対象のパス（`"keyseq.infrastructure.os_backend.macos.backend.XXX"` の形の文字列を含む）を新しいモジュールへ直す。
- `codebase_map.md` の `os_backend/macos/backend.py` の行を新しいファイル構成に合わせる。

### R2: `keyseq/presentation/modal.py` の `install_minimize_grab_custody` の入れ子の関数を外へ

- 入れ子の `belongs_to_app` / `deferred_check` / `take_custody` / `return_custody` / `deferred_return` を、`app` を最初の引数に取るモジュールの非公開関数（`_belongs_to_app(app, window)` 等）にする。
- `install_minimize_grab_custody(app)` は `install_minimize_preparation(app)` と 2 つの `bind` だけにする（`bind` の関数は `lambda event: _take_custody(app, event)` の形）。
- モジュールの状態（`_app_minimized`・`_minimize_check_id`・`_restore_check_id`・`_custody_window`・`_hidden_by_minimize` 等の global）・処理の順・`after(0)` の予約は変えない。テストがこれらの入れ子の関数を直接参照していれば、新しい関数へ直す。

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
2. `grep -rn "from keyseq.infrastructure.os_backend.macos.backend import Mac" keyseq tests tests_ui` が 0 件。`macos/backend.py` は 80 行以下。`modal.py` に 80 行を超える関数が無い。
3. Mac（ユーザーの Mac の作業時）: `tests` 全件と `tests_ui` の `test_minimize_grab_custody`・`test_modal_grab`・`test_nested_modal_grab`（モジュール指定）・smoke。実機でフックの開始・置換・メニュー・ダイアログを開いたままの最小化と戻し。
4. Windows の目視: ダイアログを開いたままメインを最小化して戻す（入れ子のダイアログを含む）。

## 完了条件

- 確認 1〜4 が pass・**reviewer 採用**。
- 確認 3 は Mac で行うため、Windows 側の確認 1・2・4 と reviewer の後、Mac の作業時に確認 3 を行って完了とする。phase 75 は task_15 の完了で閉じる。
