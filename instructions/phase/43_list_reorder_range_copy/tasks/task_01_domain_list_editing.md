# task_01_domain_list_editing

## 目的

一覧の範囲移動・出力シーケンスのループの移動判定・貼り付けの拒否判定・ラベルの連番を、tkinter に依存しない domain の純関数として用意する
（暫定 30 §3.2・§3.3・§4.1〔次に実行は同じ実体を指す〕・§4.2・§4.3・§7）。
**domain 限定（新規関数の追加のみ）。presentation / application は変えない・既存関数の振る舞いを変えない・スキーマ不変。**

## 対象範囲（domain 限定・追加のみ）

### `keyseq/domain/list_editing.py`（新規・一覧の種類に依らない汎用部）

- `move_block(items: Sequence[T], start: int, end: int, target_start: int) -> list[T]`
  - `items[start:end+1]`（連続範囲・`start <= end`）を取り出し、残りの並びの中で塊の先頭が `target_start` に来るように差し込んだ**新しい list** を返す（入力は変えない）。
  - `target_start` は `0 .. len(items) - (end - start + 1)` に丸める。範囲外の `start` / `end` は `ValueError`。
- `shift_block(length: int, start: int, end: int, delta: int) -> int | None`
  - 上へ / 下へ（`delta` = -1 / +1）での塊の新しい先頭位置を返す。端で動けなければ `None`。`delta` が ±1 以外は `None`。
- `index_after_reorder(before: Sequence[object], after: Sequence[object], position: int) -> int`
  - 「次に実行」を同じ実体へ付け直す（§4.1）。`0 <= position < len(before)` なら `before[position]` と**同一の実体（`is`）**の `after` での位置を返す。
  - `position` が範囲外（`>= len(before)` = 連続実行の終端など）なら、そのまま `position` を返す。見つからなければ `ValueError`（呼び出し側の誤り）。
- `numbered_label(label: str, existing: Iterable[str]) -> str` / `numbered_labels(labels: Sequence[str], existing: Iterable[str]) -> list[str]`（§7）
  - 比較は前後の空白を除いた文字列の完全一致（大文字・小文字を区別する）。
  - 空（空白のみを含む）ラベルは空文字列のまま返す。
  - 重ならなければそのまま（元の文字列を返す）。重なれば、末尾の ` (n)`（半角空白 + 半角括弧・n は 2 以上の 10 進整数）を除いたものを基にし、`基 (n)` で既存と重ならない最小の n（2 から）。除いた結果が空なら除かずに全体を基にする。
  - `numbered_labels` は前から順に決め、決めたラベルを以後の「既存」に含める。

### `keyseq/domain/sequence_editing.py`（出力シーケンス固有・追加のみ）

- `can_move_block(actions: Sequence[Any], start: int, end: int, target_start: int) -> bool`（§4.2）
  - `move_block` 後の並びと移動前の並びでそれぞれ `analyze_loops` を取り、次の 3 つをすべて満たすとき True:
    ① 対（始まりと終わりの組）の集合が**行の実体で比べて**同じ ② `unmatched` の行の実体の集合が同じ ③ `too_deep` の行の実体の集合が増えない（移動後 ⊆ 移動前）。
  - 実体の比較は `id()` で行う（同じ dict が一覧に二度入ることは想定しない）。並びが変わらない移動は True。
  - 既存の `can_move` は残す（呼び出し側の置き換えは task_03）。
- `paste_violation(actions: Sequence[Any], items: Sequence[Any]) -> str | None`（§4.3）
  - 末尾へ `items` を足すと規則に反するなら理由の定数を、反しなければ `None` を返す。判定順と定数:
    ① `PASTE_UNBALANCED_LOOP`: `analyze_loops(items)` に `unmatched` がある（片側だけ・崩れた行を含む）
    ② `PASTE_TOO_DEEP`: `analyze_loops(list(actions) + list(items))` の `too_deep` に、`actions` 側で既に too_deep だった行以外が含まれる
    ③ `PASTE_STANDALONE`: 足した結果に戻す / 先頭への行があり、かつ結果の長さが 1 でない（`standalone_violation` と同じ規則を複数行へ一般化）
  - `items` が空なら `None`。定数はモジュールの公開定数（文字列）とする（表示文言は presentation が持つ）。

### テスト

- `tests/test_list_editing.py`（新規）: `move_block`（上へ / 下へ / 先頭・末尾へ / 丸め / 入力不変 / 範囲外で ValueError）・`shift_block`（端で None）・
  `index_after_reorder`（同一実体を追う・同じ内容の別 dict を取り違えない・終端の位置はそのまま）・`numbered_label(s)`（重ならない / `a`→`a (2)` / `a (2)` を `a`・`a (2)` のある所へ → `a (3)` /
  `a (2)` を `a (2)` の無い所へ貼るとそのまま（`a` があっても） / `(2)` だけのラベル / 空ラベル / 前後空白 / 複数貼りで連番が進む）
- `tests/test_sequence_editing.py`（追記）: `can_move_block`（通常の行をループの内外へ = True / ループを丸ごと別ループの中へ = True / ループの行が他のループの行を越えて組が変わる = False /
  始まりを終わりの後ろへ = False / もともと深さ超過のある一覧で無関係な移動 = True / 深さ超過を新たに生む移動 = False / 崩れた行の組が変わる移動 = False）・
  `paste_violation`（各定数と None・判定順）

### 設計メモ / 制約

- 既存の `insert_actions` / `adjust_position_after_insert` / `can_move` / `standalone_violation` / `delete_indices` は変更しない。
- `list_editing.py` は sequence_control を import しない（一覧の種類に依らない）。`sequence_editing.py` から `list_editing.move_block` を使ってよい。
- 関数はおおむね 30 行以内（`.claude/rules/implementation.md`）。

## 読むファイル

- 暫定仕様 `instructions/history/30_list_reorder_range_copy.md` の §4.1〜§4.3・§7
- `keyseq/domain/sequence_editing.py`（全体・編集対象）
- `keyseq/domain/sequence_control.py:40-115`（`LoopStructure` / `analyze_loops` / `_build_loop_structure`）
- `tests/test_sequence_editing.py:1-40`（テストの流儀）

## 含まない

- 範囲削除のループ対の展開（task_03）/ 呼び出し側（presentation）での利用・表示文言（task_02〜task_08）
- トリガー・キーマップの写しの作成（内部キーを除く処理）（task_04・task_07・task_08）
- 既存の `can_move` の置き換え・削除（task_03）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_list_editing tests.test_sequence_editing` が全 pass
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` が全 pass（既存件数 1039・skip 7 から追加分だけ増える）
- `git diff --stat` が上記 4 ファイルのみ

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視なし（domain のみ。操作の目視は task_02 以降）。
