# task_06_spec_promotion_and_close

## 目的

phase 28 の設計（暫定仕様 22 v0.6）を**正本へ昇格**し、暫定仕様を凍結してフェーズを閉じる。
昇格先は暫定仕様 §10 が正（条項の文言は §4）。**文書作業のみ**で、実装・テストは変更しない
（`.claude/rules/agent_selection.md`「フェーズ末の正本反映タスクはメインセッションが直接行う」）。

レイヤ制約: **コード差分ゼロ**。`keyseq/` ・ `tests/` ・ `tests_ui/` を一切変更しない。

## 対象範囲（文書のみ）

### 1. instructions/common/spec_detail/features.md —「モーダルダイアログの作法」へ 3 条項

`#### モーダルダイアログの作法`（`:171`〜`:212`）へ暫定仕様 §4 の **3 条項**を追記する
（§4 冒頭の「2 条項」は v0.5 の §3.6 追加前の表記の残りで、§10 の「3 条項」が正）:

1. **開いた時点でキーボードフォーカスをダイアログ内へ移す**（定めた入力先があればそこへ・無ければ
   ダイアログ自身へ。**窓の前面化・フォーカス強制は行わない**）
2. **Escape でも閉じられる**（× と同じ扱い＝保存せず閉じる。フック停止の解除は `key_input.md` §7.2 のとおり
   閉じ方によらず 1 回）
3. **Esc に別用途がある状態（記録中・取得中など）ではその用途を優先し閉じない**
   （**ハンドラはダイアログにつき 1 つ・状態で分岐**）

- 位置 = 冒頭条項「表示されている間は閉じるまでモーダル」（`:172-173`）の**直後**
  （開く時点 → 閉じ方 → ネスト → 最小化 → 後始末 の順になるように）。
- **フォーカスの復帰（閉じた後・最小化復帰後）は規定しない**旨を 1 行残す
  （最小化の条項の「モーダル性は戻る」をフォーカスまで含むと読ませないため。
  [idea_34](../../backlog/idea_34_focus_restore_after_minimize.md) へリンク）。
- 既存の条項・見出しは変更しない。

### 2. instructions/common/codebase_map.md — `modal.py` 節（`:303`〜）

- 署名を `grab_modal(window, parent=None, *, focus=None)` へ更新し、**フォーカス責務**を追記
  （`focus` 省略時は窓自身 / `grab_set()` の直後に `_apply_initial_focus` で `focus_set` /
  **`focus_force` / `lift` は呼ばない** / **二重呼び出し・預かり中の窓では要求を出し直さない**）。
- 「**production の 13 箇所はすべて渡している**」→ **15 箇所**へ訂正（暫定仕様 §1・§2.1-5）。
- **Escape の結線**（群 A 4 経路は単一ハンドラ + 状態分岐 / 群 C 5 経路の結線先 = `io_dialogs.py` のみ
  `on_cancel`・他は `destroy`）を 1〜2 行。
- テスト側の固定点を 1 行: `tests_ui/test_dialog_initial_focus.py`（初期フォーカス）/
  `tests_ui/escape_delivery.py` の `send_escape`（**フォーカスを確保してから送る**・deadline 方式。
  暫定仕様 §6 / §6.1）。
- 記述は実装の実体（`keyseq/presentation/modal.py:65-105`）で裏取りしてから書く。

### 3. instructions/history/22_dialog_keyboard_focus.md — 凍結

ヘッダのブロック引用を凍結表記へ置き換える（手本 = `instructions/history/21_keymap_set_load_history.md:1-10`）:

- 状態 = **凍結（2026-09-23・正本反映済）**。正本が最新。本書は経緯記録として凍結。
- 昇格先 = `features.md` §4.6「モーダルダイアログの作法」/ `codebase_map.md` の `modal.py` 節。
- 分離先 = idea_33（`after(0)` のフック再開 family）/ idea_34（最小化復帰後のフォーカス）。
- **本書の条項を実装の根拠に引かない**（正本が正）。v0.1〜v0.6 の履歴行は残し、本文は書き換えない。

### 4. .claude_data/state/decisions_archive/28_dialog_keyboard_focus.md（新規）

`decisions.md` の phase 28 節（`:550`〜末尾）と暫定仕様 §2.1 / §2.2 の確定事項を集約する。
構成は `decisions_archive/27_keymap_set_load_history.md` に合わせ **80〜120 行程度**。少なくとも次を落とさない:

- 実装方式 = **明示引数**（推測型 `focus_lastfor()` / `after_idle` は**実測で反証**・その理由）
- 群分け（A=6 / A'=1 / B=3 / C=5 = 15 箇所）と、群 C の挙動変化の受容
- idea_18 の根 = **配送の遅さではなくフォーカス不在**（「待つ」案 B では直らない実測）→ `send_escape`
- **v0.5 のスコープ拡大**（正本 Escape 条項と群 A の矛盾 → 群 A へも Escape・単一ハンドラ + 状態分岐。
  Tk の bind 解決順の実測）
- task_05 の指摘 11 件の判定（`decisions.md:550` 以降）と **§8-7 を Escape family に限定**した判断・
  idea_33 分離（A/B 実測で phase 28 由来でないことを確認）/ M2 = task_05d
- 実機目視の結果（A / A2 / C① OK・C② 再現 → idea_34）

移設後、`decisions.md` 本体から phase 28 節の本文を削除し、「アーカイブ索引」へ 1 行
（`| 28_dialog_keyboard_focus | [...](decisions_archive/28_dialog_keyboard_focus.md) | <概要> |`。既存行の書式に合わせる）。

### 5. instructions/phase/current.md — 完了記載と次採番

- 「現在の参照先」の phase 28 項を**完了**へ書き換え、**アクティブなフェーズが無い**状態にする。
- 「直近の一連の作業が扱っている領域」を **phase 28** へ差し替える（正本の該当節 / 実装ファイル /
  テスト / 要点 / 残件 = idea_33・idea_34 / `decisions_archive/28` へのリンク）。phase 27 項は 1 行へ縮める。
- 「次採番」節 = **phase 29 / 暫定 23 / decisions 29** を明記し、暫定 22 を**凍結**へ更新。

### 6. instructions/backlog/ — idea_26・idea_18 を完了へ

`INDEX.md` の idea_18 / idea_26 行を `**完了**（phase 28 フェーズ 2026-09-23・正本反映済 → 参照リンク）`
にした上で `INDEX_done.md` へ**移動**する（手本 = `INDEX_done.md` の idea_19 行）。

### 7. /refactor_check の実行

`.claude/commands/refactor_check.md` に従う。**PHASE_BASE = `60372bf`**（phase 28 起票コミット）。
**メトリクス収集（手順 1〜2・M1〜M6）は `verifier` へ委任**し、判定（手順 3 以降）と提案書起票の要否は
メインが行う。判定結果を完了報告と `decisions_archive/28` 末尾に記載する（提案書起票はユーザー承認後）。

## 設計メモ / 制約

- **正本へ書くのは確定した規範のみ**。反証済みの推測型・レビュー経緯は正本へ持ち込まない
  （暫定仕様と `decisions_archive/28` に残る）。
- **実装に合わせて仕様を緩めない**。正本へ書くと実装と食い違う箇所を見つけたら、書き換えずに
  **作業を止めてユーザーへ報告**する（`.claude/rules/spec_change_workflow.md` の検出基準 A/D）。
- 既存節の節番号・見出しは変更しない。
- 別実装同期は**なし**（暫定仕様 §10）。

## 読むファイル

1. `instructions/history/22_dialog_keyboard_focus.md`（**冒頭ヘッダ / §1 / §2.1 / §2.2 / §3.1 / §3.5 / §3.6 / §4 / §6.1 / §10 / §11**）
2. `instructions/common/spec_detail/features.md:171-212`（モーダルダイアログの作法）
3. `instructions/common/codebase_map.md:296-331`（`modal.py` 節）
4. `keyseq/presentation/modal.py:65-105`（裏取り）
5. `instructions/history/21_keymap_set_load_history.md:1-12`（凍結ヘッダの手本）
6. `.claude_data/state/decisions_archive/27_keymap_set_load_history.md`（アーカイブの手本）
7. `.claude_data/state/decisions.md`（「アーカイブ索引」節 + `:550`〜末尾）
8. `instructions/phase/current.md`（「現在の参照先」「次採番」節）
9. `instructions/backlog/INDEX.md` の idea_18 / idea_26 行・`INDEX_done.md` の idea_19 行

## 含まない

- **コードとテストの変更**（`keyseq/` ・ `tests/` ・ `tests_ui/`）。差分ゼロで完了すること。
- idea_33（フック再開の flaky）/ idea_34（最小化復帰後のフォーカス）の着手。**別フェーズ**。
- 暫定仕様 §11 のスコープ外項目（同型スケルトンの共通化 / 初期フォーカス位置の UX 見直し / idea_32）。
- `/refactor_check` で挙がった改善の**実施**（提案書の起票要否の判断まで）。
- `handoff.md` の再生成（`/save_handoff` で別途行う）。

## 確認

- **コード差分ゼロ**: `git diff --stat 968f129 -- keyseq tests tests_ui` が空であること。
- 標準検証 4 本が**前回と同値**（`verifier` へ委任。compile clean / `tests` 556 ran OK〔skip 7〕/
  `tests_ui` 507 ran OK / smoke `SMOKE OK`）。文書変更なので値が動いたら異常。
- **正本の反映漏れチェック**: 暫定仕様 §4 の 3 条項と §10 の各項目が `features.md` /
  `codebase_map.md` に現れていることを逐一照合する。
- **リンクの実在確認**: 追記した相対リンク（`decisions_archive/28` / idea_33 / idea_34 / 正本の節参照）が解決すること。
- `features.md` の既存条項が無改変であること（`git diff` で追記のみ）。
- `/refactor_check` の判定結果（要否と根拠）が出ていること。

## 完了条件

- 上記「確認」がすべて pass。
- **フェーズ完了判定のレビューを 2 系統で実施**（`.claude/rules/agent_selection.md` の表）:
  `deep-reviewer`（正本の記述と実装の整合・条項の欠落と矛盾）+ `codex-adversarial-reviewer`（敵対的レビュー）。
  **指摘の採否はユーザー確認を経る**（task 単位の `reviewer` 採用はこの 2 系統で代える。フェーズ完了判定前の運用形）。
- `.claude/rules/task_execution.md`「フェーズ完了時」のチェックリストを満たす
  （正本昇格 + 暫定仕様の凍結 / `decisions_archive/28` / `current.md` の完了記載と次採番 /
  idea_26・idea_18 の INDEX_done 移動 / `/refactor_check` の実行と結果の記載）。
- 実機目視は**不要**（文書タスク。task_05 で実施済み）。

## 完了記録（2026-09-23）

- **状態 = 完了**（文書のみ・コード差分ゼロ）。**phase 28 の完了宣言は task_07 の後**（`/refactor_check` = 推奨 →
  ユーザー選択 (a) で task_07 を追加したため。`current.md` の「アクティブなフェーズ」は task_07 完了時に「なし」へ戻す）。
- 反映: `features.md` §4.6（3 条項 + フォーカスの戻り先を規定しない旨。v0.7 の文言）/ `codebase_map.md` の `modal.py` 節 /
  暫定仕様 22 を **v0.7 で凍結**（途中で L3 のため一度解除 → task_05e → 再凍結）/ `decisions_archive/28` 新設 + `decisions.md` 索引 /
  `current.md` / idea_18・idea_26 を `INDEX_done.md` へ / idea_33 補記 / 提案書 11 起票。
- 完了判定前レビュー: `deep-reviewer`（条件付き可）+ `codex-adversarial-reviewer`（needs-attention）→ 指摘の採否はユーザー確定
  （`decisions_archive/28`「フェーズ完了判定レビューの採否」）。v0.7 改訂は `codex-adversarial-reviewer` を通してからユーザー確定。
- 標準検証（`verifier`・HEAD `5d83e49`）: compile clean / `tests` 556 OK（skipped 7）/ `tests_ui` 509 OK / smoke OK。
- `/refactor_check`: **推奨**（M3 = Esc の別用途つき閉じ処理の 3 重複）→ [提案書 11](../../../modified_proposal/11_refactor_dialog_escape_secondary_use.md)・task_07。
