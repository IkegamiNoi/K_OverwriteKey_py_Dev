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
2. `instructions/phase/current.md` を読む（**アクティブ = phase 11**）
3. `instructions/phase/11_orphan_child_file_sweep/phase.md` と、**主入力の暫定仕様**
   `instructions/history/10_orphan_child_file_sweep.md`（**v0.6・ユーザー確定済**）を読む。
   **フェーズ中は正本 `spec_detail/` を直接改訂しない**（昇格は最終タスク task_08）
4. 着手するタスクの定義 `instructions/phase/11_orphan_child_file_sweep/tasks/task_NN_*.md` を読む
5. CLAUDE.md → `.claude/rules/` の順に必要分を読む
6. 過去の判断は `.claude_data/state/decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`

## 現在の作業の 1 行サマリ
**phase 11 task_07（統合確認）は実機目視のみ残り**。実測・受け入れ条件の突合・二次レビュー 2 本・
**task_07b（指摘 7 件の反映）まで完了しコミット済**。
**次にやること = ユーザーへ実機目視（`manual_check.md` の M1〜M8 + M2b）を依頼し、
結果を `integration_result.md` §4 へ転記して task_07 を完了させる**。その後 task_08（正本反映）。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近の実測（**task_07b 完了時点**）:
compile **clean** / tests **413**（skip 7）/ tests_ui **288**（skip 0）/ smoke **pass**。
**件数が減ったら退行を疑う**。skip 7 件は**シンボリックリンク作成の特権不足**（`WinError 1314`）で環境依存。
**同じ観点はジャンクション版のテストが実行されている**ので観点の抜けにはならない。
実行後に worktree ルートへ **`user/` も `quarantine/` も生成されていない**ことを確認する。

## 次アクション（session.md.next_action より）
- **【次にやること】task_07（統合確認 + 実機目視）を `/task_new` で起票し、実施する**。
  統合確認は `verifier`、二次レビューは `deep-reviewer`（フェーズ区切りのため）。
  **実機目視の観点に必ず含める**: 「隔離実行後の `quarantine/<unit>/` の中身と `manifest.json` の
  `state`」「`quarantine` を書込み不可にした状態での中止表示」「走査ディレクトリの追加 / 削除と
  再起動後の保持」「**隔離 → 復元の往復で元に戻ること**」「**隔離 → 削除で実体が消えること**」
  「**マニフェスト不正な単位の削除時に警告文が出ること**」。
- **【v0.5 / v0.6 の確定内容】** §3-8 検証④（有効な `manifest.json`）は
  **`allow_invalid_manifest=True` で上書き可能**（**①②③は緩和しない**）。理由 = ④を絶対条件にすると
  §3-7 により**復元も削除もできない残骸**が残り、**§4-A の判断と矛盾する**ため。
  加えて **削除の TOCTOU 2 件は受容済**（**§3-12-6 / §3-12-7**。①確認後に追加された未提示ファイルも
  消える = 削除の粒度が実行単位ディレクトリなので仕様どおり ②検証後の隔離ルート差し替え =
  窓は関数内に限られ、塞ぐには「新規依存を足さない」と衝突）。**蒸し返さない**。
  経緯は `decisions.md`「【task_06b 起票時】」「【task_06b 完了時】」。
- **残課題（非 blocking・未対応）**: ①`quarantine.py` の `_move_file` で `os.makedirs` がガードより前
  ②`dropped_paths` が stored 表記へ未正規化 ③例外内容が理由コードへ落ちて失われる
  ④`missing_scan_dirs` の表記不揃い（既定 `user/keymap_sets/` が無い場合だけ絶対パス）。
- **phase 10 task_05 の `deep-reviewer` 指摘 5 件は候補送りのまま**（H8 / H10 / H11 / H13 / H14）。

## 現在のフェーズ（phase 11 = 孤児ファイルの棚卸し）の要点

**規範は暫定仕様 10（未凍結・v0.6）**。到達範囲 = **検出 + 隔離 + 復元 + 隔離済みの削除**。
**本アプリ初のディレクトリ走査かつ初のファイル削除機能**（削除は **task_06b で green**）。
番号対応: **phase 11 / 暫定 10 / decisions_archive 11**。
タスクは 1〜8 + 枝番 3（`phase.md`）。**task_01〜06 + 05b + 06b + 07b が完了**。
**task_07 は実機目視のみ残り**。
- **【task_07b の成果】境界判定 `is_real_path_within` の唯一の定義は
  `config_service/path_boundary.py`**（`quarantine.py` / `orphan_scan.py` に再定義しない。
  `quarantine.py` → `orphan_scan` の import があるので**逆向きは循環**）。
  追加した理由コード = `SOURCE_REDIRECTED` / `SOURCE_DIRECTORY_UNREADABLE`（`reference_scan.py`）/
  `QUARANTINE_ROOT_REDIRECTED`（`quarantine.py`）。
  **既定ディレクトリの不在は `missing_scan_dirs` に入れない**（§3-5-1 はユーザー指定ディレクトリの規定）。

- **走査（参照側）4 経路**: `user/keymap_sets/` 直下 + 起動エントリ + **現在開いているセット
  （`app.keymap_set_path`）** + ユーザー指定ディレクトリ。**3 番目を落とすと、既定外のセットを開いている間に
  その子が隔離される**（`load_keymap_set_from` は `config.json` を書かないため起動エントリでは代替不可）。
- **参照集合は 2 段辿り**: sequence のパスは keymap_set に無く **trigger_set の `triggers[].sequence_path`** のみ。
- **候補側は config 配下の既定 4 種の直下のみ**（keymap / trigger_set / sequence / 個別 hotkey_presets）。
  **形状検証あり**（`mappings` dict / `triggers` list / `actions` list / `hotkey_presets` list）。
  `user/hotkey_presets/global/` は除外。
- **【実測済み・最重要の罠】`canonical_path` は `realpath` を通さない**（`normcase(normpath(abspath))` のみ）。
  **Windows のジャンクションは `os.path.islink()` が `False`** を返すため、**islink スキップでは防げない**。
  **`os.path.realpath()` はジャンクションを解決する**。task_05b で**候補分類と移動直前の両方に
  realpath 境界検証**を入れた。**`_list_json_files` には入れていない**
  （参照側 `scan_dirs` は **config 外を指してよい**仕様。ここに境界検証を足すと**ユーザー指定ディレクトリの
  走査が壊れる**）。
- **【実測済み】`is_path_within` は同一パスも「配下」と判定する**（`__init__.py:738` の docstring）。
  **削除の検証③・復元の `original_path` ガードは、これだけに頼ると穴が開く**
  （隔離ルート自身の再帰削除 / 候補側ディレクトリそのものへの復元）。
- **隔離ルート = `<config_root>/quarantine/`**（`user/` の外＝候補側と構造的に交差させない・**遅延作成**）。
  **マニフェストは移動より先に原子書込み**（`repository.save_json` が `.tmp` + `os.replace`）。
  **書けなければ 1 件も動かさない**。隔離するのは**〔提示済み〕∩〔隔離直前の再判定でも孤児〕**だけ。
- **【確定した設計判断】復元は `state` を信用せず `quarantined_path` の実体の有無で判定する**。
  移動中の進捗書込みが失敗すると **`state` が `planned` のまま実体は移動済み**になり得る（実測済み）。
  **`state == "moved"` だけを復元する実装にしてはならない**。`state` は表示・統計にのみ使う。
- **壊れた親があると無傷の子が孤児候補になる**。ユーザー確定により**警告のみで隔離・削除とも許す**
  （degraded 方式は不採用）。**壊れているのは親、消えるのは子**という取り違えに注意（暫定仕様 §3-12-5）。
- **これまでの成果（application）**: `config_service/` に
  `reference_scan.py`（参照集合・2 段辿り）/ `orphan_scan.py`（走査・判定名 4 種・`normalize_scan_dirs` /
  `collect_protected_paths`）/ `quarantine.py`（隔離・マニフェスト）/ `quarantine_manage.py`（一覧・復元・**削除**）。
  **`ConfigService` へは 1 行委譲のファサードのみ**（同ファイルは **820 行**。実ロジックを置かない）。
- **presentation**: 設定メニュー「孤児ファイルの棚卸し…」「隔離の管理…」/ `orphan_sweep_text.py` ・
  `quarantine_manage_text.py`（表示文言の純関数）/ `config_io/orphan_sweep_io.py` ・
  `quarantine_manage_io.py` / `dialogs/orphan_sweep_dialog.py` ・ `quarantine_manage_dialog.py`。
  **`ReferenceCleanupDialog` は `header` / `run_label` で引数化済み**（既定値は現行文字列。**再改修しない**）。
- **最終 task_08 = 正本反映**で §5.8.1 の**改訂**が必須（現行の「孤児の削除は行わない / 孤児判定は
  原理的に成立しない」を書き換える）。**仕様書側で再検討が要る空白 4 件**（進捗書込み失敗時の扱い /
  実行単位ディレクトリ作成失敗 / §3-11 と実装〔presentation からの定数 import〕の矛盾 /
  マニフェストの `state` キーが §3-6 の例に無い）。
- 直前フェーズ（phase 10 = 参照元の掃除）の要点は**正本が正**
  （`spec_detail/data_schema.md` **§5.8.1** + `features.md` §4.6 + `codebase_map.md`）。
  経緯は `decisions_archive/10_reference_link_cleanup.md`。**暫定仕様 09 は凍結済**
  （**条項を実装の根拠に引かない**）。

## 注意事項・blockers
- **blockers: なし**（コードは green）。ただし **task_07 の完了にはユーザーの実機目視が必要**。
  **未コミットで残るのは task_07 の文書のみ**（`integration_result.md` / `manual_check.md` /
  `tasks/task_07_integration_check.md`）。task_07 の完了時にまとめてコミットする。
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
  **presentation から兄弟モジュールを直接 import しない**（公開面は `ConfigService` の委譲メソッド。
  ただし**判定名・理由コードの定数 import は既存パターンとして可**）。
  同ファイルは **820 行**のため、**新規の実ロジックを置かない**（1 行委譲のみ）。
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
  （直近 3 件: **10_reference_link_cleanup** / 09_per_keymap_set_presets / 08_hotkey_presets_global）。
  提案書「計画05」「計画06」「計画07」は完了済みで、**いずれもフェーズ番号を消費していない**。
- 未着手/保留 idea: **idea_13**（external_keyboard_layouts のパス基準の非対称・低）/
  idea_10（ネストしたモーダルの grab 復元）/ idea_11（別名保存の複製ロールバック・低）/
  idea_03（hotkey 保存正規化・低）/ idea_09（レガシー保存パス・低）/ idea_04・idea_06（保留）。
  **idea_12 は phase 11 で着手中**・**idea_07 は phase 10 で完了**（`INDEX_done.md`）。
  **敵対的レビューが挙げた削除の TOCTOU 2 件は idea 化しない**（修正予定ではないため。
  backlog は修正予定のものを置く場所というユーザー方針。残存リスクは暫定仕様 §3-12 が正）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
