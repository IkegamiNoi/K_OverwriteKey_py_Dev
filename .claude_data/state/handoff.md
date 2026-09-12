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
2. `instructions/phase/current.md` を読む（**アクティブなフェーズは無い。次フェーズ未確定**）
3. **次フェーズの方針をユーザーへ確認する**（`current.md`「次フェーズ候補」/ `instructions/backlog/INDEX.md`）。
   起票は `/phase_start` → 暫定仕様が要るなら `/spec_draft`（判断は `.claude/rules/spec_change_workflow.md`）
4. CLAUDE.md → `.claude/rules/` の順に必要分を読む。
   **`.claude/` 配下または `CLAUDE.md` を編集するなら、先に `.claude_data/modes/README.md` を読む**
   （モード切替で入れ替わるファイルがあり、参照する側の書き方に制約がある）
5. 過去の判断は `.claude_data/state/decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`。
   **凍結済の暫定仕様（`instructions/history/` の 04〜13）の条項を実装の根拠に引かない**

## 現在の作業の 1 行サマリ
**phase 15（ダイアログ後始末の確実な実行）完了。次フェーズ未確定でユーザーの方針確認待ち**（2026-09-13）。
次採番は **phase 16** / 暫定仕様は **14**。**main へは未マージ**。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近の実測（**phase 15 完了時点 = 2026-09-13**）:
compile **clean** / tests **417**（skip 7）/ tests_ui **321** / smoke **pass**。
**tests_ui は 288 →（phase 14 で +18）306 →（phase 15 で +15）321**。**件数が減ったら退行を疑う**。
skip 7 件は**シンボリックリンク作成の特権不足**（`WinError 1314`）で環境依存。
**同じ観点はジャンクション版のテストが実行されている**ので観点の抜けにはならない。
実行後に worktree ルートへ **`user/` も `quarantine/` も生成されていない**ことを確認する。

**既知の stderr ノイズ（退行ではない）**: `tests_ui` の**全体実行時のみ**
`invalid command name "..._clear_flash_message"` が **4 件**出る。
ステータスバーの 4 秒タイマーが App 破棄後に発火するもので、**phase 15 以前からの既存事象**。
テスト結果は `OK`。**フック解除（`resume_hook_after_dialog`）由来のものが出たら退行**を疑う
（phase 15 で 0 件にした。App 破棄前に `update()` を回す規約を tests_ui の 13 箇所へ入れてある）。

## 次アクション（session.md.next_action より）
- **【最優先】次フェーズの方針をユーザーへ確認する**。
- **直近の領域（モーダルダイアログの作法）の残件**は `current.md`「現在の参照先」に 4 件。
  着手候補になり得るのは ①**ダイアログ同型スケルトンの共通化**（phase 11 からの候補送り。
  **phase 14・15 で前提は揃った**＝`grab_modal` と `suspend_hook_for_dialog(window)` の 2 窓口に集約済）
  ②**静的検査の発見ベース化**（保留。**検査が 3 本に増え、いずれもファイル名のハードコード列挙**なので、
  着手するなら併用形の設計から）。
- **【運用の学び・重要】phase 15 では自分が書いた文書の事実誤り 2 件をレビューが検出した**
  （①タスク定義のテスト観測点 ②正本の条項）。**いずれも実装を読まずに書いたのが原因**。
  **仕様・タスク定義へ「実装はこうなっている」と書くときは、先に `ファイルパス:行` を実測する**。
- **前セッションからの未処理 2 件**: ①`codex_medium` を実運用へ入れる前に `Explore` の可用性確認
  ②`.claude/rules/output_style.md:41-42` の `claude_only` モードで食い違う記述（既存のズレ）。
- **phase 10 task_05 の `deep-reviewer` 指摘 5 件は候補送りのまま**（H8 / H10 / H11 / H13 / H14）。
  **phase 12 の完了レビューの保留分**（実害なし）: L-1 / L-4 / L-8。

## 直前フェーズ（phase 15 = ダイアログ後始末の確実な実行・完了）から引き継ぐ制約

判断は `decisions_archive/15_dialog_teardown_on_close.md`。**正本が正**
（`key_input.md` §7.2 / `features.md` §4.6「モーダルダイアログの作法」/ `codebase_map.md`）。

- **モーダルの窓口は 2 つだけ**。**`presentation/modal.py` の `grab_modal`**（モーダル化 + 破棄時の
  grab 復元。`grab_set` / `transient` の直呼びは 0 件）と
  **`HookController.suspend_hook_for_dialog(window)`**（フック停止 + 破棄時の自動解除。
  **`window` 省略時は呼び出し側が解除する try/finally 形**で、`controllers/` の 5 系統はこちら）。
- **`grab_modal` は各ダイアログの `__init__` の最後の文**。**静的検査が固定している**ので
  後ろに処理を足すと落ちる。**落ちたらテストを緩めず、回収機構の要否をユーザーへ諮る**。
- **`<Destroy>` の bind は `add="+"`**。外すと復元も自動解除も無言で消える。
  **`event.widget is window` の判定が必須**（子ウィジェットの破棄でも発火する）。
- **後始末は T1 / T2 に分ける**。**T1 = 状態の後始末（ウィジェットに触らない）は破棄側**、
  **T2 = ウィジェットに触る後始末は閉じる操作の側**（破棄時点で**子は既に無い**＝`TclError`）。
  **閉じるボタンでも走らせたい T2 は、閉じるボタンも閉じる操作として結線する**。
- **解除は `after(0)` 遅延**（`start_hook()` が**同期で `messagebox.showerror` を開き得る** /
  grab 復元と競合させない）。**テストでは `update()` が必要**（`update_idletasks()` では走らない）。
- **終了ガードは `start_hook` の内部**（`begin_shutdown()` で立てる）。**解除処理は終了中でも
  `start_hook()` を呼ぶ**（呼ばれた側が即 return）。**検査で `start_hook` の呼び出し回数を見てはいけない**。
  観測点は **`hook_coordinator.start` の未呼び出し + `hook_active` が False**。
- **停止カウンタは入力の扱いにも効く**が、**止まるのは置換とアクション実行だけで元入力は素通しする**
  （`InputRoute` の既定が **`accept=True`**）。**「入力を通さない」と書くと逆**になる。
- **後始末の静的検査の対象は `dialogs/` の 8 クラスのみ**。
  **`controllers/` を含めると phase 14 の検査と正面衝突する**
  （`tests_ui/test_nested_modal_grab.py:302-305` が `finally: resume_hook_after_dialog` を要求）。
- **`dialogs/` の呼び出し形**: `suspend_hook_for_dialog(self)` が 8 件 /
  `resume_hook_after_dialog` が 0 件 / `def destroy` は 4 件のみ（T2 が残るクラス）。
  引数なし呼び出しは `controllers/` と `keyboard_window.py` の**7 箇所**。**数え違えない**。
- **復元先が未マップ（`winfo_viewable()` = 0）だと grab 復元がスキップされる**。tests_ui で
  実ダイアログを親にするときは **`update_idletasks()` + viewable アサート**を先に置く。
- **`tk.Toplevel` を差し替えるテストダブルの `bind` は `add=None` を受ける必要がある**（計 3 つ）。

適用状況を見る grep:
```bash
grep -rn "grab_set\|transient" keyseq/presentation/ --include=*.py                # modal.py のみ
grep -rn "suspend_hook_for_dialog" keyseq/presentation/dialogs/ --include=*.py    # 8 件すべて (self) 付き
grep -rn "resume_hook_after_dialog" keyseq/presentation/dialogs/ --include=*.py   # 0 件
grep -rn "def destroy" keyseq/presentation/dialogs/ --include=*.py                # 4 件のみ
```

## 運用インフラ（フェーズ番号を消費しない作業・完了）

- **モード切替は `.claude_data/modes/`**（`instructions/agent_mode` ・ `instructions/save_mode` から移動。
  旧パスは存在しない）。**エージェント構成は 3 モード**（`codex`〔現構成〕/ `codex_medium` / `claude_only`）。
  **`.claude/` 配下または `CLAUDE.md` を編集する前に `.claude_data/modes/README.md` を読む**
  （**`check` は非稼働モードのズレを検知できない** / 参照側は具体エージェント名を書かず
  `agent_selection.md` の既定へ委ねる）。
- **template からの取り込みは `/template_pull`**。マーカー = `.claude/template_pull_state.md`
  （`last_pulled = 7791fa7`。**ファイルの対応関係・template と意図的に差分にした箇所はここが正**）。
- **`.gitignore` は追跡ファイルだけを根拠にしない**。確認は `git check-ignore -v`。

## 注意事項・blockers
- **blockers: なし**（phase 15 は完了処理まで終了。次フェーズ未確定のみ）。
- **【裏取り】レビュー・調査・サブエージェントの「コードがこうなっている」という主張は、
  採用前に `ファイルパス:行` を実測確認する**（**自分が書く文書も同じ**。phase 15 で 2 件の
  事実誤りをレビューに検出された）。**Codex が「仕様と実装が矛盾する」と報告して止まったら、
  まず自分で実測する**（phase 15 では Codex が正しく、タスク定義側が誤っていた）。
- **【傾向・実証済み】reviewer が「完了可・指摘なし」でも敵対的レビューで指摘が出る**。
  **フェーズ完了時は Claude 側 × Codex 側の 2 本立てを省略しない**
  （phase 08・09・10・15 とも**両者が独立に穴を検出**した）。
  **`codex-reviewer`（標準 review）は focus text を受け付けない**ので観点を渡したいときは
  **`codex-adversarial-reviewer`** を使う。
- **【Codex 運用・最重要】フォワーダが 2 分で切れても Codex ワーカーは生き続ける**（companion status は
  `running` のまま停滞する）。**ハングと即断しない**。判別は**作業ツリーの更新時刻**。
  **書き換え途中で `verifier` / `reviewer` を回すと偽の結果を掴む**。
  ワーカー終了後は state が自己更新されないため `codex_operations.md` §4 で手修復する。
- **【Codex 運用】詰まったジョブに `taskkill /T` を使わない**（PID 再利用で**無関係なプロセスを巻き込む**）。
  フォワーダが最終出力を返さず完了通知だけ来ることがある → `SendMessage` で再開して回収する。
  **Codex 申告のテスト結果は信用せず必ず実測**。**サブエージェントがセッション上限で落ちたら再実行する**。
  **Codex が使用量上限に達したら実装は止める**（レビューは Claude 側へ縮退可・**実装のフォールバックは
  ユーザー許可が必須**）。
- **【教訓】Codex は「記録を足す」指示を「skip を増やす」方向へ広げることがある**。
  **差分は必ずメインが読んで裏取りする**（テストが green でも、テストごと誤った挙動を固定していることがある）。
- **【運用・重要】委任の実行中はメイン側で文書を編集しない**。phase 10 task_05 で **Codex がメインの
  仕様書編集を「範囲外の差分」と判断して巻き戻した**。編集した場合は**完了後に必ず差分を確認する**。
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
  **`config_root` に空文字を渡さない**。
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
  **フック停止カウンタも同様**に先行テストの `after(0)` 未実行分が溜まるため、
  **生成前に `self.app.update()` でドレインして 0 を確認してから** 1 → 0 を見る。
  **`suspend_hook_for_dialog` を patch すると `<Destroy>` の結線ごと消える**ため、
  patch したままカウンタを見る検査は**常に真の空振り**になる。
  テスト後は runtime・ファイル・menubar を**元へ戻す**（`addCleanup`）。
  **破壊的 I/O の API は UI テストで必ず `patch.object` する**。
- **【テストの書き方】モジュール名前空間を patch する形は分割の障害になる**（計画07 で 6 箇所書き換えた）。
  **新規テストは `patch.object` を優先する**。
- **【メニュー項目のテスト】インデックスを固定しない**。top-level menubar には **tearoff** があり
  `0=tearoff / 1=ファイル / 2=設定` とずれる。**カスケードとラベルで探す**。
- **【罠】`event_generate("<Escape>")` は非表示ウィンドウでは配送されない**。
  `deiconify()` + `update_idletasks()` + `focus_force()` を先に行う。
  バインドを `tk.call` で直接叩くのは**不可**（`%` 置換が `TclError` になりコールバックが走らない）。
- **【教訓・UI】tkinter の「初期表示だけ崩れる」系は one-shot の再計算では直らない**。
  **対象ウィジェット自身の `<Configure>` で自己修復させる**（同幅早期 return を必ず併設）。
- **【罠】モジュール移動・パッケージ化の実測では `__pycache__` の stale な `.pyc` を疑う**。
- **【dialogs はパッケージ】**（`keyseq/presentation/dialogs/`・**1 クラス 1 ファイル**）。
  **`__init__.py` は明示列挙の再輸出のみ**で **`tk` / `messagebox` を持たない**。
  クラス間参照は**サブモジュール直指定**・`App` の型 import は**各ファイルの `TYPE_CHECKING` ガード内**。
  `PresetManagerDialog` の **`_refresh` / `_update_source_labels` はテストが `patch.object` する契約名**
  （リネーム禁止）。
- **【罠・再発済】worktree と main は別コピー**。`.claude_data/`・`instructions/`・code とも、main 側の絶対パス
  （パスに `.claude\worktrees\<name>\` を含まない）を編集すると commit から漏れる。
- **【罠】Bash ツールは Git Bash**。**長い heredoc は壊れる**（本ファイルの再生成でも実際に失敗した。
  その場合は Write ツールを使う）。複数行のコミットメッセージは `git commit -F -` + 短い heredoc に倒す
  （PowerShell の here-string `@'...'@` は**使えない**＝先頭に `@` が混入する）。
  **`git grep` は追跡済みのみ検索**（新規ファイルは `grep`）。
- レビュアーは 2 本立て: `reviewer`（sonnet・単一タスクの差分）/ `deep-reviewer`（opus・設計文書/統合/完了判定）。
  Codex レビュー系との併用は `.claude/rules/agent_selection.md` のレビュー表が正。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近 3 件: **15_dialog_teardown_on_close** / 14_nested_modal_grab_restore /
  13_contracts_boundary_ast_coverage）。
  提案書「計画05」〜「計画10」は完了済みで、**いずれもフェーズ番号を消費していない**。
- 未着手/保留 idea: **idea_17**（`ActionDialog` の親付け替え・低・phase 14 から分離）/
  idea_13（external_keyboard_layouts のパス基準の非対称・低）/
  idea_11（別名保存の複製ロールバック・低）/ idea_03（hotkey 保存正規化・低）/
  idea_09（レガシー保存パス・低）/ idea_04・idea_06（保留）。
  **idea_16 は phase 15 で完了**・**idea_10 は phase 14 で完了**（`INDEX_done.md`）。
  **敵対的レビューが挙げた削除の TOCTOU 2 件は idea 化しない**（修正予定ではないため。
  backlog は修正予定のものを置く場所というユーザー方針）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
