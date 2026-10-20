# task_01_unify_layout_path_base

## 目的

外部キーレイアウトの登録（`external_keyboard_layouts[].path`）が読込のたびに `config/` が 1 段増えて消える不具合を直す（[idea_13](../../../backlog/idea_13_external_layout_path_base_asymmetry.md)「実害の確認」）。
登録・読込・表示の 3 か所を正本 `data_schema.md` §5.7 どおり **`config` ルート基準の相対（`/` 区切り）・config 外は絶対** へそろえる。
**application（`split_loading`）+ presentation（`layout_controller`）限定。保存（`split_payloads`）・孤児検出（`reference_scan`）・domain・JSON スキーマは不変。**

## 対象範囲（application + presentation・3 か所の基準の変更とテストのみ）

### `keyseq/application/config_service/split_loading.py` — `normalize_external_keyboard_layouts`

- `config_root` 基準で解決した後、**親（`dirname(config_root)`）基準の相対へ戻す処理をやめ**、`service.to_config_relative_or_absolute(resolved_path, config_root)` の結果を runtime の `path` にする（config 配下 → `config` ルート基準の相対・`/` 区切り / 外 → 絶対・`/` 区切り）。
- `base_dir` 変数・`os.path.relpath` の try/except は不要になれば削除する。空・非文字列の除去など他の挙動は変えない。
- 結果として **同じ入力を何度通しても値が変わらない**（冪等）こと。

### `keyseq/presentation/controllers/layout_controller.py`

- 登録 `add_external_keyboard_layout`（:302）: `self._app.paths.to_rel_if_possible(path)` → `self._app.paths.to_config_relative_or_absolute(path)`。重複判定（:303）は文字列比較のまま。
- 表示 `reload_keyboard_layouts`（:205-208）: `collect_keyboard_layouts(..., base_dir=self._app.base_dir)` の基準を `self._app.paths.config_root` へ。
- 表示 `get_current_keyboard_layout`（:184）: `resolve_registered_layout_path(entry.path, base_dir=self._app.base_dir)` の基準を `self._app.paths.config_root` へ。
- 削除 `delete_keyboard_layout` は変えない（`entry.path` は記録表記のまま持つので文字列比較で合う）。

### テスト

- `tests/test_config_service.py:1947-1953`: 期待値を「`config` ルート基準の相対（`/` 区切り）」へ見直す（相対入力 / 絶対入力の両 subTest）。
- `tests/test_config_service.py` に追加（既存の split_loading のテストの近く）:
  - `user\keylayout\jis.json` / `user/keylayout/jis.json` を入力 → `user/keylayout/jis.json`
  - **3 回続けて通しても `user/keylayout/jis.json` のまま**（冪等・idea_13 の再現手順の逆）
  - config 外の絶対パス → 絶対パス（`/` 区切り）のまま・相対に化けない
- `tests/test_layout_controller_scan_code.py:32-38`・`:67`: スタブ app に `paths=SimpleNamespace(config_root="cfg")` を足し、期待値を `base_dir="cfg"` へ。
- 登録の表記のテスト（新規・`tests/` 配下の適切なファイル。既存に登録のテストがあればそこへ）: `filedialog.askopenfilename` と `load_layout_from_json`・`reload_keyboard_layouts`・`persist_keyboard_layout_selection` を差し替え、`<config_root>/user/keylayout/jis.json` を選ぶと `data["external_keyboard_layouts"]` に `{"path": "user/keylayout/jis.json"}` が入る。

### 設計メモ / 制約

- 解決・相対化は既存の `ConfigService.to_config_relative_or_absolute`（`config_service/__init__.py:742-748`）/ `ConfigPaths.to_config_relative_or_absolute`（`config_paths.py:94-95`）を使う。新しい共通関数を作らない。
- **既存の壊れた値の移行・重複除去はしない**（ユーザー判断 2026-10-20）。`config\user\…` や `config/config/…` の救済分岐を入れない。
- `ConfigPaths.to_rel_if_possible`（`config_paths.py:126-127`）は唯一の呼び出し元が :302 のため、置き換え後に**削除する**（2026-10-20 時点で他に呼び出し元・テストなし）。

## 読むファイル

1. `keyseq/application/config_service/split_loading.py:540-568`（編集対象）
2. `keyseq/presentation/controllers/layout_controller.py:178-210`・`:290-313`（編集対象）
3. `keyseq/application/config_service/__init__.py:735-750`（`to_config_relative_or_absolute`）
4. `keyseq/presentation/config_paths.py:10-14`・`:94-98`・`:126-127`（削除対象）
5. `keyseq/presentation/keyboard_layouts.py:272-295`・`:335-338`（`collect_keyboard_layouts` の基準の使い方・変更しない）
6. `tests/test_config_service.py:1900-1953`（手本と期待値の修正箇所）
7. `tests/test_layout_controller_scan_code.py:1-70`
8. 正本: `instructions/common/spec_detail/data_schema.md:284-303`（§5.7）

## 含まない

- 正本・codebase_map の更新（task_02）
- 孤児検出 `reference_scan.py` の superset（残す・ユーザー確定）
- 保存経路 `split_payloads.py` の変更
- 既存の壊れた値の移行・重複除去・登録時の重複判定の解決後比較
- 他のパス（keymaps・trigger_set 等）の扱い

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` clean
- 追加・修正した単体テスト pass（上記「テスト」の各項目）
- `-m unittest discover -s tests` 全 pass / `-m unittest discover -s tests_ui` 全 pass（単独実行）/ `-m tests.smoke_app` pass
- grep: `external_keyboard_layouts` の解決に `base_dir`（`dirname(config_root)`）を使う箇所が `reference_scan.py` の superset 以外に残っていない

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は**本タスクで実施**（ユーザー）: 既存の JSON の外部レイアウトの要素を手で直す（または削除して再登録）→ 外部レイアウトを登録 → 再起動して一覧に残る → もう一度再起動しても構成セットの JSON の値が `user/keylayout/jis.json` のまま。
