# task_03_spec_promotion

## 目的

暫定 59 v0.2 を正本へ昇格して凍結し、phase 77 を閉じる（暫定 59 §6・`.claude/rules/task_execution.md`「フェーズ完了時」）。
**文書のみ（メインセッションが直接行う・コード不変）。**

## 対象範囲（文書のみ）

- 正本: `data_schema.md` §5.14「書き出し」（書き出し先 `config/user/`・構成セット `user/keymap_sets/sample.json`・構成セットが無いときの同名の子の照合〔中身が同じなら衝突にしない / 違えば・読めなければ・リンク切れも何も書かず incomplete で空で始める〕・衝突時も標準の空フォルダはできる〔受容〕・利用者自作の同名構成セットを開く〔受容〕・別プロセスとの競合は扱わない・旧 `config/sample/` は書かない・移行しない）
- 正本: `data_schema/5_08_09_orphan_sweep.md` 経路 5（phase 73 の旧サンプル用・phase 77 以降は書き出さないが参照元としては残す）
- 正本: `features.md` §Welcome「起動の流れ」と失敗時の扱い（`config/sample/` → `config/user/`・同名の子の衝突でも警告して空で始める）
- `codebase_map.md` の `sample_install.py` の行（`_find_conflicting_children`・`save_plan_execution.preview_child_payloads`・経路 5 は旧サンプル用）
- 暫定 59 の凍結（状態行の書き換え）
- `decisions_archive/77_sample_in_user_folder.md` の作成・`decisions.md` の phase 77 節を移しアーカイブ索引へ 1 行
- `current.md` の完了記載（現在の参照先・次採番・暫定 59 の凍結）
- `/refactor_check`（手順 1〜2 は verifier）

## 読むファイル

1. `instructions/history/59_sample_in_user_folder.md` §2・§3・§6
2. 正本の該当行（上記）

## 含まない

- コードの変更

## 確認

- 正本・codebase_map に `config/sample/` への書き出しの記述が残っていない（経路 5 の旧サンプルの記述を除く）
- 完了判定前レビュー（deep-reviewer + codex-adversarial-reviewer）の採否をユーザーと決めた

## 完了条件

- 上記確認・**完了判定前レビュー採用**（reviewer 採用の代わり）。実機目視は task_02 で実施済み。
