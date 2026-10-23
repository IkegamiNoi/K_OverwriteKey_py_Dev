# 提案書 25: phase 68（UI 文言の用語統一）後のリファクタ

> 状態: **保留（ユーザー判断 2026-10-24・次の多言語化フェーズで文言の外部化と一緒に吸収）**（2026-10-24 起票）。

## 判定の要約

範囲 `git diff 55aed1d..HEAD -- keyseq/`（78 ファイル・+605 / -508。大半は文字列の置換）。メトリクスは verifier の実測、M3・M4 はメインで裏取り（下記の ファイル:行）。

- **M3・M4 該当**: 子ファイルの種別（キーマップ / トリガーセット / 出力シーケンス）を表示名へ直す表が **4 か所**。phase 68 で 4 か所目（`_PARENT_KIND_LABELS`）を足した。
  種別や表示名を変えると 4 か所を直す形（phase 68 の用語統一でも 3 か所を別々に直した）
  - `presentation/controllers/config_io/child_save_dialog.py:296` `_kind_label`
  - `presentation/controllers/config_io/child_save_rows.py:75` `_PARENT_KIND_LABELS`（親の種類名。値は他の表の表示名と同じ）
  - `presentation/orphan_sweep_text.py:6` `_KIND_LABELS`（`contracts.KIND_*` + 構成セット専用プリセット）
  - `presentation/reference_cleanup_text.py:6` `_KIND_LABELS`
- 非該当: M1（600 行超で +100 以上なし。最大 `keymap_set_io.py` 748 行 +33）/ M2（新規の最長は `choice_dialog.ask_choice` 約 45 行）/ M5（0 件）/ M6（定数モジュールに同値なし。上の表の重複として M3 で扱う）
- 参考（提案書に含めない・別タスク化候補へ）: `config_io/choice_dialog.py` と `config_io/hotkey_presets_io.py:45-90` の `confirm_overwrite` が同じ形のボタン選択ダイアログ（2 か所）

## 項目 0: 安全網の確認

- 対象領域のテスト: `tests/test_child_save_rows.py`・`test_orphan_sweep_text.py`・`test_reference_cleanup_text.py` / `tests_ui/test_child_save_dialog.py`・`test_orphan_sweep_flow.py`・`test_reference_cleanup_flow.py`
- 完了条件: 着手前に `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` / `-s tests_ui` / `-m tests.smoke_app` が全 pass（基準線）

## 項目 1: 子ファイルの種別の表示名を 1 つの表にする（M3・M4）

- 新規 `presentation/child_kind_labels.py`（presentation 直下・Feature Shared）に `KIND_LABELS`（keymap / trigger_set / sequence → 表示名）と `parent_kind_label(kind)`（keymap → 構成セット / trigger_set → キーマップ / sequence → トリガーセット）を置く
- 4 か所をこの表の参照へ置き換える（`orphan_sweep_text` の構成セット専用プリセットは同ファイルに残し、3 種別だけ参照）。表示される文言は変えない
- 完了条件: 4 か所の表が 1 つになる・表示の文言が不変（既存テストがそのまま pass）

## 備考

- 多言語化のフェーズで文言を外部化するなら、この表はその辞書へ移る。多言語化を先にやるなら本提案はそちらへ吸収してよい（ユーザー判断）
