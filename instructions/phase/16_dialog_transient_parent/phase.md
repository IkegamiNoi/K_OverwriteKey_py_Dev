# phase.md

## フェーズ名

ネストしたダイアログの前面維持（dialog_transient_parent）

## フェーズの目的

ネストして開いたダイアログが、**呼び出し元より前面に留まる**ようにする。
現状はアクション編集からプリセット編集を開いた状態で**アクション編集を掴んで動かすと前面に出てしまう**
（ユーザーが実機で確認・2026-09-13）。原因は、ネストしたダイアログが
**「App より前」としか指定されていない**こと。

**対象レイヤは presentation のみ。スキーマ変更なし。**
**正本は `features.md` §4.6 のみ改訂**（起票時は「改訂なし」の見込み。完了判定前レビュー由来・2026-09-15）。
**変えるのは「前面維持の指定」だけで、「所有関係」と「App 参照」は動かさない**
（3 つの役割の切り分けは暫定仕様 14 §1）。

- 起票元: [idea_17](../../backlog/idea_17_action_dialog_preset_manager_parent.md)
  （phase 14 の受け入れ条件 15・暫定仕様 12 §6-5 で「フェーズ外・独立 idea」と確定した分離項目）。
- 主入力（暫定仕様）: [14_dialog_parent_and_app_separation.md](../../history/14_dialog_parent_and_app_separation.md)
  （**v0.4・ユーザー確定済・実装着手可**）。
- モード: **暫定仕様先行モード**。番号対応: phase 16 / 暫定 14 / decisions 16。

## 確定（ユーザー 2026-09-13）

暫定仕様 14 §2 が正。要点のみ:

- **役割 2（前面維持の指定 = `transient`）だけを直す**。**役割 1（所有関係 = `master`）は
  App のまま動かさない** — 動かすと**破棄が連鎖**し、正本 `features.md` の
  「開いた順と違う順で閉じたら内側を優先する」条項と衝突する（実測確認済）。
- **役割 3（App 参照 = `self.parent`）も動かさない**。**引数分離と属性名の改名は不要**
  （v0.1 の案 A は撤回）。
- **対象は食い違い 2 件とも** — ①アクション編集 → プリセット編集
  ②プリセット編集 → 上書き確認。**②は実機未確認だがコード上は同型**のため同時に直す。
- **他 7 ダイアログへ予防的に広げない**。
- **非 LIFO で閉じたときに前面維持の指定が消える点は受容する**（UI から到達しない経路）。

## スコープ

### 含む

- `keyseq/presentation/dialogs/preset_manager.py` — `transient_parent` 引数の追加と
  `grab_modal` の第 2 引数への反映。
- `keyseq/presentation/dialogs/action_dialog.py` — 呼び出しの追随。
- `keyseq/presentation/controllers/config_io/hotkey_presets_io.py` —
  `confirm_overwrite` へキーワード必須の `transient_parent` を追加。
- **既存テスト 4 件の引数契約の追随**（`tests_ui/test_app_ui_flows.py:1201`・`:1261`・`:1313` /
  `tests_ui/test_nested_modal_grab.py:185`）。
- 受け入れ条件のテスト（前面維持の相手 / 所有関係の非変更 / 既定の非変更 / phase 14・15 の非退行）。

### 含まない（後送り）

- **役割 1（所有関係）の付け替え**と、それに伴う正本 `features.md` の改訂。
- **正本への作法の明文化と静的検査**（ユーザー確定）。
- **App 参照の引数分離・属性名の改名**（暫定仕様 v0.1 から撤回）。
- **`presentation/modal.py` の変更**（phase 14 の資産。渡し先が変わるだけ）。
- **他 7 ダイアログへの予防的な引数追加** / **`PresetDialog`**（既に正しい）。
- **ダイアログ同型スケルトンの共通化** / **静的検査の発見ベース化**（`current.md` の候補送り）。
- **application / domain / infrastructure の変更**（`save_hotkey_presets` を含む）。

## このフェーズで読むファイル

1. `instructions/history/14_dialog_parent_and_app_separation.md`（主入力・v0.4）
2. `keyseq/presentation/dialogs/preset_manager.py`（`:65-80` の `__init__` と `:72` の `grab_modal` /
   `:362-368` の `on_ok` のコールバック）
3. `keyseq/presentation/dialogs/action_dialog.py:339`
4. `keyseq/presentation/controllers/config_io/hotkey_presets_io.py`（`:44-47` と `:82`）
5. `keyseq/presentation/modal.py`（`grab_modal` の第 2 引数の意味。**変更しない**）
6. `tests_ui/test_nested_modal_grab.py`（`:185` の追随対象 / `:262-276` の静的検査 /
   `:311`〔現 `:335`〕の非 LIFO テスト）
7. `tests_ui/test_app_ui_flows.py:1201`・`:1261`・`:1313`（追随対象）

**読まない**: `keyseq/application/` / `keyseq/domain/` / `keyseq/infrastructure/`。
`instructions/history/` の凍結済み暫定仕様（04〜13）。

## タスク

1. **task_01**: `PresetManagerDialog` へ `transient_parent` を足し、`action_dialog.py:339` を追随。
   **既定は `parent`**（`app.py:418` は無変更）。**`grab_modal` を `__init__` の最後の文のまま保つ**。
2. **task_02**: `confirm_overwrite` へキーワード必須の `transient_parent` を足し、
   `preset_manager.py:364` を追随。**既存テスト 4 件の引数契約の追随を含む**。
3. **task_03**: 受け入れ条件のテストを追加（前面維持の相手 / **所有関係が App のまま** /
   既定の非変更 / phase 14・15 の非退行）+ **変異検査 2 件**。
4. **task_04**: 統合確認（`tests` / `tests_ui` 全体 + `smoke_app`）+ **二次レビュー**
   （`deep-reviewer` + `codex-reviewer`）+ **ユーザーによる実機目視**
   （①アクション編集を掴んで動かしてもプリセット編集が前面に残る ②上書き確認が前面に残る）。
5. **task_05（最終・正本反映）**: 起票時は**正本 `spec_detail/` の改訂は無い見込み**だったが、
   **完了判定前レビューを受け `features.md` §4.6 へ前面維持の 2 条項を追加**（ユーザー採用 2026-09-15）。
   `codebase_map.md` の更新（引数が 1 つ増える分）+ **暫定仕様 14 の凍結** +
   `.claude_data/state/decisions_archive/16_dialog_transient_parent.md` 作成 +
   `instructions/phase/current.md` の完了記載 + `backlog/INDEX.md` の idea_17 行を
   `INDEX_done.md` へ移動 + **`/refactor_check` の実行と判定結果の完了報告への記載**。

タスク定義は着手する順に `tasks/task_NN_<topic>.md` へ起票する（`/task_new`）。

## レビュー方針

共通観点は `.claude/rules/review.md`。本フェーズ固有の観点:

- **役割の混同** — `tk.Toplevel` の引数（役割 1）や `self.parent`（役割 3）を触っていないか。
  変えてよいのは **`grab_modal` の第 2 引数（役割 2）だけ**。
- **既定の扱い** — `PresetManagerDialog` は既定あり（`parent`）、`confirm_overwrite` は
  キーワード必須。**この非対称は意図どおりか**（後者は呼び出し元が 1 箇所しかないため）。
- **phase 14 との干渉** — `grab_modal` が `__init__` の最後の文のままか。
  **`master` のアサーションを弱めていないか**。
- **既存テストの扱い** — 変更は**引数契約の追随 4 件だけ**か。
  **grab・生存・復元先・`master` のアサーションを弱めていないか**（弱めるのは禁止）。
- **スコープ逸脱** — 他 7 ダイアログへの引数追加・`modal.py` の変更・
  App 参照の引数分離を取り込んでいないか。

エージェントの使い分けは `.claude/rules/agent_selection.md`:

- 各タスクの必須レビュー = `reviewer`
- task_04 の統合確認時 = `deep-reviewer` + `codex-reviewer`
- フェーズ完了判定前 = `deep-reviewer` + `codex-adversarial-reviewer`（**focus text を渡せる方**）
- テスト実行は `verifier`（Codex は python を実行できない）
