# task_09_save_dialog_layout

## 目的

子ファイル保存の一覧ダイアログが、dirty な子の件数や対象名・保存先パスの長さによって
**横方向へはみ出し、縦にも収まらない**問題を解消する（暫定仕様 05 **v0.3-C** / §3-5・受入条件 14）。
実機目視（2026-07-29）で 10 行以上のときに確認された。

- レイヤ制約: **presentation 限定**（`config_io/child_save_dialog.py` のみ）。
  **application / domain 不変・スキーマ不変**。行モデル（`ChildSaveRow`）と
  `child_save_rows.py` の判定ロジックは**変更しない**（表示の見せ方だけを変える）。
- **選択の意味・保存計画・A2 の判定条件は一切変えない**（task_08 の挙動を維持する）。

## 対象範囲（`config_io/child_save_dialog.py` 限定）

### 1. ダイアログのサイズとリサイズ

`_create_action_dialog` で以下を設定する（**数値は本タスクで確定**）。

| 項目 | 値 |
|---|---|
| 初期サイズ | `dialog.geometry("960x480")` |
| 最小サイズ | `dialog.minsize(720, 320)` |
| リサイズ | `dialog.resizable(True, True)`（現行の `resizable(False, False)` を置き換え） |

- 行数によってウィンドウサイズを変えない（**固定の初期サイズ**）。行が増えたら 2 のスクロールで見せる。

### 2. 縦スクロール

一覧部分（ヘッダ行 + 各行）を**縦スクロール可能な領域**にする。

- `tk.Canvas` + 内側の `ttk.Frame` + `ttk.Scrollbar(orient="vertical")` の定石構成にする。
  内側フレームの `<Configure>` で `canvas.configure(scrollregion=canvas.bbox("all"))` を更新する。
- **横スクロールバーは持たない**（横は 3 の省略表示で収める）。
- **OK / キャンセルのボタン行はスクロール領域の外**（常に見える位置）に置く。
- マウスホイールでの縦スクロールを有効にする（`<MouseWheel>` をキャンバスにバインド）。

### 3. 省略表示とツールチップ

長い文字列で横幅が膨らまないよう、**対象名と保存先パスだけ**を省略表示にする。

- 純関数を 2 本追加する（**モジュール関数**。`_kind_label` と同じ場所）:
  - `_ellipsize(text: str, limit: int) -> str` — **末尾省略**（`limit` 以下ならそのまま。
    超えたら先頭 `limit - 1` 文字 + `…`）
  - `_ellipsize_path(text: str, limit: int) -> str` — **中央省略**（`limit` 以下ならそのまま。
    超えたら先頭 `limit // 3` 文字 + `…` + 末尾 `limit - limit // 3 - 1` 文字）
- 適用（**上限も本タスクで確定**）: 対象名 = `_ellipsize(display_name, 24)` /
  保存先パス = `_ellipsize_path(target_path, 56)`。
- **種別・共有状況・ラジオ（操作）は省略しない**（判断に直結するため）。
- **ツールチップ**: `_bind_tooltip(widget, text)` メソッドを追加し、**省略が発生したセルにだけ**
  **全文**を出す（省略が起きていないセルにはバインドしない）。
  - `<Enter>` で `tk.Toplevel`（`overrideredirect(True)`）を表示、`<Leave>` / `<Button>` で破棄。
  - ツールチップの Toplevel は**モーダルにしない**（`grab_set` を呼ばない）。
  - 例外は握って表示だけ諦める（ツールチップの失敗で保存操作を止めない）。

### 4. テスト（`tests_ui/test_child_save_dialog.py`）

**構造テスト**（既存の「ダイアログ本体を実行する内部テスト」の手法＝ tkinter widget を patch する形を踏襲）:

| # | 内容 |
|---|---|
| 1 | `resizable(True, True)` / `geometry("960x480")` / `minsize(720, 320)` が呼ばれる |
| 2 | 縦スクロール領域が作られる（`tk.Canvas` と `ttk.Scrollbar(orient="vertical")` が生成される。横スクロールバーは作られない） |
| 3 | `_bind_tooltip` が、**省略された対象名 / 保存先パスに対してのみ全文で呼ばれる**（短い値では呼ばれない） |
| 4 | 行数が増えてもダイアログの `geometry` 呼び出しが変わらない（固定サイズ） |

**純関数テスト**（`tests/` でよい。tkinter に依存しないため `tests/test_child_save_rows.py` ではなく
**`tests_ui/test_child_save_dialog.py` 内**へ置く。新規ファイルは作らない）:

| # | 内容 |
|---|---|
| 5 | `_ellipsize` — 上限以下はそのまま / 超えたら末尾省略で長さが `limit` になる |
| 6 | `_ellipsize_path` — 上限以下はそのまま / 超えたら中央省略で長さが `limit` になり、**先頭と末尾が保持される** |

- 既存の内部ダイアログテスト（`_FakeSaveDialog` / `_FakeDialogWidget`）は、**新しく使う widget と
  メソッドに合わせて fake を拡張する**（`geometry` / `minsize` / `bind` / `configure` /
  `create_window` / `yview` など。`tk.Canvas` / `ttk.Scrollbar` の patch を追加）。
  既存テストの**アサーションは緩めない**。
- **実表示のはみ出しは自動テストの対象外**（受入条件 14 の目視分。下記「確認」6 を参照）。

### 設計メモ / 制約

- **選択・保存計画に関わるコードへ触らない**。`_confirm_actions` / `_resolve_action_targets` /
  `confirm_trigger_set_dependency` / `confirm_recalculated_overwrite` のロジックは無変更
  （スクロール領域へ移すことによる親 widget の変更は可）。
- `ChildSaveRow.target_path` / `display_name` の**値そのものは変えない**。省略はあくまで表示時の変換で、
  `_ask_save_as_path` の `initialdir` / `initialfile` などは**全文のまま**使うこと。
- ツールチップは `_app.hook`（キーボードフック）に触らない。一覧ダイアログ表示中は
  `ask_child_save_actions` が既にフックを停止しているため、追加の停止・再開は不要。
- `child_save_dialog.py` は現在約 194 行。本タスクの追加で 300 行を超える見込みなら、
  **本タスクでは分割せず**、フェーズ末の `/refactor_check` の判定へ回す（task 途中で構造を変えない）。

## 含まない

- **正本 `spec_detail/` への反映 — task_10**。
- 行モデル・共有状況の判定（`child_save_rows.py`）の変更。列の追加・削除・並べ替え。
- 一覧の並び順・グルーピング・フィルタ・全選択などの新機能（暫定仕様 §3-2 の列構成から増やさない）。
- 依存確認ダイアログ / 再計算先の上書き確認ダイアログのレイアウト変更
  （どちらも `messagebox` ベースのまま。行数が多いときの見せ方は**本タスクの対象外**）。
- 個別保存ボタンの統合（暫定仕様 §11）/ ダイアログの共通化・部品化。

## 確認

`.venv` の python で実行する（worktree ルートから `..\..\..\.venv\Scripts\python.exe`）。

1. `-m compileall -q keyseq main.py tests_ui` が clean
2. `-m unittest discover -s tests` が全 pass（現行 136 件）
3. `-m unittest discover -s tests_ui` が全 pass（現行 110 件 + 追加分）
4. `-m tests.smoke_app` が pass
5. **受入条件 14（構造）**: 上記テスト 1〜6 が pass
6. **受入条件 14（目視・ユーザー実施。本タスクでは実施しない）**:
   **dirty な子 12 行以上・対象名 40 文字・保存先パス 160 文字**の状態でダイアログを開き、
   ①横方向にはみ出さない ②縦スクロールで全行に到達できる ③端をドラッグしてリサイズできる
   ④省略された対象名・パスにカーソルを合わせると全文がツールチップで見える
7. 既存の特性テスト（保存 JSON のバイト列比較）を**緩めずに** pass すること

## 完了条件

- 上記確認 1〜5・7 が pass・**reviewer 採用**。
- 実機目視（確認 6）は **task_10 の前にユーザーがまとめて実施**する。本タスクでは実施しない。
