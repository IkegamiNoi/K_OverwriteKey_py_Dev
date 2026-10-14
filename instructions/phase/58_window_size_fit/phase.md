# phase.md

## フェーズ名

画面サイズの調整（window_size_fit）

## フェーズの目的

小さい画面・大きいフォントでもウィンドウが画面に収まるようにする。フル表示の 3 枠（キーマップ管理 | トリガー一覧 | 出力シーケンス）を枠ごとに縦スクロールできるようにして最小の高さを下げ、
省略表示の上部の「フック」「表示」を Expander で畳めるようにし、ステータス欄のフックを ON / OFF / 一時停止 の 3 状態で先頭に出す。
**presentation のみ（views/full_view・views/compact_view・controllers/pane_layout・compact_window_controller・trigger_panel / keymap_panel のステータス）。domain / application は変えない。
JSON スキーマ変更あり（`config/config.json` に任意キー `compact_header_view`・無い / 不正なら両方開く・後方互換）。**

- 起票元: ユーザー要望（2026-10-14）。
- 主入力（暫定仕様）: [42_window_size_fit.md](../../history/42_window_size_fit.md)（v0.3・ユーザー確定済 2026-10-14）
- モード: **暫定仕様先行モード**。番号対応: phase 58 / 暫定 42 / decisions 58。

## 確定（ユーザー 2026-10-14）

暫定 42 §2・§8 が正（本書に再掲しない）。要点: フル表示の 3 枠を独立に縦スクロール・収まらない枠にだけスクロールバー / 下限 = メイン領域の今の最小の半分 /
各枠の最小幅にスクロールバーの幅を常に含める / 省略表示の「フック」「表示」を別々に Expander・開閉を保存・ウィンドウの大きさは変えない /
ステータス欄のフックは 3 状態・キーマップは名前だけ（一時メッセージの `get_active_keymap_text` は変えない）/ Tab の自動スクロールなし。

## スコープ

### 含む

- 暫定 42 §3〜§5 の実装とテスト（既存テストの期待の書き換えを含む・暫定 42 §9-10）
- 実機目視（暫定 42 §9 の 1〜6・8。フォント +3 で画面に収まること）
- 正本反映（暫定 42 §11）

### 含まない（後送り）

- 暫定 42 §10 のとおり（横スクロール / フル表示の上部の開閉 / 見出しへの状態の要約 / スクロール位置の保存 / Tab の自動スクロール / 省略表示のシーケンス欄・呼び出し先の枠の規則の変更 / キーボード表示のウィンドウ）

## このフェーズで読むファイル

1. `instructions/history/42_window_size_fit.md`（全体）
2. フル表示: `keyseq/presentation/views/full_view/`（`full_view.py`・`keymap_box.py`・`trigger_box.py`・`sequence_box.py`・`call_view_frame.py`）
3. フル表示の最小の幅・高さ: `keyseq/presentation/controllers/pane_layout/`（`pane_layout_controller.py`・`pane_measure.py`）・`keyseq/presentation/pane_width_rules.py`
4. スクロール領域の手本: `keyseq/presentation/screen_grid/grid_editor_panel.py`（phase 57 task_06b）
5. 省略表示: `keyseq/presentation/views/compact_view/`（`compact_view.py`・`hook_frame.py`・`display_frame.py`・`sequence_frame.py`）・
   `keyseq/presentation/controllers/compact_sequence_controller.py`（開閉・保存の手本）・`keyseq/presentation/controllers/compact_window_controller.py`・`keyseq/presentation/compact_pane_heights.py`（保存キーの手本）
6. ステータス: `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py`（`update_status`）・`keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py`（`get_active_keymap_text`）
7. 正本: `features.md` §4.6（フル表示の幅配分・最小の高さ・省略表示のウィンドウ・シーケンス欄）・ステータス欄の節 / `data_schema.md` §5.4 / `codebase_map.md`（フル表示・省略表示・ステータス）
8. テスト: `tests_ui/test_full_view_min_height.py`・`test_full_view_panes.py`・`test_full_view_header_width.py`・`test_pane_drag_and_window_min.py`・`test_compact_window.py`・`test_compact_sequence_view.py`・`test_status_tooltip.py`・`test_app_ui_flows.py`・`test_sequence_control_review_fixes.py`

## タスク

- task_01: ステータス欄のフックの 3 状態とキーマップの名前だけの表示（ステータス欄用の関数を分ける・OFF 優先・一時メッセージは不変）とテストの書き換え（暫定 42 §5・§9-8・9・10）
- task_02: 省略表示の「フック」「表示」の Expander（閉じ方・見出し・フォーカス）・`compact_header_view` の読み書き・開閉での最小の高さの測り直し（暫定 42 §4）と UI テスト。**実装後にユーザーの実機目視**
- task_03: フル表示の 3 枠のスクロール領域（共通の部品 1 つ・中身の窓の高さ・測り直しの契機・スクロールバーの出し入れと先頭へ戻す・ホイール）と最小幅の測り方を中身の Frame 側へ（**最小の幅・高さの値はこのタスクでは変えない** = Canvas の要求高さ・幅を中身の要求に合わせ、既存の最小の高さ・幅のテストが書き換えなしで通ることを完了条件にする・暫定 42 §3.1・§3.3 の測り方・§3.4）と UI テスト
- task_04: フル表示の最小の高さを下げる（H の測り方・`app.winfo_reqheight()` − PanedWindow + ceil(H/2)）と各枠の最小幅へのスクロールバーの幅の加算（暫定 42 §3.2・§3.3）・既存の最小の高さ / 幅のテストの書き換えと UI テスト。**実装後にユーザーの実機目視**（フォント +3 で画面に収まる・3 枠すべてにスクロールバーが出ても切れない）
- task_05: 統合確認（tests / tests_ui / smoke・deep-reviewer + codex-reviewer）
- task_06: 正本反映（暫定 42 §11 の昇格・凍結・`codebase_map.md` の更新）・`decisions_archive/58_window_size_fit.md`・decisions.md の索引・current.md の完了記載・`/refactor_check`

## レビュー方針

- 各タスク: `reviewer`（5 観点）・既存テスト（tests / tests_ui / smoke）の通過を完了条件に含める
- 重点: **今の最小の高さ以上では見た目と動きが今と同じ**（スクロールバーが出ない・一覧が伸びる）/ 測り直しで `<Configure>` の無限ループを作らない（値が変わったときだけ configure・結び付けは 1 つ・phase 57 の罠）/
  ホイールを `bind_all` で他の窓へ漏らさない・間隔欄の値が変わらない / `compact_header_view` が無い・不正でも起動しファイルを書き換えない・書くときは両方の値 /
  閉じた枠に見えないフォーカスを残さない / 一時メッセージの文言が変わらない
- 統合確認（task_05）: `deep-reviewer` + `codex-reviewer` / 完了判定前（task_06）: `deep-reviewer` + `codex-adversarial-reviewer`
- 実機（ユーザー）: task_02・task_04（task_03 は値を変えないため task_04 とまとめて見る）
