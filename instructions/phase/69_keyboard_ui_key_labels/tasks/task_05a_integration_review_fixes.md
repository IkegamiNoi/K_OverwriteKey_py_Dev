# task_05a_integration_review_fixes

## 目的

task_05 の統合レビュー（deep-reviewer）の指摘のうちユーザー確定分（2026-10-26）を直す: 指摘 1（保留中の当て直しが補正に化けて記録が書かれる）・指摘 3（tests_ui の検出力）・指摘 4（実 config に依存するテスト）。
**presentation のキーボードUI（`keyboard_window.py`）と tests_ui に限定。暫定 52 §8 の規則は変えない（実装を規則へ合わせる）。スキーマ不変。**

## 対象範囲

### `keyseq/presentation/keyboard_window.py`（指摘 1）

- 現状: 最小化 / 最大化中に `update_layout` で別レイアウトへ切り替える → `_size_base = (目標の幅, 下限の高さ)`・`_ratio_pending = True`。
  通常へ戻ると `_on_window_configure`（suspended 分岐）または `_on_window_map` が `_schedule_pending_ratio()` を予約する。
  その後に Configure がもう 1 回来ると、`current != _size_base` なので保留のジョブを取り消して `_settle_size` を予約し、`_settle_size` が補正して `_record_settled_width` で**新しいレイアウトの記録を古い窓の幅で上書きする**（§8「自分が当てた大きさ（レイアウトの切替・比率の当て直し）では書かない」に反する）
- 直し方:
  - `_on_window_configure`: suspended でない通常の分岐で、`_ratio_pending` が立っている間は `_schedule_pending_ratio()` を予約し直して return する（`_settle_size` を予約しない）
  - `_settle_size`: `_ratio_pending` を解く経路（今の `if self._ratio_pending and self._ratio is not None:` の箇所）を通った場合は記録しない（`_record_settled_width` を呼ばない）。保留の当て直しは `_apply_pending_ratio` に任せる形でよい
- 保留が無い通常の利用者の操作の補正・記録は今どおり

### `tests_ui/test_app_ui_flows.py` ほか（指摘 1・3・4）

- 指摘 1 の回帰テスト: iconic で別レイアウト（記録の幅あり）へ `update_layout` → 通常の state で `_on_window_configure`（suspended 分岐）→ もう 1 回、異なる大きさの `_on_window_configure` → `_resize_job` が `_apply_pending_ratio` の予約である / `_apply_pending_ratio` で記録の幅から比率で決めた大きさの `geometry` / `on_width_settled`（または `write_startup`）が呼ばれない
- 指摘 3:
  - `tests_ui/test_keyboard_key_text.py` の `test_home_label_stays_on_one_line_at_unit_27`: 旧実装（Tk の自動の折り返し）でも通る形を直す。描いた主の文字の item について、`canvas.bbox` の高さが 1 行分（そのフォントの `metrics("linespace")` 程度・2 行分未満）であること、またはそのフォントで `measure("Home") <= 内側の幅` かつ item の `width` が 0 であることを確かめる
  - `test_keyboard_window_maximized_settle_does_not_save_width`: `_settle_size` を直接呼ぶ形（冒頭で return するだけ）をやめ、`_on_window_configure` 経由で「zoomed の Configure → 通常の state の最初の Configure（基準の取り直し）」で記録が呼ばれないことを確かめる形にする
- 指摘 4: `test_keyboard_window_switch_from_jis_to_us_tkl_uses_us_minimum` ほか、記録の有無に期待値が依存するキーボードUIのテストで、`self.app._startup_settings` をテスト用の dict に差し替える（`patch.dict` か、退避して addCleanup で戻す）。実 config の内容に左右されないこと

### 設計メモ / 制約

- 縦横比の補正（phase 55）の他の規則は変えない
- `write_startup` は今どおり必ず差し替え、実 `config/` に書かない

## 読むファイル

- `keyseq/presentation/keyboard_window.py:140-200`・`:274-420`（編集対象）
- `tests_ui/test_app_ui_flows.py:2500-2960`（キーボードUIの大きさ・記録のテスト）
- `tests_ui/test_keyboard_key_text.py`（編集対象）
- `instructions/history/52_keyboard_ui_key_labels.md` §5・§8

## 含まない

- deep-reviewer の指摘 5〜9（5 は task_06 の正本反映で文言を明確化・6〜9 は保留 / 除外）
- 実機目視の項目の追加（task_06 の定義に追記済み）

## 確認

- compileall clean / 追加・修正した tests_ui の単体 pass
- 指摘 3 の検出力: 修正後のテストが、旧実装の描き方（`width` を渡す・自動で折り返す）なら落ちることをコードの読みで説明できる
- tests 全体 / tests_ui 全体（1 本だけ）/ smoke pass・件数が減らない
- 実行後に worktree の `config/config.json` が生成されていない

## 完了条件

- 上記確認 pass・**reviewer 採用**
