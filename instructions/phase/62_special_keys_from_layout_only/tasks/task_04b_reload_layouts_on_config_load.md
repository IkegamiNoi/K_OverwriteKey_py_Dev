# task_04b_reload_layouts_on_config_load

## 目的

構成（キーマップセット）を読み込んだとき、その構成の外部レイアウトの登録（`external_keyboard_layouts`）を読み直す。
今は登録済みのレイアウト（`_keyboard_layout_entries`）が前の構成のままで、送信（暫定 45 §4.4・登録済みの値を引く）が前の構成のレイアウトの走査コードを使い得る。
読み直しの前には、押したままのキーをすべて離す（暫定 45 §6）。

- 起票: 完了判定前レビューの指摘（Codex medium・deep-reviewer 中）
- ユーザー判断: 2026-10-18・案 a
- 範囲: **presentation 限定**（`app.py` の 1 か所）。JSON スキーマ不変

## 対象範囲（presentation 限定）

### `keyseq/presentation/app.py`

- `_sync_control_vars_from_data`（:590-599）の最後の `self.layout.sync_keyboard_layout_controls()` を `self.layout.reload_keyboard_layouts()` に変える
  - `reload_keyboard_layouts` は、離す → 登録の収集 → `sync_keyboard_layout_controls` の順に処理する（`layout_controller.py:203-209`）
- 起動時（`app.py:294`）の `reload_keyboard_layouts` との二重呼び出しにならないか確かめる
  - 起動の流れで `_sync_control_vars_from_data` が `:294` の後にも呼ばれるなら、二重になっても害は無い（登録の収集が 2 回になるだけ）。その場合は変えずに、確かめた結果を報告する

### テスト

- 既存の tests_ui で `_sync_control_vars_from_data` / 構成の読込を通すテストがあれば、それに合わせる
- 単体テストを 1 つ追加する（`tests/` または `tests_ui/` の既存の手本に合わせる）: `_sync_control_vars_from_data` が `layout.reload_keyboard_layouts` を呼ぶ（`layout` を `Mock` にする）

## 読むファイル

1. `keyseq/presentation/app.py:285-300` / :585-600
2. `keyseq/presentation/controllers/layout_controller.py:195-240`
3. `grep -rn "_sync_control_vars_from_data\|sync_keyboard_layout_controls" tests tests_ui` で当たるテスト

## 含まない

- 外部レイアウトの読込の仕組み（`collect_keyboard_layouts`）の変更
- 受け取り側の毎回の読み直し（idea_51）
- 正本の文言（task_04 でメインが直す）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- 追加・変更したテストが pass
- 既存テストが全 pass: `unittest discover -s tests` / `unittest discover -s tests_ui` / `-m tests.smoke_app`

## 完了条件

- 上記の確認が pass し、**reviewer が採用**していること
- 実機目視は不要（構成の読込の既存の流れを、読み直しを含む形に変えるだけ）
