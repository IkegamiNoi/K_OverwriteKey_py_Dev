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
| 07_hook_keys_global_default | [07_hook_keys_global_default.md](decisions_archive/07_hook_keys_global_default.md) | 停止/トグルキーの全体デフォルト化 = 保存系リデザイン **Phase γ**（2026-08-05 完了・**挙動変更＋スキーマ追加**）。`config/config.json` に全体デフォルト 2 キー、keymap_set に `hook_keys_individual` を追加し、**キー解決点を keymap_set 読込時の 1 点に集約**（`split_loading.load_global_hook_keys` + `ConfigService.apply_global_hook_key_defaults`）して**フック層を無変更に保った**。OFF 時のキー編集は config.json を**成否付き**で更新し keymap_set を dirty にしない（dirty スナップショットの記録・復元）。OFF 保存で個別値を空文字化＋フラグ false（**復活は保存前セッション内のみ**）。統合レビューで**両レビュアーが独立に指摘した Import 経路の注入漏れ**ほか A〜D を task_07b で是正。正本 `data_schema.md` **§5.9** + `key_input.md` **§7.6** + `codebase_map.md` へ昇格済。**指摘 E（キー衝突検証はカレントセット内に閉じる / 「明示 false + 非空個別値」は個別値が失われる）は実装を変えず契約として明記**。refactor_check: **推奨**（M4 該当 → 提案書 [06_refactor_hook_key_pair_enumeration](../../instructions/modified_proposal/06_refactor_hook_key_pair_enumeration.md)・**未承認**。M3 は候補送り）|

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

## 2026-08-06〜 (計画06: hook キー 2 本の「対の列挙」を 1 箇所へ寄せる・挙動不変)

規範: `instructions/modified_proposal/06_refactor_hook_key_pair_enumeration.md`
（項目 0 = 安全網 / 1 = 対の列挙の集約。**1 項目 = 1 コミット**）。
Phase γ（phase 07）完了時の `/refactor_check` = 推奨（M4 のみ該当）の産物。

### 【起票時】実施形態 → **(b) 次フェーズ前の独立ミニ計画 = 「計画06」**（ユーザー確定 2026-08-06）
- 提案書の選択肢 (a) phase 07 末の追加タスク / (b) 独立ミニフェーズ / (c) 見送り のうち **(b)** を採用。
  運用は**計画05 と同じ**（提案書自体を確定設計として扱う / **フェーズ番号を消費しない** /
  1 項目 = 1 コミット / フェーズ末の `/refactor_check` は本計画自体が産物のため不要）。
- **phase 08（プリセット）より先に実施**。提案書「依存」の 2 択（phase 08 前 / phase 08 後に 2 例そろえてから）
  のうち前者。**対応表は不変**（γ=phase 07〔完了〕/ プリセット=phase 08〔次〕）。

### 【項目 0】安全網の確認 = **観点 1・2・4・5 は十分 / 観点 3 に空白**（2026-08-06・`Explore` 実測）
- 対応表（主なもの）: ①解決 = `tests/test_config_service.py` の `HookKeyResolutionTest` 5 件 +
  `ApplyGlobalHookKeyDefaultsTest` / ②移行判定 = `tests/test_domain_config.py`
  `ResolveHookKeysIndividualTest` 7 件 + 冪等性 2 件 + `tests/test_save_plan.py:207` /
  ③OFF 保存 = `tests/test_save_plan.py:190` + `tests/test_config_service.py:232`（**値レベルのみ**）/
  ④OFF 編集の config.json 更新と成否 = `tests_ui/test_config_io_characterization_keymap_set_startup.py`
  1099〜1161 の 4 件 + `tests_ui/test_app_ui_flows.py:155` / ⑤dirty 非汚染 =
  `tests_ui/test_app_ui_flows.py` 94 / 119 / 155 / 209。
- **空白 = 観点 3 の「保存 JSON のバイト列比較」**。`read_bytes()` 比較は**子ファイル（keymap /
  trigger_set / sequence）専用**で、hook キーを含む keymap_set 本体・config.json は対象外だった。
  値の同値は `test_none_and_empty_plan_have_equivalent_output` が dict 比較で押さえているが、
  **キー順（＝出力バイト列）は誰も固定していない**。項目 1 の完了条件「バイト列が不変」が
  現状では検証不能なため、**テスト追加を先行**させる（提案書 項目 0 の規定どおり）。
- **リファクタで壊れやすい直接呼び出し**（名前・引数を変えない根拠）: `apply_global_hook_key_defaults`
  （`tests/test_config_service.py` 6 箇所・`config_root=` キーワード）/ `split_loading.load_global_hook_keys`
  （同 startup 特性テスト 1 箇所）/ `write_global_hook_keys`（実呼び出し 4 + `patch.object` 7 箇所。
  うち 1 箇所は `call(stop_key=..., toggle_key=...)` の**シグネチャ完全一致比較**）/
  `toggle_hook_keys_individual`（`tests_ui/test_app_ui_flows.py` 9 箇所）。

### 【項目 0】完了（2026-08-06）= 観点 3 の空白を埋めるテスト **1 件追加**
- `tests/test_save_plan.py` に `test_saved_keymap_set_json_keeps_stable_key_order` を追加（**追加のみ**・
  `keyseq/` 配下は 1 行も変更なし）。保存済み `user/keymap_sets/main.json` を読み直し、
  トップレベルキー順を `build_keymap_set_payload` の返却順 11 キーと**リスト比較**（順序込み）。
  **ON / OFF の両ケース**で比較し、OFF でも 2 キーが**消えずに空文字で残る**ことを固定した
  （後方互換の要）。
- 検証: compile clean / tests **170 pass**（169 + 1）/ tests_ui **178 pass** / smoke pass。
- reviewer = **完了可**（指摘なし）。キー順比較が集合・ソート比較でないこと、OFF が
  `assertIn` + 空文字比較で偽陽性にならないことを確認。
  参考指摘: 期待キー順はハードコードのため、将来**意図的に**キー順を変える改修では本テストの更新が必要
  （特性テストとして意図どおり）。

### 【項目 1】完了（2026-08-06）= **計画06 完了**
- `domain/config.py` に `HOOK_STOP_KEY` / `HOOK_TOGGLE_KEY` / `HOOK_KEY_FIELDS` /
  `normalize_hook_key_pair()` を新設し、提案書どおり 8 ファイル（+58 / -32 行）を置換。
  **値オブジェクト化はしない**（差分最小の方針）。
- **設計の詰め（メイン判断）**: 定数は**単独参照用の 2 本 + 対のタプル 1 本**とし、
  `HOOK_KEY_FIELDS[0]` のような**添字参照は禁止**（可読性が落ちるため）。反復・zip する箇所
  （`apply_global_hook_key_defaults` / `build_runtime_data_from_split` のキー列 /
  `toggle_hook_keys_individual` の退避・復元）でのみタプルを使う。
  `hook_keys_individual` は**定数化しない**（提案書「3 キーの構造体化はしない」に合わせ 2 キーに閉じる）。
- **修正して採用（Codex 判断を採用）**: `ensure_config_compatibility`（domain）と
  `build_keymap_set_payload`（split_payloads）の 2 箇所は `normalize_hook_key_pair` へ寄せず、
  **`normalize_key_name` の直呼びのままキー名だけ定数化**した。新関数は `str(x or "")` を挟むため、
  **非文字列が入っていた場合に現行が送出する例外を握り潰す**＝挙動が変わるため。
  キー名の定数化はメインが補完（Codex は 2 行を丸ごと未変更で残していた）。
- **メインが直接是正した軽微 2 件**: 上記のキー名定数化 / `app.py` の追加 import が application 層の
  import 群の途中に入っていたのを domain 層の位置へ移動（reviewer の参考指摘）。
- 検証: compile clean / tests **170 pass** / tests_ui **178 pass** / smoke pass /
  キー順の特性テストは**無修正 pass** / `tests` `tests_ui` は**1 ファイルも変更なし**（import 移動後に再実測）。
- reviewer = **採用（完了可）**。分岐・評価順序・代入順序・例外挙動・公開 API のシグネチャ・
  保存 payload のキー順が不変であることを突合で確認。残置リテラルが意図的な範囲
  （`DEFAULT_CONFIG` / `split_payloads` の返却 dict キー / `startup_io` の保存 dict キー /
  対象外 4 ファイル）に収まることも確認済み。
- **候補送り（M3 由来の「runtime を新規化・置換する入口が 4 経路」）は未着手**のまま
  `current.md`「別タスク化候補」に残る。**フェーズ番号は消費していない**。

---

## 2026-08-06〜 (phase 08: プリセットの config.json グローバル化 = 保存系リデザイン プリセット案2)

規範: [phase.md](../../instructions/phase/08_hotkey_presets_global/phase.md) /
主入力 = 暫定仕様 07（`instructions/history/07_hotkey_presets_global.md`・**v0.3**）。**暫定仕様先行モード**。

### 【起票時】計画06 の候補送りを本フェーズが引き取る → **採用**（ユーザー確定 2026-08-06）
- 対象 = 「**runtime を新規化・置換する入口が 4 経路**あり、各所で注入 API を呼ぶ規約」の一本化。
  Phase γ の `/refactor_check` から候補送りされ、計画06 では**挙動保存の範囲を超える**ため見送っていた。
- **判断根拠**: ①規約は **task_07b の指摘 A（Import 経路の注入漏れ）で 1 度破れている** ②`app.py:77` の
  `new_default_data()` には注入が無く**起動シーケンスの順序依存だけで守られている**（5 個目の潜在的な穴）
  ③本フェーズでプリセットが同型の注入を追加するため、放置すると **4 経路 × 2 種類**へ増え、
  次の漏れは「プリセットが復活しない」形で出る。**2 例目が出る今が設計のタイミング**。
- **扱い**: 暫定仕様 07 を **v0.3** へ改訂し **§4 検討事項 A（未確定）** として起票。
  **task_03 でユーザー確定 → v0.4 へ改訂 → task_04 で実装**の順とする（設計先行の不変原則）。
  **確定内容が「現状維持」でも可**（その場合は根拠を暫定仕様へ残す）。§2・§3 の確定内容は無改変。
- 論点は 3 つ: ①生成の入口自体が供給済み runtime を返す形（`new_runtime_data(*, config_root)`）へ寄せるか
  ②**通常読込 `build_runtime_data_from_split` の条件付き注入との等価性**をどう保つか
  ③`app.py:77` を新方式へ寄せるか前提を明文化して据え置くか。

### 【起票時】整合チェック（`reviewer`・整合確認限定）= **修正して採用**
- 指摘 1（修正済）: 「このフェーズで読むファイル」の `app.py:405` は実際は **`:406`**。
- 指摘 2（修正済）: 受入条件 6（tests / tests_ui / smoke）の回収先がタスク表から読めない
  → **各タスクの完了条件に含める + task_07 で通し再実測**と明記。
- 主入力との齟齬なし / 最終タスクがフェーズ完了チェックリストを満たすこと / リンクと番号対応
  （phase 08 / 暫定 07 / decisions_archive 08・次採番 09）は OK。

### 【task_01】完了（2026-08-06）= グローバルプリセットパスの読み出し API
- `split_loading.load_global_hotkey_presets_path(service, *, config_root)` を新設（+22 行）。
  `load_global_hook_keys` と同じ骨格で、**保存されている表記をそのまま返し・パス解決はしない**
  （解決は `load_named_list` 側。相対値を `os.path` 系へ直接渡さない不変条件を守るため）。
- **タスク起票時の確定**: **「明示的な空文字」も既定へ縮退**させる（暫定仕様 §3 は「無ければ既定」までしか
  書いておらず空文字が未定義だった）。根拠 = §2 の「プリセットの置き場は常に 1 つ」。
  **task_08 の正本反映でこの契約を明記する**。
- **hook キーとの非対称は意図的**: `load_global_hook_keys` は `config_root` 空で `("", "")` へ縮退するが、
  本 API は**常に既定パスを返す**（キーは「未設定」があり得るが、プリセットの置き場は常に存在する）。
- **修正して採用（Codex の指摘を採用）**: タスク定義が示した `str(x or "").strip()` 一本では
  **数値 `42` が `"42"` になり「非文字列は既定へ縮退」の要件と矛盾する**ため、`isinstance(..., str)` の
  型ガードを追加。タスク定義の記述ミスであり、実装側の判断が正しい。
  reviewer の軽微指摘（ガード後の `str()` が冗長）はメインが 1 行へ整理し再実測。
- 検証: compile clean / tests **175 pass**（170 + 追加 5）/ tests_ui **178 pass**（無修正）/ smoke pass /
  差分は `split_loading.py` と `tests/test_config_service.py` の **2 ファイルのみ**。
- reviewer = **採用（完了可）**。5 経路すべての既定縮退・解決していないこと・既定値の定義元が
  `HOTKEY_PRESETS_RELATIVE_PATH` 1 箇所であること・「含まない」への未踏み込みを確認。

### 【task_02】完了（2026-08-06）= プリセットの読込元を config.json へ切替（**挙動変更**）
- `build_runtime_data_from_split` のプリセット読込 **1 行**を
  `keymap_set.get("hotkey_presets_path")` → `load_global_hotkey_presets_path(service, config_root=...)` へ差し替え。
  **keymap_set 側キーはこの関数から参照されなくなった = 読込時無視**（`pop` 等の能動削除はしない）。
- **既存テストの修正は 0 件**（挙動変更だが既存テストは同一 config_root で保存・再読込するため、
  グローバル既定パスと保存先の既定パスが一致し影響が出なかった）。追加 5 件のみ。
- **既知の中間状態（task_05 まで残す）**: 保存側は未変更のため「**別ディレクトリへ保存した keymap_set を
  読み直すとプリセットはグローバル側**」という非対称が残る。**先取りで直さない**とタスク定義に明記し、
  reviewer にも「本タスクでは正しい状態」として確認させた。
- 単一 JSON 互換の読込（`ensure_config_compatibility` のインライン `hotkey_presets`）は**対象外**（別形式）。
- 検証: compile clean / tests **180 pass**（175 + 追加 5）/ tests_ui **178 pass** / smoke pass /
  差分は `split_loading.py`（±1 行）と `tests/test_config_service.py` の 2 ファイルのみ。
- reviewer = **採用（完了可）**・指摘なし。観点 2 のテストが**グローバルと keymap_set 側に異なる内容を置いて
  値で区別**しており偽陽性でないことも確認。

### 【task_03】完了（2026-08-06）= 入口一本化の**設計確定**（文書のみ・暫定仕様 07 を **v0.5** へ）
- **方式 = 案B: 注入 API を 1 本に束ねる**（ユーザー確定）。`ConfigService.apply_global_defaults(runtime, *, config_root)`
  が **hook キー注入 + グローバルプリセット供給**を担う。**`app.py:77` も新方式へ寄せる**（ユーザー確定）。
  - **却下: 案A（供給済みファクトリ `new_runtime_data`）** — 通常読込は hook キーが**フラグ次第の条件付き注入**の
    ため素の `new_default_data()` を使い続けることになり「入口は 1 つ」にならない。公開 API 変更で
    テスト 6 + 呼び出し 4 箇所へ波及する割に得るものが小さい。
  - **却下: 案C（現状維持）** — 呼び忘れ面が **4 経路 × 2 種類**へ倍化する。
- **例外を 1 つ残す**: `App.toggle_hook_keys_individual` の **ON→OFF は従来どおり
  `apply_global_hook_key_defaults` を直接呼ぶ**。束ねた API を使うとキー切替だけで**プリセットが再読込**され、
  編集中の内容を取りこぼすため。**「hook キー単独の注入」と「runtime 置換時の全体注入」は別物**。
- **敵対的レビュー（`codex-adversarial-reviewer`）= needs-attention・指摘 2 件を実コードで裏取り →
  ユーザーが 2 件とも採用**（→ v0.5）:
  - **[high] 空リスト縮退が §2 を破る**（グローバルが空でも通常読込＝空 / 新規作成＝組込 8 件と経路で割れる。
    削除したプリセットが復活し task_06 の保存で再永続化され得る）→ 読み出しを **`list | None`** に変え
    **「読めた空リスト」と「読めない」を区別**。**読めたら空でも採用 / 読めなければ置き換えない**。
    **通常読込も同規則へ統一**（→ **task_02 のテスト「不存在・破損 → `[]`」は task_04 で
    「置き換えない = 組込 8 件」へ更新する**）。
  - **[medium] 入口台帳が不完全**（受入条件 7 が 5 経路しか見ず、通常読込 3 経路が漏れる）→
    `app.data` 置換の**実測 9 箇所**を **入口台帳 E1〜E5 / L1〜L3 / N1** として §3-2 へ列挙し、
    受入条件 7 を台帳全経路へ拡張・受入条件 9 を追加。
- **実測で判明した重要事実**: Import（`keymap_set_io.py:561`）は**レガシー単一 JSON 経路**で
  `build_runtime_data_from_split` を通らない。よって**インラインの `hotkey_presets` はグローバルが
  読めれば置き換わる**（§2 の帰結）。読めないときだけインラインが残る。
- レビュアーが触れなかった論点（ON→OFF の例外 / `app.py:77` の起動順序 / 正本 §5.9・codebase_map の
  「解決点は 4 つ」との整合）はメイン判断で v0.4 の記述を維持し、**正本側の更新は task_08 で行う**。
- 成果物は**文書のみ**（`keyseq` / `tests` / `tests_ui` は無変更）。

### task_04（`apply_global_defaults` の実装・入口台帳 E1〜E5 配線）— 2026-08-09

- 暫定仕様 07 §3-2（v0.5）をそのまま実装。**設計の再検討・仕様変更は発生していない**。
- 実装判断（いずれも仕様の範囲内・レビュー採用済）:
  - `load_global_hotkey_presets` は `load_global_hotkey_presets_path` → `_resolve_config_relative_path`
    → `_load_optional_json` の順で読み、**非 dict / 根キー非 list を `None`**、**list は空でも採用**。
    例外は握り潰さず `try` の範囲を読み出しに限定（例外を投げない契約）。
  - `apply_global_defaults` は **`apply_global_hook_key_defaults` を委譲呼び出し**（ロジック複製なし）。
  - **E1（`app.py:77`）は新規の 1 行追加**で、順序依存だけで守られていた穴を塞いだ。
- **想定外の先行実装**: なし（差分はタスク定義が挙げた production 5 + テスト 3 ファイルのみ）。
- 実測: compile clean / `tests` **186**（+6）/ `tests_ui` **181**（+3）/ smoke pass。
- `reviewer` = **採用（完了可・指摘なし）**。

---

## 運用メモ

- 1 タスク完了時に reviewer 判定をここへ転記する
- 想定外の先行実装を発見した場合の判定もここへ記録する
- 後続フェーズの設計で参照する
