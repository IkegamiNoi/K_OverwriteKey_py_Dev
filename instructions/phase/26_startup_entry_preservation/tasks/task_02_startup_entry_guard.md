# task_02_startup_entry_guard

## 目的

task_01 で改訂した正本 `data_schema.md` §5.4 の規定
「**保存では起動エントリ（`config/config.json` の `keymap_set_path`）を更新しない。
未設定 / 起動時に読めなかった場合のみ保存先で更新する**」を実装する。

**presentation（事実の保持）+ application（更新要否の判定）限定**。
domain 不変・JSON スキーマ不変（既存キーの書き込み契機だけを変える）。

## 対象範囲（presentation + application 限定）

### `keyseq/presentation/controllers/config_io/startup_io.py`

- `StartupIo.__init__` に `self.entry_loaded = False` を追加する
  （**起動エントリを起動時に読めたか**という事実だけを持つ）。
- `load_startup_and_config()`: 起動エントリの読込に成功して `apply_loaded_data_to_ui()` へ進む経路でのみ
  `self.entry_loaded = True` にする。**未設定 / 不在 / 読込例外の各経路では False のまま**
  （空データ起動の挙動は不変）。
- `write_startup()` は**汎用の書き出し口なので触らない**。ここで一律に True を立てると、
  起動エントリが不在のままフォント変更等で書き出したときに自己修復が失われる。

### `keyseq/presentation/controllers/config_io/keymap_set_io.py`

- `save_keymap_set_to()`: `config_service.save_runtime_data(...)` の呼び出しへ
  `startup_entry_loaded=self._app.startup_io.entry_loaded` を追加する。
  保存成功後（`self._app._startup_settings = startup_payload` の直後）に
  `self._app.startup_io.entry_loaded = True` を立てる
  （書かれた場合はそのパスが直前に保存成功しており読める。書かれなかった場合は既に True）。
- `set_startup_keymap_set()`: `startup_saved` が真のとき `self._app.startup_io.entry_loaded = True`
  を立てる（選択したファイルは直前に `load_runtime_data_from_keymap_set_path` で読込成功している）。

### `keyseq/application/config_service/__init__.py`

- `save_runtime_data` にキーワード専用引数 `startup_entry_loaded: bool = False` を追加し、
  `save_plan_execution.save_runtime_data` へそのまま渡す。

### `keyseq/application/config_service/save_plan_execution.py`

- `save_runtime_data` に同引数を追加し、`split_payloads.build_split_save_payloads` へ渡す。
- `resolve_child_save_targets` は**変更しない**（`startup_data=None` で payload を捨てるため、
  既定値 False のままで挙動が変わらない）。

### `keyseq/application/config_service/split_payloads.py`

- `build_split_save_payloads` に同引数を追加し、`build_startup_payload` へ渡す。
- `build_startup_payload`（`:359` の代入）を条件化する。
  **既存値（`startup_data` 由来）が空でない文字列**で、**かつ `startup_entry_loaded` が真**なら
  `keymap_set_path` を**据え置く**。それ以外（キー無し / 空 / 非文字列 / 起動時に読めなかった）は
  従来どおり `service.to_config_relative_or_absolute(keymap_set_path, config_root)` で更新する。
  `payload.pop("config_path", None)` 以降の他キーの扱いは**不変**。

### `instructions/common/codebase_map.md`

- `:205`（KeymapSetIo の「保存成功時は …`keymap_set_path` が保存先へ更新される」）を改訂後の挙動へ直す。
- StartupIo の節（`:206-212` 付近）へ `entry_loaded` の保持と**更新契機 3 つ**
  （起動読込の成功 / 保存の成功 / メニュー指定の成功）を 1〜2 行で追記する。

### テスト

`tests/test_config_service.py`（application 層）:

1. 起動エントリあり + `startup_entry_loaded=True` → **据え置き**
2. 起動エントリあり + `startup_entry_loaded=False` → 保存先へ更新
3. 起動エントリが**空文字 / キー無し / 非文字列**のいずれか + True → 保存先へ更新
4. 据え置き時も**他キーが従来どおり保存される**（`ui_font_delta_pt` / `last_used_directory` / 未知キー）

`tests_ui/test_config_io_characterization_keymap_set_startup.py`（presentation 経路）:

5. 起動エントリを読めた起動 → 保存しても `config.json` の `keymap_set_path` が変わらない（**別名保存を含む**）
6. 起動エントリが**不在**の起動 → **最初の保存で更新**され、**2 回目の別名保存では動かない**
7. `set_startup_keymap_set()` の後の保存で据え置き

### 設計メモ / 制約

- **判定（ポリシー）は application、事実（起動時に読めたか）は presentation**。
  presentation 側で「書くかどうか」を分岐させない。
- 新引数の**既定値は False**（＝従来どおり更新）。既存の直接呼び出しの挙動を変えないため。
- 既存 4 アサーション（`tests/test_config_service.py:66` / `:127` / `:2516` /
  `tests_ui/test_config_io_characterization_keymap_set_startup.py:1306`）は
  `startup_data={}` か `write_startup` 経由のため**修正不要の見込み**。
  実測で確認し、**落ちた場合のみ**前提を直す（先回りで書き換えない）。
- `write_startup` のシグネチャと既存キー保持（`base.update(current)`）は**不変**。
- `entry_loaded` は**起動時の事実**であり、実行中に外部でファイルが消えても追従しない
  （§5.4「起動時の実読込結果で判定する」どおり）。

## 読むファイル

- `instructions/common/spec_detail/data_schema.md:104-135` — §5.4 の改訂後の規定（task_01 の成果・実装の根拠）
- `keyseq/presentation/controllers/config_io/startup_io.py` — 全体（約 80 行・編集対象）
- `keyseq/presentation/controllers/config_io/keymap_set_io.py:101-150` / `:626-665` — 編集対象の 2 メソッド
- `keyseq/application/config_service/split_payloads.py:23-90` / `:347-370` — 編集対象
- `keyseq/application/config_service/save_plan_execution.py:21-35` / `:125-145` / `:145-175` — 編集対象と非対象の境界
- `keyseq/application/config_service/__init__.py:311-327` — `save_runtime_data` のシグネチャ（編集対象）
- `tests/test_config_service.py:52-75` — 既存の `save_runtime_data` 単体テストの書き方（手本）
- `tests_ui/test_config_io_characterization_keymap_set_startup.py:1280-1315` — tests_ui の組み立て方（手本）
- `instructions/common/codebase_map.md:200-215` — 更新対象の記述

## 含まない

- 正本改訂 = **task_01**（完了済）
- `decisions_archive/26` / `current.md` の完了記載 / `/refactor_check` = **task_03**
- 起動時に読めなかったときの通知・起動対象の可視化 UI・起動エントリの解除手段（phase.md「含まない」）
- `startup_io.py` の `keymap_set_path` の**型正規化**（phase 25 残件①・別件）
- `resolve_child_save_targets` / `write_startup` / `load_startup_settings` の挙動変更
- 孤児棚卸しの走査範囲の変更（`orphan_sweep_io.py` は読むだけで編集しない）
- `config.json` の他キーの書き込み契機の見直し

## 確認

python は**リポジトリルートの `.venv`**（worktree からは `..\..\..\.venv\Scripts\python.exe`）で実行する。

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests` が全 pass
- `-m unittest discover -s tests_ui` が全 pass
  （`tests_ui/test_dialog_teardown_flows.py` の Escape 依存テストは負荷下で不安定
  〔[idea_18](../../../backlog/idea_18_escape_delivery_flaky_test.md)〕。落ちたら再実行して本タスクとの
  関係を切り分ける）
- `-m tests.smoke_app` が pass
- 追加テスト **7 ケースすべて** pass
- `git diff` に無関係な整形変更が含まれていない

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視: **本タスク完了後にユーザーが実施**（①構成セットを別名保存 → 再起動して起動対象が
  変わらないこと ②メニュー「起動時に読む構成セットを指定…」が効くこと
  ③`config.json` の `keymap_set_path` を手で消して起動 → 保存 → 再起動で自己修復すること）。
  結果の報告を受けてから task_03 へ進む。
