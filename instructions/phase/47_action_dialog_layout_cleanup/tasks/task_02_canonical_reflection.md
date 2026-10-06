# task_02_canonical_reflection

## 目的

phase.md「確定」1・2・4 を正本へ反映し、phase 47 を閉じる（直接改訂モード・`.claude/rules/task_execution.md`「フェーズ完了時」）。**文書作業のみ（メイン）・コード不変**。

## 対象範囲

- 正本 `features.md` §4.6「出力シーケンスの編集」へ追記
  - 確定 1: 種別ごとの表示（値 = hotkey / text のみ・「キー入力で記録」と説明文 = hotkey のみ・プリセットの枠と「プリセット編集…」= hotkey のみ。使わない項目はグレーでなく非表示）
  - 確定 2: 「末尾に追加」の位置を種別のドロップダウンと同じ行の右端（既存の「末尾に追加」条項へ追記・挙動は不変）
  - 確定 3: 種別の切替でダイアログの高さが伸び縮みする（高さは固定しない）
  - 確定 4: 開いたときの入力先（値欄 / 無ければ種別のドロップダウン / `edit_loop` はループ回数の欄・「無限」ON ならそのチェック）。非表示の欄にフォーカスがあれば種別のドロップダウンへ移す
  - 「モーダルダイアログの作法」（ダイアログごとの入力先の一般形）は改訂しない
- `codebase_map.md` の `action_dialog.py` 行（表示切替 `_sync_capture_ui` → `_sync_type_visibility` / `_sync_hotkey_controls` / `_sync_mouse_visibility`・初期フォーカス `_initial_focus_widget`）
- フェーズ完了判定前レビュー（deep-reviewer + codex-adversarial-reviewer）と指摘の対応
- `decisions_archive/47_action_dialog_layout_cleanup.md` / decisions.md のアーカイブ索引 / current.md の完了記載（次採番 = phase 48 / decisions 48）/ `/refactor_check`
- 起票元 idea: なし（ユーザー要望 2026-10-06）

## 読むファイル

- `instructions/phase/47_action_dialog_layout_cleanup/phase.md`（確定・task_01 の完了記載）
- `.claude_data/state/decisions.md` の phase 47 節（あれば）
- `features.md` §4.6「出力シーケンスの編集」（:527-）・`codebase_map.md` :100-106
- `keyseq/presentation/dialogs/action_dialog.py:380-460`（表示切替・初期フォーカスの実体の確認）

## 含まない

- コードの変更（レビューで修正が要る場合は枝番タスクを起票する）
- phase.md「含まない」（高さ・幅の固定 / 並びの全面見直し / 他ダイアログの整理）

## 確認

- 正本 §4.6 が確定 1〜4 を漏れなく含み、実装（`action_dialog.py`）と食い違わない（レビューで照合）
- 正本に「使わない項目はグレー」と読める旧記述が残っていない

## 完了条件

- 上記をすべて実施し、レビュー 2 種の結果と `/refactor_check` の判定を完了報告に含める（文書のみのため reviewer は deep-reviewer で代える）。
- 実機目視: なし（task_01 で実施済み・2026-10-06 ユーザー OK）。
