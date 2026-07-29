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

## 2026-07-29 (Phase β / phase 06: 進行中)

### 【task_05 起票前】パスが変わる子の上位保存必須（暫定仕様 05 §2・§8）を UI でどう扱うか
- 選択肢: ①一覧のラジオで「保存しない」を静的に選べなくする ②`SavePlanError` をユーザー向けに差し戻す
  ③依存が起きた行だけ動的に無効化 ④**OK 押下時に確認ダイアログ** → **④を採用**（ユーザー確定）
- 親子で扱いを分ける: **親 keymap_set は問わない**（「保存」操作自体が明示済みのため、子の別名保存で
  索引パスが変わっても無確認で保存してよい）/ **trigger_set（＝孫 sequence に対する子）は問う**
  （保存が必要になった理由が分かる必要があるため。選択肢は 保存 / 別名保存 / 選び直す）
- 一覧のラジオは静的に無効化しない（「保存しない」は常に選べる）。`SavePlanError` は
  **UI から到達しない内部不変条件の番人**として残す。
- 併せて確定: **dirty でない子は `ACTION_SKIP`。ただし保存先ファイルが未作成なら `ACTION_SAVE`**
  （skip すると keymap_set の索引パスが空になり索引切れを起こすため）。受入条件 2 の実装形。
- 起票: [task_05_save_dialog_ui.md](../../instructions/phase/06_child_file_save_dialog/tasks/task_05_save_dialog_ui.md)

### 【task_05 定義】codex-adversarial-reviewer 指摘 2 件（high）→ **両方採用**（ユーザー確定 2026-07-29）
- **①保存先解決の陳腐化**: `_resolve_sequence_save_path`（`config_service.py:1169-1192`）は
  trigger_set の保存先が `config/user/trigger_sets/` 配下かで sequence の既定保存先を切り替えるため、
  **trigger_set を別名保存すると他の子の保存先が変わる**。`targets` を初回 1 回だけ解決する設計では
  一覧の表示パス・共有状況・非 dirty 子の SKIP/SAVE が陳腐化し、索引切れと無確認上書きが起こり得た。
  → `resolve_child_save_targets` / `collect_child_save_rows` に `save_plan` を追加し、
  **保存経路を while ループ化して trigger_set の保存先が変わるたび再解決 + 一覧再表示**する。
- **②依存確認の既定ボタン**: `askyesnocancel` は「はい（上書き）」が既定のため、所有元不明・別構成の
  trigger_set を Enter で上書きできてしまい、§5 の安全側既定が依存経路だけ後退していた。
  → `default=messagebox.NO`（`SHARE_UNKNOWN` / `SHARE_OTHER_PARENT` のとき）へ切り替える。
  専用ダイアログの新造はしない。
- 不変条件として task_05 の設計メモへ明記: **提示した保存先と実際に書く先を一致させる** /
  **未知・別の上位の保存先を明示操作なしに上書きしない**。

### 【実機目視フィードバック】暫定仕様 05 を **v0.3** へ改訂（ユーザー確定 2026-07-29）
実機目視で 5 件の指摘。3 件が設計/実装変更、1 件は仕様書と整合、1 件は正本反映で文言化。

- **①別名保存後の一覧再表示**（冗長）→ **廃止**。task_05 で入れた不変条件「提示した保存先と実際に
  書く先を一致させる（再解決のたび一覧再表示）」を緩和する。理由: 別名保存は明示操作であり、
  その帰結として子の保存先が追随するのは同一操作の一部。→ **v0.3-A**。
  安全弁として **v0.3-A2**（再計算で実体パスが変わった「保存」行のうち、新パスに既存ファイルがあり
  共有状況が「単独」以外の行だけ、**行単位の小ダイアログ**で上書き確認。一覧の再表示・選び直しはしない。
  0 件なら確認も出ない）。**「完全廃止（例外なし）」は敵対的レビューの critical 指摘を受けて不採用**、
  ユーザーが「行単位の小ダイアログ」を選択。
- **③デフォルト配下なのに「デフォルト外」確認が出る / ④新規シーケンスが `user/trigger_sets/sequences/`
  へ落ちる** → **同一原因の実バグ**（仕様変更ではない）。`os.path.commonpath([p, root]) == root` の
  素の文字列一致が、Windows でパス文字列の大文字小文字差により config_root 内を「外」と誤判定する。
  カスケード: 内外判定の誤り → `_parent_refs` / 起動設定が絶対パスで記録 → その絶対パスが
  `source_path` に載る → 次回保存で既定領域判定が外れ、新規シーケンスが `trigger_sets/sequences/` へ。
  **2026-07-29 の実機痕跡（main チェックアウトの `config/`）と手元の再現で確認済**。
  **発生経路（ユーザー回答 2026-07-29）**: VS Code の ▶ 実行。ドライブ文字が小文字（`c:\`）で渡るため
  `config_root` が `c:\...` になり、tkinter のファイルダイアログが返す `C:/...` と食い違う。
  → **v0.3-B**（比較専用の canonical identity を定義し 7 箇所へ適用。JSON 保存表記は §4 のまま）。
- **②何も変更せず保存 → 「保存しました」** → **仕様書とは整合**（§3-1 / 受入条件 2 は子ファイル保存
  ダイアログを出さないことのみ規定）。ズレていたのは task_06 目視チェックリスト #2 の文言。
  → §3 末尾に「変更なし保存でも親・起動設定・未作成の子は書かれ、完了ダイアログは出る」を明記。**修正しない**。
- **⑤ダイアログの見た目**（10 行以上で横はみ出し）→ **Phase β 内の追加タスクで対応**（task_06 の当初方針
  「NG なら idea 起票」から変更）。→ **v0.3-C**（固定初期サイズ・リサイズ可・縦スクロール・
  対象名/パスの省略表示＋ツールチップ）。

### 【暫定仕様 05 v0.3】codex-adversarial-reviewer 指摘 4 件 → **全採用**（ユーザー確定 2026-07-29）
- **critical**: v0.3-A が「未提示パスへの無断上書き」を復活させる（新規シーケンスに「保存」を選び、
  同じ一覧で trigger_set を外部へ別名保存すると、再計算先の既存ファイルを無確認で上書きする。
  「保存」選択のため `asksaveasfilename` の上書き確認は通らず、§5 の所有判定は旧パスにしか効かない）
  → **v0.3-A2** で反映。
- **high**: `normcase` だけでは、既に絶対で記録済みの `_parent_refs` と相対表記の同一パスを重複排除
  できない。保存計画の重複検出も区切り文字しか正規化していない（`config_service.py:1046,1231`）
  → **v0.3-B** の canonical identity と適用箇所 7 点の列挙で反映。
- **medium 2 件**: 受入条件 13（ケース差を決定的に再現できない）/ 14（省略基準・サイズが未定義で
  自動判定不能）→ 受入条件を書き換え（13 = Windows 統合テスト + 非 Windows はヘルパー単体テスト /
  14 = 構造テストと目視の分離。数値はタスク定義で確定）。

---

## 運用メモ

- 1 タスク完了時に reviewer 判定をここへ転記する
- 想定外の先行実装を発見した場合の判定もここへ記録する
- 後続フェーズの設計で参照する
