# task_05: `split_payloads.py::build_split_save_payloads` の分割

## 目的

`keyseq/application/config_service/split_payloads.py::build_split_save_payloads`（**120 行**・20 行〜）を、
同じファイル内の補助関数へ**挙動を変えずに**分け、本体を処理の流れが読める長さにする。

## 読むファイル

1. `keyseq/application/config_service/split_payloads.py:1-140`（import と対象関数）
2. 同ファイル内で対象関数が呼ぶ関数の定義は、シグネチャ確認が必要な場合のみ

## 実装対象

対象関数の内部ブロックを、同ファイル内の private 補助関数（`_` 付き・module 関数）へ移す。分け方の目安:

1. 別名保存で予約済みの保存先パス集合（`used_trigger_paths` / `used_sequence_paths`・現 55-64 行付近）→ 子の種類を引数に取る 1 つの補助関数
   （2 つの内包表記は `entry.kind` の比較値だけが違う同型なので、種類を引数にした 1 関数から 2 回呼ぶ）
2. トリガー一覧 1 件分の処理（現 67-116 行付近のループ本体）→ 補助関数。さらに内部の
   - 共有メンバーの親参照のマージ（現 84-91 行付近）
   - keymap の `trigger_set_path` に書く値（`indexed_path`）の決定（現 99-114 行付近）
   を補助関数に分けてよい
3. keymap payload の直列化（現 120-129 行付近）

- **処理の順序・呼び出し回数・例外・戻り値・dict のキー挿入順を変えない**
  （`service._resolve_config_relative_path` が `source` / `source_path` で 2 回呼ばれている点も、回数を減らさずそのまま保つ）。
- トリガー 0 件かつ source_path なしの一覧で `continue` する分岐（現 69-72 行付近）の挙動を保つ。
- 補助関数間で複数の値を受け渡す場合は、文字列キーの `dict[str, Any]` を状態入れ物にせず、型注釈付きタプルまたは private `@dataclass` を使う
  （戻り値の `trigger_sets` の各要素〔既存の dict 形〕はそのまま）。
- 補助関数はおおむね 30 行以内、本体はおおむね 40 行以内。型注釈を付ける。公開関数のシグネチャは変えない。

## 対象外

- 他の関数・他ファイルの変更 / 改名・ロジック変更 / 上記 1 以外の共通化。
- **テストの実行**（実測は verifier）。

## 完了条件

- compile / tests / tests_ui / smoke が pass（件数不変・verifier 実測）。
- reviewer レビュー（挙動不変・順序・呼び出し回数・`continue` 分岐）を通過。
