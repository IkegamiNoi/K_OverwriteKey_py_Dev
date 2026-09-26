# task_04: `save_plan_execution.py::save_runtime_data` の分割

## 目的

`keyseq/application/config_service/save_plan_execution.py::save_runtime_data`（**125 行**・38 行〜）を、
同じファイル内の補助関数へ**挙動を変えずに**分け、本体を処理の流れが読める長さにする。

## 読むファイル

1. `keyseq/application/config_service/save_plan_execution.py:1-165`（import と対象関数）
2. 同ファイル内で対象関数が呼ぶ関数の定義は、シグネチャ確認が必要な場合のみ

## 実装対象

対象関数の内部ブロックを、同ファイル内の private 補助関数（`_` 付き・`service` を受け取る module 関数）へ移す。分け方の目安:

1. 入力 `data` から正規化後の keymap / sequence へ親参照を戻す処理（現 53-80 行付近）
2. 保存先パスの解決・payload の組み立て・保存計画の検証（現 81-105 行付近）。解決済みの値（`resolved_config_root` /
   `resolved_keymap_set_path` / payloads 等）は戻り値で返す
3. payload 側の親参照を正規化後の keymap へ写し戻す処理（現 106-114 行付近）
4. ファイルの書き込み一式（現 116-140 行付近。**書き込み順を厳守**: dirs → sequences → trigger_sets → keymaps → keymap_set → startup → legacy copy）
5. 保存後の状態更新（現 155-162 行付近。`apply_saved_child_paths` / 移行記録のリセット / `hook_keys_individual` の除去）

- **`warnings.warn(cleanup_warning, RuntimeWarning, stacklevel=2)` は本体に残す**（補助関数へ移すと警告の発生位置〔stacklevel〕が変わるため）。
  `_cleanup_migrated_trigger_set_parent_ref` の呼び出しも本体でよい。
- `sanitized_legacy`（`service._sanitize_runtime_for_storage(normalized)`）は**現在と同じ時点**（親参照を戻した直後・payload 組み立ての前）で計算する。
- **処理の順序・呼び出し回数・例外・戻り値を変えない**。補助関数はおおむね 30 行以内、本体はおおむね 40 行以内。型注釈を付ける。
- 公開関数 `save_runtime_data` のシグネチャ（引数・既定値・戻り値注釈・先頭行の書式を含む）は変えない。

## 対象外

- 他の関数・他ファイルの変更 / 改名・ロジック変更・共通化。
- **テストの実行**（実測は verifier）。

## 完了条件

- compile / tests / tests_ui / smoke が pass（件数不変・verifier 実測）。
- reviewer レビュー（挙動不変・書き込み順・警告の位置・`sanitized_legacy` の計算時点）を通過。
