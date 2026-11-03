# task_11c_language_menu_restart

## 目的

task_12 の実機目視の後のユーザー判断（2026-11-04・暫定 55 v0.6 §4.3・§5）:
(1) メニューの言語の項目名をどの言語でも「Language」にする / (2) 言語を切り替えた後の知らせから、その場で再起動できるようにする。

## 対象範囲

### (1) 項目名（`keyseq/shared/i18n/locales/ja.json`・`en.json`）

- `menu.settings.language`: ja `言語 / Language` → `Language`・en `Language / 言語` → `Language`
- `tests/test_i18n.py:157` の `japanese_allowed` から `menu.settings.language` を外す（もう日本語を含まない）。
- `tests_ui/test_ui_language.py` の `"言語 / Language"` を `"Language"` へ。

### (2) 再起動（`keyseq/presentation/app.py` の `set_ui_language` ほか）

- 今の `messagebox.showinfo`（と前後の suspend / resume）を `choice_dialog.ask_choice` に置き換える
  （`keyseq/presentation/controllers/config_io/choice_dialog.py`・モジュール経由で呼ぶ。ask_choice は自分でフックを止めるので suspend / resume は外す）。
  - title / message は今と同じキーを `tr_in(code, ...)` で。
  - choices = `[("restart", tr_in(code, "dialog.language_restart.restart_now")), ("later", tr_in(code, "dialog.language_restart.later"))]`・
    `default="restart"`・`cancel="later"`。
  - 新しいキー: ja `今すぐ再起動` / `あとで`・en `Restart now` / `Later`（暫定 55 E1）。
- `restart` を選んだら `App.restart()`（新設）: 再起動の要求の印を立ててから `self.on_close()` を呼ぶ。
  `on_close` が未保存の確認でキャンセルされたら（窓が残ったら）印を戻す。`on_close` の中身は変えない。
- 起動し直しは**終了の後**に行う: `main.py` の `main()` で `app.mainloop()` の後、印が立っていれば起動し直す。
  - 起動し直しの関数は infrastructure の新しいモジュール（例 `keyseq/infrastructure/app_relaunch.py`）:
    `subprocess.Popen([sys.executable, *sys.argv], cwd=<起動時の作業フォルダ>)`。作業フォルダは起動時に記録したもの
    （App を作る前に `os.getcwd()`）。
  - 失敗したら（`OSError` 等）ログに残し、`messagebox.showerror` で理由を出す（窓はもう無いので親なし。文言キーを足す: ja `再起動できませんでした。\n{error}`・en `Could not restart the app.\n{error}`）。
- テスト（tests または tests_ui。`fix_language("ja")` の規則に従う）:
  - `set_ui_language`: `ask_choice` が `restart` を返すと `restart` が呼ばれ、`later` では呼ばれない・ask_choice に渡す文字は選んだ言語（`tr_in`）
  - `restart`: on_close がキャンセルされた（窓が残る）ときは印が戻る
  - 起動し直しの関数: `subprocess.Popen` を patch して、引数（`sys.executable` と `sys.argv`）と `cwd` / 失敗で showerror とログ
  - 既存の C1 のテスト（showinfo の前後で suspend / resume）は新しい形に合わせて置き換える

## 含まない

- `on_close` の終了処理の変更 / 言語の即時反映 / 正本 `spec_detail/` の改訂（task_12）

## 読むファイル

1. 本書・暫定 55 §4.3・§5（`instructions/history/55_multilingual_ui.md`）
2. `keyseq/presentation/app.py`（`set_ui_language`・`on_close`）・`main.py`
3. `keyseq/presentation/controllers/config_io/choice_dialog.py`（呼び方の例は `grep -rn "choice_dialog.ask_choice" keyseq`）
4. `tests_ui/test_ui_language.py`・`tests/test_i18n.py`

## 確認（verifier）

- compileall clean / tests 全件 / tests_ui 全件（単独実行）/ smoke
