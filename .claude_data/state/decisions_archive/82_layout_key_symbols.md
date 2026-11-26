# decisions_archive: phase 82 レイアウトごとのキー名の記号の上書き

暫定仕様先行モード（暫定 [62](../../../instructions/history/62_layout_key_symbols.md) v0.4・凍結）・JSON スキーマ = レイアウトの JSON に任意キー `key_symbols` の追加（既存キーは不変）・起票元 [idea_63](../../../instructions/backlog/idea_63_backslash_display_fullwidth.md)。

要点: 日本語のフォントで `\` が ¥ に見え、`backslash`・`\`・`ro` と `yen` を見分けられない問題を、レイアウトの JSON の `key_symbols`（キー名 → 1 行の表示）で直す。選んでいるレイアウトの表が、トリガー一覧・key_hold の行（詳細表示・簡易表示・「次に実行」の要約・呼び出し先の表示枠）・キーボードUIのキー置換の枠の記号の表示を上書きする（配列は判別しない・domain は表を引数で受け取るだけ）。不正な表は読込エラーにせず使わず、ステータスバーの一時メッセージ欄の下敷きで警告（一時メッセージが消えたら戻る）。レイアウトの選択・追加・削除で両一覧を描き直す。見本 jis.json = `backslash` / `\` / `ro` → `＼`。正本 = `features.md` §4.5・§4.6 / `codebase_map.md`（`ui_terms.md` は文言の一覧も新しい用語も持たないので変更なし・`data_schema.md` にはレイアウトの JSON の書式が無い）。

## タスクと実装エージェント

- task_01 読込と domain の表示の関数 7e113f66 = codex-delegating-implementer（子は起動されず Sol 単独）・reviewer 採用。
- task_02 表の受け渡しと描き直し 97f73cbd = codex-delegating-implementer（子 2 つ）・reviewer 採用。
- task_03 警告の下敷きと見本 b2538a2d = codex-delegating-implementer（子あり・180 秒超で背景へ）・reviewer 採用。
- task_04 統合確認と実機目視 1762189b = deep-reviewer 採用 / codex-reviewer 指摘 2 件（受容 1・除外 1）・Windows の実機目視 1〜5 問題なし（ユーザー）。コードの変更なし。
- task_05 正本反映・完了（本記録）= メイン（文書のみ）。完了判定前レビュー = deep-reviewer 修正して採用（文言 3 点 + 記録 1 点 + 参照 1 点を反映）/ Codex 敵対的 needs-attention（medium 3 件 → ユーザー判断で受容し正本に明記・削除の後の保存失敗でも描き直すことを明記）。
- 実測（task_04・Windows）: compile clean / tests 2333（skip 9）/ tests_ui 1341 / smoke pass。

## 判断の記録（decisions.md から移動）

### 【起票時】方向 → **レイアウトの JSON の新しい任意の項目で持たせる・配列の判別はしない**（ユーザー確定 2026-11-25）
- 「JIS のときだけ適用」は採らない（¥ に見えるのはフォントの問題で配列ではない・他言語〔韓国語の ₩ 等〕も利用者が直せるように）。既存の `key_display_names` はキーボードUIの枠だけで一覧に使わない決まり（改行を含むため）なので、1 行の別項目 `key_symbols` を足す。
- 配列の種類をレイアウトに書く項目は idea_70 へ分離（macOS の JIS 判別の改善・本フェーズの表示には不要）。
### 【暫定 62 v0.2・v0.3】起票時 deep-reviewer「修正して採用」を反映 / 確認事項 5 点を提案どおり確定（2026-11-25）
- 呼び出し先の表示枠を対象に足す・上書きの表は `normalize_key_name` で引く・描き直しの入口を操作の 3 か所に・同梱の入れ方の根拠を `bundled_layouts.py` に。
- 項目名 `key_symbols` / 見本は jis.json だけ `backslash`・`\`・`ro` → `＼`（案 A）/ US のレイアウトの間は直らないのを受容 / jis_mac.json には書かない / 既存の利用者のフォルダは自動で直さない。
### 【暫定 62 v0.4】Codex 敵対的レビュー needs-attention 4 件 → ユーザー判断で反映（2026-11-25）
- high: 不正な `key_symbols` でレイアウトごと読めなくなり US TKL へ落ちる → **表だけを使わずレイアウトは読む**（採用）+ **警告をステータスバーの一時メッセージ欄の下敷きにする**（ユーザー追加案。自動で消えず上書きで失われる案・右の列に専用欄を作る案は除外 = 範囲が広がるため）。
- medium: 描き直しの入口 → `set_keyboard_layout_selection` の末尾を足す（採用）・フックキーの個別設定の切替での古い一覧は受容。
- medium: 選択を保つ API が無い → **保たない**（「次に実行」へ戻るのを受容）。
- medium: key_hold の対象 → 正しく読めたキーの行だけと明記（採用・文言のみ）。
### 【task_01】完了（2026-11-26・reviewer 採用）
- delegating の試行: codex-delegating-implementer に回した（本体 6・テスト 4 で目安に該当）。サブエージェントは起動されず Sol 単独で完了（rollout 2026-11-25T23-51-32 の model は gpt-6.1-sol のみ・同時刻以降に Luna の rollout なし）。1 回で完了・テストの書き漏らしなし。
### 【task_02】完了（2026-11-26・reviewer 採用）
- delegating の試行: 本体 5・テスト 4 で codex-delegating-implementer。子 2 つが起動された（rollout 2026-11-25T23-59-27 / 23-59-44 / 2026-11-26T00-00-48 に gpt-6-luna あり）。1 回で完了・既存の期待値の変更なし。
- tests_ui 全体で `test_minimize_grab_custody` が 1 件 fail（回ごとに別のテスト・a13 は単独で pass・同モジュール 3 回ずつで変更あり 1/3・基準 7e113f66 は 0/3）。変更は最小化・grab・after の経路に触れず、テストもレイアウトの変更や一覧の描き直しを呼ばない → **負荷依存の偶発的な失敗と判断（未確定）**。task_04 の統合確認で全体を流し直して再確認する。
### 【task_03】完了（2026-11-26・reviewer 採用）
- delegating の試行: 本体 6・テスト 3 で codex-delegating-implementer。子が起動された（Codex のログ「Collaboration tool wait」・自己申告で controller と見本のテストを分担）。180 秒超でバックグラウンドへ移り、出力ファイルの伸びが止まるのを待って受け取った。1 回で完了。
- 既存のテスト 3 件のテスト用の偽物（SimpleNamespace）に `key_symbols_invalid_reason=""` を足した（期待値は不変・追加の経路が新しい属性を読むため）→ reviewer 採用。
### 【task_04 統合確認】全 pass・統合レビュー deep-reviewer 採用 / codex-reviewer 指摘 2 件 → ユーザー判断待ち（2026-11-26）
- tests 2333 / tests_ui 1341 / smoke pass。`test_minimize_grab_custody` は全体と単独 3 回とも pass → task_02 の失敗は偶発と確定。
- Codex (1) 孤立サロゲートで Tk が落ちる → 実測で再現せず（除外を推奨）。Codex (2) キーマップの複数選択が 1 件に縮む → 裏取り済み（受容を推奨）。deep-reviewer T1〜T5 は task_05 に含めるのを推奨・L1〜L4 は保留を推奨。詳細は `instructions/phase/82_layout_key_symbols/task_04_pending_decisions.md`。
- ユーザー判断（2026-11-26）: Codex (2) キーマップの複数選択が縮む → **受容**（暫定 62 §6 に 1 行追記）。Windows の実機目視 1〜5 → **問題なし**。
- ユーザー判断（2026-11-26）: Codex (1) 孤立サロゲート → **除外**（実測で再現せず）。deep-reviewer T1〜T5 → **task_05 に含める**。L1〜L4 → **保留**・idea_71（優先度 低）に起票。
### 【task_04】完了（2026-11-26）: 統合確認 pass・統合レビューの指摘の採否が決定・Windows の実機目視 1〜5 問題なし（ユーザー）。コードの変更なし（暫定 62 §6 に受容を 1 行追記のみ）。

### 【task_05 完了判定前レビュー】deep-reviewer 修正して採用 / Codex 敵対的 needs-attention（medium 3）→ ユーザー「推奨どおり」（2026-11-26）
- deep 1（判定の順）・2（警告文の引用の空白）・3（codebase_map の呼ぶ位置）・7（「選び直すと新しい値」への受容の参照）→ 正本の文言を修正。deep 6 → `ui_terms.md` は変更なし（文言の一覧と新しい用語を持たない）と本記録に残す。deep 4（codebase_map の phase 節の置き場所）は既存の癖で対象外。
- Codex 1（フックキーの個別設定の切替でレイアウトが既定へ落ちると一覧が古いまま・`app.py:797`→`:805` の順を裏取り）→ 受容。正本の受容の文を「書き換えた・動かして読めなくなった直後」に広げた。
- Codex 2 / deep 5（表示名かキー名の改行で警告が詳細表示で複数行のまま居座る）→ 受容。最小の高さの条項に明記。
- Codex 3（JSON の同じキーの重複で書いた順の後勝ちが崩れる・`json.loads` の実測で後の値が最初の位置）→ 受容。正本に明記。
- Codex の補足（削除の後に保存が失敗・取り消しでも描き直す）→ 正本に明記。

### 【refactor_check】推奨 → 提案書 30（2026-11-26・ユーザー判断待ち）
- M1・M2・M4・M5・M6 は該当なし。M3（境界）: 「一時メッセージが無ければ下敷き」の規則を `App` の 3 か所で別々に書いている → 補助の判断材料（`app.py` 989 行に責務のまとまりが 3 つ以上）で推奨。提案書 = `instructions/modified_proposal/30_refactor_layout_key_symbols.md`（1 項目・挙動不変）。

## 残存リスク

- macOS の実機目視はしていない（jis_mac.json には書かない・Mac で `\` が ¥ に見えるかは未確認）。
- 既存の利用者の構成のフォルダに `user/keylayout` があれば同梱の見本は入らない（利用者が自分で `key_symbols` を書き足す）。
- US のレイアウトを選んでいるあいだは `\` は今のまま（配列を判別しないため・idea_70）。
- 受容（正本 §4.6）: 描き直しで出力シーケンス一覧の選択・キーマップ一覧の複数選択は戻る / フックキーの個別設定の切替の後の一覧の食い違い / 改行を含む名前の警告は複数行 / JSON の同じキーの重複。
