# task_07d_v06_spec_changes

## 目的

暫定仕様 25 **v0.6** のユーザー判断（2026-09-26・統合レビュー後）を実装する: §2-13（トリガー優先へ戻す）・§2-16 注記・§2-23〜27・§4.1-2・§4.4・§4.5・§7.1・§7.3・§8.5・受け入れ条件 14・17・24・27〜30。
**JSON スキーマ不変**（読込・移行の判定と自動作成・UI・入力判定の変更）。

## 対象範囲

### 1. トリガー優先へ戻す（§2-13・§7.1・§7.3・§8.5）

- `input_router.py`: 優先順位を **停止 > トグル > 直接切替 > トリガー > 置換** へ（トリガー・置換はアクティブのもの）。
- `key_overlap.py`: トリガーの「負ける相手」から**置換を外す**（停止 / トグル / 切替のみ）。§7.3 の表から「置換と重複」を削除。
- トリガー一覧のグレー表示: 置換元キーとの重なりではグレーにしない（停止 / トグル / 切替との重なりは現行どおり）。
- `keyboard_window.py`: 置換元キーとトリガーが重なるキーは**トリガーの表示を優先**（旧版の表示。予約キーが最後に上書きする順は維持）。
- §8.5 の案内から「置換と重複しているため…」を削除。置換元キーと停止 / トグル / トリガーの重なりは案内しない。
- 編集時の拒否（§7.2・同キーマップ内のトリガーと置換元キーの双方向）は**そのまま**。

### 2. 重なり判定の表化（§2-27・§8.5）

- 重なり判定（`analyze_key_overlaps`）の結果を**読み取り専用の表**（イミュータブル・差し替えで更新）として保持し、キー入力時（フックのスレッド）の案内判定は**その表を引くだけ**にする（全件走査しない）。
- 表の作り直しの契機: グレー表示の再判定を行う箇所（トリガー一覧・キーマップ一覧の再描画）に加え、トリガー / 置換 / 切替キー / 停止・トグルキーの編集・読込・アクティブ切替。**グレー表示と案内が同じ表を使う**こと。
- どの割り当てが動くか（§7.1 の順）はキー入力時に従来どおり判定する（表は案内にだけ使う）。
- 「キーマップ一時停止」中は重なりの案内を一切出さない（§8.5 の明確化・現行どおり）。

### 3. 旧形式の移行の改訂（§2-23・§2-24・§4.1-2・§4.4・§4.5）

- `split_loading.py`（split 読込）:
  - §4.1-2 の移行対象を「アクティブの keymap ファイルに **`trigger_set_path` の項目が無い**」ときに限定（値が `""` は「一覧なし」として移行しない）。
  - 旧値が非空で、**いずれかのキーマップ**が旧一覧と同じ解決先を参照していれば `same`（何もしない・通知しない）。
  - アクティブが別ファイルを参照していて移行できない場合は、**新しいキーマップを自動作成して旧一覧を付ける**（`id` = 既存採番〔`next_keymap_id`〕/ `label` = 「旧トリガー一覧（<旧一覧ファイルの stem>）」/ `mappings` = {} / 切替キーなし / 一覧順の末尾 / アクティブは変えない）。
    状態は「移行した」扱い（`_legacy_trigger_set.state = "migrated"`・`keymap_id` = 作ったキーマップ）で、§4.2 の未保存化と「保存しない」不可が効くこと。
  - `unused` 状態は廃止（§4.4 の決定表から削除）。関連する保存側（`split_payloads.py` の決定表・`save_plan_execution.py` の `unused` 維持処理）も整理する。
- 読込完了時の通知（`keymap_set_io.py` / `startup_io.py` の §4.5 通知）: 「旧形式のトリガー一覧 <パス> を、キーマップ『<名前>』に移しました（切替キーは未設定です）」に変更（新キーマップを作った場合だけ出す）。
- 単一 JSON（Import）は対象外（従来どおり・`triggers` キーの有無で判定）。

### 4. 移行先の削除 = 関係の解除（§2-25・§4.4）

- `keymap_panel_controller.delete_keymap`: 削除するキーマップが `_legacy_trigger_set.keymap_id`（移行先）なら、**移行の記録を消す**（状態を `none` 相当へ）。保存すると構成セットの `trigger_set_path` は `""`。

### 5. 同一キーマップファイルの二重読込禁止（§2-26）

- `keymap_file_io.load_keymap_file`: 読み込むファイルの解決先パスが、既存キーマップの source_path の解決先と一致したら、`showerror`（または info）で「このキーマップは既に読み込まれています」を出して読み込まない（runtime 不変）。比較は既存の canonical path の関数を使う。

### テスト（追加・更新）

- 既存テストの期待値更新は優先順位の戻し・「置換と重複」の削除・`unused` 廃止・通知文言の変更によるもののみ。アサーションを緩めない。テスト補助で runtime を書き換えない。キーマップ 0 個のフィクスチャを作らない。未モックの実ダイアログを開かない。
- 新規 / 更新（受け入れ条件 14・17・24・27〜30）:
  1. 入力判定: トリガーと置換が同キーならトリガーが実行される。トリガーは置換との重なりでグレーにならない。キーボード表示はトリガーが上。
  2. 重なりの表: キー入力時の案内が表を引く（`analyze_key_overlaps` をキー入力ごとに呼ばない）・データ変更の各契機で表が作り直される・グレー表示と案内が同じ表。
  3. 移行: `trigger_set_path: ""` を持つキーマップには移行しない / 項目の無いキーマップには移行する / アクティブが別一覧を参照 → 新キーマップが作られ旧一覧が付き未保存・通知文言 / いずれかのキーマップが同ファイル参照 → 何もしない / 保存後は構成セットの旧値が `""`・再読込で新キーマップが一覧を持つ。
  4. 移行先を保存前に削除して保存 → 構成セットの旧値 `""`・移行の記録なし（新しいキーマップが「保存しない」を選べる）。
  5. 同じキーマップファイルの二重読込 → 拒否・runtime 不変。

## 読むファイル

- `instructions/history/25_trigger_list_per_keymap.md` v0.6 の §2-13・§2-16・§2-23〜27・§4.1・§4.4・§4.5・§7.1・§7.3・§8.5・§10
- `keyseq/application/{input_router,key_overlap,action_executor}.py` / `keyseq/presentation/keyboard_window.py:95-125`
- `keyseq/presentation/controllers/{hook_controller,trigger_panel_controller,keymap_panel_controller}.py`（重なり表示・案内・削除の箇所）
- `keyseq/application/config_service/{split_loading,split_payloads,save_plan_execution}.py`（`_legacy_trigger_set` の扱い）
- `keyseq/presentation/controllers/config_io/{keymap_set_io,startup_io,keymap_file_io}.py`（通知・個別読込）
- 手本のテスト: `tests/test_key_overlap.py` / `tests/test_per_keymap_triggers_load.py` / `tests_ui/test_task05_overlap_ui.py`（冒頭）

## 含まない

- `config_service/__init__.py` の分割（`/refactor_check`）/ 正本反映・`instructions/` 配下の編集（task_08）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq` clean
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` 全 pass（skip 7）/ `tests_ui` 全 pass（`timeout 900`・ハングなし）/ `tests.smoke_app` pass
- `git grep -n "置換と重複" -- keyseq` が 0 件 / `git grep -n '"triggers"' -- keyseq/presentation` が 0 件

## 完了条件

- 上記確認 pass・**reviewer 採用**。実機の再確認はユーザー（完了判定前にまとめて依頼）。
