# decisions_archive: phase 76 カウンター機能の拡張

暫定仕様先行モード（暫定 58 v1.1 凍結）・JSON スキーマ = 任意キーの追加（`counter_inc` の `amount`・構成セットの `counter_starts`）と種類 `counter_text` の追加・2026-11-23 完了。起票元 = ユーザー要望（idea なし）。

要点: 「カウンター +1」→「カウンター」（`amount`・既定 1・負 / 0 可）・「カウンターを0に」→「カウンターリセット」（開始値へ）。開始値は構成セットの `counter_starts`（名前ごと・0 は書かない）で、実行時は `AppState` が写しを持ち、構成セットを置き換える全経路で同期。実効値（値が入った名前は値 / 開始値 / 0）は `application/counter_values.py` の 1 か所。保留は `(op, name, amount)`。新しい種類 `counter_text` は実効値を text と同じ経路で入力。一覧・呼び出し先の表示枠の `(=値)` は保留を反映（v1.1）。昇格先は暫定 58 の冒頭の状態行。

## タスクと実装エージェント

- task_01 保存形式 25c123df・task_03 counter_text 54895e55・task_04 表示 7af28e7a = codex-implementer（Luna high）/ task_02 実行 b56a2fc1・task_05 編集 UI 9242ae4f = codex-delegating-implementer（Sol medium・サブエージェント未使用）。いずれも reviewer 採用。
- task_06 統合確認: deep-reviewer + codex-reviewer。R1〜R3 = codex-delegating-implementer（64d519e4）・R9 = codex-implementer（db6722df）・reviewer 採用・実機目視 OK。
- task_07 正本反映（本記録）。

## 【task_06 統合確認】指摘 R1〜R8 の採否（2026-11-23・ユーザー「推奨どおり進めて」）
- R1 tests_ui の `CallViewSummary` とスタブ・特性テストが `counter_starts` に未追従 → **採用**（テスト側のみ）
- R2 連続実行で待機をまたぐと、待機前に初めて入った名前が巻き戻しで消えない / R3 集合差での削除が他のトリガーの名前も消し得る → **採用**（その押下が初めて入れた名前だけを記録して消す = `track_counter_additions`・連続実行は待機をまたいで持ち回り・settle 系も記録）。暫定 58 §4.1 の「他の更新を消すことはない」の前提は実装で担保する形にした（正本 `features.md` §4.2.9）
- R4 呼び出し先の不正な `amount` のエラーが呼び出しの行で通知される → **保留**（ループ回数・待機 ms と同じ既存の扱い）
- R5 `counters is None` のとき counter_text は `(=0)` → **除外**（file_line と同じ）
- R6 描き直しは `refresh_actions` 経由・counter_text の通知はラベル付き → 正本へ実装どおり記載（task_07）
- R7 開始値を `CounterValues` の属性に持つ → **保留**（参考）
- R8 `test_minimize_grab_custody` → 解決（全体実行時のみの干渉・phase 76 と無関係）
- 保存 → 読込・サンプル設定に戻すの実機目視は自動テストで代える（ユーザー合意）

### 【phase 76 task_06】一覧の `(=値)` に保留中のカウンター操作を含める（2026-11-23・ユーザー判断 A）
- 検出: 実機目視で `[count+3]` が保留（features §4.2.2）のまま ▶ が `[counter_text]` にあるとき、表示 `(=22)` に対し入力は 25（正本 §4.2.2 L65「直前に実行した通常アクションの時点の値」どおり）
- A: `(=値)` = 実効値にそのトリガー（呼び出し先の表示枠は最上段）の保留を順に反映した値（次のステップの開始時の値）・表示だけ → **採用**
- B: 行ごとの見込み値 → **除外**（ループ・呼び出しをまたいで正確に出せない）/ C: 現行 + ヘルプで説明 → **除外**
- 影響: 暫定 58 §5.3 に条項追加・§9 に features §4.2.2 L65 の改訂を追加（task_07 で昇格）。実行の挙動は不変

## 【task_07】refactor_check = 不要（2026-11-23・メイン判断）
- M1 = 600 行超かつ +100 行のファイルなし / M2 = 80 行超の新規関数なし（`ActionExecutor.execute` 42 → 70 行）/ M3 = 該当なし（counter_text の書式は `sequence_control.py` の 1 か所・ラベル付き文言の分岐は既存の慣習の範囲）/ M4 = `CallViewSummary(` の生成 1 → 1・保留タプルの生成と分解は各 1 か所（`counter_starts` の引数の受け渡しは列挙の再構築ではない）/ M5 = 0 件 / M6 = 既存定数との重複なし
- 境界の 2 点は `current.md`「別タスク化候補」へ: `counter_text_error` の `_labeled` 動的キー（他は明示キー）・`"counter_text"` の直値（定数 `ACTION_TYPE_COUNTER_TEXT` があるが他の種別と同じく直値で並ぶ）

## 【task_07 フェーズ完了判定】deep-reviewer 修正して採用 / codex 敵対的 needs-attention の採否（2026-11-23・ユーザー「推奨どおり進めて」）
- deep-reviewer 指摘 1（§5.8.3 → §5.8.6）・2（§4.2 → §4.2.3）・4（行末の「/」）→ 修正（48e89762）/ 3（counter_text の「カウンター取得コールバックが未設定です」）→ 記載しない（配線の異常系）/ 5 → 完了時に phase.md・session.md を揃える
- C1（high・裏取り済み）: 無視した押下の巻き戻しが、その押下が入れた名前へ待機中に他の押下が書いた値まで消し、後でその押下を戻すと KeyError（`linked_call.py:19-20`・`sequence_history.py:112`）→ **採用**。暫定 58 §4.1 の「押下の間に他の押下が入らない」は待機をまたぐと偽。
  消すのは「その押下の間に他の押下が書き込んでいない名前」だけにする（`CounterValues` に名前ごとの書き込みの通し番号を持たせて判定）・戻すで名前が無ければ実効値から引く。正本 `features.md` §4.2.9 を改訂
- C2（medium）: 増やす量 0 でも値が入る（`sequence_steps.py:186`）→ **除外**（暫定 58 §4.1「カウンターの反映で値が入る」どおり）。正本 §5.11.6 の「0 は何もしない」を「値を変えない（値が入った扱いになる）」に直した
- C3（medium）: 手書きの `amount` が `2.5` / `true` の行はダイアログでそのまま OK できない → **除外**（`count` / `ms` の欄と同じ扱い・手書きの JSON のみ）
- C1 の実装: codex-implementer（Luna high）・reviewer 採用・tests 2267 / tests_ui 1316 / smoke pass（2026-11-23）
