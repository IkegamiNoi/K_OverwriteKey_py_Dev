# 計画02 最終報告

- 作成日: 2026-07-05
- ベースライン: `9dcaa7d`（作業ブランチ `claude/goofy-mclaren-c2b4bb` 上に実施）

## 実施項目（すべて完了、1項目=1コミット）
| 項目 | 内容 | コミット |
|---|---|---|
| 0 | UI特性テスト追加（tests_ui/） | aa7b7d8 |
| S1 | デッドコード2件削除 | 03d4d72 |
| S2 | listbox_utils.py 抽出 | 2fbdd9b |
| S3 | ConfigPaths 抽出（+tests/test_config_paths.py） | 32e9251 |
| S4 | DirtyStateTracker 抽出（+tests/test_dirty_state.py） | 28268a4 |
| S5 | SingleKeyCaptureController 統合抽出 | 5281798 |
| S6 | ConfigIoController 抽出 | 201a5e9 |
| S7 | LayoutController 抽出 | 1c4771f |
| S8 | KeymapPanelController 抽出 | 24897f0 |
| S9 | TriggerPanelController 抽出 | 1c09d10 |
| S10 | HookController 抽出 | 020b795 |
| S11 | 最終検証・ドキュメント更新 | （本コミット） |

スキップ項目: なし。失敗して戻した項目: なし。

## app.py 行数推移
- 分割前（計画01完了時, 概算）: 約 3,000 行
- 分割後: **990 行**（`python` 計測）。目安 <1,000 行を達成。
  ※ PowerShell `(Get-Content ...).Lines` は 815 と表示されるが、これは改行コード
  （LF）解釈差によるもの。実体の物理行数は 990。
- 新規モジュール行数: config_paths 124 / dirty_state 70 / key_capture 136 /
  config_io_controller 597 / layout_controller 298 / keymap_panel_controller 402 /
  trigger_panel_controller 575 / hook_controller 228 / listbox_utils 36。
  すべて概ね 600 行未満。

## 検証結果
標準検証は全項目でパス:
- `py -m compileall -q keyseq main.py` → OK
- `py -m unittest discover -s tests` → 59 tests OK（計画01の50 + S3/S4新規9）
- `py -m unittest discover -s tests_ui`（PYTHONPATH=.） → 9 tests OK
- `py tests/smoke_app.py`（PYTHONPATH=.） → SMOKE OK
- S6: プログラムによる構成セット save→load ラウンドトリップも正常確認。

## 設計どおりの確認
- views.py / dialogs.py / keyboard_window.py は 1 文字も変更していない
  （すべて App ファサード経由で従来どおり動作）。
- コントローラ同士の直接参照なし（相互作用は App ファサード経由）。
- 挙動・文言・JSON仕様の変更なし（機械的な移設 + S5 の同型2実装統合のみ）。
- app.py に残る実体ロジックは App 本来の責務（__init__ 配線 / _build_ui /
  メニュー / View切替 / 起動設定読込 / フォント / validate_hotkey / on_close 等）のみ。
  移設対象メソッドは 1 行委譲のみ残置。

## 未実施（要利用者確認）
実キー入力・グローバルフック挙動を観測できない実行環境のため、計画書が
「手動確認（必須）」とする対話的GUI操作は未実施。詳細と手順は
`01_progress_and_manual_checks.md` を参照（特に S10 の6項目、S5の5項目、S6の一巡、
S7/S8/S9 の各操作）。tests_ui による観測可能な契約は固定済み。

## 付随した整理（挙動影響なし）
- S5: 不要化した `App._normalize_tk_key_for_trigger` を削除。
- S10 後: 移設で未使用となった import を app.py から除去
  （re / filedialog / simpledialog / ActionDialog / KeymapEditDialog / PresetDialog /
  TriggerDialog / domain.config の normalize_key_name・coerce_nonnegative_int・
  format_action_list_item・format_trigger_list_item、および keyboard_layouts /
  key_identifiers の未使用シンボル）。
- 実行環境に GUI 依存（pynput/keyboard/PyAutoGUI 一式）を pip 導入
  （詳細は 00_environment_notes.md）。
