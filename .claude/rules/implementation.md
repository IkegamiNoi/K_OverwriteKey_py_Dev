# 実装ガイド

## UI（tkinter）

* FullView / CompactView を `pack_forget` で切替（grid 構造を崩さない）
* UI 更新は必ず UI スレッドで行う（`after()` を使用）
* UI スレッドをブロックしない

---

## フック（keyboard）

* グローバルフック・`suppress=True`。UI 編集中は停止（ネスト対応）
* フック暴走防止を最優先し、keyboard の例外は必ず吸収する
* フック処理を UI と競合させない（詳細は `instructions/common/spec_detail/key_input.md`）

---

## イベント処理・状態管理

* presentation → application に通知し、application が状態更新・実行制御を行う
* クラス構成・各コントローラの責務は `instructions/common/codebase_map.md` が正

---

## JSON

* 後方互換必須・既存キー削除禁止・意味変更禁止（`instructions/common/spec_detail/data_schema.md`）

---

## 実装前の必須手順

1. `instructions/common/codebase_map.md` を読む
2. 対象機能の関連コードを実際に読む
3. 影響範囲を把握してから実装する

---

## 実装後の必須対応

以下に変更がある場合は `instructions/common/` 配下のドキュメント
（特に `codebase_map.md` / `spec_detail/`）も更新する:

* クラス構成 / 関数責務 / JSON 構造 / UI 構成

---

## 制約と最適解が衝突する場合（非通常ルール）

* 通常案（制約内の案）を提示する
* 追加で改善案を提示してよいが、制約違反となる点を明示する

---

## テスト戦略

* domain / application: pytest による単体・ユースケーステスト（`tests/`）
* presentation: 最小限（UI フローは `tests_ui/`）

---

## 実装時のサイズ目安（予防）

* 関数はおおむね 30 行以内を目安にする
* 新規ファイルはおおむね 300 行以内を目安にする
* 超える場合は分割を検討（配置は `.claude/rules/file_organization_rules.md`）

---
