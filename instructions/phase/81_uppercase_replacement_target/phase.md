# phase.md

## フェーズ名

キー置換の置換先に英字の大文字（uppercase_replacement_target）

## フェーズの目的

キーマップの置換先に英字の大文字（例: `F1` → `A`）を置けるようにする。phase 74（Shift の要る記号を置換先にできる）の延長で、
大文字の置換先は小文字と同じキーで解き、Shift を足して送る。キーボードUI では Shift を押しながら英字を記録すると大文字で保存する。
**対象は domain（置換先の正規化の関数）・application（判定・割り当て）・infrastructure の os_backend（Windows / macOS の送信と Shift の判定）・presentation（キーボードUI の記録と表示）。JSON スキーマの型は不変（`mappings` の str → str。置換先の `A`〜`Z` だけ大文字を保つ）**。

- 起票元: [idea_62](../../backlog/idea_62_uppercase_replacement_target.md)（2026-11-21 起票・2026-11-25 意図を確認して書き直し）。
- 主入力（暫定仕様）: [61_uppercase_replacement_target.md](../../history/61_uppercase_replacement_target.md)（v0.3・ユーザー確定済）。
- モード: **暫定仕様先行モード**（`data_schema.md` / `key_input.md` に跨る・タスク 3 以上）。番号対応: phase 81 / 暫定 61 / decisions 81。

## 確定（ユーザー 2026-11-25）

- 置換先に英字の大文字を置く（暫定 61 §2）。置換元に `Shift+キー` を付ける案は [idea_68](../../backlog/idea_68_shift_layer_replacement_source.md) へ分離。
- deep-reviewer（v0.1 → v0.2）と Codex 敵対的レビュー 5 点 + 表示名 1 点（v0.2 → v0.3）を推奨どおり採用。
- Caps Lock は見ない・手書きの `"A"` の動きの変化と旧版での保存し直しは受容（暫定 61 §6）。
- macOS の「押されている」の判定に、key_hold などアプリが送って押したままの修飾キーを含める（記号と英字で共通・暫定 61 §4）。

## スコープ

### 含む

- 置換先の正規化の関数の新設と、置換先の全箇所（読込・判定・割り当て・表示）からの呼び出し（暫定 61 §3）
- Windows / macOS の送信（小文字の名前で解いて Shift を足す）と、macOS の修飾キーの判定に送信済みの修飾を含めること（§4）
- キーボードUI の置換先の記録（Shift + 英字 → 大文字）と表示（大文字は表示名を引かない）（§5）
- 既存テストの期待値の変更（§7-8）と追加のテスト・Windows / macOS の実機目視（ユーザー）

### 含まない（後送り）

- 置換元の `Shift+キー`・Shift の面（idea_68）・置換先の修飾キーの記録（idea_57）
- hotkey・key_hold・トリガーの大文字・Caps Lock の状態を見た送信・英字以外の 1 文字の大文字

## このフェーズで読むファイル

1. [暫定仕様 61](../../history/61_uppercase_replacement_target.md)（§1 の `ファイルパス:行` が実装の起点）
2. `keyseq/domain/config.py`（`normalize_key_name`・`_normalize_keymap_mappings`）
3. `keyseq/application/keymap_service.py`（置換先の取得・`set_mapping`）・`keyseq/application/input_router.py`（置換の判定）
4. `keyseq/infrastructure/input_gateway.py`（`send_mapped_key`）・`keyseq/infrastructure/os_backend/windows/keyboard_backend.py`（`_needs_shift`・`resolve_send`）・`keyseq/infrastructure/os_backend/macos/keyboard_backend.py` / `key_table.py` / `window_backend.py`
5. `keyseq/presentation/keyboard_window.py`（`_record_key`・表示）・`keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py`（`assign_keymap_from_keyboard_ui`）
6. 正本 `instructions/common/spec_detail/key_input.md` §7.4（「キーボードUI の置換先の Shift 付きの記号」「キー置換の送信の Shift」）・`data_schema.md` §5.1 / §5.6 キーマップ
7. `instructions/common/codebase_map.md` の該当節（キー名の正規化・キーの送信）

## タスク

- task_01: 置換先の大文字の保存・判定・送信（domain の正規化の関数・application・Windows / macOS の backend・macOS の修飾の判定）と tests（既存の期待値の変更を含む）。Windows の `_needs_shift("A")` の従来値の実測を含む
- task_02: キーボードUI の記録と表示（Shift + 英字 → 大文字・大文字は表示名を引かない・`a` → `A` の付け替えで変更の印）と tests_ui
- task_03: 統合確認（tests / tests_ui / smoke）と Windows / macOS の実機目視（ユーザー・暫定 61 §7-9）
- task_03a: 統合レビューの採用分 = テストの検出力の補強（表示の差し替えを大小無視に・macOS の送信済みの修飾を gateway 経由で・分割設定の往復・Shift + 数字・2026-11-25 追加）
- task_05_refactor: 提案書 29（大文字の判定を domain の 1 関数へ・Windows の press / release の補助・挙動不変・2026-11-25 追加）
- task_04: 正本反映（暫定 61 を `data_schema.md` / `key_input.md` / `codebase_map.md` へ昇格・`features.md` は置換先の説明の該当節を特定して追記・暫定 61 を凍結）+ `decisions_archive/81` + current.md の完了記載 + idea_62 を `INDEX_done.md` へ + `/refactor_check`

## レビュー方針

- 共通観点は `.claude/rules/review.md`。各タスクは `reviewer`、統合確認は `deep-reviewer` + `codex-reviewer`、フェーズ完了判定前は `deep-reviewer` + Codex 敵対的レビュー
- 固有の観点: 置換先以外のキー名（置換元・トリガー・切替 / 停止 / トグル・hotkey・key_hold）の小文字化を変えていないか / 小文字の置換先と phase 74 の記号の送信を変えていないか / 大文字と小文字が同じキーで解かれるか / macOS の修飾の判定の変更が key_hold の押したままの記録を崩さないか
