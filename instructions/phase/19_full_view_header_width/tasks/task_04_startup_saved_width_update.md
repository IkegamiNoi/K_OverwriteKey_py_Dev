# task_04_startup_saved_width_update

## 目的

暫定仕様 17（v0.3）§2-6・§3-5「保存値の更新」を実装する。**保存したウィンドウ幅がウィンドウ最小幅より狭く、起動時の初回適用で広げた場合だけ**、
適用後のウィンドウ幅で `full_view_window_width` を 1 回書く（原因がヘッダかメイン領域かは問わない）。
**保存値が無い / 不正 / 画面幅への切り詰めだけ / 広げていない / 起動時以外**は書かない（phase 18 の自動決定幅の規則を維持）。
**presentation 限定**。スキーマ不変（既存キーの書き込み契機を 1 つ追加）。

## 対象範囲（presentation 2 ファイル + tests 2 ファイル）

### `keyseq/presentation/pane_width_rules.py`

- 新規 `startup_window_width_to_save(raw: object, applied_width: int) -> int | None`（暫定仕様17 §3-5）:
  `raw` が `bool` を含む非 int、または 1 未満なら `None`（`parse_saved_window_width` と同じ有効条件。**画面幅での切り詰めはしない** = 切り詰め前の値で比べる）。
  有効かつ `raw < applied_width` なら `applied_width`、それ以外は `None`。tkinter 非依存。

### `keyseq/presentation/controllers/pane_layout/pane_layout_controller.py`

- `apply_initial_widths` の末尾（`self._auto_window_width = self.app.winfo_width()` の後）で、
  `startup = getattr(self.app, "_startup_settings", None)` が dict のときだけ
  `width = startup_window_width_to_save(startup.get(WINDOW_WIDTH_KEY), self.app.winfo_width())` を求め、`None` でなければ
  `self.app.startup_io.write_startup({WINDOW_WIDTH_KEY: width})`（戻り値は見ない）。
- 起動時以外（`on_font_changed` / `on_full_view_shown` / 保存予約）は変えない。自動決定幅の記録も変えない
  （書いた幅は自動決定幅と同じなので、その後の保存予約でも重複して書かない。§3-5）。
- 30 行を超える場合は小さな private メソッドへ切り出す。本体は 270 行以内を目安（超えたら報告）。

### `tests/test_pane_width_rules.py`（追記）

- `test_startup_window_width_to_save`: `(790, 799) → 799` / `(799, 799) → None` / `(1000, 799) → None` / `(2000, 1000) → None`（切り詰めのみ）/
  `(1100, 1054) → None`（切り詰め後に広げたが切り詰め前の値は広い）/ `(None, 799)` `(True, 799)` `("790", 799)` `(790.0, 799)` `(0, 799)` `(-1, 799)` → `None`。

### `tests_ui/test_pane_window_width_persistence.py`（追記）

既存の `WindowAppFixture`（クラス単位で `write_startup` を patch・`cls.writer`）を使う。既存クラス・アサーションは変えない
（既存の Saved 1000 / Clamped 2000・画面 1000 / Bool / 文字列 / 0 / キー無しの各クラスが「書かない」を担保している）。

1. **`NarrowSavedWidthStartupTest`**（`startup = {WINDOW_WIDTH_KEY: 300}`）: 起動後 `app.winfo_width() > 300` かつ
   `cls.writer` が **1 回だけ** `{WINDOW_WIDTH_KEY: app.winfo_width()}` で呼ばれている。続けて `pane_layout._save_window_width()` を直接呼んでも呼び出し回数が増えない。
2. **`ClampedThenWidenedStartupTest`**（`startup = {WINDOW_WIDTH_KEY: 900}`・`screen_width = 700`）: 起動後のウィンドウ幅が 700 以上（最小幅で広がる）で、`cls.writer` は呼ばれない（切り詰め前の 900 は適用後より広い）。
   - 画面幅 700 でもウィンドウ最小幅が 700 を超える前提。前提が崩れる環境では `skipTest` せず、`app.winfo_width()` と `900` の大小で期待を分岐しない（前提を `assertGreater(app.winfo_width(), 700)` で明示して落とす）。

### 設計メモ / 制約

- `app.py` の初期 geometry の決定（`parse_saved_window_width` で切り詰め）は変えない。
- `write_startup` は既存の失敗表示（フック停止付き）のまま。起動時の失敗で起動を止めない。
- 新規テストクラスは `StartupAssertions` を継承しない（「書かない」前提のため）。

## 読むファイル

- 編集対象（全体）: `keyseq/presentation/controllers/pane_layout/pane_layout_controller.py`
- `keyseq/presentation/pane_width_rules.py:1-25`（定数・`parse_saved_window_width`）
- `keyseq/presentation/app.py:88-97`（初期 geometry）
- 既存テスト（範囲のみ）: `tests/test_pane_width_rules.py:1-45` / `tests_ui/test_pane_window_width_persistence.py:1-150`
- 仕様: `instructions/history/17_full_view_header_width.md` §2-6・§3-5・§5-8

## 含まない

- 統合確認・二次レビュー・実機目視（**task_05**）/ 正本反映（**task_06**）
- 起動時以外に広がった幅の保存（従来どおり保存しない）

## 確認

python は `../../../.venv/Scripts/python.exe`。実測は `verifier`。

1. `-m compileall -q keyseq tests tests_ui` が clean。
2. `-m unittest tests.test_pane_width_rules -v` が全 pass。
3. `-m unittest tests_ui.test_pane_window_width_persistence -v` が全 pass（新規 2 クラスを含む・件数を報告）。
4. `-m unittest discover -s tests` が 450 + 追加分 OK（skip 7）/ `-m unittest discover -s tests_ui` が全 OK / `-m tests.smoke_app` が SMOKE OK / `config/config.json` の mtime 不変。
   **列挙外のテストが落ちた場合は、メインが直さずユーザーへ報告する**。
5. `git diff --stat` が上記 4 ファイル（+ 本タスク文書）のみ。

## 完了条件

- 上記確認 pass・**`reviewer` 採用**。
- 実機目視は task_05 でまとめて実施（旧保存値が狭い config での起動）。

## 完了記録（2026-09-17）

- 実装は `codex-implementer`（4 ファイル・コントローラ 270 行）。
- `verifier`: compileall clean / `test_pane_width_rules` 31 OK / `test_pane_window_width_persistence` 30 OK（新規 2 クラス含む）/ `tests` 451 OK（skip 7）/ `tests_ui` 427 OK / smoke OK / config mtime 不変 / 差分 4 ファイルのみ。
- `reviewer` = 完了可（書く条件は切り詰め前の生値で比較・呼び出しは初回適用の 1 回のみ・後続の保存予約で重複しない）。軽微（任意）: `_startup_settings` の取得が 2 回 → 対応不要。
