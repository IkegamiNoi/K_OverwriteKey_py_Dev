# 提案書 11: phase 28（ダイアログの初期キーボードフォーカス）後のリファクタ

> `/refactor_check`（`.claude/commands/refactor_check.md`）の判定 = **推奨**。
> **ユーザー承認前に実装しない**。判定の記録は
> [decisions_archive/28](../../.claude_data/state/decisions_archive/28_dialog_keyboard_focus.md)。
> 状態: **承認済**（2026-09-23・ユーザー選択 (a) = phase 28 の **task_07** として実施）。

## 判定の要約

PHASE_BASE = `60372bf`（phase 28 起票コミット）。対象 = `keyseq/` の変更 **11 ファイル・+74 / -29**（`verifier` 実測・HEAD `5d83e49`）。

- **M3 該当（→ 項目 1）**: 「Esc に別用途がある間はそちらを優先し、押しっぱなしでは閉じない」処理が
  **3 ダイアログにそっくり同じ形で 3 箇所**ある:
  `_on_escape`（`action_dialog.py:135` / `trigger_dialog.py:57` / `keymap_edit_dialog.py:58`）+
  `_on_escape_release`（`:144` / `:66` / `:67`）+ `_escape_held` の初期化 + 2 本の bind。
  違いは「記録中 / 取得中か」の判定と停止メソッドの名前だけ。**規則を変えると 3 箇所とも直す必要がある**
  （実例: task_05e の判定順の修正は 3 箇所に同じ変更を入れた）。
- **既知（提案書に入れない）**: 単純な `bind("<Escape>", lambda _e: X.destroy())` の同型 6 件（phase 28 で追加）は
  `current.md`「別タスク化候補」の**同型スケルトンの共通化**が既にカバーしている。
- **M1 / M2 / M4 / M5 / M6 非該当**: M1 = 最大 `action_dialog.py` 428 行（600 未満）/ M2 = 80 行超の関数なし（最大でも十数行）/
  M4 = 全モード列挙の増加なし / M5 = 申し送りコメント 0 件 / M6 = 既存定数と重複する直値なし。

## 項目 0（先行）: 安全網の確認

- **対象領域のカバー**: `tests_ui/test_dialog_escape_binding.py`（群 A の通常時 Escape / 記録・取得中の停止 → 2 回目で閉じる /
  **押しっぱなしで閉じない** / **印が残ったままの再開で停止する** / フック停止の解除回数）。task_05e で**変異検査 2 種
  （印の分岐除去・判定順の逆転）がそれぞれ赤になる**ことを確認済み。静的検査 `tests_ui/test_nested_modal_grab.py`
  （`__init__` の最後の文が `grab_modal`）。
- テストは `_on_escape` / `_escape_held` を直接参照していない（`grep` 実測 0 件）ため、内部の置き換えでテストを変える必要はない見込み。
- **確認手順**: 変更前に下記「完了条件」のコマンドを実行し全 pass を記録する。**特性テストの追加は不要の見込み**。

## 項目 1: Esc の別用途つき閉じ処理を 1 か所へ寄せる

- **ID**: R11-1
- **対象**: `keyseq/presentation/dialogs/action_dialog.py:30,131-145` / `trigger_dialog.py:24,53-67` / `keymap_edit_dialog.py:24,54-68`
- **何が問題か（M3）**: 上記「判定の要約」のとおり。規範（暫定仕様 22 §3.6 / §3.6.1 → 正本 `features.md` §4.6）が 1 つなのに、
  実装が 3 か所に複製されている。
- **どう変えるか**: `grab_modal` と同じく**クロージャに状態を持つ関数**を 1 つ作り、3 ダイアログはそれを呼ぶだけにする。
  置き場所 = `keyseq/presentation/dialogs/escape_close.py`（利用は `dialogs/` の 3 クラスのみ = Feature Shared。
  `file_organization_rules.md` の「レイヤフォルダ直下」。雑多名を避け内容名にする）。

  変更前（3 ファイルに同じ形）:
  ```python
  self._escape_held = False
  ...
  self.bind("<Escape>", self._on_escape)
  self.bind("<KeyRelease-Escape>", self._on_escape_release)
  grab_modal(self, parent, focus=self.key_entry)

  def _on_escape(self, _event):
      if getattr(self, "_capturing", False):
          self._stop_capture()
          self._escape_held = True
          return "break"
      if self._escape_held:
          return "break"
      self.destroy()

  def _on_escape_release(self, _event):
      self._escape_held = False
  ```
  変更後:
  ```python
  # escape_close.py
  def bind_escape_close(window, *, is_busy, stop):
      """Escape で閉じる。is_busy() の間は stop() を優先し、その Esc を離すまでは閉じない。"""
      held = False
      def on_escape(_event):
          nonlocal held
          if is_busy():
              stop()
              held = True
              return "break"
          if held:
              return "break"
          window.destroy()
      def on_release(_event):
          nonlocal held
          held = False
      window.bind("<Escape>", on_escape)
      window.bind("<KeyRelease-Escape>", on_release)

  # 各ダイアログ
  bind_escape_close(self, is_busy=lambda: getattr(self, "_capturing", False), stop=self._stop_capture)
  grab_modal(self, parent, focus=self.key_entry)
  ```
- **完了条件**: `..\..\..\.venv\Scripts\python.exe` で
  `-m compileall -q keyseq` clean / `-m unittest tests_ui.test_dialog_escape_binding -v` 全 pass /
  **変異検査**（`escape_close.py` の `if held` 分岐を外す → 押しっぱなしのテストが赤・判定順を逆にする → 再開のテストが赤）/
  `-m unittest tests_ui.test_nested_modal_grab` pass / `-m unittest discover -s tests` 556 OK（skipped 7）/
  `-m unittest discover -s tests_ui` 509 OK / `-m tests.smoke_app` SMOKE OK。
  **挙動不変**（`git diff` は 3 ダイアログの置き換えと新規 1 ファイルのみ）。
- **リスクと戻し方**: 低。変更は presentation の 3 ダイアログと新規 1 ファイルに閉じる。問題があれば 1 コミットを revert する。
  注意点 = `__init__` の最後の文が `grab_modal(...)` のまま（静的検査）/ `_stop_recording` / `_stop_capture` は変更しない。
- **依存**: 項目 0。

## 実施タイミング（ユーザー選択）

(a) phase 28 の追加タスク（`task_07_refactor`）として実施 / (b) 次フェーズ前の独立ミニフェーズ / (c) 見送り（別タスク化候補へ）。
