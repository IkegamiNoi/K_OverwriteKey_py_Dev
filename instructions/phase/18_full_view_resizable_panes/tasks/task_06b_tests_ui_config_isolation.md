# task_06b_tests_ui_config_isolation

## 目的

phase 18 完了判定前レビュー（`deep-reviewer` 指摘 1・ユーザー採用 2026-09-17）の修正。
`tests_ui/test_full_view_panes.py` / `tests_ui/test_pane_drag_and_window_min.py` は `write_startup` の差し替えがテストごとの `setUp` 内だけで、
後始末の `geometry` 復元で入ったウィンドウ幅の保存予約（暫定仕様 16 v0.5 §3-8・500ms 後）が、差し替えの外れた区間
（次テストの `setUp` 冒頭の `update()` / クラス終了時の `_destroy_app` の `update()`）で実行されうる。負荷下で実際の `config/config.json` を書く余地を塞ぐ。
**テストのみ**。`keyseq/` は変更しない。**既存アサーション・期待値は変えない**。

## 対象範囲（tests_ui 2 ファイル限定）

### `tests_ui/test_full_view_panes.py` / `tests_ui/test_pane_drag_and_window_min.py`（両方に同じ形で）

1. **クラス単位で書き込みを遮断**: `setUpClass` の App 生成前に `patch.object(app_module.StartupIo, "write_startup", return_value=True)` と
   `patch.object(app_module.ConfigService, "save_startup", return_value=None)` を開始し、`cls.addClassCleanup(patcher.stop)` で止める
   （手本 `tests_ui/test_pane_window_width_persistence.py:18-45`）。クラスの後始末は登録の逆順で走るため、**`_destroy_app` より後に止まる順で登録する**。
2. **破棄前に予約を取り消す**: `_destroy_app` の `update()` の前に `cls.app.pane_layout.cancel_window_width_save()` を呼ぶ。
3. **テストごとの後始末でも取り消す**: 各テストの復元処理（`_restore_layout` / `_restore`）の最後に `self.app.pane_layout.cancel_window_width_save()` を呼ぶ。
4. 既存の `setUp` 内の `patch.object(self.app.startup_io, "write_startup", ...)` は、呼び出し回数・引数をアサートしているテストがあるので**残す**
   （インスタンス属性の差し替えがクラス差し替えより優先されるため両立する）。

### 設計メモ / 制約

- 期待値・アサーション・テスト名・テスト数を変えない。`keyseq/` と他の tests_ui モジュールは触らない。
- `app_module` の import が無ければ `from keyseq.presentation import app as app_module` を追加する。

## 読むファイル

- 編集対象（全体）: `tests_ui/test_full_view_panes.py` / `tests_ui/test_pane_drag_and_window_min.py`
- 手本（範囲のみ）: `tests_ui/test_pane_window_width_persistence.py:1-50`
- `keyseq/presentation/controllers/pane_layout/pane_layout_controller.py:208-245`（保存予約と `cancel_window_width_save`）

## 含まない

- deep-reviewer の保留指摘（ドラッグ後の最小幅更新・`pane_measure.py` の構造依存・phase 18 以前の tests_ui の実 config 読込）
- 正本・phase 文書の更新（task_06 で実施）

## 確認

python は `../../../.venv/Scripts/python.exe`。実測は `verifier`。

1. `-m compileall -q tests_ui` が clean。
2. `-m unittest tests_ui.test_full_view_panes tests_ui.test_pane_drag_and_window_min -v` が 6 / 12 pass（件数不変）。
3. `-m unittest discover -s tests_ui` が 413 OK。`-m unittest discover -s tests` が 445 OK（skip 7）。`-m tests.smoke_app` が SMOKE OK。
4. 実行前後で `git status --short config` が空、かつ `config/config.json` の更新時刻が変わらない（ファイルが無ければ作られない）。
5. `git diff --stat` が上記 2 ファイル（+ 本タスク文書）のみ。

## 完了条件

- 上記確認 pass・**`reviewer` 採用**。実機目視は不要。

## 完了記録（2026-09-17）

- 実装は `codex-implementer`（2 ファイル各 +9 行）。
- `verifier`: compileall clean / 対象 2 モジュール 6・12 OK / `tests_ui` 413 OK / `tests` 445 OK（skip 7）/ smoke OK / config.json の mtime 前後不変 / 差分は tests_ui 2 ファイルのみ。
- `reviewer` = 完了可（登録順 LIFO で `_destroy_app` 中も遮断が有効・予約取消 2 箇所・アサーション不変を確認）。
