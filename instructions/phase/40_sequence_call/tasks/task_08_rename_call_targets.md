# task_08_rename_call_targets

## 目的

トリガーのキーを変えたとき、同じトリガー一覧の全シーケンスの呼び出しの `target` を新しいキーへ書き換える（暫定 29 §5・§2-5）。その後、ユーザーの実機目視で呼び出し全体を確かめる。
**domain（`call_graph.py` に純関数 1 つ）+ presentation（`trigger_panel_controller.rename_trigger`）とテストのみ**。

> 注意: 仕様書の `f5` は例示のキー。実装・テストは実際のキーを使う。

## 対象範囲

### `keyseq/domain/call_graph.py`

- `rename_call_targets(actions, old_key, new_key) -> list[dict] | None`: 呼び出しの行で `call_target(action) == old_key` のものの `target` を `new_key` にした**新しいリスト**（行はコピー）を返す。
  書き換える行が無ければ None。`old_key == new_key` なら None。呼び出し以外の行・他のキーの呼び出しは変えない（行のラベル等も保つ）。

### `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py`（`rename_trigger`）

- `old != new` のとき、キーの変更を反映した後（`t["key"] = new` の後）に、**アクティブなトリガー一覧**（`domain/keymap_triggers.py` の口）の全トリガーについて
  `rename_call_targets(trigger の actions, old, new)` を呼び、None でなければそのトリガーの actions を置き換えて `mark_sequence_dirty(そのトリガー)` を呼ぶ。
- 書き換えたトリガーの実行位置・周回・戻す履歴は**消さない**（`reset_loop_frames` 等のシーケンスの編集の契機を呼ばない）。既存の改名の処理（位置の移し替え・取り消し等）は変えない。
- 既に「参照先なし」だった呼び出しの `target` が新しいキーと一致すると、そのまま繋がる（受容・特別な処理はしない）。

### テスト

- `tests/test_call_graph.py`: `rename_call_targets` — 一致する行だけ書き換わる（大文字・空白の揺れも一致）/ 元のリストは変わらない / 書き換え無し・同じキーで None / 呼び出し以外・他のキーは不変。
- tests_ui（改名の既存テストの書き方。`grep -rn "rename_trigger" tests_ui` で見つかるもの）: `z7` を `z8` に改名すると、別トリガーの `[call z7]` が `[call z8]` になり未保存扱いになる /
  その別トリガーの位置・履歴は変わらない / 呼び出しの無いトリガーは未保存扱いにならない。

### 実機目視（ユーザー・本タスクで実施）

1. 編集ダイアログの system に「呼び出し」があり、呼び出し先を選べる（自分自身は出ない）。「呼び出し先の『間隔(ms)』…」の注記が出る
2. 一覧に `[call] <キー>（<呼び出し先のラベル>）` と出る。呼び出し先を削除すると `（参照先なし）` になる
3. 単発のトリガーから呼ぶと、1 回の押下で呼び出し先が最後まで（呼び出し先の間隔で）送られ、呼び出し元は次の行へ進む。呼び出し先の「次に実行」は変わらない
4. 連続実行のトリガーから呼ぶ。途中で一時停止 → 再開すると続きから（同じ入力を二度送らない）。停止すると呼び出しの行に残る
5. 呼び出し中に他のトリガー（単発）を押すと動く。呼び出し元の同じキーは無視される
6. 循環（A が B を呼び B が A を呼ぶ）を編集で作ろうとすると拒否される。入れ子（A → B → C）が動く
7. 呼び出し先のキーを変えると、呼び出し元の行が新しいキーに追従する
8. 呼び出し先に `[カウンター+1, X]` があるとき、呼び出し後に戻すとカウンターも戻る

## 読むファイル

- `instructions/history/29_sequence_call.md` §5
- `keyseq/domain/call_graph.py`（全体・編集対象）
- `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py:444-500`（`rename_trigger`）
- `keyseq/domain/keymap_triggers.py`（アクティブなトリガー一覧の口）
- 改名の既存 UI テスト 1 ファイルの冒頭（書き方の手本）

## 含まない

- 統合確認（task_09）/ 正本（task_10）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests tests_ui` が clean
- 追加テスト・`discover -s tests` / `-s tests_ui` / `tests.smoke_app` が全 pass・`grep -rn '"triggers"' keyseq/presentation` が 0 件

## 完了条件

- 上記確認 pass・**reviewer 採用**（観点: 純関数〔元を変えない〕/ 同じトリガー一覧の全トリガー / 未保存扱い / 位置・履歴を消さない / 既存の改名の不変 / 先取りなし）。
- 実機目視 1〜8: **本タスクで実施**（ユーザー報告をもって完了）。
