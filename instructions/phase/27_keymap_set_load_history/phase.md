# phase.md

## フェーズ名

構成セットの読み込み履歴管理（keymap_set_load_history）

## フェーズの目的

構成セット（keymap_set）を**アプリ内の履歴から開き直せる**ようにする。
ファイルメニューに「履歴から読み込む…」を追加し、**直近 20 件 + ユーザーが作る分類**を
`ttk.Treeview` の折り畳み UI で扱う。履歴からの削除と、直近から分類へのコピーができる。

**新規 JSON を 1 つ増やす**（`config/keymap_set_history.json`）。**既存 JSON のスキーマは不変**で、
`config.json` にはキーを追加しない。**対象レイヤ = domain / application / presentation の 3 層**
（規則 = domain / 永続化 = application / 操作の事実と UI = presentation）。

- 起票元: ユーザー要望（2026-09-21）・idea なし。
- 主入力（暫定仕様）: [21_keymap_set_load_history.md](../../history/21_keymap_set_load_history.md)
  （**v0.4・ユーザー確定済・実装着手可**）。**フェーズ中はこれが正**（正本は直接改訂しない）。
- モード: **暫定仕様先行モード**。番号対応: phase 27 / 暫定 21 / decisions 27。

## 確定（ユーザー 2026-09-21）

暫定仕様 21 §2 が正。要点のみ再掲する。

- **保存先 = `config/keymap_set_history.json`（固定パス）**。config.json にキーを増やさない。
- **記録の契機 = 読込または保存が成功し、空でないパスが確定したとき**、その**実保存先**を記録する。
  `app.py:76` の初期代入 / 新規作成 / Import / 例の復元は対象外。
- **`recent` の先頭が既に同一パスなら書き込まない**（通常の起動ではディスクに触らない）。
- **履歴ファイルが読めないときは退避してから作り直す**（`*.broken*.json`。上書きで消さない）。
- **永続化に成功してから UI を確定する**。失敗した編集は一覧へ反映しない。
- **分類は 1 階層・名前順表示**。追加 / リネーム / 削除（配下ごと）。同名不可。
- **Treeview は `ui_font_delta_pt` に追従**させる（リポジトリ初採用）。
- **孤児棚卸しは履歴を「参照」と見なさない**（走査範囲・孤児判定は不変）。

## スコープ

### 含む

- 新規 JSON `config/keymap_set_history.json` の読み書き（退避 = 暫定仕様 §4.4 を含む）。
- domain の純関数（正規化 / 重複統合 / 上限 20 / 分類の整列）。
- 記録の**単一の口**（`record()`）と、暫定仕様 §4.1 の呼び出し点への接続。
- **パス指定の共通読込入口**の追加（現状はパス指定で読む公開入口が無い）。
- 履歴ダイアログ（`ttk.Treeview`・ボタン群・フォント追従）と整形関数、メニュー項目の追加。
- 既存テストの更新: `INTERNAL_MODULE_NAMES`（追加しないと確実に赤）/ `DIALOG_FILES`。
- 既存 characterization テストが**リポジトリルートへ履歴ファイルを生成しない**ための patch。
- フェーズ末の正本反映（`data_schema.md` §5.12 新設ほか）と暫定仕様の凍結。

### 含まない（後送り）

暫定仕様 21 §10 が正。主なもの: 分類の入れ子・D&D・分類 → 分類のコピー / 任意ラベル・読込日時 /
検索・一括操作 / `*.broken*.json` の管理 UI / `last_used_directory` の復活 /
構成セット以外の履歴 / 起動エントリの扱いの変更（phase 26 の規定を維持）。

## このフェーズで読むファイル

1. **主入力** `instructions/history/21_keymap_set_load_history.md`（v0.4・全文）
2. `keyseq/domain/config.py` の `coerce_label` / `coerce_key_name`（型正規化の手本。**追記はしない**）
3. `keyseq/application/config_service/split_loading.py:45-92`（別ファイル JSON の読込と `None` 縮退の手本）/
   `keyseq/application/config_service/__init__.py:24-32`（クラス定数）・`:610-637`（書込の手本）・`:725,761`（パス解決）
4. `keyseq/infrastructure/json_repository.py`（原子的置換）
5. `keyseq/presentation/controllers/config_io/keymap_set_io.py:32-47`（未保存確認）・`:49-146`（新規 / 保存）・
   `:529-557`（読込）・`:626-665`（起動セット指定）
6. `keyseq/presentation/controllers/config_io/startup_io.py`（全体・約 80 行）
7. `keyseq/presentation/config_paths.py:62-80`（`normalize_keymap_set_save_path`）
8. `keyseq/presentation/dialogs/orphan_sweep_dialog.py`（ダイアログ骨格の手本）/
   `keyseq/presentation/controllers/config_io/quarantine_manage_io.py` +
   `keyseq/presentation/quarantine_manage_text.py`（3 点セットの責務分担の手本）
9. `keyseq/presentation/modal.py:65,88-90`（`grab_modal`）/ `keyseq/presentation/views/menu_bar.py:8-21`
10. `keyseq/presentation/theme.py` のフォント適用（`ttk.Style` の扱いを確認する範囲のみ）
11. テスト: `tests/test_config_service_contracts.py:14-18,172-180` /
    `tests_ui/test_dialog_teardown_flows.py:16-33` /
    `tests_ui/test_config_io_characterization_keymap_set_startup.py:118-124` /
    `tests_ui/test_quarantine_manage_flow.py`（UI フローの手本）

## タスク

- task_01: **domain の純関数**（`keyseq/domain/keymap_set_history.py` 新規）— 型不正の正規化 /
  重複統合 / 上限 20 / 分類の整列。比較キーは**受け取る**（`config_root` に依存しない）。+ 単体テスト
- task_02: **application の永続化**（`config_service/keymap_set_history.py` 新規 + `ConfigService` の委譲）
  — 読込（`None` 縮退）/ **退避と作り直し**（§4.4）/ 原子的書込 / 保存表記への正規化と比較キー生成。
  + `INTERNAL_MODULE_NAMES` の更新 + 単体テスト
- task_03: **記録経路の接続**（`controllers/config_io/keymap_set_history_io.py` 新規の `record()` +
  §4.1 の呼び出し点 + **パス指定の共通読込入口**を `keymap_set_io.py` へ追加）。
  + 既存 characterization テストの patch + テスト
- task_04: **履歴ダイアログ**（`dialogs/keymap_set_history_dialog.py` / `keymap_set_history_text.py` 新規 +
  `menu_bar.py` へ 1 行）— Treeview・フォント追従・ボタン群・再描画・読み取り専用モード。
  + `DIALOG_FILES` の更新 + `tests_ui` のフローテスト
- task_05: **正本反映と完了**（`data_schema.md` §5.12 新設 / `features.md` §4.6 / `codebase_map.md` /
  `data_schema/5_08_09_orphan_sweep.md` の補記要否判断〔暫定仕様 §9〕/
  **暫定仕様 21 の凍結** / `decisions_archive/27` / `decisions.md` 索引 / `current.md` / `/refactor_check`）

## レビュー方針

- 共通観点は `.claude/rules/review.md`。各タスクで `reviewer` を 1 回。
  統合確認とフェーズ完了判定では `deep-reviewer` + Codex レビューを併用する。
- **本フェーズ固有**:
  - **記録が単一の口（`record()`）に閉じているか**。呼び出し点が暫定仕様 §4.1 の表と一致し、
    **除外すべき経路（`app.py:76` / `new_config` / `import_config` / `restore_default`）を拾っていないか**。
  - **application の下位ローダー（`load_runtime_data_from_keymap_set_path`）に副作用が入っていないか**。
  - **テストがリポジトリルートを汚していないか**（実行後に `keymap_set_history.json` が
    worktree ルートへ生成されていないことを実測で確認する）。
  - **破損ファイルの退避でデータが失われないか**（上書きしていないか・退避失敗時に書かないか）。
  - **永続化の成否と UI の確定順序**（失敗した編集が一覧に残っていないか）。
  - **先頭一致 no-op が永続化済みの内容に対して判定されているか**（メモリ先行更新になっていないか）。
  - **依存方向**: domain は `config_root` に依存しない / application は presentation を参照しない。
  - 孤児棚卸しの**候補側の分類結果**が変わっていないこと。
