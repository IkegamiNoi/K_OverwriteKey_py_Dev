---
description: 改善ネタ (idea) を instructions/backlog/ へ起票し INDEX.md を更新する
---

改善ネタを `instructions/backlog/` へ 1 ネタ 1 ファイルで起票してください。
idea は **正式なフェーズ / タスクではない**（着手時にフェーズ / タスクとして起票し直す。
運用ルールの正本は `instructions/backlog/INDEX.md` 冒頭）。

## 手順

1. **採番**: `instructions/backlog/` 内の既存ファイルの最大番号 + 1。
   **INDEX.md の表を基準にしない**（表には欠落があり得る〔過去の削除運用等〕ため、表の
   最大番号はフォルダの最大番号より小さいことがある）。
   Glob `instructions/backlog/idea_*.md` で確認する。
2. **ファイル作成**: `instructions/backlog/idea_<NN>_<topic_snake_case>.md`（NN はゼロ埋め 2 桁）。
   書式は下記。
3. **INDEX.md 更新**: `instructions/backlog/INDEX.md` の「ネタ一覧」表の末尾に 1 行追加:

   ```markdown
   | idea_NN | [idea_NN_<topic>.md](idea_NN_<topic>.md) | <1〜2 文の概要> | 未着手（検討段階・<起票経緯の短い出所>）|
   ```

4. **報告**: 起票したファイルパスと INDEX 行をユーザーに提示する。

## ファイル書式

```markdown
# idea_NN_<topic_snake_case>.md

## 概要

（何をしたいか 2〜4 行。**太字**で要点）

## 起票経緯（YYYY-MM-DD）

（出所: ユーザー要望 / phase NN task_NN の実機目視 / reviewer 指摘 / 設計議論からの分離 等。
分離元がある場合はリンクする）

## 現状

（現実装・現仕様がどうなっているか。関連ファイル / 正本仕様の該当節を挙げる）

## 提案（方向性・要設計）

（実現案。複数案あるなら列挙。ここは検討メモであり確定仕様ではない）

## 想定スコープ

（含む / 含まない、影響レイヤ、仕様変更の有無の見込み）
```

- タイトル行 = ファイル名（既存 idea と同形式）。
- 設計が詰まっている場合（暫定仕様書ドラフト級）は §構成のまま置いてよいが、
  状態に「暫定仕様書ドラフト済」と明記する。

## 状態の運用（INDEX.md / INDEX_done.md）

- 起票時 = `未着手（検討段階・<出所>）`
- 着手時 = `**着手**（→ 暫定仕様 [NN](../history/NN_<topic>.md) / phase [NN_<topic>](../phase/NN_<topic>/phase.md)）` へ書き換え（行は INDEX.md に残す）
- 完了時 = `**完了**（<phase> フェーズ YYYY-MM-DD・正本反映済 → 参照リンク）` にした上で、
  行を `INDEX_done.md` へ**移動**する（フェーズ完了時の正本反映タスクに含める。
  `.claude/rules/task_execution.md`「フェーズ完了時」参照）
- 対応不要が確定 = `**クローズ（対応不要・YYYY-MM-DD）**: <判定理由>` にして
  `INDEX_done.md` へ移動（理由を必ず残す）
- 保留 = 判定理由を状態列に残して INDEX.md に残す

## 禁止事項

- 採番を INDEX の表から取ること（フォルダ実体が正）
- idea 起票を理由にその場で実装へ着手すること（着手はフェーズ / タスク起票後）
- 仕様変更を伴うネタで `.claude/rules/spec_change_workflow.md` を無視した確定的記述を
  書くこと（idea 段階の記述は提案・検討メモに留める）
- 既存 idea と重複するネタの新規起票（既存があれば追記 / 状態更新で対応）
