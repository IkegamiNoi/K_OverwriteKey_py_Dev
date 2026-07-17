# phase.md

## フェーズ名

hotkey 検証の層移設（hotkey_validation）

## フェーズの目的

App（presentation）に住む **hotkey 検証ロジックを domain / application 層へ移す**。
設計は主入力の暫定仕様が正であり、**本 phase.md は設計を再定義しない**（重複記載を避け、
判断は暫定仕様を参照する）。

- **対象レイヤ: domain / application / presentation の 3 層**（+ tests / tests_ui）
- **スキーマ変更: なし** / **挙動不変**（エラーメッセージ 4 種・戻り値契約・チェック順序を 1 文字も変えない）
- 狙い: ① application（`ActionExecutor`）が presentation（`App.validate_hotkey`）を注入経由で使う
  **層の逆転の解消** ② **テスト容易性**（現状は `tk.Tk` 生成が必要でテストが 0 件）

- 起票元: [idea_01](../../backlog/idea_01_hotkey_validation_to_domain.md)（計画04 W7 の残留ロジック分類から分離）
- 主入力（暫定仕様）: **[01_hotkey_validation.md](../../history/01_hotkey_validation.md)（v1.0・ユーザー確定済・実装着手可）**
- モード: **暫定仕様先行モード**。番号対応: **phase 02 / 暫定 01 / decisions `decisions_archive/02_hotkey_validation.md`**
  （暫定仕様は phase とは独立採番のため番号が一致しない）

## 確定（ユーザー 2026-07-17）

詳細と根拠は暫定仕様 [§2 確定事項](../../history/01_hotkey_validation.md) が正。要点のみ:

- **設計案 C**: domain = 純粋な文法検査 / application = 合成 + キー名検証 / presentation = 薄い委譲。
- **parts の再構成は廃止**（domain が `(error, normalized, parts)` を返す。公開契約 `(error, normalized)` は不変）。
- **命名**: `domain/hotkey.py::validate_hotkey_syntax` / `application/hotkey_service.py::HotkeyService.validate`。
- **安全網の特性テストは追加し、移設後も残す**。
- 敵対的レビューの `MemoryError` 指摘は**却下**（根拠不成立。暫定仕様 §2 に判断を記録済み）。

## スコープ

### 含む

1. 安全網 — 現行 `App.validate_hotkey` の特性テストを `tests_ui` へ**新規追加**（移設前・実装変更なし）
2. `keyseq/domain/hotkey.py`（新規）+ `tests/test_hotkey.py`（新規）
3. `keyseq/application/hotkey_service.py`（新規）+ `tests/test_hotkey_service.py`（新規）
4. `keyseq/presentation/app.py` — `validate_hotkey` の薄い委譲化 + `ActionExecutor` への注入元差し替え
5. 正本反映・記録（暫定仕様の昇格 / 凍結・`codebase_map.md`・decisions_archive・`/refactor_check`）

### 含まない（後送り）

暫定仕様 [§7 スコープ外](../../history/01_hotkey_validation.md) が正。要点:

- [idea_02](../../backlog/idea_02_startup_font_settings_cleanup.md)（起動設定 / フォント クラスタ）
- **単キー検証の統一** — `controllers/keymap_panel_controller.py:144, :376` / `key_capture.py:125` が
  `self._app.input_gateway.validate_key_name(...)` を直接呼ぶ箇所（hotkey ではなく単キー）。同種の層越えだが本フェーズでは触らない
- `application/action_executor.py` の変更（注入元が変わるのみ・シグネチャ不変）
- hotkey 文法・エラーメッセージの変更 / `validate_key_name` の例外→戻り値化
- `app.py` の行数削減それ自体
- tests_ui の**既存**アサーション変更（新規追加のみ可）

## このフェーズで読むファイル

実装時はこれ以外を広く読まないこと。**主入力の暫定仕様を最初に読む**。

1. **[instructions/history/01_hotkey_validation.md](../../history/01_hotkey_validation.md)（主入力・設計の正）**
2. `keyseq/presentation/app.py`（416-446 = 移設元 / 67-78 = 生成・注入箇所）
3. `keyseq/domain/config.py` / `keyseq/domain/key_identifiers.py`（既存 domain のスタイル確認。純粋関数・標準ライブラリのみ）
4. `keyseq/application/action_executor.py`（20, 29, 77-80 = 注入と呼び出しの契約。**変更しない**）
5. `keyseq/infrastructure/input_gateway.py`（54 = `validate_key_name` の振る舞い。例外を再 raise）
6. `keyseq/presentation/dialogs.py`（440, 475 = `parent.validate_hotkey` の契約。**変更しない**）
7. `tests/test_key_identifiers.py`（domain テストの既存例。unittest・モック無しで関数直呼び）
8. `tests_ui/test_app_ui_flows.py`（安全網テストの追加先）

## タスク

1. **task_01_characterization_test** — 安全網。現行 `App.validate_hotkey` の特性テスト（4 エラー + 正常系）を
   `tests_ui` へ新規追加。**実装は変更しない**。以降のタスクの回帰検出の土台になる（依存: なし）
2. **task_02_domain_hotkey** — `keyseq/domain/hotkey.py::validate_hotkey_syntax` 新規 + `tests/test_hotkey.py` 新規
   （暫定仕様 §4.1。標準ライブラリのみ・注入なし・`tk.Tk` 不要）（依存: task_01）
3. **task_03_application_hotkey_service** — `keyseq/application/hotkey_service.py::HotkeyService` 新規 +
   `tests/test_hotkey_service.py` 新規（暫定仕様 §4.2。`try` はループ全体を包む形を厳守）（依存: task_02）
4. **task_04_presentation_delegation** — `app.py` の `validate_hotkey` を薄い委譲へ + `HotkeyService` の生成 +
   `ActionExecutor` の注入元差し替え（暫定仕様 §4.3）。統合退行の確認まで（依存: task_03）
5. **task_05_finalize_records** — 正本反映・記録（最終）。暫定仕様の**正本昇格 + 凍結** /
   `codebase_map.md` 更新 / `decisions_archive/02_hotkey_validation.md` 作成 / `decisions.md` アーカイブ索引 /
   `current.md` 完了記載・次採番 / **`backlog/INDEX.md` の idea_01 を完了にして `INDEX_done.md` へ移動** /
   `/refactor_check` の実行と判定記載（依存: task_04）

※ 各タスク定義は `/task_new` で着手順に起票する。

## レビュー方針

共通観点は `.claude/rules/review.md`（仕様適合性 / 依存方向 / 責務分離 / 不要変更 / チェック漏れ）。
受け入れ条件は暫定仕様 [§6](../../history/01_hotkey_validation.md) が正（11 項目）。本フェーズ固有の観点:

- **挙動不変が絶対要件**。エラーメッセージ 4 種（暫定仕様 §5）を**移設前後で 1 文字一致**させること。
  レビューでは現行 `app.py:416-446` と新実装を突合すること。
- **`try` の範囲**（task_03）: ループ全体を包み `except` がループ変数 `p` を参照する形（暫定仕様 §4.2 の実装形）。
  各要素の内側に `try` を置くと `p` の値がずれるため、**実装形からの逸脱を必ず指摘すること**。
- **parts の再構成禁止**（task_03）: `normalized.split("+")` をしていないこと（受け入れ条件 5）。
- **依存方向**（task_02）: `keyseq/domain/hotkey.py` が標準ライブラリのみに依存し、
  application / infrastructure を import しないこと（受け入れ条件 3）。
- **層の逆転の解消**（task_04）: `ActionExecutor` への注入が `self.hotkey_service.validate` になっていること
  （presentation のバウンドメソッドを注入していない）。`action_executor.py` を変更していないこと。
- **dialogs 契約の維持**（task_04）: `App.validate_hotkey` が残り、`dialogs.py:440, 475` が動くこと。
- 実装は `codex-implementer` へ委任（`.claude/rules/agent_selection.md`）。標準検証は `verifier`、
  コミットはメインセッション。**統合確認（task_04）では二次レビュー（`codex-reviewer`）を併用**する
  （CLAUDE.md「統合テスト時・フェーズ区切りでは二次レビューを併用する」）。
- **手動確認**（task_04 完了後）: アクション編集ダイアログで不正 hotkey（空 / `ctrl++c` / `ctrl+ctrl+c` /
  不明キー）のエラー表示、正常 hotkey の正規化保存、hotkey アクションの実行（暫定仕様 §6-11）。
