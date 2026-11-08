# task_07_welcome_reopen

## 目的

ヘルプのメニューから Welcome を再表示できるようにする（暫定 56 v0.5 §7）。再表示の窓は始め方とキーボード配列を除き、今の構成を変えない。
言語を変えて閉じたら、今の言語の切り替えと同じ流れ（保存して「今すぐ再起動 / あとで」）にする。
**presentation 限定（`welcome/`・`menu_bar.py`）+ 言語ファイル・application / domain 不変・JSON スキーマ不変**。

## 対象範囲（presentation 限定）

### `keyseq/presentation/welcome/welcome_window.py`

- 引数 `reopen: bool = False` を足す（キーワード専用）。真のとき:
  - **キーボード配列と始め方の節を出さない**（結果の `layout_id` / `start` は使われない＝初期値のままでよい）
  - 代わりに一文「サンプル設定は、メニュー『ファイル』の『サンプル設定に戻す』で入れられます。」を出す（メニューの名前は言語ファイルの既存の値を差し込む）
  - 「ヘルプを開く」は `app.help.open_for_dialog(self, "guide", "")`（ヘルプの窓口の既存の作法。別の窓の子のヘルプがあれば閉じて開き直す・Welcome を閉じたら子のヘルプも閉じる）。
    初回（`reopen=False`）の今の作り（Welcome を親に `HelpWindow` を直接作る）は変えない
  - `transient(master)` を設定してよい（親は表示中）。初回では今のとおり設定しない
- 窓の中の言語の切り替え（`tr_in`）・確定（はじめる・×・Esc）は初回と同じ。ボタンの「はじめる」は再表示では「閉じる」の文言にする（言語ファイルに足す）

### `keyseq/presentation/welcome/first_launch.py`（または同じフォルダの新しい小さなファイル）

- `open_welcome_again(app) -> None`:
  1. `app.hook.suspend_hook_for_dialog()`（モーダルの作法・`features.md` §4.6）
  2. `WelcomeWindow(app, language=current_language(), reopen=True)` → `app.wait_window(window)`
  3. `app.hook.resume_hook_after_dialog()`（1〜2 で例外が出ても戻す・try / finally）
  4. 結果の言語が今の保存値と違えば `app.set_ui_language(result.language)`（今の言語の切り替え・保存・「今すぐ再起動 / あとで」）。同じなら何もしない
- **全体の言語（`set_language`）は呼ばない**（メイン画面は再起動まで今の言語のまま）

### `keyseq/presentation/views/menu_bar.py`

- ヘルプのメニューの「よくある質問」の後（区切りの前）に「Welcome を表示」を足し、`open_welcome_again(app)` を呼ぶ（項目名は言語ファイルのキー）

### `keyseq/shared/i18n/locales/ja.json` / `en.json`

- 再表示の一文・「閉じる」・メニューの項目名のキーを**両方**に足す（英語は `ui_terms.md` §2・§3。メニューの項目名は ja「Welcome を表示」/ en「Show Welcome」を案とする）

### テスト（tests_ui）

- `reopen=True` の窓に配列と始め方の節が無く、サンプル設定の案内の一文と「閉じる」がある・`reopen=False` は今のまま
- `open_welcome_again`: 窓の言語を変えずに閉じる → `set_ui_language` を呼ばない / 言語を変えて閉じる → `set_ui_language(新しい言語)` を 1 回（`set_ui_language` は patch）・全体の言語は変わらない・フックの停止と再開が 1 回ずつ（例外のときも再開）
- 再表示の「ヘルプを開く」が `app.help.open_for_dialog(window, "guide", "")` を呼ぶ・Welcome を閉じると子のヘルプも閉じる
- メニューのヘルプに項目があり、選ぶと `open_welcome_again` が呼ばれる（呼び出し先を patch）

### 設計メモ / 制約

- 初回の窓の挙動（task_06 のテスト）は変えない
- `welcome_window.py` が 300 行を超えそうなら、文言の組み立てを同じフォルダの小さなファイルへ分ける
- ソースに日本語の文言を書かない

## 読むファイル

- `keyseq/presentation/welcome/`（全体）
- `keyseq/presentation/views/menu_bar.py:55-85`
- `keyseq/presentation/app.py:570-595`（`set_ui_language`）
- `keyseq/presentation/help/help_window_controller.py`（`open_for_dialog`）
- `keyseq/presentation/controllers/hook_controller.py:51-85`（`suspend_hook_for_dialog` / `resume_hook_after_dialog`）
- `keyseq/shared/i18n/locales/ja.json` の `menu.file.*` / `menu.help.*`（該当行のみ）
- 手本のテスト: `tests_ui/test_welcome_window.py`
- 主入力: `instructions/history/56_welcome_first_launch.md` §7

## 含まない

- 初回の窓・起動の流れ（task_05・06 で済み）
- 統合確認・正本の更新（task_08・09）

## 確認

- 追加したテストが通る（verifier が `.venv` で実行）
- `python -m compileall -q keyseq`・`python -m unittest discover -s tests`・`python -m unittest discover -s tests_ui`・`python -m tests.smoke_app` が通る

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視は task_09 でまとめて実施
