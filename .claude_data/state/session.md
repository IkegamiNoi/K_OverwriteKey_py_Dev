# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-09-06T12:00:00
phase: **11_orphan_child_file_sweep（孤児ファイルの棚卸し）= task_01 / task_02 完了 / task_03 未着手**。番号対応: phase 11 / 暫定 10 / decisions_archive 11。次採番は `instructions/phase/12_<topic>`
last_commit_location: claude/task-02-progression-2fd81c @ 最新コミット = `task_02: 走査と孤児判定（orphan_scan）を新設` ※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 11 task_02（走査と孤児判定）完了**（verifier 実測 green / reviewer = 完了可）。次は **task_03（検出フローの入口と表示）= 検出のみが green になる区切り**。
mode: in_progress

## last_action
ts: 2026-09-06T12:00:00
who: main
summary: |
  【**phase 11 task_02 完了**】走査と孤児判定（application・読み出し専用）を新設。
  タスク定義の起票はメイン → 実装は `codex-implementer` → `verifier` 実測 → `reviewer` = **完了可**。
  - **新規 `config_service/orphan_scan.py`**（161 行）: `scan_orphans(service, *, config_root,
    scan_dirs, startup_keymap_set_path, current_keymap_set_path, protected_paths)` が
    `OrphanScanResult`（`entries: tuple[OrphanEntry(kind, stored_path, state)]` /
    `unreadable_sources` / `non_keymap_set_sources` / `missing_scan_dirs`）を返す。
  - **判定名 4 種**（`ORPHAN_CANDIDATE` / `REFERENCED` / `PROTECTED` / `EXCLUDED`）。
    **判定順は 保護 → 参照 → 形状検証 → 候補**（本タスクで定めた規約）で、
    **形状検証の読み取りは 3 番目に到達したファイルだけ**に行う（遅延読込）。
  - **参照側 4 経路**（既定 `user/keymap_sets/` 直下 / 起動エントリ / 現在のセット / `scan_dirs`）を
    **非再帰・symlink 除外・`.json` のみ**で列挙し、`reference_scan.collect_reference_paths` へ委譲。
    **`config.json` のグローバルプリセット**は `split_loading.load_global_hotkey_presets_path` 経由で追加。
  - **候補側 = 既定 4 ディレクトリ直下のみ**（keymaps / trigger_sets / sequences / hotkey_presets）。
    形状検証の必須キーは `mappings`(dict) / `triggers`(list) / `actions`(list) / `hotkey_presets`(list)。
    `user/hotkey_presets/global/` と `quarantine/` は**構造的に交差しない**ため除外判定を書いていない。
  - **副作用ゼロ**（`os.makedirs` / `ensure_split_config_dirs` を呼ばず、無いディレクトリは 0 件で続行）。
    `canonical_path` の戻り値は `stored_path` / `missing_scan_dirs` へ混入させない。
  - `ConfigService` への追加は **import 行 + 1 行委譲の 2 箇所のみ**（+19 / -1 行）。
result_files:
  - keyseq/application/config_service/orphan_scan.py（新規・161 行）
  - keyseq/application/config_service/__init__.py（import + 委譲の 2 箇所）
  - tests/test_orphan_scan.py（新規・16 件）
  - instructions/phase/11_orphan_child_file_sweep/tasks/task_02_orphan_scan.md（新規）
verified:
  compile: clean
  tests: pass **295**（279 → **+16**）
  tests_ui: pass **238**（維持）
  smoke: pass
  note: 実測は `verifier`。**`user/` の誤生成なし**。差分は 3 ファイル + タスク定義のみ。
  review: `reviewer` = **完了可**（5 観点 OK）。非 blocking の申し送り 2 件は next_action へ。

## next_action
- **task_03（検出フローの入口と表示）を起票して着手する**（`/task_new` →
  `tasks/task_03_*.md` → `codex-implementer` → `verifier` → `reviewer`）。
  範囲 = 表示文言の純関数 + `config_io` の新規 IO + 設定メニュー「孤児ファイルの棚卸し…」+
  未保存時の**「保存する / 中止する」2 択**（**`confirm_save_if_dirty` は使わない**＝意味が逆）+
  **受け入れ条件 17 の警告文生成と一覧先頭への配置** + **保護対象の収集**（presentation 側が集めて渡す）。
  **ここまでで「検出のみ」が green になる**（暫定仕様 §4-F の段取り）。
- **task_02 の reviewer 申し送り 2 件（いずれも非 blocking・task_03 で確認）**:
  ① **`missing_scan_dirs` の表記が不揃い**（`orphan_scan.py:77`）。`scan_dirs` は入力表記のままだが、
  既定の `user/keymap_sets/` が無い場合だけ**絶対パス**で入る。一覧表示時に見た目が変わり得る。
  ② `_scan_source_directory` と `_list_json_files` でパス解決 + `isdir` が軽微に重複（実害なし）。
- **task_01 の申し送り①は task_02 でも未担保**: **`config_root` に空文字を渡さない**
  （`resolve_config_path` は空だと **cwd 基準**になる）。**呼び出し側 = task_03 の IO で担保する**。
- **phase 10 task_05 の `deep-reviewer` 指摘 5 件は候補送りのまま**（H8 / H10 / H11 / H13 / H14）。
  **phase 11 では新規コードで同じ形を作らない**にとどめる（暫定仕様 §6）。

## blockers
- なし。

## resume_hints
- **【phase 11 の規範は暫定仕様 10（未凍結・v0.4）】** `instructions/history/10_orphan_child_file_sweep.md`。
  フェーズ中は正本 `spec_detail/` を直接改訂しない（昇格は task_08）。要点だけ再掲 =
  ①**走査（参照側）に「現在開いているセット」`app.keymap_set_path` を必ず含める**
  （`load_keymap_set_from` は `config.json` を書かないため起動エントリでは代替できない）
  ②**参照集合は 2 段辿り**（sequence のパスは keymap_set に無く **trigger_set の `triggers[].sequence_path`** のみ）
  ③**隔離ルートは `<config_root>/quarantine/`**（`user/` の外＝候補側と交差させない）
  ④**マニフェストは移動より先に原子書込み**（後追いだと中断時に復元不能な隔離物が残る）
  ⑤**削除 API はパスでなく実行単位 ID を受け取り 4 検証**
  （**`is_path_within` は同一パスも配下と判定する**〔`__init__.py:686`〕ため隔離ルート自身を消し得る）
  ⑥**削除は通常のファイル削除**（ゴミ箱へ送らない・新規依存を足さない）。**本アプリ初の削除機能**。
- **【壊れた親 = 無傷の子が消えるリスク】** 読めない keymap_set があると、その子が参照集合から抜けて
  **無傷でも孤児候補になる**。ユーザー確定により**警告のみで隔離・削除とも許す**（degraded は不採用）。
  残存リスクは暫定仕様 §3-12-5。**壊れているのは親、消えるのは子**という取り違えに注意。
- **python は必ずリポジトリルートの `.venv` を使う**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
  グローバル `py` は依存欠落で tests_ui/smoke が落ちる。
- **【計画07 で変わった構造】`dialogs` は単一ファイルではなく*パッケージ***
  （`keyseq/presentation/dialogs/`・**1 クラス 1 ファイル**）。**`__init__.py` は明示列挙の再輸出のみ**で
  **`tk` / `messagebox` を持たない**（patch 先の偽装を置かない方針）。
  クラス間参照は**サブモジュール直指定**・`App` の型 import は**各ファイルの `TYPE_CHECKING` ガード内**
  （どちらも崩すと `ImportError` / 循環）。
- **【テストの書き方】モジュール名前空間を patch する形（`patch("keyseq.presentation.dialogs.messagebox...")`）は
  分割の障害になる**（計画07 で 6 箇所を書き換えた）。**新規テストは `patch.object` を優先する**。
- **【罠】パッケージ化・モジュール移動の実測では `__pycache__` の stale な `.pyc` を疑う**
  （旧モジュールが生存し得る。削除して結果不変を確認する）。
- **【phase 10 の成果は正本が正】** `spec_detail/data_schema.md` **§5.8.1**（参照元記録 +
  **参照元の掃除**）+ `features.md` §4.6 + `codebase_map.md`。**暫定仕様 09 は凍結済**
  （経緯の参照用。**条項を実装の根拠に引かない**）。要点だけ再掲 = ①**列挙は runtime の
  source_path 3 種**（**`resolve_child_save_targets` を使ってはならない**＝未実体化の子へ既定パスが
  割り当てられ**無関係な既存ファイルを書き換える**）②**保護対象**（現在の keymap_set / trigger_set への参照）は
  **実在しなくても除去しない**が、**別枠で「保護のため残す」と提示はする**
  ③**除去直前に JSON 全体を読み直して再判定**（検査時のスナップショットを書き戻さない）。
  判断履歴は `decisions_archive/10_reference_link_cleanup.md`。
- **【運用・重要】委任の実行中はメイン側で文書を編集しない**。
  phase 10 task_05 で、Codex が**メインの仕様書編集を「範囲外の差分」と判断して巻き戻した**
  （v0.5 の記述が消えた）。編集してしまった場合は**委任完了後に必ず差分を確認する**。
- **【メニュー項目のテスト】インデックスを固定しない**。top-level menubar には **tearoff** があり
  `0=tearoff / 1=ファイル / 2=設定` とずれる。**カスケードとラベルで探す**こと（task_04 で 1 度踏んだ）。
- **【個別プリセット（phase 09 の成果）は正本が正】** `spec_detail/data_schema.md` **§5.10**
  （全体ライブラリと個別指定）+ **§5.8.8**（入口台帳。**E5 = 強制 OFF / P1 = 表示用の再読込**）+
  §5.5 / §5.4 / §5.1 + `codebase_map.md`。**暫定仕様 08 は凍結済**（経緯の参照用。**条項を実装の根拠に引かない**）。
  要点だけ再掲 = ①**フラグキーが無ければ残置 `hotkey_presets_path` も落とす**（フラグ自体は**値**、
  残置パスの遮断は**キーの有無**で判定。false + キーありはパス保持）②**トグルで一覧を読み直す**・
  **OFF の OK もグローバルへ書く**（読めなければ**組込既定**へ差し替わるので個別の内容は流出しない）・
  **OFF で開いた時点も表示元へ確定**（ON は対象外）③**読み出しは config 外も可 / 書き込みは管理下へ寄せる**
  （非対称は意図どおり）④書き込み前は**寄せ → 拒否 → 上書き確認**の順。上書き確認は
  **保存先の実体 vs ダイアログが読み込んだ一覧**の**内容比較**（出どころパスの比較にしない）で、
  **3 択**（上書きする / 既存を読み込む / キャンセル。**破損時は 2 択**）。
  **adopt は一覧と比較基準を差し替えるだけで保存も close もしない**。
- **【idea_11・既知の制約】別名保存で個別プリセットの複製に成功した後、keymap_set の保存が失敗すると
  巻き戻らない**（孤児の複製 + メモリ上だけ新パス・dirty も立たない）。**正本 §5.10.4 に明記済**。
  再編集しても**内容が一致するため上書き確認は出ない**点が要注意（優先度低で後送り）。
- **【ネストしたモーダルの grab は既知の課題】** モーダル中のモーダルを閉じると**親の grab が戻らず**、
  マネージャを開いたままメインを操作できる（**既存の「追加」「編集」も同じ**）。
  **idea_10 として分離済**。新しいダイアログにも**復元処理を書かない**（挙動を揃えるため）。
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
  γ=phase07/暫定06〔完了〕 / プリセット=phase08/暫定07〔完了・decisions_archive 08〕 /
  個別プリセット=phase09/暫定08〔完了・decisions_archive 09〕 /
  **参照元の掃除=phase10/暫定09〔完了・decisions_archive 10〕**。
  **計画05・計画06 はフェーズ番号を消費していない**（規範 = `modified_proposal/05_*.md` / `06_*.md`）。
- **【計画05 で変わった構造】`config_service` は単一ファイルではなく*パッケージ***
  （`keyseq/application/config_service/`）。**ConfigService 本体は `__init__.py`**
  （テストが `patch("keyseq.application.config_service.os.path", ntpath)` で名前空間を差し替えるため、
  この配置を崩すと 4 テストが壊れる。同じ理由で**パス基盤メソッドを兄弟へ移さない**）。
  兄弟 = `save_plan_execution.py` / `split_payloads.py` / `save_path_resolution.py` / `split_loading.py`。
  抽出関数は **`service` を第 1 引数に取る**。兄弟から `__init__` を import しない（循環回避）。
- config_io は `controllers/config_io/` へ分割済（App が `app.keymap_set_io` 等で直接公開）。
- 未着手 idea: **idea_13（external_keyboard_layouts のパス基準の非対称・優先度低）** / idea_10（ネストした
  モーダルの grab 復元）/ idea_03（hotkey 保存時正規化・優先度低）/ idea_09（レガシー settings/
  フォールバック・優先度低）。**idea_12 は phase 11 で着手**・**idea_07 は phase 10 で完了**・**idea_08 は phase 09 で完了**。
  保留 idea: idea_04 / idea_06（**残る着手条件は「共通化の実需」1 つのみ**）。
- 過去の判断は `.claude_data/state/decisions.md`（アーカイブ索引）+ `decisions_archive/<phase>.md`。
  完了済の直近 3 件: 08_hotkey_presets_global / 09_per_keymap_set_presets /
  **10_reference_link_cleanup**。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
