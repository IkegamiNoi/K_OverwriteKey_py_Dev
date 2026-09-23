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
| 10_reference_link_cleanup | [10_reference_link_cleanup.md](decisions_archive/10_reference_link_cleanup.md) | 参照元の掃除（2026-09-05 完了・**新機能・スキーマ不変**）。子JSON の陳腐化した `_parent_refs` を設定メニューからまとめて除去する保守機能。**検査範囲は現在の構成セットの子のみ**（列挙は **runtime の source_path 3 種**。**`resolve_child_save_targets` は使わない**＝未実体化の子へ既定パスが割り当てられ**無関係な既存ファイルを書き換える**。起票時 `deep-reviewer` の最大指摘）。**全網羅ではない**ことを正本へ既知の制約として明記。**孤児削除は行わず 0 件警告のみ**（この検査範囲では孤児判定が原理的に成立しない → 逆方向検査は **idea_12** へ分離）。**確認 UI は 1 枚**（読み取り専用・消えるパスを全件提示）。**現在の keymap_set / trigger_set への参照は実在しなくても保護**（検査時点で分離）。**未保存の構成セットでは先に保存**（`parent_ref` が空だと個別保存が掃除前の refs を再書き込みして**巻き戻る**）。**除去直前に JSON 全体を読み直して再判定**（外部変更を全体置換で消さない）。**除去 0 件なら書かない（冪等）/ 全件除去は `[]`** / **runtime・dirty へ反映しない**。**設計は v0.5 まで 4 回改訂**（v0.2 = `deep-reviewer` / v0.4 = `codex-adversarial-reviewer` High 3 / v0.5 = task_05 の 2 本立て）。**実機目視 14 / 14 OK**（是正なし）。正本 `data_schema.md` **§5.8.1 改訂** + `features.md` §4.6 + `codebase_map.md` へ昇格済。**契約として明記し実装は変えない**: sequence の巻き戻り前提 / 確認中に上位が消えた場合 / 再判定で対象外になった子の通知 / 前提の保存経路は §5.8.6 の best-effort（`codex-adversarial-reviewer` の High 1 は条文の限定で決着）。refactor_check: 判定は本アーカイブ末尾 |
| 11_orphan_child_file_sweep | [11_orphan_child_file_sweep.md](decisions_archive/11_orphan_child_file_sweep.md) | 孤児ファイルの棚卸し（2026-09-08 完了・**新機能・スキーマ追加**）。どの keymap_set からも参照されていない子を**上位 → 子の逆方向検査**で検出し、**可逆な隔離**を経て削除できるようにした。**本アプリ初のディレクトリ走査かつ初のファイル削除機能**。**走査は 4 経路**（`keymap_sets/` 直下 / 起動エントリ / **現在開いているセット** / ユーザー指定ディレクトリ）で**参照集合は 2 段辿り**（sequence のパスは trigger_set にしか無い）。候補側は**既定 4 ディレクトリ直下のみ + 形状検証**、`hotkey_presets/global/` は除外、**OFF の個別プリセットパスも参照ありと数える**（意図的 superset）。**隔離ルートは `config/quarantine/`**（`user/` の外・遅延作成）で、**マニフェストを移動より先に原子書込み**し（書けなければ 1 件も動かさない）、隔離対象は**〔提示済み〕∩〔再判定でも孤児〕**に限定。**復元は `state` を信用せず実体の有無で判定**し、**`original_path` は候補側配下でなければ拒否**（`is_path_within` は**同一パスも配下と判定する**ため実体基準の境界検証を併用）。**削除は実行単位 ID + 4 検証**（**④〔有効なマニフェスト〕だけ強い確認で上書き可**・①②③は不変）で**ゴミ箱へ送らない不可逆削除**。**壊れた親があると無傷の子が孤児候補になる**残存リスクは**警告を必須化したうえで受容**（degraded 方式は不採用）。**TOCTOU 2 件・マニフェストのエントリ単位検査なし・一覧に出ない残骸・削除経路のリダイレクト単位**は**実装を変えず契約として明記**。**実機目視 M1〜M8 + M2b は全件期待どおり**（M6 から「マニフェストが読めない」の定義を明確化）。正本 `data_schema.md` **§5.8.9 新設** + §5.8.1 改訂 + §5.4 / §5.10.1 + `features.md` §4.6 + `architecture.md` §3.2 + `codebase_map.md` へ昇格済。**後続**: idea_14（公開面への集約・phase 10 も対象）。refactor_check: 判定は本アーカイブ末尾 |
| 12_config_service_public_surface | [12_config_service_public_surface.md](decisions_archive/12_config_service_public_surface.md) | config_service の公開面の集約（2026-09-08 完了・**挙動不変のリファクタ**）。presentation が `config_service` の内部モジュールから直接 import していた**判定名・理由コード・結果型（定数 34 / 型 9）**を、新設した **`contracts.py` へ定義ごと移動**（**再輸出を作らない**）。参照は **`from . import contracts` + `contracts.NAME`** に統一（`from .contracts import NAME` は名前が再束縛され `hasattr` 偽の固定テストが書けないため不採用）。**定義元で未使用の定数**（`SOURCE_REDIRECTED` 等）があるため段階分割できず、**1 コミットの原子的変更**とした。**内部表現**（`QUARANTINE_DIR_NAME` / `UNIT_ID_PATTERN` / `ENTRY_*` / `CANDIDATE_DIRS`）は実装側に残し、**同値の理由コード**（`"invalid_unit_id"` / `"no_manifest"`）も**統合しない**（ラベル分岐が壊れる）。**逆戻り防止テスト 3 本**（共有参照の固定 + presentation の **AST 走査 R1〜R3 + 属性アクセスの 4 経路** + **検査関数の自己検証**）を追加し、**`INTERNAL_MODULE_NAMES` がパッケージの実ファイル一覧とずれたら落ちる**アサーションで「新モジュールが属性アクセス経路だけ素通りする穴」を塞いだ。**動的 import は検出できない**限界は明記。正本 `architecture.md` **§3.2 の例外条項と idea_14 追跡行を削除**（**`config_service` 限定表現は保つ**＝`application` 一般へ広げると `save_plan.ACTION_*` の 5 件が新規違反になる）+ `codebase_map.md`（12 → 13 ファイル）へ昇格済。**実機目視は不要**（挙動不変・UI 文言不変）。refactor_check: 判定は本アーカイブ末尾 |
| 13_contracts_boundary_ast_coverage | [13_contracts_boundary_ast_coverage.md](decisions_archive/13_contracts_boundary_ast_coverage.md) | 公開面の逆戻り防止テストの検査範囲の拡張（2026-09-08 完了・**テストのみ・プロダクション不変・仕様変更なし**）。phase 12 の完了レビューで両レビュアーが独立に指摘した**静的な素通り経路**を塞いだ。**A-1 = `ast.Attribute` の連鎖を完全修飾名へ解決** / **A-2 = `asname` 追跡** / **R4 = 相対 import を絶対名へ解決**（解決不能時は `config_service` セグメント以降の**末尾一致へ縮退**＝**素通しにしない**）/ **相対 import で束縛したエイリアスも解決**し、エイリアス表を**名前 → 束縛先の集合**にして**同名の上書きで違反が消える**問題も塞いだ〔task_01c〕。**既存の「素の名前」検査は残して和集合**にした（**相対 import でモジュールを束縛した場合の唯一の検出経路**。presentation の `config_service` という名前の変数・引数 **29 箇所**〔`ast.Name` 21 / `ast.arg` 8〕は**`ConfigService` のインスタンス**でモジュール参照ではない）。**同一（行番号, 内部モジュール名）は 1 件に畳む**。**兄弟参照 `from .io_dialogs import ...`（16 件実在）を誤検出しないこと**を許可例で固定し、**深さは level=4 検出 / level=3 非検出**を実測（オフバイワンなし）。**残る限界 4 つ**（動的 import / 実行時に組み立てた名前 / **代入による再束縛** / 縮退時の未解決）は**docstring に明記**し、解消は必要時に新規 idea 起票とした。**残存リスク**: `ConfigService` に内部モジュールと同名の公開メンバが増えると素の名前検査が誤検出する。**テストメソッドは 3 本のまま = `tests` 417 件不変**。**正本改訂なし**（`architecture.md` §3.2 は phase 12 で確定済で不変。**検査精度を上げただけ**）。**task_01b / task_01c は着手後にユーザー判断で追加した枝番**。refactor_check: 判定は本アーカイブ末尾 |
| 14_nested_modal_grab_restore | [14_nested_modal_grab_restore.md](decisions_archive/14_nested_modal_grab_restore.md) | ネストしたモーダルの grab 復元（2026-09-12 完了・**presentation 限定・スキーマ不変・挙動変更**〔モーダル性の是正〕）。モーダルの中からモーダルを開いて閉じると Tk は grab を解放するだけで**直前の保持者へ戻さない**ため、親ダイアログを開いたままメインウィンドウを操作できた欠陥を是正。**復元は子側**（案 X）で行い、新設 `keyseq/presentation/modal.py` の **`grab_modal(window, parent=None)`** へ**系統 A〔`dialogs/` 9 クラス〕+ 系統 B〔`controllers/config_io/` 4 箇所〕の全 13 箇所**を寄せた（`wait_window` 側 20 箇所は無変更・直呼びは 0 件）。**記録はクロージャ**に持ち**`<Destroy>` イベントで戻す**〔`destroy()` override ではないので **× 閉じでも働く**〕。**§3-1〔誰へ戻すか＝記録した保持者が `None` 以外なら戻す〕と §3-7〔そもそも戻してよいか＝破棄時点の保持者〕は別条件**（§3-1 を「自分自身のときだけ」に絞ると**最も実害の大きいネスト経路 3 が復元されない**）。**フェーズ途中でユーザー確定により §3-6 を「初期化失敗の回収〔破棄 → 復元 → 再送出〕」から「grab 取得後に初期化を残さない構造 + 静的検査」へ改訂**（v0.5・**実行時の挙動は不変**・**回収機構は実装しない**）。二次レビューの指摘を受け **`<Destroy>` を `add="+"` へ**（上書きすると復元が無言で消え **idea_16 の対策と衝突する**）+ **3 段 LIFO / 真の × 閉じ / §3-4 の防御分岐**のテストを追加。**変異検査 3 種**で偽 pass を排除。`tests_ui` **288 → 306**。**stdlib ダイアログは対象外**（実機目視で 3 経路は問題なし・**1 経路は親が既に破棄済みで観点が成立せず未確認**）。正本 `features.md` §4.6「モーダルダイアログの作法」+ `data_schema/5_10_03_save_contract.md` + `codebase_map.md` へ昇格済。暫定仕様 12 は凍結済。**分離**: **idea_16**〔× 閉じで `destroy()` override が走らずフック停止カウンタがずれる既存不具合〕/ `ActionDialog` 親付け替え / スケルトン共通化 / M-6〔静的検査の発見ベース化〕。refactor_check: 判定は本アーカイブ末尾 |
| 15_dialog_teardown_on_close | [15_dialog_teardown_on_close.md](decisions_archive/15_dialog_teardown_on_close.md) | ダイアログ後始末の確実な実行（2026-09-13 完了・**presentation 限定・スキーマ不変・挙動変更**〔閉じ方によらず後始末が走る / 終了中はフックを再開しない〕）。× 閉じで Python の `destroy()` override が呼ばれず**フック停止カウンタがずれたまま残る**欠陥の是正（8 クラス中 5 クラスが `protocol` 未登録）。**後始末を破棄イベントへ寄せ**（案 B）、**登録は `HookController` へ集約**（`suspend_hook_for_dialog(window)` が停止と解除予約を原子化・**省略時は現行と同じ**）、**解除は `after(0)` で遅延**（フック開始が同期でメッセージボックスを開き得る / phase 14 の grab 復元と競合させない）、**終了ガードは `start_hook` の内部**（同期・遅延の両経路に効く）。**空になる override 4 件は削除**。後始末の分類（**T1 = 状態の後始末は閉じ方によらず走る / T2 = ウィジェットに触る後始末は閉じる操作の側**）を正本 `features.md` §4.6 へ昇格し、`key_input.md` §7.2 へ 3 条項（閉じ方によらず解除 / **停止要求が残る間は置換もアクション実行も行わない〔元入力は素通し〕** / 終了確定後は再開しない）。**静的検査は `dialogs/` 8 クラスに限定**（`controllers/` を含めると phase 14 の既存検査と正面衝突する）。**終了ガードの検査は `start_hook` の呼び出し回数で見てはならない**（ガードが内部にあるため呼ばれる。観測点は `hook_coordinator.start` と `hook_active`）。`tests_ui` **306 → 321**・変異検査 4 件。実機目視 4 項目問題なし。暫定仕様 13 は凍結済。**分離**: スケルトン共通化 / 静的検査の発見ベース化 / idea_17 / `key_capture`・`keyboard_window` / `_stop_capture`・`_stop_recording`。refactor_check: 判定は本アーカイブ末尾 |
| 16_dialog_transient_parent | [16_dialog_transient_parent.md](decisions_archive/16_dialog_transient_parent.md) | ネストしたダイアログの前面維持（2026-09-15 完了・**presentation 限定・スキーマ不変**・production 実質 6 行）。ネストして開いた窓が `grab_modal` の第 2 引数へ**常に App を渡していた**ため「App より前」としか指定されず、**呼び出し元を掴んで動かすと前に出る**欠陥を是正。**役割 2（前面維持 = `transient`）だけを付け替え、役割 1（所有関係 = `master`）と役割 3（App 参照）は動かさない**（役割 1 を動かすと**破棄が連鎖**し `features.md` の「内側優先」条項と衝突する。v0.1 の案 A は撤回）。対象は**食い違い 2 件とも**（アクション編集 → プリセット編集 / プリセット編集 → 上書き確認）で、**他 7 ダイアログへは広げない**。既定は非対称（`PresetManagerDialog` は既定 `parent` / `confirm_overwrite` はキーワード必須＝呼び出し元 1 箇所のため到達しない分岐を作らない）。**非 LIFO で閉じると前面維持の指定が消える点は受容**し、その根拠「UI からは到達しない」は**実機目視（2026-09-15）で裏付け**（grab 中は背面の × も最小化も押せず操作自体が不能）＝task_04 の指摘 1「根拠が誤り」は**取り下げ**。`transient_parent` の事前条件は**ガードを足さず docstring へ明記**（指摘 3）。`tests_ui` **321 → 324**・既存テストの変更は**引数契約の追随 4 件のみ**（アサーション非緩和）。正本反映は `codebase_map.md` の `modal.py` 節 + **`features.md` §4.6 へ前面維持の 2 条項**（当初は「改訂なし」の予定だったが、完了判定前レビューの指摘 1〔**正本に前面維持の規定が 0 件のまま閉じると、受容した制限の記述先が「条項を根拠に引かない」凍結文書だけになる**〕を受けて**ユーザーが改訂を採用**・`/spec_update` 実施）。暫定仕様 14 は v0.5 で凍結。**分離**: [idea_18](../../instructions/backlog/idea_18_escape_delivery_flaky_test.md)〔Escape 依存テストの負荷下 flaky・phase 15 時点から存在〕/ [idea_19](../../instructions/backlog/idea_19_minimize_restore_with_child_grab.md)〔子が grab を持つ状態で Win+D すると再表示できない〕。refactor_check: 判定は本アーカイブ末尾 |
| 17_minimize_grab_custody | [17_minimize_grab_custody.md](decisions_archive/17_minimize_grab_custody.md) | 最小化中の grab 預かり（2026-09-16 完了・**presentation 限定・スキーマ不変**）。**ダイアログを開いたまま Win+D すると復元できない**欠陥（シェルの復元要求が非表示の grab 保持者へ向かい App に `<Map>` が来ない）を、**App の `<Unmap>` / `<Map>` で最小化の間だけ grab を預かる**ことで是正（`modal.py` の `install_minimize_grab_custody`）。**預かるのは非表示になった保持者だけ** / **復元時に窓を触らない** / **stdlib ダイアログ（解決不能）なら触らない** / 保持者が消えていたら**台帳の最内**へ張り直す。フェーズ中に**預かりへの差し戻し**を 2 段で追加（task_02b = 最小化中に復元できなかった `previous` を戻す〔A案。B / C案は除外〕/ task_02c = **破棄済みでも戻す**〔二次レビュー H-1〕）。実機目視 M1〜M4 OK・**M5 は最小化の経路がなく実施不可**（欠陥ではない）。正本反映 = `features.md` §4.6（冒頭条項を「表示されている間は」で限定 + 最小化の条項 + 残存リスク M-1 + 範囲外 L-2）+ `codebase_map.md` の `modal.py` 節。暫定仕様 15 は v0.7 で凍結。refactor_check: 判定は本アーカイブ末尾 |
| 18_full_view_resizable_panes | [18_full_view_resizable_panes.md](decisions_archive/18_full_view_resizable_panes.md) | フル表示メイン領域の幅配分と境界線ドラッグ（2026-09-17 完了・**presentation + 純関数・config.json にキー 2 つ追加〔後方互換〕**）。ウィンドウ幅はトリガー一覧が受け、`PanedWindow` の境界線ドラッグ（個別バインドで押し出し防止・中ボタン無効・移動の間引き）で両端を変える。**希望幅と表示幅を分離** / 最終値の一括適用 / **ウィンドウ幅はリサイズごとに 500ms 間引き保存・終了時は保存しない**（v0.5・ユーザー案）/ 自動決定幅は保存しない・手で変えたら無効化 / `write_startup` 失敗表示中のフック停止。暫定 16 は v0.5 で凍結。refactor_check: 不要 |
| 19_full_view_header_width | [19_full_view_header_width.md](decisions_archive/19_full_view_header_width.md) | フル表示ヘッダの幅をウィンドウ最小幅に含める（2026-09-17 完了・**presentation 限定・JSON の形は不変**）。ウィンドウ最小幅 = max(メイン, ヘッダ)・配置は変えない（案 A）/ 縮小目標 max(画面幅, ヘッダ) / ドラッグ後の最小幅は縮小規則を通さない / フル表示ヘッダの切替ボタン 4 つを最大文言幅で固定（省略表示は固定しない）/ ドロップダウン 12 / 旧保存値が最小幅未満なら起動時に広げた幅で保存値を更新（ユーザー選択）。暫定 17 は v0.3 で凍結。refactor_check: **推奨**（M3）→ 提案書 10 を task_07 で実施済 |
| 20_full_view_min_height | [20_full_view_min_height.md](decisions_archive/20_full_view_min_height.md) | フル表示ウィンドウの縦方向の最小サイズ（2026-09-18 完了・**presentation 限定・JSON 不変**）。一覧の height を 6 / 6 / 9 にし最小の高さ = 要求高さ（案 A）/ 一時メッセージは 1 行分で測る / フル表示へ戻るときは表示更新後に測る / 自動で広げた高さは最小が下がっても縮めない / 高さは保存しない・省略表示で解除・画面超過ははみ出し受容。暫定 18 は v0.5 で凍結。refactor_check: 不要 |
| 21_extended_key_send | [21_extended_key_send.md](decisions_archive/21_extended_key_send.md) | 拡張キーを拡張キーとして送る（2026-09-19 完了・**infrastructure 限定・hotkey の書式 / JSON 不変**・直接改訂モード）。原因 = `keyboard` が KEYEVENTF_EXTENDEDKEY を付けない（実機確定）/ 対象 = 拡張キー全般 18 名・hotkey とキーマップ送信の両方 / 表はアプリ側（`_EXTENDED_KEYS`）・拡張キーを含む hotkey だけ自前送信 / 記述順に押し逆順に離す・例外時も解放 / `windows` は左・`ctrl`/`alt`/`shift`・テンキー Enter・`/`・`alt gr` は従来どおり / 正規化は公開 `keyboard.normalize_name`。正本 = `key_input.md` §7.7（新設）。実機目視 7 項目 OK。refactor_check: 不要 |
| 22_mouse_drag_action | [22_mouse_drag_action.md](decisions_archive/22_mouse_drag_action.md) | マウスのドラッグ操作（2026-09-19 完了・**挙動追加＋スキーマ追加**・暫定仕様先行モード）。既存の `mouse_click` を拡張して `drag` / `to_x` / `to_y` / `drag_speed` を追加（新種別を作らない・`drag` false では新キーを出力しない＝生成停止）/ 速度は px/秒（既定 1000）で**所要時間 = 距離 ÷ 速度を 0.15〜5.0 秒へクランプ**（算出は application 層。下限 = 補間なしのワープ回避 / 上限 = UI スレッド占有）/ `dragTo` を使わず押す・移動・離すへ分解し `finally` で必ず離す / **ドラッグ中だけ `pyautogui.FAILSAFE` を無効化し復元**（解放が FailSafe に遮られるため。失うもの = 四隅の緊急停止）・`ctypes` を使わず OS 分岐を増やさない / `to_x` / `to_y` 不正は実行時エラーで何も送らない（クリックへフォールバックしない）/ マウス操作は send guard 対象外（明文化のみ）。正本 = `data_schema.md` **§5.11 新設** / `codebase_map.md`「マウス操作」節。暫定 19 は v0.5 で凍結。実機目視 全 9 項目 OK（⑦で物理マウスとの競合により離す位置がずれることを確認し §5.11.5 へ明記）。refactor_check: 不要 |
| 23_sequence_payload_action_normalization | [23_sequence_payload_action_normalization.md](decisions_archive/23_sequence_payload_action_normalization.md) | 個別 sequence JSON 単体読込の actions 正規化（2026-09-19 完了・**挙動追従のみ・スキーマ不変**・直接改訂モード・起票元 idea_24）。正規化（dict 以外の除去 + `label` 整形）を domain の公開関数 `normalize_actions` へ切り出し、`ensure_config_compatibility` と `ConfigService._normalize_sequence_payload` の双方から呼ぶ（案 A。案 B = 個別読込も `ensure_config_compatibility` を通す、は payload の形が噛み合うか不明で影響大のため不採用）/ 単体読込の戻り値に `label: ""` が付く挙動変更は既存経路と同じ形になるため許容し既存テストの期待値を更新 / **保存は payload を書いた後に正規化する順序のためディスクの JSON は不変**（実測）/ 二重正規化は冪等。正本 = `data_schema.md` §5.11 の【実装未追従】注記を削除。実機目視 不要。refactor_check: 不要（M1〜M6 該当なし・PHASE_BASE `cd9e6f2`） |
| 24_json_type_normalization | [24_json_type_normalization.md](decisions_archive/24_json_type_normalization.md) | JSON 読込の型不正の扱い統一（2026-09-19 完了・**頑健化のみ・スキーマ不変**・暫定仕様先行モード・起票元 = phase 23 後のユーザー指示）。文字列前提の処理へ非文字列が渡り **9 箇所で AttributeError** / `str()` 強制で **repr 文字列が runtime に載る**問題を解消。domain へ `coerce_key_name` / `coerce_label`（非 str は `""`）を新設し**全経路へ一斉適用**（案 F。案 G = 個別読込限定は**共有ローダーのため成立しない**ので不採用）/ `normalize_key_name` のシグネチャは不変（呼び出し 158 箇所）/ trigger の `key` 不正 = 空扱いで残す・`sequence_path` 不正 = 空扱い・`mappings` の target 不正 = 対ごと除去 / `suppress` 等 bool・int は現状維持（`null`/`0`/`""`/`[]` は false）/ falsy な非文字列は元から空扱いで挙動不変。**2 本のレビュー指摘は全件実測で CONFIRMED**（例外は 1 箇所でなく 6 箇所・`suppress` の記述が実装と逆・参照先 sequence からの repr 再流入・経路別スコープの破綻）。reviewer 差し戻し 1 件（split 読込の keymap `label` 漏れ）+ **完了判定前 `deep-reviewer` で棚卸し不足が判明し task_03 を追加**（旧形式 `trigger_key` / hook キー 2 種 / `active_keymap_id`）。同レビューで正本の記述誤り 3 件も訂正（`actions` の要素除去は形状由来・単一 JSON の `keymaps[].id` だけ扱いが違う・形状の倒し方の昇格漏れ）。パス系は idea_25 へ分離。正本 = `data_schema.md` **§5.1 型不正の共通規則（新設）** / §5.2 / §5.6（**keymap 節を新設**）/ §5.11。暫定 20 は v0.3 で凍結。実機目視 不要。refactor_check: 不要（M1〜M6 該当なし・PHASE_BASE `61a7c79`） |
| 25_path_field_type_normalization | [25_path_field_type_normalization.md](decisions_archive/25_path_field_type_normalization.md) | パス系フィールドの型正規化（2026-09-19 完了・**頑健化のみ・スキーマ不変**・直接改訂モード・起票元 idea_25）。**例外になる箇所はゼロ**で、`str()` 強制により **repr 文字列がパス / スイッチキーとして runtime に載る**問題を解消。**使い分け = パスは `coerce_label`（trim のみ）/ キー名・id は `coerce_key_name`（trim + 小文字化）**（パスを小文字化すると壊れる。§5.7 の `normcase` は比較専用）/ `keymap_switch_keys` の値も `coerce_key_name` へ（従来は membership check による**偶然の防御**）/ 案 B（現状維持 + 未定義と明記）は **§5.1 を後から緩めることになり不採用**。完了後レビューで**参照突合経路**（`reference_scan.py`・生 JSON を直接読む別実装）の取りこぼしを検出し task_01b で追加対応。正本 = `data_schema.md` §5.5 / §5.7 へ型の規定を追記（**§5.1 の本文は不変**）。残件 = `startup_io.py` の `keymap_set_path`（presentation 層）。実機目視 不要。refactor_check: 不要（M1〜M6 該当なし・PHASE_BASE `f0e5887`） |
| 26_startup_entry_preservation | [26_startup_entry_preservation.md](decisions_archive/26_startup_entry_preservation.md) | 起動エントリ（`config/config.json` の `keymap_set_path`）の保存時据え置き（2026-09-21 完了・**仕様変更・スキーマ不変**・直接改訂モード・起票元 = ユーザー要望）。保存のたびに起動対象が直近の保存先へ書き換わる問題を解消し、**変更経路をメニュー「起動時に読む構成セットを指定…」1 本へ**寄せた。**空 / 起動時に読めなかった場合のみ保存で更新**（自己修復）/ 「読めない」の判定は **案 A = 起動時の実読込結果を真偽値で保持**（案 B の保存時 `os.path.exists` は**壊れた JSON を自己修復できない**ため除外）/ **別名保存でも据え置き**（次回起動は別名保存前のファイル）/ 可視化 UI・解除手段は**除外**。実装 = `StartupIo.entry_loaded`（**presentation は事実のみ**）→ `startup_entry_loaded` を application へ貫通し、**判定は `split_payloads.py:363` の 1 箇所**。更新契機は 3 経路（起動読込成功 / 保存成功 / メニュー指定成功）で **`write_startup` には入れない**（一律に立てると自己修復が失われる）/ **新引数の既定は False** で既存経路は挙動不変。**据え置くのは `keymap_set_path` だけ**。正本 = `data_schema.md` §5.4 の条項差し替え + `5_08_09_orphan_sweep.md` の根拠文 1 行（**走査範囲 4 経路は不変**）。実測 `tests` 518 / `tests_ui` 449 / smoke pass・実機目視 **OK**。残件 = `.strip()` 非対称（**到達不能**・候補送り）/ phase 25 残件①（`startup_io.py` の型正規化）は未着手。refactor_check: 不要（M1〜M6 該当なし・対象 5 ファイル・PHASE_BASE `e0c19ba`） |
| 27_keymap_set_load_history | [27_keymap_set_load_history.md](decisions_archive/27_keymap_set_load_history.md) | 構成セットの読み込み履歴管理（2026-09-22 完了・**新規 JSON 追加**）。ファイルメニューへ「履歴から読み込む…」、直近 20 件 + ユーザーが作る分類を **リポジトリ初の `ttk.Treeview`** で扱う。保存先は `config/keymap_set_history.json`（固定・**config.json にキーを追加しない**・遅延作成）。記録契機 = **読込または保存が成功し空でないパスが確定したとき、その実保存先**（初期代入 / 新規作成 / Import / 例の復元 / **起動時の自動読込**は除外）。**先頭一致 no-op** で通常の起動はディスクに触らない。破損ファイルは `*.broken*.json` へ**退避してから**作り直す（連番 5 で打ち止め → 読み取り専用）。**永続化に成功してから UI を確定**し、ダイアログは操作のたびに永続化済みの内容を読み直して再描画する。**v0.5 改訂**の理由 = 起動時に記録すると `tests_ui` が実 `config/` を汚したため。正本 `data_schema.md` **§5.12 新設** + §5.4 / `features.md` §4.6 / `codebase_map.md` へ昇格済。**孤児棚卸しの走査範囲・判定は不変**（§9 の補記は「不要」で決着）。**後続**: [idea_26](../../instructions/backlog/idea_26_dialog_keyboard_focus.md)（ダイアログのフォーカス欠落・横断）。refactor_check: **不要**（M1〜M6 非該当。600 行超のファイルは増分が +10〜15 と小さく、80 行超の関数・申し送りコメント・コピー由来の同型ブロックはいずれも無し。根拠は本アーカイブ「refactor_check」節）|
| 28_dialog_keyboard_focus | [28_dialog_keyboard_focus.md](decisions_archive/28_dialog_keyboard_focus.md) | ダイアログの初期キーボードフォーカス（2026-09-23 完了・**presentation 限定・スキーマ不変**・暫定仕様先行モード・起票元 = idea_26 + idea_18）。Escape を bind しているのにフォーカスを移さないダイアログ（群 B 3 件）を是正するため、**フォーカスを `grab_modal(window, parent=None, *, focus=None)` の責務へ集約**（**明示引数**・省略時は窓自身。推測型 `focus_lastfor()` / `after_idle` は未マップ時の `focus_set` 保留で**明示指定を奪うと実測で反証**）/ `focus_force`・`lift` は呼ばない。**群 C 5 経路へ Escape を結線**（× と同じ閉じ方）+ 統合レビュー H1 を受け **群 A 4 経路へも Escape**（**Esc の別用途〔記録中・取得中〕を優先する単一ハンドラ + 状態分岐**。Tk では同一 widget の `<Escape>` が `<KeyPress>` より優先して単独発火すると実測）。**idea_18 の根は配送の遅さではなく配送先の違い**（ダイアログを持つ Tk アプリが入力フォーカスを持たないと Escape は破棄される）→ `send_escape`（フォーカス確保してから送る・期限方式）。§8-7 は Escape family に限定し `after(0)` family は **idea_33** へ分離。実機目視で**最小化復帰後にフォーカスが戻らない**ことが再現 → **idea_34**（正本へ「フォーカスの戻り先は規定しない」を明記）。正本 = `features.md` §4.6 へ 3 条項 + `codebase_map.md` の `modal.py` 節（13→15 箇所訂正）。**task_05e で記録中・取得中の Esc 押しっぱなしで閉じない**よう修正（v0.7・判定順 = 記録/取得中 → 印 → 閉じる）。暫定 22 は v0.7 で凍結。refactor_check: **推奨 → task_07 で実施済**（提案書 11・M3 = Esc の別用途つき閉じ処理の 3 重複を `bind_escape_close` へ） |
| 29_focus_restore_after_minimize | [29_focus_restore_after_minimize.md](decisions_archive/29_focus_restore_after_minimize.md) | 最小化から復元した後のキーボードフォーカス（2026-09-23 完了・**presentation 限定・スキーマ不変**・暫定仕様先行モード・起票元 = idea_34）。復元時に grab だけ戻りフォーカスがメイン窓に残る問題を、**`<Map>` 後に `after_idle` で予約した処理で、予約実行時の grab 保持者の `focus_lastfor() or window` へ `focus_set`** して解消（**即時 `focus_set` は実 App の 3 段ネストで外側の窓を非表示のまま残す**と実測・v0.4）。**実機目視でタスクバー復元時に Escape が届かない不合格** → 復元のアクティブ化の時点で grab が預かり中のため Tk の振り向けが働かず `focus_get()` が `None` と特定 → **Tk がフォーカスを持たず OS の前面が自アプリのメイン窓のときだけ `focus_force`**（専用 `WinDLL` の `GetForegroundWindow`・`restype=HWND`・presentation 唯一の ctypes・v0.5）。最小化中に開いた窓はその回の復元では戻さない / 閉じた後は規定しない / TOCTOU と最小化中に開いた窓の保留要求は保証範囲外。教訓 = **API 復元の probe は実操作の前面化順を再現しない**。暫定 23 は v0.5 で凍結。refactor_check: **不要** |

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

---

## 2026-09-08 (計画08: 候補側ディレクトリ定数の単一定義化・挙動不変)

規範: [`instructions/modified_proposal/08_refactor_orphan_child_file_sweep.md`](../../instructions/modified_proposal/08_refactor_orphan_child_file_sweep.md)
（phase 11 の `/refactor_check` = 推奨 → 起票）。**フェーズ番号は消費していない**。

### 【起票時】実施形態 → **(b) 次フェーズ前の独立ミニ計画 = 「計画08」**（ユーザー確定 2026-09-08）

phase 11 は正本反映まで完了して閉じているため、**追加タスクで完了宣言を巻き戻すより独立計画が清い**。

### 【項目 0】安全網の確認 = **十分・特性テスト不要**（2026-09-08・メイン実測）

既存の 2 件が**定数の値そのものに依存**しており、定義がズレれば落ちる:
`tests/test_orphan_scan.py::test_candidates_are_only_direct_json_files_in_four_directories`（走査側）/
`tests/test_quarantine_manage.py::test_outside_reserved_and_candidate_directory_itself_are_rejected`
（復元先ガード + `global/` 予約 + ディレクトリ自身の拒否）。

### 【項目 1】完了（2026-09-08）= **計画08 完了**

`config_service/candidate_dirs.py`（**新規・8 行の葉モジュール**）へ `CANDIDATE_DIRS` /
`RESERVED_DIR` を置き、`orphan_scan.py` と `quarantine_manage.py` がそこを参照する形にした。
**`quarantine_manage` から `orphan_scan` を import しない**（`quarantine.py` → `orphan_scan` が
あるため逆向きは循環）。実装は `codex-implementer` へ委任。

- **メインが 1 点是正**: Codex の初版は `_CANDIDATE_SPECS` で **`CANDIDATE_DIRS[0]`〜`[3]` の添字参照**を
  使っていた。**タプルの添字参照は計画06 で禁止した形**（`HOOK_KEY_FIELDS[0]`。並び替えで対応が
  無言でずれる）なので、`_CANDIDATE_SHAPES` と `zip(..., strict=True)` の組み合わせへ差し替えた。
  **`strict=True` で長さ不一致も即座に落ちる**。
- **追加テスト 1 件**: `test_candidate_dirs_use_shared_module_without_legacy_alias`
  （両モジュールが同一オブジェクトを見ていること・値の一致・旧名 `_CANDIDATE_DIRS` / `_RESERVED_DIR` の
  不存在を固定）。
- 実測: compile clean / `tests` **414**（413 → +1・skip 7）/ `tests_ui` **288** / smoke pass。
  `grep "user/keymaps" keyseq/` と `grep "user/hotkey_presets/global" keyseq/` は
  **`candidate_dirs.py` の 1 箇所のみ**。
- `reviewer` = **完了可・指摘なし**（添字参照 → `zip(strict=True)` の差し替えも妥当と判定）。
- **対象外のまま**: `RESTORE_ABORTED_INVALID_ID` と `DELETE_REJECTED_INVALID_ID` の同値
  （理由コードの名前空間を分ける意図的な設計）/ ダイアログ・IO・text の同型スケルトン（**候補送り**）。

### 【次】計画09 = `/spec_split`（`data_schema.md` の分割）（ユーザー方針 2026-09-08）

`data_schema.md` が **907 行**で `/spec_split` の判定基準（300 行超 / 単一節 100 行超）に該当。
**計画08 とは分ける**（検証方法が別物 = コードはテスト件数不変 / 分割は**子ファイルのバイト一致**。
承認単位も分かれる）。順序は **計画08 → 計画09**。**分割計画の提示とユーザー承認が先**。

## 2026-09-08 (計画09: `data_schema.md` の INDEX 分割・仕様内容は不変)

`/spec_split`（`.claude/commands/spec_split.md`）に従い、**907 行**へ育った正本
`instructions/common/spec_detail/data_schema.md` を INDEX 分割した（**構造変更であって仕様変更ではない**）。
**ユーザー承認済み（2026-09-08）**。分割前コミット = `126f086`。

- **分類 = 「特定節に集中」**。肥大は **§5.8（398 行）と §5.10（277 行）**で、この 2 節のみ INDEX 化。
  **§5.9（80 行）と §5.1〜§5.7 は親に残した**。親は **260 行**。
- 子は `spec_detail/data_schema/` 配下へ **13 ファイル**（`5_08_01_*` 〜 `5_08_09_*` / `5_10_01_*` 〜 `5_10_04_*`）。
  命名は**ゼロ埋め節番号 + 内容 slug**（文字列ソートで節順に並ぶ形）。
- **節番号・見出しテキストは変更していない**（見出し **36 件が分割前後で完全一致**）。
  既存文書の「`data_schema.md` §N.M」形式の参照は**書き換えず INDEX 経由で解決**する。
- 検証: 子 13 件を `git show 126f086:<親> | sed -n 'a,bp'` から生成し、**11 件はバイト一致**。
  親に残した範囲も分割前とバイト一致（差は INDEX 行と、INDEX ブロック後の空行 1 行のみ）。
- **verbatim からの唯一の逸脱 = 相対リンクの深さ 2 箇所**（`5_08_09_orphan_sweep.md` の idea_13 /
  `5_10_04_constraints.md` の idea_11）。子が 1 階層深くなったため `../../backlog/` を
  **`../../../backlog/`** へ直した。**リンク先は同一**で、内容の変更はこの 2 行以外にない。
- 文末の `---` は親に残した（§5.10.4 の子には含めない）。
- **以後の運用**: 仕様更新は**子ファイルを編集**する。節の趣旨が変わったら**親 INDEX の 1 行要約も追従**。
  新しい節は子を新規作成 + 親へ 1 行追加。子が 300 行を超えたら再分割を検討する。

## 2026-09-08 (計画10: 公開面の境界検査を経路ごとに分割・挙動不変)

規範: [`instructions/modified_proposal/09_refactor_contracts_boundary_ast_coverage.md`](../../instructions/modified_proposal/09_refactor_contracts_boundary_ast_coverage.md)
（phase 13 の `/refactor_check` = 推奨 → 起票）。**フェーズ番号は消費していない**。
対象は `tests/test_config_service_contracts.py` の 1 ファイルのみ（**プロダクション不変**）。

### 【起票時】実施形態 → **(b) 次フェーズ前の独立ミニ計画 = 「計画10」**（ユーザー確定 2026-09-08）

phase 13 は記録とフェーズ完了処理まで終えて閉じているため、**追加タスクで完了宣言を巻き戻すより
独立計画が清い**（計画08 と同じ判断）。

### 【項目 0】期待メッセージの固定 = **先行して単独コミット**（`d9be5d8`）

自己検証は**非空チェックしか行っておらず**、経路ラベル・メッセージ文字列・
**同一行に複数経路が当たる場合の畳み込みの先勝ち**が入れ替わっても検出できなかった。
**分割の前に単独で入れる**ことで「分割前後で同一」を主張できるようにした。

- **期待値はメインが `.venv` で実測した実際の出力をそのまま写した**
  （Codex は python を実行できないため、値を委任プロンプトに含めて渡した）。
- **守るべき挙動として固定された 2 点**:
  ①`from keyseq.application import config_service` + `config_service.orphan_scan` は
  **`attribute config_service.orphan_scan`**（**素の名前検査が先勝ち**。エイリアス経路が先になると
  完全修飾名に変わる）②`package` 省略時の相対 import は **`R4 config_service.orphan_scan`**（縮退形）。
- **安全網が実効的であることを実測**: メッセージ書式を意図的に変えると該当テストが FAIL し、
  復旧で pass に戻る。

### 【項目 1・2】完了（2026-09-08）= **計画10 完了**（`5eb986b`）

- `collect_forbidden_refs`（**100 行**）を `_build_alias_map`（20 行）/ `_check_import_node`（38 行）/
  `_check_attribute`（30 行）へ分割し、本体は結果を連結する **26 行**へ。
  **畳み込み（同一 行番号 × 内部モジュール名）の責務は本体側に残した**。
- R4-fallback の `"config_service"` 直値 3 箇所を **`_INTERNAL_SEGMENT`** へ寄せた。
  **素の名前検査の `node.value.id == "config_service"` は対象外のまま**（識別子名であって
  パッケージ末尾セグメントではない）。
- **挙動保存を 2 段で確認**: ①項目 0 の期待メッセージ 13 件が 1 文字も変わらない
  ②**分割前（`d9be5d8`）と分割後の出力を 95 ケースで機械照合し不一致 0**
  （presentation 実ファイル 60 + 合成 35。合成には自己検証 26 例 + `from . import X` / 深さ違い /
  素の名前 / 代入再束縛 / `import a as x, a as y` / ワイルドカード import を含む）。
- 実測: compile clean / `tests` **417**（skip 7・**件数不変**）/ `tests_ui` **288** / smoke pass。
  `git diff -- keyseq main.py tests_ui` は空。
- `reviewer` = **完了可（ブロッキングなし）**。参考指摘 3 件のうち 2 件を反映
  （`_check_import_nodes` → **単数形へ改名** / `prefix` の毎ノード再計算を
  **モジュール定数 `_PACKAGE_PREFIX`** へ）。残る 1 件（分割後の関数が 30 行目安をわずかに超える）は
  **提案書が想定した分割形**のため据え置き。

---

## 2026-09-23 (phase 30: アクション要素と内部キーの型正規化・直接改訂モード)

### 【起票時】idea_27 + idea_28 を統合 = **採用**（ユーザー確定 2026-09-23）

- 両者とも §5.1「型不正の共通規則」への追従漏れで同系統・改訂先も同じ `data_schema.md`。
- **idea_27 は案 A**（§5.11.2 の「非文字列は未定義」を削除し §5.1 に従う = 非文字列は空扱い → 既定 `left`）。
  **案 B（実装だけ防御・仕様は未定義のまま）は除外**。
- **`type` の非文字列も含める**（起票時の grep で 5 箇所の `.strip()` を発見。一覧表示 `domain/config.py:323` も含む）。
- **適用点は読込時の正規化**（`normalize_actions`）。読み手は無修正。**無いキーは補わない**。
- idea_28 は**入口（`ensure_config_compatibility`）で `coerce_label`**。読み手は約 25 箇所あるため個別には直さない。
  **入口外の混入経路**（例: `config_service/__init__.py:299` の `str(...)`）は task_02 で棚卸しし、
  1 箇所に収まらなければ暫定仕様先行モードへ切り替える。

### 【起票時】空 / 未知の `type` の実行時挙動 = **案 A（現行挙動の明文化）を採用**（ユーザー確定 2026-09-23）

- 正本 §5.11 に未規定だった「空 / 未知の `type` は `value` を文字列入力」（`action_executor.py:64`）を
  task_01 で明文化する。**コードは変えない**。`type` の非文字列を空扱いにするとこの経路へ入るため。
- **案 B（何も送らずエラー通知）は保留 → [idea_35](../../instructions/backlog/idea_35_unknown_action_type_handling.md)**。
  executor / 一覧表示 / ダイアログ（空 `type` を hotkey とみなす `action_dialog.py:115` との食い違い）/
  通知経路に跨がり挙動も変わるため、直接改訂モードに収まらない。着手時は暫定仕様先行モード。
