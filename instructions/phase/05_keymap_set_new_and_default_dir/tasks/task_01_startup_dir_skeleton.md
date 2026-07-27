# task_01_startup_dir_skeleton

## 目的

起動時に設定ディレクトリの骨格（`config/user/{keymap_sets,keymaps,trigger_sets,hotkey_presets,sequences}`）を
一括作成する。現状は `_ensure_split_config_dirs` が**保存時**に作るため、初回 Save As の時点で
`config/user/keymap_sets/` が存在せず、`suggest_keymap_set_dialog_dir` が `config_root` へフォールバックして
config 直下が初期ディレクトリになる（暫定仕様 04 §5「起動時ディレクトリ作成」・敵対的レビュー指摘④）。

- 根拠: 暫定仕様 [04](../../../history/04_keymap_set_new_and_default_dir.md) §5 / **受入条件 2**。
- **レイヤ制約**: presentation（`app.py`）+ application（`config_service` の公開面のみ）。
  domain / infrastructure 不変・**スキーマ不変**・保存処理のロジック不変。
- **config.json 本体は起動時に書かない**（作成は従来どおり初回保存時）。

## 対象範囲（application の公開面 + presentation の起動処理 + テスト）

### `keyseq/application/config_service.py`

- `_ensure_split_config_dirs(self, config_root: str) -> None`（:926）を
  **公開名 `ensure_split_config_dirs` へリネーム**する。実装（作成するディレクトリ 7 件）は**変更しない**。
- 既存の内部呼び出し（`:226`）を新名へ追従させる。
- **互換エイリアス（旧名の横流し）は作らない**（`.claude/rules/file_organization_rules.md`「恒久互換レイヤー禁止」）。
  リネーム後に `grep -rn "_ensure_split_config_dirs" keyseq/ tests/ tests_ui/` が 0 件であること。

### `keyseq/presentation/app.py`

- `App.__init__` の `os.makedirs(self.user_root, exist_ok=True)`（:56）を
  **`self.config_service.ensure_split_config_dirs(self.config_root)`** へ置き換える。
  - `user_root` の作成は `ensure_split_config_dirs` に包含されるため、置換であって追加ではない。
  - 位置は `self.config_root` / `self.user_root` の定義後・`ConfigPaths` 構築前（現在の :56 の位置）を維持する。
- `App` の他の初期化順序・属性は変更しない。

### `tests_ui/test_startup_font_characterization.py`

- `setUpClass` の `patch.object(app_module.os, "makedirs")` は、**新経路（`config_service` 側の
  `os.makedirs`）を止められない**。このままだとテスト実行時にリポジトリ配下へ実ディレクトリが作られる。
  → `ConfigService.ensure_split_config_dirs` を patch する形へ改める
  （`patch.object(app_module.ConfigService, "ensure_split_config_dirs")`）。
  既存の `load_startup` patch と同じ手法・同じ場所で行い、**テストの検証内容（フォント/起動設定の期待値）は変更しない**。

### 新規テスト（新挙動の固定）

- `tests/`（ConfigService 単体・`tmp_path` / `TemporaryDirectory` を使用）:
  `ensure_split_config_dirs(config_root)` が `config_root` / `user` / `keymap_sets` / `keymaps` /
  `trigger_sets` / `hotkey_presets` / `sequences` の 7 ディレクトリを作ること。既存ディレクトリがあっても失敗しないこと。
- `tests_ui/`（App 起動時の呼び出し・既存の patch 手法を踏襲）:
  1. App 構築時に `ensure_split_config_dirs` が `config_root` を引数に**呼ばれる**こと。
  2. App 構築時に **`config.json` を書かない**こと（起動時に保存経路が走らないことの担保）。

### 設計メモ / 制約

- リネームを選ぶ理由: presentation から application の private メソッド（`_` 始まり）を呼ぶのは
  レイヤ境界の逸脱になるため、呼び出し口を公開名にする。新規メソッドの追加ではなく**リネーム**にして
  同じ実装が 2 つ存在する状態を作らない。
- `ConfigPaths.preferred_keymap_sets_dir()` / `suggest_keymap_set_dialog_dir()` は**変更しない**
  （ディレクトリが実在すれば既存ロジックのまま受入 2 を満たす）。

## 含まない

- `new_config` の空パス化 / `save_keymap_set` の空パス → 別名保存分岐 / 別名保存の初期ファイル名（**task_02**）
- `import_config` の無条件クリア / 空起動時の `keymap_set_path` 空化 /
  `preferred_keymap_set_path`・`normalize_keymap_set_save_path` の `default.json` 用途の整理（**task_03**）
- `prompt_if_missing` の撤去（**task_04**）
- `config_service.save_runtime_data` の子ファイル書き出しロジック（**フェーズ外** = Phase β）
- 起動時に `config.json` を作成すること（暫定仕様 §2 で明確に対象外）
- `app.py` の起動シーケンス整理・その他のリファクタ

## 確認

`.venv` の python で実行する（`..\..\..\.venv\Scripts\python.exe`。グローバル `py` は使わない）。

1. `-m compileall -q keyseq main.py tests_ui` — clean
2. `-m unittest discover -s tests` — 全 pass（新規の `ensure_split_config_dirs` テストを含む）
3. `-m unittest discover -s tests_ui` — 全 pass（新規 2 項目を含む。**既存 74 件が減らないこと**）
4. `-m tests.smoke_app` — pass
5. `grep -rn "_ensure_split_config_dirs" keyseq/ tests/ tests_ui/` — **0 件**
6. テスト実行後に**リポジトリの `config/` 配下へ新規ディレクトリが作られていないこと**
   （`git status --porcelain` で `config/` の未追跡差分が出ないこと）

## 完了条件

- 上記確認 1〜6 がすべて pass・**reviewer 採用**。
- 実機目視は本タスクでは行わず、**task_05（統合退行）でまとめて**ユーザーに依頼する。
