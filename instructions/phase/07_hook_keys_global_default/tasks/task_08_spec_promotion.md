# task_08_spec_promotion

## 目的

phase 07（Phase γ）の実装・統合確認（実機目視 G1〜G9 を含む）が完了したので、
[暫定仕様 06](../../../history/06_hook_keys_global_default.md) §9 の予定に従い、確定した設計を
**正本 `instructions/common/spec_detail/` および `codebase_map.md` へ昇格**し、暫定仕様 06 を凍結する。
併せて `.claude/rules/task_execution.md`「フェーズ完了時」のチェックリストを消化する。

- **文書のみのタスク**（`.claude/rules/agent_selection.md`「メインセッションが直接行ってよい作業」）。
  **`keyseq/` / `tests/` / `tests_ui/` を変更しない**（実装は task_01〜07b で確定済み）。
- 昇格は**実装済みの挙動をそのまま記述**する。ここで新しい仕様を作らない
  （書きながら仕様の穴を見つけた場合は `.claude/rules/spec_change_workflow.md` に従い報告のみ）。

## 対象範囲（文書限定・コード不変）

### 1. `instructions/common/spec_detail/data_schema.md`

**§5.9「hook キーの全体デフォルトと個別指定」を新設**（既存 §5.1〜§5.8 の節番号・見出しは変更しない）。
記述する内容:

- **config.json（全体デフォルト）**: `hook_stop_key` / `hook_toggle_key`（正規化して保持・空可・初期値は空）。
  書き込み経路は起動設定の書き出しに集約する（`_startup_settings` と config.json を乖離させない）。
- **keymap_set（個別）**: `hook_keys_individual`（bool・既定 false）+ 既存キー `hook_stop_key` /
  `hook_toggle_key`。**3 キーとも常に出力**（既存キー削除禁止・§5.1）。
- **解決順序**: keymap_set を runtime へ載せる時点で確定する。`hook_keys_individual` が真なら個別値、
  偽/未設定なら config.json の全体デフォルトを runtime へ注入する。フック層は解決済み値のみを見る。
- **移行規則**: フラグが**存在すれば**その値。**存在しなければ**正規化後に stop/toggle の
  少なくとも一方が非空 → ON、両方空 → OFF。既存キーは残す。冪等（ON かつ両キー空を OFF へ落とさない）。
- **OFF 時の保存契約**: 個別値を `""` にクリア + `hook_keys_individual: false` で保存。
  保存後は個別値が復活しない（復活はセッション内・保存前に限る）。
- **OFF 時のキー編集**: keymap_set ではなく config.json の全体デフォルトを更新し、
  **成否付きで永続化**する。成功時のみ runtime / UI を確定する。keymap_set は dirty にしない。
- **契約として明記する 2 点**（task_07 の指摘 E・実装変更はしない）:
  - ① **キーの衝突検証はカレント keymap_set 内に閉じる**。全体デフォルトは他の keymap_set の
    トリガーとは照合されないため、別セットでトリガーと重なると停止/トグルが優先される
    （優先順位の記述は `key_input.md` §7.6 側）。
  - ② **「明示 `false` + 非空個別値」の keymap_set**（本実装は生成しない。手編集・別実装由来のみ）は、
    読込時に全体デフォルトで上書きされ、保存時に空文字化されるため**個別値が失われる**。

### 2. `instructions/common/spec_detail/key_input.md`

**§7.6「停止/トグルキーの供給源」を新設**（既存 §7.1〜§7.5 は変更しない）。記述する内容:

- 停止キー / トグルキーは**全体デフォルト（config.json）と keymap_set 個別指定**の 2 系統を持ち、
  実行時に参照されるのは**解決済みの 1 値**である（データ側の規定は `data_schema.md` §5.9）。
- 個別指定 OFF の状態でのキー取得 / クリアは**全体デフォルトを編集**する（keymap_set を変更しない）。
- 衝突検証の範囲は**カレント keymap_set 内**であり、停止/トグルはトリガーより優先される（指摘 E ①）。
- compact 表示のチェックは**状態表示のみ**（操作は full のみ）。

### 3. `instructions/common/codebase_map.md`

実装済みの責務を反映する（新規節は作らず既存節へ追記する）:

- **ConfigService**: `apply_global_hook_key_defaults`（OFF のみ注入・冪等・フラグ既定を補う）と
  `split_loading.load_global_hook_keys`（config.json の全体デフォルト読み出し）＝**キー解決点はこの 2 本のみ**。
  `split_payloads.build_keymap_set_payload` が OFF 保存時の空文字化を持つ。
- **StartupIo**: `write_startup` は `-> bool`、`write_global_hook_keys(*, stop_key, toggle_key) -> bool`。
  **全体デフォルトの書き込みはこの 1 本のみ**（config.json を別経路で read-modify-write しない）。
- **KeymapSetIo**: 注入 API を呼ぶ 4 経路（`new_config` / `restore_default` / 起動時の空データ
  フォールバック / Import）と、退避値の破棄点（保存実行の直前 / `apply_loaded_data_to_ui` /
  `new_config` / `restore_default`）。
- **SingleKeyCaptureController**: hook キー書き込みは `_apply_key` の 1 本。ON = `app.data` + dirty /
  OFF = config.json 更新（成功時のみ確定）+ dirty スナップショットの記録・復元。
- **App / UiVars**: `hook_keys_individual_var`（full / compact 共有・compact は `state="disabled"`）、
  `App.toggle_hook_keys_individual`（Var → data + 退避/復元）、`_retained_hook_keys`（セッション内退避・
  `app.data` に持たない）、`_sync_control_vars_from_data`（data → Var）。
- **domain/config.py**: `resolve_hook_keys_individual`（移行判定の純関数）。

### 4. 暫定仕様 06 の凍結

`instructions/history/06_hook_keys_global_default.md` の冒頭状態表記を
**「凍結（v0.2・正本へ昇格済み）」**へ更新し、昇格先（`data_schema.md` §5.9 / `key_input.md` §7.6 /
`codebase_map.md`）を明記する。**本文の仕様記述は書き換えない**（経緯として保存する）。

### 5. 判断履歴の集約

- `.claude_data/state/decisions_archive/07_hook_keys_global_default.md` を作成し、
  `decisions.md` の「phase 07」節（task_01〜07b + 起票時判断）を移す。
- `decisions.md` 側は該当節を削除し、**「アーカイブ索引」へ 1 行追加**する（既存フェーズと同形式）。

### 6. `instructions/phase/current.md` の更新

- 「現在の参照先」から phase 07 の要約を**削除**し、フェーズ完了を反映する
  （完了フェーズの要約はこのファイルに残さない）。次フェーズ = **phase 08（プリセット）**は
  **未起票のため着手はユーザー確認**とし、参照先の確定はユーザー判断に委ねる。
- 「次採番」を更新（次フェーズ = `08_<topic>` / 暫定仕様 = `08_<topic>`）。
- 直前の完了フェーズを `07_hook_keys_global_default` へ差し替える。
- `/refactor_check` の候補送りが出た場合は「別タスク化候補」へ追記する。

### 7. `phase.md` の進捗更新

タスク表の task_08 行に定義ファイルへのリンクを張り、進捗記述を「全タスク完了」に更新する。

### 8. `/refactor_check` の実行

`PHASE_BASE = caf41a7`。手順 1〜2（変更ファイル一覧と M1〜M6 の測定）は **`verifier` へ委任**し、
判定と提案書起票（必要な場合のみ）はメインが行う。判定結果を完了報告に記載する。

## 含まない

- **コード変更**（`keyseq/` / `tests/` / `tests_ui/`）。指摘 E は**契約の明記のみ**で実装は変えない。
- **プリセットの config.json グローバル化**（phase 08・[暫定 07](../../../history/07_hotkey_presets_global.md)）と
  [idea_08](../../../backlog/idea_08_per_keymap_set_preset_ownership.md)。
- task_07 で**除外**と判断した 2 件（`resolve_hook_keys_individual` の非 bool 値の扱い /
  `write_startup` の失敗ダイアログ文言 `"startup.json 保存失敗"`）。後者は必要なら別途 idea 化する。
- `instructions/backlog/INDEX.md` の完了移動（**本フェーズは起票元 idea を持たない**＝ユーザー要望起票のため該当なし）。
- リファクタの**実施**（`/refactor_check` は判定と提案書起票まで）。

## 確認

python は**リポジトリルートの `.venv`**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。

1. `git status` / `git diff --stat` で、**変更が `instructions/` と `.claude_data/` 配下のみ**であること
   （`keyseq/` / `tests/` / `tests_ui/` に差分が無い）。
2. 昇格した記述が実装と一致すること（キー名 `hook_keys_individual` / API 名
   `apply_global_hook_key_defaults` ・ `load_global_hook_keys` ・ `write_global_hook_keys` ・
   `resolve_hook_keys_individual` を実ファイルで突合する）。
3. `data_schema.md` の既存 §5.1〜§5.8 と `key_input.md` の §7.1〜§7.5 が**無改変**であること
   （追記のみ・節番号を動かしていない）。
4. 追加・更新した相対リンクが実在すること（`decisions_archive/07_*.md` / task_08 定義 / 暫定仕様 06）。
5. `/refactor_check` を実行し、判定（不要 / 推奨 + 提案書パス）を得ていること。
6. 文書のみの変更のため回帰テストは再実行しない（task_07b 実測の
   compile clean / tests 169 / tests_ui 178 / smoke pass が最終値）。**確認 1 で担保する**。

## 完了条件

- 「確認」1〜6 がすべて満たされている。
- **`deep-reviewer` 採用**（フェーズ完了判定・設計文書レビュー）+ **Codex レビュー系**
  （`codex-adversarial-reviewer`）の併用。Codex が使えない場合は報告のうえ Claude 側のみへ縮退してよい。
  指摘の採否はユーザー判断。
- 実機目視は **task_07 で実施済み（G1〜G9 すべて OK・2026-08-05 ユーザー報告）**。本タスクでは行わない。
- 本タスク完了をもって **phase 07 を完了**とする。
