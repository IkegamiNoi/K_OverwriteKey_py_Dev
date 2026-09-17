# decisions_archive / phase 19: フル表示ヘッダの幅をウィンドウ最小幅に含める

対応表: phase 19 / 暫定仕様 17（**凍結済・v0.3**）/ decisions 19。
起票元: [idea_21](../../../instructions/backlog/INDEX_done.md)（phase 18 task_05 の実機目視・ユーザー 2026-09-17）。
完了 2026-09-17。**presentation 限定・JSON の形は不変**（`full_view_window_width` の書き込み契機を 1 つ追加）。
正本 = `features.md` §4.6「フル表示の幅配分」/ `data_schema.md` §5.4 / `codebase_map.md`。

## 問題

フル表示のヘッダ（フック | 表示 | ファイル）はウィンドウを狭めると切れる。phase 18 のウィンドウ最小幅はメイン領域だけから算出していた。
実測では標準フォント・既定幅 780 でもヘッダは要求幅より 10px 狭く、取得中は取得ボタンが約 45px 広がってさらに切れていた。

## 確定した設計判断

| # | 判断 | 採らなかった案と理由 |
|---|---|---|
| 1 | **ウィンドウ最小幅 = max(メイン, ヘッダの要求幅)**・配置は変えない（案 A） | 案 B（狭いときに折り返す等の配置変更）= 配置設計と見た目の確認が大きい |
| 2 | **画面超過の縮小目標 = max(画面幅, ヘッダ幅)**。両方が超えるときも無駄に縮めない | 画面幅だけを目標 = ヘッダより狭くなるまで両端を縮めても無駄 |
| 3 | **ドラッグ後の最小幅は縮小規則を通さず実際の表示幅から**（確定前 Codex 敵対的レビュー） | `resolve_layout` を通す = 画面幅より広いウィンドウで実表示より小さい最小幅を当てる |
| 4 | **フル表示ヘッダの切替ボタン 4 つを最大文言幅で固定**。幅 = `ceil(max(measure)/measure("0"))`・担当は各ボタンの制御側・フォント変更時は幅配分の再計算より前 | 実測ループで文言を仮に切り替える = 取得中 / フック ON 中に戻す文言が不定（起票時 deep-reviewer）|
| 5 | **省略表示のボタンは固定しない** | 固定すると幅 270 で標準フォントでも常に約 6px 切れる（実測） |
| 6 | **文言定数は中立なモジュール `hook_button_texts.py`** | controllers に置く = views → controllers の import が生まれる |
| 7 | **ドロップダウン 18 → 12（フル・省略の両方）**（ユーザー） | フルのみ |
| 8 | **起動時にヘッダに合わせて広がることを受容**（標準 +19px・＋3 で約 +223px。保存値なしなら保存しない） | 取得ボタンの文言を短くする = 文言変更がスコープ外 |
| 9 | **旧保存値が最小幅未満なら起動時に広げた幅で保存値を更新**（ユーザー・推奨「受容」と異なる選択）。切り詰め前の値で比べる | 受容（起動のたびに広がり保存値は古いまま）|

## フェーズ中の追加判断

### 【起票】レビューと実測の訂正

- 起票時 `deep-reviewer`（修正して採用）: メインの実測表が**取得中の状態**で測られていた（`header_area` の要求幅は idle 処理後にしか変わらない）→ 標準の不足 55 → 10px・起動時の拡幅 835 → 799px に訂正。
- 確定前 `codex-adversarial-reviewer`（中 1）: 表 #3。

### 【task_03】テスト基盤の修正（メイン・タスク定義外）

- `test_full_view_panes._restore_layout`: トリガー一覧が要求幅より広い状態で同じ座標へ `sash_place` すると Tk がサッシュを 59px ずらす（433 → 492）→ 位置が同じなら置き直さない。
- `WindowWidthPersistenceTest`: 実時間 500ms の保存予約が負荷下でテスト中に発火 → 遅延定数を patch で延ばし開始時に取消。
- reviewer = 採用。**運用指摘: タスク定義で「直さず報告」とした失敗は、修正前にユーザーへ報告する**。

### 【task_05】二次レビューの採否（ユーザー・推奨どおり）

- `codex-reviewer` = 指摘なし / `deep-reviewer` = 完了可。
- 採用 → task_06: 正本 `features.md` の「画面幅超へ広げない」「既定幅は保存しない」「自動で決めた幅は保存しない」を表 #2・#9 と両立する文へ / 新規モジュールの `codebase_map.md` 記載 / 境界（保存値 > 画面幅でも最小幅未満なら書く）の注記。
- 採用 → task_05b: 上記境界の単体テスト。周知: 大きいフォントで起動すると広げた幅が保存値に残る。
- 保留 → refactor_check 候補: 保存値検証の重複 / ドロップダウン幅定数の置き場所 / 2 モジュールで保存予約の遅延を延ばしていない。
- 実機目視 1〜8: すべて OK。

### 【task_06】完了判定前レビューの採否（ユーザー 2026-09-17・推奨どおり）

- `reviewer`（正本反映の整合）: 文言の省略 1 件（「通常トリガー有効化」）→ 修正。`deep-reviewer`（修正要・軽微）/ `codex-adversarial-reviewer`（中 1）。
- 採用（文書のみ）: 「ヘッダの要求幅」= ウィンドウ幅換算（余白込み）と正本で定義 / `data_schema.md` §5.4・`features.md` の「画面幅より広い保存値は画面幅で開く（書き換えない）」に最小幅と起動時更新の例外を明記（Codex と同じ指摘）/
  起動時更新の書き込み失敗は再試行せず次回起動時に同じ条件で書く / `codebase_map.md` の「平均文字幅」→「0」1 文字の幅。
- **暫定 17 §7 の予定からの逸脱**: `data_schema.md` は「変更なし」の予定だったが、§5.4 の書き込み契機の列挙と食い違うため 1 文追記した（JSON の形・検証は不変）。
- 除外: UI テストの自己参照アサーション（実幅は別テストで検査済み）。

## refactor_check（2026-09-17）

- **判定: 推奨**（PHASE_BASE = `9b95192`・`keyseq/` 13 ファイル・+159 / -25）。M3 = `pane_layout_controller.py` の測定 2 行の組が 3 箇所。M1 / M2 / M4 / M5 / M6 非該当。
- 提案書 [10](../../../instructions/modified_proposal/10_refactor_full_view_header_width.md)（項目 1 = `_measure()` へ集約 / 項目 2 = 保存幅の有効判定を 1 箇所へ）。
- ユーザー選択 = **(a) phase 19 の task_07 として実施**（変更が小さいため）。安全網 = 新規の特性テストを足さず、**変異検査**（ヘッダ測定の削除 → tests_ui 4 件失敗 / `raw >= 0` → tests 2 件失敗）で既存テストの検出力を確認。
- 候補送り（`current.md` 別タスク化候補）: `KEYBOARD_LAYOUT_COMBO_WIDTH` の置き場所 / tests_ui 2 モジュールの保存予約遅延 / `hook_controller.py` の 2 行の同型。

## 実装の要点

- `pane_width_rules.py`: `resolve_layout(..., header_window_width=0)` / `window_min_width_after_drag` / `startup_window_width_to_save`。
- `button_width_rules.py`（新規）: `fixed_button_width_chars`。`controllers/button_width.py`（新規）: `apply_fixed_button_width`。`hook_button_texts.py`（新規）: 文言・ドロップダウン幅。
- `controllers/pane_layout/`: `measure_header_window_width` / `header_window_width` の保持 / 起動時の保存値更新。
- `HookController.register_hook_buttons(..., fixed_width=)` / `SingleKeyCaptureController.apply_fixed_button_width` / `App._apply_fixed_button_widths`。

## テスト

- `tests/test_pane_width_rules.py`（ヘッダ幅・ドラッグ後・起動時更新）/ `tests/test_button_width_rules.py` /
  `tests_ui/test_header_button_widths.py` / `test_full_view_header_width.py` / `test_pane_window_width_persistence.py`（起動時更新 2 クラス）+ 既存 3 モジュールの期待値見直し（暫定 §5-9 の列挙のみ）。
- 最終: `tests` 451 OK（skip 7）/ `tests_ui` 427 OK / smoke OK。

## 受容した制約・残件

- ヘッダの要求幅が画面幅を超える場合はウィンドウがはみ出す（保証の範囲外）/ 長い表示名のレイアウトはドロップダウンで切れる / 大きいフォントで起動すると広げた幅が保存値に残る。
- ヘッダの測り直しはフォント変更時だけ（ヘッダに可変の文言が増えたら見直す）。
- [idea_22](../../../instructions/backlog/idea_22_full_view_min_height.md)（縦方向の最小サイズ）は未着手。
