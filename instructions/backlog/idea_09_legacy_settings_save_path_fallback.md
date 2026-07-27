# idea_09_legacy_settings_save_path_fallback.md

## 概要

別名保存でレガシー `<base_dir>/settings/` 配下を保存先に選ぶと、**ユーザーが選んだパスが捨てられ、
無言で `config/user/keymap_sets/default.json` へ保存される**（既存セットを上書きしうる）。
Phase α で「`default.json` への無言の自動保存・自動フォールバックを廃止」したが、**この 1 経路だけ残存**している。
挙動変更（＝仕様判断）を伴うため、着手時は仕様変更フローに従う。

## 起票経緯（2026-07-28）

出所: Phase α（[05_keymap_set_new_and_default_dir](../phase/05_keymap_set_new_and_default_dir/phase.md)）
task_05 の統合レビューにおける `deep-reviewer` 指摘2。
ユーザー判断（2026-07-28）で「**α のスコープを広げず idea 起票して後続へ**」と決定した
（他の選択肢: α 内で task_05b を起票して塞ぐ / 現状維持で記録のみ）。

## 現状

- `keyseq/presentation/config_paths.py` の `normalize_keymap_set_save_path`（`:72-73`）:
  ```python
  if self.is_within_legacy_settings(normalized):
      return self.preferred_keymap_set_path()   # = config/user/keymap_sets/default.json
  ```
  保存先が `<base_dir>/settings/` 配下だと、**選択パスを破棄して固定 `default.json` を返す**。
- 呼び出し元は `keymap_set_io.save_keymap_set_to`（`:80`）。`save_as` でユーザーがレガシーディレクトリを
  選んだ場合、成功ダイアログには実際の保存先（`default.json`）が出るため無言ではないが、
  **選択が無視されたことは示されない**。
- 関連する Phase α の確定事項: 暫定仕様 [04](../history/04_keymap_set_new_and_default_dir.md) §2
  「`default.json` への無言の自動保存・自動フォールバックを廃止する」/ §5「`default.json` を返す用途が
  保存ターゲットに漏れていないか grep で確認する」。
  task_03 の監査は「**空パス**が到達しない」ことのみ確認しており、本経路は監査の網から漏れていた。
- 旧構成（`settings/config.json`）からの移行を意図した実装と推測されるが、レガシー読込側
  （`resolve_keymap_set_path` / `resolve_startup_path`）とは非対称で、**保存側だけがパスを差し替える**。

## 提案（方向性・要設計）

1. **案 A: エラーにする** — レガシー配下が選ばれたら保存せず、「この場所へは保存できません」と提示して
   別名保存ダイアログへ戻す（or `return False`）。ユーザーの選択を黙って変えない点で最も素直。
2. **案 B: 選択どおり保存する** — レガシー分岐を削除し、選ばれたパスへそのまま書く。
   旧構成との混在を許すことになるため、読込側の扱いとの整合を要検討。
3. **案 C: 案内した上で既定へ誘導** — 確認ダイアログを出し、`config/user/keymap_sets/` 配下への
   保存を提案する（初期ファイル名は `keymap_set.json`）。

いずれも**挙動変更**であり、`spec_change_workflow.md` に従って正本
（`spec_detail/`）側の記述と併せて確定する必要がある。テストは `tests/test_config_paths.py`
（`test_normalize_keymap_set_save_path` がレガシー分岐を現挙動として固定済み）の更新を伴う。

## 想定スコープ

- **含む**: `config_paths.normalize_keymap_set_save_path` のレガシー分岐 / 呼び出し元
  （`keymap_set_io.save_keymap_set_to` / `save_as`）の扱い / 既存テストの期待値更新。
- **含まない**: レガシー**読込**（`resolve_keymap_set_path` / `resolve_startup_path` /
  `is_within_legacy_settings` 自体）の廃止。旧 `settings/` 構成のマイグレーション機能の新設。
- **影響レイヤ**: presentation のみ（`config_paths.py` + `keymap_set_io.py`）。スキーマ不変。
- **仕様変更**: **あり**（案 A〜C いずれも保存先決定の挙動が変わる）。着手時は暫定仕様先行モードか
  直接改訂かを規模で判断する（単一ファイル・少数条項なら直接改訂で足りる見込み）。
- **着手条件**: 特になし（Phase α 完了後であればいつでも可）。優先度は**低**
  （レガシーディレクトリを能動的に選んだ場合のみ発生。既存挙動で新規退行ではない）。
