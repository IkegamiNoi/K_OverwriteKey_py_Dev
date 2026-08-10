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
| 08_hotkey_presets_global | [08_hotkey_presets_global.md](decisions_archive/08_hotkey_presets_global.md) | プリセットの config.json グローバル化 = 保存系リデザイン **プリセット案2**（2026-08-09 完了・**挙動変更＋スキーマ変更**）。hotkey プリセットを keymap_set の子から **config.json が指すアプリ全体のライブラリ**へ移し、keymap_set の `hotkey_presets_path` は**生成停止・読込時無視**（能動削除しない＝再保存で自然消滅）。**書き手をプリセットマネージャの 1 本に限定**（即時保存・成否付き・失敗時は確定せずダイアログを閉じない・dirty を汚さない）。計画06 からの持ち越し「runtime を新規化・置換する入口の一本化」を **`apply_global_defaults` + 入口台帳 E1〜E5** として設計・実装（**単独注入は ON→OFF のみ**・通常読込は経由しないが供給規則は共通）。読み出しは **`list | None`**（読めたら空でも採用 / 読めなければ置き換えない）+ **読み出し側で正規化**（横断レビュー H1 の是正 = task_07b）。正本 `data_schema.md` **§5.10 新設** + **§5.8.8**（入口台帳）+ §5.1 の**「削除禁止の例外＝生成停止」** + §5.4 / §5.5 / §5.9.2 + `codebase_map.md` へ昇格済。**受入条件 7 は「グローバルが読めた場合」へ限定**し、`None` 時の経路差・破損上書き・旧「別ディレクトリ保存」の孤児プリセット・Export のデッドデータは**実装を変えず契約として明記**。**後続**: idea_08（keymap_set 個別プリセット・**着手可**）。refactor_check: 判定は本アーカイブ末尾 |

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

## 運用メモ

- 1 タスク完了時に reviewer 判定をここへ転記する
- 想定外の先行実装を発見した場合の判定もここへ記録する
- 後続フェーズの設計で参照する

---

## 2026-08-09〜 (phase 09: keymap_set ごとの個別プリセット)

規範: [phase.md](../../instructions/phase/09_per_keymap_set_presets/phase.md) /
主入力 = 暫定仕様 08（`instructions/history/08_per_keymap_set_presets.md`・**v0.4**）。**暫定仕様先行モード**。

### 【起票時】idea_08 の昇格と設計確定（ユーザー確定 2026-08-09）

- `deep-reviewer`（起票時）= **修正要** → 確認事項を A〜F から **A〜R** へ拡充（v0.2）。
- ユーザー確定（v0.3）→ **`codex-adversarial-reviewer` = needs-attention（High 4 / Medium 2）** → v0.4。
- **確定の要点**: グローバル既定を `user/hotkey_presets/global/default.json` へ移す（**移行は手動・2 段**）/
  個別は `user/hotkey_presets/<stem>.json` / **旧キー `hotkey_presets_path` を個別パスとして再利用**し
  **新フラグ `hotkey_presets_individual` が真のときだけ読む**（**フラグ無しは常に OFF**）/
  **書き手はマネージャ 1 本** / 個別が読めなければ**グローバルへフォールバック** /
  **Import は強制 OFF** / **トグルは保存先の切替だけ**（一覧は差し替えない）/
  **別名保存では個別ファイルを複製**。
- **A（旧キー再利用）の判断根拠**: 意味は phase 08 以前へ戻る方向であり、**フラグを値で判定**すれば
  残置値は必ず無視される。加えて **G でグローバルを `global/` へ移したため、残置値はもう
  グローバルを指さない**（上書き事故が構造的に起きない）。旧版アプリが読んでも
  **未知キー無視 + 読込時無視でグローバルへ安全に倒れる**。
- **敵対的レビューで潰した穴**: ①config.json に**明示保存**があると手動移行が効かず
  **旧パス再生成のループ**になる（→ 移行手順を 2 段にした）②トグル即時解決が編集中の `_temp` と
  両立しない（→ **【I】を撤回**）③config 外パスがマネージャの保存先になり得る（→ 無効化を規定）
  ④別名保存の無警告共有（→ **【L】を反転して複製**）。
- phase.md の整合チェック（`reviewer`・限定）= **採用（修正不要）**。

### 【task_01】完了（2026-08-09）= グローバル既定パスの移動

- `HOTKEY_PRESETS_RELATIVE_PATH` を `user/hotkey_presets/global/default.json` へ変更し、
  `ensure_split_config_dirs` へ `global/` を追加（**`user/hotkey_presets` 直下の作成は残す**）。
  **production の差分は 5 行**。
- **互換フォールバック読みは実装しない**（仕様どおり）。「**旧既定にファイルがあっても読まれない**」を
  特性テストで固定した。
- 既定パスをハードコードしていた 5 箇所を**定数参照へ**更新 → 次の変更へ自動追随する。
- 実測: compile clean / `tests` **204**（+1）/ `tests_ui` **186** / smoke pass。
  件数 +1 の内訳 = 既存 1 件の**改名** + 新規 1 件。
- `reviewer` = **採用（完了可・指摘なし）**。

### 【task_02】完了（2026-08-09）= keymap_set のスキーマ追加

- `DEFAULT_CONFIG` へ 2 キー追加 + `ensure_config_compatibility` で正規化 +
  `build_runtime_data_from_split` のキーコピー + `build_keymap_set_payload` の返却へ挿入
  （**`trigger_set_path` の直後**。他のキー順は不動）。
- **移行規則は値のみで判定**。**`resolve_hook_keys_individual`（フラグ無し + 非空なら ON）を流用しない**
  = 流用すると phase 08 の**残置 `hotkey_presets_path` が個別指定として復活**する（§3-5）。
  真偽値でない値（`"true"` / `1` / `None`）は **False**。
- **OFF でも `hotkey_presets_path` を空文字化しない**（hook キーの「OFF なら常に `""`」とは別扱い・【N】）。
- **想定外の先行実装 → 修正して採用**: phase 08 の特性テスト 2 件
  （keymap_set payload に `hotkey_presets_path` を出力しないことを固定していたもの）は
  **phase 09 が意図的に覆す前提**のため、**削除せず新仕様の期待値へ更新**した
  （常時出力・OFF でもパス保持）。`reviewer` は「緩和ではなく検証内容の強化」と判定。
  → **phase 08 の受入条件 2 は phase 09 で上書きされる**。正本 §5.5 / §5.1 の改訂は **task_08** で行う。
- 実測: compile clean / `tests` **209**（+5）/ `tests_ui` **186**（増減なし）/ smoke pass。
- `reviewer` = **採用（完了可・指摘なし）**。

### 【task_03】完了（2026-08-09）= 解決順序の実装（**読込先が実際に分岐**）

- `load_hotkey_presets_file`（任意パス・`list | None`）を切り出し、`load_global_hotkey_presets` を
  **薄いラッパ**へ。**公開規約（`list | None`・正規化済み・例外を投げない）は不変**。
- 個別パスの**有効判定を 1 関数へ集約**（フラグが `is True` / 非空文字列 / **解決後が config 配下** /
  `config_root` 空なら無効）。判定は**比較専用 API**（`is_path_within`）で、**保存値は書き換えない**。
- 供給順 = **個別 → `None` ならグローバル → それも `None` なら置き換えない**。
  **`is None` で判定**（`[]` は falsy のため真偽判定で書くと「読めた空」がフォールバックしてしまう。
  受入条件 9 の規則を個別側でも維持するための要点）。
- `apply_global_defaults`・保存側・presentation は無変更。runtime へ内部キーを増やしていない。
- 実測: compile clean / `tests` **216**（+7）/ `tests_ui` **186** / smoke pass。
- `reviewer` = **採用（完了可・指摘なし）**。

### 【task_04】完了（2026-08-10）= 保存先の算出と書込先の切替

- `default_individual_hotkey_presets_path` を trigger_set と同じ流儀で追加
  （`slugify_file_stem` / フォールバック `default` / **衝突回避しない** / `split_base_dir` を取らない）。
  **グローバル既定が `global/` 配下にあるため stem が `default` でも衝突しない**（task_01 の狙いが効いた）。
- `save_hotkey_presets(..., stored_path)` を新設し `save_global_hotkey_presets` を薄いラッパへ
  （**読み出し側の 2 段構えと対称**）。**例外は送出のまま**（成否変換は presentation）。
- 書込先の決定は `resolve_hotkey_presets_save_path` に集約し、**task_03 の判定を再利用**。
  **ON + config 外は空文字（グローバル）へ倒す**＝個別へ書かない。
- presentation は `write_presets(presets, *, stored_path)` へ改名（旧名の残存ゼロ）。
  `App.save_hotkey_presets` は**成功時のみ** `data["hotkey_presets_path"]` を確定値へ反映し、
  **フラグは変えない**（切替は task_05）。**失敗時は `data` を一切変更しない**。
- **【H】ON にした時点ではファイルを作らない**（実体は保存時に初めて作られる）。
- **参考指摘（非ブロッキング・候補送り）**: `default_individual_hotkey_presets_path` は
  `HOTKEY_PRESETS_RELATIVE_PATH` へ `os.path.dirname` を 2 回かけて `user/hotkey_presets` を導いており、
  **定数の階層が変わると例外を出さず誤ったディレクトリを返す**。リポジトリ内の既存慣用手法の範囲内で、
  値ベースのテストが担保しているため今回は据え置き（専用定数を切る代替案あり）。
- 実測: compile clean / `tests` **220**（+4）/ `tests_ui` **189**（+3）/ smoke pass。
- `reviewer` = **採用（完了可）**。

### 【task_05】完了（2026-08-10）= 切替 UI と OK / キャンセルの契約

- **仕様の解釈を 2 点確定**（暫定仕様 08 が文言レベルまで規定していなかった箇所。タスク定義へ明記した）:
  - **保存先の表示は 2 行に分ける**。「保存先」= **チェックに追従**（§3-4）/
    「一覧の出どころ」= **ダイアログを開いた時点で固定**。
    **トグルで一覧を差し替えない**【I 撤回】以上、1 行に混ぜると
    「トグルへの追従」と「フォールバック中の告知」が両立しないため。
  - **表示状態の判定は application 側**（presentation で解決順序を組み立てない。task_04 と同方針）。
- `resolve_hotkey_presets_save_path` へ **`individual: bool | None` の override** を追加
  （**runtime は書き換えず局所コピーで判定**。`None` は現行どおり）。
  `describe_hotkey_presets_source` を新設し、**`individual_state`（off / active / missing / invalid）×
  `displayed_source`（individual / global / builtin）の 2 値を独立に返す**
  （**優先順位を付けて片方を隠さない**。既存 3 関数を再利用し判定を二重化しない）。
- `App.save_hotkey_presets(presets, *, individual=None)` の 4 分岐を確定。
  **ON→OFF は保存 API を呼ばず**フラグだけ False にし、**`hotkey_presets_path` は保持**【N】、
  **グローバルを読み直す**【H2】。**dirty はフラグの値が実際に変わったときだけ**。
  **失敗時は `data` を一切変更しない**（先にフラグを立てて戻す形にしない）。
- 文言は **Tk 非依存の純関数 `format_preset_manager_source_labels`** へ分離
  （`PresetManagerDialog` は `grab_set` / `wait_window` を持つためテストから構築しにくい）。
- **【Q】の再評価はダイアログを毎回構築し直す性質で満たす**（通知の仕組みは足さない＝過剰実装の回避）。
- **保留（ユーザー判断待ち・task_06 着手前に確認）**: `reviewer` の参考指摘 =
  **個別 ON かつパスが config 外（無効）のとき、UI は「無効」と表示するのに OK の保存先は
  グローバルへ倒れる**。`resolve_hotkey_presets_save_path` は「パスが非空なら既定へ差し替えない」ため
  既定の個別パスへも落ちない。**暫定仕様 08 §2【O2】は読み出しのみ規定**しており、
  書き込み側は未定義。**専用のつもりの操作でグローバルが上書きされ得る**点が
  「グローバルの保護」観点と衝突する疑い。選択肢 = (A) 現状維持 / (B) 既定の個別パスへ逃がす /
  (C) 保存を拒否して理由表示。**task_04 由来のため task_05 では不変で通した**。
- 実測: compile clean / `tests` **222**（+2）/ `tests_ui` **196**（+7）/ smoke pass。
- `reviewer` = **採用（完了可）**。

### 【仕様確定 v0.5】無効な個別パスでの保存を拒否する（2026-08-10・ユーザー確定）

- 発端 = **task_05 の `reviewer` 参考指摘**。task_04 由来の未定義挙動で、
  **個別 ON かつ `hotkey_presets_path` が config 外のとき、UI は「無効」と表示するのに
  OK の保存先はグローバルへ倒れて上書きされ得た**。
  `resolve_hotkey_presets_save_path` は「パスが非空なら既定へ差し替えない」ため既定の個別パスにも落ちない。
- **ユーザー判断 = (C) 保存を拒否して理由表示**。
  - 却下 **(A) 現状維持**（UI が「無効」と告知している状態で黙って別の場所へ書くのは事故。
    **グローバルライブラリを破壊し得る**）
  - 却下 **(B) 既定の個別パスへ逃がす**（記録済みパスから保存先が黙って変わり、同種の驚きを生む）
- **暫定仕様 08 を v0.4 → v0.5 へ改訂**し **【O3】を新設**
  （§2 / §3-3 / §3-4 / 受入条件 15 / §4 の却下記録）。**フェーズ中の正は暫定仕様**のため
  正本 `spec_detail/` の更新は **task_08** で行う。
- **【O2】読み出しは従来どおりグローバルへ倒す**。**この非対称は意図どおり**
  （読み出しは壊れないが、書き込みはグローバルを破壊するため）。
- 対象は**実効的な書込先が個別のときだけ**。**ON → OFF の確定は拒否しない**
  （無効パスを抱えたまま「専用をやめる」操作は成功させる＝**主要な復旧手段**）。
  **OFF のままの保存も従来どおりグローバルへ書ける**。

### 【task_05b】完了（2026-08-10）= 無効な個別パスでの保存拒否（枝番タスク）

- `resolve_hotkey_presets_save_target(...) -> (stored_path, status)` を新設。
  `status` = **`individual` / `global` / `invalid`** の 3 値で、
  **`resolve_hotkey_presets_save_path` はその薄いラッパ**（戻り値・既存呼び出し・既存テストは不変）。
  **`invalid` 判定は既存の `resolve_individual_hotkey_presets_path` を再利用**（新規パス判定を書かない）。
  `config_root` 空も `invalid` 側へ混ぜる（分岐を増やさない。通常経路では起きない）。
- `HotkeyPresetsIo.reject_invalid_target()` で理由表示（**現在のパス + 復旧手段**を含む）。
  **モーダルはこのファイルへ集約**（tests_ui の fail-fast ガードがここを見ているため、
  `app.py` に新しい `showerror` を増やさない）。
- `App.save_hotkey_presets` は**書き込み前に** status を見て拒否し、**`data`・dirty を一切変更しない**。
  `dialogs.py` は**無変更**（戻り値 False で閉じない契約が既にある）。
- 読込側（`build_runtime_data_from_split` / `describe_hotkey_presets_source`）は**完全に無変更**。
- 実測: compile clean / `tests` **225**（+3）/ `tests_ui` **200**（+4）/ smoke pass。
- `reviewer` = **採用（完了可・指摘なし）**。

### 【仕様確定 v0.6】無効な個別パスは拒否せず既定パスへ寄せる（2026-08-10・ユーザー確定・**v0.5 を反転**）

- **v0.5【O3】= 拒否**をユーザーが再考し、**却下していた案 B（既定の個別パスへ寄せる）を採用**した。
- 反転の理由（v0.5 で (C) を推した根拠が実際には弱かった）:
  1. **task_05 で保存先ラベルがチェックに追従して表示される**ようになったため、
     リダイレクト先は **OK を押す前に見えている**。「黙って別の場所へ書く」に当たらない。
  2. **ON + パス未設定は既に「既定パスへ新規作成」**（task_04 +【E】）。
     無効パスを「使えるパスが記録されていない」と同一視すれば**同型**になり、新しい概念が増えない。
     むしろ拒否の方が同じ状態に対して分岐を 2 つ持つ。
  3. **キーを書き換えない**という (C) の唯一の利点は、**【K】Import が 2 キーとも書き換える前例**が
     あるため原則として立たない。**【N】の趣旨（再 ON で同じファイルへ戻る）も、
     二度と書けない無効パスの保持には寄与しない**。
  4. 拒否は**復旧手段が JSON の手編集しか無く行き止まり**（GUI ツールとして厳しい）。
  - グローバル保護は両案とも同等（書込先は必ず個別側に取る）。
- **【dirty 規則】`hotkey_presets_path` の値が実際に変化したときだけ dirty を立てる**（同時確定）。
  - 発見の経緯: 「パス書き換えで dirty を立てるか」を検討した際、**現状はフラグ変更（OFF→ON）への
    相乗りで永続化している**だけで、**「最初から ON」の経路には dirty が立たない穴**があると判明。
  - **同値の再確定では立てない**ため、**通常運用（ON + 有効パスで内容編集）は dirty にならない**
    （受入条件 4 を維持）。リダイレクトと既存の穴を**1 規則で塞ぐ**。
- 正本 `spec_detail/` への反映は **task_08**（フェーズ中の正は暫定仕様）。

### 【task_05c】完了（2026-08-10）= 無効パスのリダイレクト + パス変化時 dirty

- **task_05b の拒否経路を全削除**（`resolve_hotkey_presets_save_target` の 3 値ステータス /
  `reject_invalid_target` / 保存側の `invalid` 分岐）→ `resolve_hotkey_presets_save_path` へ復帰。
  **恒久互換レイヤーを残さない**。判定は既存の `resolve_individual_hotkey_presets_path` の再利用のまま。
- 書込先の分岐 = **有効な個別パス → そのパス / 未設定 “または” 無効 → 既定パス / OFF → 空文字**。
  `config_root` 空は従来どおりグローバルへ倒す。
- `App.save_hotkey_presets` は**反映前の値と比較して、変化したときだけ** `set_dirty(True)`。
  **保存失敗時は立てない**（`data` 不変と同じ契約）。フラグ変化による dirty は従来どおり併存
  （`set_dirty(True)` は冪等なので特別扱いしない）。
- `dialogs.py` は `invalid` の文言のみ変更（**これから書く既定パスを必ず含める**）。
  **OFF の表示契約（「グローバル（<パス>）」）と出どころラベルは不変**。
- 実測: compile clean / `tests` **222**（-3）/ `tests_ui` **199**（-1）/ smoke pass
  （**減は拒否系テストの削除・差し替えによる想定内**）。
- `reviewer` = **採用（完了可）**。**参考指摘 1 件**: `dialogs.py` の invalid 文言生成で
  保存先解決を 1 回追加呼び出ししている（軽量・実害なし・非ブロッキング）。

### 【運用インシデント】Codex ジョブ復旧時のプロセス誤終了（2026-08-10）

- 実装フォワーダがハングした Codex ジョブの復旧中に **`taskkill /PID <pid> /T /F`** を実行し、
  **PID 再利用により無関係な `node_repl` プロセス約 22 個**を子プロセスと誤認して終了させた。
- リポジトリのファイルへの影響なし（差分は task_04 の想定どおり）。他ジョブの state も無事。
- **再発防止**: **詰まったジョブに `taskkill /T` を使わない**。
  `instructions/common/rules_detail/codex_operations.md` **§4 の state 手修復**
  （backup → `cancelled` へ書換・`.log` は保全）に倒す。`session.md` の resume_hints にも明記した。
