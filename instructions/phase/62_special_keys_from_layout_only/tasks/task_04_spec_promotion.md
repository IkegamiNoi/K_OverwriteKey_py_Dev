# task_04_spec_promotion

## 目的

暫定 45（v0.5・ユーザー確定済）を正本へ反映し、暫定 45 を凍結してフェーズ 62 を閉じる（暫定 45 §9・`.claude/rules/task_execution.md`「フェーズ完了時」）。
**文書のみ**（コードは変えない）。

## 対象範囲（文書のみ）

### 正本 `instructions/common/spec_detail/`

- `key_input.md`
  - §7.1: フックの実行時のキー名の出どころ（テンキー → 選んでいるレイアウトの `scan_code` だけ → `event.name`）と受容
    - 受容 1: jis.json 以外では特殊キーは `event.name`
    - 受容 2: 押下だけが続けて届くキーは扱えない（idea_52）
  - §7.4: キーボードUI の編集の項の「既知の表へは落とさない」と受容の書き換え（フックと同じ解決になった）
  - §7.7: 送信の解決の順・レイアウトのキーの送り方・検査と同じキーの判定・注入・レイアウトが変わる前の離し・受容
  - §7.8: 同じキーの判定の「JIS の特殊キーの表」→ レイアウト
- `features.md` §4.6「レイアウトの JSON」: `scan_code` の意味（受け取りと送信の名前・1〜255・keyboard が知る名前に別の値を書かない・拡張キー・特殊キーを使うならそれを書いたレイアウトを選ぶ・切替 / 読み直しで離す）

### 地図・記録

- `instructions/common/codebase_map.md`: `keyboard_layouts.py` の行・`LayoutController`・キーの送信の節・テンキーの検査 / 送信の行
- 暫定 45 の凍結（ヘッダを「凍結（2026-10-18・正本反映済）」へ）
- `.claude_data/state/decisions_archive/62_special_keys_from_layout_only.md` の新規作成
- `.claude_data/state/decisions.md` のアーカイブ索引に 1 行
- `instructions/phase/current.md`: 完了記載・次採番（phase 63 / 暫定 46 / decisions 63）
- `instructions/backlog/INDEX.md` の idea_49 の行を完了にして `INDEX_done.md` へ移す
- `/refactor_check`（メトリクス収集は verifier）
- 完了判定前レビュー: `deep-reviewer` + `codex-adversarial-reviewer`

## 読むファイル

1. `instructions/history/45_special_keys_from_layout_only.md`（全節）
2. 正本の上記の節
3. `instructions/common/codebase_map.md`（:126・:319・:791・:819-）
4. 手本: `.claude_data/state/decisions_archive/61_keyboard_ui_vk_to_scan_code.md`

## 含まない

- コードの変更
- idea_50 / idea_51 / idea_52

## 確認

- 正本の記述が暫定 45 の §3〜§6 と食い違わない（完了判定前レビューで確かめる）
- `grep -rn "resolve_key_id_from_scan_code\|resolve_known_\|SPECIAL_KEY_NAMES\|既知の特殊キーの表" instructions/common` が、経緯として残す記述を除いて 0 件

## 完了条件

- 上記の反映と、**完了判定前レビュー（deep-reviewer + codex-adversarial-reviewer）の指摘への対応**が済み、ユーザーが確定していること
- 実機目視: 済み（task_03・2026-10-18。無変換・変換は idea_52）
