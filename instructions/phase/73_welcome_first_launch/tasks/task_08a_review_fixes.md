# task_08a_review_fixes

## 目的

task_08 の二次レビュー（deep-reviewer・codex-reviewer）で採用した指摘を直す（ユーザー判断 2026-11-09「推奨どおり」・decisions.md「task_08 二次レビュー」）。
**domain（キー名の正規化の分離）+ application（孤児の掃除の参照元）+ presentation（復元・再表示の modal）+ テスト・JSON スキーマ不変**。

## 対象範囲

### 1. 「サンプルを復元」で配列を保つ（暫定 56 §5.3）— `keyseq/presentation/controllers/config_io/keymap_set_io.py` `restore_default`

- 差し替えの前の `keyboard_layout`・`external_keyboard_layouts`・`keyboard_show_physical_key_labels` を覚え、`new_default_data()` の後に写し戻す（他の項目はサンプルのまま）
- テスト（tests_ui の既存の復元のテストの近く）: JIS を登録した構成で復元 → `keyboard_layout == "jis"`・登録が残る・フックのキーはサンプル（F12 / F1）

### 2. 再表示の Welcome を本体の子のモーダルに（暫定 56 §7）— `keyseq/presentation/welcome/welcome_window.py`

- `reopen=True` のときは `grab_modal(self, self.master, focus=...)`（親を渡す・`transient` になる）。初回（`reopen=False`）は今のまま（親を渡さない）
- テスト: 再表示の窓の `transient()` が本体・初回は空（既存のテストを保つ）

### 3. `minus` → `-` の読み替えをキーの名前だけに絞る（codex-reviewer P2）— `keyseq/domain/config.py` ほか

- 新設 `normalize_identifier(value: str) -> str`（`strip().lower()` だけ・読み替えなし）を `config.py` に置く
- **キーの名前でない値**の正規化を `normalize_identifier` に替える: キーマップの id（`_normalize_keymaps`・`active_keymap_id`・`keymap_switch_keys` の値〔切替先の id〕）、
  application の `split_payloads.py` / `save_plan_execution.py` / `keymap_service.py` / `input_router.py:124` の id の比較、`input_router.py:94` の `event_type`、
  ファイル名からの id の生成（`config_service/__init__.py` の `_generate_keymap_id` 付近）。grep で `normalize_key_name(` / `coerce_key_name(` の呼び出しを全部見て、**キーの名前か id・種別か**で仕分ける
- **キーの名前**（トリガーのキー・置換元 / 置換先・切替キー・停止 / トグルキー・ホットキーのトークン）は今のまま `normalize_key_name`（読み替えあり）
- 仕分けた結果（替えた呼び出し・替えなかった呼び出し）の一覧を完了報告に書く
- テスト: id が `"minus"` のキーマップと `"-"` のキーマップが両方残る（読込）・`active_keymap_id == "minus"` がそのまま・既存の task_01 のテスト（キーの名前の読み替え）は通る

### 4. 書き出し → 読込の通しのテスト（受け入れ条件 §10 の 4）— tests/

- 一時フォルダを `config_root` に、`ConfigService.install_sample(..., keyboard_layout_id="jis", external_layout_path="user/keylayout/jis.json")` → `load_runtime_data_from_keymap_set_path(<sample.json>)` で、
  キーマップ 3・`active_keymap_id == "keymap_1"`・shortcut のトリガー r/c/v/t/a・`hook_keys_individual` True・F12 / F1・`keyboard_layout == "jis"`・登録あり・ラベルが今の言語（ja と en で 1 回ずつ）

### 5. 孤児の掃除の参照元にサンプルを足す（deep 指摘 3）— `keyseq/application/config_service/orphan_scan.py`

- 参照元の一覧（`:105-110` 付近の `user/keymap_sets/*` を集める処理）に `config/sample/keymap_sets/*` も足す（あれば）。孤児の**候補**の範囲（`candidate_dirs`）は変えない（`config/sample/` の中身は候補にしない）
- テスト: サンプルの構成セットだけが参照する `user/keymaps/<追加>.json` が孤児の候補にならない

### 設計メモ / 制約

- 1〜5 以外は変えない。ソースに日本語の文言を書かない。テストの期待値を緩めない
- 3 は呼び出し箇所が多い。キーの名前の経路の挙動は 1 つも変えないこと（迷う呼び出しは替えずに報告）

## 読むファイル

- `keyseq/presentation/controllers/config_io/keymap_set_io.py:675-700`
- `keyseq/presentation/welcome/welcome_window.py`（全体・小さい）・`keyseq/presentation/modal.py:122-140`
- `keyseq/domain/config.py:100-140`・`:355-410`
- grep: `normalize_key_name(` / `coerce_key_name(`（keyseq 全体。呼び出しの前後数行だけ読む）
- `keyseq/application/config_service/orphan_scan.py:90-130`・`candidate_dirs.py`（候補の範囲の確認のみ）
- 手本のテスト: `tests/test_sample_install.py`・`tests/test_domain_config.py` の minus のテスト・`tests_ui/test_config_io_characterization_keymap_set_startup.py` の `test_restore_default_keeps_sample_hook_keys_over_global_defaults`・`tests_ui/test_welcome_window.py`
- 孤児の掃除の既存のテスト 1 つ（`tests/` で `scan_orphans` を使うもの・数十行）

## 含まない

- 目視で決める項目（送ったキーの拾い直し・JIS の記号キーの名前）と受容の項目（task_09 で正本に明記）
- 正本の更新（task_09）

## 確認

- 追加・変更したテストが通る（verifier が `.venv` で実行）
- `python -m compileall -q keyseq`・`python -m unittest discover -s tests`・`python -m unittest discover -s tests_ui`・`python -m tests.smoke_app` が通る

## 完了条件

- 上記確認 pass・**reviewer 採用**
