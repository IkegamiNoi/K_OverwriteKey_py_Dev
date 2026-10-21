# task_03a_identity_of_key_name

## 目的

task_03 の完了判定前レビュー（deep-reviewer 指摘 2）で見つかった潜在バグの修正。`InputGateway.identity_of(send)` の末尾の `raise ValueError(f"Unknown key name: {key!r}")` が、`key_identity(key)` から中身を移したときに無くなった引数 `key` を参照しており、届けば NameError になる（今は 4 種以外の種類が来ないので届かない）。
**infrastructure 限定・挙動不変（届かない分岐の例外の型を ValueError に戻すだけ）・スキーマ不変。**

## 対象範囲（infrastructure 1 行 + テスト 1 件）

- `keyseq/infrastructure/input_gateway.py` の `identity_of`: 末尾の `key` を `send.key` にする
- `tests/test_input_gateway_send.py`: 4 種以外の種類の `KeySend` で `identity_of` が ValueError（キー名を含む）になるテストを 1 件

## 読むファイル

1. `keyseq/infrastructure/input_gateway.py:85-90`・`:367-381`
2. `tests/test_input_gateway_send.py:414-421`（手本）

## 含まない

- 指摘 3・5・9・10（保留・decisions_archive/65 に記録）
- 正本の文言の修正（task_03 で実施）

## 確認

- `compileall` clean / `unittest discover -s tests` 全 pass（1778 + 1 件）/ smoke pass
- tests_ui は presentation に変更が無いので task_02 の実測（1122 pass）を使う

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視: 不要（届かない分岐のみ）。
