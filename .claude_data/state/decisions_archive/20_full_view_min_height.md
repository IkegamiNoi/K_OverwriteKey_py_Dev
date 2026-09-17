# decisions_archive / phase 20: フル表示ウィンドウの縦方向の最小サイズ

対応表: phase 20 / 暫定仕様 18（**凍結済・v0.5**）/ decisions 20。
起票元: [idea_22](../../../instructions/backlog/INDEX_done.md)（phase 18 task_05 の実機目視・ユーザー 2026-09-17）。
完了 2026-09-18。**presentation 限定・JSON 不変**（高さは保存しない）。
正本 = `features.md` §4.6「フル表示の幅配分」の「最小の高さ」項 / `codebase_map.md`。

## 問題

フル表示のウィンドウは縦にいくらでも縮められ、一覧・ボタン列・ステータス欄が潰れた（phase 18 の `wm minsize` は高さ 1）。

## 確定した設計判断

| # | 判断 | 採らなかった案と理由 |
|---|---|---|
| 1 | **基準 = 一覧を既定の半分の行数（6 / 6 / 9）にしたときの高さ**（ユーザー） | 固定ピクセル = 大きいフォントで一覧が潰れる |
| 2 | **案 A: 一覧の `height` 自体を 6 / 6 / 9 にし、最小の高さ = ウィンドウの要求高さ**（ユーザー） | v0.1 の「式で求めた値を minsize に当てる」= pack は後置から削り expand の一覧は縮まないため、ステータスバー・ボタン列が切れる（起票時 deep-reviewer 実測）/ 案 B（pack 順を変える）= 変更ファイルが多く配置順の検証が要る |
| 3 | **高さは保存しない・省略表示では解除**（ユーザー） | 高さも保存 = JSON 変更でスコープ拡大 |
| 4 | **画面の高さ超過ははみ出しを受容**（幅と同じ・ユーザー） | 画面の高さで打ち切る = ボタン列等が切れる |
| 5 | **一時メッセージは 1 行分で測り、最小付近での複数行表示の切れは受容**（確定前 Codex 敵対的レビュー → ユーザー） | 表示のたびに測り直す = 窓が伸びて戻らない / 1 行にまとめる = 既存表示の変更 |
| 6 | **フル表示へ戻るときは表示内容の更新後に測る**（`show_full_view` 末尾で `on_full_view_shown`） | 更新前に測る = 省略表示の 2 行ステータスで +17px 高く当たる（起票時 deep-reviewer）|
| 7 | **一時メッセージのラベルは測定側で textvariable から探す**（App に属性を足さない） | App 属性で参照 = phase 01 で解消した「生やし」に戻る（task_03 指摘 4 = 保留）|
| 8 | **自動で広げた高さは最小が下がっても縮めない**（task_03b: 測定直後に normal かつ最小未満なら `geometry(幅x最小)` / task_04b: 最小が下がるときも下げる前に現在の高さを geometry で確定 = 最大化の解除で広がった高さも縮めない） | minsize だけに任せる = Tk の記憶する高さ（820 等）へ縮む（task_03 deep-reviewer 指摘 1・完了判定前 Codex medium / deep-reviewer 指摘 3・いずれもメイン再実測）|

## フェーズ中の追加判断

### 【起票】暫定仕様 18（v0.1 → v0.5）
- 起票時 `deep-reviewer`（修正して採用・実測）: 上表 #2・#6 / `tk.PanedWindow` の要求高さは `paneconfigure` まで古い → 両端の幅の適用後に測る / メニューバー込みでも `minsize`・`geometry`・要求高さは同じ基準。
- 確定前 `codex-adversarial-reviewer`（medium 1）: 上表 #5。
- `/phase_start` 整合チェック（reviewer）= 採用。

### 【task_03】二次レビューの採否（ユーザー 2026-09-18）
- `codex-reviewer` = 指摘なし / `deep-reviewer` = 修正要（中 1）。
- 採用 → task_03b: 指摘 1（上表 #8）/ 2（拡大後に最小が下がっても維持するテスト）/ 3（枠内の子の実高さ ≥ 要求高さ）/ 6（変数名）。変異検査で `test_font_growth_expands_only_below_minimum` が検出。
- 採用・文書のみ → task_04: 指摘 5（`show_full_view` の呼び出し順を正本・codebase_map に記述）。
- 保留: 指摘 4（上表 #7）。
- 実機目視 1〜5: すべて OK。

### 【task_04】完了判定前レビューの採否（ユーザー 2026-09-18）
- `codex-adversarial-reviewer`（needs-attention・medium 1）= `deep-reviewer` 指摘 3 と同じ: 最大化中に最小が上がり、解除で Tk が広げた高さが後で縮む
  （メイン実測: 1200x820 → 最大化 → ＋3 → 解除 844 → 標準 820）→ **修正**（task_04b `ba31614`・変異検査で追加テストが検出）。
- `deep-reviewer`（修正要・軽微）→ 推奨どおり。採用 = 1 refactor_check の再判定の記録（下記）/ 2 smoke を task_04b 後に再実行（OK）/ 4 凍結ヘッダの文言 /
  5 正本「フル表示へ戻るたびに測る」/ 6 codebase_map に `apply_layout` 前半の高さの扱い / 9 保留を current.md「別タスク化候補」へ。
  除外 = 7（最小化中の規定はテストなし・実装と一致）/ 10（docstring）/ 11（起動時の拡大は実機目視で担保）/ 12（820 の定義）。
  対応不要 = 8（空ラベルと 1 行ラベルの要求高さは task_03 レビューで実測済み・一致）。

## refactor_check（2026-09-18）

- **判定: 不要**（PHASE_BASE = `5e25218`・判定時点 = task_03b 後の `keyseq/` 6 ファイル・+43 / -8。task_04b の +6 行でも結論は変わらない）。M3 候補（minsize 3 箇所 / measure_* 3 関数 / 一覧 height 3 箇所）は保持値の参照・別の測定・枠ごとの値で同型コピーに当たらない。M6 候補（`window_min_height = 1` と `minsize(1, 1)`）は Tk の「制約なし」の値で共有定数の対象外。M1 / M2 / M4 / M5 非該当。
- Phase 18 の候補送り（`pane_layout_controller.py` が増えたらウィンドウ幅の保存を分ける再判定）: 256 → 約 280 行。高さの処理は `apply_layout` 内の数行と属性 1 つで独立したまとまりではない → **分割不要と再判定**。

## 実装の要点

- View: `keymap_box.py` / `trigger_box.py` = `height=6`、`sequence_box.py` = `height=9`。
- `controllers/pane_layout/pane_measure.py`: `measure_window_min_height`（要求高さ − 一時メッセージの押し上げ分）/ `_find_flash_message_label`。
- `pane_layout_controller.py`: `window_min_height` の保持 / `apply_layout` 末尾で測定 →（normal かつ「最小未満」または「最小が下がる」なら）geometry で高さを確定 → minsize / ドラッグ後の minsize にも適用。
- `app.py`: `show_full_view` の `on_full_view_shown` を末尾へ。

## テスト

- `tests_ui/test_full_view_min_height.py`（新規 10 本: 切れない判定・フォント変更・拡大と維持・ドラッグ後・省略表示往復・保存しない・一時メッセージ・ステータス 1 行での測定・戻ったときの拡大）。
- task_04b で 1 本追加（最大化の解除で広がった高さ）= 計 11 本。
- 最終（task_04b 後）: `tests` 451 OK（skip 7）/ `tests_ui` 438 OK / smoke OK。

## 受容した制約・残件

- 最小の高さが画面の高さを超える場合ははみ出す / 最小付近で複数行の一時メッセージが出ると 4 秒間下側が切れる / 大きいフォントでは起動時に 820 より高く開く（保存しない）。
- 最小の高さを決めるのは実測では全フォントで出力シーケンスのボタン列（キーマップ管理・トリガー一覧は最小でも 6 行より多く見える）。
