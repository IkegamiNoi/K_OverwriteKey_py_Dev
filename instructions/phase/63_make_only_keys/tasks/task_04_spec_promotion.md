# task_04_spec_promotion

## 目的

暫定 46（v0.5・ユーザー確定済）を正本へ反映し、暫定 46 を凍結してフェーズ 63 を閉じる（暫定 46 §8・`.claude/rules/task_execution.md`「フェーズ完了時」）。
**文書のみ**（コードは変えない）。

## 対象範囲（文書のみ）

### 正本 `instructions/common/spec_detail/`

- `key_input.md`
  - §7.1: 押下だけのキーの受容（「このキーは扱えない」）を「組み直す」規定へ（暫定 46 §3・§4 の受け取り）
  - §7.3（入力判定）: 押下だけのキーの「押した / 離した」・リピートなし・覚えた決定を返す・**離した直後の押下は押し続けの続き（v0.5・注 5）**・時間の値（§3.3）・主な受容
  - §7.2: 押下だけのキーは停止要求の間は素通し（§3.2 注 1）
  - §7.7: 送信の最中の物理の入力の取りこぼしに、押下だけのキーでは IME が切り替わり得ること・リピートなしの理由・idea_53 / 送信は `extra_scan_codes` を使わない
- `features.md` §4.6「レイアウトの JSON」: 任意キー `extra_scan_codes` / 241・242 の受容の書き換え / 「押下だけの走査コードを `scan_code` に書かない」は維持
- `features.md` §4.6「キーボード表示のウィンドウ」: 押下だけのキーの直接置換の枠は灰色がかった緑
- `data_schema.md`: レイアウトの JSON の記載があれば追従

### 地図・記録

- `instructions/common/codebase_map.md`: 新しいモジュール（domain / application の `make_only_keys.py`）・`hook_controller.on_input_event` の分岐・`keyboard_layouts` の照合・キーボードUI の色の値（地 `#e4ebe1`・枠 `#7f9a74`・文字 `#2f4429`・2026-10-20 確定）
- 暫定 46 の凍結（ヘッダを「凍結（2026-10-20・正本反映済）」へ）
- `.claude_data/state/decisions_archive/63_make_only_keys.md` の新規作成・`decisions.md` の phase 63 節を索引 1 行へ
- `instructions/phase/current.md`: 完了記載・次採番（phase 64 / 暫定 47 / decisions 64）
- `instructions/backlog/INDEX.md` の idea_52 の行を完了にして `INDEX_done.md` へ移す
- `/refactor_check`（メトリクス収集は verifier）
- 完了判定前レビュー: `deep-reviewer` + `codex-adversarial-reviewer`

## 読むファイル

1. `instructions/history/46_make_only_keys.md`（全節）
2. 正本の上記の節
3. `instructions/common/codebase_map.md`（キー入力・キーボードUI・レイアウトの節）
4. 手本: `.claude_data/state/decisions_archive/62_special_keys_from_layout_only.md`

## 含まない

- コードの変更
- idea_50 / idea_51 / idea_53 / idea_54

## 確認

- 正本の記述が暫定 46 の §2〜§5 と食い違わない（完了判定前レビューで確かめる）
- `grep -rn "扱えない" instructions/common/spec_detail/key_input.md` の押下だけのキーの受容が残っていない

## 完了条件

- 上記の反映と、**完了判定前レビュー（deep-reviewer + codex-adversarial-reviewer）の指摘への対応**が済み、ユーザーが確定していること
- 実機目視: 済み（task_03f の後・2026-10-20・§6 #6 OK）
