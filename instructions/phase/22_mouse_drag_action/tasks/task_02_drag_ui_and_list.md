# task_02_drag_ui_and_list

## 目的

ドラッグを**入力・保存・表示**できるようにする。根拠は暫定仕様
[19_mouse_drag_action.md](../../../history/19_mouse_drag_action.md) の **§3-8（生成停止）・§4（UI）・§6（一覧表示）・§8**。

**presentation + domain 限定**（application は下記「定数の移設」のみ・infrastructure は不変）。
実行経路（`drag_mouse` / 分岐 / クランプ）は **task_01 で完了済み**なので触らない。

## 対象範囲（presentation + domain 限定。application は定数の移設のみ）

### 定数の移設（`keyseq/domain/config.py` + `keyseq/application/action_executor.py`）

- `DEFAULT_DRAG_SPEED_PX_PER_SEC = 1000` を **`keyseq/domain/config.py` へ移す**
  （既存の `DEFAULT_RUN_TO_END_DELAY_MS` と同じ置き方・同じ使われ方にする）。
- `action_executor.py` は自前定義をやめ `from keyseq.domain.config import DEFAULT_DRAG_SPEED_PX_PER_SEC` で読む
  （**`MIN_DRAG_DURATION_SEC` / `MAX_DRAG_DURATION_SEC` は action_executor に残す**。実行時の都合なので domain へは出さない）。
- 理由: 既定速度を presentation（入力欄の初期値）・domain（一覧表示）・application（実行）の 3 箇所が使うため、
  直値 `1000` を複数箇所へ書かない。**挙動は変えない**。

### `keyseq/domain/config.py`

`format_action_list_item` の `mouse_click` 分岐を拡張する（暫定仕様 §6）。

- `bool(action.get("drag"))` が true のとき:
  `value_display = f"({x}, {y})→({to_x}, {to_y}) {button} {speed}px/s"`
  （`speed = action.get("drag_speed", DEFAULT_DRAG_SPEED_PX_PER_SEC)`）
- false / 未指定のときは**現在の表示のまま**（`(x, y) button xN`）。**既存の書式を変えない**。

### `keyseq/presentation/dialogs/action_dialog.py`

**(1) ウィジェットの追加**（既存の `self.mouse_frame` の中。行番号は末尾に足す）

- `self.mouse_drag_var = tk.BooleanVar(value=False)` +
  チェックボタン「ドラッグ（範囲選択・ドラッグ&ドロップ）」（`command=self._sync_drag_ui`）
- 「離す位置 X」「離す位置 Y」の `ttk.Entry`（`self.mouse_to_x_var` / `self.mouse_to_y_var`）
- 「離す位置を取得」ボタン（`self.mouse_to_capture_btn`）+ 専用ヒントラベル（`self.mouse_to_hint`）
- 「速度（px/秒）」の `ttk.Entry`（`self.mouse_drag_speed_var`・初期値 `str(DEFAULT_DRAG_SPEED_PX_PER_SEC)`）
- **既存ウィジェットの参照を保持**する（現在は保持していない）:
  - X / Y のラベル（`self.mouse_x_label` / `self.mouse_y_label`）— 文言の切替に使う
  - 回数の Entry（`self.mouse_clicks_entry`）— 無効化に使う

**(2) `_sync_drag_ui()` の新設**

- ドラッグ ON: 上記の「離す位置」「取得ボタン」「速度」を `grid()` で表示 /
  X・Y のラベル文言を **「掴む位置 X」「掴む位置 Y」** へ /
  **回数の Entry を `state="disabled"`**
- ドラッグ OFF: それらを `grid_remove()` で非表示 / ラベル文言を **「X」「Y」** へ戻す / 回数の Entry を `state="normal"`
- **表示 / 非表示は既存の `mouse_frame` と同じ `grid()` / `grid_remove()` 方式**にする（`pack` と混在させない）。
- `_sync_capture_ui()` の `mouse_click` 分岐から `_sync_drag_ui()` を呼ぶ（種別を戻したときは `mouse_frame` ごと隠れるので追加処理は不要）。

**(3) 座標取得の一般化と排他**（暫定仕様 §4・§7）

- `_capture_mouse_position` を
  `_capture_mouse_position(self, x_var, y_var, button_widget, hint_widget)` の形へ**一般化**する
  （リスナーの起動・`after(0, ...)` での反映・停止の作り方は**現在の実装をそのまま流用**する）。
- **取得は同時に 1 つだけ**: 取得を始めたら**両方のボタンを `disabled`** にし、取得完了時に**両方を `normal` へ戻す**
  （`finally` 相当の位置で戻す。片方だけ戻さない）。
- 既存の「クリック位置を取得」ボタンは `command=lambda: self._capture_mouse_position(self.mouse_x_var, self.mouse_y_var, self.mouse_capture_btn, self.mouse_hint)` の形にする。

**(4) `on_ok` の検証と dict 生成**（暫定仕様 §3・§4）

`mouse_click` 分岐の末尾を次のようにする。**hotkey / text の分岐と、ドラッグ OFF 時の出力は一切変えない**。

- ドラッグ OFF: **現在とまったく同じ dict**（`{"type": "mouse_click", "x", "y", "button", "clicks", "label"}`）。
  **`drag` / `to_x` / `to_y` / `drag_speed` を含めない**（§3-8 の生成停止）。
- ドラッグ ON:
  - `to_x` / `to_y` が空 / `int()` 変換不能なら `messagebox.showerror("入力エラー", ...)` で**差し戻す**（既存の X/Y と同じ扱い・`destroy` しない）
  - 速度は空 / 変換不能 / 0 以下なら **`DEFAULT_DRAG_SPEED_PX_PER_SEC`**（差し戻さない）
  - dict は `{"type": "mouse_click", "x", "y", "button", "clicks": 1, "label", "drag": True, "to_x", "to_y", "drag_speed"}`
    （**`clicks` は 1 固定** = §3-6）

**(5) 既存値の復元**（`__init__` の `initial` 分岐）

- `drag` が true なら `mouse_drag_var` を True にし、`to_x` / `to_y` / `drag_speed` を各欄へ復元する
  （既存の `x` / `y` / `button` / `clicks` の復元方法に合わせる）。
- 復元後に `_sync_capture_ui()` が走る位置は変えない（既存のまま）。

### `tests/test_domain_config.py`（既存ファイルへ追加）

- **既存テストは変更しない**。次を追加する:
  - ドラッグの表示: `{"type": "mouse_click", "x": 100, "y": 200, "to_x": 400, "to_y": 500, "button": "left", "drag": True, "drag_speed": 1000}`
    → `"01. [mouse_click] (100, 200)→(400, 500) left 1000px/s"`
  - `drag_speed` 欠落時に既定 1000 で表示されること
  - `drag: False` / `drag` キー無しで**従来表示のまま**であること

### `tests_ui/test_action_dialog_drag.py`（新規）

`tests_ui/test_dialog_teardown_flows.py` の作り（`setUpClass` で `App` を 1 つ作り、`ActionDialog(self.app, title=...)` を生成、
`addCleanup` で破棄）を手本にする。**`messagebox` は `patch.object` で差し替える**（差し戻し経路がモーダルでブロックしないように）。

1. **drag OFF の dict**: 種別 `mouse_click` + X/Y/ボタン/回数を入れて `on_ok()` →
   `app._dialog_result` に **`drag` / `to_x` / `to_y` / `drag_speed` が含まれない**こと（§8-2）。
2. **drag ON の dict**: チェックを入れて 2 点 + 速度を入れて `on_ok()` → 期待どおりのキーと値・**`clicks` が 1** であること（§8-9）。
3. **ON → OFF の往復**: `initial` にドラッグ ON の dict を渡してダイアログを開き、復元を確認 →
   チェックを外して `on_ok()` → 結果にドラッグ用 4 キーが**含まれず**、`x` / `y` / `button` / `clicks` / `label` は残ること（§8-3・§8-3b）。
4. **離す位置の検証**: ドラッグ ON で離す位置を空にして `on_ok()` → `messagebox.showerror` が呼ばれ、
   **`_dialog_result` が設定されず**ダイアログが生存していること。
5. **速度の不正値**: 空 / `"abc"` / `"0"` → 結果の `drag_speed` が **1000** であること（§8-5）。
6. **回数欄の無効化**: チェック ON で `mouse_clicks_entry` が `disabled`、OFF で `normal` に戻ること（§8-9）。
7. **座標取得の排他**: 取得を 1 つ始めると**両方のボタンが `disabled`** になること
   （`pynput` の `mouse.Listener` は `patch.object` で差し替え、実際のクリック待ちをしない）。

### 設計メモ / 制約

- **task_01 の実行経路（`action_executor` の分岐・クランプ・`input_gateway.drag_mouse`）を変更しない**
  （定数の import 元を変える 1 行のみ）。
- 既存の hotkey 記録 UI・プリセット・`destroy` の後始末には触らない。
- `pynput` のリスナーは既存と同じく `daemon = True` で起動し、**取得完了で停止する**作りを維持する。
- 型注釈を付ける。関数は 30 行以内を目安に（超えるならメソッドを分ける）。
- **python を実行しない**（この環境では起動できない）。テストの実行は `verifier` が行う。
- **`git checkout --` / `git restore` / `git stash` を使わない**。

## 読むファイル

1. `instructions/history/19_mouse_drag_action.md` の **§3 / §4 / §6 / §8**（根拠）
2. `keyseq/presentation/dialogs/action_dialog.py`（全体・編集対象）
3. `keyseq/domain/config.py:300-320`（`format_action_list_item`）+ `DEFAULT_RUN_TO_END_DELAY_MS` の定義箇所（定数の置き方の手本）
4. `keyseq/application/action_executor.py:1-20` と定数定義の箇所（import への差し替えのみ）
5. `tests/test_domain_config.py:228-245`（既存の `mouse_click` 表示テスト）
6. `tests_ui/test_dialog_teardown_flows.py:1-40` と `:84-130`（`App` + `ActionDialog` の組み立て方の手本）

## 含まない

- 実行経路の変更（**task_01 で完了済み**）
- 正本 `spec_detail/` / `codebase_map.md` の更新 = **task_03**（フェーズ末に昇格）
- 実機目視 = **task_03**
- 座標取得 UI を「1 ボタンで 2 点連続取得」に変える案（暫定仕様 §9・保留）
- ホイール / 押す・離すアクション / 別スレッド化 / macOS 対応 = フェーズのスコープ外

## 確認

実行は `verifier`。python は `..\..\..\.venv\Scripts\python.exe`。

1. `-m compileall -q keyseq main.py tests tests_ui` が clean。
2. `-m unittest tests.test_domain_config -v` が全 pass。
3. `-m unittest tests_ui.test_action_dialog_drag -v` が全 pass。
4. `-m unittest discover -s tests` が全 pass（**task_01 完了時点の 475 から減っていない**こと）。
5. `-m unittest discover -s tests_ui` が全 pass（**438 から減っていない**こと）。
6. `-m tests.smoke_app` が SMOKE OK。
7. **変異検査**（ファイルのコピーで退避 → 編集 → コピーで復元）:
   - `on_ok` のドラッグ OFF 経路で `drag`/`to_x`/`to_y`/`drag_speed` を**常に出力する**ようにすると、
     生成停止を見るテスト（上記 1・3）が失敗する。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は **task_03** でまとめて実施する（本タスクでは行わない）。
