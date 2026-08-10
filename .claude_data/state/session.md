# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-08-10T11:20:00
phase: `instructions/phase/09_per_keymap_set_presets`（**task_05 完了 / 次は task_06**。暫定仕様 08 は **v0.4・ユーザー確定済**）
last_commit_location: claude/task-05-progression-a013e2 ※現在地はセッション開始時の git 実測値が正

## current
focus: **phase 09 は task_05（マネージャ内の切替 UI と OK/キャンセルの契約）まで完了し、ユーザーが個別／グローバルを切り替えられるようになった。次は task_06 = Import の強制 OFF + 別名保存時の個別ファイル複製**。
mode: implementing

## last_action
ts: 2026-08-10T11:20:00
who: main
summary: |
  【phase 09 task_05 = **マネージャ内の切替 UI と OK / キャンセルの契約**
  （暫定仕様 08 §2【D】【E】【F】【H2】【J】【N】【Q】【R】【I 撤回】/ §3-4）】
  - **仕様の解釈を 2 点確定**（暫定仕様が文言レベルまで規定していなかった箇所。タスク定義へ明記）:
    ① **表示は 2 行**（「保存先」= チェックに追従 / 「出どころ」= ダイアログを開いた時点で固定）。
    トグルで一覧を差し替えない【I 撤回】以上、1 行に混ぜると両立しないため。
    ② **判定は application 側の新 API 2 本**（presentation で組み立てない。task_04 と同方針）。
  - application: `resolve_hotkey_presets_save_path` へ **`individual: bool | None` の override**
    （**runtime は書き換えない**。局所コピーで判定）+ `describe_hotkey_presets_source`
    （`individual_state` = off/active/missing/invalid × `displayed_source` = individual/global/builtin。
    **既存 3 関数を再利用**し解決順序を二重化しない）+ グローバルパスと再読込の委譲メソッド。
  - presentation: `PresetManagerDialog` に**チェック + 保存先ラベル + 出どころラベル**、
    keymap_set 未保存なら **disabled + 理由表示**【F】。**文言は Tk 非依存の純関数
    `format_preset_manager_source_labels`** へ分離（テストから固定できるように）。
  - `App.save_hotkey_presets(presets, *, individual=None)` の 4 分岐:
    OFF→OFF / ON→ON は**現行どおり + dirty を触らない** / OFF→**ON** は個別へ書き成功時のみ
    3 キー反映 + dirty True / **ON→OFF は書き込まず**フラグだけ False にして
    **`hotkey_presets_path` を保持**【N】・**グローバルを読み直す**【H2】・dirty True。
    **失敗時は `data` を一切変更しない**（先にフラグを立てて戻す形にしない）。
  - 【Q】の再評価は**ダイアログを毎回構築し直す性質**で満たす（通知の仕組みは足さない）。
result_files:
  - instructions/phase/09_per_keymap_set_presets/tasks/task_05_manager_toggle_ui.md（新規・起票）
  - keyseq/application/config_service/{__init__.py,split_loading.py}
  - keyseq/presentation/app.py / dialogs.py
  - tests/test_config_service.py / tests_ui/test_app_ui_flows.py
verified:
  compile: clean
  tests: pass **222**（基準線 220 → +2）
  tests_ui: pass **196**（基準線 189 → +7）
  smoke: pass
  review: `reviewer` = **採用（完了可）**。【H2】でグローバルを書かない / トグルで `_temp` 不変 /
    dirty がフラグ変化時のみ / 失敗時 data 完全不変 / 判定の application 集約 / override が
    runtime 非破壊 / 後続タスクの先取りなし を確認。**参考指摘 1 件（下記 blockers 参照）**

## next_action
- **【先にユーザー判断が要る】`reviewer` の参考指摘 = 未定義挙動の疑い**（task_04 由来・task_05 の
  スコープ外のため今回は不変で通した）。**task_06 着手前に方針を確認する**:
  「`hotkey_presets_individual` が ON かつ `hotkey_presets_path` が **config 外（無効）** のとき、
  UI は『無効』と表示するのに **OK 押下の保存先はグローバルへ倒れる**」。
  `resolve_hotkey_presets_save_path` は「パスが非空なら既定パスへ差し替えない」ため、
  無効パスが非空である限り既定パスへも落ちない。**専用のつもりの操作でグローバル
  ライブラリが上書きされ得る**（暫定仕様 08 の「グローバルの保護」観点と衝突する疑い）。
  選択肢 = (A) 現状維持〔読み出しと同じくグローバルへ倒す〕/ (B) 無効時は**既定の個別パス**へ
  逃がす / (C) 無効時は**保存を拒否**して理由表示。**暫定仕様 08 §2【O2】は読み出しのみ規定**。
- **task_06 を `/task_new` で起票 → 実装委任**する（規範 = 暫定仕様 08 **§2【K】【L】**・
  受入条件 **12 / 16**）。内容:
  1. **Import での強制 OFF**（`load_legacy_runtime_data` の**直後・`apply_global_defaults` の前**。
     `hotkey_presets_individual=False` / `hotkey_presets_path=""`。
     **`ensure_config_compatibility` には入れない**＝通常読込へ波及させないため）
  2. **別名保存で個別ファイルを複製**（新しい stem から個別パスを再計算 → `hotkey_presets_path` 更新。
     **コピー先に実体があれば複製しない / コピー元が無ければ複製しない**。上書き確認は新設しない）
  3. 複製は**ファイルのコピー**であり **runtime の内容を書き出さない**（書き手 1 本を維持）
- 以降の流れ（各タスク共通）: 実装委任（**テスト追加まで含める / 実行は依頼しない**）→
  `verifier` で実測 → `reviewer` → `/save_state` + `/task_commit`。

## blockers
- **task_06 着手前にユーザー判断が必要**（上記 next_action の 1 件目 = config 外の無効な個別パスで
  OK したときの保存先）。**task_05 の完了判定自体はブロックしない**（スコープ外・既存挙動）。

## resume_hints
- **python は必ずリポジトリルートの `.venv` を使う**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
  グローバル `py` は依存欠落で tests_ui/smoke が落ちる。
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
