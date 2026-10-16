# task_05_spec_promotion

## 目的

phase 60 の正本反映（暫定 44 §10）とフェーズ完了の記録。**文書のみ（コード不変）**。

## 対象範囲（文書のみ）

* `instructions/common/spec_detail/key_input.md` §7.4: 「取得の入口」「取得中の IME」「判別できないキー」を追加し、切替キーの取得の `??` の記述を置き換え（idea_46 の言及を削除）。§7.7 の送信時の IME から §7.4 へ相互参照
* `instructions/common/spec_detail/features.md` §4.3「割り当て禁止のキー」: 切替キーの `??` の旧文言を `key_input.md` §7.4 への参照へ
* `instructions/common/codebase_map.md`: infrastructure の一覧（`ime_control.py` / `own_ime_status.py`）・presentation の構成（`key_capture_ime.py`・`tk_keys.py`・`hook_button_texts.py`・`key_capture.py`・切替キーの 2 ダイアログの注記）・phase 60 の節（口・部品・8 入口の配線・`??`・前提・テスト）
* 暫定 44 の凍結（ヘッダ）/ `.claude_data/state/decisions_archive/60_ime_off_during_key_capture.md` / `decisions.md` の索引 / `instructions/phase/current.md` の完了記載 / idea_46 を `INDEX.md` から `INDEX_done.md` へ
* `/refactor_check`（メトリクスは verifier）

## 読むファイル

1. `instructions/history/44_ime_off_during_key_capture.md` §3〜§6・§10
2. task_04 の deep-reviewer の M1（正本反映で漏れやすい箇所・decisions_archive/60 に記録）

## 含まない

* コードの変更 / idea_48（取得中のフック再開）

## 確認

* 正本・地図に phase 60 の規定（8 入口・期間・開始 / 終了・重なり・失敗・受容・`??`）が載り、旧文言（「IME が ON の場合は OFF に」・idea_46 の言及）が残っていない（`grep` で確認）
* 完了判定前レビュー（`deep-reviewer` + `codex-adversarial-reviewer`）

## 完了条件

- 上記確認・完了判定前レビューの採用・`/refactor_check` の判定の記録。
