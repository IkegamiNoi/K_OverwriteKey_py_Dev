# task_05_refactor

## 目的

提案書 30（`instructions/modified_proposal/30_refactor_layout_key_symbols.md`）の項目 1 を実施する。一時メッセージ欄に出す文言を決める規則（一時メッセージがあればそれ、無ければ下敷き）を、`App` の 1 つの補助にまとめる。
**presentation の `app.py` 限定・挙動不変**（欄に出る文言・4 秒で消える / 消えないの動き・`_flash_message` の意味・ツールチップの追従は変えない）。

## 対象範囲（`keyseq/presentation/app.py` 限定）

- 補助 `_show_flash_area(self) -> None` を足す: `self._write_status_bar_text(self.ui_vars.flash_message_var, self.ui_vars.flash_message_full_var, self._flash_message or self._flash_underlay)`。
- 次の 4 か所の欄への書き込みを、この補助の呼び出しに置き換える（状態〔`_flash_message` / `_flash_underlay` / `_flash_after_id`〕を変える処理の並びは今のまま）:
  - `_refresh_status_bar`（`_update_file_status()` の後）
  - `set_flash_underlay`（**今と同じく `_flash_message` が空のときだけ**欄を書く。条件を残したまま中身を補助の呼び出しにする）
  - `_clear_flash_message`
  - `_set_flash_message`（`after` の予約の前）
- ほかの箇所・ほかのファイルは変えない。テストの追加・変更はしない（項目 0: 既存の `tests/test_app_control_sync.py` の下敷きのテスト 6 件が安全網）。

## 読むファイル

- 提案書 30（全体）
- `keyseq/presentation/app.py:515-562`

## 含まない

- `hook_controller.py` の `_flash_message` の読み方・一時メッセージを出す呼び出し元の変更
- idea_73（L1〜L4）の内容

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq`
- `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_app_control_sync` が pass
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` が全 pass
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` が全 pass
- `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` が pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。実機目視は無し（挙動不変）。
