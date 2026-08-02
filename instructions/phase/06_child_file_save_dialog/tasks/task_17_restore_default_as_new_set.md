# task_17_restore_default_as_new_set

## 目的

「例を復元」（`restore_default`）を**中身のある新規作成**として扱うよう直す
（暫定仕様 05 **v0.6-O / P / Q**・§7・受入条件 **24**・**24b**・**25**・**26**）。

1. **【O・実バグ】構成セットの同一性を引き継ぐ**。`restore_default` は `data` の差し替えと
   `reset_trigger_set_state()` だけを行い **`keymap_set_path` をクリアしない**（`new_config` はする）。
   このため保存が別名保存へ落ちず、**前に読み込んでいた keymap_set を無確認で上書き**する
   （2026-08-02 実機で発生）。例の sequence の保存先が実在しないときは、§8 の依存関係 → v0.4-D の
   自動保存を経由して**旧トリガー一覧まで上書き**される。
2. **【P】未保存確認が無い**。`restore_default` だけ `confirm_save_if_dirty()` を呼ばず、
   編集中に押すと無警告で変更が失われる。
3. **【Q】例の子が保存されない**。例のデータは子 dirty フラグを持たないため、新しい名前で保存しても
   既存の `user/sequences/<key>.json` があれば保存計画の既定規則で **SKIP** され、
   **新しい keymap_set が旧セットの子ファイルを索引する**（中身が混ざる）。

レイヤ制約: **presentation 限定**（`config_io/keymap_set_io.py` + `controllers/dirty_state.py` の既存 API 利用）。
**application / domain 不変・スキーマ不変・保存計画のロジック不変**。仕様変更ではなくバグ修正 + 位置づけの統一。

## 対象範囲（presentation の `restore_default` 限定）

### 1. `keyseq/presentation/controllers/config_io/keymap_set_io.py` — `restore_default`（567-577）

現在の実装（`askyesno` → `data` 差し替え → `reset_trigger_set_state` → UI 更新 → `set_dirty(True)`）を、
以下の順序へ変更する。**`new_config`（48-65）と同形にすること**（差異を残さない）。

| # | 処理 | 根拠 |
|---|---|---|
| 1 | `if not self.confirm_save_if_dirty("例の復元"): return` | v0.6-P |
| 2 | 既存の `messagebox.askyesno("確認", "例の設定に戻します。よろしいですか？")` で false なら return | 既存挙動の維持 |
| 3 | `self._app.data = self._app.config_service.new_default_data()` | 既存 |
| 4 | `self._app.dirty_tracker.reset_trigger_set_state()` | 既存（**必ず 5 の前**。`trigger_set_dirty` を False に落とすため） |
| 5 | `self._app.keymap_set_path = ""` | **v0.6-O（本タスクの中心）** |
| 6 | 復元した `data` の子を dirty 化（下記） | **v0.6-Q** |
| 7 | UI 更新（`_sync_control_vars_from_data` / `_indices` / `_selected_trigger_idx` / `refresh_triggers` / `refresh_actions`） | 既存 |
| 8 | `self._app.dirty_tracker.set_dirty(True)` + `_set_flash_message("例の設定に戻しました（未保存）。")` | 既存 |

- **アクション名は「例の復元」**（`confirm_save_if_dirty` は `f"{action_name}の前に保存しますか？"` を作る）。
- **確認の順序は 1 → 2**（未保存確認が先）。「保存する」を選んで `save_as` がキャンセル / 失敗した場合は
  `confirm_save_if_dirty` が `False` を返すため**復元を中止**する（既存契約どおり。追加実装は不要）。
- **フラッシュメッセージ・確認文言は変更しない**。

### 2. 子の dirty 化（v0.6-Q）

`dirty_state` の**既存メソッドのみ**を使う（新しい API を足さない・内部キーへ直接代入しない）。

- 各 `data["triggers"]` の要素 → `dirty_tracker.mark_sequence_dirty(trigger)`
- `dirty_tracker.mark_trigger_set_dirty()`
- `data["keymaps"]` があれば各要素 → `dirty_tracker.mark_keymap_dirty(keymap)`
  （例には keymap が無いが、`DEFAULT_CONFIG` の変更に耐えるよう分岐を書く）
- 対象は**復元した `data` の子だけ**。他の状態（`trigger_set_imported` 等）へ波及させない。
- **`new_config` は変更しない**（triggers を空にするため対象が無い。v0.6-Q の確定事項）。

### 3. テスト

| 追加先 | # | 内容 |
|---|---|---|
| `tests_ui/` | 1 | **受入条件 24**: 保存済み keymap_set を読み込んだ状態から `restore_default` → `save_keymap_set` で **`asksaveasfilename` が呼ばれる**。キャンセルすると**旧 keymap_set / 旧 trigger_set / 旧 sequence がバイト列不変** |
| 〃 | 2 | **受入条件 24**: 続けて**新しい名前**で保存すると、その keymap_set と **stem 由来の trigger_set** が新規に作られ、**旧 keymap_set と旧 trigger_set はバイト列不変** |
| 〃 | 3 | **受入条件 24b**: **既存と同名**の keymap_set を指定すると、親と stem 由来の trigger_set は**上書きされる**。このとき **sequence 行の既定は別名保存**で、既定のまま OK すれば**既存の sequence ファイルはバイト列不変** |
| 〃 | 4 | **受入条件 25**: ①未保存確認でキャンセル ②「保存する」を選んだが `save_as` をキャンセル ③`askyesno` でキャンセル、の 3 ケースで **`data` が置換されず `keymap_set_path` も変わらない**。①②では `askyesno` が呼ばれない（**`askyesnocancel` → `askyesno` の順序**をアサート） |
| 〃 | 5 | **受入条件 26**: `restore_default` 直後の保存で**一覧ダイアログの行に trigger_set と f1 / f2 が出る**。保存先に同名の既存 sequence があるケースで、既定のまま OK すると ①既存ファイルがバイト列不変 ②例の内容が別名で書かれる ③保存された trigger_set の `sequence_path` が**その別名**を指す |
| 〃 | 6 | **回帰（受入条件 17・task_13）**: `restore_default` 直後の個別「トリガー一覧を保存」が**前の構成の trigger_set を書かない** |

**既存テストの更新（必須。放置するとハングする）** — `tests_ui/test_config_io_characterization_keymap_set_startup.py`:

- `test_restore_default_yes` — `set_dirty.assert_called_once_with(True)` は **Q により成立しなくなる**
  （`mark_*_dirty` が `set_dirty(True, config_dirty=False)` を呼ぶ）。
  **「最後の呼び出しが `set_dirty(True)`」＋「`config_dirty` が True になる」**を確認する形へ書き換える。
- `test_restore_default_resets_trigger_set_state_and_runtime_data` / `..._trigger_set_save_does_not_write_previous_source`
  — dirty 状態を作ってから `restore_default` を呼ぶため、**`askyesnocancel` が未 patch だとモーダルで止まる**。
  各テストで `messagebox.askyesnocancel` を patch する（**`setUp` の fail-fast ガードは変更しない**。
  他経路の `confirm_save_if_dirty` テストを巻き込むため）。
- `test_restore_default_no_does_nothing` — 未保存でない状態なら `confirm_save_if_dirty` は素通りするが、
  前提が変わるなら明示的に patch する。

### 設計メモ / 制約

- **保存計画・ダイアログ・v0.4-I の判定ロジックには一切触らない**。Q は「子に dirty 印を付ける」だけで、
  以降は既存の `collect_child_save_rows` → v0.4-I → `build_save_plan` が処理する。
- **同名 keymap_set を選んだときに trigger_set が上書きされるのは意図した挙動**（v0.6-O に明記）。
  安全弁を足さない。親が実在しない名前を指定したときも同じ（敵対的レビュー指摘 → 除外で確定）。
- `reset_trigger_set_state()` は `trigger_set_dirty = False` にするため、**dirty 化はその後**に行う
  （順序を逆にすると Q が無効化される）。
- 起動設定（`_startup_settings` / `startup_path`）は**触らない**（`new_config` と同じ。保存時に
  `save_runtime_data` が更新する）。

## 含まない

- **正本 `spec_detail/` への反映 — task_10**（v0.6-O/P/Q と「非 dirty な子の既定規則」の明記を含む）。
- `new_config` / 読込 / Import / 起動設定変更の挙動変更（**触らない**）。
- v0.4-I を trigger_set へ広げること（2026-07-30 に否定済み）。孤児 trigger_set・陳腐化した
  `_parent_refs` の掃除（**idea_07**・β 完了後）。
- 別名保存ダイアログの初期ファイル名を例専用にすること（v0.6-O で不採用。`new_config` と同じ既定名）。
- `config/example/` の新設（v0.6-O で不採用）。
- 保存計画・一覧ダイアログ・依存確認の仕様変更。

## 確認

`.venv` の python で実行する（worktree ルートから `..\..\..\.venv\Scripts\python.exe`）。

1. `-m compileall -q keyseq main.py tests tests_ui` が clean
2. `-m unittest discover -s tests` が全 pass（現行 142 件）
3. `-m unittest discover -s tests_ui` が全 pass（現行 147 件 + 追加分）・**完走する**（ハングしない）
4. `-m tests.smoke_app` が pass
5. **受入条件 24・24b・25・26**: 上記テスト 1〜5 が pass
6. 既存の特性テスト（保存 JSON のバイト列比較）を**緩めずに** pass すること

## 完了条件

- 上記確認 1〜6 が pass・**reviewer 採用**。
- 実機目視（読込 → 例を復元 → 保存で別名保存ダイアログが出る / 旧ファイルが不変）は
  **task_10 の前にユーザーがまとめて実施**する。本タスクでは実施しない。
