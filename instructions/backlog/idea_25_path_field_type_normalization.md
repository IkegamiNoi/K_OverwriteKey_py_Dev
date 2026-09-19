# idea_25_path_field_type_normalization.md

## 概要

**keymap_set / 外部レイアウト登録の「パス系フィールド」にも `str()` 強制が残っている**。
非文字列（dict / list / 数値）を渡すと **Python の repr 文字列がパスとして扱われる**。
phase 24 で keymap / trigger_set / sequence の**内容フィールド**は
`coerce_key_name` / `coerce_label` へ統一したが、**パス系は対象表に無かったため意図的に残した**。
例外にはならない（読込が落ちない）ため**優先度低**。

## 起票経緯（2026-09-19）

出所 = [phase 24](../phase/24_json_type_normalization/phase.md) task_01 の実装中に、
メインセッションが `str(x or "").strip()` パターンを全走査して発見。
暫定仕様 20 の対象フィールド（keymap の `id` / `label` / `mappings`、trigger_set の
`key` / `label` / `sequence_path`、actions の `label`）に**含まれない**ため、
スコープ外として残しユーザー判断で本 idea へ分離した。

## 現状

`keyseq/application/config_service/split_loading.py` の以下が `str(x or "").strip()` のまま:

| 行 | フィールド | 出所 |
|---|---|---|
| `:396` | `entry.get("path")` | keymap_set の `keymaps[].path` |
| `:397` | `entry.get("switch_key")` | keymap_set の `keymaps[].switch_key` |
| `:399` | `entry`（非 dict 形式の旧記法） | 同上 |
| `:312` | `keymap_set.get("trigger_set_path")` | keymap_set |
| `:337` | `keymap_set.get("active_keymap_path")` | keymap_set |
| `:441` | `path_value`（trigger_set のパス） | keymap_set |
| `:522` / `:524` | `item.get("path")` | `external_keyboard_layouts` |

- **例外にはならない**。`str()` を通るため `{"a":1}` は `"{'a': 1}"` という**存在しないパス**になり、
  読込は「ファイルなし」として静かにスキップされる（`_load_optional_json` が None を返す）。
- `switch_key` は**キー名**であり、repr 文字列がそのままキー名として runtime に載り得る
  （`domain/config.py:295-310` の `keymap_switch_keys` も `str()` 強制のため例外化しない）。
- `external_keyboard_layouts` は `ensure_config_compatibility`（`domain/config.py:239-244`）でも
  `str(item.get("path") or "").strip()` を通る。

## 提案（方向性・要設計）

- 案 A: **パス系にも `coerce_label` 相当（非文字列は空扱い）を適用する**。空になれば
  「未指定」として既存の分岐（`if not stored_path: continue` 等）に自然に落ちる。
  phase 24 の流儀（「非文字列は空扱い」）と一貫する。
- 案 B: 現状維持とし、**正本へ「パス系の非文字列は未定義」と明記**するに留める。
  実害（存在しないパスとして無視される）が小さいため。

いずれにせよ**正本 `data_schema.md` §5.5（split 読込）/ §5.7（パス表記）に
パス系フィールドの型規定が無い**ため、着手時は `.claude/rules/spec_change_workflow.md` の
検出基準 B（仕様の不備）として扱う。

## 想定スコープ

- 含む: `split_loading.py` のパス系 7 箇所 + `domain/config.py` の
  `external_keyboard_layouts` / `keymap_switch_keys`、対応する単体テスト、正本の型規定追記。
- 含まない: keymap / trigger_set / sequence の**内容フィールド**（phase 24 で対応済）/
  保存側の payload 構築 / パスの実在確認。
- 影響レイヤ: application / domain。仕様変更（型規定の新設）は**あり**の見込み。優先度低。
