# phase.md

## フェーズ名

マウスのドラッグ操作（mouse_drag_action）

## フェーズの目的

出力シーケンスの `mouse_click` アクションを拡張し、**掴む点と離す点の 2 点 + カーソルの移動速度**を指定した
ドラッグ（範囲選択・ドラッグ&ドロップ）を送れるようにする。

**対象レイヤ = presentation（ActionDialog）/ application（分岐と所要時間の算出）/ infrastructure（`drag_mouse`）/ domain（表示整形）**。
**JSON は既存キーを一切変えず、`drag` / `to_x` / `to_y` / `drag_speed` を追加するのみ**（後方互換）。
**OS 分岐は増やさない**（`pyautogui` のみを使い `ctypes` を使わない）。

- 起票元: ユーザー要望（2026-09-19・ドラッグ&ドロップと範囲選択をしたい）。
- 主入力（暫定仕様）: [19_mouse_drag_action.md](../../history/19_mouse_drag_action.md)（**v0.5・ユーザー確定済・実装着手可**）。
- モード: **暫定仕様先行モード**。番号対応: phase 22 / 暫定 19 / decisions 22。

## 確定（ユーザー 2026-09-19）

暫定仕様 19 §2 が正。要点のみ再掲（**条項の根拠は暫定仕様 19 を引く**）:

- 保存形式は **`mouse_click` の拡張**（新種別 `mouse_drag` は作らない）。種別ドロップダウンは 3 種のまま。
- UI は**マウス設定内のチェックボックス**。チェックで離す点の欄と速度の欄が現れる。
- 速度は **px/秒・既定 1000**。所要時間 = 距離 ÷ 速度を **0.15〜5.0 秒へクランプ**する。
- `drag` が true のとき **`clicks` は 1 固定**（回数欄は無効化）。
- 実行は `dragTo` を使わず **`moveTo` → `mouseDown` → `moveTo(duration)` → `mouseUp`** に分解し、**例外時も必ず離す**。
- **ドラッグ実行中は `pyautogui.FAILSAFE` を False にし、終了時に必ず元へ戻す**（解放が FailSafe に遮られるため / OS 分岐を増やさないため）。
  ドラッグ以外のクリックでは FailSafe は従来どおり有効。
- マウス操作は **send guard の対象外のまま**（明文化のみ）。
- 既知の制約: 古いビルド / 別実装がこの JSON を読むと**掴む位置で単発クリック**になる。

## スコープ

### 含む

- `keyseq/infrastructure/input_gateway.py`: `drag_mouse` の新設（FailSafe の退避・復元を含む）。
- `keyseq/application/action_executor.py`: `drag` 分岐・距離と所要時間の算出・クランプ・異常系の報告。
- `keyseq/presentation/dialogs/action_dialog.py`: ドラッグのチェックボックス / 離す点の欄と取得ボタン / 速度欄 /
  回数欄の無効化 / 座標取得の排他 / X・Y ラベルの文言切替（参照保持）/ 検証と dict 生成 / 既存値の復元。
- `keyseq/domain/config.py`: `format_action_list_item` のドラッグ表示。
- `tests/` / `tests_ui/`: 暫定仕様 19 §8 の受け入れ条件に対応する単体テスト。
- **正本への昇格**（フェーズ末）: `spec_detail/data_schema.md` に **§5.11「アクション要素」を新設** +
  FailSafe / send guard の明文化 + `codebase_map.md` のマウス操作の記述。

### 含まない（後送り）

- ホイールスクロール / マウスボタンの押す・離すを独立アクションにすること（キーボード側は [idea_23](../../backlog/idea_23_key_press_release_actions.md)）。
- ドラッグ実行の別スレッド化（UI スレッド占有の根本解決）。本フェーズは上限クランプで回避する。
- 経由点を複数持つドラッグ・曲線補間（`tween` の選択）。
- 相対座標 / ウィンドウ基準座標 / マルチモニタ座標系の規定。
- **macOS / X11 対応**（拡張キー送信の `ctypes.windll` とキーフックの `keyboard` が Windows 前提）。
- 座標取得 UI を「1 ボタンで 2 点連続取得」に変える案（暫定仕様 19 §9・保留）。
- `mouse_click` を send guard へ入れる**挙動変更**（明文化のみ）。

## このフェーズで読むファイル

1. [instructions/history/19_mouse_drag_action.md](../../history/19_mouse_drag_action.md)（**主入力・全文**）
2. `keyseq/infrastructure/input_gateway.py`（編集対象。`click_mouse` と phase 21 の送信部分）
3. `keyseq/application/action_executor.py:44-127`（編集対象。種別分岐と `_execute_mouse_click`）
4. `keyseq/presentation/dialogs/action_dialog.py`（編集対象・全体）
5. `keyseq/domain/config.py:310-317`（`format_action_list_item`）
6. `tests/test_domain_config.py:236` 付近（既存の `mouse_click` 表示テスト）
7. `instructions/common/spec_detail/data_schema.md`（§5.2 / §5.6 / 冒頭 `:12-17` の後方互換方針。**昇格タスクで編集**）
8. `instructions/common/codebase_map.md`（ActionDialog / SequenceBox / InputGateway の節。**昇格タスクで編集**）

**読まない**: `keyseq/application/config_service/` / `keyseq/presentation/views/` の幅・レイアウト周り /
凍結済みの暫定仕様（04〜18）/ `__pycache__` 等。

## タスク

1. **task_01**: 実行経路 — `input_gateway.drag_mouse`（FailSafe の退避・復元 / 例外時も必ず解放）+
   `action_executor` の `drag` 分岐・距離と所要時間の算出・クランプ・異常系 + `tests/` の単体テスト
   （呼び出し順序・例外時の解放・`FAILSAFE` の退避と復元・クランプ境界・不正値の既定）。
2. **task_02**: UI と表示 — `ActionDialog` のチェックボックス / 離す点の欄と取得ボタン / 速度欄 / 回数欄の無効化 /
   座標取得の排他 / ラベルの文言切替 / 検証と dict 生成（**drag OFF では新キーを出力しない**）/ 既存値の復元 +
   `format_action_list_item` のドラッグ表示 + `tests` / `tests_ui` のテスト。
3. **task_03（最終）**: 統合確認（`tests` / `tests_ui` 全体 + `smoke_app`）+ 二次レビュー（`deep-reviewer` + `codex-reviewer`）+
   **ユーザーによる実機目視**（暫定仕様 19 §8-11 の 8 項目）+ **正本への昇格**（`data_schema.md` §5.11 新設 /
   FailSafe と send guard の明文化 / `codebase_map.md`）+ **暫定仕様 19 の凍結** +
   `decisions_archive/22_mouse_drag_action.md` + `current.md` 完了記載 + **`/refactor_check`** +
   完了判定前レビュー（`deep-reviewer` + `codex-adversarial-reviewer`）。
4. **task_03b**（task_03 の二次レビュー採用分）: `drag_speed` の NaN 判定の修正（`not (speed > 0)`）+
   ドラッグ 4 キーの永続化テスト / 種別切替の往復テスト / NaN ケースの追加。

タスク定義は着手する順に `tasks/task_NN_<topic>.md` へ起票する（`/task_new`）。

## レビュー方針

共通観点は `.claude/rules/review.md`。本フェーズ固有の観点:

- **後方互換** — `drag` の無い既存 JSON の挙動・表示が一切変わっていないか。`drag` OFF で新キーを出力していないか。
  既存キー（`x` / `y` / `button` / `clicks` / `label`）を消していないか。
- **解放の担保** — どの例外経路でも `mouseUp` に到達するか。`FAILSAFE` が**必ず元の値へ戻る**か
  （例外時・早期 return 時も）。ドラッグ以外の経路で `FAILSAFE` を触っていないか。
- **層と依存** — 所要時間の算出が application にあり、`pyautogui` が infrastructure に閉じているか。
  **`ctypes` を新たに使っていないか**（OS 分岐を増やさない方針）。
- **UI の副作用** — 回数欄の無効化・座標取得の排他・ラベル文言の切替が、種別を hotkey / text に戻したときに
  正しく復帰するか。`pynput` のリスナーがダイアログ破棄後に残らないか。
- **テストの検出力** — 呼び出し回数だけでなく**順序と引数**を固定しているか。クランプは**境界値**で検証しているか
  （phase 21 の教訓: 変異検査で「その仕様を壊すと落ちる」ことを確かめる）。

エージェントの使い分けは `.claude/rules/agent_selection.md`:

- 各タスクの必須レビュー = `reviewer` / 実装 = `codex-implementer` / テスト実行 = `verifier`
- task_03 の統合確認時 = `deep-reviewer` + `codex-reviewer` / フェーズ完了判定前 = `deep-reviewer` + `codex-adversarial-reviewer`
