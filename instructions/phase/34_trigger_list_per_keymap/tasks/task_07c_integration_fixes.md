# task_07c_integration_fixes

## 目的

統合レビュー（task_08 前・deep-reviewer / codex-reviewer）で見つかった不具合を直す（ユーザー承認 2026-09-26「A」）。
仕様（暫定 25 v0.6）の変更は伴わない（仕様変更は task_07d）。**JSON スキーマ不変**。

## 対象範囲

### H-1 保存で選択行・実行位置が先頭に戻る（両レビュー共通）

- `keyseq/application/keymap_service.py:47-56`（`get_trigger_set_id`）: キャッシュのキーを `f"trigger-list:{id(triggers)}"` から
  **共有グループの代表キーマップの id**（`keymap_triggers.trigger_set_owner(data, keymap_id)["id"]` 相当）へ変える。
  一括保存（`keymap_set_io.py:130` で `app.data` が正規化後の新しいデータへ差し替わる）・個別保存（`trigger_set_file_io.py` の実体差し替え）の前後で変わらないこと。
- `AppState.forget_trigger_set` 等、キーの破棄箇所をキーの変更に合わせる（削除で代表が変わる場合の扱いを含む）。
- 回帰テスト: **一括保存・個別トリガー一覧保存の前後で、選択行と実行位置（`_indices`）が保たれる**。連続実行中の保存で位置が先頭に戻らない。

### M-1 キーマップの個別読込で共有した一覧が未保存の印を引き継がない

- `keymap_file_io.py:260-269` 付近のキャッシュ（triggers, refs, source）に**未保存・読込済みの印（`_trigger_set_dirty` / `_trigger_set_imported`）も含める**か、
  `add_imported_keymap` の成功後に共有グループの状態を同期する（トリガー一覧の個別読込の `_sync_loaded_trigger_set_state` と同じ扱い）。
- テスト: 未保存の編集がある一覧を持つ A と共有する形で B を個別読込 → A を削除 → 一括保存で一覧が保存対象の行に出る（編集が失われない）。

### M-2 ファイル未作成の一覧を「保存しない」にすると同名の他ファイルを索引する

- `split_payloads.py:103-105` 付近: トリガー一覧の索引を、keymap（`:201-207`）・sequence（`:283-288`）と同じく
  **「保存しない」のときは source_path が存在する場合だけ索引し、それ以外は `""`** にする。
- テスト: source なしの一覧・既定保存先に他の構成セットの同名ファイルあり・「保存しない」→ keymap の `trigger_set_path` が `""`（他ファイルを指さない）。

### C-2 共有一覧の個別保存で `_parent_refs` に代表しか入らない

- `trigger_set_file_io.py:82-84` 付近: 共有しているトリガー一覧を個別保存するとき、**共有メンバー全員の keymap 保存先**を親として記録する
  （一括保存の `split_payloads.py` と同じ扱い。保存先がまだ無いメンバーは一括保存と同じ規則に従う）。
- テスト: A・B が共有する一覧を新しいパスへ個別保存 → そのファイルの `_parent_refs` に A と B の両方。

### テスト追加（L-6）・BOM（L-5）

- §10-19: 単一 JSON を Export → Import → **一括保存 → 再読込**してもキーマップごとのトリガー一覧が保たれる。
- §10-6: 新規作成（`new_config` の経路）でキーマップが 1 つある。
- `keyseq/domain/config.py:1` で除去された BOM を元に戻す（phase 34 と無関係の変更。`git diff b27336e -- keyseq/domain/config.py` の先頭行を確認）。

## 読むファイル

- `keyseq/application/keymap_service.py:40-60` / `keyseq/domain/keymap_triggers.py` / `keyseq/application/app_state.py` / `keyseq/presentation/app.py:220-250`
- `keyseq/presentation/controllers/config_io/{keymap_file_io,trigger_set_file_io,keymap_set_io}.py`（該当行の前後）
- `keyseq/application/config_service/split_payloads.py:60-110, 195-210, 280-290`
- 手本のテスト: `tests_ui/test_task06_keymap_management_ui.py` / `tests/test_per_keymap_bulk_save.py`（冒頭）

## 含まない

- 暫定 v0.6 の仕様変更（トリガー優先・移行の改訂・二重読込禁止・重なり判定の表化）= **task_07d**
- `config_service/__init__.py` の分割（task_08 の `/refactor_check`）/ `instructions/` 配下の編集

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq` clean
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` 全 pass（skip 7）/ `tests_ui` 全 pass（`timeout 900`・ハングなし）/ `tests.smoke_app` pass
- `git diff b27336e -- keyseq/domain/config.py | head -5` で BOM の差分が無いこと

## 完了条件

- 上記確認 pass・**reviewer 採用**。
