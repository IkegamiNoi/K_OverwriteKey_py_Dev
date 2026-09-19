# task_02_spec_promotion_and_close

## 目的

phase 24 の**正本反映と記録**（フェーズ最終タスク）。task_01 で実装が確定した内容を、
暫定仕様 20（v0.3）から正本 `instructions/common/spec_detail/` へ**昇格**し、暫定仕様を**凍結**する。

レイヤ制約: **文書作業のみ**。コード変更なし（`.claude/rules/agent_selection.md`
「メインセッションが直接行ってよい作業」= フェーズ末の正本反映タスク）。

## 対象範囲（文書のみ）

### instructions/common/spec_detail/data_schema.md

1. **§5.1 直下に「型不正の共通規則」を 1 段落新設**（暫定仕様 §3 / §10・`deep-reviewer` F-2）。
   - 規定は 2 文で足りる: **「読込時、文字列を期待するフィールドに非文字列が入っていたら空として扱う。
     空になると成立しない要素（`mappings` の対・`actions` の要素・`hotkey_presets` の要素）は
     その要素ごと除去する」**。
   - **R1 / R2 / R3 というラベルは正本へ持ち込まない**（後の節追加で破綻するため）。
   - falsy な非文字列が元から空扱いである点、エラーダイアログを出さない点、
     捨てた値は次の保存でファイルから消える点を添える。
   - 各表からは**この段落を参照**する形にする（型の扱いを節ごとに書き下さない）。
2. **§5.6 に keymap 個別 JSON の節を新設**（暫定仕様 §4 の表）。
   - `id`（空→ファイル名 stem→`"keymap"`）/ `label`（空文字）/ `mappings`（dict 以外は `{}`・
     target が非文字列なら対ごと除去）。
   - `mappings` のキー（source）は JSON 由来で常に str である旨を注記。
   - **§5.7 との位置づけ**（§5.7 は既に keymap 個別ファイルの存在を前提にしている）を 1 行で明記。
   - **`data_schema/5_08_09_orphan_sweep.md:43-44` の形状検証と相互参照**する
     （「`mappings` は dict」等は既にそちらが規定済み。**二重定義にしない**）。
3. **§5.6 trigger_set に型の規定を追記**（暫定仕様 §5 の表）。
   - `key` / `label` / `sequence_path` は非文字列なら空扱い。
   - `suppress` / `run_to_end` は `bool()` 強制で **`null` / `0` / `""` / `[]` は false** になる
     （「既定 true へ倒す」ではない。実装どおり）。
   - `run_to_end_delay_ms` は変換不能なら 300（`"500"` は 500 へ変換される）。
   - 参照先 sequence の `label` も同じ規則で正規化される旨（`trigger.update` で参照元へ伝播するため）。
4. **§5.2（単一 JSON）に追記**: `triggers[].key` / `triggers[].label` / `keymaps[].id` /
   `keymaps[].label` にも §5.1 の共通規則が適用される旨。
5. **§5.11 に `label` の型を追記**: 非文字列なら空扱い（現在は「一覧表示用の任意の文字列」のみ）。

### instructions/common/codebase_map.md

6. phase 23 で追記した「`actions[]` の読込時正規化」の項を更新し、
   **`coerce_key_name` / `coerce_label` による型正規化の一本化**を追記する
   （呼び出し元の系統・`normalize_key_name` のシグネチャを変えていない理由を 1 行）。

### instructions/history/20_individual_json_type_normalization.md

7. **凍結**する。ヘッダの状態行を
   「**凍結（2026-09-19・正本反映済）**。正本が最新。本書は経緯記録として凍結」へ書き換える。
   本文は編集しない。

### .claude_data/state/decisions_archive/24_json_type_normalization.md（新規）

8. phase 24 の判断履歴を集約する（`decisions_archive/23_...md` の書式に倣う）。
   記載する判断: ①「除去に寄せる」方針の採用 ②暫定仕様先行モードを選んだ理由
   ③**案 F（全経路へ一斉適用）の採用と案 G の不採用理由**（共有ローダーで経路別スコープが破綻する）
   ④個別条項 3 件 ⑤`normalize_key_name` のシグネチャを変えなかった理由（呼び出し 158 箇所）
   ⑥2 本のレビュー指摘とその裏取り結果 ⑦reviewer 差し戻し 1 件（split 読込の keymap label 漏れ）
   ⑧tests_ui の 1 件 fail が既知フレークだったこと。

### .claude_data/state/decisions.md

9. 「アーカイブ索引」へ 1 行追加する。

### instructions/phase/current.md

10. 「現在の参照先」の phase 24 項を**完了記載**へ更新し、「直近の一連の作業が扱っている領域」を
    phase 24 の内容へ差し替える（完了フェーズはリンクのみ・要約は書かない）。
    次採番（phase 25 / 暫定 21 / decisions 25）は task_01 で更新済のため**再変更しない**。

### instructions/phase/24_json_type_normalization/phase.md

11. 「タスク」一覧へ完了状態を反映する（task_01 / task_02）。

## 読むファイル

- `instructions/history/20_individual_json_type_normalization.md`（昇格元・§3 / §4 / §5 / §10）
- `instructions/common/spec_detail/data_schema.md` の §5.1（冒頭）/ §5.2 / §5.6 / §5.7 / §5.11
- `instructions/common/spec_detail/data_schema/5_08_09_orphan_sweep.md:40-46`（形状検証・相互参照先）
- `instructions/common/codebase_map.md` の「`actions[]` の読込時正規化」の項（phase 23 で追記した箇所）
- `.claude_data/state/decisions_archive/23_sequence_payload_action_normalization.md`（書式の手本・冒頭のみ）
- `.claude_data/state/decisions.md`「アーカイブ索引」節
- `instructions/phase/current.md`「現在の参照先」「フェーズ完了時の指示」

## 含まない

- コードの変更（task_01 で完了。本タスクでコードに触らない）
- **パス系フィールドの型規定**（`switch_key` / `path` 等）。[idea_25](../../../backlog/idea_25_path_field_type_normalization.md)
  として分離済で**未着手のまま**。正本にも書かない
- `button` 非文字列の `AttributeError`（`action_executor.py:119`・phase 22 からの別タスク化候補）
- backlog INDEX → INDEX_done の移動（**起票元が idea ではない**ため対象外。
  idea_25 は本フェーズで起票した別ネタなので INDEX.md に未着手のまま残す）
- main へのマージ（ユーザーが行う）

## 確認

1. `data_schema.md` に §5.1 の共通規則段落が入り、§5.6 の keymap 節 / trigger_set の型規定 /
   §5.2 / §5.11 の追記が揃っていること。**R1 / R2 / R3 のラベルが正本に入っていないこと**。
2. `5_08_09_orphan_sweep.md` の形状検証と**二重定義になっていない**こと（相互参照になっていること）。
3. 正本の記述が task_01 の実装（`coerce_key_name` / `coerce_label` の挙動）と一致すること。
   特に **`suppress` は「falsy なら false」**であり「既定 true へ倒す」ではないこと。
4. 暫定仕様 20 のヘッダが凍結状態になっていること（本文は無編集）。
5. `decisions.md` の索引リンクが実在ファイルを指すこと。
6. `/refactor_check` を実行し、判定結果（要否・根拠 M1〜M6）を完了報告に含めること。
7. 静的確認: `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui`

## 完了条件

- 上記確認 1〜7 が pass・**reviewer 採用**（観点: 正本の記述と実装の整合・記録の漏れ・
  既存節との矛盾）。
- 実機目視: **不要**（UI 変更なし）。
- 本タスク完了をもって phase 24 を完了とする。
