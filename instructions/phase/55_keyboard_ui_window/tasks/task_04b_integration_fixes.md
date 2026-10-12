# task_04b_integration_fixes

## 目的

task_04（統合確認）の deep-reviewer + codex-reviewer の指摘のうち、実装の修正が要るものを直す（暫定 39 v0.6 §4・§5）。
1. grab 中も一時解除を続ける（§4・ユーザー確定）
2. 比率の当て直しで大きさが変わらないときに「自分が当てた大きさ」の印を立てない（§5・Codex P2）
3. 比率の当て直しの前に補正の予約を取り消す（§5・deep 指摘 4）
4. 最大化 / 最小化中に保留した比率の当て直しを、通常へ戻った最初の Configure または `<Map>` を契機に、約 150ms 後の予約でマウスのボタンの判定を通して行う（§5・deep 指摘 2）
**presentation 限定（`keyboard_window.py`・`controllers/layout_controller.py`）。infrastructure / domain / application 不変・スキーマ不変。**

## 対象範囲

### `keyseq/presentation/controllers/layout_controller.py`（`_watch_topmost_tick`）

- 一時解除の判定を `is_dialog or has_grab` にする。`has_grab` = `self._app.grab_current()` が None でない（例外は False 扱い）
- ダイアログの直下へ置く呼び出し（task_03b）は従来どおり「一時解除に**入った** tick で、かつ `is_dialog` が真」のときだけ（grab だけで入ったときは置かない）

### `keyseq/presentation/keyboard_window.py`

- `_apply_ratio_to_base`:
  - 冒頭で `self._cancel_resize_job()`
  - `geometry` を当てる前に今の大きさ（`winfo_width()` / `winfo_height()`）を取り、目標と**違うときだけ** `geometry` を当てて `_applied_size = target` にする。同じなら `geometry` を当てず `_applied_size` を変えない。`_size_base = target` はどちらでも行う。`minsize` は従来どおり当てる
  - 未マップ（`winfo_width()` が 1 以下）のときは「違う」と扱ってよい（初回の Configure で印が消費される）
- 保留した比率の当て直し:
  - `_on_window_configure` の `_suspended` 復帰の分岐で `_apply_ratio_to_base()` を直接呼ぶのをやめ、`_schedule_pending_ratio()` を呼ぶ
  - `self.bind("<Map>", self._on_window_map, add="+")` を追加。`event.widget is self` かつ `_ratio_pending` かつ state が normal のとき `_schedule_pending_ratio()`（`_suspended` も False にし、`_size_base` は `winfo` の今の大きさで取り直す）
  - `_schedule_pending_ratio()`: 補正の予約を取り消して `after(RESIZE_SETTLE_MS, self._apply_pending_ratio)` を 1 件置く（`_resize_job` を共用してよい）
  - `_apply_pending_ratio()`: 予約を消し、マウスのボタンが押されていれば同じ間隔で置き直して戻る（`_settle_size` と同じ判定・例外は False 扱い）。zoomed / iconic なら何もしない。それ以外は `_ratio_pending = False` にして `_apply_ratio_to_base()`

### テスト

- `tests_ui/test_app_ui_flows.py`（既存のキーボードUIテストの近く・後始末を守る）:
  - grab: `foreground_own_window` がメインの HWND を返す差し替え + `app.grab_current` を非 None を返す差し替えで tick → 一時解除（`attributes("-topmost")` が偽）かつ `place_window_below` は呼ばれない / grab が None に戻ると手前に戻る
  - 比率の当て直しで今の大きさが目標と同じとき `geometry` が呼ばれず `_applied_size` が None のまま（`winfo_width` / `winfo_height` を差し替え）
  - `_apply_ratio_to_base` が補正の予約を取り消す
  - 保留: `_ratio_pending` を立てた状態で `_apply_pending_ratio` を、マウス押下の差し替えで呼ぶと置き直され geometry が呼ばれない・未押下なら当たり `_ratio_pending` が False になる

### 設計メモ / 制約

- それ以外の補正規則・前面化の規則は変えない
- 余計な整形変更・BOM / 改行コードの変更をしない

## 読むファイル

- `instructions/history/39_keyboard_ui_window.md` §4「ダイアログ表示中の一時解除」・§5
- `keyseq/presentation/keyboard_window.py`（全体・編集対象）
- `keyseq/presentation/controllers/layout_controller.py:60-160`
- `tests_ui/test_app_ui_flows.py` のキーボードUIのテスト群（`test_keyboard_window_` で始まるもの）

## 含まない

- 正本・codebase_map・phase.md の記述更新（task_05）
- 重複コードの整理・定数化（`/refactor_check` の判断へ）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` 全 pass
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` 全 pass
- `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は軽く行う（ユーザー）: 独自ダイアログ（トリガー追加）を開いたままメイン / キーボードUIをクリックしても、キーボードUIがダイアログを覆わない。リサイズ・レイアウト切替が従来どおり。
