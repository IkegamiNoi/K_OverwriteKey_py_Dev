# task_05_spec_promotion

## 目的

phase 15 の確定内容を**正本へ昇格**し、フェーズを完了させる。暫定仕様
[13](../../../history/13_dialog_teardown_on_close.md)（v0.4）の **§8（正本反映）**と
`.claude/rules/task_execution.md`「フェーズ完了時」のチェックリストが根拠。

**文書作業のみ。`keyseq/` と `tests_ui/` のコードは変更しない**
（実装は task_01〜03 で完了・task_04 で検証済）。

## 対象範囲（文書のみ）

### 1. 正本への昇格（3 ファイル）

**(a) `instructions/common/spec_detail/key_input.md` §7.2「フックの停止制御」**

現在の 2 項目に**条項を足す**（既存の文言・節番号は変えない）。加える内容は 2 点:

- **停止要求は閉じ方によらず解除される**（OK / キャンセル / Escape / × / プログラムからの破棄）。
- **停止要求が残っている間は入力を通さない**（ユーザー確定 2026-09-13。
  根拠 = `keyseq/application/input_router.py:70` がカウンタで入力を捨てている。
  文言が無いと「フックを外すだけ」の実装でも仕様を満たしてしまい、
  **取りこぼし入力への防御が将来無言で削られ得る**）。

**実装詳細（メソッド名・`after(0)`・イベント名）は書かない**。

**(b) `instructions/common/spec_detail/features.md` §4.6「モーダルダイアログの作法」（`:90-99`）**

**後始末の作法**を箇条書きで足す（phase 14 の昇格と同じ流儀＝**振る舞いだけを書く**）:

- **状態の後始末（アプリ側の状態を戻すもの）は、閉じ方によらず必ず走る**。
- **ウィジェットに触る後始末（値の収集・再設定）は、閉じる操作の側で行う**
  （破棄の時点では**子ウィジェットが既に無い**ため）。

**メソッド名・クラス名・イベント名は書かない**。

**(c) `instructions/common/codebase_map.md` `HookController` の行（`:246`）**

責務の記述へ「**ウィンドウを渡すと破棄時に自動で解除する**」旨を足す。
`modal.py` の記述（`:248-252`）と**同じ粒度**に揃える。

### 2. 暫定仕様 13 の凍結

`instructions/history/13_dialog_teardown_on_close.md` の冒頭に**凍結の 1 行**を足す
（先例 = 凍結済みの 04〜12）。**本文の条項は書き換えない**（経緯として保存する）。

### 3. 判断履歴の集約

- `.claude_data/state/decisions_archive/15_dialog_teardown_on_close.md` を新規作成する。
  含める内容 = **確定した設計判断**（案 B / 登録を `HookController` へ / `after(0)` 遅延 /
  終了ガード / 空 override 削除）+ **task_04 の指摘処理 7 件の判定** +
  **受容した残存リスク** + **分離した項目**。先例は `decisions_archive/14_*.md`。
- `.claude_data/state/decisions.md` の「アーカイブ索引」へ **1 行**追加する。

### 4. `instructions/phase/current.md` の完了記載

- 「現在の参照先」を**完了扱い**へ差し替える（**完了フェーズはリンクのみ・要約は書かない**）。
- 「**直近の一連の作業が扱っている領域**」を**更新する**（現在は phase 14 の grab 復元が主語）。
  **残件リストから idea_16 を落とし**、残る候補（スケルトン共通化 / 静的検査の発見ベース化 /
  idea_17 / stdlib ダイアログ）を維持する。
- 「次採番」節 = **次フェーズは `16_<topic>`**。**暫定仕様 13 を「凍結」表記へ**変更し、
  暫定仕様の次採番が **`14_<topic>`** のままであることを確認する。

### 5. 起票元 idea のクローズ

`instructions/backlog/INDEX.md` の **idea_16** の行を完了 / クローズ状態に更新し、
`instructions/backlog/INDEX_done.md` へ**移動**する（`task_execution.md`「フェーズ完了時」）。

### 6. `/refactor_check` の実行

`.claude/commands/refactor_check.md` に従う。**メトリクス収集（手順 1〜2・M1〜M6）は `verifier`**、
**判定（手順 3 以降）と提案書の起票はメイン**。判定結果を完了報告に含める。

### 7. フェーズ完了判定前のレビュー

`.claude/rules/agent_selection.md` の表に従い **`deep-reviewer` + `codex-adversarial-reviewer`**。

- **`codex-adversarial-reviewer` には focus text を渡す**
  （**task_04 の `codex-reviewer` は focus text を受け付けず観点が渡らなかった**。ここで回収する）。
- 対象 = **phase 15 の全差分 + 本タスクの正本昇格文**。
- 観点 = 昇格文が**実装と一致しているか** / **実装詳細を書いていないか** /
  **既存の正本条項と矛盾しないか** / phase.md「レビュー方針」の固有観点。

### 設計メモ / 制約

- **正本の節番号・見出しは変更しない**（既存参照が壊れる）。
- **暫定仕様の条項を正本へ丸写ししない**。正本は**振る舞いの規定**であり、
  実装手段（`<Destroy>` / `after(0)` / メソッド名）は書かない。
- **`keyseq/` と `tests_ui/` を変更しない**。必要が生じたら**別タスクへ切り出す**。
- 昇格文は**短く**する（`.claude/rules/output_style.md`）。

## 含まない

- コード変更全般（実装・テストとも。必要なら別タスク）。
- **スケルトン共通化 / 静的検査の発見ベース化 / idea_17 /
  `key_capture.py`・`keyboard_window.py`**（暫定仕様 §9・候補送りのまま）。
- **ステータスバーの 4 秒タイマー由来の stderr 4 件**（phase 15 以前からの既存事象。
  `integration_result.md` に記録済み・対応は行わない）。
- `/refactor_check` が「推奨」と判定した場合の**リファクタ実施**（提案書の起票までがここ。
  実施はユーザー承認後）。

## 確認

1. **正本 3 ファイルの更新**が済み、**節番号・既存文言が変わっていない**
   （`git diff` で追加行のみであることを確認）。
2. **暫定仕様 13 に凍結表記**がある。
3. `decisions_archive/15_dialog_teardown_on_close.md` が存在し、`decisions.md` の索引に 1 行ある。
4. `current.md` が**完了記載**になっている（次採番 = phase 16・「直近の領域」更新済）。
5. `backlog/INDEX.md` に idea_16 の行が**無く**、`INDEX_done.md` に**ある**。
6. **`/refactor_check` を実行し判定を得た**（不要 / 推奨のいずれか。推奨なら提案書を起票）。
7. **`deep-reviewer` + `codex-adversarial-reviewer` の両方**が完了し、指摘が処理済み。
8. 退行が無いこと（`verifier`）: compile clean / `tests` 417 pass・skip 7 /
   `tests_ui` 321 pass / `smoke_app` pass。**文書のみの変更なので数値は task_04 と同じはず**。
9. `git diff --stat` に `keyseq/` と `tests_ui/` が**現れない**。

## 完了条件

- 上記確認 1〜9 をすべて満たす。
- **`deep-reviewer` 採用**（フェーズ完了判定のためレビューは `reviewer` ではなく `deep-reviewer`）。
- **実機目視は不要**（task_04 で実施済・本タスクは文書のみ）。
- 完了報告に **`/refactor_check` の判定結果**を含める。
