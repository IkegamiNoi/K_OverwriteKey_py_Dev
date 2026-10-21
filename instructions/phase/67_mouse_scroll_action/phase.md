# phase.md

## フェーズ名

出力シーケンスのマウススクロール（mouse_scroll_action）

## フェーズの目的

出力シーケンスの行でマウスのホイールを回せるようにする（縦・横・量はノッチ数 / 生の値・座標は任意）。
**新しい種類 `mouse_scroll` を足す。domain（検証・分解・一覧の書式の新モジュール）+ application（`ActionExecutor` の分岐・止まる系）+ infrastructure（`InputGateway.scroll_mouse`・`SendInput` で WHEEL / HWHEEL）+ presentation（アクションのダイアログの欄・「次に実行」の要約）。JSON スキーマ = 種類の追加（既存キーの削除・意味変更なし）。**

- 起票元: ユーザー要望（2026-10-21）。
- 主入力（暫定仕様）: [50_mouse_scroll_action.md](../../history/50_mouse_scroll_action.md)（v0.4・ユーザー確定済）
- モード: **暫定仕様先行モード**。番号対応: phase 67 / 暫定 50 / decisions 67。

## 確定（ユーザー 2026-10-21）

- 向きは上下左右 / 量の単位はノッチ数（既定）と生の値（120 = 1 ノッチ）の選択式・使わない欄はグレーアウト / 座標は任意（mouse_click と同じ取得手段）/ 1 ノッチずつ間隔なし
- 上限 ノッチ 100・生の値 12000 / 既定 ノッチ 1 / FailSafe 無効（`move_cursor`）/ `unit` はキー無し・空だけ notch / 一覧は `[スクロール] 下 3`
- 不正な行は止まる系（key_hold と同じ）。詳細は暫定 50 §2〜§8

## スコープ

### 含む

- domain `mouse_scroll.py`（`parse_mouse_scroll`・事象の量への分解・一覧の値の書式）と `format_action_list_item` の分岐（暫定 50 §3・§4・§6）
- `ActionExecutor` の分岐・止まる系の通知・未知の種類の文言（§4）/ `InputGateway.scroll_mouse`（§4）
- ダイアログの欄（向き・単位と量・座標）・OK の検査・既存の行の復元（§5）/ 「次に実行」の要約（§6）
- テスト（tests / tests_ui）・実機目視（§9）・正本反映（§11）・暫定 50 の凍結

### 含まない（後送り）

- 暫定 50 §10 のスコープ外（間隔・速度・押したまま・画面の枠でのスクロール）

## このフェーズで読むファイル

1. 主入力: `instructions/history/50_mouse_scroll_action.md`
2. `keyseq/domain/key_hold.py`（手本: parse・書式）・`keyseq/domain/config.py:432-480`（`format_action_list_item`）
3. `keyseq/application/action_executor.py:100-350`（`execute()`・未知の種類・`_report_held_error`・mouse_click）
4. `keyseq/infrastructure/input_gateway.py:40-200`（`SendInput` の構造体と送信）・`:230-260`（`move_cursor`）・`:395-440`（マウス）
5. `keyseq/presentation/dialogs/action_dialog.py`（全体）・`action_key_hold_fields.py`（手本の欄）
6. `keyseq/presentation/controllers/action_list_rendering.py:49-76`
7. 正本: `data_schema.md` §5.11・`features.md` §4.2 冒頭・§4.2.12・§4.6 / `codebase_map.md`（アクションの実行・key_hold・マウス操作の節）

## タスク

- task_01: domain `mouse_scroll.py` + `format_action_list_item` + `ActionExecutor` の分岐 + `InputGateway.scroll_mouse`・テスト（tests）
- task_02: アクションのダイアログの欄（`action_mouse_scroll_fields.py`）・OK の検査・復元 + 「次に実行」の要約（呼び出し先の表示枠・省略表示のシーケンス欄が §6 の書式になることの確認を含む）・テスト（tests_ui）
- task_03: 実機目視（暫定 50 §9）・正本反映（§11）・暫定 50 凍結・`decisions_archive/67_mouse_scroll_action.md`・decisions.md の索引・current.md の完了記載・`/refactor_check`・完了判定前レビュー（deep-reviewer + codex-adversarial-reviewer）

## レビュー方針

- 各タスク: `reviewer`（5 観点）・既存テスト（tests / tests_ui / smoke）の通過を完了条件に含める
- task_01 重点: 検証が暫定 50 §3 どおり（bool・`2.7` の拒否・`unit` の扱い・座標はキーの有無）/ 分解（ノッチ ±120 × N・生の値は 120 ずつ + 端数）と符号 / 1 回の `SendInput`・負の `mouseData` / 戻り値（成功 True・エラー False）と通知の内容 / FailSafe を外す移動 / 依存方向（domain は UI・infrastructure を import しない）
- task_02 重点: 単位の切替のグレーアウト・不正な単位は未選択で OK 拒否・有効な量は整数で復元・座標の取得の同時起動の防止・隠れる欄のフォーカス・既存の種類の欄が不変
