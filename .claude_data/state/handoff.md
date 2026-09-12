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
2. `instructions/phase/current.md` を読む（**アクティブ = phase 15**）
3. `instructions/phase/15_dialog_teardown_on_close/phase.md` と
   **主入力の暫定仕様 `instructions/history/13_dialog_teardown_on_close.md`（**v0.4**・ユーザー確定済・実装着手可）** を読む。
   **凍結済の暫定仕様（`instructions/history/` の 04〜12）の条項を実装の根拠に引かない**
4. CLAUDE.md → `.claude/rules/` の順に必要分を読む。
   **`.claude/` 配下または `CLAUDE.md` を編集するなら、先に `.claude_data/modes/README.md` を読む**
   （モード切替で入れ替わるファイルがあり、参照する側の書き方に制約がある）
5. 過去の判断は `.claude_data/state/decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`

## 現在の作業の 1 行サマリ
**phase 15（ダイアログ後始末の確実な実行）進行中。task_02（`dialogs/` 8 クラスへの適用）
完了・green・reviewer 完了可。task_03〜05 は未着手**（2026-09-13）。
**次にやること = `/task_new` で task_03（受け入れ条件のテスト + 静的検査）を起票し委任する**。
直近コミット: `aa5adc8`（task_01）/ `3386c33`（task_02）。**main へは未マージ**。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近の実測（**phase 15 task_02 完了時点 = 2026-09-13・コミット `3386c33`**）:
compile **clean** / tests **417**（skip 7）/ tests_ui **311**（skip 0）/ smoke **pass**。
**tests_ui は 288 →（phase 14 で +18）306 →（phase 15 task_01 で +5）311**
（**task_02 は件数を増やさない**。既存 5 箇所の観測点を移しただけ）。
**件数が減ったら退行を疑う**。skip 7 件は**シンボリックリンク作成の特権不足**（`WinError 1314`）で環境依存。
**同じ観点はジャンクション版のテストが実行されている**ので観点の抜けにはならない。
実行後に worktree ルートへ **`user/` も `quarantine/` も生成されていない**ことを確認する。

適用状況を見る grep:
```bash
grep -rn "grab_set" keyseq/presentation/ --include=*.py     # modal.py の 2 行のみ（phase 14 の成果）
grep -rn "transient" keyseq/presentation/ --include=*.py    # modal.py の 1 行のみ
grep -rn "suspend_hook_for_dialog" keyseq/presentation/dialogs/ --include=*.py  # 8 件すべて (self) 付き
grep -rn "resume_hook_after_dialog" keyseq/presentation/dialogs/ --include=*.py # 0 件
grep -rn "def destroy" keyseq/presentation/dialogs/ --include=*.py              # 4 件のみ（T2 が残るクラス）
```

## 次アクション（session.md.next_action より）
- **【最優先】phase 15 task_03 を `/task_new` で起票する**（`tasks/task_03_acceptance_tests.md`）。
  内容 = 受け入れ条件のテスト（暫定仕様 13 §5・§7）:
  ①**× 閉じ（Tcl レベル破棄 `dialog.tk.call("destroy", str(dialog))`）で解除が走る**
  （`protocol` 未登録の代表 1〜2 クラス。全 8 クラスは静的検査が守る）
  ②**OK / キャンセル / × / プログラム破棄で解除がちょうど 1 回**
  ③**子ウィジェット破棄では走らない**
  ④**アプリ終了時に `start_hook()` が走らない**（**ダイアログ経路と `child_save_dialog` の
  try/finally 経路の両方**）
  ⑤**phase 14 の非退行**（ネストを × で閉じても grab が親へ復元）
  ⑥**静的検査**（**対象は `dialogs/` の 8 クラスに限定**）
  ⑦**既存テストの書き換え** = `test_app_ui_flows.py:1325-1341` の観測点を
  「**保存が走らないこと**」へ移す（override 削除で検証内容が空になっているため）。
  起票後 `codex-implementer` へ委任（**テスト実行は依頼しない**。実測は `verifier`）。
- その後: task_04（統合確認 + `deep-reviewer` + `codex-reviewer` + **実機目視**）→
  task_05（正本反映・最終）。
- **【運用】Codex が不調**（2026-09-13 に 2 回連続ハング）。委任したら**早期にログ停滞を監視**し、
  詰まったら `codex_operations.md` §3/§4 へ。復旧しなければユーザーへ諮って切り替える。
- **前セッションからの未処理 2 件**: ①`codex_medium` を実運用へ入れる前に `Explore` の可用性確認
  ②`.claude/rules/output_style.md:41-42` の `claude_only` モードで食い違う記述（既存のズレ）。
- **phase 10 task_05 の `deep-reviewer` 指摘 5 件は候補送りのまま**（H8 / H10 / H11 / H13 / H14）。
  **phase 12 の完了レビューの保留分**（実害なし）: L-1 / L-4 / L-8。

## 現フェーズ（phase 15 = ダイアログ後始末の確実な実行）の要点

**暫定仕様先行モード**（番号対応: phase 15 / 暫定 13 / decisions 15）。
**規範は `instructions/history/13_dialog_teardown_on_close.md`（v0.4・ユーザー確定済・実装着手可）**。
**presentation 層のみ・スキーマ不変・正本違反の是正**（`key_input.md` §7.2 を満たしていない）。

- **直す欠陥**: ダイアログを **× で閉じると Python の `destroy()` override が呼ばれず**、
  `resume_hook_after_dialog()` が飛んで**フック停止カウンタがずれる**。
  以後ダイアログを開いても**フックが止まらず誤爆し得る**。
- **【取り違え注意】× 閉じ（Tcl レベル破棄）では Python の `destroy()` は呼ばれないが、
  `root.destroy()` は子の Python `destroy()` を再帰的に呼ぶ**（どちらも実測確認済）。
  つまり**アプリ終了時は今日でも後始末が走る**（v0.1 で逆に書いて訂正した）。
- **後始末は T1 / T2 に分ける** — **T1 = 状態の後始末（ウィジェットに触らない）だけを
  破棄イベントへ寄せる**。**T2 = ウィジェットに触る後始末は `destroy()` override に残す**。
  理由: **子ウィジェットは親の `<Destroy>` より先に破棄される**ため、
  T2 を寄せると `TclError` になる（実測確認済）。
- **登録は `HookController` へ寄せた**（task_01 完了） — `suspend_hook_for_dialog(window)` が
  停止と解除予約を原子的に行う。**`window` 省略時は現行と完全に同じ**（try/finally 形は無変更）。
- **解除は `after(0)` 遅延** — `start_hook()` が**同期で `messagebox.showerror` を開き得る**ため
  破棄処理の途中で入れ子のモーダルを回さない / **grab 復元と競合させない**。
  **テストでは `update()` が必要**（`update_idletasks()` では `after` は走らない）。
- **終了ガード `begin_shutdown()`** — 終了確定後は**どの解除経路からもフックを再開しない**。
  `app.on_close` が `confirm_save_if_dirty` 通過後・`self.destroy()` 前に立てる。
  **`window.master.winfo_exists()` による終了判定は機能しない**（`Tk.destroy` は子を先に壊すため常に真）。
- **静的検査の対象は `dialogs/` の 8 クラスのみ**（task_03 で追加予定）。
  **`controllers/` の try/finally 形を巻き込むと phase 14 の既存静的検査と衝突する**
  （`tests_ui/test_nested_modal_grab.py:300-303` が `finally: resume_hook_after_dialog` を要求）。
  **task_02 完了後の引数なし呼び出しは 7 箇所**（`config_io/child_save_dialog.py` 3 +
  `config_io/io_dialogs.py` 1 + `keymap_panel_controller.py` 1 + `key_capture.py:57` +
  `keyboard_window.py:270`）。**`dialogs/` の 8 箇所は全て `(self)` 付き**。**数え違えない**。
- **スコープ外**: 非ダイアログ経路の結線方式（**終了ガードは効く**）/ `key_capture` /
  `keyboard_window` の編集モード / スケルトン共通化 / M-6（静的検査の発見ベース化）/ idea_17。

### 直前フェーズ（phase 14 = grab 復元・完了）から引き継ぐ制約

- **`grab_modal` は各ダイアログの `__init__` の最後の文**。**静的検査が固定している**ので
  後ろに処理を足すと落ちる。**落ちたらテストを緩めず、回収機構の要否をユーザーへ諮る**。
- **`<Destroy>` の bind は `add="+"`**（`modal.py:46`）。外すと復元が無言で消える。
  **本フェーズの結線もこれに倣う**。
- **`tk.Toplevel` を差し替えるテストダブルの `bind` は `add=None` を受ける必要がある**（計 3 つ）。
- **復元先が未マップ（`winfo_viewable()` = 0）だと復元がスキップされる**。tests_ui で
  実ダイアログを親にするときは **`update_idletasks()` + viewable アサート**を先に置く。

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
- **blockers: なし**（phase 15 task_02 は全確認 pass・変異検査も期待どおり・`reviewer` 完了可）。
- **【Codex 運用・2026-09-13 の実績】同一 worktree で 2 回連続ハングした**。1 回目は**ジョブ登録すら
  されず**、2 回目は `Starting Codex task thread.` の直後に**worker PID が消滅**。
  `codex_operations.md` §4 で state を手修復済（バックアップは scratchpad の `codex_state_backup`）。
  **委任後は作業ツリーの更新時刻とジョブログの伸びを早期に見る**。
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
- **【tests_ui の罠・task_02 で踏んだ】解除は `after(0)` 予約なので、`update()` を回すまで
  カウンタが減らない。App を共有するクラスでは**先行テストの未実行予約が溜まり**、
  ダイアログ生成直後のカウンタが 1 ではなく累積値になる。
  **生成前に `self.app.update()` でドレインして 0 を確認してから** 1 → 0 を見る。
  また **`suspend_hook_for_dialog` を patch すると `<Destroy>` の結線ごと消える**ため、
  patch したままカウンタを見る検査は**常に真の空振り**になる。
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
  （直近 3 件: **14_nested_modal_grab_restore** / 13_contracts_boundary_ast_coverage /
  12_config_service_public_surface）。
  提案書「計画05」〜「計画10」は完了済みで、**いずれもフェーズ番号を消費していない**。
- 未着手/保留 idea: **idea_17**（`ActionDialog` の親付け替え・低・phase 14 から分離）/
  idea_13（external_keyboard_layouts のパス基準の非対称・低）/
  idea_11（別名保存の複製ロールバック・低）/ idea_03（hotkey 保存正規化・低）/
  idea_09（レガシー保存パス・低）/ idea_04・idea_06（保留）。
  **idea_16 は phase 15 で着手中**。**idea_10 は phase 14 で完了**・**idea_15 は phase 13 で完了**・
  **idea_14 は phase 12 で完了**（`INDEX_done.md`）。
  **敵対的レビューが挙げた削除の TOCTOU 2 件は idea 化しない**（修正予定ではないため。
  backlog は修正予定のものを置く場所というユーザー方針）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
