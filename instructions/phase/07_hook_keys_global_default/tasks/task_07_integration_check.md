# task_07_integration_check

## 目的

phase 07（Phase γ）の実装タスク（task_01〜06b）が完了したので、
[暫定仕様 06](../../../history/06_hook_keys_global_default.md) §7 の**受入条件 1〜8 を通しで確認**する。
自動テストでの網羅確認・全スイートの実測・**実機目視**・フェーズ完了判定レビューを行う。

- **本タスクは検証タスク**。原則コードを変更しない（**不足が見つかった場合のみ**、
  テスト追加または最小修正を行い、その旨を完了報告に明記する）。
- レビューは `.claude/rules/agent_selection.md` に従い **`deep-reviewer` + Codex レビュー系**を併用する
  （統合確認・フェーズ完了判定のタイミング）。

## 対象範囲（検証・非実装）

### 1. 受入条件と特性テストの対応確認

暫定仕様 06 §7 の各条件について、**それを固定しているテストが実在するか**を確認し、
対応表を完了報告に含める。空欄（テスト不在）があればテストを追加する。

| # | 受入条件 | 想定される固定先 |
|---|---|---|
| 1 | config.json の全体デフォルトが keymap_set 読込時に解決されフック動作へ反映される | `tests/test_config_service.py`（task_02 の読込テスト群）|
| 2 | 新規作成した keymap_set は OFF で、hook キーの再設定が不要 | `tests_ui/test_config_io_characterization_keymap_set_startup.py`（`new_config` / `restore_default` / 空データフォールバックの注入）|
| 3 | チェック ON で個別指定でき、保存時に個別値が保存される | `tests/test_save_plan.py`（ON の payload）+ `tests_ui/test_app_ui_flows.py`（チェック UI）|
| 4 | OFF 時のキー編集が config.json を**成否付きで即永続化**し、keymap_set を dirty にしない | `tests_ui/test_app_ui_flows.py`（task_06 の OFF capture / clear）+ `tests_ui/test_config_io_characterization_keymap_set_startup.py`（`write_global_hook_keys`）|
| 5 | ON→OFF で表示が全体デフォルトへ / 再 ON で復活 / OFF 保存で空文字化 + フラグ false | `tests_ui/test_app_ui_flows.py`（task_06b）+ `tests/test_save_plan.py`・`tests/test_config_service.py`（task_03）|
| 6 | 既存 keymap_set の移行（正規化後どちらか非空 → ON / 両方空 → OFF / 既存キーは残る） | `tests/test_domain_config.py` + `tests/test_config_service.py` + `tests_ui/...keymap_set_startup.py`（移行経路のチェック復元）|
| 7 | 全体デフォルトの保存失敗時に UI / ランタイムを確定させない | `tests_ui/test_startup_font_characterization.py`（`write_startup` の成否）+ `tests_ui/test_app_ui_flows.py`（capture の失敗・例外）|
| 8 | `tests` / `tests_ui` / smoke が更新後の期待値で pass | 下記「確認」の実測 |

### 2. 設計不変条件の再確認（フェーズ横断）

実装が phase.md「レビュー方針」を維持しているかを、**差分全体**（`caf41a7..HEAD`）に対して確認する:

1. **後方互換**: keymap_set / config.json から既存キーを削除していない
2. **キー解決点が 1 箇所**: 解決は `split_loading.load_global_hook_keys` +
   `ConfigService.apply_global_hook_key_defaults` の 2 本のみ。
   **フック層（`input_router` / `hook_controller` / `keyboard_window` / `app.py` のフック供給部）が
   無変更**であること（`git diff` で確認する）
3. **dirty 非汚染**（例外経路含む）/ 4. **保存失敗時に確定しない** /
   5. **セッション内復活の境界** / 6. **層の分離**（application・domain に tkinter 依存なし・
   presentation が config.json を直接書いていない）

### 3. 実機目視シナリオ（ユーザー実施）

**ユーザーへ提示して実施してもらう**。結果をメインセッションへ報告してもらい、完了報告に含める。

| # | 手順 | 期待 |
|---|---|---|
| G1 | 起動 →（個別指定チェック **OFF** の状態で）停止トリガーを「キー入力で取得」→ 適当なキーを押す | キーが表示に入り、**タイトル / ファイル状態が未保存（dirty）にならない**。`config/config.json` に `hook_stop_key` が書かれる |
| G2 | G1 のあとアプリを再起動する | 設定した停止トリガーが**そのまま表示される**（全体デフォルトが効いている） |
| G3 | 「新規作成」する | hook キーが**再設定不要**（全体デフォルトの値が入っている）。チェックは OFF |
| G4 | 個別指定チェックを **ON** にして、停止トリガーを別のキーで取得 → 保存 | 保存後の keymap_set.json に**個別値**と `"hook_keys_individual": true` が入る。`config/config.json` の全体デフォルトは**変わらない** |
| G5 | G4 の keymap_set でチェックを **OFF** に戻す | 表示が**全体デフォルトの値**へ切り替わる |
| G6 | G5 の直後にチェックを **ON** へ戻す | **G4 で設定した個別値が復活**する |
| G7 | 再度 OFF にして**保存**し、そのあと ON にする | 個別値は**復活せず空**になる。保存された keymap_set.json は hook キーが `""` + `"hook_keys_individual": false` |
| G8 | フックを開始し、停止トリガー / トグルキーを実際に押す | OFF なら全体デフォルトのキーで、ON なら個別値のキーで**実際にフックが反応する** |
| G9 | compact 表示へ切り替える | チェックは**状態表示のみ**（クリックしても変わらない）。キーは readonly 表示 |

- **G1 / G7 は本フェーズの中核**（dirty 非汚染・保存後は復活しない）。
- 目視で異常があれば**フェーズを完了扱いにせず**、原因タスクへ戻る。

## 含まない

- 新機能の追加・仕様変更（発見した仕様の穴は `.claude/rules/spec_change_workflow.md` に従い**報告のみ**）。
- 正本 `spec_detail/` への反映・暫定仕様 06 の凍結・`decisions_archive` 作成・`current.md` 更新・
  `/refactor_check` → すべて **task_08**。
- リファクタ（`/refactor_check` の判定も task_08）。

## 確認

python は**リポジトリルートの `.venv`**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。

1. `-m compileall -q keyseq main.py tests tests_ui` が clean。
2. `-m unittest discover -s tests` が全 pass（**件数を報告**。現在 168 件）。
3. `-m unittest discover -s tests_ui` が全 pass（**件数を報告**。現在 176 件）。
4. `-m tests.smoke_app` が pass。
5. 上記「対象範囲 1」の対応表に**空欄が無い**こと（あればテストを追加して埋める）。
6. 上記「対象範囲 2」の不変条件 1〜6 がすべて維持されていること
   （特に**フック層が無変更**であることを `git diff caf41a7..HEAD --stat` で確認する）。
7. **実機目視 G1〜G9 がすべて OK**（ユーザー実施・結果を報告に含める）。

## 完了条件

- 「確認」1〜7 がすべて pass。
- **`deep-reviewer` 採用**（フェーズ完了判定・複数タスクを跨ぐ差分）+ **Codex レビュー系**の実施
  （`codex-adversarial-reviewer`。指摘は提示のみで採否はユーザー）。
  Codex が使えない場合は報告のうえ Claude 側のみへ縮退してよい。
- 実機目視の結果が完了報告に含まれていること。
- **異常・未達があれば task_08 へ進まない**（原因タスクへ戻す）。
