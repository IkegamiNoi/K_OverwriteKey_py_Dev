# phase.md

## フェーズ名

キーボードUIのウィンドウ改善（keyboard_ui_window）

## フェーズの目的

キーボードUI（`KeyboardWindow`）を、スペースを取らず・前面に置け・大きさを変えても空白が出ない窓にする
（ステータス欄の削除とタイトル表示 / 「キーボードUIを常に手前」とダイアログ表示中の一時解除 / リサイズの縦横比固定）。
**presentation 層のみ（前面の窓の判定は既存の infrastructure を再利用）。JSON スキーマ変更なし（前面化の状態は保存しない）。**

- 起票元: ユーザー要望（2026-10-12）。
- 主入力（暫定仕様）: [39_keyboard_ui_window.md](../../history/39_keyboard_ui_window.md)（v0.3・ユーザー確定済 2026-10-12）
- モード: **暫定仕様先行モード**。番号対応: phase 55 / 暫定 39 / decisions 55。

## 確定（ユーザー 2026-10-12）

暫定 39 §2 の 1〜3 が正（本書に再掲しない）。要点: ステータス欄を削除しタイトルへ（通常 = レイアウト名 / 編集中 = キーと Esc の案内）/
表示欄に「キーボードUIを常に手前」（保存しない・閉じていても操作可・両方手前ならアクティブが上・ダイアログが前面の間は一時解除〔前面の窓の監視〕）/
縦横比固定（手を離して約 150ms 後に 1 回補正・斜めは今の大きさに収まる最大の形・比率が変わったときだけ当て直す・スナップ後の補正は受容）。

## スコープ

### 含む

- 暫定 39 §3〜§5 の実装とテスト（タイトル表示 / 縦横比固定の純関数と補正 / 前面化と一時解除）
- 所有関係の前提の実測（暫定 39 §4。成り立たなければ止めてユーザー確認）
- 実機目視（暫定 39 §6 の 5・7・8・10）
- 正本反映（暫定 39 §8）

### 含まない（後送り）

- 暫定 39 §7 のとおり（前面化・大きさの保存 / 凡例の別表示 / 配色の変更 / WM_SIZING 方式 / ダイアログ側の変更）

## このフェーズで読むファイル

1. `instructions/history/39_keyboard_ui_window.md`（全体）
2. `keyseq/presentation/keyboard_window.py`（全体・375 行）
3. `keyseq/presentation/controllers/layout_controller.py`（:36-80 開閉・`refresh_keyboard_window`）
4. `keyseq/presentation/ui_vars.py`・`keyseq/presentation/views/full_view/display_frame.py`・`keyseq/presentation/views/compact_view/display_frame.py`・`keyseq/presentation/app.py`（:543 `_apply_always_on_top`）
5. 前面の窓の判定: `keyseq/infrastructure/input_gateway.py`（:85-120 付近・phase 53）と、その presentation への供給経路（phase 53 の `codebase_map.md` 記載）
6. 純関数の前例: `keyseq/presentation/compact_window_size.py`
7. テスト: `tests_ui/test_app_ui_flows.py`（:2324 `test_keyboard_window_opens_and_closes`）
8. 正本: `instructions/common/spec_detail/features.md` §4.6（UI 構成・省略表示のウィンドウ・モーダルダイアログの作法）/ `codebase_map.md`（:593・:604・LayoutController）

## タスク

- task_01: ステータス欄の削除とタイトル表示（暫定 39 §3・§6 の 1・2）とテスト — **完了**（2026-10-12・codex-implementer・reviewer 採用・tests 1529 / tests_ui 946 / smoke pass・実機目視は task_02 でまとめて）
- task_02: 縦横比固定（純関数モジュール + `<Configure>` 補正 + `update_layout` の比率判定・暫定 39 §5・§6 の 8〜10）と単体テスト。**実装後にユーザーの実機目視**（§6 の 8・10） — **完了**（2026-10-12・codex-implementer・reviewer 採用・初回目視でリサイズが意図とずれる NG → task_02b で修正後にユーザー実機目視 OK〔§6 の 1・2・8・10〕）
- task_02b: task_02 の実機目視 NG（縮めると大きく・広げると小さく）への修正 = マウスのボタンが押されている間は補正しない（暫定 39 v0.4 §5・infrastructure に `is_mouse_button_down`）。task_02 と合わせて実機目視 — **完了**（2026-10-12・codex-implementer・reviewer 採用・Codex が消した BOM 2 件をメインで復元・tests 1542 / tests_ui 949 / smoke pass・Codex 敵対的レビュー〔v0.4〕の 2 件はユーザー判断で受容として §5 に明記）
- task_03: 「キーボードUIを常に手前」とダイアログ表示中の一時解除（暫定 39 §4・§6 の 3〜7・11）と UI テスト。着手時に所有関係の前提を実測。**実装後にユーザーの実機目視**（§6 の 5・7） — **完了**（2026-10-12・所有関係は probe で None〔前提成立〕・codex-implementer・reviewer 採用・表示欄の行追加で `test_compact_sequence_view` の固定高さ 820 が足りず 860 へ〔メイン・行を外すと 820 で通ることを実測〕・初回目視でダイアログが覆われる NG → task_03b 修正後にユーザー実機目視 OK〔§6 の 3〜7・11〕）
- task_03b: task_03 の実機目視 NG（一時解除でキーボードUIがダイアログを覆う）への修正 = 外した直後にダイアログの直下へ置く（暫定 39 v0.5 §4・infrastructure に `place_window_below`）。task_03 と合わせて実機目視 — **完了**（2026-10-12・HWND_NOTOPMOST で非 topmost 最上位へ来ることを probe で確認・codex-implementer・reviewer 採用・tests 1550 / tests_ui 953 / smoke pass・ユーザー実機目視 OK）
- task_04: 統合確認（tests / tests_ui / smoke・deep-reviewer + codex-reviewer）
- task_05: 正本反映（暫定 39 §8 の昇格・凍結）・`decisions_archive/55_keyboard_ui_window.md`・decisions.md の索引・current.md の完了記載・`/refactor_check`

## レビュー方針

- 各タスク: `reviewer`（5 観点）・既存テスト（tests / tests_ui / smoke）の通過を完了条件に含める
- 重点: **補正が振動・再入しない**（予約 1 件・収束・`event.widget is self`・zoomed / iconic）/ 設定反映で大きさが変わらない /
  前面化の実効値（チェック ∧ ¬一時解除）が全経路（ボタン・メニュー・既存窓の再表示・チェック変更）で当たる / 監視タイマーが条件外・破棄で止まる /
  presentation から ctypes を直接呼ばない / 表示欄の行追加で既存の窓サイズ規定が崩れない
- 統合確認（task_04）: `deep-reviewer` + `codex-reviewer` / 完了判定前（task_05）: `deep-reviewer` + `codex-adversarial-reviewer`
- 実機目視（ユーザー）: task_02・task_03
