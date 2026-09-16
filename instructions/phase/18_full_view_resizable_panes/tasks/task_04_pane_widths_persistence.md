# task_04_pane_widths_persistence

## 目的

フル表示両端の枠の**希望幅**を `config/config.json` の `full_view_pane_widths` へ保存し、起動時に検証して復元する
（暫定仕様 16 §2-7〜§2-9・§3-5・§3-6。受け入れ条件 §5-8・§5-10・§5-13）。
**presentation 限定**。domain / application / infrastructure は変更しない。`pane_width_rules.py` も変更しない
（`PANE_WIDTHS_KEY` / `parse_saved_pane_widths` は task_01 で実装済み）。

## 対象範囲（presentation 限定・新規テスト 1 モジュール）

### `keyseq/presentation/controllers/pane_layout_controller.py`

1. **復元**: 初回の `<Configure>` で呼ばれる幅の初期適用で、最小幅を測ったあと
   `parse_saved_pane_widths(self.app._startup_settings.get(PANE_WIDTHS_KEY))` を評価する。
   - 戻り値が `PaneWidths` → それを `desired` にする（**最小幅未満でもそのまま保持**。表示幅の引き上げは既存の `resolve_layout` が行う）。
   - `None`（キー無し・非 dict・欠け・bool・非 int・0 以下）→ 従来どおり `default_pane_widths(...)` を `desired` にする。
   - どちらもエラー表示なし・**ファイルを書かない**。その後 `apply_layout()`。
   - `_startup_settings` が dict でない場合も既定幅で動く（`getattr` + `isinstance` で守る）。
   - メソッド名は中身に合わせて `apply_initial_widths` へ改名してよい（参照は `_on_configure` のみ。テストに参照なし）。
2. **保存**: `_on_desired_changed(new)` で、既存どおり `self.desired = new` と最小幅の更新を**先に**行い、その後
   `self.app.startup_io.write_startup({PANE_WIDTHS_KEY: {"keymap": new.keymap, "sequence": new.sequence}})` を呼ぶ。
   - 戻り値が False（書込失敗）でも `desired` は戻さない（§3-5）。失敗表示は `write_startup` 既存の `messagebox` に任せる。
   - 「変化が無ければ書かない」は `_on_release` の既存条件 `new != self.desired` で満たす（条件を変えない）。

### `tests_ui/test_pane_widths_persistence.py`（新規）

`tests_ui/test_pane_drag_and_window_min.py` の共有 App・`setUp` の保存 / 復元の型を踏襲する
（ドラッグ操作の手順もそのファイルのヘルパを参考にしてよいが、**既存ファイルは変更しない**）。
**実際の `config/config.json` を書かない**: 保存経路は `patch.object(app.startup_io, "write_startup", ...)` で記録するか、
`patch.object(app.config_service, "save_startup")` で差し替える。`app._startup_settings` は後始末で元に戻す。

1. **ドラッグで保存**: サッシュ 0 をドラッグして離すと `write_startup` が 1 回だけ、
   `{"full_view_pane_widths": {"keymap": <desired.keymap>, "sequence": <desired.sequence>}}` で呼ばれる（サッシュ 1 も同様）。
2. **書かない場合**（§5-8）: ①サッシュ以外で押して離す ②サッシュを押してそのまま同じ位置で離す
   ③最小幅未満の希望幅を持つ状態でサッシュ 0 を縮める方向へ動かし最小幅で止まった場合（§5-9 後半）— いずれも `write_startup` は呼ばれない。
3. **表示幅を保存しない**（§5-9 前半）: フォントを上げてキーマップ管理が最小幅へ広がった状態でサッシュ 1 を動かして離すと、
   保存される `keymap` は元の希望幅のまま。
4. **書込失敗**: `write_startup` が False を返しても `desired` は新しい値。続けて同じ位置で押して離しても再度呼ばれない。
5. **既存キーを消さない**（§5-13）: `write_startup` は差し替えず `config_service.save_startup` を patch し、
   `_startup_settings` に `ui_font_delta_pt` / `orphan_sweep_scan_dirs` / `keymap_set_path` を入れた状態でドラッグ保存 →
   保存 dict にそれらと `full_view_pane_widths` が両方含まれる。
6. **復元**（§5-10）: `_startup_settings` に保存値を入れて初期適用メソッドを呼ぶ →
   - 正常値 → `desired` が保存値・両端の `winfo_width()` が保存値（最小幅以上のとき）。
   - 不正値（非 dict / `keymap` 欠け / `sequence` 欠け / `True` / `"300"` / `300.0` / `0` / `-1`）→ `desired` がキー無しのときの既定幅と一致。
   - 最小幅未満（例 `keymap: 1`）→ `desired.keymap == 1`・キーマップ管理の表示幅は最小幅。
   - いずれの場合も `write_startup` / `save_startup` は呼ばれない。
7. **keymap_set 保存で値が残る**（§5-13）: `app.config_service.save_runtime_data` を一時ディレクトリの `config_root` で呼び
   （`startup_data` に `full_view_pane_widths` を含める）、**返り値の startup payload** と
   **一時ディレクトリに書かれた config.json**の両方に値が残ること。呼び方は
   `tests_ui/test_config_io_characterization_keymap_set_startup.py` の既存パターンに合わせる
   （実プロジェクトの `config/` を書かないこと）。

### 設計メモ / 制約

- 保存キー名は `PANE_WIDTHS_KEY` 定数を使う（文字列直書きしない）。
- 保存は `write_startup` 経由のみ（`config_service.save_startup` をコントローラから直接呼ばない）。
- task_02 / task_03 のテスト（`test_full_view_panes.py` / `test_pane_drag_and_window_min.py`）は**変更しない**。
  task_03 のテストは `write_startup` を patch 済みなので保存追加で実 config は書かれない。
- コントローラが 250 行を超える場合のみ task_03 の分割方針に従う（超えない見込み）。関数はおおむね 30 行以内。

## 含まない

- 統合確認・二次レビュー・実機目視（**task_05**）
- task_03 完了記録の「既知の残存」（画面幅超過中のドラッグ後の最小幅）の修正（**task_05** で扱う）
- 正本 `features.md` / `data_schema.md` / `codebase_map.md` の更新（**task_06**）
- `write_startup` / `load_startup_settings` / application 層の保存経路の変更（無変更で値が保持される）

## 確認

python は `../../../.venv/Scripts/python.exe`（素の `python` / `py` は使わない）。実測は `verifier`。

1. `-m compileall -q keyseq main.py tests tests_ui` が clean。
2. `-m unittest tests_ui.test_pane_widths_persistence -v` が全 pass（上記 1〜7 が存在）。
3. `-m unittest tests_ui.test_pane_drag_and_window_min tests_ui.test_full_view_panes -v` が全 pass（無変更）。
4. `-m unittest discover -s tests` が 441 実行 OK（skip 7）。
5. `-m unittest discover -s tests_ui` が全 pass（368 + 追加）。
6. `-m tests.smoke_app` が SMOKE OK。
7. `git diff --stat` が対象範囲のファイルのみ。`git status --short config` が空。

## 完了条件

- 上記確認 pass・**`reviewer` 採用**。
- 実機目視（再起動後の復元を含む）は **task_05 でまとめて実施**。

## 完了記録（2026-09-17）

- 実装は `codex-implementer`（Codex 回復）。`apply_default_widths` → `apply_initial_widths` へ改名（保存値 or 既定幅）・
  `_on_desired_changed` で `write_startup`。コントローラ 243 行（分割なし）。新規テスト 12 件。
- `verifier`: compileall clean / 新規 12 OK / task_02・03 の 17 OK / `tests` 441 OK（skip 7）/ `tests_ui` 380 OK / smoke OK / config 差分なし。
- `reviewer` = 採用（指摘なし）。§5-13 は `split_payloads.py:354-356` が未知キーを透過することで成立（application 無変更）。
