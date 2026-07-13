# AGENTS.md

本プロジェクトは Python + tkinter + keyboard を用いた
**キーボード入力置換シーケンサーアプリ**である。
エントリーポイントは `main.py`、パッケージは `keyseq/`（オニオンアーキテクチャ）。

本ファイルは入口のみ。仕様・ルールの正本は以下を参照すること。

---

# 最初に読むべきドキュメント

必須:

1. `instructions/common/app_overview.md` — アプリ全体概要・詳細仕様への索引
2. `instructions/common/codebase_map.md` — コード構造（実装状態の正）
3. `.claude/rules/implementation.md` / `.claude/rules/python_rules.md` — 実装ルール

作業内容に応じて（`instructions/common/spec_detail/`）:

- JSON 関連 → `data_schema.md`
- フック・キー入力 → `key_input.md`
- UI 変更 → `features.md`（4.6 UI 構成）
- 設計判断 → `design.md` / `architecture.md`

ワークフロー（タスク進行・レビュー・仕様変更）は `CLAUDE.md` と `.claude/rules/` に従う。

---

# 特に重要な制約

- **JSON 後方互換必須**: 既存キーの削除・意味変更は禁止（設計変更タスクで指示された範囲のみ可）
- **フック安全**: 暴走を起こさない / suppress の副作用を考慮 / keyboard 例外は必ず吸収
- **UI スレッドをブロックしない**（UI 更新は `after()` を使用）
- タスク指示なしの独断再設計を行わない
- クラス構成・関数責務・JSON 構造・UI 構成を変えたら `instructions/common/` 配下の
  ドキュメントも更新する
