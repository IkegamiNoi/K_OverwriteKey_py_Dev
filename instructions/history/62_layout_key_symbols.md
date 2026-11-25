# 暫定仕様 62: レイアウトごとのキー名の記号の上書き（layout_key_symbols）

> 状態: **未凍結・v0.4・主入力・ユーザー確定済（2026-11-25）・実装着手可**（v0.1 起票時 deep-reviewer「修正して採用」→ v0.2 で反映 / v0.3 で v0.2 の §8 確認事項 5 点をユーザー確定・§2 へ移し節番号を詰めた / v0.4 で Codex 敵対的レビュー〔needs-attention・4 件〕をユーザー判断で反映・警告を一時メッセージ欄の下敷きに〔2026-11-25〕）。本書がこのフェーズの確定設計（フェーズ中は正本を直接改訂しない）。
> フェーズ末タスクで正本 `instructions/common/spec_detail/` へ昇格し本書を凍結する。
> 起票元: idea_63（2026-11-22 phase 75 task_13 の Windows 実機確認の要望）・方向は 2026-11-25 ユーザー確定。番号対応: phase 82 / 暫定 62 / decisions 82。

---

## §1 目的 / 背景

日本語のフォントは半角の `\`（U+005C）を ¥ の形で描くため、キー名 `backslash`・`\`・`ro` の表示（記号キーの表示で `\`）が `yen`（`¥`）と画面で見分けられない。**レイアウトの JSON に、キー名の記号の表示を上書きする任意の表を足し、選んでいるレイアウトのファイルがその表示を決める**。他の言語のフォントの同種の問題（例: 韓国語のフォントの ₩）も、利用者がレイアウトに書けば直せる。

### 現状監査（2026-11-25・起票時レビューで実測）

- 記号の表: `keyseq/domain/key_symbols.py:3` `KEY_SYMBOLS`（`backslash` `\`・`ro` `\`・`yen` `¥`）。`display_key_name`（`:43`）は名前を小文字にして引く。正本 `features.md` §4.6「記号キーのキー名の表示」（`:764` 表は全言語・全レイアウトで共通 / `:767` 配列固有のキーの表示は `key_display_names` に書く）。
- 呼び出し元は 3 つ。
  - トリガー一覧: `domain/config.py:487` `format_trigger_list_item`（キー名を `normalize_key_name` してから引く）← `presentation/controllers/trigger_panel/trigger_panel_controller.py:217` `refresh_triggers`。
  - key_hold の行: `domain/key_hold.py:134,136` `format_key_hold_value`（キー名は `strip().lower()` だけ・`:85`）← `domain/config.py:525` `format_action_list_item` ← `presentation/controllers/action_list_rendering.py` `build_action_rows`（`:25`）・`format_next_action_summary`（`:51`）。`build_action_rows` の呼び出し元は詳細表示の出力シーケンス一覧と簡易表示の出力シーケンス欄（`trigger_panel_controller.py` `refresh_actions` `:266`・`:334-335` で同じ行を共有）・呼び出し先の表示枠（`call_view_controller.py:224` `_render_rows`）。正本 `features.md:792` は key_hold の書式をこれらと「次に実行」の要約で同じと決めている。
  - キーボードUIのキー置換の枠: `presentation/keyboard_window.py:478`（`key_display_names` → 記号の表 → キー名。英字の大文字はどちらも引かない・`:476`）。
- domain の format 系の関数はレイアウトを知らない（domain から presentation への参照は無い）。外から注入する前例は `resolve_call`（`action_list_rendering.py`・`call_view_controller.py:229`）。
- 選んでいるレイアウト: `presentation/controllers/layout_controller.py` の `_active_layout`（`get_current_keyboard_layout()`・`:220`）。`KeyboardLayout.key_display_names` は組の tuple（`keyboard_layouts.py:28`）で、引くときに `normalize_key_name` する（`:31`）。
- レイアウトの描き直し:
  - 構成の読込（`keymap_set_io.py` の各経路）と起動（`app.py:375`・`:378-380`）は、レイアウトの読み直しの後にトリガー一覧と出力シーケンス一覧を描く（足りている）。
  - 利用者の操作の 3 入口（ドロップダウンの選択 `layout_controller.py:333`・追加 `:341`〔`:362` で読み直し〕・削除 `:366`〔`:408` で読み直し〕）は、キーボードUIだけを描き直す。
  - `refresh_actions(select=None)` は選択を「次に実行」の行へ戻す（`trigger_panel_controller.py:336-337`）。末尾で呼び出し先の表示枠も描き直す（`:343-345`）。
- レイアウトの JSON を書き戻す処理は無い。読込は `keyboard_layouts.py:171-185`（`key_display_names`）。起動・構成の読込で読込エラーのレイアウトは黙って外れる（`:317-320`）。
- 同梱のレイアウトは `infrastructure/bundled_layouts.py:11` `install_bundled_layouts` が、利用者の `user/keylayout` のフォルダが無いときだけフォルダごと入れる（フォルダがあれば何もしない）。開発時はリポジトリの `config/` を使う。
- キー名: US TKL の `\` の位置の id は `\`（`us_tkl.json`）。JIS の見本は `yen`（label `¥`）・`ro`（jis.json の label `ろ`・jis_mac.json の label `_`）。キーボードUIで記録すると `backslash` で保存されることもある（idea_63 の経緯・`tk_keys.py:73`）。

## §2 確定事項（ユーザー 2026-11-25）

- **表示の切り替えはレイアウトの JSON の新しい任意の項目で持たせる**（`key_display_names` とは別の項目）。
- **配列の判別はしない**。選んでいるレイアウトのファイルが規則を持つ（JIS かどうかの判別の改善は idea_70 へ分離）。
- **保存するキー名・送信は変えない**（表示だけ）。
- **文字からキー名への逆引き（`presentation/tk_keys.py:73`）には使わない**（逆引きは `KEY_SYMBOLS` のまま）。
- **v0.2 の §8 確認事項はすべて提案どおり**（ユーザー 2026-11-25）:
  1. 項目名は `key_symbols`。
  2. 見本の jis.json の値は `backslash`・`\`・`ro` → `＼`（`yen` は `¥` のまま・idea_63 の案 A。`ro` は Shift なしで `\` を出すキーなので出る文字を優先）。
  3. 起票元の場面（US のレイアウトのまま ろ キーを記録 → `backslash`）は、US TKL（内蔵）・`us_tkl.json` を選んでいる間は今のまま ¥ に見える。配列の判別をしないことの帰結として受容（JIS のレイアウトを選ぶか自分で書けば直る）。
  4. `jis_mac.json` には書かない（Mac で `\` が ¥ に見えるかは未確認。困ると分かってから足す。利用者が書けば効く）。
  5. 既に入れてある利用者のレイアウトは自動では直さない（§7 の受容）。
- **Codex 敵対的レビューの反映**（ユーザー 2026-11-25）: 不正な `key_symbols` はレイアウトの読込エラーにせず表だけを使わない・**ステータスバーに警告を出す**（ユーザーの追加案。一時メッセージ欄の下敷きにし、ほかのメッセージが消えたら戻す）/ レイアウトの切替の描き直しで出力シーケンス一覧の選択は保たない（「次に実行」へ戻るのを受容）/ 描き直しの入口に `set_keyboard_layout_selection` を足す / key_hold は正しく読めたキーの行だけに当てる。

## §3 レイアウトの JSON の `key_symbols`

- 最上位の任意キー `key_symbols`: キー名 → 1 行の表示の文字の object。既存キーは不変。
- 例: `"key_symbols": {"backslash": "＼", "\\": "＼", "ro": "＼"}`
- 読込（**不正でもレイアウトの読込エラーにしない**。表示のための項目の書き間違いで、受信・送信〔`scan_code`〕やレイアウトの選択まで失わないため）:
  - 無い・`null` → 空（警告なし）
  - 次のどれかに当たれば **`key_symbols` を表ごと使わず（空として扱い）、レイアウトはそれ以外の項目で読み込む**。理由を 1 つ持つ（最初に見つかったもの）:
    object でない / 値が文字列でない / キーを正規化すると空になる / 値に改行（`\n`・`\r`）を含む（1 行の一覧で使うため）
  - キーはキー名の正規化（`normalize_key_name`）をして持つ。正規化後に重なるキーは後に書いた方
  - 値が空文字・空白だけなら表に無いものとして扱う（不正ではない）/ それ以外の値は書いたまま使う（前後の空白も除かない）
  - `key_display_names` 等ほかの項目の読込エラーは今のまま（レイアウトの読込エラー）
- **警告 = ステータスバー中央の一時メッセージ欄の「下敷き」**（新しい部品は作らない・ダイアログは使わない）:
  - 選んでいるレイアウトの `key_symbols` を使わなかったとき、警告の文言（レイアウトの表示名と理由）を下敷きとして持つ。一時メッセージが無いあいだは欄に下敷きを出す。
  - ほかの一時メッセージ（`app.py:544` `_set_flash_message`）が来たらそちらを優先して出す（今と同じく 4 秒で消えるもの・消えないものとも）。一時メッセージが消えたとき（自動で消える・空の文言で置き換える・`app.py:539` `_clear_flash_message`）は、空にする代わりに下敷きを出し直す。
  - 下敷きを決め直すのは、選んでいるレイアウトを当て直したとき（起動・構成の読込・ドロップダウンの選択・追加・削除・フックキーの個別設定の切替の読み直し）。不正の無いレイアウトになれば下敷きは消える（JSON を直して読み直した場合を含む）。決め直した直後に一時メッセージが無ければ欄にすぐ出す。
  - 追加の操作で読んだレイアウト（選んでいなくても）の `key_symbols` が使えなかったときは、「追加しました」の代わりに、追加できたことと警告の両方が分かる一時メッセージを出す（今の「追加しました」と同じく自動で消える。選んでいるレイアウトでなければ下敷きにはしない）。
  - 選んでいないレイアウトの `key_symbols` が不正でも、追加のとき以外は出さない。
  - 見切れたときのツールチップ・簡易表示の 1 行は一時メッセージ欄の今の決まりのまま（`features.md:553`・`:686`）。
  - 文言は ja / en の両方に足す（`ui_terms.md`）。
- 書けるキー名は記号の表（`KEY_SYMBOLS`）にあるものに限らない（例: `"muhenkan": "無変換"`）。

## §4 表示の決め方

表示の文字 = **選んでいるレイアウトの `key_symbols` → 記号の表 `KEY_SYMBOLS` → キー名**の順で最初に見つかったもの。

| 箇所 | 決め方 |
|---|---|
| キーボードUIのキー置換の枠 | `key_display_names` → `key_symbols` → `KEY_SYMBOLS` → キー名。送信先が英字 1 文字の大文字なら今と同じくどれも引かない |
| トリガー一覧（`01. ＼: ラベル`） | `key_symbols` → `KEY_SYMBOLS` → キー名（`key_display_names` は今と同じく使わない） |
| key_hold の行（詳細表示の出力シーケンス一覧・簡易表示の出力シーケンス欄と「次に実行」の要約・呼び出し先の表示枠） | 同上。**正しく読めたキーの行のキー名だけ**に当てる（不正な行の `[key_hold] <値>`・マウスの行・リピートの表記は今のまま・正本 `features.md:792`） |

- `key_symbols` は**キー名を `normalize_key_name` して引く**（`minus` で書いた key_hold の行も `-` の上書きに当たる）。`KEY_SYMBOLS` は今と同じく小文字にして引く。
- 記号の表示を使わない箇所（hotkey の一覧と入力欄・キーマップ編集のキー置換一覧・切替 / 停止 / トグルキーの欄・割り当ての無い枠の `label`・物理キー名の小さい文字）は `key_symbols` も使わない（今のまま）。
- 文字からキー名への逆引き（`tk_keys.py:73`）は `KEY_SYMBOLS` のまま（§2）。

## §5 層の分担

- domain の `display_key_name`・`format_trigger_list_item`・`format_key_hold_value`・`format_action_list_item` は、上書きの表（`Mapping[str, str] | None`・既定 `None` = 上書きなし）を引数で受け取る。domain はレイアウトを参照しない。
- presentation は選んでいるレイアウトの表をこれらへ渡す（`refresh_triggers`・`build_action_rows`・`format_next_action_summary`・呼び出し先の表示枠・キーボードUI）。
- `KeyboardLayout` は読み込んだ `key_symbols` を `key_display_names` と同じ組の tuple で持ち、渡すときの dict を返す手段（プロパティ等）を持つ。内蔵の US TKL は空。

## §6 レイアウトの切替・読み直しのとき

- 利用者の操作の 3 入口（ドロップダウンの選択〔同じレイアウトの選び直しを含む〕・追加・削除）の末尾と、`set_keyboard_layout_selection` の末尾（削除で選んでいたレイアウトを外し、その後の保存の失敗・取り消しで操作の末尾へ届かない場合のため）で、**トリガー一覧と出力シーケンス一覧も描き直す**（出力シーケンス一覧の描き直しで簡易表示の欄・要約・呼び出し先の表示枠も揃う）。`_refresh_active_layout`・`sync_keyboard_layout_controls` には入れない（構成の読込の経路で二重に描くため）。起動・構成の読込は今のまま（既に描き直している）。
- 描き直しでは、出力シーケンス一覧の選択は今の描き直しと同じく「次に実行」の行へ戻る（**受容**。何も選んでいない状態や Shift で伸ばした範囲の基点を戻す仕組みは作らない・レイアウトの切替はまれな操作のため）。
- 受容: フックキーの個別設定の切替（`app.py:887` `_sync_control_vars_from_data`）もレイアウトを読み直すが一覧は描き直さない。外部のレイアウトの JSON を書き換えた直後にこの切替をしたときだけ、キーボードUIは新しい表示・一覧は古い表示になる（次の描き直しで揃う）。
- 起動中に外部レイアウトの JSON を書き換えても、選び直すか読み直すまでは反映しない（`scan_code` 等と同じ・ファイルは監視しない）。

## §7 見本のレイアウト

- 同梱の `jis.json` に `"key_symbols": {"backslash": "＼", "\\": "＼", "ro": "＼"}` を書く（`yen` は `¥` のまま・`＼` は全角 U+FF3C）。`jis_mac.json` には書かない（§2）。
- `us_tkl.json` は空の `{}`（ひな形として項目を見せる・`key_display_names` と同じ扱い）。`jis_mac.json`・`us_mac.json`・`de.json`・`jis_test.json` は書かない。
- 受容: 利用者の構成のフォルダに `user/keylayout` が既にあれば、アプリを更新しても同梱のレイアウトは入らない（書き換えも新しいファイルの追加もしない・`bundled_layouts.py:11`）。直したい利用者は自分で `key_symbols` を書き足す。

## §8 受け入れ条件（ドラフト）

1. `key_symbols` を書いたレイアウトを選ぶと、トリガー一覧・key_hold の行（詳細表示の一覧・簡易表示の欄と「次に実行」の要約・呼び出し先の表示枠）・キーボードUIのキー置換の枠に上書きの文字が出る（§3・§4）。
2. `key_symbols` の無いレイアウト・内蔵の US TKL では表示が今と変わらない（§4）。
3. キーボードUIの枠では `key_display_names` が `key_symbols` より優先し、英字の大文字はどちらも引かない（§4）。
4. `key_symbols` は正規化した名前で引く（`minus` の key_hold の行が `-` の上書きに当たる）（§4）。
5. 読込の規則（型・正規化・改行・空文字と空白だけ）が §3 のとおり。不正な `key_symbols` のレイアウトは表だけを使わずに読み込まれ、選択・受信・送信は変わらない（起動時に不正な表を持つレイアウトを選んでいても US TKL に落ちない）。
6. 不正な `key_symbols` のレイアウトを選んでいるあいだ、ステータスバー中央の一時メッセージ欄に表示名と理由の警告が出る。ほかの一時メッセージが来るとそちらが出て、それが消えると警告に戻る。不正の無いレイアウトに切り替える・直して読み直すと警告は消える。追加のときは追加できたことと警告の両方が出る。文言は ja / en の両方（§3）。
7. ドロップダウンの選択・追加・削除（保存の失敗・取り消しを含む）でレイアウトが変わると、トリガー一覧と出力シーケンス一覧も新しいレイアウトの表示になる（§6）。
8. key_hold の不正な行・マウスの行の表示は変わらない（§4）。
9. 保存するキー名・送信・逆引き（`tk_keys.py:73`）が変わらない（§2）。
10. 見本の `jis.json` で `backslash`・`\`・`ro` が `＼`、`yen` が `¥` で出る（§7・Windows の実機目視）。

## §9 スコープ外（本フェーズでやらない）

- 配列（JIS 等）の判別の改善（idea_70）。
- 記号の表示を使わない箇所（hotkey の一覧・キー置換一覧・切替 / 停止 / トグルキーの欄等）の表示の変更。
- 割り当ての無い枠の `label`・物理キー名の小さい文字（レイアウトの作者が `label` で決める）。
- 既に入れてある利用者のレイアウトのファイルの自動の書き換え・同梱の新しいファイルの追加。
- 言語ごとの切り替え（表はレイアウトごとで、言語では変えない）。
- 内蔵の表 `KEY_SYMBOLS` の値の変更（全言語・全環境で全角になるため採らない）。

## §10 正本反映（フェーズ末昇格・予定）

- 正本 `features.md` §4.6:
  - 「キーの文字」の枠の文字の決め方（`:726`）に `key_symbols` を足す。
  - 「記号キーのキー名の表示」の「表は全言語・全レイアウトで共通」（`:764`）を「レイアウトの `key_symbols` で上書きできる」に、「配列固有のキーの表示は `key_display_names` に書く」（`:767`）を一覧にも出すなら `key_symbols` と言い換える。
  - 「レイアウトの JSON の `key_display_names`」の並びに `key_symbols` の節を足す。見本の説明（jis.json）。
  - レイアウトの切替で両一覧を描き直すこと（§6）。
  - 不正な `key_symbols` の扱いと警告（§3）・「一時的な案内」（`:552`）の一時メッセージ欄に下敷きの警告を足す。
- 正本 `ui_terms.md`（警告の文言の表記）。`data_schema.md` にはレイアウトの JSON の書式が無いので対象外。
- 実装: `domain/key_symbols.py`・`domain/config.py`・`domain/key_hold.py`・`presentation/keyboard_layouts.py`・`presentation/keyboard_window.py`・`presentation/controllers/trigger_panel/trigger_panel_controller.py`・`presentation/controllers/action_list_rendering.py`・`presentation/controllers/call_view_controller.py`・`presentation/controllers/layout_controller.py`・`presentation/app.py`（一時メッセージ欄の下敷き）・`shared/i18n/locales/ja.json`・`en.json`・`config/user/keylayout/jis.json`・`us_tkl.json`。
- テスト: `tests/test_key_symbols.py`・`tests/test_domain_config.py`・`tests/test_key_hold.py`・`tests/test_keyboard_layout_files.py`・レイアウトの読込のテスト・`tests_ui`（キーボードUIの枠・一覧の描き直しと選択の保持・`test_action_dialog_labels.py`）。
- `codebase_map.md`（`key_symbols` の受け渡し）。

## 関連

- idea_63（起票元）・idea_70（配列の判別・分離）
- phase 69（`key_display_names`）・phase 74（記号キーのキー名の表示）・phase 81（英字の大文字の置換先）
- 正本 `features.md` §4.6・`key_input.md` §7（JIS の特殊キー）
