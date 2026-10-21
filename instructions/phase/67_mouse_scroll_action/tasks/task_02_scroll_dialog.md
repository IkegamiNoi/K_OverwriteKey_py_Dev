# task_02_scroll_dialog

## 目的

暫定 50 v0.4 §5 のアクションのダイアログの mouse_scroll の欄と、§6 の「次に実行」の要約を作る。
**presentation 限定（新規 `action_mouse_scroll_fields.py` + `action_dialog.py` + `action_list_rendering.py`）・domain / application / infrastructure は不変（task_01 の `keyseq/domain/mouse_scroll.py` を使うだけ）・スキーマ不変。**

## 対象範囲（presentation 限定）

### 新規 `keyseq/presentation/dialogs/action_mouse_scroll_fields.py`: `ActionMouseScrollFields`（`action_key_hold_fields.py` と同じ形）

- コンストラクタ `(parent, *, capture_mouse_position: Callable)`。`self.frame = ttk.LabelFrame(parent, text="マウススクロール", padding=8)`
- 欄:
  - **向き**: 読み取り専用の Combobox（上 / 下 / 左 / 右・既定 下）。表示名 ↔ `up` / `down` / `left` / `right`
  - **量**: ラジオボタン「ノッチ数」「生の値（120 = 1 ノッチ）」（`unit_var`・値 `notch` / `delta`・既定 `notch`）と、それぞれの Entry（既定 `"1"` / `"120"`）。**選んだ方の Entry だけ `normal`・他方は `disabled`**（値は残す）。**どちらも選ばれていない状態**（`unit_var` = `""`）では両方 `normal`
  - **「座標を指定する」チェック + X / Y の Entry + 「座標を取得」ボタン + 案内のラベル**（文言は key_hold と同じ）。チェックが外れていれば X / Y の Entry と取得ボタンは `disabled`（**非表示にしない**・暫定 50 §5）。取得ボタンは `capture_mouse_position(x_var, y_var, capture_button, capture_hint)` を呼ぶ
- `load(action)`（暫定 50 §5「既存の行を開いたとき」）:
  - 単位: `unit` のキーが無い・文字列で trim 後が空・`notch`（大小無視）→ `notch` / `delta` → `delta` / それ以外 → `""`（未選択）
  - 量: `amount` が §3 で有効（`mouse_scroll` モジュールの量の解析を使ってよい・必要なら domain に公開関数が既にあるか確認し、無ければ `parse_mouse_scroll` の結果の `amount` を使う。**domain は変更しない**）なら整数の文字。無効なら `""` でなければ `str(元の値)`（キー無しは既定値のまま）。単位が notch → ノッチの欄 / delta → 生の値の欄 / 未選択 → 両方の欄。選ばなかった方の欄は既定値
  - 向き: 4 つ以外（非文字列を含む）→ 下
  - 座標: `x` / `y` のどちらかのキーがあればチェック ON。値は有効な整数ならその文字・それ以外は `str(元の値)`（無ければ空）
- `build_action(label) -> dict`: `{"type": "mouse_scroll", "direction": …, "unit": unit_var, "amount": <選んだ欄の文字>, "label": label}`。チェック ON なら `x` / `y` に欄の文字。単位が未選択なら `unit` を `""` で入れる（OK 側で拒否）
- `stop_capture` 等は不要（座標の取得の停止は既存の仕組みに無い）

### `keyseq/presentation/dialogs/action_dialog.py`

- 種類の候補に `mouse_scroll` を `mouse_click` の直後へ加える（すべての文脈）
- `ActionMouseScrollFields` を作り、key_hold の欄と同じ行の並び（重ならない row）に grid → `grid_remove`。`_sync_capture_ui` で `t == "mouse_scroll"` のときだけ表示
- `initial` の type が `mouse_scroll` なら `load(initial)`
- `on_ok`: 種類の検査に `mouse_scroll` を加える。`mouse_scroll` のとき:
  1. 単位が未選択 → `messagebox.showerror("入力エラー", "単位を選んでください。")` で戻る
  2. チェック ON で X / Y のどちらかが空 → 「マウス座標の X/Y は両方入力してください。」で戻る
  3. `build_action` の結果を `parse_mouse_scroll` で検査 → 文字列なら `showerror("入力エラー", 理由)` で戻る
  4. 成功 → `{"type": "mouse_scroll", "direction": spec.direction, "unit": spec.unit, "amount": spec.amount, "label": label}` + 座標があれば `x` / `y`（整数）を `_dialog_result` に
- `_set_mouse_capture_state`: 新しい取得ボタンも同じ state にする。**ただしチェックが外れている間は取得の終了（`normal` へ戻す）で有効にしない**（欄の `sync` を呼び直す等で、チェックの状態に合わせる）
- `_focus_is_hidden_for_type`: `action_type != "mouse_scroll"` のとき新しい欄のウィジェット（向きの Combobox・2 つのラジオ・2 つの Entry・チェック・X / Y の Entry・取得ボタン）を隠れる側に加える
- `_initial_focus_widget`: 変更しない（mouse_scroll は種類のドロップダウン・暫定 50 §5）

### `keyseq/presentation/controllers/action_list_rendering.py`

- `format_next_action_summary` の `("system", "file_line", "key_hold")` に `mouse_scroll` を加える（`format_action_list_item` と同じ書式）
- フル表示の一覧・省略表示のシーケンス欄・呼び出し先の表示枠が `format_action_list_item` を通ることを確認し、通らない経路があれば報告する（直さない）

### テスト（tests_ui）

- 新規 `tests_ui/test_action_dialog_mouse_scroll.py`（手本 `test_action_dialog_key_hold.py`）: 種類の候補 / 表示の切替（mouse_scroll だけ表示）/ 単位の切替で Entry の state / 未選択で両方 normal / 座標のチェックで X / Y と取得ボタンの state / load（notch・delta・単位なし・不正な単位 → 未選択・`amount: 3.0` → `"3"`・`"3"` → `"3"`・不正な量の原文・不正な向き → 下・座標）/ OK（正常の保存形・座標あり / なし・未選択で拒否・範囲外で拒否・`3.0` の行をラベルだけ変えて `3` で保存・X/Y 片方で拒否）/ 隠れる欄のフォーカスで種類のドロップダウンへ / 開いたときの入力先が種類のドロップダウン
- `tests_ui/test_action_list_rendering.py`: 「次に実行」の要約に mouse_scroll（ノッチ・生の値・座標・不正）

## 読むファイル

1. `instructions/history/50_mouse_scroll_action.md`（§5・§6）
2. `keyseq/domain/mouse_scroll.py`（task_01 で作成・全体）
3. `keyseq/presentation/dialogs/action_dialog.py`（全体）
4. `keyseq/presentation/dialogs/action_key_hold_fields.py:1-170`（手本）
5. `keyseq/presentation/controllers/action_list_rendering.py`（全体）
6. `tests_ui/test_action_dialog_key_hold.py`（手本・必要な範囲）

## 含まない

- domain / application / infrastructure の変更（task_01 済み）
- 正本・codebase_map の更新・実機目視（task_03）

## 確認

- `compileall` clean / `unittest discover -s tests` 全 pass / `unittest discover -s tests_ui` 全 pass（新規分を含む）/ `-m tests.smoke_app` pass
- 差分の直読み: 既存の種類（hotkey / text / mouse_click / key_hold / system / file_line）の欄・検査・保存形が不変 / presentation 以外の変更なし

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視は task_03 でまとめて実施
