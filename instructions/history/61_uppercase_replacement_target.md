# 暫定仕様 61: キー置換の置換先に英字の大文字（uppercase_replacement_target）

> 状態: **未凍結・v0.3・主入力・**ユーザー確定済（2026-11-25）・実装着手可**（v0.1 → deep-reviewer「修正して採用」を反映 = v0.2 → Codex 敵対的レビュー 5 点 + 表示名 1 点を推奨どおり反映 = v0.3）**。本書がこのフェーズの確定設計（フェーズ中は正本を直接改訂しない）。
> フェーズ末タスクで正本 `instructions/common/spec_detail/` へ昇格し本書を凍結する。
> 起票元: [idea_62](../backlog/idea_62_uppercase_replacement_target.md)（2026-11-21 起票・2026-11-25 ユーザーと意図を確認して書き直し）。番号対応: phase 81 / 暫定 61 / decisions 81。

---

## §1 目的 / 背景

キーマップの置換先に英字の大文字（例: `F1` → `A`）を置けるようにする。Shift の要る記号（`!`・`|` 等）は phase 74 で置けるようになったので、同じ送り方を英字の大文字へ広げる。

### 現状監査（2026-11-25・メインで直読み）

- 置換先は保存・判定・表示・割り当てのたびに `normalize_key_name`（trim + 小文字化）を通るため、大文字は残らない:
  - 読込: `keyseq/domain/config.py:328` `_normalize_keymap_mappings`（`coerce_key_name` → `normalize_key_name`・`config.py:122`）
  - 判定: `keyseq/application/input_router.py:143`（`normalize_key_name(self._find_keymap_target(key))`）・`keyseq/application/keymap_service.py:239`（置換先の取得）
  - 割り当て: `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py:633`（`assign_keymap_from_keyboard_ui` の `target`）→ `keymap_service.py:288`（`set_mapping` の `target`・キーボードUI の割り当ての唯一の保存箇所）・`:293`（前の値。`:296` で変更の有無を比べる）
  - 表示: `keyseq/presentation/keyboard_window.py:231`（枠に出す置換先）
  - 影響なしを確認: `key_overlap.py`（置換元だけ）・`reference_scan` / `orphan_scan`（形の判定だけ）・`keymap_add_flow`（空の mappings）。split の読込・保存は `ensure_config_compatibility` を通るため `config.py:333` の 1 箇所でそろう（deep-reviewer 2026-11-25）
- 送信: `keyseq/infrastructure/input_gateway.py:80` `send_mapped_key`。`needs_shift` が真で、Shift も Ctrl / Alt / Windows も押されていなければ Shift を足す（phase 74・正本 `key_input.md` §7.4「キー置換の送信の Shift」）。
  - Windows: `keyseq/infrastructure/os_backend/windows/keyboard_backend.py:51` `_needs_shift` = keyboard ライブラリの `map_name` の先頭の候補の修飾が `shift` だけか。keyboard の `normalize_name` は 1 文字の名前の大小を保つ（`.venv/Lib/site-packages/keyboard/_canonical_names.py:1241`）が、名前の表は修飾なしの候補も集め、修飾の優先度順（`()` が `('shift',)` より先）に並べる（`_winkeyboard.py:429-436`）ため、**`A` は Shift 付きと判定されない見込み**（ソースの読みで推定・未実測）。`!` は Shift の候補しか無いため phase 74 は動いている。
  - macOS: `keyseq/infrastructure/os_backend/macos/keyboard_backend.py:188` が `SHIFTED_US` / `SHIFTED_JIS`（`macos/key_table.py:69`・`:78`）を引き、当たれば `mac_shift`。表に英字は無い。
- 記録: `keyboard_window.py:618` `_record_key`。Shift を押していて `yen` / `ro` なら `bar` / `underscore` にする（`_SHIFTED_TARGET_NAMES`・`keyboard_window.py:67`）。英字は Shift を押していても小文字で記録される。
- 置換先のリピート停止: `keyseq/application/action_executor.py:357` `held_inputs.stop_repeat_for_keys((key,))`。照合は名前ではなく `resolve_send` + `identity_of` の走査コード（`held_inputs.py:87-90`・`:143-148`）。
- 置換先の検査: `keymap_panel_controller.py:665` `validate_key_name(target)` → backend の `resolve_send`。

## §2 確定事項（ユーザー 2026-11-25）

- **置換先に英字の大文字を置けるようにする**（例 1）。置換元は従来どおり単一キー・小文字。
- **意図は phase 74（Shift の要る記号を置換先にできる）の延長として英字の大文字に対応し、使い勝手を上げること**。大文字が出ることを保証するのはラテン文字の入力配列（US / JIS 等）。
- Codex 敵対的レビュー（2026-11-25）の 5 点と表示名の 1 点を推奨どおり採用（§4・§5・§3 に反映）。§6 の確認事項はすべて確定。
- **置換元に `Shift+キー` を付ける案（同じキーマップに Shift を押している間の面を持たせる）は本フェーズで行わない** → [idea_68](../backlog/idea_68_shift_layer_replacement_source.md)（Shift 以外の修飾キーの面の検討も同 idea に含む）。

## §3 置換先の名前（保存形式）

- 置換先の正規化は domain に新設する 1 関数（例: `normalize_mapping_target`・`domain/config.py`）に集め、§1 の置換先の全箇所（`config.py:333`・`keymap_service.py:239`・`:288`・`:293`・`input_router.py:143`・`keymap_panel_controller.py:633`・`keyboard_window.py:231`）から呼ぶ。
- `mappings` の値（置換先）が **ASCII の英字 1 文字の大文字（`A`〜`Z`）** のときだけ、大文字のまま保持する。それ以外の値は従来どおり trim + 小文字化（`F1` → `f1`・`Shift` → `shift`・全角や英字以外の 1 文字は対象外）。
  - 判定は trim の後。trim 後に英字 1 文字の大文字なら大文字、小文字なら小文字のまま（`a` と `A` は別の置換先）。
- 置換元（`mappings` のキー）・トリガー・切替 / 停止 / トグルキー・hotkey・key_hold のキー名は変えない（小文字化のまま）。
- **JSON スキーマの型は不変**（str → str）。読込・保存・split 読込・単一 JSON のいずれも同じ規則。
- 後方互換:
  - 既存の設定の置換先はすべて小文字で保存されているため、読み込みも動きも変わらない。
  - 手で JSON に `"A"` と書いていた置換先は、これまで `a` として動いていたが、本フェーズから大文字の `A` を送る（**動きが変わる**・自動移行しない・受容）。
  - 大文字を含む設定を本フェーズより前の版で読むと小文字化され、小文字で動く。**その版で保存し直すとファイルにも小文字で書かれ、本フェーズ以降の版に戻しても大文字は戻らない**（受容・ユーザー 2026-11-25）。
  - 単一 JSON・split・個別保存のいずれも、本フェーズ以降の版では読込 → 保存で大文字を保つ。

## §4 送信

- 置換先が `A`〜`Z` なら **Shift の要る文字として扱い、phase 74 の送り方に従う**（正本 `key_input.md` §7.4「キー置換の送信の Shift」）:
  - Shift（物理キー・key_hold のどちらでも）も Ctrl / Alt / Windows キーも押されていなければ、Shift 押下 → 英字キー押下 → 離し → Shift 離し。足した Shift は失敗しても必ず離す。全体を send_guard の中で行う。
  - 既に Shift が押されているときは足さずにそのまま送る（物理の Shift で大文字になる）。
  - Ctrl / Alt / Windows キーのどれかが押されているときは足さない（ショートカットを変えないため。`Ctrl+F1` → `Ctrl+a` になる。phase 74 と同じ）。
- **キーの解き方（両 OS 共通）**: 大文字の置換先は**小文字の名前でキーを解き**（送るキー = 小文字の `a` と同じキー）、Shift の要否だけを「英字 1 文字の大文字であること」で決める。大文字の名前のまま keyboard ライブラリ等で解かない（入力配列によって小文字と別のキーに解け得るため・Codex 指摘 4）。正本の「表は持たない」判定に対する英字の大文字の例外。
  - Windows: `resolve_send` で大文字 1 文字は小文字の名前で解き、`needs_shift` は大文字 1 文字なら「要る」とする（keyboard の表の先頭の候補は修飾なしになり、大文字のままでは「要る」にならないため・§1）。task_01 で従来の `_needs_shift("A")` が False であることを実測する。
  - macOS: 小文字の名前で VK を引き `mac_shift` で送る（`SHIFTED_US` / `SHIFTED_JIS` に `A`〜`Z` → `a`〜`z` を足す形でもよい。引き方は大小を区別する〔`macos/keyboard_backend.py:189`〕ため小文字の `a` は従来どおり）。
- **macOS の「押されている」の判定に、アプリが送って押したままの修飾キーも含める**（Codex 指摘 2）: 現在の `is_shift_down` / `is_ctrl_alt_win_down`（`macos/window_backend.py:230`・`:233`）は物理のフラグだけを見るため、key_hold で押したままの Shift / Control / Option / Command を見落とし得る（送ったキーが物理のフラグに反映されるかは未実測）。正本 §7.4 の「物理キー・key_hold のどちらでも」に合わせ、backend が記録している送信済みの修飾（`keyboard_backend.py:83` `_sent_modifiers`）も合わせて判定する。**記号（phase 74）と英字で共通の処理**。Windows は従来どおり（task_01 で key_hold の Shift が判定に入ることを確かめる）。
- 置換先の検査（`keymap_panel_controller.py:665` → `resolve_send`）は両 OS で大文字を受ける（Windows は従来から・macOS は表を足すことで）。
- 置換先のリピート停止（`action_executor.py:357`）は**変更不要**。照合は走査コードで、`A` は両 OS で `a` と同じ走査コード（30）になる（§1）。テストで確かめる。
- **受容**:
  - Caps Lock の状態は見ない。Caps Lock が ON のとき、Windows は OS が大小を反転するため `A` の置換先で小文字の `a` が出る見込み（物理で Shift+A を打ったときと同じ）。macOS は送るイベントのフラグを上書きするため Caps Lock は効かず `A` が出る見込み（物理の Shift+A も大文字）。いずれも実機で確かめるが、結果に合わせた補正はしない（ユーザー 2026-11-25）。
  - 置換先が小文字の `a` のときに物理の Shift を押していると `A` が出る（従来どおり・変えない）。
  - 送信のごく短い間の物理入力に足した Shift が混ざること（phase 74 と同じ・idea_53）。

## §5 記録と表示（キーボードUI）

- 置換先の記録（`_record_key`。Tk の経路と「記録用のフック」の経路の両方）で、**Shift を押していて記録した名前が英字 1 文字（`a`〜`z`）なら大文字にして保存する**。Shift を押していなければ小文字のまま。
  - Shift の判定は `yen` / `ro` と同じく処理時点の `is_shift_down()`。Caps Lock の状態は見ない。
  - 受容: 英字を押してすぐ Shift を離すと小文字で、Shift を押した直後に英字が処理されると大文字で記録されることがある（押下の時点ではなく処理の時点で見るため・Codex 指摘 1・phase 74 の記号と同じ）。枠の表示で分かり、入れ直せる。
  - 置換元・トリガー・key_hold・切替 / 停止 / トグルキーの記録は変えない（phase 74 と同じ理由）。
- 大文字化は `yen` / `ro` の変換と同じ位置（`keyboard_window.py:629`）で行う。Tk の経路も記録用のフックの経路も `_record_key` に合流し、記録用のフックは修飾キーを素通しするため `is_shift_down()` が効く。
- `assign_keymap_from_keyboard_ui` と `set_mapping` の置換先の正規化は §3 の関数に従う（大文字を保つ）。`a` → `A` の付け替えは変更として扱う（キーマップに変更の印が付く）。
- 表示: キーボードUI の枠には置換先を**大文字のまま**出す（`A` と `a` を見分けられる・`display_key_name` は英字をそのまま返す）。**大文字の置換先はレイアウトの `key_display_names` を引かず、大文字のまま出す**（表示名は `A` と `a` を同じ名前で引くため・Codex 追加指摘）。小文字の置換先は従来どおり表示名があればそれを出す（同梱のレイアウトに英字の表示名は無い）。
  - 文言の追加は無い見込み（追加が要るときは `ui_terms.md` に従い `ja.json` と `en.json` の両方へ足す）。

## §6 確認事項（確定済）

- Q1 Caps Lock の扱い → 見ない・受容（§4・ユーザー 2026-11-25）。
- Q2 手書きの `"A"` の動きの変化と旧版での保存し直し → どちらも受容（§3・ユーザー 2026-11-25）。

## §7 受け入れ条件（ドラフト）

1. `mappings` の置換先 `A`〜`Z` が読込・保存・split 読込で大文字のまま残り、それ以外の置換先・置換元は従来どおり小文字になる（§3）。
2. Windows と macOS で、置換先 `A` のキーを押すと大文字の `A` が出る。Shift を押していても `A`、Ctrl を押していれば `Ctrl+a` になる（§4）。
3. 置換先が小文字の `a` の既存の置換は、動きが変わらない（§3・§4）。
4. キーボードUI で Shift を押しながら（通常の押し方で）英字を記録すると大文字で保存され、枠に大文字で表示される。Shift なしなら小文字。外部レイアウトに英字の表示名があっても大文字の置換先は大文字で出る（§5）。
5. キーボードUI で `a` → `A` に付け替えるとキーマップに変更の印が付く（§5）。
6. 置換先 `A` の送信で、押したままの `a` の key_hold のリピートが止まる（§4）。
7. 置換元・トリガー・hotkey・key_hold の記録と判定は変わらない（§3・§5）。
7a. 大文字の置換先は小文字と同じキー（走査コード / VK）で解かれる（§4）。
7b. macOS で key_hold が Shift / Control / Option / Command を押したまま置換先 `A`（および phase 74 の記号）を送ると、Shift を足さず、key_hold の押したままの記録も崩れない（§4）。Windows も key_hold の Shift で足さない。
8. 大文字の置換先が小文字になることを期待していた既存テスト（`tests/test_config_service.py:2090`・`:2097`・`:2101`・`tests/test_domain_config.py:484`・`:497`・`tests/test_keymap_service.py:77-80`）の期待値を、§3 に合わせて変える（置換先の大文字は保つ・置換元は小文字）。
9. tests / tests_ui / smoke が pass。Windows と macOS の実機目視（ユーザー）で 2・4・7b と Caps Lock ON の結果（§4 の受容の見込みどおりか）を確かめる。

## §8 スコープ外（本フェーズでやらない）

- 置換元に `Shift+キー` を付けること・Shift の面（[idea_68](../backlog/idea_68_shift_layer_replacement_source.md)）。
- 置換先に修飾キーを記録すること（[idea_57](../backlog/idea_57_modifier_as_replacement_target.md)）。
- hotkey・key_hold・トリガーの大文字。Caps Lock の状態を見た送信。
- 英字以外の 1 文字（全角・アクセント付きの文字等）の大文字。

## §9 正本反映（フェーズ末昇格・予定）

- `spec_detail/data_schema.md` §5.1 の共通規則（`mappings` のキーと値の小文字化・`:40-41`）と §5.6 のキーマップ（`mappings` の正規化の文・`:280-281`）: 置換先の `A`〜`Z` の例外。`:912` 付近の「置換先も `normalize_key_name` を通る」記述の言い回しも合わせる。
- `spec_detail/key_input.md` §7.4「キーボードUI の置換先の Shift 付きの記号」「キー置換の送信の Shift」: 英字の大文字の記録と送信・受容。判定の「表は持たない」（`:152`）に英字の大文字の例外（小文字の名前で解く・両 OS）を明記する。macOS の「押されている」の判定に送信済みの修飾を含めること。§7.9 前後の macOS の送信の節に該当があれば合わせる。
- `instructions/common/codebase_map.md`（キー名の trim + 小文字化の記述・`:964-973` 付近）: 置換先の例外と新設の関数。
- `spec_detail/features.md`: キー置換の置換先の説明があれば大文字の追記（昇格タスクで該当節を特定する）。
- 実装（見込み）: `domain/config.py`（置換先の正規化の関数）・`application/input_router.py`・`application/keymap_service.py`・`infrastructure/os_backend/macos/key_table.py`（または `macos/keyboard_backend.py`）・`infrastructure/os_backend/macos/window_backend.py`・`infrastructure/os_backend/windows/keyboard_backend.py`・`presentation/keyboard_window.py`・`presentation/controllers/keymap_panel/keymap_panel_controller.py`・`instructions/common/codebase_map.md`。
- テスト: `tests/test_config_service.py`・`tests/test_domain_config.py`・`tests/test_keymap_service.py`（§7-8 の期待値の変更）・`tests/test_input_router.py`・Windows / macOS の keyboard backend のテスト（`tests/test_macos_keyboard_backend.py:670` の `a` は Shift 不要が回帰の確認）・`tests_ui` のキーボードUI の記録。

## 関連

- [idea_62](../backlog/idea_62_uppercase_replacement_target.md)（起票元）・[idea_68](../backlog/idea_68_shift_layer_replacement_source.md)（分離した置換元の Shift の面）・[idea_57](../backlog/idea_57_modifier_as_replacement_target.md)・[idea_53](../backlog/idea_53_send_without_dropping_physical_input.md)
- phase 74（記号キーの表示と置換先の Shift・`decisions_archive/74_key_symbol_display.md`）
- 正本 `key_input.md` §7.4・`data_schema.md` §5.6
