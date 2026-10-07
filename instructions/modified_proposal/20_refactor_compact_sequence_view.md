# 提案書 20: phase 48（省略表示の出力シーケンス欄）後のリファクタ

> 状態: **実施済**（2026-10-07・phase 48 task_07_refactor。`call_view_controller.py` の `host.key == "compact"` 7 → 0〔`_FullCallViewLayout` / `_CompactCallViewLayout`〕・`WINDOW_SIZE_SAVE_DELAY_MS` を共有）。

## 判定の要約

範囲 `git diff 9002ec5..HEAD -- keyseq/`（14 ファイル・+692 / -49）。メトリクスは verifier の実測、M4・M6 はメインで裏取り済み。

- **M4 該当**: `controllers/call_view_controller.py` の `host.key == "compact"` の分岐が 2 → 7 に増えた（:77・:89・:104・:155・:194。省略表示の配置を `CompactPaneLayout` へ委ねるための分岐。置き場が増えるたびに全箇所を直す形）
- **M6 該当**: `controllers/compact_window_controller.py:107` の `after(500, …)` が `pane_layout/pane_layout_controller.py:20` の `WINDOW_WIDTH_SAVE_DELAY_MS = 500` と同値（正本でも「フル表示の幅の保存と同じ作法」）
- M1（600 行超で +100 以上なし。`app.py` 657 行 +17・`trigger_panel_controller.py` 639 行 +6）・M2（80 行超の新規関数なし）・M3（遅延保存は 2 箇所で 3 個目なし）・M5（0 件）: 非該当

## 項目 0: 安全網の確認

- 対象領域のテスト: `tests_ui/test_call_view_compact.py`・`test_call_view_frame.py`・`test_compact_sequence_view.py`・`test_compact_window.py`・`tests/test_call_view_heights.py`
- 完了条件: 着手前に `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` / `-s tests_ui` / `-m tests.smoke_app` が全 pass（基準線）

## 項目 1: `CallViewController` の省略表示の分岐を、置き場の配置役へまとめる（M4）

- 対象: `call_view_controller.py:77-90, 103-106, 154-156, 193-195`
- 変更: `_CallViewHost` に配置役（`layout`）を持たせ、分岐を置き場の側へ寄せる。フル表示は今の `_set_minimums` / `_schedule_layout` / `on_font_changed` の処理、省略表示は `CompactPaneLayout` の `schedule_layout` / `on_font_changed` を呼ぶ
  ```python
  # 変更前
  def _schedule_layout(self, host):
      if host.key == "compact":
          self.app.compact_pane_layout.schedule_layout()
          return
      ...
  # 変更後（例）
  def _schedule_layout(self, host):
      host.layout.schedule_layout()   # full = _FullHostLayout(self, host) / compact = app.compact_pane_layout
  ```
  イベントの bind（:77）・既定の高さの決め方（:155 の minsize・`_ensure_desired` の呼び分け）も同じ配置役のメソッドへ移す。`hosts["compact"]` を読む `compact_pane_layout.py` 側の口は変えない
- 完了条件: `grep -c 'host.key == "compact"' call_view_controller.py` が 0〜1・項目 0 が全 pass
- リスクと戻し方: 配置の順序（`_render_host` で欄を足した後に配置を予約する順）が変わると、Tk が要求の高さへ戻す不具合（phase 48 task_05a）が再発し得る。順序を変えず呼び先だけ差し替える。戻しは差し替えの取り消しのみ
- 依存: 項目 0

## 項目 2: 省略表示のサイズ保存の待ち時間を既存定数で共有する（M6）

- 対象: `compact_window_controller.py:107`
- 変更: `WINDOW_WIDTH_SAVE_DELAY_MS` を `WINDOW_SIZE_SAVE_DELAY_MS` へ改名して両方から使う（定義は `pane_layout_controller.py:20` のまま・import して参照）。挙動不変（500ms）
- 完了条件: `grep -rn "after(500" keyseq/presentation/controllers` が 0 件・項目 0 が全 pass
- リスクと戻し方: 改名でテストの参照があれば追随（`grep -rn WINDOW_WIDTH_SAVE_DELAY_MS tests tests_ui`）。戻しは改名の取り消し
- 依存: 項目 0
