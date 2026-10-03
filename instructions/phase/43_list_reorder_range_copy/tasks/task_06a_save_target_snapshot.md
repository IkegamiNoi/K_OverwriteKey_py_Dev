# task_06a_save_target_snapshot

## 目的

保存の計画を作った時点で、対象のトリガー一覧の実体と行の並びを固定し、書き込みの直前に照合する。違えば保存を中止して理由を示す
（暫定 30 v0.6 §5.4 の 2 項目め）。保存ダイアログの表示中も `after` で予約した直接切替などが動くため、計画は一覧 A で作ったのに、
書き込みと後処理では一覧 B を引き直す、というずれが起こりうる。現行の個別保存は、計画（`trigger_set_file_io.py:124`）と
書き込み（`child_file_io.py:97`）・差し替え（`trigger_set_file_io.py:101`）で、アクティブな一覧をそれぞれ引き直している。
**presentation 限定（config_io）。application / domain 不変・スキーマ不変。**

## 対象範囲（presentation 限定）

### `keyseq/presentation/controllers/config_io/save_target_snapshot.py`（新規・tkinter を import しない）

- `@dataclass(frozen=True) class SaveTargetSnapshot`: 固定した対象。トリガー一覧ごとに (代表の keymap の dict・一覧の list の実体・行の dict の tuple) を**オブジェクトの参照のまま**持つ
  （`id()` の数値は持たない。参照を持てば再利用で一致してしまうことがない）
- `capture_all(data) -> SaveTargetSnapshot`: `iter_trigger_sets(data)` の全一覧（一括保存用）
- `capture_active(data) -> SaveTargetSnapshot`: `trigger_set_owner(data)` の一覧だけ（個別保存用）。アクティブな代表も記録する
- `snapshot_matches(data, snapshot) -> bool`: 取り直した結果と比べる。一覧の数・代表・list の実体・行の並びがすべて `is` で同じなら True。
  個別保存用は、アクティブな代表が同じことも条件にする
- 中止の文言の定数 `SAVE_TARGET_CHANGED_MESSAGE` =「保存の準備中にトリガー一覧が変わったため、保存を中止しました。もう一度保存してください。」

### `keyseq/presentation/controllers/config_io/keymap_set_io.py`（一括保存）

- `save_keymap_set_to`: `_collect_child_save_plan` の**前**に `capture_all(self._app.data)` で固定する
- `save_runtime_data` の呼び出し（と、その直前の `relocate_individual_hotkey_presets`・`discard_retained_hook_keys` など data を変える処理）の**前**に照合する。
  違えば何も書かずに `_set_flash_message(SAVE_TARGET_CHANGED_MESSAGE, auto_clear=False)` + `messagebox.showwarning("保存", ...)` を出し、`False` を返す
  （例外にしない。既存の「保存を中止しました。」と同じく中止扱い）

### `keyseq/presentation/controllers/config_io/trigger_set_file_io.py`（個別保存）

- `save_trigger_set_to_path`: `_collect_sequence_save_plan` の**前**に `capture_active(self._app.data)` で固定する
- `_save_trigger_set` の**前**に照合する。違えば上と同じく中止する（書き込みも `_apply_saved_trigger_set` もしない）
- 照合から書き込み・差し替え（`_save_trigger_set` の中の `save_trigger_set_file` → `_apply_saved_trigger_set`）までにイベントループが回らない
  （ダイアログを出さない）ことを保つ。これで照合した一覧と書き込む一覧が同じになる。成功の `messagebox` は差し替えの後のまま

### テスト（追加・修正まで）

- 新規 `tests/test_save_target_snapshot.py`（tkinter 非依存）: 変化なしなら一致 / 行の入れ替え・行の追加・削除・一覧の list の差し替え・
  アクティブの切替（個別保存用）・一覧の追加・削除（一括保存用）ではそれぞれ不一致 / 中身が等しい別オブジェクトへの差し替えも不一致
- tests_ui（既存の保存経路のテストの作り方に倣う。例: `tests_ui/test_config_io_characterization.py`）:
  - 一括保存: 子ファイルの保存ダイアログ（`child_save_dialog.ask_child_save_actions` を patch）の中で、一覧の行の並びを変えてから選択を返す →
    keymap_set のファイルが書かれない・`save_runtime_data` が呼ばれない・中止の文言が出る・`False`
  - 個別保存: 同じダイアログの中でアクティブなキーマップを別の一覧のものへ切り替える → トリガー一覧のファイルが書かれない・
    どちらの一覧の行も差し替わらない・中止の文言
  - 変化が無ければ従来どおり保存できる（既存テストが通ることで確認。必要なら 1 件追加）

### 設計メモ / 制約

- 照合は「同じオブジェクトか」で比べる（`==` で中身を比べない）。中身が等しい別オブジェクトへの差し替えも「変わった」とみなす
- 保存の後処理（`save_runtime_data` の中・`_apply_saved_trigger_set`）は照合の後に同期で走るため、本タスクでは application 側へ固定した一覧を渡す変更はしない
- 関数 30 行の目安。`keymap_set_io.py` / `trigger_set_file_io.py` へは固定と照合の呼び出しの数行だけを足す

## 読むファイル

- 暫定仕様 `instructions/history/30_list_reorder_range_copy.md` §5.4
- `keyseq/presentation/controllers/config_io/keymap_set_io.py:80-180`
- `keyseq/presentation/controllers/config_io/trigger_set_file_io.py:1-170`
- `keyseq/domain/keymap_triggers.py`（`iter_trigger_sets` / `trigger_set_owner` / `trigger_set_members` の定義のみ）
- 手本のテスト: `tests_ui/test_config_io_characterization.py` の保存経路の 1〜2 件（stub と patch の仕方）

## 含まない

- 保存計画の識別子（task_06 で完了）
- トリガー一覧 / キーマップ一覧の操作（task_07・task_08）
- 保存ダイアログの表示中にアクティブの切替そのものを止めること（しない。照合で中止する）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest tests.test_save_target_snapshot` と追加した tests_ui のテストが全 pass
- `-m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。続けて task_06 + 06a の完了判定前に `deep-reviewer` + Codex レビュー（phase.md の方針）。
- **実機目視（本タスクで実施・task_06 の分を含む）**: 同じキーの 2 行（シーケンスが異なる）を一括保存 → 読込で入れ替わらない・消えない /
  個別保存でも同様 / 保存ダイアログに `（N 行目）` が出る / 保存の前後で `▶` と実行位置が変わらない。
