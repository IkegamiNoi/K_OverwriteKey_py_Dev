# プロジェクト概要

本プロジェクトは

Python + tkinter + keyboard を用いた  
**キーボード入力置換シーケンサーアプリ**

である。

エントリーポイントは `main.py`。

---

# 最初に読むべきドキュメント

必須：

1. instruction/common/architecture_rules.md
2. instruction/common/dev_rules.md
3. instruction/common/codebase_map.md

作業内容に応じて：

- JSON関連 → instruction/common/json_spec.md
- UI変更 → instruction/common/ui_rules.md
- 変更手順 → instruction/common/change_rules.md
- 全体把握 → instruction/common/project_overview.md

---

# 禁止事項（重要）

- タスク指示なしの独断再設計を行わない
- 既存機能を破壊しない
- フック仕様（suppress / 停止制御）を軽視しない
- UIスレッドをブロックしない

---

# JSONに関する制約

- 既存キーの削除は禁止
- 意味の変更は禁止
- 後方互換を必ず維持する

※設計変更タスクの場合は、指示された範囲で変更可能

---

# 実装の基本姿勢

- 目的達成に必要な範囲で変更してよい
- 不要な変更は行わない
- 既存設計・命名を尊重する
- 影響範囲を理解してから実装する

---

# 実装前の必須手順

1. instruction/common/codebase_map.md を読む
2. 対象機能の関連コードを実際に読む
3. 影響範囲を把握する

---

# 実装後の必須対応

以下に変更がある場合は`instruction/common/`配下のドキュメントも更新する：

- クラス構成
- 関数責務
- JSON構造
- UI構成

---

# 出力ルール

- 変更内容は、変更箇所と意図が分かる形で示す
- 必要に応じて変更コードも提示する
- 説明は簡潔にする

---

# 安全設計

- フック暴走を起こさない
- suppressの副作用を考慮する
- keyboard例外は必ず吸収する