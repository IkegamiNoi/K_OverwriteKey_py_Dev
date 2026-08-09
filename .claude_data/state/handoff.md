# handoff.md

過去の会話履歴は参照しないでください。
このファイルと `.claude_data/state/session.md` を起点に作業を再開してください。

## プロジェクト概要
- 言語/実行: Python（tkinter GUI）。オニオン構成（presentation / application / domain / infrastructure）。
- 対象アプリ: keyseq（キー割り当て/オーバーライドツール）。全体仕様は `instructions/common/`（`app_overview.md` / `codebase_map.md`）参照。
- **python 実行は必ずリポジトリルートの `.venv` を使う**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
  依存 keyboard/pyautogui/pynput はこの `.venv` にのみ導入済み。グローバル `py` は使わない（tests_ui/smoke が落ちる）。
- **Codex は python を一切実行できない**（サンドボックス制約・回避不能）。実装委任にテスト実行を含めず、
  実測は `verifier`（またはメイン）が行う（理由は `instructions/common/rules_detail/codex_operations.md` §0）。

## 再開手順
1. `.claude_data/state/session.md` を読む（最重要・最新状態）
2. `instructions/phase/current.md` を読む（**アクティブなフェーズは無い**。次フェーズ候補と次採番がここ）
3. **次フェーズの方針をユーザーへ確認する**（未確定のまま着手しない）
4. CLAUDE.md → `.claude/rules/` の順に必要分を読む
5. 過去の判断は `.claude_data/state/decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`

## 現在の作業の 1 行サマリ
**phase 08（プリセットの config.json グローバル化）は 2026-08-09 完了。次フェーズは未確定で、着手前にユーザーへ方針確認する**。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近の実測（phase 08 完了時・コミット `25467e8`）:
compile **clean** / tests **203** / tests_ui **186** / smoke **pass** / manual **OK**。
**件数が減ったら退行を疑う**。実行後に worktree ルートへ `user/` が生成されていないことも確認する。

## 次アクション（session.md.next_action より）
- **次フェーズの方針をユーザーへ確認する**。候補（`instructions/phase/current.md`「次フェーズ候補」）:
  - **[idea_08] keymap_set ごとの個別プリセット**（phase 08 完了で**着手可**。停止/トグルキーの
    個別指定〔正本 §5.9〕と同型で、前提の正本は **§5.10**。保存系リデザインの自然な続き）
  - [idea_07] 参照元の掃除（孤児 trigger_set と陳腐化した `_parent_refs` の回収・着手可）
  - [idea_09] レガシー `settings/` 保存パスのフォールバック / [idea_03] アクション hotkey の
    保存時正規化（いずれも優先度低）
  - 未承認の提案書 [05_refactor_child_file_save_dialog] と、`current.md`「別タスク化候補」の項目
- 決まったら `/phase_start` で起票（**次採番: フェーズ `09_<topic>` / 暫定仕様 `08_<topic>` /
  リファクタ提案書 `07_<topic>`**）。
- 各タスクの流れ: タスク定義起票 → codex-implementer へ委任 → **verifier で実測** → reviewer → コミット。

## 直前フェーズ（phase 08 = プリセットの config.json グローバル化）の要点

**正本が正**: `spec_detail/data_schema.md` **§5.10**（プリセットの全体ライブラリ）+ **§5.8.8**（入口台帳）
+ §5.1 の例外 / §5.4 / §5.5 / §5.9.2、および `codebase_map.md`。暫定仕様 07 は**凍結済**。
判断履歴は `decisions_archive/08_hotkey_presets_global.md`。

- hotkey プリセットは **`config/config.json` の `hotkey_presets_path` が指すアプリ全体のライブラリ**
  （既定 `user/hotkey_presets/default.json`）。**アプリはこのキーを書かない**（手編集はアプリ終了中に）。
  keymap_set 側の同キーは**生成停止・読込時無視**（**能動削除しない**＝再保存で自然消滅。§5.1 の例外）。
- **全体デフォルトの注入は `ConfigService.apply_global_defaults` の 1 本**。呼ぶのは**入口台帳 E1〜E5**
  （App 初期化 / 新規作成 / 例を復元 / 空データ起動 / Import）。**L1〜L3（通常読込）は経由しない**が
  供給規則は共通。**N1 は供給不要**。**全体デフォルトを増やすときは台帳の全経路を見る**。
- **単独注入が残るのは個別指定 ON→OFF だけ**（`apply_global_hook_key_defaults` を直呼び）。
  束ねた API を使うとキー切替だけでプリセットが再読込され、編集中の内容を取りこぼす。
- **読み出しは `load_global_hotkey_presets` が `list | None`**: 読めた＝`list`（**空も採用**）/
  不存在・破損・非 dict・根キー非 list＝`None`（**置き換えない**）。
  戻り値は**正規化済み**（trim / 小文字化 / **非 dict 要素と非文字列 `label`・`value` の要素を除去**）。
  **「読めたか」の判定は正規化の前**。**正規化は読み出し側 1 箇所**（ここを緩めると起動不能が再発する）。
- **書き手は 1 本のみ**: `PresetManagerDialog.on_ok` → `App.save_hotkey_presets` →
  `HotkeyPresetsIo.write_global_presets`（成否 bool）→ `ConfigService.save_global_hotkey_presets`
  （**例外は送出**し presentation が成否へ変換）。**保存カスケードは書かない**。
  **失敗時は runtime を更新せずダイアログも閉じない**。プリセット編集は **dirty を汚さない**。
- **既知の制約（実装は変えない）**: `None` のとき runtime は **E4 = 空 / E5 = Import のインライン値 /
  それ以外 = 組込 8 件**と割れる（その内容でライブラリが確定し得る）/ 破損ファイルも上書きする /
  旧「別ディレクトリ保存」の孤児プリセットは参照されない / Export のインライン値は Import で置き換わる。

## 注意事項・blockers
- **blockers: なし**。
- **【config_service の配置制約】`config_service` はパッケージ**（`keyseq/application/config_service/`）で
  **ConfigService 本体は `__init__.py`**。テスト 4 箇所が
  `patch("keyseq.application.config_service.os.path", ntpath)` で**モジュール名前空間の `os.path` を差し替える**
  ため、この配置を崩すと壊れる。同じ理由で**パス基盤メソッド**（`canonical_path` / `is_path_within` /
  `to_config_relative_or_absolute` 等）**を兄弟モジュールへ移さない**。
  兄弟 = `save_plan_execution.py` / `split_payloads.py` / `save_path_resolution.py` / `split_loading.py`。
  抽出関数は **`service` を第 1 引数に取る**。**兄弟から `__init__` を import しない**（循環回避）。
- **【最重要・2 度踏んだ罠】パス表記の混在事故**: runtime の `source_path` 3 種は **config 配下なら相対**で
  保持される（config 外は絶対・区切りは `/` 正規化）。**相対値を `os.path.abspath` / `dirname` / `exists` /
  `join` へ解決なしで渡すと cwd 基準で解決される**。症状 = **リポジトリルートに `user/` が生成される** /
  「別名で保存」が前回の場所に開かない。解決は `ConfigService.resolve_config_path(path, config_root)`。
  `to_config_relative_or_absolute` は**入口で解決するので相対を渡してよい**。
- **不変条件（壊しやすい）**: ① `dirty_tracker.trigger_set_source_path` と
  `data[INTERNAL_TRIGGER_SET_SOURCE_PATH]` は**常に一致**（入口は `dirty_state` のメソッドのみ・内部キー直代入禁止）/
  ② 子の `_parent_refs` は**保存先ファイルの集合 + 現在の上位**（in-memory の旧 refs を持ち込まない）/
  ③ **canonical identity は比較専用**（`normcase` 済み文字列を保存値・戻り値・表示へ混入させない）/
  ④ **共有状況は判定名で分岐する**（`SHARE_SOLE` / `SHARE_NEW`。表示文言 `share_text_for` で分岐しない）。
- **【hook キー（phase γ）】キー名の定義元は `domain/config.py`**（`HOOK_STOP_KEY` / `HOOK_TOGGLE_KEY` /
  対のタプル `HOOK_KEY_FIELDS` / `normalize_hook_key_pair`）。新規箇所はリテラルを書かない
  （**添字参照 `HOOK_KEY_FIELDS[0]` は禁止**）。**明示列挙のまま残す 3 箇所** = `DEFAULT_CONFIG` /
  `split_payloads` の保存 dict キー / `startup_io` の保存 dict キー
  （保存 JSON のキー順は `tests/test_save_plan.py::test_saved_keymap_set_json_keeps_stable_key_order` が固定）。
  config.json への書き込みは `StartupIo.write_startup`（`-> bool`）に集約する
  （**別経路で read-modify-write しない**。`_startup_settings` と乖離すると次の書き出しでキーが消える）。
  仕様は `spec_detail/data_schema.md` §5.9 + `key_input.md` §7.6。
- **【罠・重要】保存経路の例外は `messagebox.showerror` になり、テストではモーダルで永久ブロックする**。
  テスト内の `AssertionError` も広い `except Exception` に捕まり、**失敗が「ハング」に化ける**。
  tests_ui の 4 ファイル（`test_child_save_dialog` / `test_config_io_characterization` /
  `test_config_io_characterization_keymap_set_startup` / `test_app_ui_flows`）の `setUp` に
  **fail-fast ガード**がある。期待するテストは個別 patch で上書きする。新しいモーダルを増やすときは
  同じガードを足す（`askyesnocancel` はガードへ入れない）。
  **ハングしたら `messagebox` / `filedialog` を全遮断して単独実行**する。
- **【tests_ui の罠】`AppUiFlowsTest` は `setUpClass` で App を 1 つ共有する**。
  `dirty_tracker.has_unsaved_changes()` は個別 dirty（trigger_set / sequence / keymap）も OR するため、
  **絶対値で assert せず前後の変化・`set_dirty` の呼出有無で見る**。
- **【tests_ui の罠】`_prepare_loaded_keymap_set` は `save_plan=None` で `save_runtime_data` を呼ぶため
  runtime に source_path が入らない**。source_path 前提のテストは保存後に
  `load_runtime_data_from_keymap_set_path` → `apply_loaded_data_to_ui` で読み直すこと。
- **【tests_ui の罠】特性テストは `config_service` の生成系をスタブ dict で差し替える**
  （`new_empty_data` → `{"empty": True}` 等）。runtime へキーを増やす変更を入れると
  `assertEqual(self.app.data, {...})` が落ちる。**実装ではなくテスト側の追従で正しい**。
- **【教訓・UI】tkinter の「初期表示だけ崩れる」系は one-shot の再計算（`after_idle` 1 回）では直らない**。
  **対象ウィジェット自身の `<Configure>` で自己修復させる**（同幅早期 return を必ず併設）。
- **【Codex 運用】フォワーダが最終出力を返さないまま完了通知だけ来る / 差分 0 件で返る**ことがある
  → `SendMessage` で同じフォワーダを再開して回収する。**Codex 申告のテスト結果は信用せず必ず verifier で再実測**。
  **報告が「実装物なし」でも鵜呑みにせず `git status` / `git log` で自分で確かめる**（コミット後だと空に見える）。
  **worker PID が消えたジョブは `cancel` が効かない** → `codex_operations.md` §4 の state 手修復
  （`state.json` と `jobs/<id>.json` を **backup してから** `cancelled` へ書換・`.log` は保全）。
- **【サブエージェントが落ちるとき】** セッション上限に当たると `verifier` / `reviewer` が
  API エラーで終了する。**実測はメインで代行してよい**（縮退した旨を報告に書く）。
  レビューは必須なので、時間をおいて再実行する。
- **【罠・再発済】worktree と main は別コピー**。`.claude_data/`・`instructions/`・code とも、main 側の絶対パス
  （パスに `.claude\worktrees\<name>\` を含まない）を編集すると commit から漏れる。編集は必ず worktree ルート配下で。
- **【罠】Bash ツールは Git Bash**。PowerShell の here-string（`@'...'@`）はコミットメッセージに `@` が混入する。
  複数行は heredoc（`git commit -F - <<'EOF'`）を使う。
- **【罠】`git grep` は追跡済みのみ検索**。新規（未追跡）ファイルの確認は**直接 `grep`**。行数計測は `wc -l`。
- **【傾向・phase 08 で 4 回発生】reviewer が「完了可」でも実測・別レビューで問題が出る**。
  **判定はテストの実測が優先**。fail が出たら**まず production か test かを切り分ける**。
  レビュー依頼では**呼び出し元を含む全テスト**を対象に指示する（変更ファイル限定だと追随漏れを拾えない）。
  **フェーズ完了時は Claude 側 × Codex 側の 2 本立てを省略しない**（phase 08 では両者が独立に
  同じ起動不能バグを検出した）。
- レビュアーは 2 本立て: `reviewer`（sonnet・単一タスクの差分）/ `deep-reviewer`（opus・設計文書/統合/完了判定）。
  Codex レビュー系との併用は `.claude/rules/agent_selection.md` のレビュー表が正。出力の作法は
  `.claude/rules/output_style.md`。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近 3 件: **08_hotkey_presets_global** / 07_hook_keys_global_default / 06_child_file_save_dialog）。
  提案書「計画05」「計画06」は完了済みで、**どちらもフェーズ番号を消費していない**。
- 未着手/保留 idea: **idea_08（keymap_set 個別プリセット・着手可）** / idea_07（参照元の掃除・着手可）/
  idea_03（hotkey 保存正規化・低）/ idea_09（レガシー保存パス・低）/ idea_04・idea_06（保留）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
