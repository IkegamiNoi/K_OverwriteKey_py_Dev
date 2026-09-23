# 提案書 12: phase 30（アクション要素と内部キーの型正規化）後のリファクタ

> `/refactor_check`（`.claude/commands/refactor_check.md`）の判定 = **推奨（境界事例）**。
> **ユーザー承認前に実装しない**。判定の記録は
> [decisions_archive/30](../../.claude_data/state/decisions_archive/30_action_and_internal_key_type_coercion.md)。
> 状態: **見送り**（2026-09-23・ユーザー判断。効果が小さく 5 箇所が同一ファイル内で近接しているため。
> `current.md`「別タスク化候補」の「定数・直値の重複」へ送り、同型がさらに増えたら再判定する）。

## 判定の要約

PHASE_BASE = `102fdfc`（phase 30 起票コミット `ff81f14` の親）。対象 = `keyseq/` の変更 **1 ファイル**
（`keyseq/domain/config.py`・353 → 361 行・+10 / -2。`verifier` 実測・作業ツリー比較）。

- **M3 該当（境界・→ 項目 1）**: 「キーがあれば `coerce_label` で置き換える」2 行の同じ形が、このフェーズで **5 箇所**新設された
  （フェーズ前 0）: `normalize_actions` の `type`（`:153-154`）/ `button`（`:155-156`）、
  `ensure_config_compatibility` の `_trigger_set_source_path`（`:165-166`）/ `_sequence_source_path`（`:203-204`）/
  `_keymap_source_path`（`:284-285`）。規則（§5.1 + 「無いキーは補わない」）が変わると 5 箇所とも直す。
  各ブロックは 2 行と小さいため境界事例とし、定性材料（`domain/config.py` に正規化 / 互換変換 / hook キー解決 /
  一覧表示の整形と**異なる責務のまとまりが 3 つ以上**ある）で「推奨」に倒した。
  **効果は小さい**（10 行 → 5 行 + ヘルパ 4 行程度）ため、**見送って「別タスク化候補」へ送る判断も妥当**。
- **M1 / M2 / M4 / M5 / M6 非該当**: M1 = 361 行（600 未満）/ M2 = 新規関数なし・`ensure_config_compatibility`（161 行・既存）の変更は 8 行 /
  M4 = 列挙タプルは 3 → 2 要素 × 2 箇所で**減少** / M5 = 申し送りコメント 0 件 /
  M6 = 照合範囲（変更ファイル + import 先）に同値の定数なし（`ConfigService.INTERNAL_*` は application 層で import 対象外）。
  ただし内部キー名の文字列直値は同ファイル内で各 1 → 3 回に増えている（項目 1 で同時に解消できる）。

## 項目 0（先行）: 安全網の確認

- **対象領域のカバー**: `tests/test_domain_config.py` の `NormalizeActionsTest`（`type` / `button` の非文字列・trim・キー不在・要素保持）/
  `EnsureConfigCompatibilityTest`・`PathFieldCoercionTest`（内部キー 3 種の非文字列・trim と大小文字の保持・キー不在・非パス内部キーの保持）。
  phase 30 で追加した 9 件がちょうど 5 箇所の挙動を固定している。
- **確認手順**: 変更前に下記「完了条件」のコマンドを実行し全 pass を記録する。**特性テストの追加は不要の見込み**。

## 項目 1: 「キーがあれば `coerce_label`」を 1 関数へ寄せる

- **ID**: R12-1
- **対象**: `keyseq/domain/config.py:153-156`（`normalize_actions`）/ `:165-166` / `:203-204` / `:284-285`（`ensure_config_compatibility`）
- **何が問題か（M3）**: 上記「判定の要約」のとおり。
- **どう変えるか**: `coerce_label` の直後に private 関数を 1 つ置く（利用は同ファイル内のみ = Private。新規ファイルは作らない）。

  変更前（5 箇所）:
  ```python
  if "_sequence_source_path" in trigger:
      t["_sequence_source_path"] = coerce_label(trigger["_sequence_source_path"])
  ```
  変更後:
  ```python
  def _coerce_label_if_present(dst: dict[str, Any], src: dict[str, Any], key: str) -> None:
      """src にキーがあれば、coerce_label した値を dst へ書く（無いキーは補わない・§5.1）。"""
      if key in src:
          dst[key] = coerce_label(src[key])

  _coerce_label_if_present(t, trigger, "_sequence_source_path")
  ```
  `normalize_actions` の 2 箇所は `for key in ("type", "button"): _coerce_label_if_present(a, a, key)`、
  最上位は `_coerce_label_if_present(config, config, "_trigger_set_source_path")`。
- **完了条件**: `../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui` clean /
  `-m unittest discover -s tests` = 565 件 OK（skip 7・**件数不変**）/ `-m unittest discover -s tests_ui` = 532 件 OK /
  `-m tests.smoke_app` OK / `git diff` が `keyseq/domain/config.py` のみ・テスト無変更。
- **リスクと戻し方**: 読み元と書き先が異なる箇所（`trigger` → `t` / `item` → `normalized_keymaps[-1]`）で引数を取り違えると、
  コピー前の値を読む / 別の dict へ書くことになる。既存テスト 9 件で検出できる。戻しは当該コミットの revert。
- **依存**: なし。

## 見送る場合

`current.md`「別タスク化候補」の「定数・直値の重複」へ 1 行追記し、同型がさらに増えたときに再判定する。
