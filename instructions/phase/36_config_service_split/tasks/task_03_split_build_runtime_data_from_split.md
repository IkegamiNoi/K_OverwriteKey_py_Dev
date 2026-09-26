# task_03: `split_loading.py::build_runtime_data_from_split` の分割

## 目的

`keyseq/application/config_service/split_loading.py::build_runtime_data_from_split`（**154 行**・285 行〜）を、
同じファイル内の補助関数へ**挙動を変えずに**分け、本体を処理の流れが読める長さにする。

## 読むファイル

1. `keyseq/application/config_service/split_loading.py:285-475`（対象関数と直後の `_migrate_legacy_trigger_set`）
2. 同ファイル内で対象関数が呼ぶ関数の定義は、シグネチャ確認が必要な場合のみ

## 実装対象

対象関数の内部ブロックを、同ファイル内の private 補助関数（`_` 付き・module 関数・`service` を受け取る形）へ移す。分け方の目安:

1. 設定値の写し取り・hook キー・外部キーボード配列・ホットキープリセットの読込（現 291-331 行付近）→ runtime を作って返す補助関数
2. `keymaps` 一覧の読込とトリガー一覧の付与・切替キーの登録（現 333-378 行付近）
3. 一覧に無いアクティブキーマップの補完（現 379-399 行付近）
4. 旧形式の移行の記録（現 400-422 行付近。`_migrate_legacy_trigger_set` の呼び出しと `INTERNAL_LEGACY_TRIGGER_SET` の設定・dirty 化）
5. 正規化と親参照の復元（現 423-430 行付近）

- 2 と 3 の間で共有される局所変数（`keymaps` / `keymap_switch_keys` / `loaded_keymap_ids_by_path` / `keymap_trigger_path_presence` /
  `used_keymap_ids` / `trigger_sets` 等）は、引数・戻り値で明示的に受け渡す（モジュール変数・グローバルにしない）。
  受け渡しが煩雑になる場合は 2 と 3 を 1 つの補助関数にまとめてよい。
- **処理の順序・呼び出し回数・例外・戻り値・dict のキー挿入順を変えない**（`runtime` への代入順も含む）。
- 補助関数はおおむね 30 行以内を目安、分割後の本体もおおむね 30〜40 行以内。型注釈を付ける。
- 2 と 3 に同型の「`has_trigger_set_path` の記録 → `attach_trigger_set`」がある。共通化は**しない**（本タスクは分割のみ）。

## 対象外

- 他の関数・他ファイルの変更 / 改名・ロジック変更・共通化 / docstring 以外のコメント追加。
- **テストの実行**（実測は verifier）。

## 完了条件

- compile / tests / tests_ui / smoke が pass（件数不変・verifier 実測）。
- reviewer レビュー（挙動不変・順序維持・局所変数の受け渡し）を通過。
