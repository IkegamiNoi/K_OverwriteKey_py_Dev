# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-09-10T00:30:00
phase: **進行中のフェーズなし**。phase 13 と計画10 は 2026-09-08 完了。**次フェーズは未確定**
（次採番 `instructions/phase/14_<topic>`）。今セッションは template からの逆同期 + スキル化で、
**フェーズ番号を消費しない運用インフラ作業**（アプリ本体・テストへのコード差分 0 行）
last_commit_location: `claude/folder-commit-import-2e88db` @ `1c40182`
（今セッションの 8 コミット `2466c3d`..`1c40182`。**main へは未マージ**）。
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **template（`D:/Claude/doc/00_claude_template`）からの逆同期を完了し、手順を `/template_pull` としてスキル化。進行中のフェーズなし・次フェーズ未確定**。
mode: completed

## last_action
ts: 2026-09-10T00:30:00
who: main
summary: |
  【**template からの逆同期 + スキル化**】生成元 template リポジトリ
  （`D:/Claude/doc/00_claude_template`・追加ワーキングディレクトリ）の 3 コミット
  `aa2f827` / `15e2514` / `7791fa7` を取り込み、手順を `/template_pull` として固定した。
  順方向の `/template_sync` は template 側にあるが**逆同期は責務外**と明記されているため、
  手順（候補抽出 → 分類 → 確認ゲート → 適合化）だけ借りて手作業で実施した。
  - **取込 3 件**: ①モード切替機構を `instructions/{agent_mode,save_mode}/` → **`.claude_data/modes/`**
    へ移動（17 ファイル rename + 旧パス参照 8 箇所 + `ROOT_DIR` を `parents[1]` → `[2]`）
    ②**`codex_medium` モード追加**（Codex を実装・レビューに絞り調査は `Explore`。
    `agent_selection.md` は template の汎用版ではなく**こちらの `codex` 変種をベースに 3 箇所差替**）
    ③`.gitignore` にモード backup 2 行（**部分取込**）。
  - **`deep-reviewer` の指摘を反映**（2 回実施）: 3 モード化に伴う表記統一 / `codex_medium` の
    理由文の差替 / `.gitignore` へ `settings.local.json`・`.claude/worktrees/` を追加
    （**グローバル設定と `.git/info/exclude` 由来で追跡ファイルには無かった**＝別マシンで無効）/
    モード管理外の 3 文書から `codex-explorer` の直名を除去 /
    **`save_mode` 登録 5 種へ SessionStart の git 実測ヘッダを書き戻し**（`check` の警告が解消）。
  - **新設 2 件**: `.claude_data/modes/README.md`（モード管理の限界と参照側の書き方）/
    `/template_pull` + `.claude/template_pull_state.md`（逆同期の手順とマーカー）。
result_files:
  - .claude_data/modes/**（`instructions/` から移動 + `codex_medium` 変種 + `README.md`）
  - .claude/commands/template_pull.md / .claude/template_pull_state.md（新規）
  - CLAUDE.md / .claude/rules/{agent_selection,output_style,task_execution}.md / .claude/commands/task_commit.md
  - .gitignore
verified:
  compile: clean（`.claude_data/modes` の compileall）
  tests: not_run（**アプリ本体・テストへのコード差分 0 行**のため）
  tests_ui: not_run（同上）
  smoke: not_run（同上）
  note: agent_mode の `check` = **[1] Codex併用（既定）一致** / save_mode の `check` =
    **[4] 自動保存・タスクファイルの読み込み指示 一致**（従来の「どれにも一致しません」警告が解消）/
    `git check-ignore -v` で追跡 `.gitignore` が根拠になることを確認 / **旧パス参照の残存 0**
  review: **`deep-reviewer` × 2**（①取込差分 = 修正要 → 反映済 ②`/template_pull` = 修正要 → 反映済）

## next_action
- **【最優先】次フェーズが未確定**（前セッションから継続）。ユーザーへ方針確認し、決まったら
  `/phase_start` で `instructions/phase/14_<topic>/` を起票する。候補は `instructions/backlog/INDEX.md`:
  idea_10（ネストしたモーダルの grab 復元）/ idea_13 / idea_09 / idea_03 / idea_11 / idea_04・idea_06（保留）。
- **今回の未処理 3 件**（`.claude/template_pull_state.md` の履歴メモにも記録済）:
  ①`.claude_data/state/decisions.md` へ今回の判断履歴を記録（未実施）
  ②`codex_medium` を実運用へ入れる前に `Explore` を 1 度起動して可用性を確認
  ③`.claude/rules/output_style.md:41-42` の `claude_only` モードで食い違う記述
  （`codex-implementer` 等の直名。**今回起因ではない既存のズレ**）。
- **境界検査の残件**（着手するなら新規 idea 起票）: 検査に残る限界 4 つ（動的 import /
  実行時に組み立てた名前 / 代入による再束縛 / 縮退時の未解決）と、**素の名前検査の潜在的誤検出**
  （`ConfigService` に内部モジュールと同名の公開メンバが増えると落ちる）。
- **残課題（非 blocking・未対応）**: ①`dropped_paths` が stored 表記へ未正規化
  ②例外内容が理由コードへ落ちて失われる。
- **phase 10 task_05 の `deep-reviewer` 指摘 5 件は候補送りのまま**（H8 / H10 / H11 / H13 / H14）。
- **phase 12 の完了レビューの保留分**（実害なし）: L-1 / L-4 / L-8。

## blockers
- **なし**（取込・スキル化とも green。アプリ本体は無変更）。

## resume_hints
- **【今セッションの運用インフラ変更・重要】モード切替は `.claude_data/modes/`**
  （`instructions/agent_mode` ・ `instructions/save_mode` から移動。旧パスは存在しない）。
  **`.claude/` 配下または `CLAUDE.md` を編集する前に `.claude_data/modes/README.md` を読む**
  （管理対象パス一覧 / **`check` は非稼働モードのズレを検知しない** / 参照側はどのモードでも
  真になるように書く）。エージェント構成は **3 モード**（`codex` / **`codex_medium`** / `claude_only`）で、
  現構成は `[1] codex`。template からの取り込みは **`/template_pull`**
  （マーカー = `.claude/template_pull_state.md`。`last_pulled = 7791fa7`。
  **template と意図的に差分にした箇所・ファイルの対応関係もここが正**）。
- **【phase 13 + 計画10 の成果】公開面の逆戻り防止テスト = `tests/test_config_service_contracts.py` の 3 メソッド**。
  **検査関数は計画10 で経路ごとに分割済**（`_build_alias_map` / `_check_import_node` /
  `_check_attribute` + 本体 26 行）。**禁止 13 例は期待メッセージを `assertEqual` で固定**して
  あるので、**触ると出力の差がそのまま落ちる**（分割時はこれが挙動保存の担保になった）。
  検査は **R1〜R4 + 属性アクセス 3 形**（素の名前 / 完全修飾 / エイリアス〔絶対・相対とも〕）。
  **相対 import は `_resolve_relative_module` で絶対名へ解決**し、**解決不能時は `config_service`
  セグメント以降の末尾一致へ縮退**する（**素通しにしない**）。エイリアス表は **名前 → 束縛先の集合**で、
  **いずれかが内部モジュールへ解決されたら違反**（スコープ解析はしない）。
  **素の名前検査（`config_service.<内部>`）は残す**（相対 import でモジュールを束縛した場合の唯一の検出経路）。
  **`INTERNAL_MODULE_NAMES` はパッケージの実ファイル一覧と一致必須**（モジュールを増やしたら更新する）。
  **残る限界 4 つ**: 動的 import / 実行時に組み立てた名前 / **代入による再束縛** / 縮退時の未解決。
  **残存リスク**: `ConfigService` に内部モジュールと同名の公開メンバが増えると**誤検出で落ちる**。
  判断は `decisions_archive/13_contracts_boundary_ast_coverage.md`。
- **【phase 12 の成果は正本が正】** `spec_detail/architecture.md` **§3.2**（公開面 = `ConfigService` の
  公開 API + `config_service/contracts.py` / `contracts` は葉）+ `codebase_map.md`（パッケージ表 **13 ファイル**）。
  **暫定仕様 11 は凍結済**（v0.3・経緯の参照用。**条項を実装の根拠に引かない**）。要点だけ再掲 =
  ①**公開面 = `config_service/contracts.py`**（**判定名・理由コード・結果型の唯一の定義**。定数 34 / 型 9。
  `config_service` 内の他モジュールを import しない葉）②**参照は `from . import contracts` + `contracts.NAME`**
  （`from .contracts import NAME` は**不可**。名前が再束縛されて `hasattr` 偽の固定テストが書けない）
  ③**内部表現（`QUARANTINE_DIR_NAME` / `UNIT_ID_PATTERN` / `ENTRY_*` / `CANDIDATE_DIRS`）は実装側に残す**
  ④**値の重複（`"invalid_unit_id"` / `"no_manifest"`）を統合しない**（ラベル分岐が壊れる）
  ⑤**逆戻り防止テスト = `tests/test_config_service_contracts.py` の 3 本**（共有参照の固定 /
  presentation の AST 走査 R1〜R3 + 属性アクセス / 検査関数の自己検証）。
  **`INTERNAL_MODULE_NAMES` はパッケージの実ファイル一覧と一致必須**（モジュールを増やしたら更新する。
  更新しないと属性アクセス経路だけ素通りする）
  ⑥（**phase 13 で解消済**）AST 検査に残っていた静的経路の穴 3 つ（完全修飾のドット参照 / エイリアス束縛 /
  `from keyseq import application` 経由）。**現在の presentation に該当参照は 0 件**で、
  強化は **idea_15** へ分離済（判断は `decisions_archive/12`）。
- **【計画09 の成果】正本 `data_schema.md` は **INDEX**（260 行）。**§5.8 と §5.10 の実体は
  `spec_detail/data_schema/` 配下の 13 子ファイル**。**節番号・見出しは不変**なので
  「`data_schema.md` §5.8.9」形式の既存参照はそのまま通じる。**更新は子ファイル側で行う**。
- **【計画08 の成果】候補側ディレクトリの定義は `config_service/candidate_dirs.py` の
  `CANDIDATE_DIRS` / `RESERVED_DIR` が唯一**（`orphan_scan` の候補範囲と `quarantine_manage` の
  復元先ガードが同じ定義を見る）。**再定義しない・添字で結び付けない**（`zip(strict=True)` を使う）。
- **【phase 11 の成果は正本が正】** `spec_detail/data_schema.md` **§5.8.9**（+ §5.8.1 改訂 / §5.4 / §5.10.1）
  + `features.md` §4.6 + `architecture.md` §3.2 + `codebase_map.md`。
  **暫定仕様 10 は凍結済**（v0.8・経緯の参照用。**条項を実装の根拠に引かない**）。要点だけ再掲 =
  ①**走査（参照側）に「現在開いているセット」`app.keymap_set_path` を必ず含める**
  （`load_keymap_set_from` は `config.json` を書かないため起動エントリでは代替できない）
  ②**参照集合は 2 段辿り**（sequence のパスは keymap_set に無く **trigger_set の `triggers[].sequence_path`** のみ）
  ③**隔離ルートは `<config_root>/quarantine/`**（`user/` の外＝候補側と交差させない）
  ④**マニフェストは移動より先に原子書込み**（後追いだと中断時に復元不能な隔離物が残る）
  ⑤**削除 API はパスでなく実行単位 ID を受け取り 4 検証**
  （**`is_path_within` は同一パスも配下と判定する**〔`__init__.py:686`〕ため隔離ルート自身を消し得る）
  ⑥**削除は通常のファイル削除**（ゴミ箱へ送らない・新規依存を足さない）。**本アプリ初の削除機能**。
  ⑦**検証④のみ `allow_invalid_manifest=True` で上書き可**（v0.5）。**①②③は緩和しない**。
  ⑧**削除の TOCTOU 2 件は受容済**（§3-12-6 / §3-12-7・v0.6）。**蒸し返さない**。
  ⑨**境界判定 `is_real_path_within` の唯一の定義は `config_service/path_boundary.py`**
  （task_07b で統合。**`quarantine.py` / `orphan_scan.py` に再定義しない**。
  `quarantine.py` は `orphan_scan` を import しているので**逆向きの import は循環になる**）。
  ⑩**「マニフェスト不正」= ①JSON 解析不能 ②トップレベルが object でない ③`entries` が配列でない
  ④`manifest.json` 自体がリンク、の 4 つ**（正本 §5.8.9）。**エントリ単位の妥当性は検査しない**ため
  `{"entries": [{}]}` は「有効」扱い（制約 8）。**ユーザー確定済（2026-09-08）なので蒸し返さない**。
  ⑪**外部レイアウトの参照解決は `config_root` 基準と `dirname(config_root)` 基準の superset**
  （**「keymap_set 基準」ではない**。task_08 の Codex レビューで訂正した誤りなので繰り返さない）。
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
  フォールバック・優先度低）。**idea_15 は phase 13 で完了**・**idea_14 は phase 12 で完了**・**idea_12 は phase 11 で完了**・
  **idea_07 は phase 10 で完了**・**idea_08 は phase 09 で完了**。
  保留 idea: idea_04 / idea_06（**残る着手条件は「共通化の実需」1 つのみ**）。
- 過去の判断は `.claude_data/state/decisions.md`（アーカイブ索引）+ `decisions_archive/<phase>.md`。
  完了済の直近 3 件: 11_orphan_child_file_sweep / 12_config_service_public_surface /
  **13_contracts_boundary_ast_coverage**。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
