# task_09e_mac_modifier_key_names

## 目的

暫定 57 v0.11 §5.3.4 の「Mac のキー名」を実装する。Mac の Command / Option を `command` / `left command` / `right command` / `option` / `right option`（Windows の語彙の `windows` → `command`・`alt` → `option` の語単位の置き換え）で受信・送信・記録し、§5.3.3 の表示名の差し替え（task_09a / 09c）を撤去する。Mac の既定データ（§8 Q2）を新しい名前にする。

- 変更は Mac の backend（`os_backend/macos/`）・domain の修飾キーの語彙と Mac の既定データ・application の修飾キーの表・presentation の Tk の記録と表示の差し替えの撤去。**Windows の受信名・送信・表示は変えない**（他方の名前の拒否は task_09f）。
- domain / application / presentation は OS を判定しない（Mac の名前は backend から得るか、OS 非依存の語として表に足す）。

## 対象範囲

### Mac の backend（`keyseq/infrastructure/os_backend/macos/`）

- `key_table.py`: 受信の表（:29-31 の vk 54 / 55 / 58 / 61）を `right command` / `left command` / `option` / `right option` に。送信の別名 `_SEND_ALIASES`（:88-93）の `windows` → `command`・`left alt` → `left option`。`MODIFIER_NAMES`（:96-101）にレイアウトの id `command_l` / `command_r` / `option_l` / `option_r` → `left command` / `right command` / `option` / `right option` を足す。**既存の id `windows_l` / `windows_r` / `alt_l` / `alt_r` の行は今の名前（`left windows` 等）のまま残す**（Windows 用の見本の Win / Alt の枠が Mac で task_09f の拒否に当たり、§5.3.2 v0.11「割り当てに使えない」が成り立つため・起票レビュー L1）。`keyboard_window.py` の `_LOOKUP_KEY_BY_ID` も同じ扱い。
- `backend.py`: `modifier_display_names`（:402）を外す。物理の修飾キーの状態・送るフラグ（`macos/modifier_state.py` の `modifier_flags`）は vk で判定しキー名を見ないため変更しない（起票レビュー L1）。
- Tk の記録: aqua の `Meta_L` / `Meta_R` → `command` 系・`Alt_L` / `Alt_R` → `option` 系（`key_hold` は左右つき）を、backend の `TkKeyTranslator`（`contracts.py:101-104`）に口を 1 つ足して返す（例 `modifier_name(keysym: str, *, sided: bool) -> str | None`。Windows は今の表の結果を返す）。

### presentation

- `tk_keys.py`: `normalize_tk_keysym` / `normalize_key_hold_tk_keysym` の修飾キーの名前を上の backend の口から得る（presentation で OS を判定しない）。
- `action_dialog.py`: hotkey の修飾キーの並び順（`_update_hotkey_preview` の `order`・`ctrl` → `alt` / `option` → `shift` → `windows` / `command`・§5.3.4）と、集める名前（`option` / `command` を集める）だけを本タスクで変える。`:453` の判定を `is_modifier_key` へ置き換えるのは task_09f（起票レビュー L2）。task_09f までの間、トリガー等の記録で Option / Command 単独が確定するのは既知の中間状態（目視は 09f の後）。
- `keyboard_window.py:40-50` の `_LOOKUP_KEY_BY_ID`: `command_l` / `command_r` / `option_l` / `option_r` を backend の名前で引けるようにする（Mac 用の見本は task_09b で作る）。
- **表示名の差し替えの撤去**（§5.3.4「廃止するもの」）: `display_modifier_names` / `display_key_name` の修飾キーの差し替えと `set_modifier_display_names` の注入（`app.py`）・`OsBackend.modifier_display_names`（`contracts.py:131`・両 backend）・`ui_vars.py` の表示用の変数と hook_frame（full / compact）の `textvariable`・ダイアログの表示用の変数を外し、task_09a 以前の表示（キー名そのもの）に戻す。参照箇所は `grep -rn "display_modifier_names\|display_key_name\|modifier_display_names\|display_var" keyseq` の全件（2026-11-15 時点で 27 ファイル）。`display_key_name` が記号キーの表示（phase 74）も兼ねている場合は、記号の部分を残して修飾キーの差し替えだけを外す。

### domain / application

- `domain/key_symbols.py`: 修飾キーの表示名の差し替え（task_09a で足した表と関数）を外す（上の撤去と同じ）。
- `domain/default_profile.py:35-47`（Mac の既定）: `windows` → `command`・`alt` → `option`（プリセット 8 件の値・サンプルの行の選択・コピー・貼り付け・アプリの切替）。ラベル（`Command+Tab` 等）は変えない。Windows の既定は変えない。
- `domain/key_hold.py` の `MODIFIER_KEY_NAMES`・`domain/key_identifiers.py` の割り当て禁止（`command` / `left command` / `right command` を足す・§8 Q5）・`application/key_state_manager.py:26-34` の左右の寄せ（`command` 系 → `command`・`option` 系 → `option` を足す）・`application/input_router.py:160-161` の修飾キーの一覧: `left command` / `right command` / `left option` / `right option` 等の不足を OS 非依存の語として足す。
- サンプルの構成セット（`config_service/sample_install.py`）: `:33-55` は keymap / sequence の ID と保存先だけでキー名を持たず、キー名は `default_profile.py` から来る見込み。そうであることを確かめて報告する（固定の JSON にキー名があれば、Mac 用を新しい名前で用意するかを報告して止める・§5.3.4「既定データとサンプル」）。

## 読むファイル

- `instructions/history/57_mac_support.md` §5.3.4・§8 Q2・Q5
- `keyseq/infrastructure/os_backend/macos/key_table.py`・`macos/backend.py`（修飾キーと `MacTkKeyTranslator` の範囲）・`os_backend/contracts.py:95-135`
- `keyseq/presentation/tk_keys.py`・`action_dialog.py:440-490`・`keyboard_window.py:40-60`
- `keyseq/domain/key_symbols.py`・`domain/default_profile.py`・`domain/key_hold.py:20-45`・`domain/key_identifiers.py`
- `application/key_state_manager.py:20-40`・`application/input_router.py:150-170`
- 撤去の参照箇所は grep の結果の該当行だけ

## 含まない

- 両 OS で他方の名前を拒否する受付の口と、その入口（置換元・トリガー・hotkey / key_hold の保存・切替 / 停止 / トグルの記録）・修飾キー単独の読み飛ばしの統一（task_09f）
- Mac 用のレイアウトの見本の JSON（task_09b）
- 既存の設定の変換（§5.3.4・しない）・正本の反映（task_14）
- 割り当て禁止の文言の Mac 向けの言い換え（task_11）

## 確認

Mac（verifier）:
- tests: 受信の表（vk 55 → `left command`・58 → `option`・61 → `right option`・54 → `right command`）・送信（`command+c` が vk 55 のフラグつきで送られる・`option` / `left option` が解決できる）・Tk の口（aqua の `Meta_L` → `command`・`key_hold` は `left command`）・Mac の既定データの値・`is_modifier_key("left option")` 等・割り当て禁止に `command` 系・`key_state_manager` の寄せ。表示の差し替えを前提にした既存のテスト（task_09a / 09c で足したもの）は撤去に合わせて外すか期待値を戻し、外した件数を報告。
- compile clean・`tests` が基準線から増えない・smoke pass・`tests_ui` の触れたモジュールに関係するものを 1 本ずつ。
Windows（verifier）: compile clean・tests 失敗 0・`tests_ui` 失敗 0（1 本ずつ）・smoke pass（Windows の名前・表示が不変）。

## 完了条件

- 上記確認 pass・**reviewer 採用**。`codebase_map.md` の `key_symbols`・`ui_vars`・backend の行を追従（メイン）。
- 実機目視（Mac）は task_09f の後にまとめて行う（§9 の 13〜15。task_09c の目視もここで代える）。

## 起票レビュー

reviewer「修正して採用」（2026-11-15）: 中 2（M1 = 09d のフォールバック先の誤り・M2 = 09d のレイアウトの受け取りと key_hold のファイル名）・低 3（L1 = 09e の modifier_flags と既存 id の扱い・L2 = 09e / 09f の action_dialog の分担・L3 = 09f の tests_ui の指定）を反映（ユーザー「反映してコミット」）。
