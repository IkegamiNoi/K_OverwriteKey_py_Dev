# decisions_archive / 04_config_io_controller_split

フェーズ **04_config_io_controller_split**（`ConfigIoController` の責務分割）の判断履歴。
索引は `.claude_data/state/decisions.md`「アーカイブ索引」。
フェーズ定義: `instructions/phase/04_config_io_controller_split/phase.md`。
**設計の正（凍結）**: 暫定仕様 `instructions/history/03_config_io_controller_split.md`（v0.4・凍結）。

- 期間: 2026-07-23（起票・確定）〜 2026-07-26（完了）
- モード: **暫定仕様先行モード**（番号対応: phase 04 / 暫定 03 / decisions 04。暫定仕様は独立採番）
- 目的: `keyseq/presentation/controllers/config_io_controller.py`（598 行・1 クラス・29 メソッド）を
  責務ごとに **6 モジュールへ分割**し、保守性と修正時の説明可能性を回復。**対象は presentation のみ**。
- 結果: **完了**（task_01〜06）。標準検証全緑・実機目視 OK・reviewer/codex-reviewer 指摘なし。**挙動不変**。
  `config_io_controller.py` を削除し、App が 6 クラスを直接公開（`config_io` 名は完全消滅・互換レイヤーなし）。
- 起票元: ユーザー要望（2026-07-23）。`current.md`「別タスク化候補」に記録されていた「598 行で 600 行目安に接近」の着手。

---

## 設計判断（暫定仕様 §2・ユーザー確定 2026-07-23・v0.4）

1. **挙動不変が絶対前提** → **採用**。ダイアログ文言・表示順・flash メッセージ・保存 JSON のバイト列・
   例外時の分岐を一切変えない。挙動変更が必要なら本フェーズ外（仕様変更フローへ）。
2. **安全網（特性テスト）を最初のタスクに置く** → **採用**（task_01/02）。分割はその後。
3. **§4 = 案 B（呼び出し元 30 箇所を本フェーズで差し替え）** → **採用**。恒久ファサードは互換レイヤー禁止に抵触し、
   一時ラッパー案（案 C）は削除を強制するゲートを持てないため。App が分割後クラスを個別に公開し `app.<名>.<method>` 参照。
4. **§5 = 案 1（分割のみ・共通化しない）** → **採用**。D/E/F の差異が 9 点あり、共通化は挙動差混入経路そのもの。
   共通化は [idea_06](../../instructions/backlog/idea_06_individual_json_io_unification.md) として分離・**保留**。
5. **§1「既存の不整合」（E の source_path 分断・到達不能な askyesno デッドコード）はそのまま移設** → **採用**。
   修正は挙動変更を伴うため [idea_05](../../instructions/backlog/idea_05_trigger_set_source_path_inconsistency.md)（phase 04 完了後）へ。
6. **`self._app.` reach-through（169 箇所）は本フェーズで扱わない** → **採用**（§9 スコープ外）。

## 敵対的レビューの指摘処理（暫定仕様 §6・codex-adversarial-reviewer 2026-07-23・v0.3 反映）

- **§4 推奨を案 C → 案 B へ**（[high]）→ **採用**。案 C は削除完了を強制するゲートがなく放置前例あり
  （`action_list` alias が計画04 から据え置き）。30 箇所は静的参照で機械的置換が可能と実測。
- **§7 に経路別の特性テスト表を追加**（[high]）→ **採用**。「挙動不変」保証のため メソッド×分岐 粒度へ引き上げ。
- **§5 の差異を 7 → 9 点へ**（[high]）→ **採用・実コードで裏取り**。E のラベル連動なし / E の source_path 分断を追加。
- **§1 の着手根拠から M3 援用を撤回**（[medium]）→ **採用**。M3 は「本フェーズで追加したコード」の指標で既存重複に不適用。
  着手根拠は「ユーザーが独立した設計タスクとして指示したこと」に一本化。

## 分割の骨格（暫定仕様 §3・クラスタ → 落とし先）

| ID | クラスタ | 落とし先ファイル | クラス | App 公開名 |
|---|---|---|---|---|
| A + A' | 構成セット（keymap_set）+ 専用ヘルパ | `config_io/keymap_set_io.py` | KeymapSetIo | `app.keymap_set_io` |
| B | 起動設定（startup.json） | `config_io/startup_io.py` | StartupIo | `app.startup_io` |
| C | 共有ダイアログヘルパ | `config_io/io_dialogs.py` | IoDialogs | `app.io_dialogs` |
| D | keymap 個別 JSON | `config_io/keymap_file_io.py` | KeymapFileIo | `app.keymap_io` |
| E | trigger_set 個別 JSON | `config_io/trigger_set_file_io.py` | TriggerSetFileIo | `app.trigger_set_io` |
| F | sequence 個別 JSON | `config_io/sequence_file_io.py` | SequenceFileIo | `app.sequence_io` |

- 配置は `file_organization_rules.md`「親フォルダ方式」に従い `controllers/config_io/` を新設して親ごと入れた。
- 各ファイルは 300 行以内の目安に収まる（最大 A+A' の ~223 行）。

## 特性テストの調整（task_03/04/05・分割に伴う mock 境界の付け替え）

分割で「本体無変更のまま特性テストを pass」は原理的に不可能と判明（別オブジェクトへ分かれたヘルパとメソッドを
1 アクセサで両方 patch できない）。**production は挙動不変**（内部呼び出しが新オブジェクトに束縛されただけ）。
task ごとに最適手段を選び、**assert する挙動は一切緩めない**方針で対応した:

- **task_03（D/E/F）**: 内部メソッド mock → **境界 mock（Option A）** へ書き換え → **修正して採用**（ユーザー確定 2026-07-24）。
  `config_service.save_X_file` / `messagebox` / refresh を mock。assert する挙動（保存パス・文言・E のラベル連動なし）は保持。
  codex-reviewer P2「特性テストの不変性が崩れている」は Option A の再指摘でユーザー再確認の上受諾。
  Codex 代替案（wrapper 経由で元テスト無変更）は循環委譲・task_05 破綻・非 verbatim のため却下。
- **task_04（A/B/C）**: **アクセサ切替** を採用 → **採用**（ユーザー確定 2026-07-24）。同一クラスタ内 mock はそのまま intercept され
  **アサーション非緩和で 35 件 pass**。クロスモジュール 2 箇所（write_startup / apply）のみ facade patch。
  task_03 で Option B を見送った理由（C と D が別クラスタで 1 アクセサ不可）は A/B には非該当（同一クラスタ完結）。
- **task_05（差し替え + ファサード削除）**: テスト 3 ファイルのアクセサを owner オブジェクトへ最終調整 → **採用**。
  `_dialog_io`→io_dialogs / `_keymap_io`→keymap_io / `_trigger_set_io`→trigger_set_io / `_sequence_io`→sequence_io /
  `_config_set_io`→keymap_set_io / `_startup_io`→startup_io。cross-cluster patch も owner へ
  （confirm→keymap_set_io / write_startup→startup_io / apply→keymap_set_io）。**アサーション非緩和**。

## 呼び出し元の差し替え（task_05・案 B）

- `config_io_controller.py` を削除し、App が 6 分割オブジェクトを直接公開（app.py:142-147）。
- 外部 30 箇所（menu_bar 8 / file_frame 4 / keymap・sequence・trigger_box 各 3 / layout 1 / app.py 7）+
  内部クロスモジュール 9 箇所（`self._app.config_io.X` → `self._app.<owner>.X`）を「メソッド → 所有オブジェクト」対応表どおり
  機械的に差し替え。**`config_io` 名は完全消滅**（互換エイリアスなし）。

## 実装上の注意点（レビュー重点観点）

- **「既存の不整合」を直さない**（暫定仕様 §1）: E の source_path 分断（読み `app._trigger_set_source_path`〔未定義・常に ""〕/
  書き `dirty_tracker.trigger_set_source_path`〔write-only〕）と `:440` の到達不能な askyesno を**そのまま維持**。
  善意の修正が最も混入しやすい箇所。
- **共通化の先取りをしない**（§5 = 案 1）: D/E/F に共通基底・共有ヘルパを新設しない。
- **スコープ外へ波及しない**: `self._app.` 書き換え・`config_service` 変更・ダイアログ文言変更（誤字含む）を入れない。
- 新規（未追跡）ファイルの確認 grep は `git grep` でなく**直接 grep**。app.py 等の行数計測は `wc -l`。
- Codex 運用: codex-implementer は task_03・04・05 とも実装・review 正常完了（**ハングなし**・Monitor が JOB_ENDED を正検知）。
  Codex 申告のテスト結果は信用せず必ず verifier で `.venv` 再実行する運用を維持。

## 正本反映（昇格）要否（task_06・調査 2026-07-26）

- **昇格不要** → **採用**。`instructions/common/spec_detail/` に `ConfigIo` / `config_io` の言及は **0 件**（再 grep 確認）。
  担当層/クラス割り当ては `architecture.md §3.5` が「codebase_map.md を正とする」と明言。挙動不変ゆえ仕様変更なし。
- 追従更新は **`codebase_map.md`** のみ実施（ツリー図に `config_io/` 6 ファイル / コントローラ節を 6 クラス構成へ /
  `_apply_font_delta` の永続化参照を `startup_io.write_startup` へ / `app.<名>` 例を `app.keymap_set_io` へ）。
- 暫定仕様 `history/03_config_io_controller_split.md` は **v0.4 で凍結**（ヘッダを「凍結・正本反映済」へ）。

## /refactor_check 判定（task_06・2026-07-26）

- **不要**（提案書なし）→ **採用**。対象: keyseq/ 配下 14 ファイル（+686 / -629・PHASE_BASE=`3797aba`〜HEAD）。
  - M1: 600 行超ファイルなし（最大 app.py **460 行**・増分 +100 行未満。config_io/ は最大 keymap_set_io.py 230 行）。非該当。
  - M2: 80 行超の新規/大幅変更関数なし（最大 `set_startup_keymap_set` ~32 行）。非該当。
  - **M3: keymap/trigger_set/sequence の `*_file_io.py` 3 ファイルが同型（save/save_as/save_to_path/load）だが、
    旧 `config_io_controller.py` の D/E/F ブロックの verbatim 移設で新規コピーではない。§5=案1（分割のみ・共通化しない）は
    ユーザー確定済、共通化は [idea_06](../../instructions/backlog/idea_06_individual_json_io_unification.md) として保留判断済 →
    「既知（idea_06）」扱いで提案書に含めない**（再提案の抑止ルール）。
  - M4: 非該当。M5: 申し送りコメント新規 **0 件**。M6: `filetypes=[("JSON","*.json"),("All","*.*")]` の直値は
    分割前ファイルで既に 12 回出現していた既存重複の移設で、対応する定数モジュールも不在（新規重複ではない）。非該当。
- 提案書は起票しない。M3 の同型 3 ブロックは idea_06 が既にカバー（ユーザー保留・充足条件は phase 04 完了 + idea_05 解消 + 実需）。

## codebase_map / 正本仕様の更新

- `codebase_map.md`: **更新** → **採用**。presentation ツリーに `controllers/config_io/`（6 ファイル）を追記 /
  コントローラ節の `ConfigIoController` 行を 6 クラス（KeymapSetIo/StartupIo/IoDialogs/KeymapFileIo/TriggerSetFileIo/SequenceFileIo）
  + App 公開名へ差し替え / `config_io.write_startup` → `startup_io.write_startup` / `app.config_io` 例 → `app.keymap_set_io`。
- `spec_detail/`: **更新不要**（上記「昇格要否」の裏取りどおり）→ **採用**。

## コミット一覧

| コミット | 内容 |
|---|---|
| `b0f2106` | 暫定仕様 03 起票（ConfigIoController 分割）+ idea_05 / idea_06 |
| `670e20a` | phase 04 起票（ConfigIoController の責務分割） |
| `8e5d1c1` | task_01 を起票・タスクを 6 本へ再構成 |
| `2f07fe8` | task_01: 特性テスト① C + D/E/F を追加（安全網・実装無変更） |
| `c0015b2` | task_02: 特性テスト② A + B を追加 |
| `3ee09a1` | task_03: D/E/F を config_io/ 配下 3 モジュールへ分割 |
| `67f8f19` | task_04: A/B/C を config_io/ 配下 3 モジュールへ分割 |
| `0e68286` | task_05: 呼び出し元を 6 分割オブジェクトへ差し替え・ファサード削除 |
| （本コミット） | task_06: 正本反映・記録（codebase_map / 凍結 / decisions_archive / current.md / refactor_check 判定） |

## 検証・レビュー

- 標準検証（全タスクで全緑・`.venv` python）: compile clean / tests **86** / tests_ui **74**（19 + 35 + 既存 20）/ smoke pass。
  **特性テスト（挙動不変の安全網）＝分割の挙動不変の証明**。
- reviewer（5観点）: task_01〜05 いずれも「**完了可**・採用」。
- codex-reviewer（task_04/05 統合の二次レビュー）: **指摘なし（clean）**。
- 実機目視（task_05・ユーザー 2026-07-26 **OK**）: 保存 / 読込 / 別名保存 / Import / Export / 起動時に読む構成セット指定 /
  keymap・トリガー一覧・出力シーケンスの個別保存・読込。

## 次フェーズへの申し送り

- **[idea_05](../../instructions/backlog/idea_05_trigger_set_source_path_inconsistency.md)**（E の source_path 分断修正）は
  **phase 04 完了が着手条件**。挙動変更を伴うため仕様変更フローで着手する。
- **[idea_06](../../instructions/backlog/idea_06_individual_json_io_unification.md)**（D/E/F 共通化）は**保留**。
  着手条件は「phase 04 完了 + idea_05 の解消 + 共通化の実需」の 3 つすべて。
- **[idea_04](../../instructions/backlog/idea_04_font_settings_controller.md)**（FontSettingsController・保留）: `write_startup` が
  B クラスタ（`startup_io.py`）へ移ったため、着手時の前提が変わる点に留意。
- `self._app.` reach-through（169 箇所）は未着手（本フェーズのスコープ外）。分割後に改めて評価する。
- 次採番は phase **`05`** / 暫定仕様 **`04`**。
