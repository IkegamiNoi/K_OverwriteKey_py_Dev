# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-09-21T14:40:00
phase: `instructions/phase/26_startup_entry_preservation`（起動エントリの保存時据え置き）**完了**。**直接改訂モード**・暫定仕様なし。番号対応: phase 26 / decisions 26。次採番 = phase 27 / 暫定 21 / decisions 27。
直前の完了フェーズ = phase 26（判断履歴 = `decisions_archive/26_startup_entry_preservation.md`）。
last_commit_location: `claude/jikki-mokushi-ok-58bca4`
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 26（起動エントリを保存で上書きしない）完了。task_01〔正本改訂〕/ task_02〔実装〕/ task_03〔記録と完了〕すべて reviewer 採用・実測 green・実機目視 OK・refactor_check 不要。次フェーズ未確定。**
mode: completed

## last_action
ts: 2026-09-21T14:40:00
who: main
summary: |
  【task_03 = 記録と完了（文書のみ）】ユーザーの実機目視 OK を受けてフェーズ最終タスクを実施。
  タスク定義を起票し、`decisions_archive/26_startup_entry_preservation.md` を新規作成して
  phase 26 の判断（仕様変更判定 / 案 A 採用・案 B 除外 / 別名保存でも据え置き / 可視化 UI・解除手段の除外 /
  実装上の判断 4 点 / 現状監査 / 残件）を集約。`decisions.md` は**本文の phase 26 節を削除し索引 1 行へ**。
  `current.md` = 完了記載（リンクのみ）+ 「直近の領域」を phase 26 へ差し替え + 直前完了フェーズ 26/25/24 +
  「別タスク化候補」へ Phase 26 項（`.strip()` 非対称・到達不能のため据え置き）+ 次採番行を完了表記へ。
  **起票元 idea が無いため backlog は無変更**（`git status` で確認）。
  【refactor_check】メトリクス収集 = `verifier`。PHASE_BASE `e0c19ba`・対象 `keyseq` 5 ファイル・**+16/-1 行**。
  **M1〜M6 すべて非該当** → 判定 **不要**（`keymap_set_io.py` は 687 行だが増分 +4 で「600 行超 **かつ** +100 行」を満たさない）。
  【レビュー = reviewer】**完了可（採用）**。事実主張（`split_payloads.py:363` / `startup_io.py:31` /
  `keymap_set_io.py:135`・`:655`）を実測で裏取り済み。参考指摘 1 件 = phase.md の task_03 行を
  レビュー確定前に「採用」と先書きした順序（実害なし）。
  なお reviewer は `current.md` を「全行 LF」と報告したが、**worktree 実測では 341 行すべて CRLF**で混在なし。
result_files:
  - .claude_data/state/decisions_archive/26_startup_entry_preservation.md（新規）
  - .claude_data/state/decisions.md（索引 1 行追加・本文 phase 26 節を削除）
  - instructions/phase/current.md
  - instructions/phase/26_startup_entry_preservation/phase.md
  - instructions/phase/26_startup_entry_preservation/tasks/task_03_record_and_close.md（新規）
verified:
  compile: clean
  tests: 518 ran OK（skipped 7・task_02 実測。task_03 はコード無変更）
  tests_ui: 449 ran OK（task_02 実測。task_03 はコード無変更）
  smoke: SMOKE OK（task_02 実測）
  review: reviewer（task_03 差分）= 完了可・採用 / task_01・task_02 も採用済
  refactor_check: 不要（M1〜M6 該当なし・対象 5 ファイル・PHASE_BASE `e0c19ba`）
  実機目視: OK（2026-09-21・ユーザー確認）


## next_action
- **phase 26 は完了。次フェーズは未確定** — 着手前に**ユーザーへ方針を確認する**。
  候補の確認先は `instructions/backlog/INDEX.md`（未着手はいずれも優先度低）。起票は `/phase_start`。
- 次フェーズ番号 = **27**（decisions も 27 / 暫定仕様を使う場合は 21）。
- **main へのマージはユーザーが行う**（main は phase 18 task_05d まで取り込み済）。
- **前セッションからの未処理 2 件**: ①`codex_medium` を実運用へ入れる前に `Explore` の可用性確認
  ②`.claude/rules/output_style.md:41-42` の `claude_only` モードで食い違う記述（既存のズレ）。

## blockers
- なし

## resume_hints
- **ユーザーへの提示は日本語で行う**（2026-09-16 指示）。
- **【phase 26 の設計は正本が正】起動エントリ = `config/config.json` の `keymap_set_path`。
  正本 `spec_detail/data_schema.md` §5.4**。要点 = ①**保存では更新しない**（別名保存でも据え置き）。
  変更経路はメニュー「起動時に読む構成セットを指定…」のみ ②**例外 = 未設定 / 起動時に読めなかった場合のみ**
  保存先で更新（自己修復）③**判定は起動時の実読込結果**（保存時に実在確認をし直さない＝壊れた JSON も自己修復対象）
  ④**据え置くのは `keymap_set_path` の値だけ**で、config.json の他キーは従来どおり書き直す。
  実装の要 = `build_startup_payload`（application が更新要否を判定）+ `StartupIo.entry_loaded`（presentation は事実のみ保持）。
- **【phase 25 の成果は正本が正】パス系の型正規化 = `spec_detail/data_schema.md` §5.5 / §5.7**（§5.1 の共通規則を参照する形）。
  要点 = ①**使い分け = パスは `coerce_label`（trim のみ）/ キー名・id は `coerce_key_name`（trim + 小文字化）**。
  **パスに `coerce_key_name` を使うと小文字化で壊れる**（§5.7 の `normcase` は比較専用）
  ②**参照突合経路（`reference_scan.py`）は生 JSON を直接読む別実装**で `ensure_config_compatibility` を通らない。
  同種の修正はこの経路も個別に確認する
  ③**keymap_set の `keymaps[]`（参照エントリ）は旧記法の文字列を受ける**。§5.1 の「`keymaps[]` の非 dict 要素は除去」は
  **単一 JSON / runtime の内容 keymaps** を指す別物。混同すると互換を壊す
  ④**未対応の残件** = `startup_io.py` の `keymap_set_path`（presentation 層）/ **runtime 内部キー**
  （`_keymap_source_path` 等。正本 §5.7 に【実装未追従】として明記済）。
- **【phase 24 の成果は正本が正】JSON 読込の型正規化 = `spec_detail/data_schema.md` §5.1「型不正の共通規則」（新設）+ §5.6「keymap」（新設）+ §5.2 / §5.11**。暫定仕様 20 は凍結済。
  要点 = ①`domain/config.py` の **`coerce_key_name` / `coerce_label`**（非 str は `""`）へ一本化し**全読込経路へ適用**
  （`normalize_key_name` のシグネチャは不変。呼び出しが多数で意味が変わるため）
  ②**非文字列は空扱い**。ただし要素が成立しないなら除去（`mappings` の対 / `hotkey_presets`）。
  **`actions` の要素除去は非 dict という形状由来**であり `label` の型不正では要素は残る
  ③**単一 JSON の `keymaps[].id` だけ扱いが違う**（stem へ倒せないため要素ごと除去・`_2` 一意化なし）
  ④**falsy な非文字列は元から空扱い**で挙動不変。変わるのは truthy な非文字列のみ
  ⑤**パス系フィールド（`path` / `switch_key` 等）は未対応** = idea_25。
  ⑥教訓: **棚卸しは「該当パターンの全走査」で裏を取る**。当初 6 箇所と見積もったが実際は 9 箇所だった。
- **【phase 23 の成果は正本が正】`actions[]` の読込時正規化 = `spec_detail/data_schema.md` §5.11 + `codebase_map.md`**。暫定仕様なし（直接改訂モード）。
  要点 = ①正規化（**dict 以外の要素を除去 + `label` を整形**）は `domain/config.py::normalize_actions` に一本化し、
  `ensure_config_compatibility` と `application/config_service::_normalize_sequence_payload` の 2 系統から呼ぶ（**application 側に規則を再実装しない**）
  ②`_normalize_sequence_payload` の戻り値には `label: ""` が付く（既存経路と同じ形。テストの期待値もこれに合わせる）
  ③**保存（`build_sequence_payload`）は正規化を通さない**設計のまま。`save_sequence_file` は payload を書いた**後**に正規化するので**ディスクの JSON は不変**
  ④`split_loading` 経由は二重に正規化されるが冪等。**keymap / trigger_set の個別読込は未対応のまま**（スコープ外）。
- **【phase 22 の成果は正本が正】マウスのドラッグ = `spec_detail/data_schema.md` §5.11「アクション要素」 + `codebase_map.md`「マウス操作」節**。
  暫定仕様 19 は凍結済で条項の根拠に引かない。要点 = ①`mouse_click` に `drag` / `to_x` / `to_y` / `drag_speed`（px/秒・既定 1000）を追加し
  **`drag` false では新 4 キーを出力しない**（生成停止）②**所要時間 = 距離 ÷ 速度を 0.15〜5.0 秒へクランプ**（算出は application 層。
  下限が無いと pyautogui が補間せずワープ / 上限が無いと UI スレッドが固まる）③**ドラッグ中だけ `pyautogui.FAILSAFE` を False にし `finally` で復元**
  （`mouseUp` の前に FailSafe 判定が走り、離す点が隅だと解放が遮られる）・`dragTo` と `ctypes` は使わない
  ④**実行中に物理マウスを動かすと離す位置がずれる**（制御しない・§5.11.5）
  ⑤**この穴は phase 23 で解消済**（下記）。
- **【phase 21 の成果は正本が正】キーの送信 = `spec_detail/key_input.md` §7.7 + `codebase_map.md`「キーの送信」節**。暫定仕様なし（直接改訂モード）。
  要点 = ①**拡張キー 18 名は `ctypes` の `keybd_event` + KEYEVENTF_EXTENDEDKEY で送る**（表 = `keyseq/infrastructure/input_gateway.py` の `_EXTENDED_KEYS`。
  `keyboard` ライブラリの `from_name` は同名に拡張 / 非拡張が混在し `windows` が無いので**使わない**）
  ②**拡張キーを含む hotkey だけ自前送信**（含まなければ従来どおり `keyboard.send`）・記述順に押し逆順に離す・例外時も押した分を逆順に離してから再送出
  ③`windows` は左・`ctrl` / `alt` / `shift`・テンキーの Enter と `/`・`alt gr` は**対象外**（`alt gr` は欧州系配列で `right alt` と同一物理キーだが**意図的に**対象外）
  ④正規化は**公開 API** `keyboard.normalize_name`（非公開 `keyboard._canonical_names` を直 import しない）
  ⑤**【新しい前提】注入した拡張キーは `keyboard` の `is_replaying` が効かず自アプリのフックに届く**。
  現状は send guard が先に素通しにするので挙動は不変（実機確認済）だが、**guard の解除タイミングを変える改修時は自己起動しないか再確認する**。
- **【phase 20 の成果は正本が正】最小の高さ = `features.md` §4.6「最小の高さ」項 + `codebase_map.md`**。暫定仕様 18 は凍結済。最小の高さ = `paneconfigure` 後の要求高さ（`tk.PanedWindow` の要求高さは paneconfigure まで古い）。
  tests_ui で最小の高さを触るテストは `pane_layout.window_min_height` も退避・復元する（手本 `tests_ui/test_full_view_min_height.py`）。
- **【phase 19 の成果は正本が正】ヘッダ幅 = `features.md` §4.6「フル表示の幅配分」（「ヘッダの要求幅」はウィンドウ幅換算）+ `codebase_map.md`**。暫定仕様 17 は凍結済。
  **tests_ui でヘッダ幅が絡む既定幅の期待値は `max(780, pane_layout.header_window_width)` で書く**（標準フォントでも 799 に広がる）。
- **【phase 18 の成果は正本が正】フル表示の幅配分 = `features.md` §4.6「フル表示の幅配分」+ `data_schema.md` §5.4 + `codebase_map.md` の PaneLayoutController 節**。
  暫定仕様 16 は凍結済で条項の根拠に引かない。**tests_ui で App を作るテストはウィンドウ幅の保存予約（500ms）が走るので、`write_startup` をクラス単位で差し替え、破棄前に `pane_layout.cancel_window_width_save()`**（手本 `tests_ui/test_pane_window_width_persistence.py`）。
- **【phase 17 の成果は正本が正】最小化中の grab 預かり = `features.md` §4.6 + `codebase_map.md` の `modal.py` 節**。
  暫定仕様 15 は凍結済で条項の根拠に引かない。
- **【tests_ui のテストの罠・phase 17】①`App.state` は `AppState` に占有**されているので App では **`wm_state()`** を使う。
  ②**`withdraw()` した transient 子は App の `deiconify()` に追従して再表示される**。
  ③`modal.py` の状態 3 つ（`_active_modals` / `_custody_window` / `_app_minimized`）は **`setUp` で patch** して独立させる。
- **【phase 16 の成果は正本が正】前面維持（`transient`）の規定は `spec_detail/features.md` §4.6**
  （「ネストした子は呼び出し元より前面に留まる」「呼び出し元を先に閉じたら前面維持の指定は戻らないが
  生存と grab は変わらない」）+ **`codebase_map.md` の `presentation/modal.py` 節**（第 2 引数の意味。
  **渡さなければ `transient` を設定しない**。「App より前」になるのは `PresetManagerDialog` の既定
  `parent` の話）。**暫定仕様 14 は凍結済で条項の根拠に引かない**。
  **未解決の関連問題 = [idea_18]**（`tests_ui` の Escape 依存テストが負荷下で flaky）。idea_19 は phase 17 で完了。
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
- **【phase 15 = ダイアログ後始末の確実な実行・進行中】規範は暫定仕様
  [13](../../instructions/history/13_dialog_teardown_on_close.md)（v0.4・確定済）**。要点 =
  ①**× 閉じでは Python の `destroy()` override が呼ばれない**（Tcl レベル破棄）。
  **一方 `root.destroy()` は子の Python `destroy()` を再帰的に呼ぶ**（実測。**取り違え注意**）
  ②**後始末は T1（状態・ウィジェットに触らない）と T2（ウィジェットに触る）に分ける**。
  **T1 だけを破棄イベントへ寄せる**（**子ウィジェットは親の `<Destroy>` より先に破棄される**ため、
  T2 を寄せると `TclError` になる）
  ③**登録は `suspend_hook_for_dialog(window)` が原子的に行う**（**省略時は現行と同じ**）
  ④**解除は `after(0)` 遅延**（`start_hook` が**同期で messagebox を開き得る** /
  grab 復元と競合させない）。**テストでは `update()` が必要**（`update_idletasks()` では走らない）
  ⑤**終了ガード**（`begin_shutdown()`）で終了確定後はどの経路からも再開しない。
  **`window.master.winfo_exists()` による終了判定は機能しない**（`Tk.destroy` は子を先に壊すため常に真）
  ⑥**静的検査の対象は `dialogs/` の 8 クラスのみ**。`controllers/` の try/finally 形を巻き込むと
  **phase 14 の既存静的検査と衝突する**。**引数なし呼び出しは計 15 箇所**
  （try/finally 形 5 + dialogs 8 + `key_capture.py:57` + `keyboard_window.py:270`）。
- **【phase 14 の適用は完了済】`grab_modal` は系統 A（`dialogs/` 9 クラス）・系統 B
  （`controllers/config_io/` 4 箇所）の**全 13 箇所へ適用済**（task_01 / task_02）。
  `keyseq/presentation/` に `grab_set` / `transient` の直呼びは**残っていない**。
  **ネスト経路 3 系統のテストも `tests_ui/test_nested_modal_grab.py` で完了**（task_03）。
  **契約 3 条のテストも完了**（task_04・`tests_ui/test_nested_modal_grab.py` が **8 本**）。
  **実機目視まで完了**（B4 のみ未確認・受容）。**残りは正本反映（task_06）のみ**。
  **【M-5 の教訓】`grab_modal` の `bind` は `"+"` 付きになった**ため、
  **`tk.Toplevel` を差し替えるテストダブルの `bind` は `add=None` を受ける必要がある**
  （スタブは `test_child_save_dialog.py` に 2 つ・`test_config_io_characterization.py` に 1 つの**計 3 つ**）。
  **【罠】復元先が未マップ（`winfo_viewable()` = 0）だと §3-2 で復元がスキップされ grab が `None` になる**。
  tests_ui で実ダイアログを親にするときは **`update_idletasks()` + viewable アサート**を先に置くこと
  （単独実行では通り一括実行で落ちる形の不安定さになる）。
  **【§3-6 は v0.5 で改訂済】回収機構は実装しない**。規約は **`grab_modal` を初期化の
  最後の文に置く**ことで、**静的検査テスト（`test_grab_modal_is_last_initialization_statement`）が
  これを固定している**。**`grab_modal` の後ろに処理を足すとこのテストが落ちる**ので、
  落ちたら回収機構の要否をユーザーへ諮ること（実装で握りつぶさない）。
  **テスト手法の型**: 子は親のメソッド内部で生成されるため**子の `__init__` を patch して
  `after(0, destroy)` を仕込む**。**`wait_window` / `grab_set` / `grab_current` を no-op にしない**。
  **変異検査（`restore_grab` を無効化して落ちるか）で偽 pass を排除する**。
  **`grab_modal` は各ダイアログの `__init__` の最後の文**という規約なので、
  今後 `__init__` へ処理を足すときは `grab_modal` より**前**に置く（§3-6）。
- **【phase 14 = ネストしたモーダルの grab 復元・進行中】規範は暫定仕様
  [12](../../instructions/history/12_nested_modal_grab_restore.md)（v0.4・確定済）**。要点 =
  ①**復元は子側**（ダイアログが自分の `grab_set()` の前に `grab_current()` を記録し破棄時に戻す）
  ②**「誰へ戻すか」（§3-1・記録した保持者が `None` 以外なら戻す）と「そもそも戻してよいか」
  （§3-7・破棄時点の保持者が自分か誰も居ないときだけ）は別条件**。§3-1 を「自分自身のときだけ」に
  絞ると**最も実害の大きいネスト経路 3 が復元されない**
  ③**ネスト経路は 3 系統**（プリセット編集 → 追加/編集 / アクション編集 → プリセット編集 /
  **プリセット編集 → 上書き確認**〔`preset_manager.py:364` → `hotkey_presets_io.py:42`。
  上書きを承諾しないと `save_hotkey_presets` が `False` を返しマネージャが閉じない〕）
  ④**破棄フックは `__init__` 途中の例外では発火しない**ため初期化失敗の回収を明示する（§3-6）
  ⑤**コールバック例外で子を閉じない**（§3-8）。
  ⑥**stdlib ダイアログ（`messagebox` / `filedialog`）は対象外**（未検証・実機目視のみ）。
- **【phase 14 のテスト上の罠】** `tests_ui/test_child_save_dialog.py` は `tk.Toplevel` を
  `_FakeSaveDialog`（`:149`）へ patch し `grab_set` / `wait_window` とも no-op なので
  **grab の回帰基準にならない**（フローの回帰基準にはなる）。スタブは `winfo_exists` /
  `grab_current` を持たないため拡張要否の判断が要る。`tests_ui/test_app_ui_flows.py:72`・`:1327-1338` は
  `object.__new__(PresetManagerDialog)` + `destroy` 直呼びなので、**復元処理は属性未初期化でも落ちないこと**。
  `grab_current()` の観測例は `tests_ui/test_quarantine_manage_flow.py:286`。
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
- 未着手 idea: **idea_13（external_keyboard_layouts のパス基準の非対称・優先度低）** /
  idea_03（hotkey 保存時正規化・優先度低）/ idea_09（レガシー settings/ フォールバック・優先度低）/
  idea_11（別名保存の複製ロールバック・優先度低）。**idea_10 は phase 14 で着手中**。**idea_15 は phase 13 で完了**・**idea_14 は phase 12 で完了**・**idea_12 は phase 11 で完了**・
  **idea_07 は phase 10 で完了**・**idea_08 は phase 09 で完了**。
  保留 idea: idea_04 / idea_06（**残る着手条件は「共通化の実需」1 つのみ**）。
- 過去の判断は `.claude_data/state/decisions.md`（アーカイブ索引）+ `decisions_archive/<phase>.md`。
  完了済の直近 3 件: 11_orphan_child_file_sweep / 12_config_service_public_surface /
  **13_contracts_boundary_ast_coverage**。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
