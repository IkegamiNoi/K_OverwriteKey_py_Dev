# task_04_spec_reflection

## 目的

phase 66 の正本反映とフェーズ完了処理（暫定 49 §9）。task_01〜03 の実装（取得用のフック・8 入口の受け取り）を正本へ昇格し、暫定 49 を凍結する。
**文書のみ・コード変更なし。** 実機目視（暫定 49 §7-8）は 2026-10-21 ユーザー OK。

## 対象範囲（文書のみ）

- `instructions/common/spec_detail/key_input.md` §7.4: 「取得用のフック」の項を足す（暫定 49 §3・§4・§5）/ 「未対応: JIS の特殊キー」と「判別できないキー」の JIS の特殊キーの記述を、レイアウトの行に当たれば取得用のフックで取れる・書いていないレイアウトでは今どおり `??` へ / §7.1 に取得用のフックが同じ解決を使うこと
- `instructions/common/spec_detail/features.md` §4.3 :481 付近（切替キーの取得の `??` の説明）に、レイアウトの行に当たる特殊キーは取れることを 1 文
- `instructions/common/codebase_map.md`: `key_capture_hook.py` の 1 行（ツリー）・phase 60 の節に phase 66 の取得用のフックと入口の受け取り（`on_hook_key`・世代・#7 / #8 の begin）の項
- 暫定 49 の凍結
- `.claude_data/state/decisions_archive/66_capture_jis_special_keys.md` の作成・`decisions.md` の phase 66 節を移しアーカイブ索引へ 1 行
- `instructions/phase/current.md`: 完了記載・次採番（phase 67 / 暫定 50 / decisions 67）
- `instructions/backlog/INDEX.md` の idea_50 行を完了にして `INDEX_done.md` へ移動
- `/refactor_check` の判定記録
- 完了判定前レビュー（`deep-reviewer` + `codex-adversarial-reviewer`）

## 読むファイル

1. `instructions/history/49_capture_jis_special_keys.md`（§3〜§5・§9）
2. `instructions/common/spec_detail/key_input.md:13-15`・`:133-161`
3. `instructions/common/spec_detail/features.md:478-482`
4. `instructions/common/codebase_map.md:140-155`・`:808-816`

## 含まない

- コードの変更
- 暫定 49 §8 のスコープ外（idea_45・idea_48・特殊キーを書いていないレイアウト）

## 確認

- 正本の記述が実装（`key_capture_hook.py`・`key_capture_ime.py`・8 入口・`app.py`）と一致
- リンク切れなし（idea_50 を INDEX_done へ移した後の参照）
- `/refactor_check`: PHASE_BASE = `1a01d5b`（phase 65 の最終コミット）・`git diff 1a01d5b..HEAD -- keyseq/` で M1〜M6 判定

## 完了条件

- 上記確認・**reviewer 採用**（フェーズ完了判定のため `deep-reviewer` + `codex-adversarial-reviewer`）。
- 実機目視: 2026-10-21 ユーザー OK（暫定 49 §7-8）。
