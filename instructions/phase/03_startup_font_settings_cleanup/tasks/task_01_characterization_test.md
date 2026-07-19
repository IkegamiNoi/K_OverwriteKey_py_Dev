# task_01_characterization_test

## 目的

移設前の安全網。現行の起動設定 / フォント設定 3 メソッド
（`App._coerce_font_delta` / `App._load_startup_settings` / `App.set_ui_font_delta`）の
**現行挙動を特性テストで固定**する（暫定仕様 [§9 安全網](../../../history/02_startup_font_settings_cleanup.md) /
受け入れ条件 §8-8・§8-12）。挙動不変リファクタ（task_02〜04）の前後で振る舞いがズレないことを保証する土台。

- **実装コード（`keyseq/` 配下）は一切変更しない**。テスト（`tests/` または `tests_ui/`）の**新規追加のみ**。
- レイヤ制約: presentation の現行 API に対するテスト追加のみ。スキーマ不変・挙動不変。

## 対象範囲（テスト新規追加のみ・実装コード不変）

現行 3 メソッドはいずれも `App`（`keyseq/presentation/app.py`）のメソッドであり、
現時点では App インスタンス経由でしか呼べない。よって特性テストは **`tests_ui/`**
（App を生成する既存の枠組み。`tests_ui/test_app_ui_flows.py` に準拠）へ新規追加する。
ファイルは新規 `tests_ui/test_startup_font_characterization.py` を作成する
（既存 `test_app_ui_flows.py` のアサーションは変更しない＝スコープ外）。

### 1. coerce_font_delta の値テーブル（現行 `App._coerce_font_delta`・`app.py:357-366`）

App インスタンスの `app._coerce_font_delta(value)` を直接呼び、以下を固定する:

- 非数値（`"x"` / `None` / `object()` 等） → `0`
- 範囲内整数（`-3, -1, 0, 2, 3`） → 同値
- 範囲外（`-4, -100`） → `-3` / （`4, 100`） → `3`（下限 `-3`・上限 `+3` クランプ）
- 文字列数値（`"2"`, `"-3"`） → `int` 変換後の値（`2`, `-3`）
- 境界（`-3`, `+3`） → 同値

### 2. 起動設定ローダの真理値表（現行 `App._load_startup_settings`・`app.py:376-392`）

`app.config_service.load_startup` と `keyseq.presentation.app.messagebox.showwarning` を
テスト内で一時差し替え（monkeypatch / `unittest.mock.patch`）し、`app._load_startup_settings()`
の返り値と警告呼び出しを、暫定仕様 §5 の真理値表どおりに固定する:

| ケース | `load_startup` 差し替え | 警告 | 返り値の検証 |
|---|---|---|---|
| ファイル欠損相当 | `{}` を返す | showwarning **未呼び出し** | `ui_font_delta_pt==0` / `prompt_if_missing==True` |
| JSON 破損 / 読込例外 | 例外送出 | showwarning **1 回**・title=「startup.json 読込失敗」・body=`f"startup.json の読込に失敗しました。\n{exc}\n\n既定設定で起動します。"`（**1 文字一致**） | `ui_font_delta_pt==0` / `prompt_if_missing==True` |
| 非 dict | 文字列 / list を返す | showwarning **未呼び出し** | 既定化され `ui_font_delta_pt==0` / `prompt_if_missing==True` |
| 正常 dict | `{"ui_font_delta_pt": "5", "prompt_if_missing": 0}` を返す | showwarning 未呼び出し | `ui_font_delta_pt==3`（coerce クランプ）/ `prompt_if_missing==False`（bool 化） |

### 3. 未知キー全保持（受け入れ条件 §8-12・後方互換の要）

`load_startup` 差し替えで `{"keymap_set_path": "X.json", "last_used_directory": "D", "ui_font_delta_pt": "1"}`
を返させ、`app._load_startup_settings()` の返り値が:

- `keymap_set_path == "X.json"` / `last_used_directory == "D"` を**保持**する
- 既知2キー（`ui_font_delta_pt` → `1`・`prompt_if_missing` → 既定 `True`）のみ正規化される

ことを固定する（未知キーが消えないことの回帰防止）。

### 4. フォント変更フロー（現行 `App.set_ui_font_delta`・`app.py:227-243`）

App インスタンスに対し `app.set_ui_font_delta(delta)` を呼び、以下を固定する:

- **差分なし早期 return**: 現在値と同じ delta を渡すと、`ui_vars.ui_font_delta_var` / `_ui_font_delta_pt` /
  フラッシュメッセージが変化しないこと（`config_io.write_startup` を差し替えて**呼ばれない**ことを確認）。
- **状態反映**: 異なる delta を渡すと `_ui_font_delta_pt` と `ui_vars.ui_font_delta_var.get()` が新値になること。
- **メニュー再構築の副作用**: `keyseq.presentation.app.build_menu_bar` を差し替えて呼び出しを記録し、
  delta 変更時に **`build_menu_bar` が呼ばれ、`bind_menu_shortcuts` は呼ばれない**ことを固定（受け入れ条件 §8-7）。
- `config_io.write_startup` を差し替え、永続化が**呼ばれる**こと（引数に `ui_font_delta_pt` を含む）を確認する
  （実ファイル保存はしない＝config/ を汚さない）。

## 設計メモ / 制約

- **実行環境**: python は必ずリポジトリルートの `.venv`（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
- **config/ を汚さない**: 永続化 (`config_io.write_startup` / `save_startup`) は必ず差し替え、実ファイル書き込みをしない。
  グローバルフックは開始しない（`start_hook` を呼ばない）。既存 `test_app_ui_flows.py` の作法に合わせる。
- **差し替え対象の名前解決**: `messagebox` / `build_menu_bar` / `bind_menu_shortcuts` は
  `keyseq.presentation.app` の名前空間で参照されている実体を差し替える（import 済みシンボルを patch）。
- **現行 API を対象にする理由**: 3 メソッドは現時点で App 専用。安全網は「今存在する挙動」を固定するのが目的。
  task_02（coerce → `theme.py`）/ task_03（ローダ → `startup_settings.py`）/ task_04（案 A 分割）で
  ロジックが自由関数へ移る際、**呼び出し先の差し替えは各移設タスクで行い、本テストの挙動アサーション（値・回数・文言）は
  同一契約として維持**する。移設後の tk 不要な自由関数向け単体テスト（`tests/`）は各移設タスクで追加する
  （暫定仕様 §9 の「fake config_service / tk 不要」ユニットテストはそちらで実現）。
- **やってはいけない**: 実装コードの変更、既存テストのアサーション変更、後続タスク（移設）の先取り。

## 含まない

- `theme.coerce_font_delta` / `startup_settings.load_startup_settings` など**移設後の自由関数の新規実装・テスト**（task_02 / task_03）。
- `set_ui_font_delta` の案 A 分割（`_apply_font_delta` 抽出）・`UiVars` 引数化（task_04）。
- `config_io_controller.py:278` の逆参照解消（task_02）。
- 実装コードの変更全般・既存テストの改変。正本反映（task_05）。

## 確認

`.venv` python で以下を実行し、いずれも pass すること:

- 新規特性テスト: `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui -v`
  （追加した `test_startup_font_characterization.py` の全ケースが pass）
- 静的確認: `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py`（clean）
- 既存回帰: `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests`（従来 77 pass 維持）/
  `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui`（従来 16 + 新規分が pass）/
  `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app`（pass）
- `git diff --stat` に `keyseq/` 配下の変更が含まれない（テスト追加のみ）ことを確認する。

## 完了条件

- 上記「確認」全 pass・実装コード（`keyseq/`）無変更・**reviewer 採用**（CLAUDE.md レビュー必須）。
- 実機目視: 本タスクでは不要（安全網の追加のみ）。実機目視は task_04 完了後にまとめて実施する。
