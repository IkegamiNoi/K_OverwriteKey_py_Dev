# decisions_archive / phase 48: 省略表示の出力シーケンス欄

対応表: phase 48 / 暫定 33（v0.6・凍結）/ decisions 48。起票元: ユーザー要望（2026-10-06・「省略表示に通常シーケンスの欄が欲しい」「省略表示の画面サイズを記録」「縦を短くしたときにステータスが消えないよう最低サイズ」）。
完了 2026-10-07。presentation 限定・domain / application 不変・keymap_set の JSON スキーマ不変。`config/config.json` にキー 2 つ追加（`compact_sequence_view`・`compact_window_size`・後方互換）。
正本 = `features.md` §4.6「省略表示のシーケンス欄」「省略表示のウィンドウ」「呼び出し先の表示枠」「フル表示の幅配分」の「省略表示との関係」/ `data_schema.md` §5.4 / 地図 = `codebase_map.md` の compact 系モジュールの行。

## 確定した設計判断（ユーザー）

| # | 判断 | 採らなかった案と理由 |
|---|---|---|
| 1 | 操作 = 見る + 次に実行の変更（選択の帯・↑↓ はフル表示と同じ。編集・並べ替え・範囲選択はしない） | 見るだけ = 次に実行を変えるのにフル表示へ戻る手間 / 編集まで = 幅 270 で操作が窮屈 |
| 2 | 開閉は全体で 1 つ・保存する（呼び出し先の枠のトリガーごと・保存しないとは別規則） | トリガーごと = 選び替えのたびに開閉が揺れる |
| 3 | 並び = トリガー一覧 / シーケンス欄 / 呼び出し先。開閉で窓の大きさは変えずトリガー一覧が伸び縮み | — |
| 4 | 収まらないときは 呼び出し先 → シーケンス欄の順に縮め、下の欄の最小を優先・トリガー一覧は 3 行を割ってよい・見出しは残す（v0.6 Codex 敵対的 high を反映） | トリガー一覧の 3 行を守る = 窓の最小で下の欄の見出しが消える |
| 5 | 押している間に構成セット・トリガー・描き直し・閉じるが起きたら取り消す（v0.3 Codex 敵対的 high）。実行中は描き直しのたびに取り消される＝受容（task_05 目視で許容） | 押下時の行で確定 = 実行の進行で別トリガーの行を変える |
| 6 | 省略表示の幅・高さを記録・最小の高さを設ける（v0.5 ユーザー追加要望）。最小の高さがモニタより大きくても最小を優先 | — |
| 7 | 省略表示中はステータス欄 2 行・ステータスバー 1 行に固定（改行を空白へ。v0.6 Codex 敵対的 medium） | 中身で高さが変わる = 最小の高さを測り直す契機が増える |
| 8 | 行の下の空白のクリックは何もしない（task_05 の統合レビュー Codex P2・ユーザー判断） | 最寄りの行で確定 = 押した行で離したときだけ、と矛盾 |
| 9 | （完了判定前 Codex 敵対的 medium = deep-reviewer M2）一覧の左右の外で離しても確定しない → task_06a で修正 | 正本の文言を上下の外だけへ絞る |
| 10 | （完了判定前 deep-reviewer L2）有効でないトリガーの判定を、呼び出し先の実行中の拒否より先に → task_06a で修正 | 受容（グレー行で拒否の一時メッセージが出る） |
| 11 | ステータスの見切れのツールチップ（task_05 目視時の要望）は範囲外として idea_40 へ分離 | phase 48 に枝番で入れる |

## 結果（タスク）

| タスク | 内容 | 実装 |
|---|---|---|
| task_01 | 次に実行の変更を行番号の共有処理へ（`set_next_action_index`） | codex-implementer・reviewer 採用 |
| task_02 | 省略表示のシーケンス欄の部品・描画・操作 | codex-delegating-implementer（Luna サブエージェント使用）・reviewer 採用 |
| task_03 | 3 段の高さの制御（`CompactPaneLayout`）・`compact_sequence_view` の保存 | codex-delegating-implementer・reviewer 修正して採用 |
| task_04 | 省略表示の窓の大きさ・最小の高さ・ステータスの行数 | codex-delegating-implementer・reviewer 修正して採用 |
| task_05 / 05a | 統合確認（deep-reviewer 修正して採用 / codex-reviewer P2）と指摘対応。欄の高さが Tk の都合で戻る不具合をメインで修正。実機目視 OK | codex-implementer・reviewer 採用 |
| task_06 / 06a | 正本反映・完了判定前レビュー（deep-reviewer 修正して採用 / Codex 敵対的 needs-attention 1 件）と指摘対応。遅延保存が混ざるテストの不安定さを修正 | メイン / codex-implementer・reviewer 採用 |
| task_07_refactor | 提案書 20（CallViewController の省略表示の分岐を置き場の配置役へ・保存の待ち時間の定数共有） | codex-delegating-implementer（サブエージェント不使用）・reviewer 採用 |

検証（最終・task_07 後）: tests 1325（skipped 7）/ tests_ui 875 ×2 / smoke pass。
その前の 1 回だけ `tests_ui/test_dialog_teardown_flows.py` の t4a / t4b / t5 が `1 != 0` で失敗（単独 2 回・全体 2 回では再現せず。phase 48 の差分と無関係の領域＝タイミング依存の不安定さとして記録）。

## レビュー保留（低・実害が出たら idea 化）

- 省略表示のシーケンス欄を閉じたとき `CompactPaneLayout._drag_heights` を消していない（ButtonRelease の取りこぼしで配置が止まる可能性・経路未確認。deep-reviewer L8）
- 最小の高さの測定はトリガー一覧のペインに一覧以外の部品が無い前提（部品が増えると黙って低く測る）
- フル表示のキー操作に呼び出し先の実行中の拒否が無い（既存・暫定 33 §11）
- `codebase_map.md` に phase 48 の索引項目（仕様・判断・テストの列挙）は置かない（phase 47 と同じ扱い。deep-reviewer L5）

## /refactor_check

- **推奨** → [提案書 20](../../../instructions/modified_proposal/20_refactor_compact_sequence_view.md)（M4: `call_view_controller.py` の `host.key == "compact"` 2 → 7 / M6: 500ms の直値）。ユーザー承認 → task_07_refactor で実施（分岐 0 件）
- 非該当: M1（`app.py` 657 行 +17・`trigger_panel_controller.py` 639 行 +6）・M2・M3（遅延保存は 2 箇所）・M5

## 教訓

- Tk の PanedWindow は欄の高さを明示しないと要求の高さへ戻し、古い大きさのまま境界を置くと押さえ込まれる。`paneconfigure height` で明示し、境界を置く前に `update_idletasks`。0 に縮んだ欄の子の `winfo_height` は古い値が残るのでテストで頼らない
- 遅延保存（after 500ms）を持つ部品を足すと、書き込み回数を数える既存テストに時間依存で混ざる。テストでは先にタイマーを取り消す
- Codex が既存の LF ファイルを CRLF で書き戻すことがある。コミット前に改行コードを確かめる
