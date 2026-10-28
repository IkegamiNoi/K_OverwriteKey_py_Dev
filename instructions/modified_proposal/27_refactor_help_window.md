# 提案書 27: phase 70（ヘルプの作成）後のリファクタ

> 状態: **ユーザー判断待ち**（2026-10-29 起票）。

## 判定の要約

範囲 `git diff 7b7e62a..HEAD -- keyseq/ main.py`（新規 `presentation/help/` 12 ファイル + 既存 26 ファイル）。メトリクスは verifier の実測、M3 はメインで `app.py` を直読みして裏取り。

- **M3 該当**: `presentation/app.py` に「呼んで、例外ならログに残して続ける」同型の try/except が phase 70 で 5 個増えた（`_apply_always_on_top` の :625-636 に 3 個・終了処理の :792-799 に 2 個）。同じ形は既存にも `shutdown_capture_hook`（:782-785）・`delayed_calls.stop`（:802-805）があり、コピーの 3 個目以降に当たる
- 参考（判定には使わない）: `add_help_button` の 12 か所の呼び出しは共通の関数経由で同型ブロックではない / `help_content.py` の `_parse_*` の検証の `raise` の繰り返しは新規の検証で、コピーではない
- 非該当: M1（600 行超は `app.py` 829 行のみで +25）/ M2（80 行超の関数の新規発生なし）/ M4（増加なし）/ M5（0 件）/ M6（同値の直値なし）

## 項目 0: 安全網の確認

- 対象領域のテスト: `tests_ui/test_help_window.py`（topmost の追従・終了で閉じる）・`tests_ui/test_app_ime_shutdown.py`・`tests_ui/test_app_ui_flows.py`（終了処理）
- 完了条件: 着手前に `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` / `-s tests_ui` / `-m tests.smoke_app` が全 pass（基準線）

## 項目 1: 「呼んで失敗をログに残す」を 1 つの関数に（M3）

- 対象: `keyseq/presentation/app.py:625-636`・`:792-799`（phase 70 で足した 5 個のみ。既存の 2 個はフェーズ外のため対象外）
- 変え方: `app.py` のモジュールに私的な関数を置き、5 個をその呼び出しにする

  ```python
  def _call_logged(func: Callable[[], object], message: str) -> None:
      try:
          func()
      except Exception:
          logging.getLogger(__name__).exception(message)

  # 変更後（_apply_always_on_top）
  _call_logged(self.help.apply_topmost, "Could not apply help window topmost")
  _call_logged(self.license.apply_topmost, "Could not apply license window topmost")
  _call_logged(self.layout.resync_keyboard_topmost, "Could not resync keyboard window topmost")
  ```
- 完了条件: 5 個の try/except が消え、ログの文言は不変・上記の既存テストが pass
- リスクと戻し方: 低（局所的な置き換え・挙動とログの文言は不変）。テストが落ちたらコミットを戻す
- 依存: なし

## 備考

- 実施タイミングはユーザー判断: (a) phase 70 の追加タスク `task_09_refactor` / (b) 次フェーズ前の独立ミニフェーズ / (c) 保留
- 既存の同型 2 個（:782-785・:802-805）を同じ関数へ寄せるのは、実施時にユーザーが望めば同じタスクで足してよい（フェーズ外のため本提案の項目には含めない）
