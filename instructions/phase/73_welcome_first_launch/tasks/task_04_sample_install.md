# task_04_sample_install

## 目的

Welcome で「サンプル入り」を選んだときに使う、サンプル（既定データ）を `config/sample/` へ書き出す処理を application 層に作る（暫定 56 §5.2）。
既にサンプルがあれば書き出さずに完全性を確かめ、欠けていれば手を付けない。Welcome・起動の流れからの呼び出しは task_05 で行う。
**application 限定（新規モジュール + `save_runtime_data` に任意の引数 1 つ）・presentation / domain 不変・JSON スキーマ不変**。

## 対象範囲（application 限定）

### 新規 `keyseq/application/config_service/sample_install.py`

- 定数: サンプルの置き場 `SAMPLE_DIR = "sample"`（`config/` 基準）・構成セットの相対パス `sample/keymap_sets/sample.json`
- `sample_keymap_set_path(config_root: str) -> str`: 構成セットの絶対パス
- 結果の型（dataclass）`SampleInstallResult`: `status`（`"written"` / `"existing"` / `"incomplete"` / `"failed"`）・`keymap_set_path: str`・`error: str`（失敗・欠けの理由。画面の文言にしない＝ログ・知らせの差し込み用の短い説明）
- `install_sample(service, *, config_root: str, keyboard_layout_id: str, external_layout_path: str = "") -> SampleInstallResult`
  1. 構成セットが既にあれば → `check_sample_complete` が真なら `"existing"`・偽なら `"incomplete"`（どちらも**何も書かない**）
  2. 無ければ → `service.new_default_data()`（サンプル・今の言語）を作り、`keyboard_layout` を `keyboard_layout_id` に。`external_layout_path` が空でなければ `external_keyboard_layouts` を `[{"path": external_layout_path}]` にする（JIS = `"user/keylayout/jis.json"`。呼び出し側が渡す）
  3. 下の **ファイル名の表**どおりの置き場を `SavePlan`（`keyseq/application/save_plan.py` の `ChildSaveEntry` で `ACTION_SAVE_AS` + `target_path`）で決め打ちにし、
     `service.save_runtime_data(<構成セットのパス>, data, config_root=..., split_base_dir=<config/sample>, save_plan=plan, write_startup_entry=False)` で書く（ダイアログなし）
  4. 成功 → `"written"`。例外 → `"failed"`（例外は握りつぶさず `error` に型と内容を入れる。構成セットまで書けていなければ次回の初回扱いで書き直せる＝§5.2）
  - 構成セットが無く子だけ残っている（前回の途中失敗）ときは、2〜3 で上書きしてよい（子の上書きの確認は出さない）
- `check_sample_complete(service, *, config_root: str) -> bool`: 構成セットが読め、そこから辿れる子（キーマップ・トリガー一覧・出力シーケンス）がすべて存在し JSON として読めるなら真。
  辿り方は既存の読み出し専用の参照の収集（`reference_scan.collect_reference_paths`）を使ってよい。読めない参照元があれば偽
- **ファイル名の表**（`config/sample/` 基準・全言語共通の英語）:

  | 種類 | キー | パス |
  |---|---|---|
  | キーマップ | keymap_1 / keymap_2 / keymap_3 | `keymaps/shortcuts.json` / `keymaps/right_hand.json` / `keymaps/numpad.json` |
  | トリガー一覧 | keymap_1 / keymap_2 / keymap_3 | `trigger_sets/shortcuts.json` / `trigger_sets/right_hand.json` / `trigger_sets/numpad.json` |
  | 出力シーケンス | keymap_1 の r / c / v / t / a | `sequences/select_line.json` / `copy.json` / `paste.json` / `switch_app.json` / `paste_line_to_app.json` |
  | 出力シーケンス | keymap_2 の h / keymap_3 の h | `sequences/right_hand_guide.json` / `sequences/numpad_guide.json` |

  （出力シーケンスの行のキーは `compose_sequence_key(keymap_id, trigger_key)` の形。サンプルのキー・id を変えたら表も追従させる）

### `keyseq/application/config_service/save_plan_execution.py` / `__init__.py`

- `save_runtime_data` に任意の引数 `write_startup_entry: bool = True` を足す（`ConfigService.save_runtime_data` も素通し）。False のとき `_write_runtime_payloads` は起動設定ファイル（`config/config.json`）を書かない。既定の挙動は不変
- 書く順は今のまま（出力シーケンス → トリガー一覧 → キーマップ → 構成セット）で、§5.2「子を先・構成セットを最後」を満たす（変えない）

### `keyseq/application/config_service/__init__.py`

- `ConfigService` に `install_sample` / `check_sample_complete` / `sample_keymap_set_path` の薄い委譲を足す（既存の委譲の書き方に合わせる）

### テスト（tests/・一時フォルダで）

- 構成セットが無い → `"written"`・表どおりの 14 ファイル + 構成セットができる・`config/config.json` は作られない・`config/user/` に何も書かれない
- 書いた構成セットを `load_runtime_data_from_keymap_set_path` で読むと 3 キーマップ・F12 / F1・`hook_keys_individual` True・`keyboard_layout` が渡した値
- `external_layout_path="user/keylayout/jis.json"` で書くと `keyboard_layout == "jis"` と登録が入る
- 2 回目の呼び出し → `"existing"`・ファイルの更新時刻・中身が変わらない
- 子を 1 つ消してから呼ぶ → `"incomplete"`・何も書き換えない
- 構成セットが無く子だけある → 書き直して `"written"`
- 書き込みの途中で例外（`repository.save_json` を構成セットのときだけ失敗させる等）→ `"failed"`・構成セットは無い
- `write_startup_entry` の既定（True）で今どおり起動設定ファイルを書く（既存テストが通ることでも可）

### 設計メモ / 制約

- 置き場の走査（孤児の掃除・保存先の確認）が `config/sample/` を扱えるかは、この task で**調べて完了報告に書く**（`orphan_scan` / `normalize_scan_dirs` の既定の走査対象。直す必要があれば報告のみで、直さない）
- 言語は呼び出し時の言語（`new_default_data()` がその時点の言語で組み立てる）
- presentation から呼ばれる前提（task_05）。この task では呼び出し元を作らない

## 読むファイル

- `keyseq/application/config_service/__init__.py:55-110`・`:296-345`（委譲の書き方・`save_runtime_data`）
- `keyseq/application/config_service/save_plan_execution.py:120-230`
- `keyseq/application/save_plan.py:1-110`（`ChildSaveEntry` / `SavePlan` / `compose_sequence_key` / `ACTION_SAVE_AS` の所在）
- `keyseq/application/config_service/reference_scan.py:1-60`
- `keyseq/application/config_service/orphan_scan.py`（走査対象の既定の部分のみ）
- `keyseq/domain/config.py` の `build_sample_config`（id とトリガーのキーの確認のみ）
- 手本のテスト: `tests/test_config_service.py` のうち `save_runtime_data` を一時フォルダで使うもの 1 つ（数十行）
- 主入力: `instructions/history/56_welcome_first_launch.md` §5.2

## 含まない

- 初回の判定・Welcome の結果の受け渡し・起動の流れからの呼び出し・失敗時の警告の表示（task_05）
- Welcome の窓（task_06）・正本の更新（task_09）
- 置き場の走査の修正（必要なら報告のみ）

## 確認

- 追加したテストが通る（verifier が `.venv` で実行）
- `python -m compileall -q keyseq`・`python -m unittest discover -s tests`・`python -m unittest discover -s tests_ui`・`python -m tests.smoke_app` が通る

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視は task_09 でまとめて実施
