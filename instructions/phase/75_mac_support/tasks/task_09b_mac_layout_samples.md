# task_09b_mac_layout_samples

## 目的

Mac 用のキーボードレイアウトの見本 2 つ（US / JIS）を足す（暫定 57 §5.3.2・v0.8 / v0.11）。既存の見本（`jis` / `us_tkl` / `de`）は Windows 用キーボードの並びと表示名で、Mac の Command / Option の位置が無い。

- データ（JSON）とそのテストだけ。コード・JSON の形式・スキーマは変えない（§8 Q7）。レイアウトの読み込み・登録の仕組みは今のまま（ユーザーがキーボードUIの「レイアウトの追加」でファイルを選ぶ）。
- 修飾キーの id は v0.11 の `command_l` / `command_r` / `option_l` / `option_r`（task_09e で `keyboard_window._LOOKUP_KEY_BY_ID` と Mac の `key_table.MODIFIER_NAMES` に追加済み）。

## 対象範囲（データとテストのみ）

> **v0.12 で改訂**: fn・矢印・jis_mac の右 Option の扱いは末尾「実装後の改訂」節が優先する（fn は禁止のキーとして置く・矢印は右 Shift の下・jis_mac は右 Option の位置が fn）。

### `config/user/keylayout/us_mac.json`（新規・`layout_id` = `us_mac_sample`・`display_name` = `US (Mac)`）

Apple の内蔵キーボード（US・Touch ID つきの現行機）の並び。`label` は Mac の印字。
- 1 段目: `esc`・`f1`〜`f12`（PrtSc / Scroll / Pause は置かない）
- 2 段目: `` ` ``・`1`〜`0`・`-`・`=`・`backspace`（label `delete`）
- 3 段目: `tab`・`q`〜`p`・`[`・`]`・`\`
- 4 段目: `caps lock`（label `caps lock`・禁止の色になる）・`a`〜`l`・`;`・`'`・`enter`（label `return`）
- 5 段目: `shift_l`（label `shift`）・`z`〜`m`・`,`・`.`・`/`・`shift_r`
- 6 段目: **fn の位置は空ける**・`ctrl_l`（label `Control`）・`option_l`（label `Option`）・`command_l`（label `⌘ Command`）・`space`・`command_r`・`option_r`・矢印（`left`・`up` と `down` は半分の高さで上下に重ねる・`right`）
- 置かない: fn・Insert / Home / End / PgUp / PgDn / Delete（前方削除）・テンキー・Menu・`ctrl_r`
- 記号キーの id は `us_tkl.json` と同じ。`scan_code` は書かない（`us_tkl.json` と同じく、名前で決まる）。

### `config/user/keylayout/jis_mac.json`（新規・`layout_id` = `jis_mac_sample`・`display_name` = `JIS (Mac)`）

Apple の内蔵キーボード（JIS・Touch ID つきの現行機）の並び。
- 1 段目: us_mac と同じ（`esc`・`f1`〜`f12`）
- 2 段目: `1`〜`0`・`-`・`^`・`yen`（label `¥`・`scan_code` 125）・`backspace`（label `delete`）
- 3 段目: `tab`・`q`〜`p`・`@`・`[`・`enter`（label `return`・縦長は 4 段目まで）
- 4 段目: `ctrl_l`（label `Control`）・`a`〜`l`・`;`・`:`・`]`
- 5 段目: `shift_l`・`z`〜`m`・`,`・`.`・`/`・`ro`（label `_`・`scan_code` 115）・`shift_r`
- 6 段目: 左端から `caps lock`（label `caps`）・`option_l`・`command_l`・`muhenkan`（label `英数`・`scan_code` 123・`extra_scan_codes` [241]）・`space`・`henkan`（label `かな`・`scan_code` 121・`extra_scan_codes` [242]）・`command_r`・fn の位置は空ける・矢印（US と同じ）
- **`yen` と `ro` を必ず置く**（task_09 の JIS の判定 = id に `yen` か `ro` があること・`key_table.is_jis_layout`）。記号キーの id は `jis.json` と同じ。`scan_code` は `jis.json` と同じ値のキーにだけ書く。
- 並びの細部（6 段目の caps / control の位置・return の形）は機種で違う。上は現行の内蔵キーボードを想定した案で、Mac の実機目視でユーザーのキーボードと照合し、違いは報告して直す。

### 共通

- 座標・幅は `jis.json` / `us_tkl.json` の単位（1.0 = 1 キー・段の間 1.2 の流儀）に合わせる。キーが重ならないこと。
- `key_display_names` は必要なものだけ（無ければ省く）。
- `label` は §5.3.2 の例（`⌘ Command`・`Option`・`Control`・`英数`・`かな`・`delete`・`return`）に合わせる。`ui_terms.md`（`instructions/common/spec_detail/`）の表記と食い違えば報告する。
- `config/` は `.gitignore` の対象。既存の見本と同じくコミットは `git add -f`（メイン）。
- 既存の 4 本の JSON は変えない。

### `tests/test_keyboard_layout_files.py`

- 2 本を既存の検査の対象（ファイル先頭のレイアウトの dict）に足す。
- `_NO_SCAN_CODE_IDS`（修飾キー等に scan_code が無いことの検査）に `command_` / `option_` を足す。
- 追加の検査: us_mac は全キーで scan_code が無い・jis_mac の scan_code は `jis.json` の同じ id と同じ値・2 本とも `load_layout_from_json` で読める・id の重複なし・キーの矩形が重ならない・`command_l` / `command_r` / `option_l` / `option_r` があり `windows_*` / `alt_*` / `fn` が無い・`jis_mac` は `is_jis_layout` が真で `us_mac` は偽・`caps lock` がある。

## 読むファイル

- `instructions/history/57_mac_support.md` §5.3.2（v0.8・v0.11 の改訂）・§5.3.4 の表
- `config/user/keylayout/jis.json`・`us_tkl.json`（形式と座標の流儀の手本）
- `tests/test_keyboard_layout_files.py`（全体）
- `keyseq/presentation/keyboard_layouts.py:280-300`（`keyboard_layout_from_dict` の検査）
- `keyseq/infrastructure/os_backend/macos/key_table.py:96-121`（`MODIFIER_NAMES`・`is_jis_layout`）

## 含まない

- ウェルカム画面で Mac のときに Mac 用の見本を選ばせること・初回のコピー（§6.1・ビルド段階 task_12）
- 見本の同梱（task_13）
- JIS の英数 / かなの受信の実測（§9 の 10・JIS キーボードがあるとき）
- Caps Lock の Mac での扱い（別の未決）

## 確認

Mac（verifier）: compile clean・`tests.test_keyboard_layout_files` pass・`tests` が基準線（失敗 6・エラー 10）から増えない・smoke pass。
Windows: task_09〜09f の Windows 検証と合わせて `tests.test_keyboard_layout_files`。

## 完了条件

- 上記確認 pass・**reviewer 採用**。`codebase_map.md:853` の見本の一覧に us_mac / jis_mac を追記（メイン）。
- 実機目視（Mac・本タスクで実施・§9 の 13）: キーボードUIの「レイアウトの追加」で `us_mac.json` / `jis_mac.json` を選ぶと Mac の並びと印字で出る・ユーザーのキーボードと並びを照合（違いは報告）・Command と caps の枠は禁止の色で編集が始まらない・Option の枠をクリックするとタイトルに編集中のキー名（`option` / `right option`）が出る・Option / Control の枠で割り当てた置換が動く・`jis_mac` 選択中に `@` の枠で割り当てた置換が、物理の `@` の位置のキーで動く（JIS の受信名）。

## 起票レビュー

reviewer「修正して採用」（2026-11-15）: 中 1（codebase_map の追従先を確定形に）・低 3（`git add -f`・scan_code の検査・jis_mac の 1 段目と 6 段目の左端の明記）を反映。加えてメインが label を §5.3.2 の例（大文字始まり）に合わせた。

## 実装後の改訂（2026-11-15・Mac 目視・暫定 57 v0.12）

ユーザー: 矢印は右 Shift の下の空きに置いてよい・JIS の右 Option の位置には fn がある・fn はグレーアウトで置いてよい。→ fn を id `fn` で実機の位置（US = 左下・JIS = 右 Option の位置。jis_mac から `option_r` を外す）に置き、`domain/key_identifiers.py` の割り当て禁止に `fn` を足して禁止の色にする。矢印は x = 12〜14（右 Shift の下）。テストは fn と caps lock の存在・jis_mac に `option_r` が無いこと・`fn` が割り当て禁止であることを検査。その他の目視項目は OK。
