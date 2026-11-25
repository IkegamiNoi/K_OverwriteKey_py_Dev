# decisions_archive: phase 81 キー置換の置換先に英字の大文字

暫定仕様先行モード（暫定 [61](../../../instructions/history/61_uppercase_replacement_target.md) v0.3・凍結）・JSON スキーマの型は不変（置換先の `A`〜`Z` だけ大文字を保つ）・2026-11-25 完了。起票元 = [idea_62](../../../instructions/backlog/idea_62_uppercase_replacement_target.md)（置換元の Shift の面は [idea_68](../../../instructions/backlog/idea_68_shift_layer_replacement_source.md) へ分離）。

要点: 置換先の `A`〜`Z` は大文字のまま保存し、小文字と同じキーで解いて Shift を足して送る（phase 74 の送り方。Shift / Ctrl / Alt / Win が物理または送信済みで押されていれば足さない）。macOS は「押されている」の判定に送信済みの修飾（`KeyboardBackend.sent_modifiers_down`）を含める。キーボードUI は Shift + 英字の記録で大文字・大文字の置換先は表示名を引かない。正本 = `data_schema.md` §5.1・§5.6 / `key_input.md` §7.4・§7.9 / `features.md` §4.6 / `codebase_map.md`。

## タスクと実装エージェント

- task_01 保存・判定・送信 e722ec75 = codex-implementer（Luna high）+ メイン修正 2 点・reviewer 採用。
- task_02 キーボードUI の記録と表示 54070fdd = codex-implementer（Luna high）+ メイン修正 1 点・reviewer 採用。
- task_03 統合確認と実機目視 2ef511d7 = deep-reviewer 修正して採用 / codex-reviewer P3 × 3 → task_03a・reviewer 採用。
- task_03a テストの検出力の補強 56b3c8dc = codex-implementer（Luna high）+ メイン修正 1 点・reviewer 採用。
- task_04 正本反映・完了（本記録）= メイン（文書 + `contracts.py` のコメント）。tests 2295（skip 9）/ tests_ui 1334 / smoke pass（verifier・task_02〜03a 時点）・`compileall` clean（task_04）。

## 2026-11-25 (phase 81: キー置換の置換先に英字の大文字・暫定 61)

### 【起票】idea_62 の意図確認 → 置換先に大文字（2026-11-25・ユーザー確定）
- idea_62 の当初案（置換元に `Shift+A` 等の修飾付きの組み合わせ）ではなく、ねらいは**置換先に英字の大文字を置くこと**（phase 74 の Shift の要る記号の延長・使い勝手の向上）→ **採用**。idea_62 を書き直し、置換元の Shift の面（同じキーマップに Shift を押している間の面）は idea_68 へ分離（Shift 以外の修飾の面も同 idea で検討）。
- 暫定仕様先行モード（`data_schema.md` / `key_input.md` に跨る）。

### 【暫定 61】v0.1 → deep-reviewer 修正して採用 → v0.2 → Codex 敵対的 needs-attention（5 件 + 表示名）→ v0.3 ユーザー確定（2026-11-25・「推奨通りで良い」）
- deep-reviewer: Windows の keyboard の表は修飾なしの候補が先で `A` は Shift 付きと判定されない見込み（H1）/ `set_mapping` の保存箇所の漏れ（M1）/ 正本 §5.1・codebase_map の反映先（M2）/ 既存テストの期待値の変更（M3）/ リピート停止は走査コードの照合で変更不要（M4）→ すべて反映。
- Codex 1（記録の Shift の判定は処理の時点）→ 受容（phase 74 と同じ・入れ直せる）。
- Codex 2（macOS の Shift / Ctrl 等の判定が物理のフラグだけで key_hold の送信済みの修飾を見ない）→ **本フェーズで直す**（記号と英字で共通・正本 §7.4「物理キー・key_hold のどちらでも」に合わせる）。
- Codex 3（Caps Lock）→ 見ない・受容。結果は OS ごと（Windows は小文字・macOS は大文字の見込み）を実機で確かめるが補正しない。
- Codex 4（大文字の名前のままだと入力配列で別のキーに解け得る）→ 大文字は小文字の名前で解き Shift の要否だけを決める（両 OS）。保証はラテン文字の配列。ユーザー: 意図に沿う。
- Codex 5（手書きの `"A"` の意味の変化・旧版で保存し直すと小文字になる）→ どちらも受容し明記。
- 追加（外部レイアウトの表示名は `A` と `a` を同じ名前で引く）→ 大文字の置換先は表示名を引かずに大文字で出す。

### 【task_03 統合確認】deep-reviewer 修正して採用 / codex-reviewer P3 × 3（いずれもテストの検出力）→ task_03a（2026-11-25・ユーザー判断「推奨どおり」）
- 実装の欠陥の指摘なし。採用 = 表示のテストの差し替えを本物と同じ大小無視に（両者）・macOS の送信済みの修飾を送信の経路と gateway を通して確かめる（両者）・分割設定の保存と読込の往復で大文字が残る（両者）・Shift + 数字が変わらない（deep 7）。
- 足さない（メイン判断）: リピート停止の直接テスト（deep 3）。照合は gateway の走査コード（`held_inputs.py:87-90`）で、`A` と `a` の一致は task_01 で両 OS を確かめた。偽の gateway で書くと同じ前提の繰り返しになる。reviewer も妥当と判定。
- task_04 へ送る: Windows の `sent_modifiers_down` が (False, False) の理由（`GetAsyncKeyState` が送ったキーも反映する見込み）を正本と契約に書き添える（deep 4）/ 英字 1 文字の判定の重複 6 か所（deep 6・任意・/refactor_check で扱う）/ `sent_modifiers_down` の lock なしの読み（deep 5・低・受容）。

### 【task_03 実機目視】OK（2026-11-25・ユーザー報告「目視 OK」）
- 手順 1〜5 をユーザーが確かめ「目視 OK」。NG の報告なし。5（Caps Lock ON の文字）は見込みどおりとして扱う（補正しない・暫定 61 §5 のまま）。OS ごとの内訳と 5 の実際の文字の報告はないので、正本には「見込み」と書き、実測済みとは書かない。
- OS 別の内訳は未報告（macOS で確かめたかは不明）。正本と current.md には「macOS の実機目視は未確認」と書く（task_04 へ）。reviewer 採用（2026-11-25）。

### 【task_03 実機目視の補足】macOS の Caps Lock 以外はすべて条件どおり（2026-11-25・ユーザー報告）
- Windows: 手順 1〜5 すべて条件どおり（Caps Lock ON で `a`）。macOS: 1〜4 は条件どおり・5（Caps Lock ON）は未確認。正本は Windows の Caps Lock を実機目視・macOS の Caps Lock を見込み（未確認）と書く。

### 【task_04 完了判定前レビュー】deep-reviewer 修正して採用 / Codex 敵対的 needs-attention（medium 3）→ ユーザー「推奨どおり」（2026-11-25）
- deep 1（macOS の物理のフラグに送信済みの修飾が入らないと事実として書いた）→ 「入らない場合に備え（未実測）」に直す（`key_input.md` §7.4）。
- deep 2（macOS の実機目視の未確認の明記が弱い）→ 上の補足で目視の範囲が確定したため、§7.4・§7.9 に「実機目視 2026-11-25〔Caps Lock ON は未確認〕」を書く。
- deep 3（Shift の受容の逆向きが正本にない）・deep 4（§5.6 の小文字化の文に例外の参照）→ 採用。deep 5（codebase_map の OS 窓口の列挙）→ 保留（`:908` に記載済み）。
- Codex 1（macOS でフックの開始前から押している Command が置換の送信に付かない）→ phase 81 の変更ではなく送るフラグの組み立ての以前からの性質 → [idea_69](../../../instructions/backlog/idea_69_mac_premod_lost_on_mapped_send.md) へ分離（静的推論・未実測）。
- Codex 2（外部レイアウトに `a` の表示名 `A` があると `a` と `A` が同じ表示）→ 暫定 61 §5 の確定どおり（小文字は表示名を使う）。`features.md` の「見分けられる」の言い過ぎを直し、受容として明記。
- Codex 3（実機目視の記録の不足）→ 上の補足で解消。

### 【refactor_check】推奨 → 提案書 29（2026-11-25・ユーザー承認待ち）
- M3 該当: 英字 1 文字の大文字の判定が 3 層 7 か所（+ 記録時の小文字の判定 1 か所は対象外）・Windows の press / release の同じ式 2 か所 → [29_refactor_uppercase_replacement_target.md](../../../instructions/modified_proposal/29_refactor_uppercase_replacement_target.md)（R1・R2）。M1 = 600 行超の 2 ファイルは増分小で非該当・他は該当なし。

## 残存リスク

- macOS の Caps Lock ON の文字は未確認（`A` の見込み・補正しない）。
- Windows で `GetAsyncKeyState` が送ったキーも反映する点は見込み（key_hold の Shift での目視は OK）。macOS の物理のフラグに送信済みの修飾が入るかは未実測（OR で合わせるため結果は同じ）。
- 置換先 `A` のリピート停止は走査コードの一致で間接的に確かめただけ（直接のテストなし・メイン判断）。
- macOS でフックの開始前から押している修飾の扱い（idea_69）。外部レイアウトの英字の表示名による `a` / `A` の同じ表示（受容）。
