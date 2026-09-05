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
| 09_per_keymap_set_presets | [09_per_keymap_set_presets.md](decisions_archive/09_per_keymap_set_presets.md) | keymap_set ごとの個別プリセット（2026-08-16 完了・**挙動変更＋スキーマ追加**）。グローバル既定を **`user/hotkey_presets/global/`（予約ディレクトリ）**へ移し（**移行は手動 2 段**）、keymap_set の**旧キー `hotkey_presets_path` を個別パスとして再利用** + 新フラグ **`hotkey_presets_individual`**（**フラグキーが無ければ残置パスごと落とす**）。解決は**個別 → グローバル → 置き換えない**、**読み出しは config 外も許容 / 書き込みは管理下の既定パスへ寄せる**（意図的な非対称）。書き込み前の判定を **①既定パスへ寄せ → ②保存先ガード〔`global/` 配下・グローバルと同一なら拒否〕→ ③上書き確認〔内容比較・**3 択**〕**の順に確定。**書き手はマネージャ 1 本**のまま、**トグル / OFF で開いた時点の一覧読み直しはダイアログ内の表示のみ**（**プリセット単独の注入 API は作らない**＝入口台帳 **P1**）。**dirty は `hotkey_presets_path` の値が変化したときだけ**。別名保存は**個別ファイルを複製**。**設計は 2 度反転**（v0.5→v0.6 の【O3】拒否→寄せ / v0.4→v0.8 の【I】撤回→再採用）。**実機目視で 4 件の不具合を検出**（→ task_07c / 07d / 07e / 07g）。正本 `data_schema.md` **§5.10 全面改訂** + §5.10.4 + **§5.8.8** + §5.5 / §5.4 / §5.1 + `codebase_map.md` へ昇格済。**除外**: ネストしたモーダルの grab 復元（アプリ全体の課題 → **idea_10**）/ 確認と書き込みの間の競合（契約として明記）。refactor_check: 判定は本アーカイブ末尾 |

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


## 2026-08-16〜 (計画07: phase 09 後のリファクタ・挙動不変)

規範: `instructions/modified_proposal/07_refactor_per_keymap_set_presets.md`
（項目 0 = 安全網 / 1 = `PresetManagerDialog.__init__` の UI 構築抽出 / 2 = `dialogs.py` の
パッケージ化 / 3 = 直値の定数化。**1 項目 = 1 コミット**）。
phase 09 完了時の `/refactor_check` = 推奨（M1 / M2 / M6 該当）の産物。

### 【起票時】実施形態 → **(b) 次フェーズ前の独立ミニ計画 = 「計画07」**（ユーザー確定 2026-08-16）
- 提案書の選択肢 (a) phase 09 末の追加タスク / (b) 独立ミニ計画 のうち **(b)** を採用。
  運用は**計画05 / 計画06 と同じ**（提案書自体を確定設計として扱う / **フェーズ番号を消費しない** /
  1 項目 = 1 コミット / 本計画自体が `/refactor_check` の産物のため完了時の再実行は不要）。
- **(a) を採らない理由**: phase 09 は正本反映まで終えて**すでに閉じている**
  （`current.md` 更新・`decisions_archive/09` 作成・idea_08 クローズ済）ため、
  追加タスクは閉じたフェーズを開け直すことになる。
- **暫定仕様書は起票しない**（挙動保存のみで仕様確定の反復が不要）。**対応表は不変**
  （次フェーズは引き続き `10_<topic>`）。

### 【項目 0】安全網の調査 = **契約 1〜5 は十分 / `__init__` 周辺に 5 つの空白**（2026-08-16・`Explore` 実測）
- **プリセットマネージャ関連のテストは `tests_ui/test_app_ui_flows.py` の 1 ファイルに集中**
  （`tests/` 側に UI 契約のテストは無い）。OK / キャンセルの不変性・トグルの読み直し・破棄確認・
  OFF で開いた時点の一覧確定・上書き確認の 3 択と adopt / cancel の不変性は**強く守られている**。
- **空白（抽出で壊れても検知されない）**: ①**`_update_source_labels()` 本体が完全に無テスト**
  （テストされているのは純関数 `format_preset_manager_source_labels` だけ。最大の穴）
  ②`__init__` が初期化する状態（トグル系テストは **`object.__new__` で手埋め**するため）
  ③**イベント配線**（`command=` / `bind`。既存テストはハンドラを直接呼ぶ）
  ④`suspend_hook_for_dialog` / `resume_hook_after_dialog` の呼出 assert
  ⑤`_refresh()` による listbox の実内容。
  → **項目 0 として実構築ベースの特性テスト 4 種類を先行追加**（提案書の規定どおり）。
- **【項目 1 への制約】`_refresh` / `_update_source_labels` はリネーム禁止**
  （`patch.object(PresetManagerDialog, ...)` が **9 箇所以上**でクラス属性を差し替えている）。
- **【項目 2 への制約】分割で `tests_ui` の patch 6 箇所が壊れる**
  （`keyseq.presentation.dialogs.tk.Toplevel.destroy` × 3 / `...dialogs.messagebox.askyesno` × 3）。
  `tk` / `messagebox` は**共有モジュールオブジェクト**なので patch の効果自体は同じで、
  壊れるのは**属性解決だけ**。
  - **判断 = テスト側の patch 文字列を実体モジュールへ更新する**（**アサーションは変えない**）。
    却下案 = `__init__.py` で `tk` / `messagebox` を import して属性を維持する
    （**公開面でないものを公開面に置く互換維持**になり、`file_organization_rules.md` の
    「恒久互換レイヤー禁止」の趣旨に反する）。
- **循環 import**: クラス間依存は `ActionDialog → PresetManagerDialog` と
  `PresetManagerDialog → PresetDialog` の 2 本（一方向）。
  **サブモジュール直指定**にすれば部分初期化の `ImportError` を避けられる。
  `App` の型 import は**各ファイルで `TYPE_CHECKING` ガードの中に置く**（外すと真の循環）。

### 【項目 0】完了（2026-08-16）= 安全網の特性テスト 6 本を追加
- `tests_ui/test_app_ui_flows.py` に **+203 行・6 メソッド**（**純追加・削除 0**）。**production は無変更**。
  ①〜③ ラベルの実値 3 ケース（OFF+グローバル可 / ON+個別可 / **ON+config 外＝既定パスへの再解決**）
  ④ **`individual_check.invoke()` 経由**（`command=` 配線込み）のトグル
  ⑤ `suspend_hook_for_dialog` / `resume_hook_after_dialog` の**呼出回数**
  ⑥ `listbox.get(0, "end")` が `format_preset_list_item` の実フォーマットと一致すること。
- **すべて実構築**（`PresetManagerDialog(self.app)`）で書いた。`object.__new__` の手埋めを使わないことが
  ②の空白（`__init__` の初期化が検知されない）を埋める要件だったため。
- 実測: compile clean / `tests` **238**（不変）/ `tests_ui` **229**（223 → **+6**・ハングなし）/ smoke pass。
- `reviewer` = **完了可（指摘なし）**。5 観点に加え、共有 App の汚染防止（`before`/`finally` 復元・
  `patch.object` のコンテキスト・`destroy()` の `try/finally`）・**モーダル非到達**・
  assert が広い `except` の内側にないこと・**`_refresh` / `_update_source_labels` 以外の
  private メソッド名に依存していないこと**（項目 1 で壊れない形）を確認。

### 【項目 1】完了（2026-08-16）= `PresetManagerDialog.__init__` の UI 構築抽出
- 99 行の `__init__` を 4 メソッドへ抽出（**+38 / -28**・`dialogs.py` の 1 ファイルのみ）:
  `_init_preset_manager_state`（状態・Tk 変数）/ `_build_preset_manager_widgets`（生成・配置）/
  `_bind_preset_manager_events`（配線）/ `_sync_initial_presets`（OFF 時の一覧確定 + `_refresh`）。
  **`__init__` は 8 行**。**既存のメソッド名・属性名は 1 つも変えていない**
  （`_refresh` / `_update_source_labels` のリネーム禁止を遵守）。
- **テストは 1 行も変更していない**（挙動保存の要件）。実測 = compile clean / `tests` **238**（不変）/
  `tests_ui` **229**（不変・ハングなし）/ smoke pass。
- `reviewer` = **完了可**。ウィジェット生成順・`grid`/`pack` 順・文言・`suspend_hook_for_dialog` の
  位置が完全一致であることを**逐行**で確認。挙動が変わり得る 2 点も**同値と判定**:
  ①state 計算ブロックの移動 = **純 Python 計算で mainloop と無関係**
  ②`individual_check` の `command` 配線が**コンストラクタ引数 → 生成直後の `.configure()`** へ変わったが、
  **間で mainloop が回らないため中間発火の余地が無い**（かつ項目 0 で追加した
  `individual_check.invoke()` テストがこの配線を直接守っている）。
- **参考指摘（対応不要と判定）**: `_build_preset_manager_widgets` が約 56 行で
  `implementation.md` の「関数 30 行目安」を超えるが、**既存コードの逐語移動**であり、
  項目 1 の範囲でさらに分割するのは過剰実装になるため据え置き。

### 【項目 2】完了（2026-08-16）= `dialogs.py`（1026 行）を `dialogs/` パッケージへ分割
- **1 クラス 1 ファイル**の 7 ファイル構成（最大 `preset_manager.py` **386 行**・全ファイル 400 行以内）。
  **逐語移動**（ロジック・整形・命名・コメントの変更ゼロ）。**旧 `dialogs.py` は削除**
  （横流し専用モジュールを残さない＝恒久互換レイヤーの禁止）。
- **`__init__.py` は明示列挙の再輸出のみ**（6 クラス + `format_preset_manager_source_labels`）。
  **`tk` / `ttk` / `messagebox` を置かない**（patch 先を維持するためだけの互換維持は採らない・項目 0 の判断）。
- **クラス間参照はサブモジュール直指定**（`action_dialog → dialogs.preset_manager` /
  `preset_manager → dialogs.preset_dialog`）。パッケージ経由にすると
  `__init__.py` の列挙順次第で**部分初期化の `ImportError`** になるため。
  `App` の型 import は**全ファイルで `TYPE_CHECKING` ガード内**（外すと真の循環）。
- **テスト差分は patch 文字列 6 箇所のみ**（`+6 / -6`。アサーション・テスト名・構造は不変）。
  production の 4 ファイルは**無変更で通る**。
- **修正して採用（計画との差異）**: 計画のコード例は `PresetDialog` を `preset_manager.py` へ同居させる
  書き方だったが、**400 行以内の条件**を満たすため `preset_dialog.py` として独立させた。
  依存は一方向で循環せず、1 クラス 1 ファイルの原則にも忠実なため**採用**（提案書の構成図も実体へ更新）。
- 実測: compile clean / `tests` **238**（不変）/ `tests_ui` **229**（不変・ハングなし）/ smoke pass。
  **production の import 7 名が無変更で成功**・**循環 import なし**
  （`dialogs.action_dialog` 単独 / `presentation.app` 単独の両方向で確認）。
  **stale な `__pycache__/dialogs.cpython-314.pyc` が残っていた**ため削除して再実測し、**結果不変**を確認。
- `reviewer` = **完了可**。旧ファイル（`git show HEAD:...`）との**全文逐語突き合わせ**で
  欠落・重複・ついで修正が無いことを確認。
- **付随更新**: `codebase_map.md` のツリーを `dialogs/` の 7 ファイル構成へ更新
  （`PresetManagerDialog` の所在も `dialogs/preset_manager.py` へ）。

### 【項目 3】完了（2026-08-16）= `global/` ディレクトリ作成の直値を定数由来へ
- `ensure_split_config_dirs` の `os.path.join(config_root, "user", "hotkey_presets", "global")` を
  `os.path.join(config_root, os.path.dirname(self.HOTKEY_PRESETS_RELATIVE_PATH))` へ（**+4 / -1**）。
  **`split_loading.py:181` と同じパターン**に揃えた（`save_path_resolution.py:189` は
  `dirname` を 2 回かけて**別階層**〔`hotkey_presets` 直下〕を求める別用途であり、非対称ではない）。
- **メインセッションが直接実装**（`agent_selection.md`「数行程度の軽微な修正」）。
- 実測: compile clean / `tests` **238** / `tests_ui` **229** / smoke pass。
  **一時ディレクトリで `ensure_split_config_dirs` を実行し、生成されるディレクトリ集合が
  変更前と完全に同一**（`user/{keymap_sets,keymaps,trigger_sets,hotkey_presets,hotkey_presets/global,sequences}`・
  余分なし）であることを直接確認。
- `reviewer` = **完了可**。既存の `tests/test_config_service.py::EnsureSplitConfigDirsTest` が
  **実際に呼び出して `global` を含む全ディレクトリを assert しており、この変更を直接保護している**
  ことを確認（`tests_ui/test_startup_dir_skeleton.py` は `patch.object` でモック化するため保護しない）。

### 【計画07 の完了】（2026-08-16）
- **項目 0〜3 をすべて完了**（1 項目 = 1 コミット・**挙動保存**）。
  最終実測 = compile clean / `tests` **238** / `tests_ui` **229** / smoke pass / **循環 import なし**。
- **解消したメトリクス**: M2（`__init__` 99 行）/ M6（直値）/ M1 のうち `dialogs.py`（1026 → 最大 386 行）。
  **`config_service/__init__.py`（734 行）は対象外のまま**（`current.md` の「別タスク化候補」で追跡）。
- **フェーズ番号は消費していない**（次フェーズは引き続き `10_<topic>`）。
  **本計画自体が `/refactor_check` の産物**のため完了時の再実行は不要。
- **得られた知見**: ①**モジュール名前空間を patch するテストは分割の障害になる**
  （今回は 6 箇所。`patch.object` 形式なら影響を受けないため、**新規テストは `patch.object` を優先**する）
  ②**分割前に `Explore` で patch 箇所と依存を洗い出す**手順は有効だった（実装が 1 発で通った）
  ③**stale な `__pycache__` が旧モジュールを生存させ得る**ので、パッケージ化の実測では
  **`.pyc` を削除して結果不変を確認する**とよい。

## 2026-08-16〜 (phase 10: 参照元の掃除)

規範: [phase.md](../../instructions/phase/10_reference_link_cleanup/phase.md) /
主入力 = 暫定仕様 09（`instructions/history/09_reference_link_cleanup.md`・**v0.4**）。**暫定仕様先行モード**。

### 【起票時】idea_07 の昇格と設計確定（ユーザー確定 2026-08-16）
- **検査範囲 = 現在の構成セットの子のみ**（ユーザー判断）。根拠 = ①**子は config 外にも置ける**ため
  ディレクトリ走査でも**全網羅にならない** ②**keymap_set の列挙手段が無い**
  （`keyseq/` に `os.listdir` / `glob` / `os.walk` が 1 箇所も無い）③目的は
  「実際に使っているものが余計な処理を抱えないようにする」こと。
- **孤児削除は行わず警告表示のみ**（v0.1 で「削除も選べる」と確定したが**差し戻して再判断**）。
  理由 = **この検査範囲では孤児判定が原理的に成立しない**（対象は現在のセットの索引に載っている＝使用中。
  かつ `_parent_refs` は best-effort で「どこからも参照されない」証明にならない。
  **sequence の親は trigger_set** なので trigger_set 未保存なら使用中の sequence の参照元が全滅する）。
  → 孤児検出には**逆方向検査**が要るため **[idea_12](../../instructions/backlog/idea_12_orphan_child_file_sweep.md) へ分離**
  （ユーザー方針: **全検査と現在のセットのみを段階的に両方作る**）。
- **確認 UI は 1 枚**（読み取り専用の一覧 + 実行 / キャンセル）。削除を外して**非破壊・冪等**になったため
  行ごとの取捨選択は設けない。**消える参照元のパスは全件提示**する。
- `deep-reviewer`（起票時）= **修正要** → v0.2 で反映。**最大の指摘 = 子の列挙を
  `resolve_child_save_targets` にしていたのは誤り**（「次に保存するとしたらどこへ書くか」であり、
  **未実体化の子へ既定パスが割り当てられて無関係な既存ファイルを書き換える**）→
  **runtime の source_path 3 種**へ訂正。ほかに依存方向の逆流是正 / **現在の上位への参照は除去しない** /
  **消えるパスの全件提示** / 目的と受入条件を検証可能な形へ。
- `codex-adversarial-reviewer`（確定前）= **needs-attention（High 3）** → v0.4 で**全件反映**:
  ①**保護対象を検査時点で分離**（実行では残すのに UI が「消える」と出す乖離を解消）
  ②**未保存セットでは先に保存を確認**（`parent_ref` が空だと `_parent_refs_for_save` が
  保存先を読み直さず、**個別保存で掃除前の refs が再書き込みされて巻き戻る**。**ユーザー案を採用**）
  ③**除去直前に JSON 全体を読み直す**（全体置換なので確認中の外部変更を消し得る。
  版情報の照合までは行わず、残る窓は §5.8.3 / §5.10.3 と同水準の既知の性質として除外）。
- `reviewer`（phase.md の整合確認）= **修正して採用**。指摘 1 件（`current.md`「次フェーズ候補」の
  idea_07 行が着手済みに追従しておらず**文書が自己矛盾**）を反映。

### 【task_01】完了（2026-08-16）= 検査ロジック（application 新規モジュール）
- `config_service/parent_refs_cleanup.py` を**兄弟モジュール**として新設（`service` を第 1 引数に取る /
  `__init__` を import しない / **`__init__.py` へ委譲を足さない**＝737 行で分割保留中のため）。
- 公開面 = 判定名 4 定数 + 凍結データクラス `ParentRefsCleanupInspection`
  （`kind` / `stored_path` / `alive_refs` / `stale_refs` / `protected_refs` / `state`）+
  `inspect_parent_refs(service, runtime, *, config_root, keymap_set_path)`。
  **表示都合を持たせない**（行モデルは presentation 側）。
- 規則: **列挙は source_path 3 種のみ**（`resolve_child_save_targets` 不使用）/
  **keymap → trigger_set → sequence** の順で固定 / **`canonical_path` で重複排除（先着優先）** /
  **保護対象は実在しなくても `protected_refs` へ** / 判定名は優先順の表どおり
  （**stale + protected で alive 無しは `ALL_STALE` ではなく `TARGET`**）/
  戻り値から `CLEANUP_SKIP` を除外。
- 実測: compile clean / `tests` **247**（238 → **+9**・追加テスト数と一致）/ `tests_ui` **229**（不変）/
  smoke pass / **既存ファイルの変更 0 件** / **`user/` の誤生成なし**。
- `reviewer` = **完了可（指摘なし）**。特に **`os.path.exists` が解決後のパスにのみ適用**され、
  **`canonical_path` の値が保存値・戻り値へ混入していない**こと、
  **`stored_path` と各 refs が記録表記のまま**返ることを確認
  （Codex が自己申告した「過剰な正規化」は実際には入っておらず、テストの弱化も無し）。

### 【task_02】完了（2026-08-16）= 除去 API（`prune_parent_refs`）
- 同モジュールへ追加: `prune_parent_refs(service, inspections, *, runtime, config_root, keymap_set_path)`
  + 凍結データクラス `ParentRefsPruneResult`（更新したファイル / 失敗したファイル）
  + 失敗理由の定数 3 種（`PRUNE_FAILURE_UNREADABLE` / `_INVALID_DATA` / `_SAVE_FAILED`。
  **表示文言は持たせない**＝文言は task_03）。
- **判定は task_01 と共用**（`_classify_parent_refs` へ抽出）。**二重実装しない**のが要件
  （検査と実行で食い違うと UI の表示と結果が乖離するため）。
  **抽出は機械的で検査側の挙動は不変**（`reviewer` が diff の削除行と現在のコードで突き合わせ確認・
  task_01 の 9 テストも 1 件も削除 / 弱体化されていない）。
- 規則: **除去直前に JSON を丸ごと読み直す**（検査時のスナップショットを書き戻さない＝
  **全体置換で外部変更を消さない**）/ **`None`・非 dict は書かずに失敗記録** /
  **読み直した内容で判定をやり直す** / 残すのは**実在 + 保護対象**（記録順・記録表記のまま）/
  **除去 0 件なら書かない（冪等）** / **全件除去時は `[]`（キーは残す）** /
  **`_parent_refs` 以外を変えない** / **1 件の失敗で全体を止めない** / **runtime 不変**。
- 実測: compile clean / `tests` **257**（247 → **+10**・追加テスト数と一致）/ `tests_ui` **229**（不変）/
  smoke pass / 変更は 2 ファイルのみ / `user/` の誤生成なし。
- `reviewer` = **完了可**。参考指摘 1 件（refs に重複文字列があると `not in` で両方消え得るが、
  `_normalize_parent_refs` が読み込み時に重複除去するため**発生しない**）。

### 【task_03】完了（2026-08-16）= 提示テキストの整形（presentation の純関数）
- `keyseq/presentation/reference_cleanup_text.py`（新規）: `CLEANUP_EMPTY_MESSAGE` +
  `format_cleanup_plan(inspections)` / `format_cleanup_result(result)`。**戻り値は行のタプル**
  （結合・描画はダイアログ側＝task_04）。
- **配置の判断**: `presentation/dialogs/` ではなく **presentation 直下**へ置いた。
  `dialogs/__init__.py` が全ダイアログを import する＝**`tkinter` と `pynput` を巻き込む**ため、
  そこへ置くと `tests/` から純関数だけをテストできなくなる。
  `file_organization_rules.md` の「所有者の近くに置く」より**テスト可能性を優先**した
  （`child_save_rows.py` と同じ「純モジュール」の位置づけ）。
- 規則: **消える参照元は全件列挙**（省略・「ほか N 件」への丸めをしない＝**到達不能な媒体の参照元を
  消す事故に気づけるようにする**）/ **保護対象は「残す」側にだけ出す**（消える側に混ぜると
  実行結果と食い違う）/ **`CLEANUP_ALL_STALE` にだけ警告**（0 件になる・**子ファイルは削除しない**・
  **孤児判定はこの範囲ではできない**）/ **失敗理由の定数 → 文言の変換はこの層の責務** /
  **判定名で分岐し表示文言で分岐しない**。
- 実測: compile clean / `tests` **264**（257 → **+7**）/ `tests_ui` **229**（不変）/ smoke pass /
  **`tkinter` 非依存を実証**（`sys.modules['tkinter']=None` でも import 成功・grep ヒット 0）/
  既存ファイルの変更 0 件。
- `reviewer` = **修正して採用**。指摘 1 件（**`sequence` の表示名が「シーケンス」で、既存の
  `child_save_dialog._kind_label` と正本の用語「出力シーケンス」と不一致**）を
  **メインが修正**（実装・テストとも）。再実測で 264 pass（件数不変）を確認。

### 【task_04】完了（2026-08-16）= UI 配線（メニュー / 確認ダイアログ / 保存確認導線）
- 新規 3: `controllers/config_io/reference_cleanup_io.py`（`ReferenceCleanupIo.run_cleanup` = フローのみ）/
  `dialogs/reference_cleanup_dialog.py`（`tk.Toplevel` 継承・`destroy()` override で resume・
  **読み取り専用の一覧 + 実行 / キャンセル**・**`result` の既定は `False`**）/
  `tests_ui/test_reference_cleanup_flow.py`（7 本）。
  既存 4 ファイルは **+7 / -1**（`config_service/__init__.py` の**委譲 2 本** /
  `app.py` の配線 / `dialogs/__init__.py` の再輸出 / `menu_bar.py` の「設定」メニュー 1 行）。
- **フローの分岐**: 未保存（**`keymap_set_path` が空**。dirty ではない）→ 保存確認 →
  **いいえ / 保存失敗なら検査もせず終了** → 検査 → **0 件なら一覧を出さず通知** →
  確認ダイアログ → **キャンセルなら何も書かない** → 除去 → 結果通知。
  **runtime・dirty は不変**。**`ReferenceCleanupIo` はロジックを持たない**
  （検査・除去は application の委譲 / 文言は `reference_cleanup_text` の純関数）。
- **実測で 1 件 fail → テスト側の誤りと判明**: メニュー配線のテストが
  `menubar.entrycget(1, ...)` を「設定」と決め打ちしていたが、**top-level menubar の tearoff**で
  `0=tearoff / 1=ファイル / 2=設定` とずれていた。production の配線は正しく、
  **メインがテストを「カスケードとラベルで探す」形へ修正**（`_invoke_menu_command`）。
  → **今後メニュー項目のテストを書くときはインデックスを固定しない**。
- 実測: compile clean / `tests` **264**（不変）/ `tests_ui` **236**（229 → **+7**・ハングなし）/ smoke pass /
  `user/` の誤生成なし。`config_io/__init__.py` の `M` は**改行コードのみで内容差分ゼロ**。
- `reviewer` = **完了可**。参考指摘（委譲 2 本が 1 行スタイルで前後と不揃い）は**メインが整形**し再実測。
- **【運用】`reviewer` が 1 度セッション上限で中断**したため再実行して回収した。

### 【task_05】通し確認と 2 本立てレビュー（2026-08-16・**実機目視は未実施**）
- **通し実測**: compile clean / `tests` **267** / `tests_ui` **238**（ハングなし）/ smoke pass /
  `user/` の誤生成なし。phase 10 の実装差分は **11 ファイル・+1403 / -1**。
  新規 production 4 ファイルは **262 / 70 / 49 / 58 行**。
  `config_service/__init__.py` は **767 行**（phase 09 の 737 → **+30**。task_06 の `/refactor_check` 対象）。
- **`deep-reviewer` = 修正要**。採否:
  - **H1 = 修正して採用**: 受入条件 12 が「**特性テストで固定する**」と明記しているのに
    **「共有中 → 単独所有」のテストが 1 本も無かった**（本機能の目的そのもの）→ 追加。
  - **H2 / H9 / H12 = 修正して採用**: **実行後**の runtime・dirty 不変（従来はキャンセル経路のみ）/
    **`ConfigService` の委譲 2 本が全テストで未実行**（引数取り違えを検出できない）/
    メニューテストが共有 App の menubar を復元しない → いずれもテスト側で解消。
  - **H5 = 採用（目視項目を追加）**: フックの suspend / resume の対を確認する経路が
    **自動テストにも目視表にも無かった**（4 経路を項目 4b として追加）。
  - **H3 = 修正して採用（ユーザー確定）**: **保護対象だけの子が「対象」に数えられ、
    書き込みゼロなのにダイアログが出る** → **件数から外し、消える参照元が 0 件なら一覧を出さない**（v0.5）。
  - **H4 / H6 / H7 = 仕様へ明記（実装は変えない・ユーザー確定）**: sequence の巻き戻り前提 /
    確認中に上位が消えた場合 / 再判定で対象外になった子の通知 → **§3-5 既知の制約**として追記。
  - **H8 / H10 / H11 / H13 / H14 = task_06 送り・参考**。
- **`codex-adversarial-reviewer` = needs-attention（High 1）**。
  「**保存失敗時に 1 ファイルも書かれない保証が成立しない**」（保存は非トランザクションで、
  子を書いた後に失敗し得る）→ **条文を限定して決着（ユーザー確定）**。
  指摘の観察自体は正しいが、**当たり先は既存の保存フロー**であり、正本 **§5.8.6 が best-effort と明記**、
  暫定仕様 §6 も「保存経路を変更しない」をスコープ外に置いている。
  本フェーズが保証するのは「**掃除による書き込みが 1 件も発生しない**」ことなので、
  **受入条件 5b と §3-5 をその形へ限定**した（保存失敗で `prune` を呼ばないことは既にテスト済み）。
- **【運用・重要】Codex が並行してメインの仕様書編集を差し戻した**。
  委任中にメイン側で `instructions/history/09_*.md` を編集していたところ、Codex が
  「範囲外の差分」と判断して**巻き戻していた**（v0.5 の記述が消えた）。
  → **委任の実行中は、対象外であってもメイン側で同時に文書を編集しない**。
  編集した場合は**委任完了後に必ず差分を確認する**（今回は grep で消失に気付いて書き直した）。

### 【task_05】完了（2026-09-05）= 実機目視 14 項目すべて OK
- ユーザーが §3 の表 **14 項目を実機で実施し全項目 OK**（不具合なし・**是正なし・コード変更なし**）。
  重点項目（7 = 保護対象 / 9〜11 = 未保存時の保存確認導線 3 経路 / 13 = 保護対象だけの子は一覧を出さない〔v0.5〕/
  4b = フックの suspend / resume 4 経路）も期待どおり。
- 受入条件 **1〜15 のすべて**を自動テストまたは実機目視で充足確認 → **task_05 完了**。
  結果は `tasks/task_05_integration_check.md` 末尾へ追記。
- 残るは **task_06 = 正本反映（最終）**。
