# phase.md

## フェーズ名

フル表示ウィンドウの縦方向の最小サイズ（full_view_min_height）

## フェーズの目的

フル表示のウィンドウを縦に縮めると一覧・ボタン列・ステータス欄が潰れる問題を解消する。
**一覧の `height` を既定の半分（6 / 6 / 9）にし、フル表示中のウィンドウの要求高さを `wm minsize` の高さとして当てる**。

**presentation 限定（View の `height` + `controllers/pane_layout/` + `app.py` の呼び出し順）。JSON スキーマ変更なし**（高さは保存しない）。

- 起票元: [idea_22](../../backlog/idea_22_full_view_min_height.md)（phase 18 task_05 の実機目視・ユーザー 2026-09-17）。
- 主入力（暫定仕様）: [18_full_view_min_height.md](../../history/18_full_view_min_height.md)（**v0.5・ユーザー確定済**）。
- モード: **暫定仕様先行モード**。番号対応: phase 20 / 暫定 18 / decisions 20。

## 確定（ユーザー 2026-09-17）

暫定仕様 18 §2 が正。要点のみ:

- 最小の高さの基準 = 一覧を既定の行数の半分（キーマップ管理・トリガー一覧 6 行 / 出力シーケンス 9 行）にしたときの高さ。フォント設定ごとに幅と同じ契機で再計算。
- **案 A**: フル表示の一覧の `height` を 12→6 / 18→9 に変え、ウィンドウの要求高さをそのまま最小の高さにする。
- 高さは保存・復元しない / 省略表示では適用しない（入るときに解除）/ 画面の高さを超える場合ははみ出しを受け入れる。
- ステータスバーの一時メッセージは常に 1 行分として測る（最小付近での複数行表示の切れは受容）。

## スコープ

### 含む

- `views/full_view/keymap_box.py`・`trigger_box.py`・`sequence_box.py`: 一覧の `height`（基準である旨のコメント）。
- `controllers/pane_layout/`（`pane_layout_controller.py` / `pane_measure.py`）: 最小の高さの測定（一時メッセージ 1 行分）・保持・`minsize` を当てる全箇所への適用・幅を変える `geometry` の高さ。
- `app.py`: `show_full_view` の `update_status` を測定より前へ（暫定 §3-4）。
- `tests_ui/`（新規。**実 `config/config.json` を書かない**）。
- 正本反映: `features.md` §4.6「フル表示の幅配分」/ `codebase_map.md`。

### 含まない（後送り）

- 高さ・位置・最大化状態の保存 / 省略表示の最小サイズ・一覧の行数 / 初期高さ 820 の変更 / ボタン列の配置変更 / 画面の高さに収める縮小規則。
- 複数行の一時メッセージでの測り直し（受容）。
- `data_schema.md` の変更（JSON 不変）。

## このフェーズで読むファイル

1. `instructions/history/18_full_view_min_height.md`（主入力・v0.5）
2. `keyseq/presentation/controllers/pane_layout/pane_layout_controller.py` / `pane_measure.py`
3. `keyseq/presentation/views/full_view/keymap_box.py` / `trigger_box.py` / `sequence_box.py` / `full_view.py`
4. `keyseq/presentation/views/status_bar.py` / `app.py` の `_build_ui`・`show_compact_view`・`show_full_view`・`_set_flash_message`（`rg -n` で位置特定）
5. `instructions/common/spec_detail/features.md` §4.6「フル表示の幅配分」/ `codebase_map.md` の PaneLayoutController 節
6. 既存テストの型: `tests_ui/test_pane_drag_and_window_min.py`（解除値の実測）/ `tests_ui/test_full_view_header_width.py`（フォント変更・省略表示往復）

**読まない**: `keyseq/domain/` / `keyseq/application/` / `keyseq/infrastructure/` / 凍結済み暫定仕様（04〜17）。

## タスク

1. **task_01**: 最小の高さの本体 — 一覧の `height` 変更 / 測定・保持 / `apply_layout`・ドラッグ後の `minsize` へ高さを適用 / 幅を変える `geometry` の高さ = max(現在, 最小)
   + `tests_ui`（暫定 §5-1・§5-3・§5-5・§5-6）。
2. **task_02**: 測定の揺れ対策 — 一時メッセージを 1 行分として測る / `show_full_view` の `update_status` を測定より前へ
   + `tests_ui`（暫定 §5-2・§5-4）。
3. **task_03**: 統合確認（`tests` / `tests_ui` 全体 + `smoke_app`）+ 二次レビュー（`deep-reviewer` + `codex-reviewer`）+ **ユーザーによる実機目視**（暫定 §5-7・§5-8）。
4. **task_04（最終・正本反映）**: `features.md` §4.6 / `codebase_map.md` への昇格 + **暫定仕様 18 の凍結** + `decisions_archive/20_full_view_min_height.md` + `current.md` 完了記載 +
   idea_22 を `INDEX_done.md` へ + **`/refactor_check`** + 完了判定前レビュー（`deep-reviewer` + `codex-adversarial-reviewer`）。

タスク定義は着手する順に `tasks/task_NN_<topic>.md` へ起票する（`/task_new`）。

## レビュー方針

共通観点は `.claude/rules/review.md`。本フェーズ固有の観点:

- **切れの判定** — 最小の高さまで縮めた状態で root 直下の部品・3 枠の子部品が表示され下端が収まり、一覧が 6 / 9 行分以上か（`wm_minsize` の値の比較だけで済ませていないか）。
- **測定順序** — `paneconfigure` → `update_idletasks()` → 要求高さ、の順が初回・フォント変更・フル表示復帰で守られているか。
- **測定の揺れ** — ステータス欄 2 行・複数行の一時メッセージの表示中に測っても同じ値か。
- **minsize の全箇所** — ドラッグ後・フル表示復帰で高さが 1 へ戻らないか / 省略表示では解除されるか。
- **既存挙動の不変** — 幅の計算・既定幅・ウィンドウ幅の保存判定・820 での見た目（一覧の実高さ）が変わっていないか。

エージェントの使い分けは `.claude/rules/agent_selection.md`:

- 各タスクの必須レビュー = `reviewer` / 実装 = `codex-implementer` / テスト実行 = `verifier`
- task_03 の統合確認時 = `deep-reviewer` + `codex-reviewer`
- フェーズ完了判定前 = `deep-reviewer` + `codex-adversarial-reviewer`
