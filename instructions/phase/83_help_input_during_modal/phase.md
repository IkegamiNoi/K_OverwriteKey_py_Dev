# phase.md

## フェーズ名

ダイアログを開いている間にヘルプの絞り込み欄へ入力できない（help_input_during_modal）

## フェーズの目的

ダイアログ（モーダル）を開いている間にヘルプを開くと、ヘルプの絞り込み欄にカーソルが入らない（2026-11-17・Mac の目視で報告）。
原因を実測で確かめてから、直し方（idea の案 A / B / C ほか）をユーザーが決める。
**対象は presentation の見込み（`keyseq/presentation/help/`・`modal.py`）・JSON スキーマ不変**。

- 起票元: [idea_60](../../backlog/idea_60_help_input_during_modal.md)（2026-11-17・phase 75 task_11d の Mac 目視）。
- 主入力（暫定仕様）: なし（直接改訂モード）。
- モード: **直接改訂モード**（task_01 は実測のみ）。番号対応: phase 83 / 暫定なし / decisions 83。
  task_01 で決める方針が `features.md` §4.6「ヘルプの窓」「モーダルダイアログの作法」や `key_input.md` のヘルプの節を
  変える場合（案 A / B）は、止めてユーザーへ報告し、`.claude/rules/spec_change_workflow.md` に従ってモードを選び直す。

## 確定（ユーザー 2026-11-26）

- idea_60 に着手する（phase 83）。方針は決めずに、まず原因を実測する（task_01）。
- task_01 の結論（2026-11-26・ユーザー判断）: 原因 = macOS の Tk 9.1 のローカル grab（grab の窓以外へクリックが届かない）。Windows は問題なし。直し方 = **案 D**（Mac だけ、ヘルプが前面の間は grab をヘルプへ・前面でなくなったらダイアログへ）。正本 `features.md` §4.6 に macOS の例外を追加済み（`/spec_update`・直接改訂モードのまま）
- 起票時の調査（2026-11-26・直読みで確認済み）: ダイアログの「?」から開くヘルプは、すでにダイアログを親（Tk の master）として作られる
  （`help/help_button.py:24` → `help/help_window_controller.py:59-66`）。transient にはせず、`grab_modal` も通さない。
  メニューから開くヘルプは App が親（`views/menu_bar.py:81-82` → `help/help_window_controller.py:34-36`）。idea の前提「ヘルプは grab の外の窓」は「?」の経路には当てはまらない可能性がある。

## スコープ

### 含む

- 再現と原因の切り分け（Mac / Windows）。次の候補を区別する
  - ① `modal.py` の `_restore_modal_focus` 等が grab の保持者（ダイアログ）へフォーカスを戻す
  - ② macOS で transient でない子の窓がキー入力を受ける窓にならない（OS の差）
  - ③ 報告の場面がメニュー経由のヘルプ（App が親で grab の外）だった
- 結果に基づく直し方の決定（ユーザー）と、以降のタスクの起票
- 直したあとの tests_ui のテストと Mac / Windows の目視（ユーザー）

### 含まない（後送り）

- ヘルプの本文・絞り込みの仕様
- モーダルの grab の作り（ネスト・最小化の預かり・phase 80 の transient の付け外し）を、ヘルプと関係しない範囲で変えること

## このフェーズで読むファイル

1. [idea_60](../../backlog/idea_60_help_input_during_modal.md)
2. `keyseq/presentation/help/help_button.py` / `help_window_controller.py` / `help_window.py`
3. `keyseq/presentation/modal.py`（`grab_modal`・`_restore_modal_focus`・`_return_grab`）
4. `keyseq/presentation/views/menu_bar.py`（メニューからヘルプを開く経路）
5. `instructions/common/spec_detail/features.md` §4.6「ヘルプの窓」（1049 行〜）・「モーダルダイアログの作法」（1138 行〜）
6. `instructions/common/spec_detail/key_input.md` のヘルプの絞り込み欄の項（28〜29 行）
7. `instructions/common/codebase_map.md` の help / modal.py の節
8. `tests_ui/test_dialog_help_buttons.py` / `test_help_window.py` / `test_modal_grab.py` / `test_nested_modal_grab.py`
9. 必要時のみ: `.claude_data/state/decisions_archive/80_win_d_restore_blank_dialog.md`（transient の深さ 3 以上の扱い）

## タスク

- task_01: 再現と原因の実測（Mac・Windows は手順を渡してユーザー）。素の tkinter の最小構成（grab を持つ窓 + その子の Toplevel / App が親の Toplevel）と実機の両方で、
  「?」で開いたヘルプ・メニューから開いたヘルプのそれぞれで絞り込み欄をクリックして入力できるかを確かめ、候補 ①〜③ を切り分ける。
  原因と直し方の案（案 A / B / C ほか・仕様変更の要否）を出してユーザーが選ぶ。コード変更なし（計測用の一時スクリプトは scratchpad）
- task_02: macOS で「?」から開いたヘルプへの grab の受け渡し（案 D・正本 §4.6 の macOS の例外・2026-11-26 改訂）。最初に transient なしで成り立つかを素の tkinter で確かめる。実装 = 既定の実装エージェント・tests / tests_ui のテスト・標準検証・Mac / Windows の目視（ユーザー）
- task_03（最終タスク）: 記録（正本の追記が要ればユーザー承認のうえ `features.md`・`key_input.md`・`codebase_map.md`・`decisions_archive/83`・
  current.md の完了記載・`instructions/backlog/INDEX.md` の idea_60 の行を完了にして `INDEX_done.md` へ移動・`/refactor_check`）。
  案 C（受け入れ）ならコードは変えず、ヘルプ・ツールチップの文言（`ja.json` / `en.json`・`ui_terms.md` に従う）と記録だけになる

## レビュー方針

- 共通観点は `.claude/rules/review.md`。各タスクは `reviewer`、フェーズ完了判定前は `deep-reviewer` + Codex 敵対的レビュー
- 固有の観点: モーダルの意味（ダイアログの外の App を操作できない）を崩していないか /
  ヘルプの絞り込み欄のフック停止（`key_input.md`）とダイアログ側の停止の入れ子が崩れないか /
  ヘルプの単一性・前面維持・親の破棄で閉じる挙動（`test_dialog_help_buttons.py`）を変えていないか /
  ヘルプを transient にする場合は phase 80 の深さ 3 以上の扱いに入ることを確かめたか / Mac と Windows の差を backend の契約で吸収しているか
