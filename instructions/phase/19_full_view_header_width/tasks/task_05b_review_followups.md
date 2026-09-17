# task_05b_review_followups

## 目的

task_05 二次レビュー（`deep-reviewer` 指摘 3・ユーザー採用 2026-09-17）の採用分のうち、テストで固定するもの。
**保存値が画面幅より広く、かつ最小幅より狭い**場合（例: 画面 700・保存値 750・最小幅 799）は、切り詰め前の保存値 750 < 適用後 799 なので**書く**（暫定仕様17 §3-5 ②の文言どおり）。
この境界を `startup_window_width_to_save` の単体テストに 1 ケース追加する。**テストのみ・実装は変えない**。
（正本の注記と、指摘 1・6 の反映は task_06 で行う。）

## 対象範囲（tests 1 ファイル）

- `tests/test_pane_width_rules.py` `test_startup_window_width_to_save` のケース表に `(750, 799, 799)` を追加（理由コメント付き）。

## 読むファイル

- `tests/test_pane_width_rules.py:44-62` / `keyseq/presentation/pane_width_rules.py` の `startup_window_width_to_save`

## 含まない

- 正本反映（指摘 1: `features.md:62,65,70` の書き換え / 指摘 6: 新規モジュールの `codebase_map.md` 記載 / 指摘 3 の注記）= **task_06**
- 保留（指摘 4・5・8）= task_06 の `/refactor_check` の候補 / 除外（指摘 7・9・10）

## 確認

1. `../../../.venv/Scripts/python.exe -m unittest tests.test_pane_width_rules -v` が全 pass。
2. `git diff --stat` が上記 1 ファイル（+ 本タスク文書）のみ。

## 完了条件

- 上記確認 pass・**`reviewer` 採用**。実機目視は不要。

## 完了記録（2026-09-17）

- メインが直接追記（2 行・テストのみ）。`test_pane_width_rules` 31 OK（メイン実測）。
- `reviewer` = 完了可（ケースは §3-5 ② と実装に一致。参考: 分岐としては既存ケースと同じ経路・境界の明示として妥当）。
