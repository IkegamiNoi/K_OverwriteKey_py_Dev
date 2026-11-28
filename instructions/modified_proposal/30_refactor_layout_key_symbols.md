# 提案書 30: phase 84 のリファクタ（一時メッセージ欄の書き込みの一本化）

> 状態: **実施済（2026-11-26・phase 84 task_05_refactor・ユーザー承認「phase 84 の末尾で」）**。起票元 = phase 84 task_05 の `/refactor_check`（PHASE_BASE = 7dc202ff・対象 = keyseq の変更 10 ファイル）。挙動不変。

## 判定の根拠

- M1・M2・M4・M5・M6: 該当なし。
- **M3（境界）**: 「一時メッセージがあればそれ、無ければ下敷き」の規則を、`App` の 3 か所で別々に書いている。規則を変えるときは 3 か所とも直す必要がある。境界の事例なので補助の判断材料を当てた。`app.py`（989 行）は異なる責務のまとまりが 3 つ以上あるため、「推奨」とした。

## 項目 0: 安全網の確認

- 既存のテストで足りる: `tests/test_app_control_sync.py` の下敷きのテスト 6 件（task_03）は、次の動きを確かめている。
  - 下敷きだけのとき
  - 一時メッセージを優先するとき
  - 自動で消えたあと・空の文言で置き換えたあとに下敷きへ戻るとき
  - 一時メッセージの最中に下敷きを変えたとき
  - 消えない一時メッセージのとき
  - ステータスを描き直すとき
- 一時メッセージの既存のテスト（`tests_ui` の各フロー）もそのまま通ること。追加のテストは要らない。

## 項目 1: 一時メッセージ欄の書き込みを 1 つの補助にまとめる

- **対象**: `keyseq/presentation/app.py` の 4 か所
  - `_refresh_status_bar`（:524-526）
  - `set_flash_underlay`（:540-543）
  - `_clear_flash_message`（:545-548）
  - `_set_flash_message`（:550-558）
- **何が問題か（M3）**: 欄に出す文言を決める規則（`self._flash_message or self._flash_underlay`）と、`_write_status_bar_text(self.ui_vars.flash_message_var, self.ui_vars.flash_message_full_var, ...)` の呼び出しが 4 か所に書き写されている。
- **どう変えるか**:
  ```python
  # 変更後（例）
  def _show_flash_area(self) -> None:
      """一時メッセージがあればそれ、無ければ下敷きを欄に出す。"""
      self._write_status_bar_text(
          self.ui_vars.flash_message_var, self.ui_vars.flash_message_full_var,
          self._flash_message or self._flash_underlay,
      )
  ```
  - 4 か所はそれぞれ状態（`_flash_message` / `_flash_underlay`）を変えたあと、`self._show_flash_area()` を呼ぶだけにする。
  - `set_flash_underlay` は今の「一時メッセージがあれば欄を変えない」を保つ。一時メッセージがあれば、補助を呼んでも同じ文言を書き直すだけで、見た目は変わらない。
- **完了条件**:
  - `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_app_control_sync` が pass
  - `-m unittest discover -s tests` が全 pass
  - `-m unittest discover -s tests_ui` が全 pass
  - `-m tests.smoke_app` が pass
- **リスクと戻し方**:
  - リスク: `set_flash_underlay` で一時メッセージが出ている最中にも欄を書き直す（同じ文言）。ツールチップの追従（`full_var` の trace）が 1 回余計に走る。見た目は変わらない。気になるなら、補助を呼ぶ前に今と同じ判定を残す。
  - 戻し方: 1 コミットの revert。
- **依存**: なし（phase 84 の task_03 の後）。

## 実施のタイミング（ユーザー選択）

- (a) phase 84 の末尾の追加タスク（`task_05_refactor`）
- (b) 次フェーズの前の独立ミニフェーズ
