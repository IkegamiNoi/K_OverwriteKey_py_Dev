# task_07: `domain/config.py::ensure_config_compatibility` の分割

## 目的

`keyseq/domain/config.py::ensure_config_compatibility`（**158 行**）を、同じファイル内の補助関数へ**挙動を変えずに**分け、
本体を処理の流れが読める長さにする。

## 読むファイル

1. `keyseq/domain/config.py` の `ensure_config_compatibility` 全体（`grep -n "^def ensure_config_compatibility"` で位置を特定）
2. 同ファイル内で対象関数が呼ぶ関数（`normalize_triggers` / `normalize_hotkey_presets` / `coerce_*` 等）はシグネチャ確認が必要な場合のみ

**注意**: このファイルは **BOM 付き UTF-8** の可能性がある。先頭の BOM を消したり付け足したりしない。

## 実装対象

対象関数の内部ブロックを、同ファイル内の private 補助関数（`_` 付き）へ移す。分け方の目安:

1. 最古形式（`trigger_key` / `actions`）からの `triggers` 変換（先頭付近の `if "triggers" not in config and "trigger_key" in config:` ブロック）
2. 一般設定の正規化（`hotkey_presets` 〜 `debug_jis_special_key_events` まで）
3. 外部キーボード配列の正規化（`external_keyboard_layouts`）→ 正規化済みリストを返す補助関数
4. キーマップ一覧の正規化（`raw_keymaps` のループ）→ さらに「キーマップ 1 件の正規化」と「`mappings` の正規化」を補助関数に分けてよい
5. アクティブキーマップ id の決定
6. 切替キーの正規化（`keymap_switch_keys`）

- **`raw_keymaps` は `data.get("keymaps")`（deepcopy 前の元データ）から読む点を保つ**。`trigger_memo` は `id(raw)` で同じリストの共有を検出しており、
  元データのリスト同一性に依存しているため。`trigger_memo` はキーマップ一覧の正規化 1 回の中で共有される 1 つの dict のまま。
- `keyseq.domain.keymap_triggers` からの**関数内 import**（循環 import 回避のため関数内にある）は、その定数を使う補助関数の中へ移すか、
  本体で import して引数で渡す。**モジュール先頭へ移さない**。
- `config` への代入順（dict のキー挿入順）・`pop` の順序・呼び出し回数を変えない。`coerce_key_name` / `coerce_label` 等の呼び出しの形を変えない。
- 文字列キーの状態 dict を受け渡しに使わない。型注釈を付ける。補助関数はおおむね 30 行以内、本体はおおむね 30〜40 行以内。
- 公開関数のシグネチャは変えない。

## 対象外

- 他の関数・他ファイルの変更 / 改名・ロジック変更・共通化（「キーがあれば `coerce_label`」の集約〔提案書 12・見送り〕も含めない）。
- **テストの実行**（実測は verifier）。

## 完了条件

- compile / tests / tests_ui / smoke が pass（件数不変・verifier 実測）。
- reviewer レビュー（挙動不変・キー挿入順・`raw_keymaps` の出所と `trigger_memo` の共有・関数内 import の維持）を通過。
