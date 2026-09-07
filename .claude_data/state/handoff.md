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
2. `instructions/phase/current.md` を読む（**アクティブ = phase 13**）
3. `instructions/phase/13_contracts_boundary_ast_coverage/phase.md` を読む
   （**直接改訂モード = 暫定仕様なし**。設計の出発点は起票元
   `instructions/backlog/idea_15_contracts_boundary_ast_coverage.md`）
4. 着手するタスクの定義 `instructions/phase/13_contracts_boundary_ast_coverage/tasks/task_NN_*.md` を読む
   （**未起票。task_01 から `/task_new` で起票してから着手する**）。
   **凍結済の暫定仕様（`instructions/history/`）の条項を実装の根拠に引かない**
5. CLAUDE.md → `.claude/rules/` の順に必要分を読む
6. 過去の判断は `.claude_data/state/decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`

## 現在の作業の 1 行サマリ
**phase 13（公開面の逆戻り防止テストの検査範囲の拡張）を起票済・未着手**（全 2 タスク・2026-09-08）。
phase 12（config_service の公開面の集約）は**完了**。
**次にやること = task_01（検査関数の拡張と自己検証の追加）を `/task_new` で起票して実行する**。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近の実測（**phase 12 完了時点**・phase 13 は未着手でコード差分なし）:
compile **clean** / tests **417**（skip 7）/ tests_ui **288**（skip 0）/ smoke **pass**。
**件数が減ったら退行を疑う**。skip 7 件は**シンボリックリンク作成の特権不足**（`WinError 1314`）で環境依存。
**同じ観点はジャンクション版のテストが実行されている**ので観点の抜けにはならない。
実行後に worktree ルートへ **`user/` も `quarantine/` も生成されていない**ことを確認する。

## 次アクション（session.md.next_action より）
- **【最優先】phase 13 task_01（検査関数の拡張と自己検証の追加）を `/task_new` で起票して実行する**:
  ①`collect_forbidden_refs` に **`ast.Attribute` の連鎖を完全修飾名へ解決**する検査を足す
  ②**`Import` / `ImportFrom` の `asname` を収集**して `cs.orphan_scan` 形を解決する
  ③**自己検証ケースへ 3 経路の禁止例 + 対応する `contracts` の許可例**を追加
  ④**docstring の限界記述を更新**（残る限界＝動的 import / 実行時に組み立てた名前 のみ）。
  **実装は `codex-implementer` へ委任**（テスト実行は依頼しない）→ 実測は `verifier` → `reviewer`。
- **誤検出を最優先で疑う**（`contracts` への完全修飾・エイリアス参照や無関係な同名属性を違反にしない）。
  **既存アサーションを緩めない**。
- **残課題（非 blocking・未対応）**: ①`dropped_paths` が stored 表記へ未正規化
  ②例外内容が理由コードへ落ちて失われる。
- **phase 10 task_05 の `deep-reviewer` 指摘 5 件は候補送りのまま**（H8 / H10 / H11 / H13 / H14）。
- **phase 12 の完了レビューの保留分**（実害なし）: L-1 / L-4 / L-8。

## 現在のフェーズ（phase 13 = 公開面の逆戻り防止テストの検査範囲の拡張）の要点

**直接改訂モード（暫定仕様なし）**。**テストのみ・プロダクション不変・仕様変更なし・実機目視なし**。
番号対応: **phase 13 / 暫定仕様なし / decisions_archive 13**。全 2 タスク・**未着手**。

- **唯一の変更対象は `tests/test_config_service_contracts.py`**。**`keyseq/` に差分を出さない**。
- **塞ぐのは静的な 3 経路**（phase 12 の完了レビューで `deep-reviewer` と Codex が独立に指摘・実測済）:
  ①`from keyseq.application import config_service as cs` + `cs.orphan_scan`
  ②`import keyseq.application.config_service`（**パッケージ名ちょうど**）+
  `keyseq.application.config_service.orphan_scan.X`
  ③`from keyseq import application` + `application.config_service.orphan_scan`。
- **正本 `architecture.md` §3.2 の条項は変更しない**（**検査精度を上げるだけ**）。
- **期待値**: **テストメソッドは 3 本のまま = `tests` 417 件のまま** /
  **現在の presentation は違反 0 件なので拡張後も全 pass**（落ちたら**誤検出**を先に疑う）。
- **検査対象範囲は広げない**（`keyseq/presentation/` 配下の `config_service` 関連のみ。
  `save_plan` / `keymap_service` などは対象外）。**動的 import は原理的な限界として据え置き**。

## 直前フェーズ（phase 12 = config_service の公開面の集約・**完了**）の要点

**規範は正本**（`spec_detail/architecture.md` **§3.2** + `codebase_map.md` の `config_service` パッケージ表
**13 ファイル**）。**暫定仕様 11 は凍結済（v0.3）＝条項を実装の根拠に引かない**。**挙動不変のリファクタ**。
判断の経緯は `decisions_archive/12_config_service_public_surface.md`。

- **公開面 = `config_service/contracts.py`**（**定数 34 / 型 9**・126 行）。
  **`config_service` 内の他モジュールを import しない葉モジュール**（stdlib のみ）。
  `path_boundary.py` / `candidate_dirs.py` と同じ形。**presentation はここと `ConfigService` の公開 API だけを見る**。
- **参照は `from . import contracts` + `contracts.NAME`**（**`from .contracts import NAME` は不可** =
  名前が実装モジュールへ再束縛され `hasattr` の固定テストが書けない）。
- **実装側に残した内部仕様**: `QUARANTINE_DIR_NAME` / `MANIFEST_FILE_NAME` / `UNIT_ID_PATTERN` /
  `ENTRY_*`（`quarantine.py`）/ `CANDIDATE_DIRS` / `RESERVED_DIR`（`candidate_dirs.py`）。
  **「全部移す」方向の退行もテストが落とす**。
- **値の重複（`"invalid_unit_id"` / `"no_manifest"`）は意図的で統合しない**
  （`quarantine_manage_text.py` のラベル分岐が壊れる）。
- **境界は `tests/test_config_service_contracts.py` の 3 メソッドが固定**（実装 5 モジュールの `assertIs` +
  移した 43 名の `hasattr` 偽 / presentation の **AST 走査 4 経路** / **検査関数の自己検証**）。
  **`INTERNAL_MODULE_NAMES` はパッケージの実ファイル一覧と一致必須**（モジュールを増やしたら更新する）。
  **検出できない経路**: 動的 import に加え、**完全修飾のドット参照 / エイリアス束縛 /
  `from keyseq import application` 経由の 3 つ**（実測確認済・**現在の presentation では 0 件**。
  強化は **idea_15** へ分離）。
- **【計画09 の成果・重要】正本 `data_schema.md` は INDEX（260 行）**。**§5.8 / §5.10 の実体は
  `spec_detail/data_schema/` 配下の 13 子ファイル**。**節番号・見出しは不変**なので既存参照はそのまま通じる。
  **仕様更新は子ファイルを編集**し、趣旨が変わったら**親の 1 行要約も追従**させる。
- **【計画08 の成果】候補側ディレクトリの定義は `config_service/candidate_dirs.py` が唯一**
  （走査の候補範囲と復元先ガードが同じ定義を見る）。**再定義しない・添字で結び付けない**（`zip(strict=True)`）。
- **【phase 11 由来・誤りやすい】外部レイアウトの参照解決は `config_root` 基準と `dirname(config_root)` 基準の
  superset**（**「keymap_set 基準」ではない**）。「マニフェスト不正」の **4 条件**・削除の **TOCTOU 2 件受容**は
  **蒸し返さない**（正本 `data_schema.md` §5.8.9 / `decisions_archive/11`）。

## 注意事項・blockers
- **blockers: なし**（phase 13 は起票済・未着手。実機目視の要らないフェーズ）。
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
  ユーザー許可が必須**。phase 11 task_05 で 1 度実施した）。
- **【config_service の配置制約】`config_service` はパッケージ**で **ConfigService 本体は `__init__.py`**。
  テストが `patch("keyseq.application.config_service.os.path", ntpath)` で名前空間を差し替えるため、
  この配置を崩すと壊れる。同じ理由で**パス基盤メソッドを兄弟モジュールへ移さない**。
  抽出関数は **`service` を第 1 引数に取る**。**兄弟から `__init__` を import しない**（循環回避）。
  **兄弟間の共有は public 名を経由する**（private への直接参照は慣習違反）。
  **presentation から兄弟モジュールを直接 import しない**（公開面は **`ConfigService` の公開 API と
  `contracts.py` のみ**。phase 12 で例外は解消済で、**逆戻りはテストが落とす**）。
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
- **【罠】Bash ツールは Git Bash**。複数行のコミットメッセージは**スクラッチパッドへ本文を書いて
  `git commit -F <file>`** が最も確実（PowerShell の here-string `@'...'@` は**使えない**＝
  先頭に `@` が混入する）。**長い python スクリプトの heredoc も失敗することがある**ため
  `.py` を書いて `.venv` の python で実行する。**`git grep` は追跡済みのみ検索**（新規ファイルは `grep`）。
- **【傾向・実証済み】reviewer が「完了可・指摘なし」でも敵対的レビューで High が出る**。
  **判定はテストの実測が優先**。**実装者とレビュアーが同じモデル側になったら別視点が失われている**と疑う
  （phase 11 task_05 がこれに該当し、追加の敵対的レビュー 2 本で **High 3 件**を検出した）。
  **フェーズ完了時は Claude 側 × Codex 側の 2 本立てを省略しない**
  （phase 08・09・10 とも**両者が独立に別の穴を検出**した）。
- **【裏取り】レビュー・調査の「コードがこうなっている」という主張は、採用前に `ファイルパス:行` を実測確認する**
  （行番号のずれ・件数の誤りが実際に何度も出ている）。
- レビュアーは 2 本立て: `reviewer`（sonnet・単一タスクの差分）/ `deep-reviewer`（opus・設計文書/統合/完了判定）。
  Codex レビュー系との併用は `.claude/rules/agent_selection.md` のレビュー表が正。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近 3 件: **12_config_service_public_surface** / 11_orphan_child_file_sweep / 10_reference_link_cleanup）。
  提案書「計画05」「計画06」「計画07」は完了済みで、**いずれもフェーズ番号を消費していない**。
- 未着手/保留 idea: **idea_13**（external_keyboard_layouts のパス基準の非対称・低）/
  idea_10（ネストしたモーダルの grab 復元）/ idea_11（別名保存の複製ロールバック・低）/
  idea_03（hotkey 保存正規化・低）/ idea_09（レガシー保存パス・低）/ idea_04・idea_06（保留）。
  **idea_15 は phase 13 で着手中**・**idea_14 は phase 12 で完了**・**idea_12 は phase 11 で完了**・**idea_07 は phase 10 で完了**（`INDEX_done.md`）。
  **敵対的レビューが挙げた削除の TOCTOU 2 件は idea 化しない**（修正予定ではないため。
  backlog は修正予定のものを置く場所というユーザー方針。残存リスクは暫定仕様 §3-12 が正）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
