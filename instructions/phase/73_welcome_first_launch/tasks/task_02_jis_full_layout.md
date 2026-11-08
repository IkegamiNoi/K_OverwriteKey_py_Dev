# task_02_jis_full_layout

## 目的

Welcome で選べる JIS の配列として、全キーを持つ JIS の配列ファイルを用意する。今の一部のキーだけの見本は、テスト用として名前を変えて残す（暫定 56 §5.4・§2）。
**データファイル（`config/user/keylayout/`）とテストのみ・keyseq のコード不変・JSON スキーマ不変**（配列ファイルの書式は既存のとおり）。

## 対象範囲（配列ファイル 2 つ + テストの参照の追従）

### `config/user/keylayout/jis_test.json`（今の `jis.json` を改名）

- 今の `jis.json` の中身をそのまま新しいファイルへ写す（`jis.json` 自体は下の全キーの内容で書き直す）。変えるのは `layout_id` を `"jis_test"`、`display_name` を `"JIS（テスト用）"` にすることだけ（`jis` と同時に登録しても衝突しないため）
- キーの行・`scan_code`・`extra_scan_codes`・`key_display_names` は変えない

### `config/user/keylayout/jis.json`（新規・全キー）

- `layout_id: "jis"`・`display_name: "JIS"`。書式は `us_tkl.json` と同じ（`keys` の各行に `id` / `label` / `x` / `y` / `w` / `h`、必要な行だけ `scan_code` / `extra_scan_codes`）
- **範囲は `us_tkl.json` と同じ TKL**（テンキーなし）: Esc・F1〜F12・Print Screen / Scroll Lock / Pause・数字の段・Tab の段・Caps の段・Shift の段・最下段・Insert〜Page Down の 6 キー・矢印。
  JIS の物理の並び（数字の段の 13 キー + Backspace、Enter は 2 段の逆 L 字〔今の見本の `enter` と同じく 2u×2u で表してよい〕、右 Shift の左に「ろ」、Backspace の左に「¥」、最下段に 無変換・変換・かな）
- **キーの `id`（＝名前）の付け方**（`key_input.md` §7.1「フックの実行時のキー名の出どころ」に従う）:
  - 文字・数字・記号のキーは、JIS 配列の Windows で `keyboard` の `event.name` が出す文字を `id` にする（例: `-`・`^`・`@`・`[`・`;`・`:`・`]`・`,`・`.`・`/`）。`scan_code` は書かない（US TKL の見本と同じ扱い）
  - 今の見本に `scan_code` があるキー（半角/全角 41・無変換 123 + `extra_scan_codes` [241]・変換 121 + [242]・かな 112）は、**見本と同じ `id`・`scan_code`・`extra_scan_codes`・`label`** にする
  - JIS だけにあるキー「¥」（走査コード 125）と「ろ」（走査コード 115）は `scan_code` を書き、`id` は `yen` / `ro` にする（`event.name` の文字が環境で揺れるため。名前はレイアウトが決める＝phase 62）
  - 修飾・制御のキーの `id` は `us_tkl.json` と同じ（`shift_l` / `ctrl_r` / `caps lock` / `print screen` 等）
  - `key_display_names` は今の見本と同じ（`zenkaku_hankaku`）
- `label` は刻印の表記（英字は大文字・JIS の記号は記号そのまま・「¥」「ろ」「無変換」「変換」「かな」「半角\n全角」）
- 座標は 1u 単位で、行の y は `us_tkl.json` に合わせる（0.0 / 1.2 / 2.2 / 3.2 / 4.2 / 5.2）。キー同士が重ならないこと

### テスト（tests / tests_ui）

- **見本の中身（一部のキーだけ・特定の行や座標）を前提にしているテスト**は参照先を `jis_test.json` に、`layout_id` の期待値を `jis_test` に変える。
  候補: `tests/test_keyboard_layout_files.py:18,151,196,255,283-286`・`tests/test_layout_controller_scan_code.py:19`・`tests_ui/test_app_ui_flows.py:2537,2793,2882,2972`・
  `tests_ui/test_keyboard_key_text.py:21`・`tests_ui/test_keyboard_window_scan_code.py:16`・`tests_ui/test_make_only_key_color_ui.py:18`
  （それぞれ中身を読んで、全キーの `jis.json` でも成り立つなら変えなくてよい。変えた / 変えなかった理由を完了報告に書く）
- パスの文字列だけを扱うテスト（`tests/test_config_service.py:1958-1983`・`tests/test_layout_controller_registration.py` の `"user/keylayout/jis.json"` 等。ファイルの中身を読まない）は変えない
- 新しいテスト（`tests/test_keyboard_layout_files.py` に追加）:
  - `jis.json` が読み込め、`layout_id == "jis"`
  - キーの `id` に重複がない・キーの矩形が重ならない
  - Welcome のサンプルで使うキーがすべてある: `1` `2` `3` `q` `w` `e` `r` `t` `a` `s` `d` `f` `g` `z` `x` `c` `v` `b` `h` `f1` `f12`
  - `zenkaku_hankaku` / `muhenkan` / `henkan` / `kana` の `scan_code`・`extra_scan_codes` が見本と同じ・`yen` = 125・`ro` = 115
  - `jis_test.json` の `layout_id == "jis_test"`

### 設計メモ / 制約

- keyseq のコード・ヘルプの本文は変えない（ヘルプが見本として挙げる `jis.json` は、全キーになっても特殊キーを含むので記述は正しいまま。`test_help_content.py:113` も不変）
- `de.json` は触らない（スコープ外）
- 既存の利用者が `user/keylayout/jis.json` を登録済みなら、更新後は全キーの JIS になる（意図どおり・暫定 56 §5.4）

## 読むファイル

- `config/user/keylayout/jis.json`（全体・小さい）/ `config/user/keylayout/us_tkl.json`（全体・書式と座標の手本）
- `instructions/common/spec_detail/key_input.md` §7.1（「フックの実行時のキー名の出どころ」の段落のみ）
- `instructions/common/spec_detail/features.md` §4.6「キーボード表示のウィンドウ」のうちレイアウトの JSON の書式（`label` の改行・`key_display_names`・`scan_code`・`extra_scan_codes`）の段落のみ
- 上の「候補」に挙げたテストの該当箇所（各数十行）
- 配列の読込: `keyseq/presentation/keyboard_layouts.py` の `load_layout_from_json` と検証（該当関数のみ・重なりや必須キーの検査の有無を確かめる）

## 含まない

- Welcome での配列の選択と、外部の配列としての登録（task_04〜06）
- サンプル（既定データ）の変更（task_03）
- ヘルプの本文・正本の更新（正本は task_09）
- `de.json` の作り直し（スコープ外）

## 確認

- 追加・変更したテストが通る（verifier が `.venv` で実行）
- `python -m compileall -q keyseq`・`python -m unittest discover -s tests`・`python -m unittest discover -s tests_ui`・`python -m tests.smoke_app` が通る
- `jis_test.json` の内容が改名前の `jis.json`（HEAD）と `layout_id` / `display_name` 以外で一致する（メインが `git show HEAD:config/user/keylayout/jis.json` と比べる）

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視（JIS の Windows で全キーのキーボード表示・キーを押して名前が合うか）は task_09 でまとめて実施
