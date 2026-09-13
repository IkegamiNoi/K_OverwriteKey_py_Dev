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
2. `instructions/phase/current.md` を読む（**アクティブ = phase 16**）
3. `instructions/phase/16_dialog_transient_parent/phase.md` と
   **主入力の暫定仕様 `instructions/history/14_dialog_parent_and_app_separation.md`（**v0.4**・ユーザー確定済）** を読む。
   進行中タスクの記録は同フォルダの `integration_result.md`（**task_04 の判定の正**）。
   **凍結済の暫定仕様（`instructions/history/` の 04〜13）の条項を実装の根拠に引かない**
4. CLAUDE.md → `.claude/rules/` の順に必要分を読む。
   **`.claude/` 配下または `CLAUDE.md` を編集するなら、先に `.claude_data/modes/README.md` を読む**
5. 過去の判断は `.claude_data/state/decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`

## 現在の作業の 1 行サマリ
**phase 16 task_04 進行中。統合確認・二次レビュー・指摘処理は完了し、残りはユーザーの実機目視 6 項目のみ**（2026-09-13）。
直近コミット: `187907f`（task_03）。**task_04 の記録文書は未コミット**。**phase 15 までは main へマージ済**。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近の実測（**phase 16 task_03 完了時点 = 2026-09-13**）:
compile **clean** / tests **417**（skip 7）/ tests_ui **324** / smoke **pass**。
**tests_ui は 306（phase 14）→ 321（phase 15）→ 324（phase 16）**。**件数が減ったら退行を疑う**。
skip 7 件は**シンボリックリンク作成の特権不足**（`WinError 1314`）で環境依存。
実行後に worktree ルートへ **`user/` も `quarantine/` も生成されていない**ことを確認する。

**【重要】`tests_ui` の一括実行は負荷下で不定期に 5 件 fail する**（**退行ではない**）。
`test_dialog_teardown_flows` の `test_t2_escape_resumes_quarantine_once` が
**Escape の配送を取りこぼす**と、フック停止カウンタが 1 残り**後続 4 件が連鎖**する。
**phase 15 の時点から存在**（`0beb1b4` でも負荷下 6 回中 2 回 fail）。**単独実行なら安定**。
分離済 = [idea_18](../../instructions/backlog/idea_18_escape_delivery_flaky_test.md)。
**赤を見たらまず単独実行で再現するか確かめる**。

**既知の stderr ノイズ（退行ではない）**: 一括実行時のみ
`invalid command name "..._clear_flash_message"` が 4 件（ステータスバーの 4 秒タイマー）。
**フック解除由来のものが出たら退行**を疑う（phase 15 で 0 件にした）。

## 次アクション（session.md.next_action より）
- **【最優先・ユーザー作業】実機目視 6 項目**（`integration_result.md` §5）:
  ①アクション編集を掴んで動かしてもプリセット編集が前面に残る ②プリセット編集を掴んでも
  上書き確認が前面に残る（**未確認のまま実装した経路**）③メニューからのプリセット編集が従来どおり
  ④プリセット追加を閉じて親のモーダル性が戻る ⑤**上書き確認を出したままプリセット編集を ×**
  ⑥入れ子を開いたまま App を最小化 → 復元。
- 結果を `integration_result.md` §5 へ記入 → **task_04 を commit** → task_05 へ。
- **task_05（正本反映）の申し送り 3 件**: ①**暫定仕様 §1-④ の受容根拠を訂正してから凍結**
  ②**`transient_parent` の契約を docstring へ 1 行** ③**`codebase_map.md` の更新先は `modal.py` の節**。
  加えて `decisions_archive/16` / `current.md` 完了記載 / idea_17 を `INDEX_done.md` へ /
  `/refactor_check` / **`deep-reviewer` + `codex-adversarial-reviewer`**。
- **前セッションからの未処理 2 件**: ①`codex_medium` を実運用へ入れる前に `Explore` の可用性確認
  ②`.claude/rules/output_style.md:41-42` の `claude_only` モードで食い違う記述（既存のズレ）。

## 現フェーズ（phase 16 = ネストしたダイアログの前面維持）の要点

**暫定仕様先行モード**（番号対応: phase 16 / 暫定 14 / decisions 16）。
**presentation 限定・スキーマ不変・正本の改訂なし**。**production の差分は実質 6 行**。

- **直す欠陥**: ネストして開いたダイアログが**呼び出し元より前面に留まらない**
  （アクション編集を掴んで動かすとプリセット編集より前に出る。ユーザーが実機で確認）。
- **【用語・最重要】「親」は 3 つの役割を指す**。混同が v0.1 の設計事故の原因だった:
  - **役割 1 = 所有関係**（`tk.Toplevel(master)`）→ **破棄の連鎖**を決める。**動かさない**。
    動かすと正本 `features.md` の「開いた順と違う順で閉じたら内側を優先する」と衝突する（実測）。
  - **役割 2 = 前面維持**（`window.transient(...)` = `grab_modal` の第 2 引数）→ **これだけ直す**。
  - **役割 3 = App 参照**（`parent.hook` 等）→ **動かさない**（App が正しい）。
- **食い違いは 2 件**: `action_dialog.py:339`（→ プリセット編集）/
  `hotkey_presets_io.py:83`（→ 上書き確認）。**`PresetDialog` は既に正しい**。
- **引数の扱いは非対称（意図どおり）**: `PresetManagerDialog` は
  **`transient_parent` に既定あり**（省略時は親。`app.py:418` が既定を使う）/
  `confirm_overwrite` は**キーワード必須**（呼び出し元が 1 箇所だけで既定が到達しないため）。
- **【テストの観測点】呼び出し引数を見るだけの検査は空振りする**（変異検査で実証）。
  **実際の `wm_transient()` を見る**。**戻り値は `Tcl_Obj` なので `assertIs` は不可・`str()` 比較**。
  **`master is app` も併せて固定**する（役割 1 を動かしていない証拠）。
- **受容した制約**: **前面維持の相手を先に破棄すると指定が消える**（実測。生存と grab は保たれる）。
  **「UI から到達しない」という当初の根拠は誤り**（`PresetManagerDialog` は
  `WM_DELETE_WINDOW` を持たず × で直接破棄されるため到達しうる）。**task_05 で文言を訂正する**。

### 前フェーズから引き継ぐ制約（phase 14 = grab 復元 / phase 15 = 後始末）

- **モーダルの窓口は 2 つだけ**: `presentation/modal.py` の **`grab_modal`** と
  `HookController` の **`suspend_hook_for_dialog(window)`**。
  **`grab_set` / `transient` の直呼びは 0 件**。**`grab_modal` は `__init__` の最後の文**
  （静的検査が固定。後ろに処理を足すと落ちる。**落ちたら緩めずユーザーへ諮る**）。
- **`<Destroy>` の bind は `add="+"`**。**`event.widget is window` の判定が必須**。
- **後始末は T1 / T2 に分ける**: 状態の後始末は破棄側、ウィジェットに触る後始末は閉じる操作の側。
  **閉じるボタンでも走らせたいものは閉じるボタンも閉じる操作として結線する**。
- **フック解除は `after(0)` 遅延**。**テストでは `update()` が必要**。
  **終了ガードは `start_hook` の内部**にあり、解除処理は終了中でも `start_hook()` を呼ぶ。
  **検査で `start_hook` の呼び出し回数を見てはいけない**（観測点は `hook_coordinator.start` と `hook_active`）。
- **停止カウンタは入力の扱いにも効くが、止まるのは置換とアクション実行だけで元入力は素通し**。
- **静的検査の対象範囲**: 後始末の検査は **`dialogs/` の 8 クラス限定**。
  `controllers/` を含めると phase 14 の検査（`test_nested_modal_grab.py:302-305`）と正面衝突する。

## 運用インフラ（フェーズ番号を消費しない作業・完了）

- **モード切替は `.claude_data/modes/`**。**エージェント構成は 3 モード**
  （`codex`〔現構成〕/ `codex_medium` / `claude_only`）。
  **`.claude/` 配下または `CLAUDE.md` を編集する前に `.claude_data/modes/README.md` を読む**
  （**`check` は非稼働モードのズレを検知できない**）。
- **template からの取り込みは `/template_pull`**（マーカー = `.claude/template_pull_state.md`。
  `last_pulled = 7791fa7`）。
- **`.gitignore` は追跡ファイルだけを根拠にしない**。確認は `git check-ignore -v`。

## 注意事項・blockers
- **blockers: 実機目視 6 項目が未実施**（ユーザー作業）。**揃うまで task_04 を完了扱いにしない**。
- **【裏取り】レビュー・調査・サブエージェントの「コードがこうなっている」という主張は、
  採用前に `ファイルパス:行` を実測確認する**（**自分が書く文書も同じ**。
  phase 15 で 2 件・phase 16 で 2 件の事実誤りをレビューに検出された。**いずれも実装を読まずに書いたのが原因**）。
  **Codex が「仕様と実装が矛盾する」と報告して止まったら、まず自分で実測する**
  （phase 15 では Codex が正しく、タスク定義側が誤っていた）。
- **【傾向・実証済み】reviewer が「完了可・指摘なし」でも敵対的レビューで指摘が出る**。
  **フェーズ完了時は Claude 側 × Codex 側の 2 本立てを省略しない**。
  **`codex-reviewer`（標準 review）は focus text を受け付けない**ので、観点を渡したいときは
  **`codex-adversarial-reviewer`** を使う。
- **【Codex 運用・最重要】フォワーダが 2 分で切れても Codex ワーカーは生き続ける**。
  **ハングと即断しない**。判別は**作業ツリーの更新時刻**。
  **書き換え途中で `verifier` / `reviewer` を回すと偽の結果を掴む**。
  ワーカー終了後は state が自己更新されないため `codex_operations.md` §4 で手修復する。
- **【Codex 運用】詰まったジョブに `taskkill /T` を使わない**（PID 再利用で無関係なプロセスを巻き込む）。
  **Codex 申告のテスト結果は信用せず必ず実測**。**Codex が使用量上限に達したら実装は止める**
  （レビューは Claude 側へ縮退可・**実装のフォールバックはユーザー許可が必須**）。
- **【運用・重要】委任の実行中はメイン側で文書を編集しない**（Codex が範囲外の差分と判断して巻き戻した実績）。
- **【config_service の配置制約】`config_service` はパッケージ**で **ConfigService 本体は `__init__.py`**。
  テストが `patch("keyseq.application.config_service.os.path", ntpath)` で名前空間を差し替えるため、
  この配置を崩すと壊れる。**パス基盤メソッドを兄弟モジュールへ移さない**。
  抽出関数は **`service` を第 1 引数に取る**。**兄弟から `__init__` を import しない**（循環回避）。
  **presentation から兄弟モジュールを直接 import しない**（公開面は `ConfigService` の公開 API と
  `contracts.py` のみ。**逆戻りはテストが落とす**）。同ファイルは **828 行**のため
  **新規の実ロジックを置かない**（1 行委譲のみ）。
- **【最重要・2 度踏んだ罠】パス表記の混在事故**: runtime の `source_path` 3 種と
  `hotkey_presets_path` は **config 配下なら相対**で保持される。
  **相対値を `os.path.abspath` / `dirname` / `exists` / `join` へ解決なしで渡すと cwd 基準になる**。
  症状 = **リポジトリルートに `user/` が生成される**。解決は `ConfigService.resolve_config_path(path, config_root)`。
  **`config_root` に空文字を渡さない**。
- **不変条件（壊しやすい）**: ① `dirty_tracker.trigger_set_source_path` と
  `data[INTERNAL_TRIGGER_SET_SOURCE_PATH]` は**常に一致** / ② 子の `_parent_refs` は
  **保存先ファイルの集合 + 現在の上位** / ③ **canonical identity は比較専用** /
  ④ **共有状況・孤児判定は判定名で分岐する**（表示文言で分岐しない）。
- **【罠・重要】保存経路の例外は `messagebox.showerror` になり、テストではモーダルで永久ブロックする**。
  テスト内の `AssertionError` も広い `except Exception` に捕まり、**失敗が「ハング」に化ける**。
  tests_ui の各ファイルの `setUp` に **fail-fast ガード**がある。新しいモーダルを増やすときは同じガードを足す。
- **【tests_ui の罠】`setUpClass` で App を共有する**テストクラスでは
  `has_unsaved_changes()` が他テストの dirty も拾う。**絶対値で assert せず前後の変化で見る**。
  **フック停止カウンタも同様**に先行テストの `after(0)` 未実行分が溜まるため、
  **生成前に `self.app.update()` でドレインして 0 を確認してから** 1 → 0 を見る。
  **`suspend_hook_for_dialog` を patch すると `<Destroy>` の結線ごと消える**（空振りになる）。
  **App を破棄する前に `update()` を回す**（保留中の `after` を後続モジュールへ持ち越さない）。
  テスト後は runtime・ファイル・menubar を**元へ戻す**（`addCleanup`）。
  **破壊的 I/O の API は UI テストで必ず `patch.object` する**。
- **【テストの書き方】モジュール名前空間を patch する形は分割の障害になる**。
  **新規テストは `patch.object` を優先する**。
- **【メニュー項目のテスト】インデックスを固定しない**（tearoff でずれる。カスケードとラベルで探す）。
- **【罠】`event_generate("<Escape>")` は非表示ウィンドウでは配送されない**。
  `deiconify()` + `update_idletasks()` + `focus_force()` を先に行う。
  **それでも負荷下では取りこぼす**（idea_18）。`tk.call` で直接叩くのは**不可**。
- **【教訓・UI】tkinter の「初期表示だけ崩れる」系は one-shot の再計算では直らない**。
  **対象ウィジェット自身の `<Configure>` で自己修復させる**（同幅早期 return を必ず併設）。
- **【罠】モジュール移動・パッケージ化の実測では `__pycache__` の stale な `.pyc` を疑う**。
- **【dialogs はパッケージ】**（**1 クラス 1 ファイル**）。**`__init__.py` は明示列挙の再輸出のみ**で
  **`tk` / `messagebox` を持たない**。クラス間参照は**サブモジュール直指定**・
  `App` の型 import は**各ファイルの `TYPE_CHECKING` ガード内**。
  `PresetManagerDialog` の **`_refresh` / `_update_source_labels` はテストが `patch.object` する契約名**。
- **【罠・再発済】worktree と main は別コピー**。main 側の絶対パスを編集すると commit から漏れる。
- **【罠】Bash ツールは Git Bash**。**長い heredoc は壊れる**（本ファイルの再生成でも失敗した。
  その場合は Write ツールを使う）。複数行のコミットメッセージは `git commit -F -` + 短い heredoc。
  PowerShell の here-string `@'...'@` は**使えない**（先頭に `@` が混入する）。
  **`git grep` は追跡済みのみ検索**（新規ファイルは `grep`）。
- レビュアーは 2 本立て: `reviewer`（sonnet・単一タスクの差分）/ `deep-reviewer`（opus・設計文書/統合/完了判定）。
  併用は `.claude/rules/agent_selection.md` のレビュー表が正。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近 3 件: **15_dialog_teardown_on_close** / 14_nested_modal_grab_restore /
  13_contracts_boundary_ast_coverage）。
  提案書「計画05」〜「計画10」は完了済みで、**いずれもフェーズ番号を消費していない**。
- 未着手/保留 idea: **idea_18**（Escape 配送依存テストの不安定・**phase 16 から分離**）/
  idea_13（external_keyboard_layouts のパス基準の非対称・低）/
  idea_11（別名保存の複製ロールバック・低）/ idea_03（hotkey 保存正規化・低）/
  idea_09（レガシー保存パス・低）/ idea_04・idea_06（保留）。
  **idea_17 は phase 16 で着手中**。**idea_16 は phase 15 で完了**・**idea_10 は phase 14 で完了**。
  **敵対的レビューが挙げた削除の TOCTOU 2 件は idea 化しない**（修正予定のものだけを backlog へ置く方針）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
