# decisions_archive / phase 35: 旧形式トリガー一覧の移行の境界値

対応表: phase 35 / 暫定なし（直接改訂モード）/ decisions 35。
起票元: phase 34 task_07d reviewer の参考指摘（移行の境界値の明示テストが無い）/ ユーザー要望（2026-09-26）。
完了 2026-09-26。**application 層の 3 行 + `tests/` のテスト 5 件・JSON スキーマ不変・正本 `data_schema.md` §5.13.3-8 を追記**。

## 問題（起票前の調査で検出・仕様変更フラグ B）

keymap_set の `trigger_set_path`（旧形式の読込元）が**存在しないファイル**を指す場合が正本 §5.13.3 で未定義だった。
実装（`split_loading.py::_migrate_legacy_trigger_set`）はファイルの有無を見ずに移行扱いにしていたため、
アクティブなキーマップに空の一覧が付いて未保存表示になり、アクティブ側が項目を持つ場合は空の
「旧トリガー一覧（<stem>）」キーマップが自動作成されて通知も出ていた。
非文字列は §5.1「型不正の共通規則」で空扱い（移行しない）と既に決まっており、明示テストが無いだけだった。

## 確定した設計判断

| # | 判断（ユーザー 2026-09-26） | 採らなかった案と理由 |
|---|---|---|
| 1 | **ファイルが無いなら移行しない**（旧参照なしと同じ・§5.13.4 の書く値は `""`）。判定は使用済み（`same`）判定の**後** | 現状挙動を仕様に明記 = 存在しないファイルのために空のキーマップ作成・通知・未保存化が起きる |
| 2 | **あるが読めない**（壊れた JSON・最上位が dict でない）は**移行のまま**（読込失敗時の扱いで空の一覧が付く）。§5.12 の「無い / あるが読めない」の区別に揃える | 無い・読めないとも移行しない = 壊れたファイルへの参照も保存時に消える |
| 3 | 項番号をずらさないよう §5.13.3 の**末尾に項目 8** として追記（他節からの「§5.13.3-2」等の参照を保つ） | — |

## 実装と確認

- `split_loading.py::_migrate_legacy_trigger_set` に不在判定（`_resolve_config_relative_path` で解決 → `os.path.exists` が偽なら `"none"`）。
- テスト 5 件（`tests/test_per_keymap_triggers_load.py`）: 不在 × 項目なし / 不在 × `""`・別ファイル参照 / 不在を別キーマップが参照＝`same` /
  あるが読めない（壊れた JSON・list）/ 非文字列 5 種（`1`・list・dict・`None`・`True`）。
- 実測: compile clean / tests 674（skip 7）/ tests_ui 576 / smoke pass。reviewer = 完了可（指摘なし）。
- 裏取り: 保存側は状態に関係なく keymap_set の `trigger_set_path` に常に `""` を書く（`split_payloads.py:354`）ため、`"none"` でも §5.13.4 を満たす。
  通知・一括保存の行（`keymap_set_io.py` / `child_save_rows.py`）は `state == "migrated"` のときだけ働く。
- 起票時の整合チェック（reviewer）= 問題なし。

## 残件（別タスク化候補のまま）

- L-1 / L-7（phase 34 統合レビュー保留）・`config_service/__init__.py` 1133 行・80 行超の関数 5 つ。

## refactor_check

**不要**。`keyseq/` の変更は `split_loading.py` の +3 行のみ（666 行・`_migrate_legacy_trigger_set` 33 行）で M1〜M6 いずれも非該当（verifier 実測・PHASE_BASE = `e9cbc92`）。
