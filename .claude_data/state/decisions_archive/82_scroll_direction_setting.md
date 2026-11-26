# decisions_archive: phase 82 スクロールのアクションの向きの反転

暫定仕様先行モード（暫定 [62](../../../instructions/history/62_scroll_direction_setting.md) v0.4・凍結）・JSON スキーマ = config.json の任意キー `scroll_invert` の追加・起票元 [idea_58](../../../instructions/backlog/idea_58_scroll_direction_setting.md)。

要点: 出力シーケンスの `mouse_scroll` の向きを config.json の `scroll_invert` = `{"vertical": bool, "horizontal": bool}`（値ごとに bool だけ採用・既定は反転なし）で縦・横別に反転する。application が gateway の手前で符号だけを入れ替え（backend・OS の設定は不変・macOS の横は backend が OS へ渡すときにさらに符号を入れ替える）、行ごとに不変の値を読む。設定 > サブメニュー「スクロールの向き」> 縦を反転 / 横を反転。保存は `menu_commands.defer` 経由・保存済みと同じなら書かない・失敗で 2 つのチェックを戻す・成功で 1 回の代入。構成セットを未保存にしない。

## タスクと実装エージェント

- 起票 c6ee58a5 = メイン（暫定 62 v0.1 → deep-reviewer 修正して採用 → v0.2 → §6 ユーザー確定 v0.3 → Codex 敵対的 needs-attention 2〜5 反映 v0.4・1 は idea_70 へ）・reviewer 整合確認 採用。
- task_01 domain + application 872bc0c4 = codex-implementer（Luna high）・reviewer 採用。
- task_02 presentation 7bfc6821 = codex-delegating-implementer（Sol medium 主・Luna の子がテスト 3 ファイル・rollout で子の起動を実測）・reviewer 採用。
- task_03 統合確認と実機目視 b1cac697 = verifier（Mac: tests 2243 / tests_ui 80 モジュール 1339・失敗 0 / smoke）・deep-reviewer 採用（低 5）・codex-reviewer 指摘なし・実機目視 Windows / macOS OK。
- task_03a テストの補強 81723c9a = codex-implementer + メインの軽微修正 3 点・reviewer 採用。
- task_03b 横と待ち行列の境界のテスト 06c77a8b = codex-implementer・reviewer 採用。
- task_04 正本反映・完了（本記録）= メイン（文書のみ）。完了判定前レビュー = deep-reviewer 完了可（低のみ）/ Codex 敵対的 needs-attention（3 件）。

## 2026-11-26 (phase 82: スクロールのアクションの向きの反転・暫定 62)

### 【起票】方式と縦横（2026-11-26・ユーザー確定）
- 案 A = config.json のグローバル設定（アクションごとの指定・Mac の OS の設定への自動追従は採らない）・縦横を別々に・既定は反転なし。
- 暫定仕様先行モード（config.json・メニュー・文言・application・正本に跨る）。

### 【暫定 62】v0.1 → v0.4（2026-11-26・ユーザー確定）
- deep-reviewer: macOS のメニューの遅延（保存は defer）・`test_menu_bar_deferral.py` の期待値の変更・構成セットを未保存にしない・書く値と戻し先・不正値が残る書き方 等を採用。setter 案は保留（callable は `get_counter` の前例に揃う）。
- §6: メニュー = 設定 > スクロールの向き（物理キー名の後・フォントサイズの前）/ ヘルプに 1 文 / ダイアログ・一覧に反転中を出さない。
- Codex 敵対的（起票時）: 2 保存失敗でフックが止まる（受容・明記）/ 3 反転は保存成功の後の行から / 4 片方だけ不正 / 5 符号の 3 段（macOS の横）→ 反映。1 多重起動での上書き → スコープ外・idea_70。

### 【task_02】codex-delegating-implementer の試行の記録（2026-11-26・目安の試行扱い）
- 目安に当たった理由: 本体 7 ファイル（presentation 3 + 言語ファイル 2 + ヘルプ 2）・テスト 3 ファイル・既存の期待値の変更（`test_menu_bar_deferral.py`）。
- 実測: rollout `2026-11-26T20-19-58-…` に `thread_source: subagent`（gpt-6-luna）あり = 子は起動された（主は gpt-6.1-sol）。子の担当はテスト 3 ファイル（自己申告）。1 回の依頼で本体・テストとも書き終えた（期待値の直し漏れなし・既存テストの途中への差し込みなし・メインで直読み済）。

### 【task_03】統合確認 pass・統合レビューの採否・実機目視 OK（2026-11-26・ユーザー判断「推奨通りでよい」）
- 統合確認（Mac・HEAD 7bfc6821）: compileall clean / tests 2243 pass（skip 34）/ tests_ui 80 モジュール別プロセス 1339 件・失敗 0 / smoke OK。
- deep-reviewer 採用（低 5）・codex-reviewer 指摘なし。採否: ①保存→再読込の往復テスト・③メニューの invoke とフォント変更での作り直しのテスト・⑤dirty テストの意図の明示 → **task_03a（テストのみ）**。②失敗のつながりは既存の起動設定の保存失敗と同じ経路のため**受容**（Mac で固まらないことは実機目視 5 で確認）。④正本昇格の注意（`features.md` §4.8 の列挙と文・`data_schema.md` §5.4 を `compact_header_view` と同じ書き方で 4 点）→ **task_04**。
- 実機目視（ユーザー・Windows / macOS とも task_03 定義の 1〜7）: 問題なし。

### 【task_04 完了判定前】deep-reviewer 完了可 / Codex 敵対的 needs-attention 3 件（2026-11-26・ユーザー判断「推奨」）
- Codex 1（起動時に config.json が読めなかったとき、次の保存で元のファイルを置き換える・全設定に共通の既存の性質）→ **スコープ外・idea_71**。
- Codex 2（§5.11.10 の ③ が Windows の送り方を OS 限定せず・反転の段落が ③ の途中）+ deep-reviewer ①（段落の位置）→ **正本修正**（反転を ③ の後へ・③は Windows と明記し macOS は `features.md` §4.8「マウス」を参照）。deep-reviewer ②（macOS の遅延の間は前の向き・終了で捨てた切り替えは反映しない）→ **features §4.6 に 1 文**。
- Codex 3（横のチェックの配線と macOS の待ち行列の境界のテストなし）→ **task_03b**。
- deep-reviewer ③（ヘルプの 1 文は正本に入れない）・④（待ち行列に 2 件溜まり 1 件目が失敗した場合の挙動は正本から導ける）・⑤（受け入れ条件の担保の内訳）・⑥ は記録のみ。

### 【refactor_check】不要（2026-11-26・メイン判定）
- M1・M2・M3・M5・M6 は該当なし。M4 = `ScrollInvert(` の全フィールドの組み立てが新しい型のため 0 → 3 か所（フィールド 2 つ）。境界事例とし、定性材料（責務の混在・説明しにくさ）に当たらないため不要。`current.md` の別タスク化候補に記録（M3 の参考 = `set_scroll_invert` と `set_ui_language` の同型 2 か所も）。

## 残存リスク

- 実際のスクロールの向き（特に backend が符号を入れ替える macOS の横）と、macOS でメニューから切り替えて固まらないこと・失敗の知らせは実機目視のみで確認（2026-11-26 OK）。
- 「新規作成・読込で値が変わらない」は構造上のみ（値は App と `_startup_settings` が持ち、構成セットのデータは持たない）。ヘルプの 1 文は専用のテストなし。
- 多重起動での上書き（idea_70）・読めなかった config.json の上書き（idea_71）は未対応。
