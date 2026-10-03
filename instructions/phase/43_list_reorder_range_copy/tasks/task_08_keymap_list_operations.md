# task_08_keymap_list_operations

## 目的

フル表示のキーマップ一覧に、範囲選択（下線 = アクティブ）・ドラッグ並べ替え（禁止条件・代表の付け替え）・範囲削除・Ctrl+C / Ctrl+V
（切替キーの入力ダイアログつき）を加える（暫定 30 v0.7 §3・§6.1〜6.3・§10-1/2/4/10/11/12）。
**presentation（keymap_panel・keymap_box・list_clipboard）＋ domain に写しの口 1 つ ＋ application に進行中の判定 1 つ。スキーマ不変。**
省略表示のキーマップ表示は変えない。

## 対象範囲

### `keyseq/domain/keymap_triggers.py`（追加のみ・既存の関数は変えない）

- `duplicate_keymap(keymap: dict, new_id: str, label: str) -> dict`: キーマップの写しを返す純関数。
  キー名が `_` で始まる内部の値を除いて深い写しを作り、`id` / `label` を置き換える。トリガー一覧は**共有せず新しい list**（各行も `_` 始まりのキーを除いた深い写し）。
  `mappings` 等の他の値も元と共有しない。元のキーマップは変えない
  （presentation は `"triggers"` を直接書けないため〔静的検査〕、トリガー一覧に触れる写しはこの口に閉じる）

### `keyseq/application/sequence_runner/sequence_runner.py`

- `has_any_active_execution() -> bool`: §6.2 の並べ替えの禁止条件。次のいずれかがあれば True:
  連続実行（`state.run_to_end_key` がある = 実行中・一時停止中）/ 単発の呼び出しの文脈（実行中・一時停止中・アクションの間隔待ちを含む）/
  `state.pending_steps` が空でない / 待ち（送った後の待ち）/ file_line の読込中。**すべてのトリガー一覧が対象**（`has_active_execution(key)` はアクティブな一覧の 1 キーだけ）。
  既存のフィールド（`_run_to_end_*`・保留中の待ち・呼び出し文脈など）から組み立て、どのフィールドを見たかをテストで固定する

### `keyseq/presentation/list_clipboard.py`

- 種類の定数 `CLIP_KEYMAPS = "keymap_rows"` を足す

### `keyseq/presentation/controllers/keymap_panel/keymap_list_edit.py`（新規・処理の本体）

`trigger_list_edit.py` に倣い、キーマップ一覧の範囲操作をここへ集める（`keymap_panel_controller.py`〔527 行〕へは委譲の数行だけ）。

- **選択とアクティブ（§6.1）**: 範囲選択の確定（離したとき・キーを離したとき）に、**下線の行**をアクティブにする（現行の選択 → アクティブ化の流れを使う）。
  切替を拒否したら、選択範囲も下線も元のアクティブの行だけに戻す（現行の拒否と同じ通知）
- **移動（§6.2・`move_keymap_range(start, end, target_start) -> bool`・`bind_listbox_range_drag` の `on_move`）**:
  - `can_start_drag` で `has_any_active_execution()` を見て、True なら開始しない（理由を一時メッセージ:「実行中のためキーマップを並べ替えられません」）。**確定の直前にも再検査**し、True なら `False`（部品が戻す）
  - `move_block` でキーマップの並びを変える。並びが変わらなければ何もしない
  - 並べ替えの前後で共有トリガー一覧ごとの代表（`iter_trigger_sets` の一覧順の先頭）を比べ、変わった一覧は `state.rekey_trigger_set(旧代表 id, 新代表 id)`
  - **アクティブは変えない**。選択範囲 = 動かした行・**下線 = アクティブの行**（§3.1 の「動かした行が選択範囲」と §6.1 の「下線 = アクティブ」を両立させる。帯と下線は別の行でよい）
  - 構成セットを未保存にする（`dirty_tracker.set_dirty(True)`）・後処理（下記）
- **範囲削除（§3.5）**: 範囲が 2 行以上なら「キーマップ n 件を削除しますか？」で 1 回確認（未保存の子がある場合の追記は現行と同じ）。
  全部消すと 0 個になるなら削除しない。範囲にアクティブを含み現行の削除の規則で拒否される場合（`can_switch_keymap(..., changes_active=True)` が False）は範囲全体を削除しない。
  実際の削除は現行の `delete_keymap`（`keymap_panel_controller.py:264-320`）の確認後の処理を 1 件ずつ適用する（確認ダイアログを除いた部分を関数に切り出して共有。共有一覧の rekey・移行記録の後始末・アクティブの決め方を含む）
- **Ctrl+C**: 範囲のキーマップを `CLIP_KEYMAPS` で保管庫へ写す。`"break"`
- **Ctrl+V（§6.3）**: 保管庫の各キーマップについて順に
  - 現行の追加の流れ（`keymap_add_flow.py:18-53`）と同じく、切替キーが未設定の既存キーマップの補完（最初の 1 回）と、**貼るキーマップごとの切替キーの入力ダイアログ**（必須・入力エラーで閉じない・検証は追加と同じ）を開く
  - キャンセルしたら**そのキーマップと残りを貼らない**（それまでに貼ったものは残す）
  - 確定したら `next_keymap_id` で採番し、`duplicate_keymap(元, 新 id, ラベル)` を末尾へ足す。ラベルは `numbered_labels`（貼り先の既存ラベル・先に貼った分を含む）。入力ダイアログのラベル欄の初期値はこの連番のラベル
  - 切替キーを登録し、写したキーマップ・トリガー一覧・各シーケンスを未保存にする（現行の追加と同じ印）
  - アクティブは変えない（現行の追加と同じく元のアクティブに戻す）。貼った行を選択範囲・下線はアクティブの行
  - 種類違い・保管庫が空なら何もしない。`"break"`
  - ダイアログの処理は `keymap_add_flow.py` の既存メソッドを使う（必要なら同ファイルに貼り付け用の入口を足す）
- **後処理**（移動・範囲削除・貼り付けで共通）: 現行の `_refresh_after_keymap_change`（トリガー・シーケンス欄・重なりの表・キーボード表示）→ フック稼働中なら `hook.start_hook()`

### `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py`

- `refresh_keymap_list_ui` に `select: tuple[int, int] | None = None` を足し、あればフル表示の一覧に範囲を当てて下線はアクティブの行にする（無ければ現行どおり）
- 委譲（`on_keymap_list_move` / `copy_keymaps` / `paste_keymaps` / 範囲があるときの `delete_keymap`）

### `keyseq/presentation/views/full_view/keymap_box.py`

- `keymap_listbox` を `bind_listbox_range_drag(on_move=..., on_commit=現行の離したときの処理, can_start_drag=...)` で接続（現行のクリック同期は置き換え）
- `<Control-c>` / `<Control-C>` / `<Control-v>` / `<Control-V>` を一覧にだけバインド

### テスト（追加・修正まで）

- `tests/test_keymap_triggers.py`: `duplicate_keymap`（`_` 始まりが消える・トリガー一覧が新しい list で行も別オブジェクト・`mappings` を共有しない・元が不変・id / label の置き換え）
- `tests/`（sequence_runner のテストの作り方に倣う）: `has_any_active_execution` が各条件（連続実行中・一時停止中・単発の呼び出し・保留中のステップ・待ち・file_line の読込）で True / 何も無ければ False・アクティブでない一覧の保留でも True
- 新規 `tests_ui/test_keymap_list_operations.py`:
  - Shift 範囲選択の確定で下線の行がアクティブになる / 切替拒否で選択も下線も元のアクティブだけに戻る
  - ドラッグ並べ替えでアクティブが変わらない・帯 = 動かした行・下線 = アクティブ / 構成セットが未保存
  - 共有トリガー一覧の代表が変わると `rekey_trigger_set` が呼ばれ実行位置が保たれる
  - 実行中（`has_any_active_execution` を True）は開始しない・確定直前に True になったら戻す
  - 範囲削除: 件数つき確認・0 個になるなら削除しない・アクティブを含み拒否されるなら全体を削除しない
  - Ctrl+C → Ctrl+V: 切替キーのダイアログが貼る数だけ開く・2 件目でキャンセルすると 1 件目だけ残る・ラベルの連番・トリガー一覧を共有しない（写した一覧の行を編集しても元が変わらない）・未保存の印・アクティブ不変
- 既存のキーマップ一覧のクリック同期テスト（`tests_ui/test_listbox_click_selection_sync.py` のキーマップの項）は部品の置き換えに追随

### 設計メモ / 制約

- 1 件の削除の中身は現行コードを切り出して共有し、範囲削除で別の削除ロジックを書かない
- `keymap_list_edit.py` は 300 行・関数 30 行の目安
- キーマップの切替キーの重複は持たない（§6.3。追加と同じ検証）

## 読むファイル

- 暫定仕様 `instructions/history/30_list_reorder_range_copy.md` §3・§6
- `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py:1-150`・`:255-330`・`:415-440`
- `keyseq/presentation/controllers/keymap_panel/keymap_add_flow.py`（全体）
- `keyseq/presentation/controllers/trigger_panel/trigger_list_edit.py`（全体・手本）
- `keyseq/presentation/views/full_view/keymap_box.py`・`views/full_view/trigger_box.py`（接続の手本）
- `keyseq/domain/keymap_triggers.py`・`keyseq/application/app_state.py:30-60`・`:130-165`
- `keyseq/application/sequence_runner/sequence_runner.py:40-110`（フィールドと `has_active_execution`）・待ち / file_line / 呼び出しの mixin は必要な箇所のみ
- `keyseq/application/keymap_service.py:85-165`（採番・作成・削除）
- 手本のテスト: `tests_ui/test_trigger_list_operations.py`

## 含まない

- 正本反映（task_09）/ 省略表示 / キーマップの切替キーの重複保持（§11）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- 追加した tests / tests_ui のテストが全 pass
- `-m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- **実機目視（本タスクで実施）**: キーマップ一覧の Shift 範囲選択（下線 = アクティブ）・ドラッグ並べ替え（アクティブ不変・連続実行中は不可）・範囲削除・
  Ctrl+C → Ctrl+V（切替キーのダイアログ・キャンセルで残りを中止・ラベルの連番・写したキーマップのトリガー一覧が独立）。
