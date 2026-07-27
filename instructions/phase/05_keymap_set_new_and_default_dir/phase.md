# phase.md

## フェーズ名

新規作成と保存先ディレクトリの整理（keymap_set_new_and_default_dir）

## フェーズの目的

構成セット（keymap_set）の**新規作成・保存の挙動**をユーザーの想定へ合わせる。
新規作成直後の「無言で `default.json` に上書き」を解消し、**既定の保存先を固定ファイルから
ディレクトリ `config/user/keymap_sets/` へ**移す。あわせて死にフラグ `prompt_if_missing` を撤去する。

- **本フェーズは挙動変更を伴う**（挙動不変フェーズではない）。変更する経路は特性テストで
  **新挙動として固定**し、変更しない経路は回帰しないことを担保する（暫定仕様 §8 安全網）。
- **対象レイヤ: 原則 presentation**（KeymapSetIo / StartupIo / ConfigPaths / App 起動時処理）。
  `prompt_if_missing` 撤去に伴い application（`config_service` の startup 正規化行）に軽微な変更が入る。
  **スキーマは後方互換を維持**（既存キー削除禁止・未知キー保持契約は不変）。
- 起票元: ユーザー要望（2026-07-26〜27・保存系統の改善討議）。**idea 由来ではない**ため
  `backlog/INDEX.md` の更新対象なし。
- 主入力（暫定仕様）: [04_keymap_set_new_and_default_dir.md](../../history/04_keymap_set_new_and_default_dir.md)
  （**v0.3・ユーザー確定済**）
- モード: **暫定仕様先行モード**。番号対応: phase 05 / 暫定 04 / decisions 05。
- 保存系リデザインの **Phase α**。後続は Phase β（暫定 05）/ Phase γ（暫定 06）/ プリセット（暫定 07）。

## 確定（ユーザー 2026-07-26〜27）

暫定仕様 04 §2 が正。要点のみ再掲する（**設計の正は暫定仕様。本ファイルで再定義しない**）:

- **新規作成は「ファイルなし」**（`new_config` は `keymap_set_path` を空にする）。
- **保存は空パスなら別名保存へ分岐**（ボタン名は「保存」のまま）。
- **Import 成功時は `keymap_set_path` を無条件で空にする**。
- **既定保存先はディレクトリ `config/user/keymap_sets/`**。`default.json` への自動保存・
  自動フォールバックを廃止。別名保存の初期ファイル名は **`keymap_set.json`**（一般名）。
- **起動時にディレクトリ骨格を一括作成**（config.json 本体の作成は従来どおり初回保存時）。
- **`prompt_if_missing` は新規出力を止める。既存 config.json の値は残置を許容**（能動削除しない）。
- **見つからないときは現状維持**（無言で空起動・選択ダイアログは作らない）。

## スコープ

### 含む

- 新規作成 = 空パス / 保存の空パス → 別名保存分岐（暫定仕様 §3・§4）
- 既定保存先のディレクトリ化・Import 後の無条件クリア・空起動時の path 空化・
  起動時ディレクトリ骨格作成（§5）
- `prompt_if_missing` の撤去（§6）と既存 startup 系テストの期待値更新
- 変更経路の特性テスト追加（§8 安全網）
- 正本反映（`data_schema.md` / `codebase_map.md`）・暫定仕様 04 の凍結・記録類の更新

### 含まない（後送り）

- **複数の独立した keymap_set の完全対応**（子ファイルの共有・上書きは残る。暫定仕様 §9 制約）
- 子ファイル保存の確認ダイアログ・参照元記録 → Phase β（暫定 05）
- `config_service.save_runtime_data` の子ファイル書き出しロジック本体 → Phase β
- trigger_set の source_path 不整合 → [idea_05](../../backlog/idea_05_trigger_set_source_path_inconsistency.md)（Phase β）
- 停止/トグルキーの config.json 既定化 → Phase γ（暫定 06）/ プリセットのグローバル化 → 暫定 07
- 起動時のファイル選択 UX の新設（無言空起動を維持）

## このフェーズで読むファイル

1. `instructions/history/04_keymap_set_new_and_default_dir.md`（**主入力・設計の正**）
2. `keyseq/presentation/controllers/config_io/keymap_set_io.py`（new_config / save_keymap_set /
   save_as / import_config / set_startup_keymap_set）
3. `keyseq/presentation/controllers/config_io/startup_io.py`（空起動時の path / write_startup base）
4. `keyseq/presentation/config_paths.py`（`preferred_keymap_set_path` / `normalize_keymap_set_save_path` /
   suggest 系）
5. `keyseq/presentation/app.py`（起動時ディレクトリ作成の挿入位置）
6. `keyseq/presentation/startup_settings.py`（`prompt_if_missing` 型ガード）
7. `keyseq/application/config_service.py`（**該当箇所のみ**: startup 正規化 / `_ensure_split_config_dirs`。
   分割保存ロジック本体は読まない = 本フェーズ非対象）
8. `tests_ui/test_startup_font_characterization.py`（期待値更新 + monkeypatch 手法の先例）
9. `instructions/common/spec_detail/data_schema.md` / `instructions/common/codebase_map.md`（最終タスクのみ）

## タスク

| # | タスク | 概要 |
|---|---|---|
| task_01 | `startup_dir_skeleton` | 起動時に `config/user/{keymap_sets,keymaps,trigger_sets,hotkey_presets,sequences}` を一括作成（既存 `_ensure_split_config_dirs` 相当を再利用）。**config.json は起動時に書かない**。受入 2 |
| task_02 | `new_config_empty_path` | `new_config` の path 空化 + `save_keymap_set` の空パス → `save_as` 分岐 + 別名保存の初期ファイル名 `keymap_set.json`。受入 1 |
| task_03 | `import_and_empty_start_path` | Import 成功時の無条件クリア + 空起動時 path の空化 + `default.json` が保存ターゲット用途に残っていないかの grep 確認と整理。受入 3・4 |
| task_04 | `remove_prompt_if_missing` | 4 箇所（`config_service` / `startup_settings` / `startup_io` / `keymap_set_io`）の撤去 + startup 系テストの期待値更新。**既存値の能動削除はしない**。受入 5・6 |
| task_05 | `integration_recheck` | 受入条件 §8 の通し確認・`tests` / `tests_ui` / smoke 全 pass・非変更経路の回帰確認（既存パスへの保存 / 読込 / 別名保存 / Import / Export）。受入 7・8 |
| task_06 | `finalize_records` | 正本反映（`data_schema.md` / `codebase_map.md`）・暫定仕様 04 の凍結・`decisions_archive/05` 作成・`current.md` 更新・`/refactor_check` |

- 順序の根拠: task_01 は他と独立かつ受入 2（初回 Save As の初期ディレクトリ）の前提。
  task_02 → task_03 は `keymap_set_path` を空にする経路を「新規」→「Import / 空起動」の順で広げる。
  task_04 は死にフラグ撤去で他タスクと独立のため、path 系の変更と混ぜず最後に置く。
- **各実装タスクは対応する特性テスト（新挙動の固定）まで含める**。変更しない経路の回帰確認は task_05。
- タスク定義ファイルは着手するタスクから順に `/task_new` で起票する（全部を先に作らない）。

## レビュー方針

共通観点は `.claude/rules/review.md`。本フェーズ固有の観点:

1. **挙動変更の範囲が暫定仕様どおりか**（最重要）。空パス化するのは
   「新規作成 / Import 成功 / 空起動」の 3 経路のみ。既存パスを開いている状態の保存を
   別名保存に変えていないか。
2. **`default.json` への自動フォールバックが保存ターゲットとして残っていないか**。
   逆に `preferred_keymap_set_path()` を suggest 系の補助用途まで一括削除していないか
   （§5 は「保存先の既定値としては使わない」であり関数の全廃ではない）。
3. **スキーマ後方互換**。`prompt_if_missing` 以外のキーに触れていないか。既存 config.json の
   当該キーを `pop` していないか（残置許容が確定事項）。
4. **スコープ外への波及がないか**。`config_service.save_runtime_data` の子ファイル書き出し・
   trigger_set の source_path・起動時のファイル選択 UX に手が入っていないか。
5. **特性テストが新挙動を固定しているか**（旧挙動のまま pass する書き方になっていないか）。

- タスク単位の必須レビューは `reviewer`。**task_05（統合）とフェーズ完了判定前は
  Codex レビュー + `deep-reviewer` を併用する**（`.claude/rules/agent_selection.md`）。
- 実機目視はユーザー。最低限「新規作成 → 保存（別名保存が出ること）/ 既存セットの上書き保存 /
  別名保存の初期ディレクトリとファイル名 / Import 後の保存 / 起動時に stored セットが無い場合 /
  既存 config.json（`prompt_if_missing` 付き）での起動」を確認してもらう。
