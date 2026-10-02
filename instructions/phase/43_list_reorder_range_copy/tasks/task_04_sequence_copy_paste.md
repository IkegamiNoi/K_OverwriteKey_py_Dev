# task_04_sequence_copy_paste

## 目的

出力シーケンス欄に「複製」ボタン（選択範囲を末尾に複製）と Ctrl+C → Ctrl+V（アプリ内の保管庫・別のトリガーのシーケンスへも貼れる）を加える
（暫定 30 §3.4・§4.1・§4.3）。保管庫はトリガー一覧・キーマップ一覧（task_07・task_08）でも使う共通部品として作る。
**presentation 限定（task_01 の `paste_violation` を使う）。domain / application 不変・スキーマ不変。**

## 対象範囲（presentation 限定）

### `keyseq/presentation/list_clipboard.py`（新規）

- 一覧の種類の定数（`CLIP_ACTIONS = "actions"`。トリガー・キーマップの種類は task_07・task_08 で足す）
- `class ListClipboard`: `copy(kind: str, items: Sequence[dict]) -> None`（写しで保持・元の後の編集は影響しない）/
  `paste(kind: str) -> list[dict] | None`（種類が一致すれば保持内容の**新しい写し**を返す。不一致・空なら None）/ `clear() -> None`
- 写しは `keyseq.domain.config.safe_deepcopy` を使う

### `keyseq/presentation/app.py`

- App に保管庫を 1 つ持たせる（例 `self.list_clipboard = ListClipboard()`。生成位置は他のコントローラの生成の近く）

### `keyseq/presentation/controllers/config_io/keymap_set_io.py`

- `new_config` と `apply_loaded_data_to_ui` で保管庫を空にする（§3.4「構成セットの読込・新規作成で空にする」。読込の全経路・起動時の読込は `apply_loaded_data_to_ui` を通る）

### `keyseq/presentation/views/full_view/sequence_box.py`

- 「削除」の直後に「複製」ボタン（`command` は trigger_panel 側）。幅・余白は他のボタンに揃える
- `action_list` に `<Control-c>` / `<Control-C>` / `<Control-v>` / `<Control-V>` をバインドし、ハンドラは `"break"` を返す（Listbox だけ・`bind_all` 不使用）

### `keyseq/presentation/controllers/trigger_panel/`（`action_edit.py` に処理・`trigger_panel_controller.py` は委譲のみ）

- 対象の行: 選択範囲（`listbox_range_drag.selected_range`）。選択が無ければフォーカスのある下線の行（現行の `selected_action_index`）。トリガー未選択・シーケンスが空なら何もしない
- **複製**（ボタン）: 対象の行の写しを末尾へ足す（保管庫は変えない）
- **Ctrl+C**: 対象の行を保管庫へ `CLIP_ACTIONS` で写す（一覧の見た目は変えない）
- **Ctrl+V**: 保管庫の `CLIP_ACTIONS` の写しを、選択中のトリガーのシーケンスの末尾へ足す。保管庫が空・トリガー未選択なら何もしない
- 足す前に `paste_violation(actions, items)` を確認し、理由があれば足さずに `messagebox.showinfo` で示す（文言例:
  `PASTE_UNBALANCED_LOOP` =「ループの始まりと終わりの片方だけは複製 / 貼り付けできません。」/
  `PASTE_TOO_DEEP` =「ループの入れ子が 9 段を超えるため複製 / 貼り付けできません。」（段数は `MAX_LOOP_DEPTH`）/
  `PASTE_STANDALONE` =「戻す・先頭へは、出力シーケンスにそれ 1 つだけで登録してください。」= 現行の追加と同じ文言）
- 足したら: 次に実行は同じアクションのまま（末尾への追加なので位置は変えない。**ただし連続実行の終端〔位置 = 元の長さ〕の場合は、終端の意味を保つため新しい長さにする**）・
  現行の追加と同じく `reset_loop_frames`・未保存化（`mark_sequence_dirty`）・`refresh_actions(select=足した範囲)`（足した行が見えるようにする）
- 共通の「末尾へ足す」処理は 1 つの関数にまとめ、複製と Ctrl+V の両方から使う

### テスト（`tests_ui/`。追加・修正まで）

- 新規 `tests_ui/test_sequence_copy_paste.py`: 複製ボタンで範囲が末尾に複製され選択される・保管庫は変わらない / Ctrl+C → 別のトリガーを選んで Ctrl+V で貼れる /
  コピー後に元を編集しても貼る内容は変わらない・繰り返し貼れる / 片側だけのループ・深さ超過・戻す / 先頭への規則違反は貼らず案内（messagebox を patch）/
  次に実行が同じアクションのまま・連続実行の終端は終端のまま / 新規作成・読込（`apply_loaded_data_to_ui`）で保管庫が空になる / Ctrl+C / V のハンドラが `"break"` を返す
- `tests/` に `ListClipboard` の単体テスト（写しの独立性・種類不一致で None・clear）を新規 `tests/test_list_clipboard.py` で（tkinter 非依存のため）

### 設計メモ / 制約

- `list_clipboard.py` は tkinter を import しない
- 関数 30 行の目安。`trigger_panel_controller.py`（617 行）へは委譲の数行だけを足す

## 読むファイル

- 暫定仕様 §3.4・§4.1・§4.3
- `keyseq/presentation/controllers/trigger_panel/action_edit.py`（全体）
- `keyseq/presentation/views/full_view/sequence_box.py`（全体）
- `keyseq/presentation/listbox_range_drag.py:1-40`（`selected_range` / `select_range`）
- `keyseq/domain/sequence_editing.py`（`paste_violation` と定数）
- `keyseq/presentation/controllers/config_io/keymap_set_io.py:54-75`・`:683-700`
- `keyseq/presentation/app.py:190-215`（コントローラの生成）
- 既存の sequence 欄のテストの作り方: `tests_ui/test_sequence_list_operations.py:1-60`

## 含まない

- トリガー一覧・キーマップ一覧の Ctrl+C / V と種類の定数（task_07・task_08）/ ラベルの連番（出力シーケンスの行には付けない・§7）
- グレーのトリガーの扱い（task_05）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest tests.test_list_clipboard tests_ui.test_sequence_copy_paste` が全 pass
- `-m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- **実機目視（本タスクで実施）**: 複製ボタン / Ctrl+C → Ctrl+V（同じトリガー・別のトリガー）/ 貼れない場合の案内 / 入力欄（間隔(ms)）の Ctrl+C / V が通常どおり働く。
