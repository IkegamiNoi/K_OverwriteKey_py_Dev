# phase.md

## フェーズ名

レイアウトごとのキー名の記号の上書き（layout_key_symbols）

## フェーズの目的

日本語のフォントで `\` が ¥ に見え、`backslash`・`\`・`ro` と `yen` を見分けられない問題を、レイアウトの JSON の新しい任意の項目 `key_symbols`（キー名 → 1 行の表示）で直す。選んでいるレイアウトの表が、トリガー一覧・key_hold の行・キーボードUIのキー置換の枠の記号の表示を上書きする。配列の判別はしない。
**対象は domain（記号の表示と一覧の整形の関数に上書きの表を引数で渡す）・presentation（レイアウトの読込・表の受け渡し・レイアウトの切替での一覧の描き直し・ステータスバーの警告の下敷き）・同梱の見本 jis.json / us_tkl.json。JSON スキーマ = レイアウトの JSON に任意キーの追加（既存キーは不変）。保存するキー名・送信・逆引きは変えない**。

- 起票元: [idea_63](../../backlog/idea_63_backslash_display_fullwidth.md)（2026-11-22 起票・2026-11-25 方向をユーザー確定）。配列の判別の改善は [idea_72](../../backlog/idea_72_layout_physical_type_field.md) へ分離。
- 主入力（暫定仕様）: [64_layout_key_symbols.md](../../history/64_layout_key_symbols.md)（v0.4・ユーザー確定済）。
- モード: **暫定仕様先行モード**（domain と presentation に跨る・タスク 3 以上・探索的に詰めた）。番号対応: phase 84 / 暫定 64 / decisions 84。

## 確定（ユーザー 2026-11-25）

- レイアウトの JSON の新しい項目 `key_symbols` で持たせる・配列の判別はしない・逆引きには使わない（暫定 64 §2）。
- 見本は jis.json だけに `backslash`・`\`・`ro` → `＼`（`yen` は `¥`）。jis_mac.json には書かない。US のレイアウトを選んでいる間は直らないことと、既存の利用者のフォルダを自動で直さないことは受容（§2・§7）。
- deep-reviewer（v0.1 → v0.2）と Codex 敵対的レビュー 4 件（v0.3 → v0.4）を推奨どおり採用。不正な `key_symbols` はレイアウトの読込エラーにせず表だけを使わない。警告はステータスバーの一時メッセージ欄の下敷き（ほかのメッセージが消えたら戻す）（§3）。
- レイアウトの切替で両一覧を描き直す。出力シーケンス一覧の選択は「次に実行」へ戻るのを受容（§6）。

## スコープ

### 含む

- レイアウトの JSON の `key_symbols` の読込（不正なら表だけを使わず理由を持つ）と `KeyboardLayout` の保持（§3・§5）
- domain の記号の表示と一覧の整形の関数への上書きの表の引数（正規化した名前で引く・key_hold は正しく読めたキーの行だけ）（§4・§5）
- presentation の表の受け渡し（トリガー一覧・出力シーケンス一覧・簡易表示の欄と要約・呼び出し先の表示枠・キーボードUI）と、レイアウトの切替の 4 か所での一覧の描き直し（§5・§6）
- ステータスバーの一時メッセージ欄の警告の下敷き・追加のときの文言・ja / en の文言（§3）
- 見本 jis.json / us_tkl.json（§7）・tests / tests_ui・Windows の実機目視（ユーザー）

### 含まない（後送り）

- 配列の判別の改善（idea_72）・内蔵の表 `KEY_SYMBOLS` の値の変更・言語ごとの切り替え
- 記号の表示を使わない箇所（hotkey・キー置換一覧・切替 / 停止 / トグルキーの欄・割り当ての無い枠の `label`）の表示
- 既存の利用者のレイアウトの自動の書き換え・出力シーケンス一覧の選択を保つ仕組み

## このフェーズで読むファイル

1. [暫定仕様 64](../../history/64_layout_key_symbols.md)（§1 の `ファイルパス:行` が実装の起点）
2. `keyseq/domain/key_symbols.py`・`keyseq/domain/config.py`（`normalize_key_name`・`format_trigger_list_item`・`format_action_list_item`）・`keyseq/domain/key_hold.py`（`format_key_hold_value`）
3. `keyseq/presentation/keyboard_layouts.py`（`KeyboardLayout`・`key_display_names` の読込・`collect_keyboard_layouts`）
4. `keyseq/presentation/keyboard_window.py`（枠の文字）・`keyseq/presentation/controllers/layout_controller.py`（選択・追加・削除・`set_keyboard_layout_selection`・`sync_keyboard_layout_controls`）
5. `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py`（`refresh_triggers`・`refresh_actions`）・`keyseq/presentation/controllers/action_list_rendering.py`・`keyseq/presentation/controllers/call_view_controller.py`
6. `keyseq/presentation/app.py`（`_set_flash_message`・`_clear_flash_message`）・`keyseq/shared/i18n/locales/ja.json`・`en.json`
7. 正本 `instructions/common/spec_detail/features.md` §4.6（キーの文字・レイアウトの JSON の `key_display_names`・記号キーのキー名の表示・一時的な案内）・`ui_terms.md`
8. `instructions/common/codebase_map.md` の該当節（キー名の表示・レイアウト）

## タスク

- task_01: `key_symbols` の読込と domain の表示の関数（レイアウトの読込・不正の理由・`KeyboardLayout` の保持と dict の取り出し・`display_key_name` / `format_trigger_list_item` / `format_key_hold_value` / `format_action_list_item` の引数）と tests（§3・§4・§5。`key_symbols` の無いレイアウト・表を渡さないときに表示が変わらないこと〔§8-2〕と保存名・逆引きが変わらないこと〔§8-9〕を含む）
- task_02: presentation の表の受け渡しと描き直し（トリガー一覧・出力シーケンス一覧・簡易表示・呼び出し先の表示枠・キーボードUI・レイアウトの切替の 4 か所）と tests_ui（§4・§5・§6。内蔵の US TKL で表示が変わらないこと〔§8-2〕を含む）
- task_03: 警告の下敷き（一時メッセージ欄・追加のときの文言・ja / en）と見本 jis.json / us_tkl.json と tests / tests_ui（§3・§7）
- task_04: 統合確認（tests / tests_ui / smoke）と Windows の実機目視（ユーザー・暫定 64 §8）
- task_05: 正本反映（暫定 64 を `features.md` §4.6・`ui_terms.md`・`codebase_map.md` へ昇格・暫定 64 を凍結）+ `decisions_archive/84` + current.md の完了記載 + idea_63 を `INDEX_done.md` へ + `/refactor_check`
- task_05_refactor: 提案書 30（一時メッセージ欄の書き込みを `App._show_flash_area` に一本化・挙動不変・2026-11-26 追加）

## レビュー方針

- 共通観点は `.claude/rules/review.md`。各タスクは `reviewer`、統合確認は `deep-reviewer` + `codex-reviewer`、フェーズ完了判定前は `deep-reviewer` + Codex 敵対的レビュー
- 固有の観点: domain がレイアウトを参照していないか（表は引数だけ）/ 保存するキー名・送信・逆引き（`tk_keys.py:73`）を変えていないか / `key_symbols` の無いレイアウトで表示が変わっていないか / 不正な `key_symbols` でレイアウトの選択・受信・送信を失わないか / 一時メッセージの既存の動き（4 秒で消える・消えないもの）を下敷きが崩さないか
