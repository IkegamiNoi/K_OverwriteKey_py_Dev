# decisions_archive: phase 78 アクションの hotkey の保存時の検査と正規化

直接改訂モード（暫定なし・正本 `key_input.md` §7.7 L232・§7.9 L346）・JSON スキーマ不変・2026-11-23 完了。起票元 = [idea_03](../../../instructions/backlog/idea_03_action_hotkey_save_normalization.md)。

要点: 出力シーケンスの hotkey アクションの OK で、他方の OS の修飾キーの検査（phase 75・文言不変）の後に `App.validate_hotkey`（文法の検査 + 各キーの `validate_key_name`。プリセット編集と同じ）を通す。不正なら保存しない。通れば正規化した値（`Ctrl+ A` → `ctrl+a`）を保存する。既存の正規化前の値は移行しない（実行時の正規化で送り、編集して OK を押せば正規化される）。今のレイアウトで通らない既存値は、ラベルだけの変更でも保存できない（key_hold と同じ）。

## タスクと実装エージェント

- task_01 正本改訂 64f1dc46 = メイン（文書）・reviewer 採用。
- task_02 `ActionDialog.on_ok` 8ea74fc4 = codex-implementer（Luna high）・reviewer 修正して採用（`tests_ui/test_action_dialog_labels.py` の fake root に `validate_hotkey` が無く落ちる → メインが setUp に追加）・verifier pass。
- task_03a テスト補強 8aab3f01 = codex-implementer（Luna high・① の文言の強化が抜けていたためメインが 1 語修正）・reviewer 採用・35 件 pass。
- task_03 統合確認・記録（本記録）: compile / tests 2278（skip 9）/ tests_ui 1319 / smoke pass（verifier）・実機目視 OK（ユーザー・Windows）。refactor_check = 不要。

### 【phase 78 起票】（2026-11-23・ユーザー確定）
- 保存時 = 検査して不正なら拒否・通れば正規化値を保存 → **採用**（プリセット・key_hold と揃える。idea_03 の案 1 + 案 3 + 2026-11-15 追記のホワイトリスト方式）
- 既存 `sequences/*.json` の正規化前の値 = 移行しない・読み込み時の正規化なし → **採用**
- 直接改訂モード → **採用**
- phase 77 の完了日の誤記 2026-11-24 → 2026-11-23（ユーザー指摘・state と phase 77 の文書で訂正）

### 【task_03 完了判定前レビュー】deep-reviewer 修正要（軽微 7）/ codex-adversarial-reviewer needs-attention（medium 2）の採否（2026-11-23・ユーザー判断）
- Codex 2 = deep 1「今のレイアウトで通らない既存値は、ラベルだけ変えても OK できない」→ **A: 拒否のまま**（コード不変・正本 L232 に 1 文追加。key_hold と同じ扱い。「値が未変更なら通す」案は不採用）
- Codex 1「macOS で Option+, を記録すると `option+comma` になり、送信側が `comma` を解決できず OK で弾かれる」（実測で事実: `tk_keys.py:72-74`・`macos/key_table.py:26,88-93`・見本レイアウトの `,` に `scan_code` なし）→ **除外**（記録と送信の名前の不一致は既存の問題・以前は実行時に失敗していた。[idea_45](../../../instructions/backlog/idea_45_tk_key_capture_symbol_names.md) に追記）
- deep 2（他方 OS の検査が先に走ることを文言全体で固定）・3（既存行の編集で正規化）・4（エラー文の表示）→ **採用**（task_03a）/ deep 6（codebase_map L646 の呼び出し元）→ **採用** / deep 5（記録から OK までの通し）→ 実機目視で代える / deep 7（features.md への追記）→ **保留**
- refactor_check の実測（メイン・PHASE_BASE d7988c67・keyseq 1 ファイル +5）: M1 = action_dialog.py 670 行 +5（600 行超だが増分 100 未満）/ M2〜M4・M6 = 該当なし / M5 = 0 件 → **不要**
