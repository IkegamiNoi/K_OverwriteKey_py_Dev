# idea_26_dialog_keyboard_focus.md

## 概要

**Escape を bind しているのにキーボードフォーカスを取らないダイアログ**があり、実使用で
Escape が効かない（キーが親の App へ届く）。phase 27 task_04 の実機目視で
`KeymapSetHistoryDialog` の同不具合が見つかり、**同じ欠落が既存ダイアログにも残っている**。
あわせて、**既存テストが `focus_force()` を呼んでから `event_generate("<Escape>")` している**ため
この種の欠落をテストで検出できない（テストの検出力の問題）。

## 起票経緯（2026-09-22）

出所: [phase 27](../phase/27_keymap_set_load_history/phase.md) task_04 の実機目視（ユーザー指摘「Escape で
ダイアログが閉じない」）。原因調査の診断スクリプトで、**ダイアログ生成直後の Tk フォーカスが
App ルート `.` のまま**であることを実測。task_04 では対象ダイアログ
（`keymap_set_history_dialog.py`）のみ修正し（`tree.focus_set()` を `grab_modal` の直前へ）、
**他ダイアログへの横断適用は範囲外として本 idea へ分離**した。

テスト側の問題は [idea_18](idea_18_escape_delivery_flaky_test.md)（負荷下で Escape 配送が不安定）とは
**別物**（あちらはテストの flaky、こちらは production の欠落 + テストが隠している構図）。

## 現状

- **フォーカスを設定しているダイアログ**: `action_dialog.py:129,275,378` / `keymap_edit_dialog.py:53,82` /
  `preset_dialog.py:39` / `trigger_dialog.py:52,79` / `child_save_dialog.py:284`（実使用で Escape が効く）。
- **Escape を bind しているのにフォーカスを設定していないダイアログ**:
  - `keyseq/presentation/dialogs/orphan_sweep_dialog.py:24`（**診断スクリプトで実測。生成直後の
    フォーカスは App ルート `.`**）
  - `keyseq/presentation/dialogs/quarantine_manage_dialog.py:24`
  - `keyseq/presentation/dialogs/reference_cleanup_dialog.py:55`
- `preset_manager.py` / `layout_delete_dialog.py` は **Escape 自体を bind していない**（挙動の是非は別論点）。
- テスト側: `tests_ui/test_dialog_teardown_flows.py:157` / `test_orphan_sweep_flow.py:540` /
  `test_quarantine_manage_flow.py:319` が **`dialog.focus_force()` の後に Escape を送っている**ため、
  フォーカス欠落があっても緑のまま通る。
- 正本の規定: `spec_detail/features.md` §4.6（ダイアログ作法。Escape で閉じる）。
  **フォーカスの所在についての規定は無い**（＝仕様側の空白）。

## 提案（方向性・要設計）

- **案 A（最小）**: 対象 3 ダイアログの `__init__` で `grab_modal` の直前に
  代表ウィジェットへ `focus_set()` を入れる。task_04 と同じ形。差分は数行。
- **案 B（作法として一本化）**: `modal.grab_modal()` 側でフォーカスを面倒見る
  （引数で受けた代表ウィジェット、無ければ window 自身へ `focus_set`）。
  全ダイアログへ一律に効くが、**既存の `focus_set` 呼び出しとの二重指定**と
  `test_nested_modal_grab.py` の「`__init__` の最後は `grab_modal`」検査への影響を確認する必要がある。
- **テストの補強（案 A / B 共通・必須）**: `focus_force()` に頼らず
  **「生成直後のフォーカスがダイアログ内にあること」**を検査する
  （手本 = `tests_ui/test_keymap_set_history_flow.py` の
  `test_keyboard_focus_moves_into_dialog_and_only_path_column_stretches`）。
  既存の Escape 経路テストから `focus_force()` を外せるかも併せて判断する。
- **正本への追記の要否**: `features.md` §4.6 のダイアログ作法へ「開いた時点で
  ダイアログ内へキーボードフォーカスを移す」を追記するかを判断する（仕様変更フロー対象）。

## 想定スコープ

- **含む**: `orphan_sweep_dialog.py` / `quarantine_manage_dialog.py` / `reference_cleanup_dialog.py` の
  フォーカス設定、対応する `tests_ui` の検出力強化、（案 B なら）`modal.py` の作法変更、
  正本 `features.md` §4.6 への追記可否の判断。
- **含まない**: Escape を bind していないダイアログ（`preset_manager.py` / `layout_delete_dialog.py`）に
  Escape を追加するかどうか / [idea_18](idea_18_escape_delivery_flaky_test.md) の flaky 解消 /
  ダイアログの初期フォーカス位置の UX 設計（どのウィジェットを既定にするか）を全面的に見直すこと。
- **影響レイヤ**: presentation のみ。**仕様変更の見込み** = 案 A なら無し（実装の不具合修正）、
  案 B と正本追記を採るなら `features.md` §4.6 の改訂が必要。
- **規模感**: 案 A なら 1 タスク相当。案 B + 正本追記なら小さめの 1 フェーズ。
