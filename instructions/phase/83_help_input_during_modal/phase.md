# phase.md

## フェーズ名

ダイアログを開いている間にヘルプの絞り込み欄へ入力できない（help_input_during_modal）

## フェーズの目的

ダイアログ（モーダル）を開いている間にヘルプを開くと、ヘルプの絞り込み欄にカーソルが入らない（2026-11-17・Mac の目視で報告）。
原因を実測で確かめてから、直し方（idea の案 A / B / C ほか）をユーザーが決める。
**対象は presentation の見込み（`keyseq/presentation/help/`・`modal.py`）・JSON スキーマ不変**。

- 起票元: [idea_60](../../backlog/idea_60_help_input_during_modal.md)（2026-11-17・phase 75 task_11d の Mac 目視）。
- 主入力（暫定仕様）: [63_help_follows_front_dialog.md](../../history/63_help_follows_front_dialog.md)（2026-11-26 起票・task_02 の目視の別件 = ヘルプを開いたあとに別のダイアログを開くとヘルプが操作できない・案 E）。task_01〜02 は直接改訂モードで行い、正本 §4.6 の macOS の例外は task_01 で改訂済み。以降は暫定 63 が正（フェーズ末に昇格）。
- モード: **直接改訂モード → 暫定仕様先行モード**（2026-11-26 ユーザー判断で切り替え）。番号対応: phase 83 / 暫定 63 / decisions 83。
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

- task_01（完了・2026-11-26）: 再現と原因の実測（Mac・Windows は手順を渡してユーザー）。素の tkinter の最小構成（grab を持つ窓 + その子の Toplevel / App が親の Toplevel）と実機の両方で、
  「?」で開いたヘルプ・メニューから開いたヘルプのそれぞれで絞り込み欄をクリックして入力できるかを確かめ、候補 ①〜③ を切り分ける。
  原因と直し方の案（案 A / B / C ほか・仕様変更の要否）を出してユーザーが選ぶ。コード変更なし（計測用の一時スクリプトは scratchpad）
- task_02（完了・2026-11-26）: macOS で「?」から開いたヘルプへの grab の受け渡し（案 D・正本 §4.6 の macOS の例外・2026-11-26 改訂）。最初に transient なしで成り立つかを素の tkinter で確かめる。実装 = 既定の実装エージェント・tests / tests_ui のテスト・標準検証・Mac / Windows の目視（ユーザー）
- task_03（完了・2026-11-27）: 暫定 63 の前提の実測（A0・メイン・コード変更なし）。素の tkinter で、①ダイアログが破棄されたあと `after_idle` で作り直せて状態が保たれる ②`lower(持ち主)` で新しいヘルプがダイアログのすぐ下に置ける を Mac で確かめ、Windows はユーザーへ手順を渡す。効かなければ止めて相談する
- task_04（完了・2026-11-27）: modal.py の口と grab の持ち主の解決（暫定 63 §3.2・§5）= `set_modal_front_listener`・「grab の持ち主がヘルプならその親」の解決関数と、`grab_modal` の前の持ち主・最小化の預かり・`choice_dialog._grab_holder` での使用・カーソルグリッドの編集窓の対象外の印。テスト
- task_05（完了・2026-11-27）: ヘルプの付け替え（暫定 63 §3・§4・§5）= 持ち主の選び直し・開く / 閉じるときの作り直し・状態の控えと復元・窓の消え方の 4 区分・初期フォーカスの抑止・本文の保持・`install_grab_handoff` の掛け直し・メニューの `open` と「?」の扱い。テスト（期待値の変わる既存テストを列挙）
- task_06（完了・2026-11-28）: 統合確認と実機目視（verifier・deep-reviewer + codex-reviewer・Mac / Windows の目視 = 暫定 63 §7 A1〜A14・閉じるときの一瞬の消え方の許容の判断）
- task_06a（完了・2026-11-27）: task_06 の統合レビューの採用分の修正（暫定 63 v0.6・付け替えのあとのフォーカスの判定・下に置くのは付け替えのときだけ・予約し直しの条件・控える時点・Tk の対策は Mac だけ・App の最小化の間は待つ・テスト 3 件の前提）・2026-11-27 追加
- task_07a（完了・2026-11-28）: 完了判定前レビューのコードの採用分（付け替えのフォーカスの判定を前面の窓が確かに自分のときだけに・初回の Welcome のヘルプの deiconify）・2026-11-28 追加
- task_07（最終タスク・完了・2026-11-28）: 正本反映と記録（暫定 63 の正本への昇格と凍結〔`features.md` §4.6「ヘルプの窓」「モーダルダイアログの作法」・`key_input.md`〕・`codebase_map.md`・`decisions_archive/83`・current.md の完了記載・`instructions/history/README.md`・idea_60 の行を完了にして `INDEX_done.md` へ移動・目視用の一時スクリプト `spike/` の削除・`/refactor_check`）

## レビュー方針

- 共通観点は `.claude/rules/review.md`。各タスクは `reviewer`、フェーズ完了判定前は `deep-reviewer` + Codex 敵対的レビュー
- 固有の観点: モーダルの意味（ダイアログの外の App を操作できない）を崩していないか /
  ヘルプの絞り込み欄のフック停止（`key_input.md`）とダイアログ側の停止の入れ子が崩れないか /
  ヘルプの単一性・前面維持・親の破棄で閉じる挙動（`test_dialog_help_buttons.py`）を変えていないか /
  ヘルプを transient にする場合は phase 80 の深さ 3 以上の扱いに入ることを確かめたか / Mac と Windows の差を backend の契約で吸収しているか
