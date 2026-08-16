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
2. `instructions/phase/current.md` → [phase 10 の phase.md](../../instructions/phase/10_reference_link_cleanup/phase.md) を読む
3. 主入力の確定設計 = [history/09_reference_link_cleanup.md](../../instructions/history/09_reference_link_cleanup.md)
   （**v0.5・ユーザー確定済**。**§2 が確定事項の集約**。§3-1 検査 / §3-2 除去 / §3-3 UI /
   **§3-5 既知の制約**が実装の規範。**版が多いので古い版の条項を引かないこと**）
4. 実機目視の観点 = [tasks/task_05_integration_check.md](../../instructions/phase/10_reference_link_cleanup/tasks/task_05_integration_check.md) **§3 の表**
5. CLAUDE.md → `.claude/rules/` の順に必要分を読む
6. 過去の判断は `.claude_data/state/decisions.md`（**末尾に進行中の phase 10 の節がある**）+
   「アーカイブ索引」→ `decisions_archive/<phase>.md`

## 現在の作業の 1 行サマリ
**phase 10 の実装（task_01〜04）は完了。task_05 の通し実測と 2 本立てレビューも完了し指摘を反映済み。
残るは実機目視 14 項目〔ユーザー作業〕→ task_06（正本反映）**。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近の実測（phase 10 task_05 の是正後・コミット `165f8c4`）:
compile **clean** / tests **267** / tests_ui **238** / smoke **pass** /
manual **未実施（14 項目）**。
**件数が減ったら退行を疑う**。実行後に worktree ルートへ `user/` が生成されていないことも確認する。

## 次アクション（session.md.next_action より）
- **【ユーザー作業・これが残り全部】実機目視 14 項目**。観点は
  `tasks/task_05_integration_check.md` **§3 の表**が正（受入条件との対応付き）。
  準備 = **アプリ終了中に `config/user/` 配下の子JSON の `_parent_refs` へ実在しないパスを 1〜2 件足す**。
  特に重要な 4 つ:
  - **7**（現在の構成セットのファイルを別フォルダへ移動 → 掃除 → **その参照元は「消える」側に出ず残る**）
  - **9〜11**（未保存の導線。**いいえ = 何も起きない** / **保存ダイアログをキャンセル = 掃除も走らない** /
    **保存完了 = そのまま検査へ進む**）
  - **13**（**保護対象だけの子なら一覧が出ず「掃除する項目はありません。」**＝ v0.5 の是正）
  - **4b**（フックの suspend / resume を **実行・キャンセル・× ・Esc の 4 経路**で）
  - 目視で不具合が出たら **task_05 内で是正**（最小差分 + `reviewer` 再実施）。
    仕様変更を伴うなら**枝番タスクへ切り出す**。
- その後 **task_06 = 正本反映（最終）**: `data_schema.md` **§5.8.1 改訂**
  （「掃除は後続課題」の差し替え / 「追加のみ」への例外 / **検査範囲は現在の構成セットの子＝全網羅ではない** /
  **全件除去時は `[]`** / **現在の keymap_set・trigger_set への参照は除去しない** /
  **未保存時は先に保存が要る**）+ 必要なら §5.8.4 の注記 + `features.md` + `codebase_map.md` /
  暫定仕様 09 を凍結 / `decisions_archive/10_reference_link_cleanup.md` 作成 /
  `current.md` 完了更新 / `backlog/INDEX.md` の idea_07 を `INDEX_done.md` へ / `/refactor_check`。
  - **`/refactor_check` の注目点**: `config_service/__init__.py` が **767 行**（+30）。phase 09 から M1 該当で保留中。
  - **task_06 送りのレビュー指摘**: presentation が `config_service` の内部モジュールを直参照 /
    委譲の戻り値型が `Any` / `reference_cleanup_text.py` の配置が利用範囲より広い /
    `_nonempty_path` が strip しない値を返す / `run_cleanup` に例外の受け皿が無い。
- 各タスクの流れ: タスク定義起票 → codex-implementer へ委任 → **verifier で実測** → reviewer → コミット。

## 現フェーズ（phase 10 = 参照元の掃除）の要点

**確定設計は暫定仕様 09（v0.5）が正**。**実装は task_01〜04 まで完了**（残りは実機目視 → task_06）。

- **何をする機能か**: 子JSON（keymap / trigger_set / sequence）の **`_parent_refs`** から
  **実体の無い上位パスを除去する**保守機能（設定メニュー →「参照元を掃除…」）。
  目的は §5.8.4 の**誤警告**（「N 個の上位で共有中」）と**余分な依存確認**の解消。
- **検査範囲は「現在の構成セットが参照している子」のみ**。**列挙は runtime の source_path 3 種**
  （`INTERNAL_{KEYMAP,TRIGGER_SET,SEQUENCE}_SOURCE_PATH`）。
  **`resolve_child_save_targets` を使ってはならない**（「次に保存するとしたらどこへ書くか」であり、
  未実体化の子へ既定パスが割り当てられて**無関係な既存ファイルを書き換える**）。
- **保護対象**（keymap / trigger_set → 現在の `keymap_set_path` / sequence → 現在の trigger_set パス）は
  **実在しなくても除去しない**（消すと次回保存で全子が「所有元不明」→ 既定が別名保存へ倒れる）。
  **検査の時点で分離**し、**「消える」一覧・件数・0 件警告に出さない**（表示と実行結果を一致させる）。
- **除去直前に JSON 全体を読み直して判定をやり直す**（検査時のスナップショットを書き戻すと、
  確認中の外部変更を全体置換で消す）。**読めない / 非 dict / 保存例外は失敗記録して継続**。
  **除去 0 件なら書かない（冪等）**。**全件除去時は `[]`**（キーは残す。§5.1）。
- **孤児は削除しない**（警告表示のみ）。**確認 UI は 1 枚**（読み取り専用の一覧 + 実行 / キャンセル。
  **消える参照元は全件提示**＝到達不能な媒体の参照元を消す事故に気づけるように）。
- **未保存（`keymap_set_path` が空）なら先に保存を確認**し、**成功時だけ掃除する**
  （空だと個別保存が掃除前の refs を再書き込みして**巻き戻る**ため）。
- **runtime・dirty は変更しない**。**保存フロー・JSON スキーマは変更しない**。
- **層**: 検査・除去 = `config_service/parent_refs_cleanup.py`（application）/ 文言 =
  `presentation/reference_cleanup_text.py`（**tkinter 非依存の純関数**）/ フロー =
  `controllers/config_io/reference_cleanup_io.py` / UI = `dialogs/reference_cleanup_dialog.py`。
- **既知の制約（§3-5・実装は変えない）**: sequence の掃除は **trigger_set が実体化していること**が前提 /
  確認中に上位が消えると**提示していない参照元も消え得る** / **再判定で対象外になった子は通知に出ない** /
  **前提として呼ぶ保存経路は正本 §5.8.6 の best-effort**（本フェーズの保証は「掃除による書き込みが 0 件」）。
- **スコープ外**: 全走査 / 孤児検出 / 逆方向検査 → **idea_12**（次フェーズ以降）。

## 注意事項・blockers
- **blockers: task_05 の完了に実機目視（ユーザー作業）が必要**。それまでフェーズ完了判定は出せない。
  自動確認（実測・2 本立てレビュー）は**完了済み**。
- **【運用・重要】委任の実行中はメイン側で文書を編集しない**。task_05 で **Codex がメインの仕様書編集を
  「範囲外の差分」と判断して巻き戻した**（v0.5 の記述が消えた）。編集した場合は**完了後に必ず差分を確認する**。
- **【メニュー項目のテスト】インデックスを固定しない**。top-level menubar には **tearoff** があり
  `0=tearoff / 1=ファイル / 2=設定` とずれる。**カスケードとラベルで探す**（task_04 で 1 度踏んだ）。
- **【テストの書き方】モジュール名前空間を patch する形は分割の障害になる**（計画07 で 6 箇所書き換えた）。
  **新規テストは `patch.object` を優先する**。
- **【罠】モジュール移動・パッケージ化の実測では `__pycache__` の stale な `.pyc` を疑う**
  （旧モジュールが生存し得る。削除して結果不変を確認する）。
- **【計画07 の成果】`dialogs` はパッケージ**（`keyseq/presentation/dialogs/`・**1 クラス 1 ファイル**）。
  **`__init__.py` は明示列挙の再輸出のみ**で **`tk` / `messagebox` を持たない**。
  クラス間参照は**サブモジュール直指定**・`App` の型 import は**各ファイルの `TYPE_CHECKING` ガード内**
  （どちらを崩しても `ImportError` / 循環）。
  `PresetManagerDialog` の **`_refresh` / `_update_source_labels` はテストが `patch.object` する契約名**
  （リネーム禁止）。
- **【Codex 運用・最重要】フォワーダが 2 分で切れても Codex ワーカーは生き続ける**（companion status は
  `running` のまま停滞する）。**ハングと即断しない**。判別は**作業ツリーの更新時刻**。
  **書き換え途中で `verifier` / `reviewer` を回すと偽の結果を掴む**。
  ワーカー終了後は state が自己更新されないため `codex_operations.md` §4 で手修復する。
- **【Codex 運用】詰まったジョブに `taskkill /T` を使わない**（PID 再利用で**無関係なプロセスを巻き込む**）。
  フォワーダが最終出力を返さず完了通知だけ来ることがある → `SendMessage` で再開して回収する。
  **Codex 申告のテスト結果は信用せず必ず実測**。**サブエージェントがセッション上限で落ちたら再実行する**。
- **【config_service の配置制約】`config_service` はパッケージ**で **ConfigService 本体は `__init__.py`**。
  テストが `patch("keyseq.application.config_service.os.path", ntpath)` で名前空間を差し替えるため、
  この配置を崩すと壊れる。同じ理由で**パス基盤メソッドを兄弟モジュールへ移さない**。
  抽出関数は **`service` を第 1 引数に取る**。**兄弟から `__init__` を import しない**（循環回避）。
  **presentation から兄弟モジュールを直接 import しない**（公開面は `ConfigService` の委譲メソッド）。
- **【最重要・2 度踏んだ罠】パス表記の混在事故**: runtime の `source_path` 3 種と
  `hotkey_presets_path` は **config 配下なら相対**で保持される（config 外は絶対・区切りは `/` 正規化）。
  **相対値を `os.path.abspath` / `dirname` / `exists` / `join` へ解決なしで渡すと cwd 基準で解決される**。
  症状 = **リポジトリルートに `user/` が生成される**。解決は `ConfigService.resolve_config_path(path, config_root)`。
- **不変条件（壊しやすい）**: ① `dirty_tracker.trigger_set_source_path` と
  `data[INTERNAL_TRIGGER_SET_SOURCE_PATH]` は**常に一致** / ② 子の `_parent_refs` は
  **保存先ファイルの集合 + 現在の上位** / ③ **canonical identity は比較専用**
  （`normcase` 済み文字列を保存値・戻り値・表示へ混入させない）/
  ④ **共有状況は判定名で分岐する**（`SHARE_SOLE` / `SHARE_NEW`。表示文言で分岐しない）。
- **【罠・重要】保存経路の例外は `messagebox.showerror` になり、テストではモーダルで永久ブロックする**。
  テスト内の `AssertionError` も広い `except Exception` に捕まり、**失敗が「ハング」に化ける**。
  tests_ui の各ファイルの `setUp` に **fail-fast ガード**がある。新しいモーダルを増やすときは同じガードを足す。
  **ハングしたら `messagebox` / `filedialog` を全遮断して単独実行**する。
- **【tests_ui の罠】`setUpClass` で App を共有する**テストクラスでは
  `has_unsaved_changes()` が他テストの dirty も拾う。**絶対値で assert せず前後の変化で見る**。
  テスト後は runtime・ファイル・menubar を**元へ戻す**（`addCleanup`）。
- **【教訓・UI】tkinter の「初期表示だけ崩れる」系は one-shot の再計算では直らない**。
  **対象ウィジェット自身の `<Configure>` で自己修復させる**（同幅早期 return を必ず併設）。
- **【罠・再発済】worktree と main は別コピー**。`.claude_data/`・`instructions/`・code とも、main 側の絶対パス
  （パスに `.claude\worktrees\<name>\` を含まない）を編集すると commit から漏れる。
- **【罠】Bash ツールは Git Bash**。複数行のコミットメッセージは **heredoc** が確実。
  **`git grep` は追跡済みのみ検索**（新規ファイルは直接 `grep`）。行数計測は `wc -l`。
- **【傾向】reviewer が「完了可」でも実測・別レビューで問題が出る**。**判定はテストの実測が優先**。
  **フェーズ完了時は Claude 側 × Codex 側の 2 本立てを省略しない**
  （phase 08・09・10 とも**両者が独立に別の穴を検出**した）。
- レビュアーは 2 本立て: `reviewer`（sonnet・単一タスクの差分）/ `deep-reviewer`（opus・設計文書/統合/完了判定）。
  Codex レビュー系との併用は `.claude/rules/agent_selection.md` のレビュー表が正。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近 3 件: **09_per_keymap_set_presets** / 08_hotkey_presets_global / 07_hook_keys_global_default）。
  提案書「計画05」「計画06」「計画07」は完了済みで、**いずれもフェーズ番号を消費していない**。
- 未着手/保留 idea: **idea_12**（全走査 + 孤児候補・**phase 10 完了が前提**）/
  idea_10（ネストしたモーダルの grab 復元）/ idea_11（別名保存の複製ロールバック・低）/
  idea_03（hotkey 保存正規化・低）/ idea_09（レガシー保存パス・低）/ idea_04・idea_06（保留）。
  **idea_07 は phase 10 で着手中**。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
