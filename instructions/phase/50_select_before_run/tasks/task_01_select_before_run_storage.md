# task_01_select_before_run_storage

## 目的

暫定 34 §6 の保存を実装する: keymap_set の `select_before_run`（全体）と sequence の `select_before_run`（トリガーごと）の読み書き・既定値・後方互換。
**domain / application 限定・presentation 不変（UI は task_03）。判定（runner）は task_02。**

## 対象範囲（domain / application・保存のみ）

### keymap_set の `select_before_run`（bool・既定 false・**bool 型でなければ false**・推論しない）

- `keyseq/domain/config.py`: 既定の構成（:38 付近の `hook_keys_individual` / `hotkey_presets_individual` と同じ並び）に `"select_before_run": False`。
  単一 JSON の正規化（:227-231 付近の `hotkey_presets_individual` と同じ書き方）で bool 型でなければ false
- `keyseq/application/config_service/split_loading.py:104-112`: keymap_set から runtime へ写すキーの列挙に追加（無ければ false・bool 型でなければ false）
- `keyseq/application/config_service/split_payloads.py:448-475`: keymap_set のペイロードに追加（`hotkey_presets_individual` と同じ書き方・常に書く）
- `keyseq/application/config_service/__init__.py:540-580` 付近: runtime の既定値の補完（`hook_keys_individual` の `setdefault` 等と同じ流儀）が要るなら追加

### sequence / trigger の `select_before_run`（bool・既定 false・**`run_to_end` と同じ解釈**: キーが無ければ false・値があれば `bool()`）

- `split_payloads.py:534-544`（sequence のペイロード・個別保存 `child_file_io.py:51` も同じ関数）: `run_to_end` の隣に追加（常に書く）
- `config_service/__init__.py:458-467` `_normalize_sequence_payload`: `run_to_end` の隣に追加
- `split_loading.py:491-503`（trigger_set 内の trigger）: `run_to_end` の隣に追加（sequence 側が上書きする既存の優先 :510 に従う＝`select_before_run` も sequence 側で上書きされること）
- `domain/config.py:169-197` `normalize_triggers`（単一 JSON のインラインの trigger）: `run_to_end` の隣に追加
- `domain/config.py` の既定のトリガー（:52・:67・:211 付近の `run_to_end` を持つ雛形）にも `"select_before_run": False`

### テスト（tests/）

- keymap_set: 保存 → 再読込で true / false が保たれる・キーが無い古い JSON は false・`"yes"` / `1` / `null` 等の非 bool は false
- sequence: 保存 → 再読込・シーケンスの個別保存 → 個別読込で保たれる・キーが無ければ false・`run_to_end` と同じ解釈（`1` は true・`0` / `null` は false）
- trigger_set 内と sequence の両方にあれば sequence 側が優先
- 単一 JSON の Import → Export で keymap_set とトリガーの値が保たれる
- 既存の往復テストの流儀（`tests/test_config_service*.py`）に合わせる。実 `config/` を汚さない（一時ディレクトリ）

## 読むファイル

- `instructions/history/34_select_before_run.md` の §6（全体は不要）・`instructions/common/spec_detail/data_schema.md` §5.6「trigger_set」「sequence」
- `keyseq/domain/config.py:30-70, 100-235`
- `keyseq/application/config_service/split_loading.py:100-120, 485-515`・`split_payloads.py:440-480, 525-545`・`config_service/__init__.py:450-470, 535-585`・`child_file_io.py:15-60`
- 手本のテスト: `tests/` の `run_to_end` / `hotkey_presets_individual` の往復テスト（`grep -rln "hotkey_presets_individual\|run_to_end" tests`）

## 含まない

- runner の判定・注入口（task_02）/ UI・dirty・同期（task_03）/ 正本の改訂（task_05）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` clean
- 追加したテストを含めて tests 全体・tests_ui 全体・`-m tests.smoke_app` pass。実 `config/` を汚さない

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視: なし（task_03 以降でまとめて）
