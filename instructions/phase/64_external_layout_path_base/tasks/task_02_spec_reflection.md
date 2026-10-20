# task_02_spec_reflection

## 目的

phase 64 の正本反映とフェーズ完了処理。§5.7 の規定は不変（task_01 は実装を仕様へ合わせた修正）のため、正本は孤児検出 §5.8.9 の理由の記述と codebase_map のみを更新する。
**文書のみ・コード変更なし。**

## 対象範囲（文書のみ）

- `instructions/common/spec_detail/data_schema/5_08_09_orphan_sweep.md:38-42`: 「既存の非対称（是正は idea_13）」を「phase 64 で統一済み・旧表記は移行しないので保護のため両基準を残す」へ
- `instructions/common/codebase_map.md`: パス系の節に外部レイアウトのパスの 3 経路（登録・読込・表示）と孤児検出の superset を 1 項
- `.claude_data/state/decisions_archive/64_external_layout_path_base.md` 作成・`decisions.md` の phase 64 節を移しアーカイブ索引へ 1 行
- `instructions/phase/current.md`: 完了記載・次採番（phase 65 / decisions 65）
- `instructions/backlog/INDEX.md` の idea_13 行を完了にして `INDEX_done.md` へ移動
- `/refactor_check` の判定記録
- 完了判定前レビュー（`deep-reviewer` + `codex-adversarial-reviewer`）

## 読むファイル

1. `instructions/phase/64_external_layout_path_base/phase.md`
2. `instructions/common/spec_detail/data_schema/5_08_09_orphan_sweep.md:30-50`
3. `instructions/common/codebase_map.md:871-886`
4. `.claude_data/state/decisions_archive/61_keyboard_ui_vk_to_scan_code.md`（書式の手本）

## 含まない

- コードの変更・§5.7 本文の変更
- 既存の壊れた JSON の移行（ユーザー判断で不要）

## 確認

- 正本の記述が task_01 の実装（`split_loading.py:559`・`layout_controller.py:185`・`:209`・`:304`・`reference_scan.py:204-216`）と一致
- リンク切れなし（idea_13 を INDEX_done へ移した後の参照）
- `/refactor_check`: `git diff 693f039..HEAD -- keyseq/` で M1〜M6 判定

## 完了条件

- 上記確認・**reviewer 採用**（フェーズ完了判定のため `deep-reviewer` + `codex-adversarial-reviewer`）。
- 実機目視: task_01 で実施済み（2026-10-21 ユーザー OK）。
