# decisions.md

> 採用 / 修正して採用 / 保留 / 除外 の判断を時系列で記録。
> 後続フェーズで「なぜそうしたか」を辿れるようにする。
> **完了フェーズの判断は `decisions_archive/<phase>.md` へ集約し、本ファイルには索引のみ残す。**

---

## アーカイブ索引

| フェーズ | アーカイブ | 概要 |
|---|---|---|
| 01_view_ref_cleanup | [01_view_ref_cleanup.md](decisions_archive/01_view_ref_cleanup.md) | View 参照の後始末（2026-07-17 完了）。status_bar 生やしのローカル変数化 / trigger_list alias 削除。**action_list alias は据え置き**（production が使う生きたパスのため。取り違え注意）。refactor_check: 不要 |
| 02_hotkey_validation | [02_hotkey_validation.md](decisions_archive/02_hotkey_validation.md) | hotkey 検証を presentation → domain/application へ層移設（2026-07-18 完了・挙動不変）。設計案 C（domain=文法検査 / application=HotkeyService）/ 層の逆転を解消 / 安全網の特性テスト。**正本昇格は不要**（spec_detail に記述なし＝担当層は codebase_map.md が正）。実機目視で判明したアクション hotkey の保存非対称は **idea_03 へ分離**し §6-11 を補正。refactor_check: 不要 |
| 03_startup_font_settings_cleanup | [03_startup_font_settings_cleanup.md](decisions_archive/03_startup_font_settings_cleanup.md) | 起動設定/フォント3メソッドの整理（2026-07-20 完了・挙動不変）。coerce→`theme.py`純関数 / 起動設定ローダ→新規`startup_settings.py`（config_service直依存・未知キー全保持・on_read_error注入） / `set_ui_font_delta`案A分割 / UiVars引数化。**案B（FontSettingsController）は将来idea化**。**正本昇格は不要**（spec_detailに記述なし＝担当層はcodebase_map.mdが正）。refactor_check: 不要 |
| 04_config_io_controller_split | [04_config_io_controller_split.md](decisions_archive/04_config_io_controller_split.md) | `config_io_controller.py`（598行）を `controllers/config_io/` の**6クラスへ分割**（2026-07-26 完了・挙動不変）。§4=案B（呼び出し元30箇所差し替え・`config_io_controller.py`削除・**config_io名消滅**・互換レイヤーなし）/ §5=案1（共通化しない）/ §1「既存の不整合」（E の source_path 分断）は**直さず移設**→idea_05。特性テストは task ごとに境界mock / アクセサ切替で調整（**アサーション非緩和**）。**正本昇格は不要**（spec_detailに config_io 記述なし＝担当層はcodebase_map.mdが正）。refactor_check: 不要（M3 の同型3ブロックは既存重複の移設で idea_06〔D/E/F共通化・保留〕がカバー済＝既知。他は非該当） |
| 05_keymap_set_new_and_default_dir | [05_keymap_set_new_and_default_dir.md](decisions_archive/05_keymap_set_new_and_default_dir.md) | 新規作成と保存先ディレクトリの整理 = 保存系リデザイン **Phase α**（2026-07-28 完了・**挙動変更**）。新規作成/Import 成功/空起動で `keymap_set_path` を空にし、空パスの保存は別名保存へ分岐。既定保存先を固定 `default.json` から**ディレクトリ `config/user/keymap_sets/`** へ移し、起動時にディレクトリ骨格を一括作成。死にフラグ `prompt_if_missing` は新規出力停止（**既存値は残置許容・`pop` しない**）。正本 `data_schema.md` §5.4・§5.6 へ昇格済。**未対応の残存経路 = [idea_09](../../instructions/backlog/idea_09_legacy_settings_save_path_fallback.md)**（レガシー `settings/` 配下選択時の `default.json` フォールバック・ユーザー判断で後続送り）。refactor_check: 不要 |
| 06_child_file_save_dialog | [06_child_file_save_dialog.md](decisions_archive/06_child_file_save_dialog.md) | 子ファイル保存の確認ダイアログと参照元記録 = 保存系リデザイン **Phase β**（2026-08-03 完了・**挙動変更＋スキーマ追加**）。keymap_set の「保存」を**子ごとに 保存/別名保存/保存しない を選べる一覧ダイアログ**へ置換し、子JSON へ `_parent_refs`（直接の上位）を記録して誤爆上書きを防止。**実機目視 5 回**で暫定仕様を v0.3〜v0.7 へ改訂（一覧再表示の廃止と A2 / canonical identity / 依存確認の提示条件縮小と 4 択・deferred index / v0.4-I は keymap・sequence 限定 / 個別保存のパス解決と上位 dirty 化 / 個別トリガー一覧保存の計画化 / 「例を復元」= 中身のある新規作成 / 共有状況の表示文言）。正本 `data_schema.md` §5.4・§5.6・§5.7・**§5.8** + `features.md` §4.6 + `codebase_map.md` へ昇格済。フェーズ完了レビュー由来の **task_19 / 20** で個別保存・個別読込の source_path を **config 相対へ統一**（§5.7 に実装を追従）。**内包**: idea_05。**後続**: idea_07（参照元の掃除・着手可）。refactor_check: **推奨**（M1/M2/M3/M4 該当 → 提案書 [05_refactor_child_file_save_dialog](../../instructions/modified_proposal/05_refactor_child_file_save_dialog.md)・**未承認**。M3 は idea_06 がカバーする既知領域として除外）|

※ 下記「2026-07-15〜07-17 (計画04)」はフェーズではなくリファクタ計画
（`instructions/modified_proposal/04_widget_split_plan.md`）の記録のため、本ファイルに残置している。

## 凡例
- **採用**: 仕様適合・依存方向・責務に問題なし、そのまま取り込む
- **修正して採用**: 概ね適合、小さな修正で取り込む
- **保留**: 後続タスクの内容、現タスクには不要
- **除外**: 仕様逸脱が大きい、責務・依存方向を壊す

---

## 2026-07-15〜07-17 (計画04: Widget分割・フォルダ再編・挙動不変)

規範: `instructions/modified_proposal/04_widget_split_plan.md`（W0〜W7 / 1項目=1コミット）。
ブランチ `claude/w1-physical-verification-647a57`。全項目 完了・手動確認まで完了。

### 【案A】計画書の条項間矛盾（views.py と views/ パッケージの共存不可）
- W2 着手時に検出。計画 §1.1/W2 は `views/` パッケージ新設を要求する一方、W3〜W6 は既存 `views.py` の
  存続（re-export 置き場）を前提としていた。**Python では同一ディレクトリの `views.py` と `views/` は
  共存できず**（パッケージが優先されモジュールが覆い隠される）、両立不能だった。
- 対応: `views.py` を**内容不変で `views/__init__.py` へ移設**し、既存 import
  （`from keyseq.presentation.views import FullView, CompactView`）を無傷に保つ → **修正して採用**（ユーザー承認）
- 以降、計画書中の `views.py` は **`views/__init__.py` と読み替える**（W3/W4 の re-export も、W6 の
  「views.py 削除」= 「re-export 除去 + 空パッケージマーカー化」も __init__.py 側で実施）。
- 根拠: 計画意図（views/ パッケージ化）を保ちつつ最小差分・全 import 無傷。代替案（パッケージ名変更＝
  目標構成と乖離 / W3〜W6 の前倒し＝1項目1コミット違反）はいずれも劣ると判断。

### 【W2】`_bind_menu_shortcuts` を menu_bar.py へ移すか
- `build_menu_bar(app)` と `bind_menu_shortcuts(app)` の **2関数に分離して移設** → **採用**
- 根拠: `_build_menu` は `__init__` と `set_ui_font_delta`（フォント変更時の再構築）の2箇所から、
  `_bind_menu_shortcuts` は `__init__` の1箇所からのみ呼ばれる。**1関数に束ねると再構築時に
  `add="+"` バインドが重複し挙動が変わる**ため、呼び出し頻度差を保持した。
- ショートカットハンドラ（`_on_shortcut_*` / `_is_menu_shortcut_enabled`）は App の capture/focus 状態を
  参照するため **App に残置** → **採用**

### 【W3/W4】分割で失われる外部属性契約を alias で保持
- 分割前の View が直接公開していた `trigger_list`（full/compact）・`action_list`（full）を、
  production（`trigger_panel_controller`）と tests_ui が `app.<view>.<attr>` で参照していた。
  Widget 内へ移動したため **View 側に alias を置いて外部契約を保持** → **採用**（reviewer 判定）
- 根拠: 計画 §4-2（挙動変更禁止）・§4-6（tests_ui のアサーション変更禁止）に照らし、
  コントローラ改修（W5相当=スコープ外）やテスト変更（禁止）なしで契約を保つ最小措置。
- W5 での再確認結果: **trigger_list alias は残置**（tests_ui が `app.full_view.trigger_list` /
  `app.compact_view.trigger_list` を参照。テスト変更禁止のため）。`action_list` も
  `app.full_view.action_list` のまま **据え置き**（§1.3-2 の「App→View→Widget パス」を既に満たすため）。

### 【W5】生やし解消の分類判断（§1.3）
- **登録方式**（複数View共有）: フック2ボタン組 / レイアウトコンボ / トリガー一覧 → **採用**
  （走査順は登録順 = full→compact。旧実装の更新順を保持）
- **App→View→Widget パス**（単一View所有）: keymap 系 / run_to_end_delay_entry → **採用**
- **write-only（読み手なし）**: topmost_chk / compact_btn / suppress_chk / run_to_end_chk / keymap_add_btn は
  `self.xxx` 化のみ → **採用**。特に `topmost_chk` は full/compact が同一 App 属性へ二重代入する
  **事故的共有（後勝ち）**だったが、読み手が無いため所有化で衝突が自然消滅した。
- **status_bar.py の `app.runtime_status_frame` / `app.status_bar`** → **保留**（W5 §1.3 の対象外＝
  ボタン/入力ウィジェットの逆流ではない。同種の生やしとして残存。次期課題候補）
- 検証: reviewer が text/state/更新順を1文字単位で突合し不一致なし + codex-adversarial-reviewer が
  登録順・タイミング・ライフサイクルを approve。手動確認4項目（省略禁止）もユーザー OK。

### 【W7】app.py 行数の目安未達（**489行** / 目安300行未満）
- **超過を事実として報告し、残留ロジックは移動しない** → **保留**（計画 §W7-1 の指示どおり次期課題へ）
- 主因は `__init__` の配線 約122行＝「生成と配線」として正当な残留。
- **【計測上の注意】計画書 §W7-3 が指定する `(Get-Content app.py | Measure-Object -Line).Lines` は
  PowerShell の仕様で空行を数えないため 413 を返すが、これは「空行を除いた行数」であり実際の
  ファイル行数ではない。総行数は `wc -l` で 489 行（空行除くと 412 行）。
  今後この計測を行う際は `wc -l` かつ/または空行の扱いを明示すること**（当初 413 行と誤報告し訂正した）。
- 次期課題（どの分類にも属さない残留ロジック。本計画の範囲外）:
  1. `validate_hotkey` の実装本体（約31行）→ domain/application へ移し App は薄い委譲に
  2. `_load_startup_settings`（約17行）→ ConfigIoController / ConfigPaths へ
  3. `_coerce_font_delta`（約10行）→ theme.py 等へ
  4. `set_ui_font_delta`（約17行）→ フォント適用 + 永続化 + フラッシュの責務混在を切り出し
  （上記を移しても約414行の見込みで、300行には届かない）

### 【計画04 完了時】/refactor_check 判定
- **不要**（M1〜M6 いずれも該当なし。対象: keyseq/ 配下 27ファイル / +690・-574行）→ **採用**
- 提案書は起票しない。M3（同型ブロック増殖）は Full/Compact の類似 Widget が各2インスタンスに留まり
  「3個目以降のコピー」に非該当（計画 §4-1 が View 間の Widget 共通化を明示的に禁止しており、
  2インスタンスは設計上の意図的分離）。M5（申し送りコメント）も新規追加0件。
- なお本フェーズは挙動不変リファクタであり、`/refactor_check` の「挙動不変が前提のフェーズは
  スキップしてよい」に該当したが、ユーザー判断で実行した。

---

## 2026-08-03〜 (計画05: config_service / keymap_set_io の分割・挙動不変)

規範: `instructions/modified_proposal/05_refactor_child_file_save_dialog.md`
（項目 0 = 安全網 / 1 = `config_service.py` から保存計画の実行を切り出す / 2 = `_collect_child_save_plan` の分割。
**1 項目 = 1 コミット**）。Phase β（phase 06）完了時の `/refactor_check` = 推奨 の産物。

### 【起票時】実施形態と順序 → **計画として実施・γ より先**（ユーザー確定 2026-08-03）
- **実施形態**: 選択肢は「①計画として実施（計画04 と同じ運用）②独立ミニフェーズ phase 07
  ③枝番フェーズ 06b」→ **①を採用**。
  **根拠**: フェーズ運用（暫定仕様先行モード）が重いのは**設計を確定させる工程**
  （暫定仕様の起票 → 敵対的レビュー → ユーザー確定）を内包するためだが、提案書 05 には
  対象・変更方針・完了条件・リスク・依存・安全網がそろっており**そのまま確定設計として機能する**。
  加えて `/refactor_check` の規定で「挙動保存が原則・挙動変更は範囲外」と制約が閉じており、
  設計判断の余地がほとんどない。フェーズ末の `/refactor_check` も本計画自体が
  refactor_check の産物のため実質空振りになる。
  ②③を採らないことで **γ = phase 07 / プリセット = phase 08 の対応表を触らずに済む**。
- **順序**: **γ（phase 07）より先に実施**（ユーザー確定）。
  **根拠**: ①tests 145 / tests_ui 159 が全 green + 実機目視 R1〜R11 OK 直後で、
  「挙動不変」の基準線が最も明確 ②γ は `config_service.py`
  （`_build_runtime_data_from_split` の hook キー読み出し・正規化）を触るため、
  1650 行のまま載せると後の分割差分が膨らむ ③γ が触るのは「hook キーの解決」、
  本計画が切り出すのは「保存計画の実行」で**責務が別のため切り口が変わりにくい**。
- 項目 2（`_collect_child_save_plan` の分割）は γ とほぼ無関係のため、
  **途中で止めて γ へ移ることも可**とする。

### 【項目 0】安全網の確認 = **OK・追加テスト不要**（2026-08-03）
- バイト列比較 21 箇所 / `test_save_plan.py` 12 件（旧索引維持・書き込み順序・deferred index）+
  `test_dependency_query.py` 5 件 / ダイアログ駆動 46 件。移設対象の private ヘルパは
  **テストから直接呼ばれていない**（`save_runtime_data` 経由）。
- **発見 1 → 採用**: `patch("keyseq.application.config_service.os.path", ntpath)` が **4 箇所**あり、
  クラスを `config_service/config_service.py` へ置くとパッチ対象が外れて壊れる。
  → **クラス本体を `config_service/__init__.py` へ置く**（計画04 案A と同じ手）。4 テストは無修正で通る。
- **発見 2 → 抽出方式を確定**（ユーザー確認 2026-08-03・観点は「後で把握しやすい方」）:
  対象関数は `self.` を 1〜15 個参照するため**引数への全展開は不採用**（シグネチャが読めなくなる）。
  **Mixin も不採用**（定義位置が MRO 依存で把握しにくい＝要望と逆行）。
  → **`service` を第 1 引数に取るモジュール関数**（`self.X` → `service.X` の機械的置換）。
  `_sequence_save_path_changed`（self 依存 0）のみ純粋関数化。

### 【項目 1】分割範囲 → **A+B+C+D・2 コミット**（ユーザー確定 2026-08-03）
- 実測: A 保存計画の実行 297 行 / B payload 構築 399 行 / C 保存先の解決・命名 180 行 /
  D split 読込 204 行。**A+B のみでは親 約 982 行**で完了条件「600 行未満」に届かず
  （提案書起票時の見積もりが甘かった）。**A+B+C+D で親 約 598 行**。
- **1a = A + B → 1b = C + D** の 2 コミットに分け、各段階でフル検証 + reviewer を通す
  （一括だと退行時の切り分けが難しいため）。

### 【項目 1a】完了（2026-08-03）
- `config_service.py` → **`config_service/__init__.py`**（内容不変で移動）+ `save_plan_execution.py`（A・318 行）
  + `split_payloads.py`（B・407 行）。親は 1678 → **1011 行**。
  移設関数は `service` を第 1 引数に取るモジュール関数、`sequence_save_path_changed` のみ純粋関数。
  公開 3 メソッド（`save_runtime_data` / `resolve_child_save_targets` /
  `find_dependency_blocked_sequences`）は**薄い委譲として親に残置**（外部契約のため）。
  private ヘルパのラッパは**作らない**（互換レイヤー禁止）。
- 検証: compile clean / tests **145 pass** / tests_ui **159 pass**（**1a 前後で同数**＝テスト追加削除なし）/
  smoke pass / `patch(...config_service.os.path, ntpath)` の **4 テストも pass**（パッケージ化でパッチ対象が
  外れていないことの担保）。
- reviewer = **完了可**。元実装との全文突合で `self.X` → `service.X` の機械的置換のみ・分岐 / 書き込み順序 /
  エラーメッセージが不変であることを確認。指摘 = 未使用 import 6 個の残置（**メインが直接削除**・
  再検証で 145/159/smoke pass）。
- **参考として記録**: ntpath パッチの 4 テストは `__init__.py` に残る `canonical_path` / `_merge_parent_ref`
  （= 1b 対象の C 系）だけを経由しており、移設側の `import os` はパッチ対象外。
  将来 Windows パス識別のテストを移設側へ広げるならパッチ対象の拡張要否を再検討する。

### 【項目 1b】完了（2026-08-03）
- `save_path_resolution.py`（C・213 行）+ `split_loading.py`（D・289 行）を新設。親は 1011 → **551 行**
  （完了条件「600 行未満」を満たす）。方式は 1a と同一（`service` 第 1 引数のモジュール関数・
  private ヘルパのラッパを作らない）。
- **parent に残した判断**（移すと壊れる / 責務が跨る）:
  ① `canonical_path` / `is_path_within` / `to_config_relative_or_absolute` /
  `_resolve_config_relative_path` / `_normalize_path_separators` / `_merge_parent_ref`
  = **ntpath パッチの 4 テストが `__init__` の名前空間で `os.path` を見ている**ため移動不可。
  ② `_normalize_sequence_payload`（`load_sequence_file` / `save_sequence_file` からも使用）と
  `_generate_keymap_id`（`load_keymap_file` からも使用）= 読込専用ではないため D に含めない。
- **例外扱い 2 件**: ① `slugify_file_stem` は**公開メソッド**（`config_paths.py` から使用）のため
  本体を C へ移し親には薄い委譲を残す ② `_normalize_external_keyboard_layouts` は
  `_build_runtime_data_from_split` 専用のため D へ含めた（提案書の列挙外だが読込責務）。
- **テスト 2 箇所を修正**（`tests/test_config_service.py`）: `_default_trigger_set_path` /
  `_is_default_trigger_set_area` を直接呼ぶ箇所を `save_path_resolution.<新名>(self.service, ...)` へ。
  互換ラッパを作らない方針の帰結であり、挙動・アサーションは不変。
- 検証: compile clean / tests **145 pass** / tests_ui **159 pass** / smoke pass /
  ntpath パッチの **4 テストも個別 pass**。reviewer = **完了可**（AST 正規化差分で機械的置換のみを確認・指摘なし）。
- → **項目 1 完了**。次は項目 2（`keymap_set_io._collect_child_save_plan` の分割）。

### 【項目 2】完了（2026-08-03）= **計画05 完了**
- `_collect_child_save_plan`（130 行）を手順の並びへ分解。**新規ファイルは作らず**同一ファイル内の
  private メソッド抽出のみ（提案書どおり）。抽出 = `_collect_rows_and_targets` /
  `_recalculate_for_trigger_target` / `_ask_trigger_set_dependency_action` /
  `_apply_trigger_set_action` / `_resolve_trigger_set_dependency` / `_blocked_sequences` / `_build_plan`。
- **ループ再入は `_RETRY` センチネル**（モジュール定数）で表現。
  元の `if not action: (rows が空なら return / そうでなければ pending 初期化して continue)` を
  「`_resolve_trigger_set_dependency` が `_RETRY` か結果タプルを返す → 呼び出し側が `continue`」へ写した。
  **戻り値が 3 系統（キャンセル / 再試行 / 確定）**あるため、`None` の多重利用を避けてセンチネルを採用。
- **重複の統合**: 再計算 → 上書き確認のブロックが 2 箇所に同型で存在したため
  `_recalculate_for_trigger_target` 1 本にまとめた。元は 1 回目が `choices` を更新・2 回目が捨てる
  差があったが、**2 回目は以降 `choices` を読まない**ため呼び出し側で捨てる形で等価。
  `_trigger_target_changed` のガード（1 回目のみ `trigger_entry and`）は**呼び出し側に残す**
  （「再計算不要」と「キャンセル」を 1 つの戻り値で表さないため）。
- `build_save_plan(data=self._app.data, ...)` の 5 箇所は `_build_plan` へ機械的に置換。
- 検証: compile clean / tests **145 pass** / tests_ui **159 pass**（うち `test_child_save_dialog` 46 件は
  **無修正 pass** = ダイアログ駆動の挙動が不変）/ smoke pass。無限ループ・ハングなし。
- reviewer = **修正して採用**。制御フロー突合（ダイアログ呼び出し順序・再入条件・早期 return・通知合成）は
  全一致で挙動不変を確認。指摘は**行数のみ**（`_collect_child_save_plan` / `_resolve_trigger_set_dependency` が
  44 行で完了条件 40 行超過）→ **メインが是正**（`_blocked_sequences` 抽出 + シグネチャ折り返し）し、
  39 行 / 38 行へ。再検証で 145 / 159 / smoke pass。
- **残る 40 行超は `save_keymap_set_to`（46 行・本タスクの対象外・無変更）**。必要なら別途 idea 化。

---

## 2026-08-03〜 (phase 07 = 保存系リデザイン Phase γ: hook キーの全体デフォルト化)

規範: `instructions/phase/07_hook_keys_global_default/phase.md`。
主入力（確定設計）= `instructions/history/06_hook_keys_global_default.md`（v0.2・ユーザー確定済 2026-07-27）。
モード = **暫定仕様先行モード**。番号対応: **phase 07 / 暫定 06 / decisions_archive 07**。

### 【起票】タスク分割と読むファイルの補正（2026-08-03）
- task_01 スキーマ/移行判定 → 02 キー解決点 → 03 保存時挙動 → 04 全体デフォルト更新 API（成否付き）→
  05 チェック UI → 06 所有者切替 capture → 07 統合確認 → 08 正本反映、の 8 タスク。
  **02 と 03 は 01 完了後なら並行可**。
- **暫定仕様 06 の「現状監査」の行番号は計画05 の分割で無効**になっていたため、phase.md
  「このフェーズで読むファイル」で現在の所在へ差し替えた（読込 = `config_service/split_loading.py` /
  保存 = `config_service/split_payloads.py`）。reviewer の整合確認で実ファイルとの一致を検証済み。

### 【task_01】完了（2026-08-03）
- `domain/config.py` のみ変更。`DEFAULT_CONFIG` へ `hook_keys_individual: False` +
  純関数 `resolve_hook_keys_individual(source)` を新設し、`ensure_config_compatibility` の
  hook キー正規化**直後**で呼ぶ（正規化後の値で判定させるため位置が重要）。
- **明示フラグの有無は `in` で判定**する（`.get()` の真偽で見ると `false` とキー無しを区別できず
  移行規則が壊れる）。フラグがあれば中身を見ずに `bool()`、無ければ
  「正規化後どちらか非空 → ON」。
- **冪等性を要件に含めた**: 「フラグ True のまま両キーが空」で False へ落ちると、
  暫定仕様 §2 の「ON→OFF で個別値を内部保持」が壊れるため。テストで固定済み。
- **split 経路ではこの移行は発火しない**（`build_runtime_data_from_split` は
  `new_default_data()` = フラグを含む土台から始まるため、最後の
  `ensure_config_compatibility` 時点でフラグが常に存在する）。
  **生の keymap_set dict に対して `resolve_hook_keys_individual` を呼ぶのは task_02 の責務**。
- 懸念していた**保存 JSON バイト列比較テストの破壊は発生しなかった**
  （keymap_set への書き出しは `split_payloads.py` の明示キー列挙のため）。
- 検証: compile clean / tests **155 pass**（145 + 追加 10）/ tests_ui 159 pass / smoke pass。
  reviewer = **完了可・指摘なし**。

### 【task_02】完了（2026-08-03）
- **キー解決点を 2 本の関数に集約**: `split_loading.load_global_hook_keys(service, config_root)`
  （config.json の全体デフォルト読み出し・正規化・失敗時 `("", "")` へ縮退）と、
  公開 API `ConfigService.apply_global_hook_key_defaults(runtime, config_root)`（OFF のみ注入・冪等）。
  **フック層（`input_router` / `hook_controller` / `keyboard_window` / `app.py`）は無変更**
  ＝ 暫定仕様 §3 の「常に解決済みの値を見る」を満たす。
- **移行判定に渡すのは生の `keymap_set` dict**（task_01 の申し送りどおり）。hook キーのコピーループの
  タプルへ `hook_keys_individual` を**追加しない**（明示代入で一本化・二重経路を作らない）。
- **注入は読込時だけでは足りない**（受入条件 2「新規作成で再設定不要」）。新しい runtime を生成する
  presentation 3 箇所（`keymap_set_io.new_config` / `restore_default` /
  `startup_io.load_startup_and_config` の空データフォールバック）からも API を呼ぶ。
  **`app.py:76` は対象外**（直後に `load_startup_and_config` が必ず上書きするため）。
- **tests_ui 3 件の期待値を更新**（`test_config_io_characterization_keymap_set_startup.py`）。
  スタブ dict（`{"empty": True}` / `{"d": 1}`）へ注入結果の空 hook キー 2 個が加わったため。
  **実装ではなくテスト側の追従**であり、実 runtime では `new_default_data()` が既に両キーを持つので
  実挙動の変化ではない（config.json 未設定時の注入値は空文字）。
- 検証: compile clean / tests **164 pass**（155 + 追加 9）/ tests_ui 159 pass / smoke pass。
  **保存 JSON のバイト列比較テストは無修正で pass**（本タスクは保存経路を触らない）。
  reviewer = **完了可・指摘なし**。

### 【task_03】完了（2026-08-03）
- 保存時の分岐は `split_payloads.build_keymap_set_payload` の **1 関数のみ**に閉じた。
  ON = 個別値をそのまま保存 / OFF = `hook_stop_key` / `hook_toggle_key` を **`""`** で書き出し
  `hook_keys_individual: false`。**キー自体は 3 つとも常に出力**（既存キー削除禁止）。
- **OFF 時に書くのは `""` であって `runtime.get(...)` ではない**（最も壊しやすい点）。
  OFF の runtime は task_02 で全体デフォルトが注入済みのため、そのまま書くと
  **全体デフォルトが keymap_set へ焼き付き**、次回読込で移行判定が「個別値あり」と誤発火する。
- **判定は `resolve_hook_keys_individual(runtime)` を通す**（`.get()` の真偽で見ない）。
  `build_keymap_set_payload` を直接呼ぶ経路（テスト等）はフラグを持たないため、
  純関数側の移行規則に載せることで**フラグ無しの旧 runtime は従来どおり個別値を保存**（後方互換）。
- **`runtime` は書き換えない**（payload 生成は副作用なし）。runtime の hook キーは
  OFF のとき解決済みの全体デフォルトを保持しており、フック層がこれを直読みするため。
- **tests_ui 1 件が fail → テスト側追従で解消**（想定内の唯一の破壊）:
  `_prepare_loaded_keymap_set` が `hook_keys_individual` 未設定のまま `hook_stop_key="f12"` を置いており、
  新契約では保存時に空文字化されて**既定復元後のファイルとバイト一致**してしまい
  `test_restore_default_overwrites_named_parent_and_trigger_set_but_not_sequences` の
  `assertNotEqual` が落ちた。フィクスチャの意図（個別指定された停止キー）どおり
  `hook_keys_individual = True` を明示して解消。**実装側の問題ではない**。
- **申し送り（task_06）**: 「OFF 保存後にセッション内保持していた個別値も破棄する」処理は本タスク範囲外。
  保持先が UI 側の状態のため task_06 が担当する。
- 検証: compile clean / tests **168 pass**（164 + 追加 4）/ tests_ui 159 pass / smoke pass。
  reviewer = **完了可・指摘なし**。

### 【task_04】完了（2026-08-03）
- **全体デフォルトの書き込み API は presentation（`StartupIo`）に置いた**。
  `write_startup` を `-> bool` 化（成功 True / 例外捕捉 False。既存の `base` 組み立て・
  `coerce_font_delta`・`showerror` は不変）+ `write_global_hook_keys(*, stop_key, toggle_key) -> bool` を新設。
  正規化は `normalize_key_name`（presentation → domain の直接 import は既存 14 ファイルの踏襲）。
- **書き込み経路を `write_startup` の 1 本に集約した理由**（最も壊しやすい点）:
  `_startup_settings`（in-memory の起動設定）と config.json が乖離すると、次の `write_startup`
  （フォント変更・keymap_set パス記録）が**古い `_startup_settings` を土台に上書きして hook キーを消す**。
  そのため ConfigService へ独自の read-modify-write な保存 API を作らなかった。
- **失敗時の旧値維持**は `self._app._startup_settings = base` が `try` 内・保存成功後にある
  既存構造で成立する。**この代入位置を動かさない**（受入条件 7）。
- keymap_set 保存カスケード（`keymap_set_io.py:116` → `build_startup_payload`）は `startup_data` を
  丸ごとコピーするため**全体デフォルトは自動的に維持される**。hook キー用の分岐を足さず、
  テストで固定した（確認 5）。
- **API を呼ぶコードは書いていない**（UI 配線 = task_05 / capture とランタイム反映 = task_06）。
- タスク定義の記述ミス 1 件を是正: 読み出し API を `ConfigService.load_global_hook_keys` と書いていたが
  実体は `split_loading.load_global_hook_keys(service, config_root=...)`（+ 公開 API は
  `apply_global_hook_key_defaults`）。Codex が実装時に指摘し、定義側を修正した。
- 検証: compile clean / tests **168 pass**（presentation 限定のため増減なし）/
  tests_ui **165 pass**（159 + 追加 6）/ smoke pass。reviewer = **完了可・指摘なし**。

### 【task_05】完了（2026-08-03）
- **チェック UI は presentation に閉じた 4 ファイル**: `ui_vars.hook_keys_individual_var`（BooleanVar・
  full / compact が**同一インスタンスを共有**）/ `app._sync_control_vars_from_data` へ 1 行（data → Var）/
  `App.toggle_hook_keys_individual`（Var → data + dirty）/ full・compact の `hook_frame` に
  `ttk.Checkbutton`（`full_hook_line2` / `compact_hook_line2` の row=2・grid 構造は不変）。
- **同期の入口は 2 本だけ**（data → Var = `_sync_control_vars_from_data` / Var → data =
  `toggle_hook_keys_individual`）。`apply_loaded_data_to_ui` / `new_config` / `restore_default` は
  既に前者を呼ぶため**無変更で追従**する。
- **チェック操作は dirty にする**。`hook_keys_individual` は keymap_set に保存される値のため。
  暫定仕様 §4 の「dirty 非汚染」は **OFF 時のキー編集**に対する要件でありチェック操作は対象外。
- **compact のチェックは表示専用（`state="disabled"`・`command` 無し）＝ユーザー確定（2026-08-03）**。
  compact のフックキーは既に readonly Entry のみで capture / clear を持たない＝「compact は表示のみ」
  という既存方針に合わせた判断。**確定済みのため task_07 で再確認しない**。
- **reviewer 指摘 1 件を修正して採用**: 確認 3（移行で ON になる keymap_set を読むとチェックが ON）が
  `app.data` への直接代入 + `apply_loaded_data_to_ui` の直呼びで代替されており、**移行判定を
  バイパスしていた**。実ファイル（フラグ無し・stop のみ非空 / 両方空）を
  `load_runtime_data_from_keymap_set_path` で読む特性テストをメインで追加して解消。
- 検証: compile clean / tests **168 pass**（presentation 限定のため増減なし）/
  tests_ui **169 pass**（165 → Codex 追加 3 → 指摘対応 +1）/ smoke pass。

### 【task_06 起票時】task_06 を 06 / 06b へ分割（2026-08-03）
- phase.md の task_06 は「所有者切替 capture + dirty 非汚染 + ON⇄OFF 表示切替 + 個別値の内部保持」を
  1 タスクに束ねていたが**範囲が広すぎる**ため、**06（書き込み先の切替と dirty 非汚染）**と
  **06b（表示切替と個別値のセッション内保持・OFF 保存後の破棄）**へ分割した。
  phase.md のタスク表と依存の並びも更新済み。

### 【task_06】完了（2026-08-03）
- **hook キーへの書き込み点を `SingleKeyCaptureController._apply_key` の 1 本へ集約**した
  （従来は `clear()` と `on_keypress()` の 2 箇所に散っていた）。
  ON = `app.data` 更新 + Var 反映 + dirty（従来どおり）/ OFF = `write_global_hook_keys` で
  config.json を更新し、**成功時のみ** `app.data` と Var を確定（§3 の即反映）。
- **dirty 非汚染は `DirtyStateTracker.capture_dirty_snapshot` / `restore_dirty_snapshot`**
  （記録対象は `is_dirty` / `config_dirty` の 2 つ。個別 dirty フラグは capture が触らないため対象外）。
  **`try` / `finally` で復元**するため例外経路でも汚れない（phase.md レビュー方針 3）。
  ユーザー案（暫定仕様 §4 の「OFF 前の dirty を記録し操作後に復元」）をそのまま実装したもので、
  「OFF なら `set_dirty` を呼ばないだけ」に簡略化していない（間接的な dirty 化にも耐えるため）。
- **既存挙動の維持**: `clear()` の「旧値が空なら dirty にしない」は `mark_dirty=bool(old)` で表現。
  OFF 経路では `mark_dirty` は使われない（snapshot 復元が優先されるため無害）。
- **OFF では 2 キーとも書く**（`write_global_hook_keys` が 2 キー同時指定の API のため）。
  更新しない側は `app.data` の現在値＝現在の全体デフォルトをそのまま再書き込みする。
- 保存失敗（偽 or 例外）時は **runtime も Var も書き換えない**（受入条件 7）。
  エラー表示は `write_startup` の `showerror` が既に行うため二重に出さない。
- 検証: compile clean / tests **168 pass**（presentation 限定のため増減なし）/
  tests_ui **173 pass**（169 → +4）/ smoke pass。reviewer = **完了可・指摘なし**。

---

## 運用メモ

- 1 タスク完了時に reviewer 判定をここへ転記する
- 想定外の先行実装を発見した場合の判定もここへ記録する
- 後続フェーズの設計で参照する
