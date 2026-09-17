# phase.md

## フェーズ名

フル表示ヘッダの幅をウィンドウ最小幅に含める（full_view_header_width）

## フェーズの目的

フル表示のヘッダ（**フック | 表示 | ファイル**）がウィンドウを狭めると切れる問題を解消する。
**ウィンドウ最小幅をヘッダの要求幅も含めた値にし**、**文言が切り替わるボタンの幅を固定し**、**キーボード選択のドロップダウンを狭める**。

**presentation 限定（純関数 + コントローラ + View の幅指定）。JSON スキーマ変更なし**（既存キー `full_view_window_width` の書き込み契機を 1 つ追加）。

- 起票元: [idea_21](../../backlog/idea_21_full_view_header_width.md)（phase 18 task_05 の実機目視・ユーザー 2026-09-17）。
- 主入力（暫定仕様）: [17_full_view_header_width.md](../../history/17_full_view_header_width.md)（**v0.3・ユーザー確定済**）。
- モード: **暫定仕様先行モード**。番号対応: phase 19 / 暫定 17 / decisions 19。

## 確定（ユーザー 2026-09-17）

暫定仕様 17 §2 が正。要点のみ:

- **案 A**: ウィンドウ最小幅 = max(メイン領域からの必要幅, ヘッダの要求幅からの幅)。**ヘッダの配置は変えない**。
- **フル表示のヘッダの、文言が切り替わるボタン 4 つ（取得 2・フック開始・通常トリガー切替）を最大文言幅で固定**。省略表示のボタンは固定しない。
- **キーボード選択のドロップダウン `width` 18 → 12（フル・省略の両方）**。
- **起動時にヘッダに合わせて自動で広がることを受け入れる**（標準 +19px。保存値が無ければ保存しない）。
- **保存したウィンドウ幅が最小幅より狭くて起動時に広げた場合は、広げた幅で保存値を更新する**（切り詰めのみのときは書かない）。

## スコープ

### 含む

- `pane_width_rules.py`: `resolve_layout` へヘッダ幅の入力（最小幅・縮小目標）/ ドラッグ後の最小幅 / ボタン幅の算出（純関数）+ `tests/`。
- 文言定数モジュール（presentation 直下・新規）/ `controllers/hook_controller.py` / `controllers/key_capture.py`（フル表示のボタンへの幅の適用）/
  `app.py`（`_apply_font_delta` の呼び出し順）/ `views/full_view/hook_frame.py` / `display_frame.py` / `views/compact_view/display_frame.py`。
- `controllers/pane_layout/`: ヘッダの測定と保持・最小幅への組込み・起動時の保存値の更新。
- `tests_ui/`（新規 + 暫定仕様 17 §5-9 の既存テスト期待値の見直し。**実 `config/config.json` を書かない**）。
- 正本反映: `features.md` §4.6「フル表示の幅配分」/ `codebase_map.md`。

### 含まない（後送り）

- ヘッダの配置変更（案 B）/ ボタン文言の変更 / 省略表示の幅・配置 / 長い表示名のドロップダウンでの切れ（受容）。
- 縦方向の最小サイズ（[idea_22](../../backlog/idea_22_full_view_min_height.md)）。
- `data_schema.md` の変更（JSON 不変）。

## このフェーズで読むファイル

1. `instructions/history/17_full_view_header_width.md`（主入力・v0.3）
2. `keyseq/presentation/pane_width_rules.py` / `keyseq/presentation/controllers/pane_layout/`（`pane_layout_controller.py` / `pane_measure.py`）
3. `keyseq/presentation/views/full_view/full_view.py:26-40` / `hook_frame.py` / `display_frame.py` / `views/compact_view/display_frame.py` / `compact_view/hook_frame.py:15-25`
4. `keyseq/presentation/controllers/hook_controller.py:1-30,60-86` / `controllers/key_capture.py:25-80`
5. `keyseq/presentation/app.py` の `_apply_font_delta`（`rg -n "_apply_font_delta"` で位置特定）
6. `instructions/common/spec_detail/features.md` §4.6「フル表示の幅配分」/ `codebase_map.md` の PaneLayoutController 節
7. 既存テストの型: `tests/test_pane_width_rules.py` / `tests_ui/test_pane_window_width_persistence.py`（クラス単位の書き込み遮断）

**読まない**: `keyseq/domain/` / `keyseq/application/` / `keyseq/infrastructure/` / 凍結済み暫定仕様（04〜16）。

## タスク

1. **task_01**: 純関数 — `resolve_layout` へヘッダ幅（ウィンドウ最小幅・画面超過の縮小目標 max(画面幅, ヘッダ幅)。既存呼び出しは不変）/ ドラッグ後の最小幅（縮小規則を通さない）/
   ボタン幅の算出 `ceil(max(measure)/measure("0"))` + `tests/` の単体テスト（暫定 §5-2・§5-3・§5-4 の純関数分）。**UI へは未結線**。
2. **task_02**: ボタン幅の固定とドロップダウン — 文言定数モジュール / View の初期文言 / `HookController`・`SingleKeyCaptureController` がフル表示のボタンへ幅を当てる（登録時・フォント変更時）/
   `_apply_font_delta` で `pane_layout.on_font_changed()` より前に呼ぶ / Combobox `width=12`（両表示）+ `tests_ui`（暫定 §5-4・§5-6・省略表示は固定しない）。
3. **task_03**: ヘッダ幅の組込み — `controllers/pane_layout/` でヘッダを測定・保持し、一括適用とドラッグ後の最小幅に使う + `tests_ui`（暫定 §5-1・§5-3 ドラッグ後・§5-5・§5-7・§5-8 前半）+
   **既存テストの期待値見直し**（暫定 §5-9 の列挙。条項で説明できるものだけ・完了報告に列挙）。
4. **task_04**: 起動時の保存値の更新（暫定 §3-5・§2-6）+ `tests_ui`（暫定 §5-8 後半）。
5. **task_05**: 統合確認（`tests` / `tests_ui` 全体 + `smoke_app`）+ 二次レビュー（`deep-reviewer` + `codex-reviewer`）+ **ユーザーによる実機目視**。
   - **task_05b**: task_05 二次レビュー（deep-reviewer 指摘 3）の採用分 = 保存値 > 画面幅でも最小幅未満なら書く境界の単体テスト（テストのみ）。
6. **task_06（最終・正本反映）**: `features.md` §4.6 / `codebase_map.md` への昇格 + **暫定仕様 17 の凍結** + `decisions_archive/19_full_view_header_width.md` + `current.md` 完了記載 +
   idea_21 を `INDEX_done.md` へ + **`/refactor_check`** + 完了判定前レビュー（`deep-reviewer` + `codex-adversarial-reviewer`）。

タスク定義は着手する順に `tasks/task_NN_<topic>.md` へ起票する（`/task_new`）。

## レビュー方針

共通観点は `.claude/rules/review.md`。本フェーズ固有の観点:

- **ヘッダの切れ** — フォント −3 / 標準 / ＋3・取得中でも、最小幅でヘッダと子 3 枠の実幅 ≥ 要求幅か。
- **測定順序** — ボタン幅の固定 → `update_idletasks()` → ヘッダ測定、の順が初回・フォント変更・フル表示復帰のすべてで守られているか。
- **縮小規則の適用範囲** — 画面超過の縮小は一括適用だけで、ドラッグ後の最小幅は実際の表示幅から求めているか。
- **保存の境界** — 起動時の保存値更新が「保存値あり・広げた」ときだけで、切り詰めのみ・保存値なし・起動時以外では書かないか。自動決定幅の規則（phase 18）を壊していないか。
- **依存方向** — views → controllers の import を作っていないか（文言定数は中立なモジュール）。
- **既存テストの期待値変更** — 暫定 §5-9 の列挙に当たり、変わる理由を条項で説明できるものだけか（弱化の混入がないか）。

エージェントの使い分けは `.claude/rules/agent_selection.md`:

- 各タスクの必須レビュー = `reviewer` / 実装 = `codex-implementer` / テスト実行 = `verifier`
- task_05 の統合確認時 = `deep-reviewer` + `codex-reviewer`
- フェーズ完了判定前 = `deep-reviewer` + `codex-adversarial-reviewer`
