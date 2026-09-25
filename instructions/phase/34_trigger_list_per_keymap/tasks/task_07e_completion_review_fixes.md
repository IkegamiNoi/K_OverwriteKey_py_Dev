# task_07e_completion_review_fixes

## 目的

フェーズ完了判定前レビュー（deep-reviewer / codex-adversarial・2026-09-27）の指摘と、暫定仕様 25 **v0.7** のユーザー判断（§2-28〜31）を実装する。
正本は `instructions/common/spec_detail/`（data_schema §5.13.3・5_08_03・5_08_07・key_input §7.3）に反映済み。**JSON スキーマ不変**。

## 対象範囲

1. **H-2 実行位置の初期化**: `keymap_set_io.py:540-541`（通常読込・履歴からの読込）と `:634-635`（例の復元）の `self._app._indices = {}` /
   `_selected_trigger_idx = 0` を `self._app.state.reset_indices()` に揃える（新規作成・Import・起動時読込と同じ）。
2. **codex High 共有に加わった一覧の親参照**: トリガー一覧の個別読込・キーマップの個別読込で、**既存の一覧の実体を共有した**ときはその一覧を未保存（`_trigger_set_dirty`）にし、
   次の保存で trigger_set が書かれ `_parent_refs` に新しいキーマップが加わるようにする（`trigger_set_file_io._apply_loaded_trigger_set` / `keymap_file_io` の共有経路）。
3. **§2-28 アクティブが `""` を持つ場合も新キーマップへ移す**: `split_loading.py:455-463` の `_migrate_legacy_trigger_set` で、`has_trigger_set_path` が真なら
   値が空でも（`elif active_source:` → `else:`）新キーマップを自動作成して移行扱いにする（`same` の判定は従来どおり先）。
4. **§2-29 移行した trigger_set の行も「保存しない」不可**: `child_save_rows.py`（`allow_skip`）と保存計画の検証（移行先キーマップと同じ扱い）。
5. **§2-30 アクションが空のトリガー**: 入力判定は現行どおり（空なら置換へ）。コードの変更は不要の見込み。仕様どおりであることを確かめるテストを 1 本足す。
6. **§2-31 切替中の受け付け停止**: `input_router.py` が直接切替（`SelectKeymapAction`）を返すときに「切替中」の印を立て（フックのスレッドで同期的に）、
   印がある間は停止 / トグル以外のキーを**処理せず素通し**（`InputRoute()` を返す・待ち行列に入れない）。UI スレッドで切替の処理
   （`ActionExecutor` の `SelectKeymapAction` 実行 → アクティブ変更・再描画・重なりの表の作り直し。**拒否された場合も**）が終わったら印を下ろす。
   印は App（または AppState）が持ち、スレッド間で読み書きするので単純な bool（または `threading.Event`）とし、UI スレッドの例外で下ろし漏れないよう try/finally で下ろす。
   フック停止・キーマップ一時停止など、印が立ったまま残る経路が無いこと（フック開始時にも下ろす）。

### テスト（追加・更新）

- 既存テストの期待値更新は §2-28（`""` でも移行）による `tests/test_per_keymap_triggers_load.py:158` 付近・`tests/test_per_keymap_bulk_save.py:657` 付近のみ。アサーションを緩めない。
  テスト補助で runtime を書き換えない。キーマップ 0 個のフィクスチャを作らない。未モックの実ダイアログを開かない。
- 新規: ①読込・例の復元の後、アクティブ以外のキーマップの実行位置が 0（H-2）②共有に加わった一覧が未保存になり次の保存で `_parent_refs` に新キーマップが入る ③アクティブが `""` → 新キーマップ・通知・保存後 `""`
  ④移行した trigger_set の行で「保存しない」不可 ⑤アクションが空のトリガーと置換元キーが重なると置換が動く ⑥切替中の印: 切替を返した直後の次キー（トリガー・置換）が素通し（`InputRoute()`）・
  停止 / トグルは効く・切替処理の完了（拒否含む・例外時も）で印が下りて次キーが処理される。

## 読むファイル

- `instructions/history/25_trigger_list_per_keymap.md` v0.7 の §2-28〜31
- `keyseq/application/input_router.py` / `keyseq/application/action_executor.py` / `keyseq/application/app_state.py` / `keyseq/presentation/app.py`（フック周り・InputRouter 生成）/
  `keyseq/presentation/controllers/hook_controller.py`（on_input_event）
- `keyseq/application/config_service/split_loading.py:430-500` / `keyseq/presentation/controllers/config_io/{keymap_set_io,trigger_set_file_io,keymap_file_io,child_save_rows}.py`（該当箇所）
- 手本のテスト: `tests/test_input_router.py` / `tests/test_per_keymap_triggers_load.py` / `tests_ui/test_task06_keymap_management_ui.py`（冒頭）

## 含まない

- 提案書 13 のリファクタ / `instructions/` 配下の編集

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq` clean / `tests` 全 pass（skip 7）/ `tests_ui` 全 pass（`timeout 900`）/ `tests.smoke_app` pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。
