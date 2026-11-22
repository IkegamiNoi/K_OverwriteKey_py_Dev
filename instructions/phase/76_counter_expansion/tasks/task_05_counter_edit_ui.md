# task_05_counter_edit_ui

## 目的

カウンターの編集 UI と、開始値を構成セットから実行時へ渡す配線を作る（暫定 58 §5.1・§5.2・§4.1 の差し替え契機）。
①編集ダイアログ: 「カウンター」に増やす量と開始値の欄・名前を変えたら開始値を入れ替える / 種類「カウンターの値を入力」 ②行の追加・置換が成立した時点で開始値を構成セットへ書き未保存にする
③構成セットを置き換えるすべての経路で `AppState` の開始値を同期し、一覧・呼び出し先の表示枠を描き直す ④名称の文言（ja / en）・ヘルプ。
**presentation 限定**（application は task_02 の `AppState.set_counter_starts` を呼ぶだけ・変えない）。保存形式・実行・書式は変えない。

## 対象範囲（presentation 限定）

### `keyseq/presentation/dialogs/action_control_fields.py`

- 「カウンター」（`counter_inc`）のときだけ表示する欄を 2 つ足す（`system_counter_combo` の下の行）:
  - **増やす量**（`amount_var`・整数・既定 `1`）。`load` で `action.get("amount", 1)` をそのまま文字列で入れる（不正な値もそのまま出す）。
  - **開始値**（`start_var`・整数）。
- 開始値の欄の値は、コンストラクタで受け取る `counter_starts: Mapping[str, int]`（既定 `{}`）から引く。**名前の欄（`system_counter_var`）が変わるたびに**（`trace_add("write", ...)`・候補の選択・打鍵のどちらでも）その名前の開始値（無ければ 0）を開始値の欄へ入れ直す。`load` で名前を入れた後も同じ。
- `_build_system_result` の `counter_inc`: 増やす量・開始値を `int(var.get().strip())` で解釈し、どちらかが整数でなければ理由を出して `None`（新しい文言キー `action_dialog.error.amount_integer`「増やす量は整数で入力してください。」/ `action_dialog.error.start_integer`「開始値は整数で入力してください。」・英語は `ui_terms.md` の表記規則に合わせる）。**0 も負も可**。
  結果の行に `amount` を常に書く。**開始値は行に書かず**、属性 `self.counter_start_result: tuple[str, int] | None` に `(OK 時点の名前, 開始値)` を入れる（`counter_inc` 以外で OK したら `None`）。
- 欄のラベルの文言キー（`action_dialog.counter_amount`「増やす量」/ `action_dialog.counter_start`「開始値」と英語）を足す。
- `sync_system` で 2 つの欄を `counter_inc` のときだけ表示する。

### `keyseq/presentation/dialogs/action_dialog.py`

- 種類の候補に `counter_text` を足す（`self._type_labels` と、`mode is None` で隠す `system` / `file_line` と同じ扱いの列）。表示名のキー `action.type.counter_text`（ja「カウンターの値を入力」/ en「Type counter value」・`ui_terms.md` の表）。
- `counter_text` を選んだときは、カウンター名のドロップダウンだけを出す（file_line の `file_counter_combo` と同じ候補。新しい小さな枠を `ActionControlFields` に足すか、既存の枠を流用するかは実装に任せるが、system / file_line の枠の表示の切替〔`_sync_capture_ui`・`_focus_is_hidden_for_type`〕を壊さない）。
  OK 時: 名前が空なら既存の `action_dialog.error.counter_required` で拒否 / 結果 `{"type": "counter_text", "counter": 名前, "label": ラベル}`。`load` で名前を入れる。開いたときの入力先は種類のドロップダウン（値の欄が無いため）。
- コンストラクタに `counter_starts` を足して `ActionControlFields` へ渡す。ダイアログの結果と一緒に `counter_start_result` を呼ぶ側が読めるようにする（例: `parent._dialog_counter_start`。既存の `_dialog_result` と同じ受け渡しの形にそろえる）。

### `keyseq/presentation/controllers/trigger_panel/action_edit.py`

- `add_action` / `edit_action` でダイアログに `counter_starts=self._app.data.get("counter_starts", {})` を渡す。
- **行の追加・置換が成立した後で**（`standalone_violation` 等の拒否を通った後・`mark_sequence_dirty` と同じ所）、ダイアログの `counter_start_result` が `(name, start)` なら:
  今の `self._app.data["counter_starts"]` のその名前の値（無ければ 0）と違うときだけ、`counter_starts` を書き換え（0 なら要素を消す）・`self._app.state.set_counter_starts(...)`・`self._app.dirty_tracker.set_dirty(True)`（構成セットを未保存にする・`App.toggle_select_before_run` と同じ）・一覧と呼び出し先の表示枠を描き直す。
  拒否・キャンセルでは何も変えない。
- `_counter_names` に `self._app.data.get("counter_starts", {})` の名前も足す（`counter_text` の行の名前は既存の `action.get("counter")` で拾える）。

### 構成セットを置き換える経路の同期（`keyseq/presentation/app.py`）

- `App._sync_control_vars_from_data`（起動時の読込・読込・Import・新規作成・サンプル設定に戻すがすべて通る・`select_before_run` の同期と同じ所）で `self.state.set_counter_starts(self.data.get("counter_starts", {}))` を呼ぶ。
  呼ぶ側の経路のうち、この後に一覧・呼び出し先の表示枠を描き直さない経路があれば描き直しを足す（既存の描き直しの関数を使う）。

### 文言（`keyseq/shared/i18n/locales/ja.json`・`en.json` の両方）

- `action_dialog.system.op.counter_inc`: ja「カウンター」/ en「Counter」・`action_dialog.system.op.counter_reset`: ja「カウンターリセット」/ en「Reset counter」（§5.1）。
- 上で足すキー（欄のラベル・エラー 2 つ・種類の表示名）。

### ヘルプ（`keyseq/presentation/help/content/help_ja.json`・`help_en.json`）

- アクションの種類の説明（`help_ja.json:313,315,332` 付近と英語の対応箇所）を直す: 「カウンター+1 / カウンターを0に」→「カウンター / カウンターリセット」、増やす量（負・0 も可）と開始値（構成セットに保存・リセットで戻る）の 1〜2 文、`counter_text`（カウンターの値をそのまま入力）の 1 行を足す。分量は既存の項目と同程度。

### テスト（追加・修正。**テストの実行はしない**）

- `tests_ui/test_action_dialog_control.py`（既存の作り方に合わせる）:
  - 増やす量・開始値の欄が `counter_inc` だけに出る / 既定 1 / 不正な値で OK を拒否 / 0・負で OK できる / 結果に `amount` が入り開始値は入らない・`counter_start_result` が OK 時点の名前と値。
  - 既知の名前を選ぶと開始値の欄がその開始値になり、名前を変えると入れ替わる・未知の名前は 0。
  - 種類 `counter_text` が候補にあり（mode None では出ない）、空名を拒否・結果の形。
- `tests_ui/` の追加・置換のテスト（`action_edit` の既存テストの置き場に合わせる）: 追加が成立したときだけ開始値が書かれ構成セットが未保存になる・`standalone_violation` で拒否されたら開始値は変わらない・同じ値なら未保存にしない・0 にしたら要素が消える。
- `tests/` または `tests_ui/`: `_sync_control_vars_from_data` の後に `state.counters.starts` が構成セットの値になる（読込・新規作成・サンプル設定に戻すで前の開始値が残らない）。
- 文言キーが ja / en の両方にある（既存の静的テストが見るなら追加不要）。ヘルプの JSON の検証テスト（`tests/` の help の検証）が通る形にする。

## 設計メモ / 制約

- 主入力 = 暫定 58 §5.1・§5.2・§4.1（差し替え契機）・§2.2（ダイアログに今の値・上書き可）。
- **ダイアログは構成セットを書き換えない**（結果として返すだけ）。書き換えはコントローラが成立後に行う（§5.2・行は入らないのに開始値だけ変わるのを防ぐ）。
- 画面の文言はソースに日本語を書かず、`ja.json` と `en.json` の両方にキーを足す（静的テスト）。`tr` はモジュール定数・import 時に評価しない。英語は `ui_terms.md` §2・§3（E1〜E7）。
- tests_ui の `App()` を作る新しいテストモジュールは import 直後に `fix_language("ja")`。
- 編集は apply_patch で行い、Python のスクリプトでファイルを書き換えない。互換の工夫・テストの期待値の推測を足さない。既存のテストの途中に新しいテストを差し込まない。

## 読むファイル

- `instructions/history/58_counter_expansion.md` §5.1・§5.2・§4.1（主入力）
- `keyseq/presentation/dialogs/action_control_fields.py`（全体・編集対象）
- `keyseq/presentation/dialogs/action_dialog.py:29-70,150-260,507-605`
- `keyseq/presentation/controllers/trigger_panel/action_edit.py:60-120,189-250,355-372`
- `keyseq/presentation/app.py:785-800,865-872`（`_sync_control_vars_from_data`・`toggle_select_before_run`）
- `keyseq/presentation/controllers/config_io/keymap_set_io.py:80-92,700-712,761-772`（同期を呼ぶ経路）
- `instructions/common/spec_detail/ui_terms.md` §2・§3・「アクションの種類の表示名」
- 手本のテスト: `tests_ui/test_action_dialog_control.py`

## 含まない

- 保存形式・実行・一覧の書式（task_01〜04 で完了）
- 正本 `spec_detail/`（`ui_terms.md` を含む）・`codebase_map.md` の更新（task_07）
- 実機目視（task_06）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests tests_ui` clean
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` 全 pass
- tests_ui は今回足した・直したモジュールを **1 本ずつ**流す（例 `-m unittest tests_ui.test_action_dialog_control`。通しで走らせない・同時に 2 本走らせない）
- `-m tests.smoke_app` OK

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_06 でまとめて実施。
