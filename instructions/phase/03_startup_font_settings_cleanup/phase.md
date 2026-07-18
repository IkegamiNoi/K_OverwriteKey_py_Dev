# phase.md

## フェーズ名

起動設定 / フォント設定クラスタの整理（startup_font_settings_cleanup）

## フェーズの目的

App（presentation）に残る**起動設定読込とフォントサイズ設定の 3 メソッド**
（`_coerce_font_delta` / `_load_startup_settings` / `set_ui_font_delta`）を整理し、
責務混在・controller → App private 逆参照・初期化順序の制約・ui_vars の App private 依存を解消する。
設計は主入力の暫定仕様が正であり、**本 phase.md は設計を再定義しない**（判断は暫定仕様を参照）。

- **対象レイヤ: presentation 内での再編に限定**（application `ConfigService` / domain / infrastructure は不変）
- **スキーマ変更: なし** / **挙動不変**（フォント範囲 `-3〜+3`・既定 0・startup.json 後方互換・
  エラー通知の分岐/回数/文言・メニュー構成・`build_menu_bar` のみ再構築の副作用を変えない）

- 起票元: [idea_02](../../backlog/idea_02_startup_font_settings_cleanup.md)（計画04 W7 の残留ロジック分類から分離）
- 主入力（暫定仕様）: **[02_startup_font_settings_cleanup.md](../../history/02_startup_font_settings_cleanup.md)（v1.0・ユーザー確定済・実装着手可）**
- モード: **暫定仕様先行モード**。番号対応: **phase 03 / 暫定 02 / decisions `decisions_archive/03_startup_font_settings_cleanup.md`**

## 確定（ユーザー 2026-07-18）

詳細と根拠は暫定仕様 [§2 確定事項](../../history/02_startup_font_settings_cleanup.md) が正。要点のみ:

- **coerce_font_delta → `theme.py` の純関数**（逆参照を解消）。
- **起動設定ローダ → 新規 `presentation/startup_settings.py`**（`config_service` 直依存で初期化順序を壊さない）。
- **フォント設定の責務分離は案 A（最小抽出）で確定**。`_ui_font_delta_pt` は App 保持。
  **案 B（FontSettingsController 新設）は今フェーズ見送り**（初期化順序未解決・将来 idea 化）。
- **エラー通知は `on_read_error(exc)` のコールバック注入**（真理値表どおり分岐/回数/文言は不変）。
- **未知キー全保持の契約**（`keymap_set_path` 等を保持し既知2キーのみ正規化。後方互換の要）。

## スコープ

### 含む

1. 安全網 — 現行 3 メソッドの特性テスト（coerce / startup ローダの真理値表 / 未知キー保持 / フォント変更フロー）を
   移設前に**新規追加**（実装変更なし）
2. `theme.py` に `coerce_font_delta` 追加 + 呼び出し元 4 箇所の差し替え + `App._coerce_font_delta` 削除
   （`config_io_controller.py:278` の逆参照解消を含む）
3. `presentation/startup_settings.py`（新規）+ `App._load_startup_settings` 削除・`app.py:57` 差し替え
   （未知キー全保持・真理値表どおりの `on_read_error` 注入）
4. `set_ui_font_delta` の案 A 分割（`_apply_font_delta` 抽出）+ `UiVars` の引数化（`ui_vars` の App private 直読み解消）
5. 正本反映・記録（暫定仕様の昇格 / 凍結・`codebase_map.md`・decisions_archive・`/refactor_check`）

### 含まない（後送り）

暫定仕様 [§10 スコープ外](../../history/02_startup_font_settings_cleanup.md) が正。要点:

- **案 B（FontSettingsController 新設）** — 初期化順序の設計が未確定のため今フェーズ見送り（将来 idea 化）。
- フォント範囲/既定値の変更 / startup.json スキーマ変更 / メニュー構成・文言の変更。
- application（`ConfigService`）/ domain / infrastructure の変更。
- [idea_03](../../backlog/idea_03_action_hotkey_save_normalization.md)（アクション hotkey の保存時正規化）。
- `app.py` の行数削減それ自体 / tests・tests_ui の既存アサーション変更（新規追加のみ可）。

## このフェーズで読むファイル

実装時はこれ以外を広く読まないこと。**主入力の暫定仕様を最初に読む**。

1. **[instructions/history/02_startup_font_settings_cleanup.md](../../history/02_startup_font_settings_cleanup.md)（主入力・設計の正）**
2. `keyseq/presentation/app.py`（357-366 / 376-392 / 227-243 = 移設元 3 メソッド。43-61 = 初期化順序・生成箇所）
3. `keyseq/presentation/theme.py`（既存フォントロジック。`coerce_font_delta` の追加先・`apply_global_theme`）
4. `keyseq/presentation/startup_settings.py`（新規作成先）
5. `keyseq/presentation/ui_vars.py`（17 = `master._ui_font_delta_pt` 直読み。コンストラクタ引数化の対象）
6. `keyseq/presentation/controllers/config_io_controller.py`（245-246 = keymap_set_path 依存 / 266-285 = `write_startup`・逆参照 278）
7. `keyseq/application/config_service.py`（76-79 = `load_startup`。**変更しない**・依存先として確認）
8. `keyseq/presentation/views/menu_bar.py`（37-46 = フォントメニュー / 44 = `set_ui_font_delta` 呼び出し / `build_menu_bar`・`bind_menu_shortcuts` の副作用差）
9. `tests/test_key_identifiers.py`（domain/純関数テストの既存例・unittest）/ 既存 `tests_ui/`（安全網の追加先）

## タスク

1. **task_01_characterization_test** — 安全網。現行 3 メソッドの特性テストを新規追加
   （`coerce` 純関数 / startup ローダの真理値表〔欠損・例外・非dict・正常〕+ `on_read_error` 呼出/文言 /
   **未知キー保持** / フォント変更フロー〔差分なし早期 return・`build_menu_bar` のみ〕）。**実装は変更しない**（依存: なし）
2. **task_02_theme_coerce_font_delta** — `theme.py::coerce_font_delta` 新規 + 呼び出し元 4 箇所差し替え +
   `App._coerce_font_delta` 削除（`config_io_controller.py:278` の逆参照解消を含む）+ tests（暫定仕様 §4）（依存: task_01）
3. **task_03_startup_settings_loader** — `presentation/startup_settings.py::load_startup_settings` 新規
   （`config_service` 直依存・**未知キー全保持**・真理値表どおりの `on_read_error` 注入）+ `App._load_startup_settings` 削除・
   `app.py:57` 差し替え + tests（暫定仕様 §5）（依存: task_02）
4. **task_04_font_apply_and_uivars** — `set_ui_font_delta` の案 A 分割（`_apply_font_delta` 抽出）+
   `UiVars` の引数化（`ui_vars` の `master._ui_font_delta_pt` 直読み解消）+ 統合退行（暫定仕様 §6）（依存: task_03）
5. **task_05_finalize_records** — 正本反映・記録（最終）。暫定仕様の**正本昇格判断 + 凍結** /
   `codebase_map.md` 更新 / `decisions_archive/03_startup_font_settings_cleanup.md` 作成 / `decisions.md` 索引 /
   `current.md` 完了記載・次採番 / **`backlog/INDEX.md` の idea_02 を完了にして `INDEX_done.md` へ移動** /
   `/refactor_check` の実行と判定記載（依存: task_04）

※ 各タスク定義は `/task_new` で着手順に起票する。

## レビュー方針

共通観点は `.claude/rules/review.md`（仕様適合性 / 依存方向 / 責務分離 / 不要変更 / チェック漏れ）。
受け入れ条件は暫定仕様 [§8](../../history/02_startup_font_settings_cleanup.md) が正（12 項目）。本フェーズ固有の観点:

- **挙動不変が絶対要件**。エラー通知の**真理値表**（暫定仕様 §5: 欠損=無警告 / 例外=警告1回 / 非dict=無警告）を
  移設前後で保つこと。title「startup.json 読込失敗」・body を 1 文字一致させる。
- **未知キー全保持**（task_03・受け入れ条件 §8-12）: 読込 dict の `keymap_set_path` 等が保持され、
  フォント変更保存後も startup.json に残ること。fixture テストで裏取り（最優先の後方互換観点）。
- **依存方向**（task_02・task_03）: presentation → application（`config_service`）は可。`theme.py` / `startup_settings.py` が
  application/infrastructure を無秩序に参照しないこと。`config_io_controller.py` が App private を呼ばないこと（逆参照解消）。
- **初期化順序**（task_03）: 起動設定ローダが `config_io`（`:127` 生成）に依存せず `config_service`（`:43`）のみに依存し、
  `app.py:57` の実行位置を保つこと。
- **メニュー再構築の副作用**（task_04）: フォント変更で `build_menu_bar` のみ呼ばれ `bind_menu_shortcuts` を呼ばないこと。
- **案 B を実装しないこと**（task_04）: FontSettingsController を新設しない（暫定仕様 §6・スコープ外）。
- 実装は `codex-implementer` へ委任（`.claude/rules/agent_selection.md`）。標準検証は `verifier`、コミットはメイン。
  **統合確認（task_04）では二次レビュー（`codex-reviewer`）を併用**する。
- **手動確認**（task_04 完了後）: 起動（startup.json 正常/欠損/破損/非dict）のフォント適用と警告挙動、
  メニューからのフォント変更の即時反映・永続化・再起動後の保持、`keymap_set_path` を持つ構成の起動復元（暫定仕様 §8-11,12）。
