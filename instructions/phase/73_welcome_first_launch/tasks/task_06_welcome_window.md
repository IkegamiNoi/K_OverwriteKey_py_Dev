# task_06_welcome_window

## 目的

初回の起動で出す Welcome の窓を作り、task_05 の差し替え口 `run_first_launch_welcome` をこの窓に替える（暫定 56 v0.5 §4）。
**presentation 限定（`presentation/welcome/` の窓とその呼び出し）+ 言語ファイル・application / domain 不変・JSON スキーマ不変**。

## 対象範囲（presentation 限定）

### 新規 `keyseq/presentation/welcome/welcome_window.py`

- `WelcomeWindow(tk.Toplevel)`: 1 枚の窓。上から:
  1. **Language**（項目名は全言語共通の固定文字列 `Language`・phase 72 と同じ）: `available_languages()` の自称名の選択（Combobox または Radiobutton）。初期値 = 渡された言語。
     変えたら**その場で窓の文言をすべてその言語で作り直す**（窓は閉じない）。全体の言語（`set_language`）はこの窓では呼ばない（結果として返す・呼び出し側が設定する）
  2. **キーボード配列**: US TKL / JIS の 2 択。初期値 = `estimate_layout_id(<言語>)`。言語を変えたとき、利用者が配列を**まだ触っていなければ**推定値へ追従、触った後は追従しない
  3. **基本的な使い方**（3 行・番号付き。文言は下の表）
  4. **始め方**: 「サンプル入りで始める」（既定）/「空で始める」の 2 択 + サンプルの説明（文言は下の表）
  5. ボタン: 「ヘルプを開く」/「はじめる」
- 文言は **`tr_in(<窓の今の言語>, key)`** で引く（窓の中の言語の切り替えに使う。言語ファイルのキーは `welcome.` で始める）
- 閉じ方: 「はじめる」・×・Esc はどれも「その時点の選択で確定」（`features.md` §4.6 モーダルの作法で Esc = ×）
- 結果: 閉じた後に `WelcomeResult(language, layout_id, start)` を返せる（プロパティまたはメソッド）
- 「ヘルプを開く」: **Welcome を親としてヘルプの窓（`HelpWindow`）を直接作る**（初回はヘルプの窓口 `HelpWindowController` がまだ無い・`app.ui_vars` / `app.hook` も無いため）。
  フックの停止・再開は不要（何もしない関数を渡す）。既に開いていれば前に出す。**Welcome を閉じたらヘルプも閉じる**。開くタブは「使い方」のタブ（ヘルプの既存のタブの id を確かめて使う）。
  ヘルプ本文の言語はヘルプの既存の読み方（今の全体の言語）に従う（窓の中で言語を変えた直後でも、全体の言語はまだ変わっていないことを受容）
- 窓の作法: `keyseq/presentation/modal.py` の `grab_modal` でモーダルにする。**親（Tk ルート）は `withdraw` 中なので `transient` を親へ設定しない**（設定すると窓が見えなくなる）。
  画面の中央に出す・大きさは中身に合わせる（最小幅を決めてよい）・テーマは既存のもの（ttk）

### `keyseq/presentation/welcome/first_launch.py`

- `run_first_launch_welcome(app) -> WelcomeResult`: `WelcomeWindow(app, language=current_language())` を作り、`app.wait_window(window)` で閉じるまで待って結果を返す（差し替え口の docstring を本実装の説明に直す）

### 文言（ja の確定案・英語は `ui_terms.md` §2・§3 に従って訳す。いずれも `ja.json` と `en.json` の両方に足す）

| キー（例） | ja |
|---|---|
| 窓の題名 | ようこそ |
| 配列の見出し | キーボード配列 |
| 使い方の見出し | 基本的な使い方 |
| 使い方 1 | 1. 「トリガー」に、押すキーを登録します。 |
| 使い方 2 | 2. 「出力シーケンス」に、そのキーで送る操作を並べます。 |
| 使い方 3 | 3. 「フック開始」を押すと、割り当てが効きます。 |
| 始め方の見出し | 始め方 |
| サンプル入り | サンプル入りで始める |
| 空 | 空で始める |
| サンプルの説明 | 数字キーで 3 つのキーマップ（ショートカット・右手側の文字・テンキー）を切り替えます。まず「フック開始」を押し、メモ帳などで試してください。F1 で一時停止/再開、F12 でフックを止めます。右手側の文字とテンキーでは h で案内を入力します。 |
| ヘルプを開く | ヘルプを開く |
| はじめる | はじめる |

- 「フック開始」「トリガー」「出力シーケンス」は今の画面の表記（言語ファイルの既存の値）と一致させる（違えば既存の表記に合わせて報告）
- 配列の選択肢の表示名は既存の配列の表示名（`US TKL` / `JIS`）

### テスト（tests_ui）

- 窓を作る → 初期値（言語 = 渡した値・配列 = 推定・始め方 = サンプル入り）
- 言語を変える → 窓の文言（題名・見出し・ボタン）がその言語になる・全体の言語は変わらない（`current_language()` 不変）
- 言語を変えたとき配列を触っていなければ追従・触った後は追従しない
- 「はじめる」・×（`WM_DELETE_WINDOW`）・Esc でそれぞれ閉じ、そのときの選択が結果になる
- 「ヘルプを開く」でヘルプの窓が Welcome の子として開き、2 回押しても 1 つ・Welcome を閉じるとヘルプも閉じる
- `run_first_launch_welcome` が窓の結果を返す（窓の操作は `after` で「はじめる」を押す等で自動化）
- task_05 の tests_ui（`test_first_launch_flow.py`）は `run_first_launch_welcome` を patch しているので通ること

### 設計メモ / 制約

- 窓のファイルは 300 行以内目安。長くなるなら文言の組み立て（キーの表）を同じフォルダの小さなファイルへ分けてよい
- ソースに日本語の文言を書かない（静的テスト）。`Language` の固定文字列は phase 72 のメニューと同じ扱い（既存の書き方を確かめる）
- ヘルプからの再表示（始め方と配列を除く・`tr_in`・再起動の知らせ）は task_07。この task では初回の窓だけを作る（再表示のための引数・分岐を先に作らない）

## 読むファイル

- `keyseq/presentation/welcome/`（全体・小さい）
- `keyseq/presentation/modal.py:100-180`（`grab_modal`）
- `keyseq/presentation/help/help_window.py:1-60`（`HelpWindow` の生成の引数）・`keyseq/presentation/help/help_window_controller.py`（全体・小さい）・ヘルプのタブの id（`help_content.py` の該当箇所のみ）
- `keyseq/presentation/views/menu_bar.py:50-70`（`Language` の項目の作り方）
- `keyseq/shared/i18n/catalog.py`（`tr_in` / `available_languages` / `current_language`）
- 手本の窓: 既存の小さなモーダルのダイアログ 1 つ（例 `keyseq/presentation/controllers/config_io/choice_dialog.py`）
- `instructions/common/spec_detail/ui_terms.md` §2・§3・`features.md` §4.6「モーダルダイアログの作法」（該当段落のみ）
- 主入力: `instructions/history/56_welcome_first_launch.md` §4

## 含まない

- ヘルプのメニューからの再表示（task_07）
- 起動の流れ（task_05 で済み）・サンプルの中身（task_03）
- 正本の更新（task_09）

## 確認

- 追加したテストが通る（verifier が `.venv` で実行）
- `python -m compileall -q keyseq`・`python -m unittest discover -s tests`・`python -m unittest discover -s tests_ui`・`python -m tests.smoke_app` が通る

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視（見た目・言語の切り替え・ヘルプ）は task_09 でまとめて実施
