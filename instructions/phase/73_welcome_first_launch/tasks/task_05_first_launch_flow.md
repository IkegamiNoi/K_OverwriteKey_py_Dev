# task_05_first_launch_flow

## 目的

初回の起動を判定し、Welcome の結果（言語・キーボード配列・始め方）を起動の流れへつなぐ（暫定 56 v0.5 §3・§6）。
Welcome の窓そのものは task_06 で作り、この task では**結果を返す差し替え口**（窓を出さずに既定の結果を返す関数）を置く。
**presentation 限定（`main.py`・`app.py`・新規 `presentation/welcome/`・`keymap_set_io.py`）+ 言語ファイル・application / domain 不変・JSON スキーマ不変**。

## 対象範囲（presentation 限定）

### 新規 `keyseq/presentation/welcome/`（パッケージ）

- `welcome_result.py`:
  - `WelcomeResult`（frozen dataclass）: `language: str`・`layout_id: str`（`"us_tkl"` / `"jis"`）・`start: str`（`"sample"` / `"empty"`）
  - `estimate_layout_id(language: str) -> str`: `"ja"` → `"jis"`・それ以外 → `"us_tkl"`
  - 定数 `JIS_LAYOUT_ID = "jis"`・`JIS_LAYOUT_PATH = "user/keylayout/jis.json"`（外部の配列として登録するパス・`config/` 基準）
- `first_launch.py`:
  - `run_first_launch_welcome(app) -> WelcomeResult`: **この task では窓を出さず**、`WelcomeResult(language=<今の言語>, layout_id=estimate_layout_id(<今の言語>), start="sample")` を返す（task_06 で窓を出す実装に替える。差し替え口であることを docstring に書く）
  - `is_first_launch(paths) -> bool`: `config/config.json`（`paths.preferred_startup_path()`）も旧 `settings/startup.json`（`resolve_startup_path()` が返す旧パス）も**無い**とき真

### `main.py`

- `App()` を `App(first_launch_welcome=True)` にする（実際の起動だけ初回の判定をする）

### `keyseq/presentation/app.py`

- `__init__(self, *, first_launch_welcome: bool = False)`
- 起動設定のパスを決めた直後（:123 付近・画面の描画より前）に `self._first_launch = first_launch_welcome and is_first_launch(self.paths)`。真なら `self.withdraw()`
- テーマの適用の後・`self.data = ...`（:139）の前で、初回なら:
  1. `result = run_first_launch_welcome(self)` → `set_language(result.language)`・`self._startup_settings["ui_language"] = result.language`
  2. `result.start == "sample"` なら `self.config_service.install_sample(config_root=self.config_root, keyboard_layout_id=result.layout_id, external_layout_path=JIS_LAYOUT_PATH if result.layout_id == JIS_LAYOUT_ID else "")`。
     status が `written` / `existing` → `self._startup_settings["keymap_set_path"] = "sample/keymap_sets/sample.json"`（`config/` 基準の相対）。
     `incomplete` / `failed` → 空で始める扱いにし、知らせる内容（status と error）を覚えておく
  3. 結果を `self._welcome_result` に覚える（空で始めるかの判定と配列に使う）
- `load_startup_and_config()`（:349）の直後・`self.layout.reload_keyboard_layouts()` の前で、初回かつ空で始める（選んだ・またはサンプルの失敗）なら `self.keymap_set_io.start_empty(layout_id=..., external_layout_path=...)` を呼ぶ
- その後（初回のときだけ）:
  - `self.startup_io.write_startup({"ui_language": ..., ["keymap_set_path": ...]})` で起動設定ファイルを書く（失敗の知らせは今の `write_startup` のまま）
  - サンプルが `incomplete` / `failed` だったら `messagebox.showwarning`（新しい文言・status と error を差し込む）
  - `self.deiconify()`

### `keyseq/presentation/controllers/config_io/keymap_set_io.py`

- `start_empty(self, *, layout_id: str, external_layout_path: str = "") -> None`: メニュー「新規」（`new_config`）と同じ組み立て（`new_base_data` → `apply_global_defaults` → `normalize_runtime_data` → 画面への反映）で、確認ダイアログ・クリップボードの消去・一時メッセージは出さない。
  `keyboard_layout = layout_id`・`external_layout_path` があれば `external_keyboard_layouts = [{"path": ...}]`。未保存の印は「新規」と同じ扱い。
  `new_config` と共通にできる部分は小さな private 関数に分けてよい（`new_config` の挙動は変えない）

### `keyseq/shared/i18n/locales/ja.json` / `en.json`

- サンプルの書き出しに失敗したときの知らせ（題名・本文〔status / error を差し込む〕）のキーを両方に足す（キー名は `welcome.` で始める。英語は `ui_terms.md` §2・§3）

### テスト

- `tests/`: `estimate_layout_id`・`is_first_launch`（一時フォルダ・新パスあり / 旧パスあり / どちらも無し）
- `tests_ui/`（**実際の `config/` に書かない**: `install_sample`・`write_startup`・`run_first_launch_welcome`・`is_first_launch` を patch する）:
  - `App()`（引数なし）は初回の判定をせず Welcome を呼ばない（`run_first_launch_welcome` が呼ばれない）
  - `App(first_launch_welcome=True)` + 初回でない → 呼ばない
  - 初回 + `start="sample"` + `install_sample` が `written` → `_startup_settings["keymap_set_path"]` がサンプル・`write_startup` に `ui_language` と `keymap_set_path`・警告なし
  - 初回 + `start="empty"`・`layout_id="jis"` → `start_empty` で 1 キーマップ・トリガーなし・`keyboard_layout == "jis"`・登録あり・`keymap_set_path` を書かない
  - 初回 + `install_sample` が `failed` → 空で始める・警告を出す（`messagebox.showwarning` を patch）
  - 初回 + `result.language == "ja"` → 画面の文言が日本語（`set_language` が画面の構築より前）・`ui_vars` の言語の値が `ja`

### 設計メモ / 制約

- 初回でない起動（`first_launch_welcome=False` を含む）の流れは**今と 1 行も変えない**（`_first_launch` が偽なら新しい分岐に入らない）
- `withdraw` / `deiconify` は初回のときだけ
- `run_first_launch_welcome` は import 時に `tr` を評価しない・窓を作らない（この task）
- `keyseq/presentation/welcome/` の各ファイルは小さく（各 100 行以内目安）

## 読むファイル

- `main.py`（全体）/ `keyseq/presentation/app.py:100-160`・`:330-360`・`:515-536`（言語の切り替えの書き方）
- `keyseq/presentation/controllers/config_io/startup_io.py:1-70`
- `keyseq/presentation/controllers/config_io/keymap_set_io.py:55-95`（`new_config`）
- `keyseq/presentation/config_paths.py:1-50`
- `keyseq/application/config_service/sample_install.py`（`SampleInstallResult` の status のみ）・`keyseq/application/config_service/__init__.py` の `install_sample` の委譲
- `keyseq/shared/i18n/catalog.py`（`set_language` / `resolve_language` / `current_language` の名前の確認のみ）
- 手本のテスト: tests_ui で `App()` を作り `StartupIo` を patch しているもの 1 つ（例 `tests_ui/test_capture_ime_entries.py:24-60`）
- 主入力: `instructions/history/56_welcome_first_launch.md` §3・§6

## 含まない

- Welcome の窓（言語・配列・使い方・始め方・ヘルプ）（task_06）
- ヘルプのメニューからの再表示（task_07）
- サンプルの中身・書き出しの処理（task_03・task_04 で済み）
- 正本の更新（task_09）

## 確認

- 追加したテストが通る（verifier が `.venv` で実行）
- `python -m compileall -q keyseq`・`python -m unittest discover -s tests`・`python -m unittest discover -s tests_ui`・`python -m tests.smoke_app` が通る
- 実行後に worktree の `config/` に新しいファイル（`config/sample/` 等）が増えていない（verifier が `git status --ignored config` で確認）

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視（初回の起動・2 回目の起動）は task_09 でまとめて実施
