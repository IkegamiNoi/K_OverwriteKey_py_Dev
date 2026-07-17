# task_01_status_bar_local_vars

## 目的

`keyseq/presentation/views/status_bar.py` が App へ生やしている 2 属性
（`app.runtime_status_frame` / `app.status_bar`）を**ローカル変数化**し、View → App の
ウィジェット逆流を解消する（[phase.md](../phase.md) スコープ「含む」1）。

計画04 W5 で「ボタン/入力ウィジェットの逆流ではない」として対象外にした残り。W5 で処理した
write-only 生やし（`topmost_chk` / `compact_btn` / `suppress_chk` / `run_to_end_chk` / `keymap_add_btn`）と
**同型**であり、同じ扱い（所有側のローカル化・生やし削除）で解消できる。

**レイヤ制約: presentation 限定**。domain / application / infrastructure 不変。スキーマ不変。
**挙動不変**（文言・レイアウト値・ウィジェットの親子関係を 1 文字も変えない）。

## 対象範囲（presentation 限定・単一ファイル・数行）

### `keyseq/presentation/views/status_bar.py`

関数 `build_status_area(app, parent)` の中で、以下 2 つの **App への代入をローカル変数へ変える**:

| 現状 | 変更後 |
|---|---|
| `app.runtime_status_frame = ttk.LabelFrame(parent, ...)`（6行目） | `runtime_status_frame = ttk.LabelFrame(parent, ...)`（ローカル変数） |
| `app.status_bar = ttk.Frame(parent, style="Statusbar.TFrame")`（10行目） | `status_bar = ttk.Frame(parent, style="Statusbar.TFrame")`（ローカル変数） |

これに伴い、同関数内の**参照側も全てローカル変数へ置換**する:

- `app.runtime_status_frame` の参照: 7行目（`.pack(...)`）、8行目（`ttk.Label` の親）
- `app.status_bar` の参照: 11行目（`.pack(...)`）、12〜14行目（`grid_columnconfigure` ×3）、
  16行目・23行目・29行目（`ttk.Label` の親）

**変更しないもの**（App への正当な参照。そのまま残す）:

- `app.ui_vars.status_var` / `app.ui_vars.file_status_var` / `app.ui_vars.flash_message_var`（8, 17, 24行目）
- `app._update_file_status()`（31行目・関数末尾）
- 関数シグネチャ `build_status_area(app, parent)`（`app` 引数は上記のため引き続き必要）
- 呼び出し側 `keyseq/presentation/app.py` の `build_status_area(self, self)`

### 設計メモ / 制約

- **着手前に必ず grep で「読み手なし」を再確認すること**。
  `git grep -nE "(runtime_status_frame|status_bar)" -- keyseq tests tests_ui` を実行し、
  `views/status_bar.py` 内と `app.py` の import 行以外に参照が無いことを確認する。
  **App 属性を消すため、読み手の見落としは即 `AttributeError` になる**（調査時点では
  `build_status_area` 内のみで読み手なしを確認済み。phase.md「レビュー方針」参照）。
  想定と異なる読み手を発見した場合は**独自判断で進めず、報告して停止すること**。
- ウィジェットの**親子関係・`pack` / `grid` の引数・`style` / `text` / `padding` / `textvariable` /
  `anchor` / `justify` / `sticky` / `row` / `column` / `weight` を 1 文字も変えない**。
  変えるのは「代入先が `app.<name>` かローカル変数か」だけ。
- ウィジェットの**生成順・pack 順を変えない**（`side="top"` の LabelFrame → `side="bottom"` の
  status_bar の順序は表示レイアウトに影響する）。
- ローカル変数名は現行の属性名を引き継ぐ（`runtime_status_frame` / `status_bar`）＝追跡性のため。

## 含まない

- `trigger_list` alias の削除と tests_ui の参照経路変更（**task_02**）
- 正本反映・記録・`/refactor_check`（**task_03**）
- `views/status_bar.py` の**関数分割・命名変更・整形**（本タスクは生やし解消のみ）
- `build_status_area` の**シグネチャ変更**（`app` 引数の除去等）。`app.ui_vars` /
  `app._update_file_status()` を使うため `app` は必要
- `app.py` 側の変更（呼び出し方は不変）
- 計画04 W7 の次期課題（[idea_01](../../../backlog/idea_01_hotkey_validation_to_domain.md) /
  [idea_02](../../../backlog/idea_02_startup_font_settings_cleanup.md)）

## 確認

python は必ずリポジトリルートの `.venv` を使う（worktree 相対 `..\..\..\.venv\Scripts\python.exe`。
グローバル `py` は依存欠落で tests_ui / smoke が落ちる。`.claude/rules/python_rules.md`）。

1. **grep（生やし解消の確認）**:
   `git grep -nE "app\.(runtime_status_frame|status_bar)" -- keyseq` が **0 件**
2. **grep（読み手の不在確認）**:
   `git grep -nE "\.(runtime_status_frame|status_bar)\b" -- keyseq tests tests_ui` の結果に
   `views/status_bar.py` 以外の参照が無いこと（`app.py` の `from ...views.status_bar import build_status_area` は
   モジュール import であり該当しない）
3. **標準検証 4 項目**（ベースライン一致）:
   - `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py` → clean
   - `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` → **59 pass**
   - `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` → **9 pass**
   - `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` → **SMOKE OK**
4. **差分確認**: `git diff -- keyseq/presentation/views/status_bar.py` の差分が
   「`app.` の除去に伴う識別子変更のみ」であること（レイアウト引数・文言の差分が無いこと）

## 完了条件

- 上記「確認」1〜4 が pass。
- **reviewer 採用**（`.claude/rules/review.md` の 5 観点。CLAUDE.md「レビュー（必須）」）。
- 実機目視: **task_02 完了後に phase.md「レビュー方針」の手動確認としてまとめて実施**
  （ステータスバー表示 = ファイル状態 / 一時メッセージ / 「ステータス」欄）。
  本タスク単独では標準検証（smoke に UI 構築が含まれる）までとする。
