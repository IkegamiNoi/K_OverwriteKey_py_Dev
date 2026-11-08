# task_01_minus_key_name

## 目的

キー置換の置換先（や他のキーの取得）でマイナスのキーを記録すると、記録された名前 `minus` を `keyboard` ライブラリが解決できず、
送信・フックの登録でエラーになる不具合を直す（暫定 56 §8）。
**domain（キー名の正規化）+ presentation（Tk の keysym の変換表）限定・application / infrastructure 不変・JSON スキーマ不変**
（読み替えは意味の変更ではない＝同じキーの別名）。

### 原因（メインセッションの実測 2026-11-08・`.venv` の python）

- Tk の取得は keysym を小文字にするだけで、記号は変換しない（`keyseq/presentation/tk_keys.py:51-75`）。マイナスのキーは `minus` で記録される
- `keyboard.key_to_scan_codes("minus")` は `ValueError`（`keyboard` は `minus` を Unicode の `−` に読み替えるため）。`"-"` は解決できる（`(74, 12)`）
- 他の Tk の記号の keysym（`equal` / `comma` / `period` / `slash` / `backslash` / `semicolon` / `apostrophe` / `bracketleft` / `bracketright` / `grave` / `bar` / `plus` / `asterisk` ほか）は `keyboard` で解決できる。
  解決できなかったのは `minus` と `quoteleft` / `quoteright` / `yen`（後 3 つは Windows の Tk が出すかは未確認）
- 送信の解決は `keyseq/infrastructure/input_gateway.py:224-248`（`_resolve_key` → 解決できなければ `ValueError("Unknown key name")`）

## 対象範囲（domain の正規化 + tk_keys の変換表のみ）

### `keyseq/domain/config.py`（`normalize_key_name`）

- キー名の正規化で **`minus` → `-`** に読み替える（既存の JSON に保存済みの `minus` も読込で `-` になる。保存すれば `-` で書かれる）
- 読み替えの表は 1 か所（例: モジュール内の小さな辞書）。今回は `minus` の 1 件だけ入れる
- ホットキー（`ctrl+minus` 等の組み合わせ）のトークンにも同じ読み替えが要るかを調べ、ホットキーの正規化の関数が domain にあれば同じ表を使う。
  無ければ手を入れず、完了報告で経路と結論を書く

### `keyseq/presentation/tk_keys.py`（`TK_KEYSYM_TO_KEYBOARD_NAME`）

- `"minus": "-"` を足す（新しい取得で最初から `-` を記録する）

### テスト

- `tests/` に追加: `normalize_key_name("minus") == "-"`・`normalize_key_name("MINUS") == "-"`・`"-"` は不変・他の名前（`equal` 等）は不変
- 既存の JSON の読込（キーマップの `mappings` の置換元・置換先、トリガーのキー）で `minus` が `-` になること
- `normalize_tk_keysym("minus") == "-"`
- ホットキーにも読み替えを入れた場合はそのテスト

### 設計メモ / 制約

- `quoteleft` / `quoteright` / `yen` は今回の対象外（Tk が出すか未確認のため）。読み替えの表に入れない
- 送信側（infrastructure）に別名の処理を足さない（正規化を 1 か所にする）
- `-` / `+` / `*` / `/` の解決で `keyboard` が最初にテンキーの走査コード（74 / 78 / 55 / 57397）を返す件は**本タスクでは扱わない**（下の「含まない」）

## 読むファイル

- `keyseq/domain/config.py`（`normalize_key_name` / `coerce_key_name` の定義と、`_normalize_keymap_mappings` 付近 :283-293）
- `keyseq/presentation/tk_keys.py`（全体・小さい）
- `keyseq/infrastructure/input_gateway.py:224-248`（送信の解決。読むだけ）
- ホットキーの正規化を探す: `keyseq/domain/hotkey.py`（あれば該当関数のみ）
- 手本のテスト: `tests/` の `normalize_key_name` / `tk_keys` を扱う既存テスト（grep で探し、該当の数十行のみ）
- 正本: `instructions/common/spec_detail/key_input.md` §7.4（取得の入口・名前）・`data_schema.md` のキー名の正規化の記述（該当節のみ）

## 含まない

- サンプルの num の q を `minus`（＝ `-`）にすること（task_03 の既定データで行う）
- 記号キー全般の取得名の見直し（idea_45 の範囲）・`bar` → `|` 等の表示（スコープ外・別扱い）
- `-` / `+` / `*` / `/` が `keyboard` でテンキーの走査コードを先に返す件（気づいた事実として完了報告に書くだけ）
- 正本の更新（task_09 でまとめて反映）

## 確認

- 追加したテストが通る（verifier が `.venv` で実行）
- `python -m compileall keyseq` が通る
- 既存テスト全件: `python -m unittest discover -s tests` / `python -m unittest discover -s tests_ui` / `python -m tests.smoke_app` が通る

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視（キー置換の置換先にマイナスを選んでフックで送れる）は task_09 でまとめて実施
