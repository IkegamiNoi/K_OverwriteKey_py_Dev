# task_01_call_domain

## 目的

呼び出し（`op: call`・`target`）の domain 側を作る（暫定 29 §3・§4.2 の開始時点のコピー・§5・§6 の検査と表示）。**domain 限定・純関数・UI / runner 非依存**。
実行（task_02〜05）・UI（task_06〜08）はこの口を使う。

## 対象範囲（domain とテストのみ）

### `keyseq/domain/sequence_control.py`

- `OP_CALL: str = "call"`・`MAX_CALL_DEPTH: int = 9` を追加。
- 表示: `format_control_value(..., resolve_call: Callable[[Any], tuple[str, str | None]] | None = None)` を追加（キーワード専用・既定 None）。
  `resolve_call(target)` は `(表示するキー, 呼び出し先のラベル or None=参照先なし)` を返す。呼び出しの表示:
  - 解決できてラベルが空でない → `[call] f5（ラベル）` / ラベルが空 → `[call] f5` / 参照先なし（None）→ `[call] f5（参照先なし）`
  - `resolve_call` が None（表示の文脈が無い）→ `[call] <target を trim した文字列>`。`target` が空・非文字列 → `[call] （呼び出し先なし）`
  - 呼び出し以外の表示は変えない。このモジュールは `config.py` を import しない（循環 import を作らない）。

### `keyseq/domain/config.py`

- `normalize_actions` の trim 対象に `"target"` を加える（`:162` の tuple）。
- `format_action_list_item(..., resolve_call=None)` を追加し、`format_control_value` へそのまま渡す（行のラベルの付け方は既存どおり）。

### `keyseq/domain/call_graph.py`（新規）

呼び出しグラフの純関数。トリガーの参照は引数の `find_trigger: Callable[[str], Mapping | None]`（正規化済みキー → トリガー辞書 or None）で受ける。キーの比較は `config.normalize_key_name`。

- `call_target(action) -> str`: 呼び出しの行なら `target` を `normalize_key_name` した値（空・非文字列は `""`）、それ以外は `""`。
- `call_targets(actions) -> list[str]`: シーケンス中の呼び出しの `target`（空は除く・出現順・重複はそのまま）。
- `@dataclass(frozen=True) CallEntry`: `actions: tuple[dict, ...]`（**ディープコピー**）・`interval_ms: int`（トリガーの `run_to_end_delay_ms` を `coerce_nonnegative_int`・既定 `DEFAULT_RUN_TO_END_DELAY_MS`）。
- `collect_call_snapshot(target_key, find_trigger) -> dict[str, CallEntry | None]`: `target_key` から呼び出しの辺を幅優先で辿り、**深さ `MAX_CALL_DEPTH` まで**（target_key が深さ 1）の
  キー → `CallEntry`（見つからないキーは None）の表を返す（暫定 §4.2 の開始時点のコピー）。既に表にあるキーは辿り直さない（循環でも止まる）。
- `edit_call_violation(owner_key, target_key, find_trigger) -> str | None`: 呼び出しの行を保存するときの検査（暫定 §6）。違反なら理由の文言、なければ None。判定順:
  1. `target_key` が空 → 「呼び出し先を選んでください」
  2. 見つからない → 「呼び出し先のトリガーがありません（f5）」
  3. `target_key == owner_key` → 「自分自身は呼び出せません」
  4. **循環**: `target_key` から辿って `owner_key` に達する → 「呼び出しが循環します（f5 > f6 > f1）」（辿った経路を含める）
  5. **下流の深さ**: `1 + (target_key から下流の最大の深さ)` が `MAX_CALL_DEPTH` を超える → 「呼び出しの深さが 9 を超えます」（上流は数えない）
  6. **直接の呼び出し先が戻す・先頭へだけ**（シーケンスが 1 行で `back` / `rewind`）→ 「戻す・先頭へのトリガーは呼び出せません」
  - 保存しようとしている行の呼び出しは `owner_key` の現在のシーケンスにまだ無い前提で、`owner_key` → `target_key` の辺を足した状態で判定する。
  - 下流に既存の循環があっても無限に辿らない（訪問済みで打ち切る）。

### テスト

- `tests/test_sequence_control.py`: 呼び出しの表示 5 通り（ラベルあり / 空 / 参照先なし / 解決関数なし / target 空）・呼び出し以外の表示が不変。
- `tests/test_domain_config.py`（既存の `normalize_actions` / `format_action_list_item` のテストの隣）: `target` の trim・`format_action_list_item` で行ラベルが `（ラベル）: 行ラベル` の形になる。
- `tests/test_call_graph.py`（新規）: `call_target`（大文字・空白の正規化・非文字列）/ `collect_call_snapshot`（ディープコピー＝元を変えても表が変わらない・間隔の既定値と不正値・参照先なし・深さ 9 で止まる・循環で止まる）/
  `edit_call_violation` の 6 つの判定と判定順・上流の深さを数えないこと・下流の既存の循環で無限に辿らないこと。

## 読むファイル

- `instructions/history/29_sequence_call.md` §3・§4.2・§5・§6
- `keyseq/domain/sequence_control.py`（全体・編集対象）
- `keyseq/domain/config.py:1-40`（`normalize_key_name`・定数）・`:140-170`・`:400-450`
- `tests/test_sequence_control.py`・`tests/test_domain_config.py` の該当テスト部分（書き方の手本）

## 含まない

- `advance` / `settle_after_normal` / runner（task_02〜05）/ 編集ダイアログ・一覧の配線・改名（task_06〜08）/ 正本（task_10）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests` が clean
- `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_call_graph tests.test_sequence_control tests.test_domain_config -v` が全 pass
- `unittest discover -s tests` が全 pass

## 完了条件

- 上記確認 pass・**reviewer 採用**（観点: 純関数・依存方向〔sequence_control が config を import しない〕/ 判定順と文言 / ディープコピー / 深さの数え方 / 既存の表示・正規化の不変 / 先取りなし）。
- 実機目視: task_08 でまとめて実施。
