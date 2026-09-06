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
   `instructions/history/10_orphan_child_file_sweep.md`（**v0.4・ユーザー確定済**）を読む。
   **フェーズ中は正本 `spec_detail/` を直接改訂しない**（昇格は最終タスク task_08）
4. 着手するタスクの定義 `instructions/phase/11_orphan_child_file_sweep/tasks/task_NN_*.md` を読む
5. CLAUDE.md → `.claude/rules/` の順に必要分を読む
6. 過去の判断は `.claude_data/state/decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`

## 現在の作業の 1 行サマリ
**phase 11 task_01（参照パス収集器）完了**（verifier 実測 green / reviewer = 完了可）。次は **task_02（走査と孤児判定）**。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近の実測（phase 11 task_01 完了時点）:
compile **clean** / tests **279** / tests_ui **238** / smoke **pass**（実機目視は task_07 でまとめて実施）。
**件数が減ったら退行を疑う**。実行後に worktree ルートへ `user/` が生成されていないことも確認する。

## 次アクション（session.md.next_action より）
- **task_02（走査と孤児判定）を起票して着手する**（`/task_new` → `codex-implementer` →
  **`verifier` で実測** → `reviewer` → `/save_state` → `/task_commit`）。
  範囲 = 参照側の**ディレクトリ列挙**（既定 / 起動エントリ / 現在のセット / 指定ディレクトリ）+
  **`config.json` のグローバルプリセットパスの取り込み** + 候補側の収集と**形状検証** +
  **保護対象の適用** + 判定名 4 種 + 走査の不完全性の記録（暫定仕様 §3-2 / §3-4 / §3-5）。
- **task_01 の reviewer 申し送り（非 blocking）**: ①**`collect_reference_paths` に空文字の `config_root` を
  渡さない**（`resolve_config_path` は空だと相対値を絶対化せず **cwd 基準**になる。task_02 の呼び出し側で担保）
  ②同一ファイルを複数表記で参照して読めない場合、`unreadable_sources` の記録は**1 回だけ**（重複抑制）
  ③trigger_set の `SOURCE_MISSING` 単体テストは無い（`_load_source` は共有で keymap_set 側が通過済み）。
- **phase 10 task_05 の `deep-reviewer` 指摘 5 件は候補送りのまま**（H8 / H10 / H11 / H13 / H14）。
  **phase 11 では新規コードで同じ形を作らない**にとどめる（暫定仕様 §6）。

## 現在のフェーズ（phase 11 = 孤児ファイルの棚卸し）の要点

**規範は暫定仕様 10（未凍結・v0.4）**。到達範囲 = **検出 + 隔離 + 復元 + 隔離済みの削除**。
**本アプリ初のディレクトリ走査かつ初のファイル削除機能**（`keyseq/` に `os.remove` は現在 0 件）。
番号対応: **phase 11 / 暫定 10 / decisions_archive 11**。

- **走査（参照側）4 経路**: `user/keymap_sets/` 直下 + 起動エントリ + **現在開いているセット
  （`app.keymap_set_path`）** + ユーザー指定ディレクトリ。**3 番目を落とすと、既定外のセットを開いている間に
  その子が隔離される**（`load_keymap_set_from` は `config.json` を書かないため起動エントリでは代替不可）。
- **参照集合は 2 段辿り**: sequence のパスは keymap_set に無く **trigger_set の `triggers[].sequence_path`** のみ。
- **候補側は config 配下の既定 4 種の直下のみ**（keymap / trigger_set / sequence / 個別 hotkey_presets）。
  **形状検証あり**（`mappings` dict / `triggers` list / `actions` list / `hotkey_presets` list）。
  `user/hotkey_presets/global/` は除外。
- **隔離ルート = `<config_root>/quarantine/`**（`user/` の外＝候補側と構造的に交差させない）。
  **マニフェストは移動より先に原子書込み**（後追いだと中断時に**アプリから復元できない隔離物**が残る）。
- **削除 API はパスでなく実行単位 ID を受け取り 4 検証**。
  **`is_path_within` は同一パスも「配下」と判定する**（`__init__.py:686`）ため、
  それだけに頼ると**隔離ルート自身が再帰削除され得る**。
- **削除は通常のファイル削除**（ゴミ箱へ送らない・新規依存を足さない）。
- **壊れた親があると無傷の子が孤児候補になる**。ユーザー確定により**警告のみで隔離・削除とも許す**
  （degraded 方式は不採用）。**壊れているのは親、消えるのは子**という取り違えに注意（暫定仕様 §3-12-5）。
- **task_01 の成果（完了）**: `config_service/reference_scan.py` の
  `collect_reference_paths(service, keymap_set_paths, *, config_root)` →
  `ReferenceScanResult(referenced: frozenset[str]〔canonical・**比較専用**〕/
  unreadable_sources: tuple[(入力表記, 理由)] / non_keymap_set_sources)`。
  理由コード = `SOURCE_MISSING` / `SOURCE_UNREADABLE`。**keymap_set 判定はキーの有無だけ**。
  `external_keyboard_layouts` は **config_root 基準と dirname(config_root) 基準の両方**を登録（superset）。
- タスクは 1〜8（`phase.md`）。**最終 task_08 = 正本反映**で §5.8.1 の**改訂**が必須
  （現行の「孤児の削除は行わない / 孤児判定は原理的に成立しない」を書き換える）。
- 直前フェーズ（phase 10 = 参照元の掃除）の要点は**正本が正**
  （`spec_detail/data_schema.md` **§5.8.1** + `features.md` §4.6 + `codebase_map.md`）。
  経緯は `decisions_archive/10_reference_link_cleanup.md`。**暫定仕様 09 は凍結済**
  （**条項を実装の根拠に引かない**）。

## 注意事項・blockers
- **blockers: なし**（phase 11 進行中。次は task_02）。
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
- **【config_service の配置制約】`config_service` はパッケージ**で **ConfigService 本体は `__init__.py`**。
  テストが `patch("keyseq.application.config_service.os.path", ntpath)` で名前空間を差し替えるため、
  この配置を崩すと壊れる。同じ理由で**パス基盤メソッドを兄弟モジュールへ移さない**。
  抽出関数は **`service` を第 1 引数に取る**。**兄弟から `__init__` を import しない**（循環回避）。
  **presentation から兄弟モジュールを直接 import しない**（公開面は `ConfigService` の委譲メソッド）。
  同ファイルは **767 行で分割保留中**のため、**新規の実ロジックを置かない**（1 行委譲のみ）。
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
  ただし**長い python スクリプトの heredoc は失敗することがある**ため、
  スクラッチパッドへ `.py` を書いて `.venv` の python で実行する方が確実。
  **`git grep` は追跡済みのみ検索**（新規ファイルは直接 `grep`）。行数計測は `wc -l`。
- **【傾向】reviewer が「完了可」でも実測・別レビューで問題が出る**。**判定はテストの実測が優先**。
  **フェーズ完了時は Claude 側 × Codex 側の 2 本立てを省略しない**
  （phase 08・09・10 とも**両者が独立に別の穴を検出**した。phase 11 の暫定仕様でも同様）。
- レビュアーは 2 本立て: `reviewer`（sonnet・単一タスクの差分）/ `deep-reviewer`（opus・設計文書/統合/完了判定）。
  Codex レビュー系との併用は `.claude/rules/agent_selection.md` のレビュー表が正。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近 3 件: **10_reference_link_cleanup** / 09_per_keymap_set_presets / 08_hotkey_presets_global）。
  提案書「計画05」「計画06」「計画07」は完了済みで、**いずれもフェーズ番号を消費していない**。
- 未着手/保留 idea: **idea_13**（external_keyboard_layouts のパス基準の非対称・低）/
  idea_10（ネストしたモーダルの grab 復元）/ idea_11（別名保存の複製ロールバック・低）/
  idea_03（hotkey 保存正規化・低）/ idea_09（レガシー保存パス・低）/ idea_04・idea_06（保留）。
  **idea_12 は phase 11 で着手中**・**idea_07 は phase 10 で完了**（`INDEX_done.md`）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
