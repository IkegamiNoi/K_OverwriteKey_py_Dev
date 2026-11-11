# task_07_macos_test_baseline

## 目的

暫定 57 §7「段階 ② の完了時に `tests` / `tests_ui` の結果を基準線として記録する。skip を許すのは `win32` 実装そのものを検証するテストのみ」を行う。
Mac の実測（2026-11-11〜12・task_07c 後）: tests = 1924 件・失敗 89・エラー 15 / tests_ui（モジュールごとに別プロセス）= 1241 件・失敗 42・エラー 14（`test_minimize_grab_custody` を除く）。
本タスクでは、①テスト側の環境差を直す ②Windows の実装・Windows のパスの意味を検証するテストに skip を付ける ③残りを担当タスクつきで基準線として記録する。

**レイヤ制約**: テストコードのみ（`tests/`・`tests_ui/`）。`keyseq/` は変えない。Windows の結果は不変（skip は win32 以外でだけ効く・環境差の修正は Windows でも同じ値になる）。

## 対象範囲（テストのみ）

### A. tests_ui の Tk 9 の長さ（task_05b レビューの参考 2）

- `tests_ui/test_compact_sequence_view.py:465,511,568,589` の `int(X.cget("sashwidth"))` を `screen_distance(X, "sashwidth")`（`keyseq.presentation.tk_platform`）に替える。

### A2. aqua のクリップボードのショートカット（検証で追加・2026-11-12・メインが修正）

アプリは task_05 から aqua では `<Command-c>` 等にバインドする（`tk_platform.primary_modifier`）が、テストは `<Control-c>` を探していた。
- `tests_ui/test_compact_sequence_view.py:366-377`・`test_keymap_list_operations.py:466`・`test_trigger_list_operations.py:287` の `<Control-x>` を `primary_modifier(<widget>)` から作る形にする（Windows では従来と同じ `Control`）。

### B. 一時フォルダのシンボリックリンク（Mac の `/var` → `/private/var`）

quarantine はリンクを経由する置き場を拒む（`quarantine.py:211`）。Mac の一時フォルダは `/var/folders/...` でリンクを経由するため、テスト環境だけで全件が拒まれる（`TMPDIR` を実体のパスにすると 50 件すべて pass を実測）。

- `tests/test_quarantine.py:47`・`tests/test_quarantine_manage.py:19` の一時フォルダのパスを `os.path.realpath(...)` で実体にしてから使う（`TemporaryDirectory()` のオブジェクトはそのまま保持して後始末する）。
- 同じ理由で失敗するテストが他にあれば同じ直し方にする（`tests/test_reference_scan.py` の `/var` 由来の 1 件を含めて確認）。

### C. skip（`sys.platform != "win32"` のときだけ）

理由の文言は「Windows の…を検証する（暫定 57 §7）」の形で、何の Windows 前提かを書く。

1. **Windows の keyboard_backend を import するモジュール**: `tests/test_input_gateway_repeat.py`・`tests/test_input_gateway_send.py` は module 先頭の import が Mac で `ModuleNotFoundError: keyboard` になる。import より前で `raise unittest.SkipTest(...)`（win32 以外）にする。
2. **Windows の Tk keycode / extended ビット**: `tests/test_tk_keys.py` の `test_numpad_names_by_keycode_and_extended_state`（:20）・`test_event_normalizers_prefer_numpad_and_fall_back_to_keysym`（:55）に `@unittest.skipUnless(sys.platform == "win32", ...)`。
3. **Windows のパスの意味（`\` 区切り・大文字小文字の同一視。暫定 57 Q8 で OS 間の共有は対象外）**: 次の 8 件に `skipUnless`:
   - `test_config_service.ParentRefsSchemaTest.test_merge_parent_ref_normalizes_and_deduplicates_paths`
   - `test_file_line_loader.FileLineLoaderTests.test_confirmation_1_normalizes_path_and_separates_encoding`
   - `test_orphan_scan.NormalizeScanDirsTest.test_aliases_are_deduplicated_in_input_order`
   - `test_parent_refs_cleanup.ParentRefsCleanupTest` の `test_current_keymap_set_and_trigger_set_refs_are_protected_when_miss…`・`test_prune_removes_only_stale_refs_and_preserves_runtime`・`test_relative_absolute_and_separator_variants_are_resolved_before_ex…`
   - `test_reference_scan.ReferenceScanTest.test_deduplicates_relative_absolute_and_separator_variants`
   - `test_child_save_rows.ChildSaveRowsTest.test_collect_normalizes_parent_paths_uses_trigger_set_parent_and_scopes_new_collisions`
   - いずれも、B を直した後も Mac で失敗し、原因が `\` または大文字小文字であることを実装者がテストの入力で確かめてから付ける。原因が違えば skip せず報告する。

### D. 基準線の記録（メインが行う）

`instructions/phase/75_mac_support/mac_test_baseline.md` を作る（A〜C の後に verifier で再計測した値で）:
- tests / tests_ui の件数・失敗・エラー・skip、計測環境、tests_ui の流し方
- 残る失敗をモジュール単位で、原因と担当タスク（task_08〜13）つきの表にする
- Mac で tests_ui を通しで流さない理由（実行順依存の Tk の Segmentation fault・`test_grid_editor_window`）と、除外して流すモジュール（スタブのキー検証でモーダルが出る 3 モジュール = task_09 まで・`test_minimize_grab_custody` = task_11 まで）

## 読むファイル

- `tests_ui/test_compact_sequence_view.py:455-595`・`keyseq/presentation/tk_platform.py`
- `tests/test_quarantine.py:40-60`・`tests/test_quarantine_manage.py:10-30`・`keyseq/application/config_service/quarantine.py:203-216`
- `tests/test_input_gateway_repeat.py:1-20`・`tests/test_input_gateway_send.py:1-20`
- `tests/test_tk_keys.py:1-80`
- C-3 の各テストの本体（入力のパスの確認のため）
- skip の既存の書き方: `tests/test_config_service.py:2801`

## 含まない

- `keyseq/` の変更（スタブの実装は task_08〜11、パスは task_12）
- tests_ui の Windows 前提の失敗（テンキー・hotkey の記録など）の skip。Mac の `TkKeyTranslator` を入れる task_09 で再判定する（基準線に記録のみ）
- `test_minimize_grab_custody`（aqua では最小化で入れ子の transient が隠れない・task_11）
- `test_third_party` の Python のバージョン（同梱の第三者ライセンスの表が Windows のビルドの値・task_13）
- tests_ui を Mac で流すための実行スクリプトの追加（基準線の文書に手順として書く）

## 確認

**Mac**（`../../../.venv/bin/python`。tests_ui は通しで流さない）:

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests`: 失敗・エラーが A〜C の分だけ減り（見込み: quarantine 系 50 件 + skip 対象）、増えたものが 0。skip が C の件数だけ増える
- `-m unittest tests_ui.test_compact_sequence_view` が失敗 0
- `-m tests.smoke_app` が pass

**Windows**: 次に Windows で標準検証 4 種を行う機会にまとめて実施する（件数・結果が不変であること。skip は win32 では効かない）。

## 完了条件

- 上記確認 pass・D の基準線の文書を作成・**reviewer 採用**。
  - 2026-11-12 実施: tests 1924 件・失敗 6・エラー 10・skip 28 / tests_ui（モジュールごと）1270 件・失敗 64・エラー 14 / compile clean / smoke OK（verifier・メイン）。reviewer 採用（参考: §7 の skip の範囲の文言の更新はユーザー確認・Mac 用の兄弟テストは後続）。
- 実機目視: なし（テストのみ）。
