# phase.md

## フェーズ名

JSON 読込の型不正の扱い統一（json_type_normalization）

## フェーズの目的

JSON 読込時に**要素の型が不正だった場合の扱い**を全経路で統一する。現在は文字列前提の処理へ
非文字列がそのまま渡り、**6 箇所で `AttributeError` になって読込自体が落ちる**ほか、
`str()` 強制により **Python の repr 文字列が runtime に載る**。
**型検査を domain の入口関数（`coerce_key_name` / `coerce_label`）へ一本化**し、
「非文字列は空扱い / 同一性フィールドで代替不能なら除去」へ揃える。

**domain / application 限定・JSON スキーマ不変**（読込の頑健化のみでファイル形式は変えない）。

- 起票元: phase 23 完了後のユーザー指示（2026-09-19）= 「keymap / trigger_set の個別読込経路を
  実際に見直して必要なら直す」。見直しで検出した欠陥への対応。
- 主入力（暫定仕様）: [20_individual_json_type_normalization.md](../../history/20_individual_json_type_normalization.md)
  （v0.3・ユーザー確定済）
- モード: **暫定仕様先行モード**。番号対応: phase 24 / 暫定 20 / decisions 24。

## 確定（ユーザー 2026-09-19）

- **「除去に寄せる」方針**（`hotkey_presets` / `actions` の要素判定と同じ流儀へ統一）。
- **スコープ = 案 F（全経路へ一斉適用）**。個別読込・split 読込・単一 JSON のすべてを対象にする
  （共有ローダーのため経路別に切ると破綻する）。
- 個別条項: trigger の `key` 不正 = **空扱いで残す** / `sequence_path` 不正 = **空扱い** /
  `mappings` の target 不正 = **対ごと除去**。
- `suppress` / `run_to_end` / `run_to_end_delay_ms` は **R3 = 現状の実装どおり**（変更しない）。
- 挙動変更（repr 文字列だった値が消える）を許容する。

## スコープ

### 含む

- `keyseq/domain/config.py`: `coerce_key_name` / `coerce_label` の新設と、
  `ensure_config_compatibility`（`triggers[].key` / `triggers[].label` / `keymaps[].id` /
  `keymaps[].label`）・`normalize_actions`（要素の `label`）・`mappings` の target 除去への適用。
- `keyseq/application/config_service/__init__.py`: `_generate_keymap_id` / `load_keymap_file`。
- `keyseq/application/config_service/split_loading.py`: `load_triggers_from_trigger_set` と
  `_normalize_sequence_payload` 経由の `label`（参照先 sequence からの再流入対策）。
- 対応する単体テスト。
- 正本への反映（§5.1 直下の共通規則 / §5.6 の keymap 節新設 + trigger_set の型規定 /
  §5.2・§5.11 への追記 / 形状検証との相互参照）。

### 含まない（後送り）

- `actions[]` の**要素**の型規定（phase 23 で確定済・§5.11 が正）。扱うのは要素内の `label` のみ。
- `hotkey_presets` の読込（既に規定どおり）。
- R3 フィールドの既定値への倒し方の見直し。
- `button` 非文字列の `AttributeError`（`action_executor.py:119`。**実行時**の型不正で別レイヤ。
  phase 22 からの別タスク化候補のまま）。
- UI・ダイアログの変更。

## このフェーズで読むファイル

1. [暫定仕様 20](../../history/20_individual_json_type_normalization.md)（主入力・全節）
2. `keyseq/domain/config.py`（`normalize_key_name` / `safe_deepcopy` / `normalize_actions` /
   `ensure_config_compatibility` の trigger・keymap 正規化）
3. `keyseq/application/config_service/__init__.py`（`load_keymap_file` / `_generate_keymap_id` /
   `_normalize_sequence_payload`）
4. `keyseq/application/config_service/split_loading.py`（`load_triggers_from_trigger_set` /
   `load_keymap_entry` 周辺）
5. `tests/test_domain_config.py` / `tests/test_config_service.py`
6. 正本 `instructions/common/spec_detail/data_schema.md` §5.1 / §5.2 / §5.6 / §5.11 と
   `data_schema/5_08_09_orphan_sweep.md` の形状検証

## タスク

- task_01: domain へ `coerce_key_name` / `coerce_label` を新設し全経路へ適用する（+ 単体テスト）— **完了**（2026-09-19・`a1764d1`）
- task_03: 取りこぼした 4 箇所（旧形式 `trigger_key` / hook キー 2 種 / `active_keymap_id`）へ `coerce_key_name` を適用する — **完了**（2026-09-19）
- task_02: 正本反映と記録（暫定仕様 20 の昇格・凍結 / decisions_archive/24 / current.md /
  `/refactor_check`）— **完了**（2026-09-19）

## レビュー方針

- 共通観点は `.claude/rules/review.md`。
- **本フェーズ固有**:
  - **falsy な非文字列（`0` / `false` / `[]` / `{}`）の既存挙動が変わっていないか**
    （既に空へ倒れている。変えるのは truthy な非文字列のみ）。
  - `normalize_key_name` のシグネチャと既存 158 箇所の呼び出しの意味を変えていないか。
  - 正常な JSON の読込結果が 1 バイトも変わらないこと（後方互換・正本 §5.1）。
  - 保存 payload の形が変わっていないか（読込時正規化のみ）。
  - 依存方向（application → domain のみ）。
