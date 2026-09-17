# task_06_spec_promotion

## 目的

phase 19 の最終タスク（正本反映）。暫定仕様 17（v0.3）§7 と task_05 二次レビューの採用分に従い、
①`features.md` §4.6「フル表示の幅配分」へ昇格（**`:62` / `:65` / `:70` の矛盾解消**・境界の注記・`:77` の削除を含む）
②`data_schema.md` §5.4 の `full_view_window_width` の書き込み契機へ「起動時の保存値更新」を追記（JSON の形・検証は不変）
③`codebase_map.md` へヘッダ測定・ボタン幅固定・新規 3 モジュールを追記 ④**暫定仕様 17 を凍結** ⑤フェーズ完了処理。
**文書作業のみ。コード・テスト不変。**

## 対象範囲（文書限定）

1. `instructions/common/spec_detail/features.md` §4.6「フル表示の幅配分」:
   - ウィンドウ最小幅 = max(両端の表示幅 + トリガー一覧の最小幅, **ヘッダの要求幅**)。ヘッダはフォント設定ごとに測り直す。ドラッグ後の最小幅は実際の表示幅から（縮小規則を通さない）。
   - 収まらない場合の縮小目標 = max(画面幅, ヘッダから求めた幅)。**`:65`「途中でウィンドウを画面幅超へ広げない」を、ヘッダが画面幅を超える場合ははみ出す（保証の範囲外）と両立する文へ**。
   - **`:62`「既定幅は保存しない」/ `:70`「自動で決めた幅は保存しない」に、起動時の保存値更新の例外**（有効な保存値が最小幅未満で起動時に広げたら書く。切り詰め前の値で比べる = 保存値 > 画面幅でも最小幅未満なら書く）と周知（大きいフォントで起動すると広げた幅が残る）。
   - 標準フォントでも起動時にヘッダに合わせて 780 より広く開く（保存値が無ければ保存しない）。
   - フル表示ヘッダの切替ボタン 4 つの幅固定（省略表示は固定しない）/ キーボード選択のドロップダウンは幅 12（両表示）。
   - `:77`「ヘッダの切れは対象外」を削除。
2. `instructions/common/spec_detail/data_schema.md` §5.4 `full_view_window_width` の書き込み契機に起動時の更新を 1 文追記。
3. `instructions/common/codebase_map.md`: ツリー（`hook_button_texts.py` / `button_width_rules.py` / `controllers/button_width.py` / `pane_measure.py` の説明）/
   PaneLayoutController 節（ヘッダ測定・保持・縮小目標・ドラッグ後の最小幅・起動時の保存値更新）/ HookController・SingleKeyCaptureController（幅固定）/
   App の `_apply_fixed_button_widths` の呼び出し順 / 登録方式の一覧（`register_hook_buttons(..., fixed_width=)`）。
4. `instructions/history/17_full_view_header_width.md` のヘッダを凍結（本文は変更しない）。
5. フェーズ完了処理: `decisions_archive/19_full_view_header_width.md` 作成・`decisions.md` の phase 19 節を移設し索引へ 1 行 /
   `current.md` 完了記載（次採番 phase 20 / 暫定 18 / decisions 20）/ idea_21 を `INDEX_done.md` へ /
   **`/refactor_check`**（保留 3 件 = 保存値検証の重複・ドロップダウン幅定数の置き場所・2 モジュールの保存予約遅延を候補に）/
   **完了判定前レビュー** `deep-reviewer` + `codex-adversarial-reviewer`（縮退しない）。

## 読むファイル

- `features.md:43-78` / `data_schema.md:59-75` / `codebase_map.md:40-110,180-270,300-315`
- 暫定仕様 17 §2・§3・§6・§7 / `tasks/task_05_integration_check.md` の採否
- 手本: `decisions_archive/18_full_view_resizable_panes.md` / phase 18 `tasks/task_06_spec_promotion.md`

## 含まない

- コード・テストの変更 / main へのマージ（ユーザー）/ idea_22

## 確認

- 正本の各条項の根拠となる実装行をメインが照合し、完了報告に対応表を載せる。
- リンク実在（暫定 17 ヘッダ → archive 19 / INDEX_done の idea_21 行）/ INDEX.md に idea_21 行なし / decisions.md に phase 19 節なし・索引に 19。
- `git diff --stat` が文書のみ。
- `/refactor_check` の判定と、完了判定前レビューの結果・採否を完了報告に含める。

## 完了条件

- 上記確認・**`reviewer` 採用**（正本反映の文面と実装の整合確認に限定）・完了判定前レビューの指摘をユーザーが採否判断済み。実機目視は不要。

## 完了記録（2026-09-17）

- 正本反映: `features.md` §4.6「フル表示の幅配分」（用語「ヘッダの要求幅」= ウィンドウ幅換算 / 最小幅 = max(メイン, ヘッダ) / 縮小目標 / ドラッグ後の最小幅 / 起動時の拡幅 /
  旧文言 3 箇所の矛盾解消 / 起動時の保存値更新の例外・境界・失敗時 / ボタン幅固定 / ドロップダウン幅 / ヘッダ切れの行を削除）/ `data_schema.md` §5.4（書き込み契機と画面幅の例外）/
  `codebase_map.md`（新規 3 モジュール・ヘッダ測定・幅固定の担当と呼び出し順）。暫定仕様 17 を v0.3 で凍結。`decisions_archive/19` 作成・`decisions.md` から移設。idea_21 を `INDEX_done.md` へ。
- **正本と実装の対応**（`reviewer` が条項ごとに根拠行を確認）: 最小幅 max = `pane_width_rules.py` `resolve_layout` / 縮小目標 = 同 `target = max(screen_width, header_window_width)` /
  ドラッグ後 = `window_min_width_after_drag`・`pane_layout_controller.py` `_update_window_min_size` / 起動時更新 = `startup_window_width_to_save`・`apply_initial_widths` 末尾 /
  ボタン幅固定 = `hook_controller.py` `register_hook_buttons`・`full_view/hook_frame.py` `fixed_width=True` / ドロップダウン = 両 `display_frame.py` の `KEYBOARD_LAYOUT_COMBO_WIDTH` / 呼び出し順 = `app.py` `_apply_font_delta`。
- `/refactor_check` = **推奨**（M3: 測定の 2 行が 3 箇所）→ 提案書 10 → ユーザー選択 (a) で **task_07 として実施済み**（変異検査で安全網を確認）。
- 完了判定前レビュー: `deep-reviewer`（修正要・軽微）+ `codex-adversarial-reviewer`（中 1）+ `reviewer`（文言 1 件）→ ユーザー採否（推奨どおり）: 文書 A〜E 反映 / F 除外。詳細は `decisions_archive/19`。
