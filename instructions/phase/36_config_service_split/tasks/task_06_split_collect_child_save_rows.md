# task_06: `config_io/child_save_rows.py::collect_child_save_rows` の分割

## 目的

`keyseq/presentation/controllers/config_io/child_save_rows.py::collect_child_save_rows`（**99 行**・94 行〜）を、
同じファイル内の補助関数へ**挙動を変えずに**分け、本体を処理の流れが読める長さにする。

## 読むファイル

1. `keyseq/presentation/controllers/config_io/child_save_rows.py:1-30`（import・定数）/ `:94-195`（対象関数）
2. 同ファイル内の `build_row` / `_stored_parent_path` はシグネチャ確認が必要な場合のみ

## 実装対象

対象関数の内部ブロックを、同ファイル内の private 補助関数（`_` 付き）へ移す。分け方の目安:

1. 移行先キーマップ id の読み取り（`migrated_id`・現 120-125 行付近）
2. キーマップの行（現 126-150 行付近）→ `rows` に追加する補助関数（または行のリストを返す補助関数）
3. トリガー一覧 1 件の行（現 152-174 行付近）
4. その一覧に属するシーケンスの行（現 175-191 行付近）

- **行の並び順を変えない**（キーマップの行すべて → 一覧ごとに「トリガー一覧の行 → その一覧のシーケンスの行」）。
- シーケンスの行の `current_parent` は、同じ一覧の `trigger_target`（**None の場合も含めて**そのまま）を使う点を保つ。
- `trigger['key']` の添字アクセス（`label` が空のときの表示名）など、例外が出うる式の形を変えない。
- `_stored_parent_path` などの呼び出し回数・順序を変えない（テストが `config_service.os.path` を差し替えて `_stored_parent_path` 経由の結果を見ているため）。
- 補助関数間で複数の値を受け渡す場合は文字列キーの状態 dict を使わない。型注釈を付ける（既存の引数に注釈が無い箇所は、補助関数でも無理に付けなくてよい）。
- 補助関数はおおむね 30 行以内、本体はおおむね 30 行以内。公開関数のシグネチャは変えない。

## 対象外

- 他の関数・他ファイルの変更 / 改名・ロジック変更・共通化。
- **テストの実行**（実測は verifier）。

## 完了条件

- compile / tests / tests_ui / smoke が pass（件数不変・verifier 実測）。
- reviewer レビュー（挙動不変・行の並び順・`trigger_target` の受け渡し）を通過。
