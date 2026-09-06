# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-09-06T22:00:00
phase: **11_orphan_child_file_sweep（孤児ファイルの棚卸し）= task_01〜task_06 + task_05b 完了 / task_06b 未着手**。番号対応: phase 11 / 暫定 10 / decisions_archive 11。次採番は `instructions/phase/12_<topic>`
last_commit_location: claude/task-02-progression-2fd81c @ 最新コミット = `task_06: 隔離の管理（一覧 + 復元）を新設` ※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 11 task_06（隔離の管理 = 一覧 + 復元）完了**（verifier 実測 green / reviewer = 完了可）。次は **task_06b（隔離済みの削除）= このフェーズ唯一の不可逆操作**。
mode: in_progress

## last_action
ts: 2026-09-06T22:00:00
who: main
summary: |
  【**phase 11 task_06 完了**】隔離した実行単位の**一覧と復元**を新設。
  **task_06 を「一覧 + 復元」と「削除（task_06b）」へ分割**した（メイン判断）。理由 =
  **削除はこのフェーズ唯一の不可逆操作**であり、**復元を先に green にしてから**載せれば
  誤っても戻せる経路が検証済みの状態で進められる（§4-F の段取りに倣う）。
  実装は `codex-implementer` → `verifier` 実測 → `reviewer` = **完了可**。
  - **新規 `config_service/quarantine_manage.py`**（219 行）:
    `list_quarantine_units(service, *, config_root)` → `QuarantineUnit`（`unit_id` / `created_at` /
    `entry_count` / **`remaining_count`〔実体ベース〕** / `manifest_valid`）/
    `restore_quarantine_unit(service, unit_id, *, config_root)` → `QuarantineRestoreResult`。
  - **【最重要】復元は `state` を信用せず `quarantined_path` の実体の有無で判定**
    （task_05 の H-1 を吸収する確定判断。`test_planned_and_failed_states_do_not_prevent_restore` で担保）。
  - **`original_path` のガード**: 候補側 4 ディレクトリ配下であることに加え、
    **canonical 一致除外で「ディレクトリそのもの」を弾く**（`is_path_within` が同一パスも
    配下と判定する穴を塞いだ）。**`user/hotkey_presets/global/` も拒否**。
  - **`unit_id` は正規表現 + 隔離ルート直下の実在のみで検証**し、不正値では
    **`_load_optional_json` すら呼ばない**（テストで未呼び出しまで確認）。
  - 同名は `os.path.lexists` でスキップ（**上書きしない**）/ 復元先ディレクトリは作成 /
    部分失敗は継続 / **全件戻ったら manifest と空ディレクトリを削除**（マニフェスト外の
    未知ファイルが残っていれば実行単位を残す堅い実装）/ **マニフェストを書き換えない**（冪等）。
  - presentation: `quarantine_manage_text.py`（純関数 3）/ `dialogs/quarantine_manage_dialog.py`
    （実行単位のリスト選択）/ `config_io/quarantine_manage_io.py` / メニュー「隔離の管理…」。
    確認は **task_05 で引数化済みの `ReferenceCleanupDialog`**（`run_label="復元する"`）を**使うだけ**。
  - `quarantine.py` の変更は **`_quarantine_root` → `quarantine_root` の公開化 +
    `UNIT_ID_PATTERN` の追加のみ**（隔離ロジックは不変）。
result_files:
  - keyseq/application/config_service/quarantine_manage.py（新規・219 行）
  - keyseq/application/config_service/quarantine.py（公開名 + 定数のみ）/ __init__.py（委譲 2 つ）
  - keyseq/presentation/quarantine_manage_text.py（新規）/ dialogs/quarantine_manage_dialog.py（新規）/
    controllers/config_io/quarantine_manage_io.py（新規）/ dialogs/__init__.py / app.py / views/menu_bar.py
  - tests/test_quarantine_manage.py（18 件）/ tests/test_quarantine_manage_text.py（5 件）/
    tests_ui/test_quarantine_manage_flow.py（11 件）
  - instructions/phase/11_orphan_child_file_sweep/tasks/task_06_quarantine_restore.md（新規）/
    phase.md（task_06 の分割を反映）
verified:
  compile: clean
  tests: pass **377**（354 → **+23**・skip 2）
  tests_ui: pass **279**（268 → **+11**）
  smoke: pass
  note: 実測は `verifier`。skip 2 件は**シンボリックリンク作成の特権不足**（`WinError 1314`）で環境依存。
    実行前後で **`user/` も `quarantine/` も未生成・git 差分の増加なし**。
    退行確認 4 ファイル（test_quarantine 24 / test_orphan_sweep_flow 30 /
    test_reference_cleanup_flow 9 / test_orphan_scan 31）は**無変更で全 pass**。
  review: `reviewer` = **完了可**（5 観点 OK）。**削除の先取りは grep 0 件**で確認。
    非ブロッカー指摘 1 件（下記）。

## next_action
- **task_06b（隔離済みの削除）を起票して着手する**。**このフェーズ唯一の不可逆操作**。
  **`reviewer` に加えて Codex の敵対的レビューを通す**（ユーザー判断 2026-09-06。
  毎タスクではなく**重要なタスクに限る**方針）。
  範囲 = **削除 API は実行単位 ID のみを受け取り 4 検証**
  〔①隔離ルート**直下**に実在するディレクトリ ②名前が実行単位の形式（`_2` / `_3` は
  **ゼロ埋めなし・上限なし**）③**canonical が隔離ルート自身と一致しない**
  ④**有効な `manifest.json` を持つ**〕+ **実行単位ディレクトリの再帰削除**（`manifest.json` も一緒に）+
  **OS のゴミ箱へ送らない通常削除** + **シンボリックリンクは辿らずリンク自体を削除** +
  **削除前に対象パスを全件提示し、不可逆である旨を確認画面に明記** + 部分失敗の継続 +
  管理ダイアログへの削除ボタン追加（`run_label="削除する"`）。
  - **実測済みの前提**: **Python 3.14 の `shutil.rmtree` はジャンクションを辿らない**
    （外部のファイルが残ることを確認）。**この挙動をテストで固定する**こと。
  - **`is_path_within` は同一パスも配下と判定する**（`__init__.py:732-733`）ため、
    **それだけでは隔離ルート自身の再帰削除を防げない**（検証③が要る理由）。
  - **マニフェスト不正な実行単位は削除もできない**（§3-8 検証④）。その結果
    **「復元も削除もできない残骸」**が残り得る点をどう扱うか、起票時に整理する
    （task_05b で `.tmp` の発生源は塞いだが、既存の残骸はあり得る）。
- **【task_06 の reviewer 指摘・task_06b で対応】**
  `quarantine_manage.py:54,89,139` が `quarantine.py` の **private 関数 `_is_real_path_within` を
  兄弟モジュールから直接呼んでいる**。本コードベースの兄弟間共有は public 名を経由する慣習。
  **task_06b でも削除の境界検証に同じ関数が要る**ので、そこで
  **`quarantine.is_real_path_within` として公開**し、呼び出し 3 箇所を追随させる。
- **task_08（正本反映）で判断が要る「仕様書側で再検討推奨」3 件**:
  ①§3-6 に「移動中の進捗書込み失敗時の扱い」が無い ②§3-6 に「実行単位ディレクトリ作成失敗」の
  規定が無い ③**§3-11「presentation から config_service の内部モジュールを直参照しない」と
  実装（定数 import）が矛盾**。加えて**マニフェストの `state` キーは §3-6 の例に無い**
  （`planned` / `moved` / `failed` の意味と「完了後も `planned` が残り得る」旨を明記する）。
- **残課題（非 blocking・未対応）**: ①`quarantine.py:305` の `os.makedirs` がガードより前にあり、
  移動が拒否されても**隔離先の空ディレクトリ構造が作られ得る** ②`dropped_paths` が stored 表記へ
  未正規化 ③例外内容（errno / メッセージ）が理由コードへ落ちて失われる
  ④task_02 の `missing_scan_dirs` の表記不揃い。
- **task_07 の実機目視に必ず含める観点**: 「隔離実行後の `quarantine/<unit>/` の中身と
  `manifest.json` の `state`」「**`quarantine` を書込み不可にした状態での中止表示**」
  「走査ディレクトリの追加 / 削除と再起動後の保持」「**隔離 → 復元の往復で元に戻ること**」。
- **phase 10 task_05 の `deep-reviewer` 指摘 5 件は候補送りのまま**（H8 / H10 / H11 / H13 / H14）。

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
