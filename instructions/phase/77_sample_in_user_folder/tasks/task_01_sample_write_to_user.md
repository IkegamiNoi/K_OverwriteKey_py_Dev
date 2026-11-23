# task_01_sample_write_to_user

## 目的

初回の「サンプル入り」の書き出し先を `config/sample/` から `config/user/` へ変え、構成セットが無いときに中身の違う同名の子があれば何も書かない（暫定 59 §3.1・§3.2）。
**application（`config_service/`）と presentation（`app.py` の起動設定の 1 行）限定・domain 不変・JSON スキーマ不変・`orphan_scan.py` は変えない（§3.3）。**

## 対象範囲（application + presentation 1 行・既存ファイルの変更のみ）

### `keyseq/application/config_service/sample_install.py`

- 定数: `SAMPLE_DIR = "user"`・`SAMPLE_KEYMAP_SET_RELATIVE_PATH = "user/keymap_sets/sample.json"`（名前は変えない。子のパス・`split_base_dir` はこの定数から作るので自動で `config/user/` になる）
- `install_sample`: 構成セットが無いとき、書き出す前に `_find_conflicting_children(...)`（新規の private 関数）で衝突を調べる
  - 対象 = 今回書き出す全ての子（出力シーケンス 7・トリガー一覧 3・キーマップ 3 = `_sample_save_plan` の全エントリ）。構成セット本体は対象外（無いことを確認済みのため）
  - 各パスについて: ファイルが無い → 衝突でない / 読めて JSON の値が「今回書き出す中身」と等しい → 衝突でない / それ以外（中身が違う・読めない・JSON でない）→ 衝突
  - 衝突が 1 つでもあれば **何も書かず** `SampleInstallResult("incomplete", path, error)` を返す。`error` は `"Sample files already exist: "` + 衝突した子の `config_root` 相対パス（`/` 区切り）を `", "` で連結
  - 衝突が無ければ今までどおり `save_runtime_data(...)` で書く
- 「今回書き出す中身」は §save_plan_execution の新関数で求める（同じ `data`・`save_plan`・`split_base_dir`・`config_root`・構成セットのパスで、書く処理と同じ組み立て）。比較は `json.loads(json.dumps(payload, ensure_ascii=False))` と読んだ値の `==`（タプル等の差を消す）
- `check_sample_complete` は変えない

### `keyseq/application/config_service/save_plan_execution.py`

- 新しい公開関数 `preview_child_payloads(service, keymap_set_path, data, *, config_root, split_base_dir, save_plan) -> list[tuple[str, Any]]` を足す: `save_runtime_data` の前半（`_restore_input_parent_refs` → `_build_and_validate_runtime_payloads`〔`startup_data=None`・`startup_entry_loaded=False`・`keep_legacy_copy=False`・`legacy_path=""`〕→ `_restore_payload_keymap_parent_refs`）と同じ手順で payloads を作り、**`_write_runtime_payloads` が書く子**（`skip` でない sequences / trigger_sets / keymaps）の `(絶対パス, payload)` を書く順に返す。キーマップのパスは `_write_runtime_payloads` と同じく `service._resolve_config_relative_path(item["path"], resolved_config_root)`
- 書き込みは一切しない。`save_runtime_data` 本体は変えない（重複を避けるための共通化もしない）

### `keyseq/presentation/app.py`

- `_prepare_first_launch` の `"sample/keymap_sets/sample.json"`（405 行付近）を `"user/keymap_sets/sample.json"` に変える（直値のまま・定数化しない）

### テスト

- `tests/test_sample_install.py`（既存テストを新しいパスに合わせて直す + 追加。**既存テストの途中に新しいテストを差し込まず、クラス末尾に足す**）
  - 既存: 期待パスを `user/...` に・`SAMPLE_DIR == "user"`・「`user/` にファイルが無い」の検査を「`sample/` が作られない」に置き換え・`test_failure_leaves_no_keymap_set_and_retry_succeeds` の `calls` の接頭辞を `user/`
  - `test_leftover_children_are_overwritten` は意味が変わる（§3.2）: 「中身の違う同名の子があると `incomplete`・何も書かれない（snapshot 不変・`save_json` 未呼び出し）・`error` にその相対パス」へ書き換え（名前も変える）
  - 追加 1: 中身が同じ子が残っている（1 回書いてから構成セットだけ消す）→ `written`
  - 追加 2: 中身が違う子が 1 つ + 同じ子が他にある → `incomplete`・既存の子は全部不変
  - 追加 3: 子の参照が `config/` 基準の相対（`user/...`）で書かれ、JIS の `external_layout_path="user/keylayout/jis.json"` を渡した書き出しを読み直すと `external_keyboard_layouts` の path が同じ値
  - 追加 4: `config/sample/` に既存の旧サンプル一式がある状態で書き出すと、`config/sample/` 配下は snapshot 不変
- `tests/test_orphan_scan.py` に追加（末尾）: 新しいサンプルを `install_sample` で書いた構成で走査すると、書いた子 13 個がすべて参照あり（候補にならない）。既存の `test_sample_set_references_user_child_without_expanding_candidates` は変えない
- `tests_ui/test_first_launch_flow.py`: 期待値の `"sample/keymap_sets/sample.json"` を `"user/keymap_sets/sample.json"` へ（他は変えない）

## 読むファイル

1. `instructions/history/59_sample_in_user_folder.md` §3.1〜§3.5・§4（主入力）
2. `keyseq/application/config_service/sample_install.py`（全体・編集対象）
3. `keyseq/application/config_service/save_plan_execution.py:29-235`（payload の組み立てと書き込みの順）
4. `keyseq/presentation/app.py:390-410`（`_prepare_first_launch`）
5. `tests/test_sample_install.py`（全体・編集対象）
6. `tests/test_orphan_scan.py:1-40`（ヘルパーの使い方）・`:108-122`
7. `tests_ui/test_first_launch_flow.py:75-95`

## 含まない

- `orphan_scan.py` の変更（経路 5 は残す・§3.3）
- 正本（`spec_detail/`）・`codebase_map.md` の更新（task_03）
- 統合検証・実機目視（task_02）
- 既存 `config/sample/` の移行・警告の文言の変更・新しい status 値の追加

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests tests_ui` が clean
- `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_sample_install tests.test_orphan_scan` が pass（上記の追加・書き換えを含む）
- `..\..\..\.venv\Scripts\python.exe -m unittest tests_ui.test_first_launch_flow` が pass
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` が全 pass（退行なし）
- `grep -rn "sample/keymap_sets" keyseq` が `orphan_scan.py` 以外に無い（`orphan_scan.py` は `"sample", "keymap_sets"` の形で残る）

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_02 でまとめて実施。
