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
2. `instructions/phase/current.md` を読む（**アクティブなフェーズなし = 次フェーズ未確定**。
   冒頭の「**直近の一連の作業が扱っている領域**」で、いま何の続きを見ているのかを掴む）
3. 次フェーズの方針をユーザーへ確認し、決まったら `/phase_start` で
   `instructions/phase/14_<topic>/` を起票する。
   **凍結済の暫定仕様（`instructions/history/`）の条項を実装の根拠に引かない**
4. CLAUDE.md → `.claude/rules/` の順に必要分を読む。
   **`.claude/` 配下または `CLAUDE.md` を編集するなら、先に `.claude_data/modes/README.md` を読む**
   （モード切替で入れ替わるファイルがあり、参照する側の書き方に制約がある）
5. 過去の判断は `.claude_data/state/decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`

## 現在の作業の 1 行サマリ
**template（`D:/Claude/doc/00_claude_template`）からの逆同期を完了し、手順を `/template_pull` としてスキル化。
進行中のフェーズなし・次フェーズ未確定**（2026-09-10）。**未決の判断は残っていない**。
**次にやること = 次フェーズの方針をユーザーへ確認し `/phase_start` で `14_<topic>` を起票する**。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近の実測（**計画10 完了時点 = 2026-09-08**）:
compile **clean** / tests **417**（skip 7）/ tests_ui **288**（skip 0）/ smoke **pass**。
**その後のセッションはアプリ本体・テストへのコード差分 0 行**（運用インフラのみ）なので、この値が現在値。
**件数が減ったら退行を疑う**。skip 7 件は**シンボリックリンク作成の特権不足**（`WinError 1314`）で環境依存。
**同じ観点はジャンクション版のテストが実行されている**ので観点の抜けにはならない。
実行後に worktree ルートへ **`user/` も `quarantine/` も生成されていない**ことを確認する。

モード切替を触った場合の追加確認（`.claude_data/modes/README.md` の変更手順 4）:
```bash
printf 'c\nq\n' | ../../../.venv/Scripts/python.exe .claude_data/modes/agent_mode/switch_agent_mode.py
printf 'c\nq\n' | ../../../.venv/Scripts/python.exe .claude_data/modes/save_mode/switch_save_mode.py
```
現在は agent_mode = **[1] Codex併用（既定）** / save_mode = **[4] 自動保存・タスクファイルの読み込み指示** で一致。

## 次アクション（session.md.next_action より）
- **【最優先】次フェーズが未確定**。ユーザーへ方針確認し、決まったら `/phase_start` で
  `instructions/phase/14_<topic>/` を起票する。候補は `instructions/backlog/INDEX.md`
  （idea_10 / idea_13 / idea_09 / idea_03 / idea_11 / 保留の idea_04・idea_06）。
- **今回の未処理 3 件**（`.claude/template_pull_state.md` の履歴メモにも記録済）:
  ①`decisions.md` へ今回の判断履歴を記録（未実施）②`codex_medium` を実運用へ入れる前に
  `Explore` を 1 度起動して可用性を確認 ③`.claude/rules/output_style.md:41-42` の
  `claude_only` モードで食い違う記述（**今回起因ではない既存のズレ**）。
- **境界検査の残件**（着手するなら新規 idea 起票）: 残る限界 4 つ（動的 import /
  実行時に組み立てた名前 / 代入による再束縛 / 縮退時の未解決）と、**素の名前検査の潜在的誤検出**
  （`ConfigService` に内部モジュールと同名の公開メンバが増えると落ちる）。
- **残課題（非 blocking・未対応）**: ①`dropped_paths` が stored 表記へ未正規化
  ②例外内容が理由コードへ落ちて失われる。
- **phase 10 task_05 の `deep-reviewer` 指摘 5 件は候補送りのまま**（H8 / H10 / H11 / H13 / H14）。
- **phase 12 の完了レビューの保留分**（実害なし）: L-1 / L-4 / L-8。

## 直前の作業（template からの逆同期 + スキル化・**完了**）の要点

**フェーズ番号を消費しない運用インフラ作業。アプリ本体・テストへのコード差分 0 行**（8 コミット
`2466c3d`..`1c40182`・ブランチ `claude/folder-commit-import-2e88db`・**main へは未マージ**）。

- **モード切替は `.claude_data/modes/`**（`instructions/agent_mode` ・ `instructions/save_mode` から移動。
  旧パスは存在しない）。`switch_*.py` の `ROOT_DIR` は `SCRIPT_DIR.parents[2]`。
- **エージェント構成は 3 モード**: `codex`（現構成）/ **`codex_medium`**（Codex を実装・レビューに絞り
  調査は `Explore`。`codex-explorer.md` は配置されず**適用時に削除**される）/ `claude_only`。
- **`.claude/` 配下または `CLAUDE.md` を編集する前に `.claude_data/modes/README.md` を読む。**
  要点 = ①管理対象を編集したら**全変種へ追随**させる ②**`check` は稼働中の `.claude/` と指定モードの
  1 組しか比較せず、非稼働モードのズレを検知できない**（切り替えた瞬間に改訂が巻き戻る）
  ③参照する側（`CLAUDE.md` / 他の `.claude/rules/`）はモード管理外なので、**具体エージェント名や
  モード列挙を書かず `agent_selection.md` の既定へ委ねる**。中立に書けない時だけモード管理へ昇格。
- **template からの取り込みは `/template_pull`**（`.claude/commands/template_pull.md`）。
  マーカー = `.claude/template_pull_state.md`（`last_pulled = 7791fa7`。
  **ファイルの対応関係・除外メモ・template と意図的に差分にした箇所はここが正**）。
  逆方向（プロジェクト → template）は template 側の `/template_sync` の責務。
- **`.gitignore` は追跡ファイルだけを根拠にしない**。`settings.local.json` と
  `.claude/worktrees/` はグローバル設定と `.git/info/exclude` 由来で追跡側に無かった
  （別マシンで無効。今回追加済）。確認は `git check-ignore -v`。
  取り込み時の git の罠（pathspec 併用で `-M` が効かない等）は `/template_pull` の手順 2a が正。

## 直前フェーズ（phase 13 = 検査範囲の拡張・**完了** / 計画10 = 検査関数の分割・**完了**）の要点

**直接改訂モード（暫定仕様なし）・テストのみ・プロダクション不変・仕様変更なし・実機目視なし**。
**正本改訂なし**（`architecture.md` §3.2 は phase 12 で確定済で不変。**検査精度を上げただけ**）。
判断は `decisions_archive/13_contracts_boundary_ast_coverage.md`。

- **検査 = R1〜R4 + 属性アクセス 3 形**（素の名前 / 完全修飾 / エイリアス〔**絶対・相対とも**〕）。
  **相対 import は `_resolve_relative_module` で絶対名へ解決**（R4 と共有。**重複実装を作らない**）し、
  **解決不能時は `config_service` セグメント以降の末尾一致へ縮退**する（**素通しにしない**）。
- **エイリアス表は 名前 → 束縛先の集合**で、**いずれかが内部モジュールへ解決されたら違反**
  （スコープ解析はしない保守的判定）。
- **素の名前検査（`config_service.<内部モジュール>`）は残す**
  （**相対 import でモジュールを束縛した場合の唯一の検出経路**）。
- **`INTERNAL_MODULE_NAMES` はパッケージの実ファイル一覧と一致必須**（増減したら更新する）。
- **残る限界 4 つ**: 動的 import / 実行時に組み立てた名前 / **代入による再束縛** / 縮退時の未解決。
- **残存リスク**: `ConfigService` に**内部モジュールと同名の公開メンバ**が増えると、
  §3.2 が許可する正当な記述でも**素の名前検査が誤検出して落ちる**。
- `collect_forbidden_refs` は計画10 で **100 行 → 26 行**へ分割済（`_build_alias_map` /
  `_check_import_node` / `_check_attribute`）。**禁止 13 例は期待メッセージを `assertEqual` で固定**
  してあるため、**検査を触ると出力の差がそのまま落ちる**（分割時の挙動保存もこれで担保した）。

## 注意事項・blockers
- **blockers: なし**（取込・スキル化とも green。アプリ本体は無変更。次フェーズ未確定）。
- **【教訓・task_07b】Codex は「記録を足す」指示を「skip を増やす」方向へ広げることがある**。
  1 回目の実装で参照側の skip 条件を `islink` から `realpath != abspath` へ広げ、
  **親ディレクトリがジャンクションなら配下の全 keymap_set が参照集合から落ちる**状態を作り、
  **追加テストでその挙動を固定していた**。**差分は必ずメインが読んで裏取りする**
  （テストが green でも、テストごと誤った挙動を固定していることがある）。
- **【運用・重要】委任の実行中はメイン側で文書を編集しない**。phase 10 task_05 で **Codex がメインの
  仕様書編集を「範囲外の差分」と判断して巻き戻した**。編集した場合は**完了後に必ず差分を確認する**。
- **【メニュー項目のテスト】インデックスを固定しない**。top-level menubar には **tearoff** があり
  `0=tearoff / 1=ファイル / 2=設定` とずれる。**カスケードとラベルで探す**。
- **【テストの書き方】モジュール名前空間を patch する形は分割の障害になる**（計画07 で 6 箇所書き換えた）。
  **新規テストは `patch.object` を優先する**。
- **【罠】モジュール移動・パッケージ化の実測では `__pycache__` の stale な `.pyc` を疑う**
  （旧モジュールが生存し得る。削除して結果不変を確認する）。
- **【dialogs はパッケージ】**（`keyseq/presentation/dialogs/`・**1 クラス 1 ファイル**）。
  **`__init__.py` は明示列挙の再輸出のみ**で **`tk` / `messagebox` を持たない**。
  クラス間参照は**サブモジュール直指定**・`App` の型 import は**各ファイルの `TYPE_CHECKING` ガード内**。
  `PresetManagerDialog` の **`_refresh` / `_update_source_labels` はテストが `patch.object` する契約名**
  （リネーム禁止）。
- **【Codex 運用・最重要】フォワーダが 2 分で切れても Codex ワーカーは生き続ける**（companion status は
  `running` のまま停滞する）。**ハングと即断しない**。判別は**作業ツリーの更新時刻**。
  **書き換え途中で `verifier` / `reviewer` を回すと偽の結果を掴む**。
  ワーカー終了後は state が自己更新されないため `codex_operations.md` §4 で手修復する。
- **【Codex 運用】詰まったジョブに `taskkill /T` を使わない**（PID 再利用で**無関係なプロセスを巻き込む**）。
  フォワーダが最終出力を返さず完了通知だけ来ることがある → `SendMessage` で再開して回収する。
  **Codex 申告のテスト結果は信用せず必ず実測**。**サブエージェントがセッション上限で落ちたら再実行する**。
  **Codex が使用量上限に達したら実装は止める**（レビューは Claude 側へ縮退可・**実装のフォールバックは
  ユーザー許可が必須**）。
- **【config_service の配置制約】`config_service` はパッケージ**で **ConfigService 本体は `__init__.py`**。
  テストが `patch("keyseq.application.config_service.os.path", ntpath)` で名前空間を差し替えるため、
  この配置を崩すと壊れる。同じ理由で**パス基盤メソッドを兄弟モジュールへ移さない**。
  抽出関数は **`service` を第 1 引数に取る**。**兄弟から `__init__` を import しない**（循環回避）。
  **presentation から兄弟モジュールを直接 import しない**（公開面は **`ConfigService` の公開 API と
  `contracts.py` のみ**。**逆戻りはテストが落とす**）。
  同ファイルは **828 行**のため、**新規の実ロジックを置かない**（1 行委譲のみ）。**分割は保留中**。
- **【最重要・2 度踏んだ罠】パス表記の混在事故**: runtime の `source_path` 3 種と
  `hotkey_presets_path` は **config 配下なら相対**で保持される（config 外は絶対・区切りは `/` 正規化）。
  **相対値を `os.path.abspath` / `dirname` / `exists` / `join` へ解決なしで渡すと cwd 基準で解決される**。
  症状 = **リポジトリルートに `user/` が生成される**。解決は `ConfigService.resolve_config_path(path, config_root)`。
  **`config_root` に空文字を渡さない**（空だと相対値が cwd 基準になる）。
- **不変条件（壊しやすい）**: ① `dirty_tracker.trigger_set_source_path` と
  `data[INTERNAL_TRIGGER_SET_SOURCE_PATH]` は**常に一致** / ② 子の `_parent_refs` は
  **保存先ファイルの集合 + 現在の上位** / ③ **canonical identity は比較専用**
  （`normcase` 済み文字列を保存値・戻り値・表示へ混入させない）/
  ④ **共有状況・孤児判定は判定名で分岐する**（表示文言で分岐しない）。
- **【罠・重要】保存経路の例外は `messagebox.showerror` になり、テストではモーダルで永久ブロックする**。
  テスト内の `AssertionError` も広い `except Exception` に捕まり、**失敗が「ハング」に化ける**。
  tests_ui の各ファイルの `setUp` に **fail-fast ガード**がある。新しいモーダルを増やすときは同じガードを足す。
  **ハングしたら `messagebox` / `filedialog` を全遮断して単独実行**する。
- **【tests_ui の罠】`setUpClass` で App を共有する**テストクラスでは
  `has_unsaved_changes()` が他テストの dirty も拾う。**絶対値で assert せず前後の変化で見る**。
  テスト後は runtime・ファイル・menubar を**元へ戻す**（`addCleanup`）。
  **破壊的 I/O の API は UI テストで必ず `patch.object` する**（実ファイルを動かさない）。
- **【教訓・UI】tkinter の「初期表示だけ崩れる」系は one-shot の再計算では直らない**。
  **対象ウィジェット自身の `<Configure>` で自己修復させる**（同幅早期 return を必ず併設）。
- **【罠】`event_generate("<Escape>")` は非表示ウィンドウでは配送されない**。
  `deiconify()` + `update_idletasks()` + `focus_force()` を先に行う。
  バインドを `tk.call` で直接叩くのは**不可**（`%` 置換が `TclError` になりコールバックが走らない）。
- **【罠・再発済】worktree と main は別コピー**。`.claude_data/`・`instructions/`・code とも、main 側の絶対パス
  （パスに `.claude\worktrees\<name>\` を含まない）を編集すると commit から漏れる。
  **本セッションでも handoff.md の書き込み先を 1 度 main 側にしかけた**（Write の既読チェックで止まった）。
- **【罠】Bash ツールは Git Bash**。**長い heredoc は壊れる**（本セッションで handoff.md の
  `cat > file <<EOF` が `unexpected EOF` で失敗した）。**長文ファイルはスクラッチパッドへ書いて `cp`**、
  複数行のコミットメッセージは `git commit -F -` + 短い heredoc に倒す
  （PowerShell の here-string `@'...'@` は**使えない**＝先頭に `@` が混入する）。
  **`git grep` は追跡済みのみ検索**（新規ファイルは `grep`）。
- **【傾向・実証済み】reviewer が「完了可・指摘なし」でも敵対的レビューで High が出る**。
  **判定はテストの実測が優先**。**実装者とレビュアーが同じモデル側になったら別視点が失われている**と疑う。
  **フェーズ完了時は Claude 側 × Codex 側の 2 本立てを省略しない**
  （phase 08・09・10 とも**両者が独立に別の穴を検出**した）。
- **【裏取り】レビュー・調査の「コードがこうなっている」という主張は、採用前に `ファイルパス:行` を実測確認する**
  （行番号のずれ・件数の誤りが実際に何度も出ている。**直近も 2 件の事実誤りを実測で訂正した**）。
- レビュアーは 2 本立て: `reviewer`（sonnet・単一タスクの差分）/ `deep-reviewer`（opus・設計文書/統合/完了判定）。
  Codex レビュー系との併用は `.claude/rules/agent_selection.md` のレビュー表が正。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近 3 件: **13_contracts_boundary_ast_coverage** / 12_config_service_public_surface / 11_orphan_child_file_sweep）。
  提案書「計画05」〜「計画10」は完了済みで、**いずれもフェーズ番号を消費していない**。
- 未着手/保留 idea: **idea_13**（external_keyboard_layouts のパス基準の非対称・低）/
  idea_10（ネストしたモーダルの grab 復元）/ idea_11（別名保存の複製ロールバック・低）/
  idea_03（hotkey 保存正規化・低）/ idea_09（レガシー保存パス・低）/ idea_04・idea_06（保留）。
  **idea_15 は phase 13 で完了**・**idea_14 は phase 12 で完了**・**idea_12 は phase 11 で完了**・**idea_07 は phase 10 で完了**（`INDEX_done.md`）。
  **敵対的レビューが挙げた削除の TOCTOU 2 件は idea 化しない**（修正予定ではないため。
  backlog は修正予定のものを置く場所というユーザー方針）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
