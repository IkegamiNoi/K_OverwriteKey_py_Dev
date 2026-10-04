# task_02a_review_fixes

## 目的

phase 44 の完了判定前レビュー（deep-reviewer 修正して採用 / Codex needs-attention）とユーザー判断（2026-10-04）を受けて、子ファイル保存ダイアログを正本
`features.md`「子ファイル保存ダイアログ」の追記に合わせる: **見出しを常に見える位置へ** / 最小の幅が画面の幅を超えるときの縮め方 / 対象名の上限の単純化 / テストの追加 / 直値の定数化。
**presentation 限定（`controllers/config_io/child_save_dialog.py`・`child_save_columns.py`）・スキーマ不変。**

## 対象範囲

### 見出しを常に見える位置へ（`child_save_dialog.py`・`child_save_columns.py`）

- 見出しの行（文言のラベルと境界の取っ手）をスクロールする content から出し、**一覧（canvas）の上の別の frame** に置く（`list_frame` の行 0 = 見出し / 行 1 = canvas、スクロールバーは canvas の横）
- 見出しの frame と content の列設定（各列の `minsize`・保存先パスだけ `weight=1`）を**同じ値で両方に当てる**。見出しの frame の幅は canvas と同じ幅になるように置く（スクロールバーの分を見出し側で空ける）。
  境界のドラッグ・ウィンドウの幅の変化の後も、見出しと一覧の列の位置が揃うこと
- 見出しの文言は `HEADINGS`（`child_save_columns.py:7`）だけから作る（`child_save_dialog.py:76` の直値をやめる）
- 見出しの省略表示・ツールチップは現行どおり

### 最小の幅が画面の幅を超える場合（`child_save_columns.py`）

- 既定の幅を決めた後、`種別・対象名・共有状況・操作 + 保存先パスの最小幅 + 余白` が画面の幅（`winfo_screenwidth()`）を超えるなら、
  **対象名 → 共有状況 → 種別の順に、各列の最小幅まで既定の幅を縮めて**収める。操作列は縮めない。最小幅まで縮めても収まらなければそのまま（受容）
- `minsize` と `geometry` の幅は同じ幅の計算から出す（`geometry` を画面の幅で頭打ちにして `minsize` がそれより大きい、という状態を作らない）

### 対象名の上限の単純化（`child_save_columns.py:34-40`）

- 対象名の上限 = **960px で開いたときの一覧の幅（960 − 余白 − スクロールバー）の 3 割**。`fixed_width / .7` の循環した計算をやめる（はみ出しは上の縮め方で解く）

### 直値の定数化

- `960` を `child_save_columns.py` の定数（例 `OPENING_WIDTH = 960`）に。`:110`・`:115` の 2 か所とコメントをこれへ
- 余白の `8` は `CELL_GAP` を `child_save_dialog.py` の `padx=(0, CELL_GAP)`（`:84`・`:113`）でも使う（最小幅の計算と同じ値であることをコードで結ぶ）

### テスト（`tests_ui/test_child_save_dialog.py`・追加・修正まで）

- **見出しが常に見える**: 60 行で一番下までスクロールしても、見出しのラベルと取っ手がスクロール領域の外にあり（親が canvas の中の content ではない）、ドラッグできる
- 見出しと一覧の列の位置が揃う: 開いた直後・境界のドラッグの後・ウィンドウを広げた後で、各列の見出しの x 座標と幅が一覧の同じ列と一致する
- **開いた幅**: 最小の幅が 960 未満のとき 960 で開く / 画面の幅が 960 より狭いとき画面の幅で開く（偽のウィジェットの大きさを調整して確かめる）
- **画面より広くなる場合**: 最小の幅が画面の幅を超える条件で、対象名 → 共有状況 → 種別の順に最小幅まで縮み、操作列の幅は変わらず、`minsize` の幅が画面の幅以下になる / 最小幅でも収まらないときは縮めきった幅
- **既定の幅**: 種別・共有状況は内容（見出しを含む）の最大幅で、初期表示では省略されない / 対象名は 960 基準の一覧の幅の 3 割で頭打ち
- 既存のテストは見出しの位置の変更に追随させる（期待値の変更は正本の追記に沿うものに限る）

## 読むファイル

- 正本 `instructions/common/spec_detail/features.md` の「子ファイル保存ダイアログ」節（全文）
- `keyseq/presentation/controllers/config_io/child_save_columns.py`（全体）
- `keyseq/presentation/controllers/config_io/child_save_dialog.py:30-120`
- `tests_ui/test_child_save_dialog.py`（偽のウィジェット `:140-200` 付近と、phase 44 で足したレイアウトのテスト `:500-1180` のうち関係する箇所）

## 含まない

- 記録（decisions_archive・current.md・`/refactor_check` の記録）は task_03
- 表示先のモニタの大きさの取得（主モニタで固定・受容）/ 依存確認・再計算先の上書き確認のダイアログ / 列幅の保存

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest tests_ui.test_child_save_dialog -v` が全 pass
- `-m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- **実機目視（本タスクで実施）**: ①子が多いダイアログで一番下までスクロールしても見出しが見え、境界をドラッグできる ②ドラッグ・ウィンドウの幅の変更の後も見出しと一覧の列がずれない ③（可能なら）大きいフォントで開いても OK / キャンセルが画面内にある。
