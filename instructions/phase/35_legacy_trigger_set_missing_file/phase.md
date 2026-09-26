# phase.md

## フェーズ名

旧形式トリガー一覧の移行の境界値（legacy_trigger_set_missing_file）

## フェーズの目的

keymap_set の `trigger_set_path`（旧形式の読込元・§5.13.3）の**境界値の扱いを正本で定め、テストで固定する**。

- **存在しないファイル**: 正本 §5.13.3 に定めが無く、現状は移行として扱われる
  （アクティブなキーマップに空の一覧が付いて未保存表示になる / アクティブ側が `""` を持つと
  「旧トリガー一覧（stem）」という空のキーマップが自動作成され通知も出る。
  `split_loading.py:441` `_migrate_legacy_trigger_set` が参照先の有無を見ていない）。
  → **ファイルが無いなら移行しない**（旧参照なしと同じ扱い）に正本を改訂し、実装を合わせる。
- **非文字列**: §5.1「型不正の共通規則」で空扱い＝移行しない、と既に決まっている（`coerce_label`・`split_loading.py:411`）。
  **明示テストが無い**ため追加のみ。

**application 層（`config_service/split_loading.py`）の小修正 + `tests/` のテスト追加・JSON スキーマ不変**。
正本 `data_schema.md` §5.13.3 に 1 項を追記する。

- 起票元: phase 34 task_07d reviewer の参考指摘（`current.md`「別タスク化候補」の「phase 34 統合レビューの保留」項）/ ユーザー要望（2026-09-26）。
- 主入力（暫定仕様）: なし（直接改訂モード）。
- モード: **直接改訂モード**（改訂は §5.13.3 の 1 項のみ・方針はユーザー確定済み）。番号対応: phase 35 / 暫定 なし / decisions 35。

## 確定（ユーザー 2026-09-26）

- keymap_set の `trigger_set_path` が**非空で、解決後のパスにファイルが無い**ときは**移行しない**
  （旧参照なしと同じ・§5.13.4 の書く値は `""`）。キーマップの自動作成・未保存化・通知は起きない。
- **ファイルはあるが読めない**（壊れた JSON / 最上位が dict でない等）ときは**現状どおり移行する**
  （§5.12 と同じく「無い」と「あるが読めない」を区別する。読込失敗時の扱い = 空の一覧が付く）。
- 非文字列は §5.1 どおり空扱い（移行しない）。挙動は変えずテストで固定する。
- 案「現状の挙動を仕様に明記」/「無い・読めないとも移行しない」は採らない。

## スコープ

### 含む

- 正本 `data_schema.md` §5.13.3 への追記（不在時は移行しない・判定の順序）。
- `split_loading.py::_migrate_legacy_trigger_set` への不在判定の追加。
- `tests/test_per_keymap_triggers_load.py` への境界値テスト追加:
  不在（アクティブが項目を持たない / `""` / 別ファイル参照の 3 通り）・あるが読めない・非文字列（数値 / list / dict / `null`）。

### 含まない（後送り）

- 単一 JSON のトップレベル `triggers`（ファイル参照ではないため該当しない）。
- keymap 側 `trigger_set_path` の参照先が無い場合（§5.13.3-1 で既に定義済み・変更しない）。
- L-1 / L-7（phase 34 統合レビュー保留）・`config_service/__init__.py` の分割・80 行超の関数（別フェーズ）。

## このフェーズで読むファイル

1. `instructions/common/spec_detail/data_schema.md:594-650`（§5.13.1〜5.13.4）
2. `keyseq/application/config_service/split_loading.py:405-485`（移行の呼び出しと `_migrate_legacy_trigger_set`）
3. `keyseq/application/config_service/__init__.py:1129-1135`（`_load_optional_json` の不在判定 = `os.path.exists`）
4. `tests/test_per_keymap_triggers_load.py:120-200`（既存の split 移行テストと `load_split` ヘルパ）

## タスク

- task_01: 正本改訂（`data_schema.md` §5.13.3 に不在時の扱いを追記。文言はユーザー確認のうえメインが反映）— **完了**（2026-09-26）
- task_02: 実装 + テスト（不在判定の追加・境界値テスト。codex-implementer → verifier → reviewer）— **完了**（2026-09-26・tests 674〔skip 7〕/ tests_ui 576 / smoke pass・reviewer 完了可）
- task_03: 記録（decisions_archive/35 / current.md の完了記載と「別タスク化候補」の該当行の更新 / `/refactor_check`）

## レビュー方針

- 共通観点は `.claude/rules/review.md`。
- **本フェーズ固有**:
  - 「無い」と「あるが読めない」を区別しているか（不在判定がファイルの**存在**だけを見ており、読込失敗まで除外していないか）。
  - 判定が**解決後のパス**（`config_root` 基準の相対解決）で行われているか。
  - 使用済み（`same`）の判定・自動作成キーマップの既存テストが壊れていないか。
  - 不在時に `_legacy_trigger_set` が `state = "none"` になり、保存側（§5.13.4）で `""` が書かれる経路に乗るか。
