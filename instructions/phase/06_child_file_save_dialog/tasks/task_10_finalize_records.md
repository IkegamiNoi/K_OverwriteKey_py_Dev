# task_10_finalize_records

## 目的

Phase β の**最終タスク（正本反映）**。暫定仕様 05（v0.7・ユーザー確定済）で確定した設計を正本
`instructions/common/spec_detail/` へ昇格し、暫定仕様を凍結する。あわせて
`.claude/rules/task_execution.md`「フェーズ完了時」のチェックリストを消化する。

レイヤ制約: **文書作業のみ**（`instructions/` ・ `.claude_data/` 配下）。**コード・テストは変更しない**
（`keyseq/` ・ `tests/` ・ `tests_ui/` に差分を出さない）。実装との乖離を見つけた場合は
`.claude/rules/spec_change_workflow.md` に従い**報告して止める**（正本を実装に合わせて緩めない）。

前提: task_01〜09・11〜18 完了 / 受入条件 1〜27 の充足は
[integration_result.md](../integration_result.md) が正 / **実機目視 R1〜R11 は全 OK（2026-08-02）**。

## 対象範囲（文書のみ）

### 1. 正本 `instructions/common/spec_detail/data_schema.md` への昇格

暫定仕様 05 §12 の表に沿って追記する。**必ず明記する項目**:

| # | 内容 | 出所 |
|---|---|---|
| 1 | 子JSON の参照元キー `_parent_refs`（直接の上位の集合・後方互換＝無ければ「未知」扱い） | §4 |
| 2 | trigger_set の `source_path` の扱いと**内部キー `INTERNAL_TRIGGER_SET_SOURCE_PATH`**（runtime 内部キーである旨） | §7・申し送り③ |
| 3 | trigger_set の既定命名（**keymap_set の stem 基準**）と、§5.4 の「trigger_set は全セット共通」記述の**更新** | §6 |
| 4 | §5.6 のフォールバック名の**経路差**（一括 = `default` / 個別 = `trigger_set.json`） | §6 |
| 5 | 保存計画（子ごとに 保存 / 別名保存 / 保存しない）と依存関係・失敗時の旧索引維持 | §8 |
| 6 | **`SHARE_NEW`** と**非 dirty な子の既定規則**＝「**保存先に実体があれば SKIP・無ければ SAVE**」（正本に記述が無い） | v0.6 の機構解説 |
| 7 | **SKIP した子の索引規則**（旧パスを維持）と **SKIP 子の dirty 保持** | §8・v0.4-E |
| 8 | 依存確認ダイアログの**提示条件と既定ボタン**（単独 / 新規作成は確認なし自動保存・それ以外は 4 択・既定＝別名保存） | v0.4-D/E |
| 9 | 個別「トリガー一覧を保存」の**保存計画化**（v0.5-K）と §8 の関係 | v0.5-K |
| 10 | **変更なし保存でも親・起動設定・未作成の子は書かれる**（完了ダイアログも出る） | v0.3・§3 末尾 |

**版別の追加分**（§12 の該当行をすべて消化する）:

- **v0.3**: A（再解決後に一覧を再表示しない）/ A2（再計算先が既存ファイルで単独以外なら行単位の上書き確認）/
  B（パス同一性は canonical identity。JSON 保存表記は §4 のまま）/ C（一覧ダイアログのレイアウト要件）
- **v0.4**: D/E（提示条件と 4 択・**deferred index 例外**と上位の dirty 化）/ F（A2 は維持）/
  G（既定保存先は既存ファイルを避けない）/ **I（新規の子が既存ファイルへ当たるときの既定は別名保存。
  `keymap` / `sequence` 限定・元判定が「単独」「共有中」のときだけ**）/ H（`data` 置換時の trigger_set 状態リセット）
- **v0.5**: J（個別保存の書き込み先は config_root から解決・**stored と resolved の分離**）/ K / L・M / N（上位の dirty 化）
- **v0.6**: O（「例を復元」は中身のある新規作成・`keymap_set_path` を引き継がない・**同名 keymap_set を選ぶと
  stem 由来 trigger_set も上書き**）/ P（未保存確認）/ Q（例の子は dirty 扱い）
- **v0.7**: R（共有状況表示は**上書きの有無が読み取れる文言**。`SHARE_SOLE` の表示は
  「この構成のみが所有・既存を上書き」。**判定名と表示文言は別物**である旨も明記）

### 2. 正本 `instructions/common/codebase_map.md` の更新

子ファイル保存ダイアログ・参照元記録・保存計画の責務分担を反映する
（**presentation が保存計画を決定・application が実行**。application に tkinter 依存を持ち込まない）。
対象クラス: `config_io/child_save_rows.py` / `child_save_dialog.py` / `child_save_plan.py` /
`keymap_set_io.py` / `controllers/dirty_state.py` / `application/config_service.py` / `application/save_plan.py`。

### 3. 暫定仕様 05 の凍結

`instructions/history/05_child_file_save_dialog.md` の状態行を**凍結済み**へ更新し、
「正本へ昇格済み・以後は正本が正」を明記する（本文の条項は書き換えない）。

### 4. フェーズ完了処理（`.claude/rules/task_execution.md`「フェーズ完了時」）

| 対象 | 内容 |
|---|---|
| `.claude_data/state/decisions_archive/06_child_file_save_dialog.md` | **新規作成**。Phase β の判断履歴（2026-07-29 〜 08-02 の 5 回分の実機目視フィードバックと v0.3〜v0.7 の改訂・敵対的レビューの採否）を集約 |
| `.claude_data/state/decisions.md` | 「アーカイブ索引」へ 1 行追加し、**本体から phase 06 の節を削除**（索引のみ残す） |
| `instructions/phase/current.md` | 完了記載へ更新・**旧フェーズの要約行は削除**・次採番（フェーズ `07_<topic>` / 暫定仕様 `08_<topic>`）を明記 |
| `instructions/backlog/INDEX.md` | **idea_05 を完了 / クローズ**にして `INDEX_done.md` へ移動 / **idea_06** の着手条件（②idea_05 の解消）を充足済みへ更新 / **idea_07** を「β 完了 = 着手可」へ更新 |
| `/refactor_check` | 実行し、判定結果を完了報告に記載（メトリクス収集 M1〜M6 は `verifier` へ委任・判定と提案書起票はメイン） |

**`/refactor_check` で必ず入力する申し送り**（session.md の resume_hints より）:
⓪ `child_save_dialog.py` が 324 行（目安 300 超）+ `_add_text_cell` の戻り値が素の dict /
① slugify 後に別々の keymap_set 名が同一 stem へ丸まる衝突（受入条件 8 の範囲外）/
② `dirty_tracker.trigger_set_imported` は読み手不在の残置状態 /
⑤ `config_service.py` が 1600 行超（分割是非をここで判定）。

## 含まない

- **コード・テストの変更**（本タスクは文書のみ。乖離を見つけたら報告して止める）
- **`/refactor_check` の判定結果に基づく実際のリファクタ実施**（提案書の起票までがフェーズ内。
  実施はユーザー承認後・別フェーズ）
- idea_07（参照元の掃除）/ idea_06（個別 JSON IO の共通化）/ idea_09（レガシー `settings/`）の**着手**
- 実機の `config/` に絶対パスで記録済みの `_parent_refs` / 起動設定の**移行処理**（申し送り④＝不要と判断済み）
- Phase γ（暫定 06）/ プリセット（暫定 07）に関する記述の追加

## 確認

1. 暫定仕様 05 §12 の表の**全行**が正本のどこへ反映されたか対応が取れている
   （§12 の各行に対し反映先ファイル + 節番号を示せる）
2. 正本の**節番号・既存見出しを変更していない**（追記と該当節の更新のみ。分割が必要なら `/spec_split`）
3. `data_schema.md` の後方互換規定（既存キー削除禁止・意味変更禁止）に反する記述を入れていない
4. コード・テストに差分が無い（`git status` で `keyseq/` ・ `tests/` ・ `tests_ui/` に変更が出ない）
5. `/refactor_check`（メトリクス収集は `verifier`）を実行し、判定結果を報告に含めた
6. `.claude/rules/task_execution.md`「フェーズ完了時」の 5 項目（昇格・凍結 / decisions_archive /
   current.md / backlog INDEX_done 移動 / refactor_check）がすべて済んでいる

## 完了条件

- 上記確認 pass・**`deep-reviewer` 採用**（フェーズ完了判定のため `reviewer` ではなく `deep-reviewer` を使う。
  `.claude/rules/agent_selection.md` のレビュー表）。あわせて `codex-adversarial-reviewer` による
  フェーズ完了判定レビューを実施する（Codex 不可時は報告のうえ Claude 側へ縮退可）。
- 実機目視は**不要**（R1〜R11 は 2026-08-02 に全 OK。本タスクは文書のみで挙動を変えない）。
