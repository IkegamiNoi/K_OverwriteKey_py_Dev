# task_07_spec_promotion

## 目的

phase 76（カウンター機能の拡張）の最終タスク。暫定 58（v1.1）の確定内容を正本 `instructions/common/spec_detail/` へ昇格させ、暫定 58 を凍結する。あわせてフェーズ完了時のチェックリスト（`.claude/rules/task_execution.md`「フェーズ完了時」）を実施する。

- 文書作業のみ（メインが行う・`agent_selection.md`「フェーズ末の正本反映タスク」）。コード・JSON スキーマ・ヘルプ本文は変えない。
- 正本への転記はユーザー確定済みの内容（暫定 58 v1.0 / v1.1）と、実装で確定した細部（下の R6）に限る。暫定 58 に無い仕様を正本で新たに決めない。

## 対象範囲

### 正本の昇格（暫定 58 §9 の列挙に従う）

- `data_schema.md`（INDEX と子ファイル）: §5.2 の最上位キーと §5.3 付近への `counter_starts`（§3.3 の正規化の順序）・§5.11.1 の種別の表と種別不正の文言・§5.11.5 の旧ビルドの記述（§3.5）・§5.11.6 の `counter_inc` の `amount` と `counter_reset` の意味（開始値へ戻す）・`counter_text`（§3.4）・§5.11.8 の通知の値・§3.6 のまたがる保存（受容）。
- `features.md`: §4.2 冒頭の通常アクションの列挙と状態の「カウンター」（開始値・実効値 §4.1）・§4.2.2 の保留の内容 `(op, name, amount)` と L65 の `(=値)` を §5.3 の保留の反映（v1.1）へ改訂・§4.2.6 の戻すの説明（初めて入った名前を消す・§4.2〜§4.3）・§4.2.8 の「送った」の列挙・§4.2.9 の呼び出し先の行の表（`counter_text`・表示枠の値は最上段の保留を反映）・§4.6 の一覧の表示形式（§5.3）と編集ダイアログ（§5.2）。
- `ui_terms.md`: 種類の表示名（「カウンター」「カウンターリセット」「カウンターの値を入力」・ja / en の実装値）。
- R6（task_06 の判定）: 描き直しの契機は `refresh_actions` 経由・`counter_text` の送信失敗の通知だけラベル付き、を実装どおりに §4.6 / §5.11.8 の該当箇所へ書く。

### 凍結

- `instructions/history/58_counter_expansion.md` の冒頭の状態行を「凍結・v1.1」に書き換え、昇格先の一覧と日付を添える。本文の条項は変えない。
- `instructions/phase/current.md` の暫定仕様の一覧（「58 = カウンター機能の拡張〔v1.0…〕」）を凍結済みに直す。

### 地図

- `instructions/common/codebase_map.md`: phase 76 で増えた構成（`counter_values.py`・`preview_counter_values`・`track_counter_additions`・`counter_text` の分岐・`counter_starts` の同期経路）が載っていること（足りなければ足す）。

### フェーズ完了の記録

- `.claude_data/state/decisions_archive/76_counter_expansion.md` を作り、`decisions.md` の phase 76 の判断（task_06 の判断 A と、本フェーズ中の R1〜R9 の採否）を集約する。`decisions.md` はアーカイブ索引に 1 行を足し、本文から phase 76 の節を外す。
- `instructions/phase/current.md`: phase 76 を完了に・アクティブなフェーズ = なし・次採番（phase 77 / 暫定 59 / decisions 77 / 提案書 29 / idea 67）。
- `instructions/phase/76_counter_expansion/phase.md`: task_07 の行とフェーズの状態を完了に。
- 起票元 idea: なし（ユーザー要望）。`instructions/backlog/` の更新は不要（idea_37 は後送りのまま）。
- `/refactor_check`（メトリクス収集は verifier・判定と提案書の起票はメイン）。候補: executor の `counter_text` 分岐の `_labeled` 動的キーと `execute` 内 28 行・`counter_text` の書式の重複・import の並び。

## 読むファイル

1. 本書・`instructions/history/58_counter_expansion.md`（全体。昇格の元）
2. 昇格先の `spec_detail/` の各ファイルの該当節（§9 の行番号付近・`grep` で節を探す）
3. `.claude_data/state/decisions.md` の phase 76 の節・`decisions_archive/75_mac_support.md`（アーカイブの形の手本）
4. `tasks/task_06_integration.md`（R1〜R9 の採否）
5. `.claude/commands/refactor_check.md`

## 含まない

- 暫定 58 §8 のスコープ外（条件分岐 = idea_37・値の表示欄と手での変更・`counter_text` の書式・使われない開始値の掃除・値の永続化）。
- R4（呼び出し先の `amount` 不正を呼び出しの行で報告する）は保留のまま（既存のループ・待機のエラーと同じ扱い）。
- `/refactor_check` が「要」と判定した場合の実施（提案書の起票まで。実施はユーザー承認後）。
- `__version__` の変更・push・main へのマージ（ユーザー）。

## 確認

1. 暫定 58 §9 の列挙と §7 の受け入れ条件 1〜8 について、昇格先（`spec_detail/` のファイル名と節）を対応表にして完了報告に載せる（漏れが無いこと）。
2. `grep -rn "カウンター +1\|カウンターを0に\|0 にした\|直前に実行した通常アクションの時点" instructions/common/` のヒットが、改訂後の仕様と矛盾しない（旧名・旧挙動の記述が残っていない）。
3. フェーズ完了判定のレビュー: `deep-reviewer`（本タスクの差分 + 正本整合・昇格漏れ・凍結）と `codex-adversarial-reviewer`（フェーズ全体の差分 `4129c67b..HEAD`）を併用する。
4. `/refactor_check` の判定結果を完了報告に書く。

## 完了条件

- 確認 1〜4 を満たし、**deep-reviewer 採用**（本タスクの必須レビューはフェーズ完了判定の deep-reviewer で兼ねる。reviewer は重ねない。Codex の敵対的レビューの指摘の採否はユーザー）。
- 実機目視: なし（文書のみ）。

## 追加の修正 C1（2026-11-23・フェーズ完了判定の codex 敵対的レビュー・ユーザー「推奨どおり進めて」）

正本 `features.md` §4.2.9「無視した押下の巻き戻し」（改訂済み）に実装を合わせる。application 限定・スキーマ不変。

- 欠陥: `linked_call.py:19-20` は、押下 T が初めて入れた名前を差分を引いた後にキーごと消す。T の待機中に別の押下 U が同じ名前へ書くと U の値も消え、後で U を戻すと `sequence_history.py:112` の `counters[name] -= delta` が KeyError になる。
- 修正:
  1. `application/counter_values.py` の `CounterValues` に、名前ごとの**書き込みの通し番号**（全体で単調増加する 1 つの番号を、書いた名前に記録）を持たせる。`__setitem__` で進める。`state.counters` を変えうる他の dict の操作（`update` / `setdefault` / `pop` / `__delitem__` / `clear` 等）が本番で使われていればそれも番号を進める（使われていなければ足さない）。参照は `write_serial(name) -> int | None` 等の小さなメソッド。
  2. `call_context.py` の記録（`CallContext.added_counter_names`・`SequenceRunner._run_to_end_added_counter_names`・`sequence_runner.py:413` のローカル）を、`set[str]` から「名前 → その押下が最後に書いたときの通し番号」と「他の押下が書いた印」を持つ小さな型にする（`clear()` と、消してよい名前を返すメソッドを持つ。今の `.clear()` の呼び出し箇所はそのまま使えること）。
  3. `track_counter_additions`: ロックの下で、区間の**前に**記録済みの名前の今の番号が記録と違えば「他の押下が書いた」印を付ける → 区間を実行 → 区間の**後に**、新しく入った名前と、印の無い記録済みの名前のうち区間内で書いた名前の番号を記録する。
  4. `_rollback_linked_press`: 差分を引く**前に**消してよい名前（印が無く、今の番号が記録と同じ）を決め、差分を引いた後にそれだけを消す。
  5. `sequence_history.undo_counter_deltas`: 名前が無い場合は実効値（`counter_value`）から引く（KeyError にしない）。
- テスト（`tests/test_sequence_runner_call.py` 等・既存テストの途中に差し込まない）: ① T が未使用の n を +1 して待機中に、別の押下が n へ +5 を確定 → T が無視されると n は「開始値 + 5」が残り、その押下を戻すと開始値に戻る（KeyError なし）② 他の押下が書いた後に T が同じ名前へもう一度書いても消さない ③ 他の押下が書いていなければ従来どおり消える（既存の回帰テストが通る）④ `CounterValues` の番号の単体テスト ⑤ `undo_counter_deltas` で名前が無い場合。
- 含まない: C2・C3（除外）・R4（保留）。
