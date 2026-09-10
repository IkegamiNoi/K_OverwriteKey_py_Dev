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
2. `instructions/phase/current.md` を読む（**アクティブ = phase 14**）
3. `instructions/phase/14_nested_modal_grab_restore/phase.md` と
   **主入力の暫定仕様 `instructions/history/12_nested_modal_grab_restore.md`（v0.4・確定済）** を読む。
   **凍結済の暫定仕様（`instructions/history/` の 04〜11）の条項を実装の根拠に引かない**
4. CLAUDE.md → `.claude/rules/` の順に必要分を読む。
   **`.claude/` 配下または `CLAUDE.md` を編集するなら、先に `.claude_data/modes/README.md` を読む**
   （モード切替で入れ替わるファイルがあり、参照する側の書き方に制約がある）
5. 過去の判断は `.claude_data/state/decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`

## 現在の作業の 1 行サマリ
**phase 14（ネストしたモーダルの grab 復元）進行中。task_01（`modal.py` 新設 + 系統 B 4 箇所）
完了・green・reviewer 採用。task_02〜06 は未着手**（2026-09-10）。
**次にやること = `/task_new` で task_02（`dialogs/` 9 クラスへの適用）を起票し委任する**。

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
**その後のセッションはアプリ本体・テストへのコード差分 0 行**（運用インフラと文書のみ）なので、この値が現在値。
**件数が減ったら退行を疑う**。skip 7 件は**シンボリックリンク作成の特権不足**（`WinError 1314`）で環境依存。
**同じ観点はジャンクション版のテストが実行されている**ので観点の抜けにはならない。
実行後に worktree ルートへ **`user/` も `quarantine/` も生成されていない**ことを確認する。

## 次アクション（session.md.next_action より）
- **【最優先】phase 14 task_02 を `/task_new` で起票する**
  （`tasks/task_02_dialogs_grab_modal.md`）。内容 = `keyseq/presentation/dialogs/` の **9 クラス**の
  `__init__` にある `grab_set` / `transient` を `grab_modal` へ置換。
  **注意点は phase.md のタスク 2 に記載済**。起票後 `codex-implementer` へ委任
  （**テスト実行は依頼しない**。実測は `verifier`）。
- その後: task_03（ネスト経路 3 系統のテスト）→ task_04（契約 3 条のテスト）→
  task_05（統合確認 + **ユーザーによる実機目視**）→ task_06（正本反映・最終）。
- フェーズ末（task_06）で **`ActionDialog` の親付け替え**を `/idea` で起票する（暫定仕様 §6-5）。
- フェーズ末に **`/refactor_check`** を実行し、**ダイアログ同型スケルトンの共通化**
  （phase 11 からの候補送り・本フェーズで意図的に分離）を判定対象にする。
- **前セッションからの未処理 2 件**: ①`codex_medium` を実運用へ入れる前に `Explore` の可用性確認
  ②`.claude/rules/output_style.md:41-42` の `claude_only` モードで食い違う記述（既存のズレ）。
- **境界検査の残件**（着手するなら新規 idea 起票）: 残る限界 4 つ（動的 import /
  実行時に組み立てた名前 / 代入による再束縛 / 縮退時の未解決）と、**素の名前検査の潜在的誤検出**
  （`ConfigService` に内部モジュールと同名の公開メンバが増えると落ちる）。
- **phase 10 task_05 の `deep-reviewer` 指摘 5 件は候補送りのまま**（H8 / H10 / H11 / H13 / H14）。
  **phase 12 の完了レビューの保留分**（実害なし）: L-1 / L-4 / L-8。

## 現フェーズ（phase 14 = ネストしたモーダルの grab 復元）の要点

**暫定仕様先行モード**（番号対応: phase 14 / 暫定 12 / decisions 14）。
**規範は `instructions/history/12_nested_modal_grab_restore.md`（v0.4・ユーザー確定済・実装着手可）**。
**presentation 層のみ・スキーマ不変・機能追加ではない**。

- **復元は子側**（ダイアログが自分の `grab_set()` の前に `grab_current()` を記録し、破棄時に戻す）。
  `wait_window` 側 20 箇所には触らない。
  **ヘルパ = `keyseq/presentation/modal.py` の `grab_modal(window, parent=None)`（task_01 で実装済）**。
  状態は**クロージャ**に持ち**ウィジェット属性に持たない**。冒頭の `previous is window` 早期 return が
  冪等性を担う。**`<Destroy>` を `"+"` なしで bind する**ので、同じウィンドウへ別の `<Destroy>` を
  足すと**復元が無言で消える**（保留扱いの既知の弱点）。
- **task_01 完了時点で系統 B の 4 箇所は適用済**。ネスト経路 3（上書き確認）は**この時点で既に直っている**
  見込みで、**実ダイアログでの確認は task_03**。残るはダイアログ 9 クラス（task_02）。
- **「誰へ戻すか」（§3-1）と「そもそも戻してよいか」（§3-7）は別条件**。
  §3-1 は**記録した保持者が `None` 以外なら戻す**（「自分自身のときだけ」に絞ると
  **最も実害の大きいネスト経路 3 が復元されない**）。§3-7 は**破棄時点の保持者が自分か
  誰も居ないときだけ戻す**（非 LIFO 終了で最内側の grab を奪わないため）。
- **ネスト経路は 3 系統**: ①プリセット編集 → 追加/編集（`preset_manager.py:283`・`:318`）
  ②アクション編集 → プリセット編集（`action_dialog.py:342`・①と連鎖して 3 段）
  ③**プリセット編集 → 上書き確認**（`preset_manager.py:364` → `hotkey_presets_io.py:42`）。
  **③が最も実害が大きい** — 上書きを承諾しないと `save_hotkey_presets` が `False` を返し
  `preset_manager.py:381-382` がマネージャを閉じないため、**grab を失ったダイアログが開いたまま残る**。
- **破棄フックは `__init__` 途中の例外では発火しない**（`action_dialog.py:123` は grab 取得後に
  `_sync_capture_ui()` を呼ぶ）。初期化失敗の回収を明示する（§3-6）。
- **コールバック例外では子を閉じない**（§3-8）。Tk は例外を `report_callback_exception` へ渡すだけ。
- **適用は系統 A（`dialogs/` 9 クラス）+ 系統 B（`controllers/config_io/` 4 箇所）の全 13 箇所**。
  系統 B を先行タスクにする。
- **対象外**: stdlib ダイアログの grab（**未検証・実機目視のみ**）/ ダイアログ同型スケルトンの共通化 /
  `ActionDialog` の親付け替え / 順序統一目的の並べ替え / grab 以外の後始末。
- **テスト上の罠**: `tk.Toplevel` を差し替えるスタブは **2 つ**あり、**両方に手当てが要る**
  （task_01 で 1 つ見落として 4 件落ちた）。`tests_ui/test_child_save_dialog.py:149` の
  `_FakeSaveDialog` と `tests_ui/test_config_io_characterization.py:66` の `_FakeDialog`。
  **どちらも `grab_set` / `wait_window` が no-op なので grab の回帰基準にならない**。
  探すときは `grep -rn "def grab_set" tests_ui/`。
  `tests_ui/test_app_ui_flows.py:72`・`:1327-1338` は `object.__new__(PresetManagerDialog)` +
  `destroy` 直呼びなので、**復元処理は属性未初期化でも落ちないこと**。
  `grab_current()` の観測例は `tests_ui/test_quarantine_manage_flow.py:286`。

## 運用インフラ（フェーズ番号を消費しない直前の作業・完了）

- **モード切替は `.claude_data/modes/`**（`instructions/agent_mode` ・ `instructions/save_mode` から移動。
  旧パスは存在しない）。**エージェント構成は 3 モード**（`codex`〔現構成〕/ `codex_medium` / `claude_only`）。
  **`.claude/` 配下または `CLAUDE.md` を編集する前に `.claude_data/modes/README.md` を読む**
  （**`check` は非稼働モードのズレを検知できない** / 参照側は具体エージェント名を書かず
  `agent_selection.md` の既定へ委ねる）。
- **template からの取り込みは `/template_pull`**。マーカー = `.claude/template_pull_state.md`
  （`last_pulled = 7791fa7`。**ファイルの対応関係・template と意図的に差分にした箇所はここが正**）。
- **`.gitignore` は追跡ファイルだけを根拠にしない**。確認は `git check-ignore -v`。

## 注意事項・blockers
- **blockers: なし**（起票は 3 レビューを通し反映済。文書のみでコード差分 0 行）。
- **【裏取り】レビュー・調査の「コードがこうなっている」という主張は、採用前に `ファイルパス:行` を実測確認する**
  （行番号のずれ・件数の誤りが何度も出ている。**phase 14 の起票でも 2 件の事実誤りを実測で訂正した**）。
- **【傾向・実証済み】reviewer が「完了可・指摘なし」でも敵対的レビューで High が出る**。
  **判定はテストの実測が優先**。**実装者とレビュアーが同じモデル側になったら別視点が失われている**と疑う。
  **フェーズ完了時は Claude 側 × Codex 側の 2 本立てを省略しない**
  （phase 08・09・10 とも**両者が独立に別の穴を検出**した。**phase 14 の起票でも同じことが起きた**）。
- **【教訓・task_07b】Codex は「記録を足す」指示を「skip を増やす」方向へ広げることがある**。
  **差分は必ずメインが読んで裏取りする**（テストが green でも、テストごと誤った挙動を固定していることがある）。
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
- **【罠】Bash ツールは Git Bash**。**長い heredoc は壊れる**。
  **長文ファイルはスクラッチパッドへ書いて `cp`**、複数行のコミットメッセージは
  `git commit -F -` + 短い heredoc に倒す
  （PowerShell の here-string `@'...'@` は**使えない**＝先頭に `@` が混入する）。
  **`git grep` は追跡済みのみ検索**（新規ファイルは `grep`）。
- レビュアーは 2 本立て: `reviewer`（sonnet・単一タスクの差分）/ `deep-reviewer`（opus・設計文書/統合/完了判定）。
  Codex レビュー系との併用は `.claude/rules/agent_selection.md` のレビュー表が正。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近 3 件: **13_contracts_boundary_ast_coverage** / 12_config_service_public_surface / 11_orphan_child_file_sweep）。
  提案書「計画05」〜「計画10」は完了済みで、**いずれもフェーズ番号を消費していない**。
- 未着手/保留 idea: **idea_13**（external_keyboard_layouts のパス基準の非対称・低）/
  idea_11（別名保存の複製ロールバック・低）/ idea_03（hotkey 保存正規化・低）/
  idea_09（レガシー保存パス・低）/ idea_04・idea_06（保留）。
  **idea_10 は phase 14 で着手中**。**idea_15 は phase 13 で完了**・**idea_14 は phase 12 で完了**・
  **idea_12 は phase 11 で完了**・**idea_07 は phase 10 で完了**（`INDEX_done.md`）。
  **敵対的レビューが挙げた削除の TOCTOU 2 件は idea 化しない**（修正予定ではないため。
  backlog は修正予定のものを置く場所というユーザー方針）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
