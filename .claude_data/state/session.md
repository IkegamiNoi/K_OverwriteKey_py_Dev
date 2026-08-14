# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-08-15T04:30:00
phase: `instructions/phase/09_per_keymap_set_presets`（**暫定仕様 08 を v0.8 へ改訂・ユーザー確定済**。**task_07c・07d・07e 完了＝v0.8 の実装は全て入った**。次は task_07 の実機目視やり直し〔ユーザー作業〕）
last_commit_location: claude/preset-file-save-reference-903f03 ※現在地はセッション開始時の git 実測値が正

## current
focus: **task_07 の実機目視で見つかった 3 件（残置パス / トグル時の上書き / config 外パス）を仕様 v0.8 として確定し、是正 3 タスク（07c・07d・07e）を全て完了。残るは実機目視のやり直し〔ユーザー作業〕→ task_08 正本反映**。
mode: blocked

## last_action
ts: 2026-08-15T04:30:00
who: main
summary: |
  【**task_07e 完了 = トグル時の読み直し + 破棄確認 + OFF での書き込み**
  （暫定仕様 08 **§2【I】【E】【H2 撤回】【R】v0.8**・受入条件 13）】
  - `PresetManagerDialog` に **`_reload_presets_for_individual_toggle`** を新設。
    **ON = 個別ファイル**（読み出し用解決）/ **OFF = グローバル、読めなければ組込既定**
    （`config_service.new_default_data()["hotkey_presets"]`）へ一覧を差し替える。
    **`_loaded_temp`（直近に読み込んだ一覧）**との比較で編集済みのときだけ `askyesno` を出し、
    **いいえ ならチェックを元へ戻す**。**トグルは `parent.data` を変更しない**。
  - `app.py` の **ON→OFF 特別分岐を削除**し、OFF も通常のグローバル書き込み経路へ（【H2】撤回）。
  - **`tests_ui` 4 ファイルすべてに `askyesno` の fail-fast ガードを追加**。実体テスト 7 本を追加し、
    旧 `test_preset_manager_toggle_keeps_temp_presets`（モック多用・v0.7 契約）を置換。
  - **`reviewer` = 修正要 → 是正 → 完了可**。指摘は**依存方向 1 件**（`dialogs.py` が
    `split_loading` を直接 import）で、**`ConfigService.load_individual_hotkey_presets` を追加**して
    ファサード経由へ統一した（**挙動不変・件数不変で再実測 green**）。
  - **【運用】Codex フォワーダが 2 分で切れてもワーカーは生き続ける**。ログパイプが切れて
    companion status が running のまま停滞するが、**作業ツリーの更新時刻で継続中と判別できる**。
    今回はこれに気付かず**書き換え途中の状態で verifier / reviewer を回してしまい**、
    偽の fail 1 件を掴んだ（**両方やり直した**）。ワーカー終了後に state を §4 の手順で手修復済み
    （`taskkill` 不使用）。
result_files:
  - keyseq/presentation/dialogs.py（トグルハンドラ・破棄確認・組込既定フォールバック・ラベル排他化）
  - keyseq/presentation/app.py（ON→OFF 特別分岐の削除）
  - keyseq/application/config_service/__init__.py（`load_individual_hotkey_presets` 委譲メソッド）
  - tests_ui/test_app_ui_flows.py（実体テスト 7 本）+ 他 3 ファイルの fail-fast ガード
  - .claude_data/state/session.md / instructions/phase/current.md
verified:
  compile: clean
  tests: pass **237**（変化なし）
  tests_ui: pass **213**（基準線 207 → +6）
  smoke: pass
  review: `reviewer` = **完了可**（是正後）。流出経路の遮断〔トグル / いいえ / 読み直し失敗 / 再オープン〕・
    トグルが runtime 不変・破棄確認の比較基準・app.py の dirty /【O3】【O4】契約・
    fail-fast ガード 4 ファイル・テストが v0.8 契約を固定していること を確認

## next_action
- **【ユーザー作業・ブロッカー】task_07 の実機目視をやり直す**
  （`tasks/task_07_integration_check.md` §3 の表が正。**項目 2 / 5 / 6 / 7 / 7b / 10 / 11 が v0.8 の期待値**。
  特に重要 = **7b**〔グローバルを削除した状態で ON→OFF → 組込既定で作り直され、個別の内容が流出しない〕/
  **2**〔phase 08 以前の `keymap_set1〜3.json` で ON にしても `<stem>.json` になる〕/
  **11**〔【O3】〕/ **15**〔手動移行の 2 段〕）。結果をメインセッションへ報告してもらう。
  - 目視で不具合が出たら **task_07 内で是正**（最小差分 + `reviewer` 再実施）。仕様変更を伴うなら
    **枝番タスクへ切り出す**（07b〜07e と同じ流儀）。
- その後 **task_08 = 正本反映（最終）**: `data_schema.md` §5.10 改訂 + §5.5 / §5.4 / §5.8.8 / §5.1 +
  `codebase_map.md` / 暫定仕様 08 を凍結 / `decisions_archive/09_per_keymap_set_presets.md` 作成 /
  `current.md` 完了更新 / `backlog/INDEX.md` の idea_08 を `INDEX_done.md` へ移動 / `/refactor_check`。
  - **正本へ追加する項目（N9）**: 入口台帳 §5.8.8 へ **「OFF 復帰時のグローバル再読込」経路**を
    追加する（E1〜E5 のどれでもない新しい供給点）。**プリセット単独の注入 API は増やさない**ことも明記。
  - **v0.5→v0.6 の反転（【O3】）/ v0.7 の【O4】/ v0.8 の 3 改訂 / dirty 規則 /
    task_05b が task_05c で置き換わった経緯**を decisions_archive へ集約すること。
- 各タスク共通の流れ: 実装委任（**テスト追加まで含める / 実行は依頼しない**）→ `verifier` で実測 →
  `reviewer` → `/save_state` + `/task_commit`。

## blockers
- **task_07 の完了に実機目視（ユーザー作業）が必要**。それまでフェーズ完了判定は出せない。
  **v0.8 の実装 3 本（07c / 07d / 07e）は揃った**ので、目視をやり直せる状態。

## resume_hints
- **python は必ずリポジトリルートの `.venv` を使う**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
  グローバル `py` は依存欠落で tests_ui/smoke が落ちる。
- **【暫定仕様 08 は v0.8 が正】**版が多いので**古い版の条項を引かない**。v0.8 で変わったのは 3 点 =
  ①**フラグキーが無ければ残置 `hotkey_presets_path` も落とす**（判定はキーの**有無**。false + キーありは
  【N】で保持）②**【I】再採用**（トグルで一覧を読み直す・**【H2】撤回で OFF の OK もグローバルへ書く**・
  **グローバルが読めなければ組込既定へ差し替える**）③**【O2】config 外は読み出しのみ許容**
  （**書き込みは【O3】のまま管理下へ寄せる**＝読み書きで非対称なのは意図どおり）。
- **【phase 08 の成果は正本が正】** `spec_detail/data_schema.md` **§5.10**（プリセットの全体ライブラリ）
  + **§5.8.8**（**全体デフォルトの入口台帳 E1〜E5 / L1〜L3 / N1**）+ §5.1 の例外 + `codebase_map.md`。
  暫定仕様 07 は**凍結済**。要点だけ再掲 = ①runtime を新規化・置換したら
  **`apply_global_defaults` を呼ぶ**（通常読込は経由しないが供給規則は共通 /
  **ON→OFF の hook キー単独注入だけ `apply_global_hook_key_defaults` を直呼び**）
  ②プリセットの読み出しは **`list | None`**（読めたら空でも採用 / `None` は置き換えない）で
  **読み出し側で正規化**（**非文字列 `label`/`value` の要素は除去**。ここを緩めると起動不能が再発する）
  ③**書き手は `PresetManagerDialog.on_ok` → `App.save_hotkey_presets` →
  `HotkeyPresetsIo` → `ConfigService.save_global_hotkey_presets` の 1 本のみ**
  （カスケードは書かない / 失敗時は確定せずダイアログを閉じない / dirty を汚さない）。
- **【tests_ui の罠・追加】`AppUiFlowsTest` は `setUpClass` で App を 1 つ共有する**ため、
  `has_unsaved_changes()` は他テストが残した個別 dirty も拾う。**絶対値で assert せず、
  前後の変化 / `set_dirty` の呼出有無で見る**こと（task_06 で 1 度踏んだ）。
- **hook キー（Phase γ の成果）は正本が正**: `spec_detail/data_schema.md` **§5.9** +
  `key_input.md` **§7.6** + `codebase_map.md`。暫定仕様 06 は**凍結済**（経緯の参照用）。
  要点だけ再掲 = **解決の分岐点は 4 つ**（`load_global_hook_keys` 読み出し /
  `build_runtime_data_from_split` 通常読込の選択 / `apply_global_hook_key_defaults` 新規化・置換経路
  〔**通常読込は経由しない**〕/ `build_keymap_set_payload` 保存側）。**フック層は無変更**が設計の芯。
- **【計画06 で変わった構造】hook キー名の定義元は `keyseq/domain/config.py` の `HOOK_STOP_KEY` /
  `HOOK_TOGGLE_KEY` / `HOOK_KEY_FIELDS`（対のタプル）+ `normalize_hook_key_pair()`**。新たに触る箇所は
  リテラルを書かずこれを使う（**添字参照 `HOOK_KEY_FIELDS[0]` は禁止**。反復・zip でのみタプルを使う）。
  意図的にリテラルのまま残した 3 箇所 = `DEFAULT_CONFIG` の既定値表 / `split_payloads` の返却 dict キー /
  `startup_io` の保存 dict キー。**保存 JSON のキー順は
  `tests/test_save_plan.py::test_saved_keymap_set_json_keeps_stable_key_order` が固定している**。
  `ensure_config_compatibility` と `build_keymap_set_payload` が `normalize_key_name` 直呼びのままなのは
  **非文字列時の例外を握り潰さないため**（`normalize_hook_key_pair` は `str()` を挟む）。
- **Phase β の成果も正本が正**: `data_schema.md` **§5.8**（子ファイルの保存計画と参照元記録）+
  §5.4 / §5.6 / §5.7、`features.md` §4.6、`codebase_map.md`。暫定仕様 05 は凍結済。
- **【最重要・2 度踏んだ罠】パス表記の混在事故**: runtime の `source_path` 3 種は **config 配下なら相対**で
  保持される（config 外は絶対・区切りは `/` 正規化）。**相対値を `os.path.abspath` / `dirname` / `exists` /
  `join` へ解決なしで渡すと cwd 基準で解決される**。症状 = **リポジトリルートに `user/` が生成される** /
  「別名で保存」が前回の場所に開かない。解決は `ConfigService.resolve_config_path(path, config_root)`。
  `to_config_relative_or_absolute` は**入口で解決するので相対を渡してよい**。
- **不変条件（壊しやすい）**: ① `dirty_tracker.trigger_set_source_path` と
  `data[INTERNAL_TRIGGER_SET_SOURCE_PATH]` は**常に一致**（入口は `dirty_state` のメソッドのみ）/
  ② 子の `_parent_refs` は**保存先ファイルの集合 + 現在の上位**（in-memory の旧 refs を持ち込まない）/
  ③ **canonical identity は比較専用**（`canonical_path` / `is_path_within` の 2 本。
  `normcase` 済み文字列を保存値・戻り値・表示へ混入させない）。
- **【共有状況の判定名と表示文言は別物】** 仕様書・タスク定義の「共有状況が単独 / 新規作成なら〜」は
  **判定名**（`SHARE_SOLE` / `SHARE_NEW`）を指す。**分岐は判定名で書き、文言で分岐しない**。
- **【罠・重要】保存経路の例外は `messagebox.showerror` になり、テストではモーダルで永久ブロックする**。
  tests_ui の 4 ファイル（`test_child_save_dialog` / `test_config_io_characterization` /
  `test_config_io_characterization_keymap_set_startup` / `test_app_ui_flows`）の
  `setUp` に **fail-fast ガード**がある。
  新しいモーダルを増やすときは同じガードを足す。**ハングしたら `messagebox` / `filedialog` を全遮断して
  単独実行**すると真因が一発で出る。
- **【tests_ui の罠】`_prepare_loaded_keymap_set` は `save_plan=None` で `save_runtime_data` を呼ぶため
  runtime に source_path が入らない**。source_path 前提のテストは保存後に
  `load_runtime_data_from_keymap_set_path` で読み直すこと。
- **【Codex 運用・重要】詰まったジョブに `taskkill /T` を使わない**（PID 再利用で**無関係な
  プロセスを巻き込む**。phase 09 task_04 で `node_repl` 約 22 個を巻き込んだ実害あり）。
  **`codex_operations.md` §4 の state 手修復**（backup してから `cancelled` へ書換・`.log` は保全）に倒す。
- **【Codex 運用・重要】フォワーダが 2 分で切れても Codex ワーカーは生き続ける**（node ラッパだけが死に、
  ログパイプが切れて companion status は `running` のまま停滞する）。**ハングと即断しない**。
  判別は**作業ツリーの更新時刻**（対象ファイルが数十秒以内に更新され続けていれば作業中）。
  **書き換え途中で `verifier` / `reviewer` を回すと偽の結果を掴む**（phase 09 task_07e で実際に踏んだ）。
  ワーカー終了後は state が自己更新されないため `codex_operations.md` §4 で手修復する。
- **【Codex 運用】**フォワーダが最終出力を返さず完了通知だけ来ることがある（`SendMessage` で再開して回収）。
  **Codex 申告のテスト結果は信用せず必ず verifier で再実行**。**Codex は python をまったく実行できない**
  → 委任にテスト実行を含めない。手順書は `instructions/common/rules_detail/codex_operations.md`。
- **【罠】state ファイル・`instructions/` 配下・code は必ず worktree のパスで編集する**（main 側を編集すると
  commit から漏れる）。`git grep` は追跡済みファイルのみ。行数計測は `wc -l`。
- **レビュアーは 2 本立て**: `reviewer`（sonnet・単一タスクの実装差分）/ `deep-reviewer`（opus・設計文書 /
  複数タスクを跨ぐ差分 / フェーズ完了判定）。使い分けは `.claude/rules/agent_selection.md` が正。
- **保存系リデザインの番号対応**: α=phase05/暫定04〔完了〕 / β=phase06/暫定05〔完了〕 /
  γ=phase07/暫定06〔完了〕 / プリセット=phase08/暫定07〔**完了**・decisions_archive 08〕 /
  **個別プリセット=phase09/暫定08〔着手中〕**。
  **計画05・計画06 はフェーズ番号を消費していない**（規範 = `modified_proposal/05_*.md` / `06_*.md`）。
- **【計画05 で変わった構造】`config_service` は単一ファイルではなく*パッケージ***
  （`keyseq/application/config_service/`）。**ConfigService 本体は `__init__.py`**
  （テストが `patch("keyseq.application.config_service.os.path", ntpath)` で名前空間を差し替えるため、
  この配置を崩すと 4 テストが壊れる。同じ理由で**パス基盤メソッドを兄弟へ移さない**）。
  兄弟 = `save_plan_execution.py` / `split_payloads.py` / `save_path_resolution.py` / `split_loading.py`。
  抽出関数は **`service` を第 1 引数に取る**。兄弟から `__init__` を import しない（循環回避）。
- config_io は `controllers/config_io/` へ分割済（App が `app.keymap_set_io` 等で直接公開）。
- 未着手 idea: idea_07（参照元の掃除・**着手可**）/ idea_03（hotkey 保存時正規化・優先度低）/
  idea_09（レガシー settings/ フォールバック・優先度低）。**idea_08 は phase 09 で着手中**。
  保留 idea: idea_04 / idea_06（**残る着手条件は「共通化の実需」1 つのみ**）。
- 過去の判断は `.claude_data/state/decisions.md`（アーカイブ索引）+ `decisions_archive/<phase>.md`。
  完了済の直近 3 件: 06_child_file_save_dialog / 07_hook_keys_global_default /
  **08_hotkey_presets_global**。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
