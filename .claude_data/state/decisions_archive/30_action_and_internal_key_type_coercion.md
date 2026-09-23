# decisions_archive / phase 30: アクション要素と内部キーの型正規化

対応表: phase 30 / **暫定仕様なし（直接改訂モード）** / decisions 30。
起票元: [idea_27](../../../instructions/backlog/idea_27_mouse_click_button_type_coercion.md) /
[idea_28](../../../instructions/backlog/idea_28_runtime_internal_key_type_coercion.md)（統合）。
完了 2026-09-23。**domain 限定・JSON スキーマ不変・読込の頑健化**。
正本 = `spec_detail/data_schema.md` §5.11.1 / §5.11.2（`type` / `button` の型・空 / 未知の `type` の実行時挙動）/
§5.7（内部キーのパス値も本規則に従う）。**§5.1「型不正の共通規則」の本文は変更していない**。

## 問題

§5.1 に追従していない残り 2 系統。

1. **アクション要素の `type` / `button`**: 非文字列だと読み手の `(... or "").strip()` が `AttributeError`。
   `type` は実行時（`action_executor.py:51`）だけでなく**一覧表示（`domain/config.py:323`）でも落ちる**。
   `button`（`action_executor.py:119`）は `x` / `y` と違い `try` の外。正本 §5.11.2 は「非文字列は未定義」だった。
2. **runtime 内部キーのパス値 3 種**（`_keymap_source_path` / `_sequence_source_path` / `_trigger_set_source_path`）:
   `ensure_config_compatibility` が生値のまま素通しし、読み手の `str(...)` を経て**保存先パス候補に repr が混入し得る**。
   正本 §5.7 は「実装未追従」と明記していた。

## 確定した設計判断（ユーザー 2026-09-23）

| # | 判断 | 採らなかった案と理由 |
|---|---|---|
| 1 | **idea_27 と idea_28 を 1 フェーズに統合** | 別フェーズ = 同系統（§5.1 追従漏れ）で改訂先も同じ `data_schema.md`。分ける利点が無い |
| 2 | **idea_27 は案 A**（§5.11.2 の「非文字列は未定義」を削除し §5.1 に従う = 空扱い → `left`） | **案 B（実装だけ防御・仕様は未定義のまま）**は未定義を固定化するだけで §5.1 と不整合が残る |
| 3 | **`type` の非文字列も含める**（起票時の grep で発見） | `button` だけに絞る = 影響の大きい `type`（一覧表示で落ちる）を残す |
| 4 | **適用点は読込時の正規化 1 箇所**（`normalize_actions` / `ensure_config_compatibility`・domain） | 読み手側で個別に潰す = `type` 5 箇所・内部キー約 25 箇所（application + presentation）に散る。phase 24 で 2 度取りこぼした形 |
| 5 | **キーが無いときは補わない**（`type` / `button` / 内部キーとも） | 補う = `button` を持たない hotkey / text に `"button": ""` が増え保存出力が変わる。`label` が常に付与されるのは既存挙動で、非対称は意図どおり |
| 6 | **`coerce_label`（trim のみ）を使う** | `coerce_key_name` = 小文字化で保存値が変わる（`type`）/ パスが壊れる（内部キー。§5.7） |
| 7 | **空 / 未知の `type` は現行挙動を §5.11 に明文化**（`value` を文字列入力・一覧は `value` を表示。コード不変） | **案 B（何も送らずエラー通知）→ [idea_35](../../../instructions/backlog/idea_35_unknown_action_type_handling.md) へ分離**。executor / 一覧表示 / ダイアログ（空 `type` を hotkey とみなす `action_dialog.py:115` との食い違い）/ 通知経路に跨り挙動も変わるため直接改訂に収まらない（着手時は暫定仕様先行モード）。未規定のまま残すと、`type` の非文字列を空扱いにした結果が仕様外の経路へ入る |
| 8 | **直接改訂モード**（棚卸しで範囲が広ければ暫定仕様先行へ切替） | task_02 の棚卸しで入口が 1 箇所に収まると確認し、切替は不要だった |

## 棚卸し（task_02・2026-09-23）

内部キーの**書き手 12 箇所はすべて算出済みの文字列**（`coerce_label` 済みのパス / 保存計画の算出パス /
ファイル選択結果）。`config_service/__init__.py:299` の `str(sequence_item.get("path") or "")` も
算出値を受けており入口外の混入経路ではない。**生 JSON の値が runtime に残る入口は
`ensure_config_compatibility` の 3 点のみ**（`triggers[]` / `keymaps[]` / 最上位）→ 読み手は無修正。
reviewer が `ファイル:行` を実読して裏取り済み。

## 実施結果

- task_01（`08de61d`）: §5.11 改訂（先行）+ `normalize_actions` に `type` / `button` の `coerce_label` + テスト 5 件。
  reviewer = 完了可・指摘なし。
- task_02: `ensure_config_compatibility` にパス系内部キー 3 種の `coerce_label` + テスト 4 件 / §5.7 注記の書き換え。
  reviewer = 完了可（参考指摘 1 件 = 書き手側に「入口で正規化される前提」のコメントが無い → 既存コードの記法で範囲外）。
- 実測: compile clean / `tests` **565**（skip 7・+9）/ `tests_ui` **532** / smoke OK。
  tests_ui の 1 回目に `test_dialog_escape_binding.py` で 3 件 `get_hook_pause_count() 1 != 0` → 再実行で全 pass。
  **既知の flaky（idea_33 の family）で本フェーズの差分〔domain のみ〕とは無関係**。
- 挙動変化: truthy な非文字列（`123` / `["a"]` 等）が repr → `""` になる / `AttributeError` が消える。
  falsy な非文字列は読み手が元々 `or ""` で受けており同値。実機目視は不要（手編集 JSON でのみ到達・単体テストで固定）。
  **非文字列の `type` は「何も送られない（`AttributeError`）」→「`value` を文字列として前面アプリへ入力」に変わった**
  （`{"type": ["hotkey"], "value": "alt+f4"}` → `alt+f4` を文字入力。`sequence_runner.py:65` は例外を捕まえないため以前は無送信）。

## 完了判定前レビュー（2026-09-23）

- `codex-adversarial-reviewer` = needs-attention（**high 1 件**: 上記の非文字列 `type` → 文字入力を新たな実行経路と指摘）。
  `deep-reviewer` = 修正要（文書のみ・軽微。M4 で同じ点を記録漏れとして指摘）。
- **非文字列 `type` の扱い = 案 Y（現状維持）を採用・案 X（読込時に要素ごと除去）は idea_35 で検討**（ユーザー判断 2026-09-23）。
  案 A 確定時の説明表で `{"type": 1, "value": "abc"}` → 文字入力を示していたが安全面の意味は強調しておらず、
  改めて提示した上での判断。空 / 未知の**文字列** `type` の扱いと一括で設計する。**残存リスク**: idea_35 解消まで、
  手編集 JSON 由来の誤入力が黙って起こり得る。
- 反映（修正して採用）: M1 `codebase_map.md`（`normalize_actions` / 内部キーの適用先）/ M2・M3 `current.md`・`phase.md` /
  L1 §5.11 を「無い / 空 / 上表以外」へ / L8 idea_33 へ観測追記 / L10 索引行の表現。
- 保留・除外: L2（`value` の型不正時の実行と表示の食い違い・スコープ外）/ L3（ダイアログの空 `type` = hotkey・idea_35）/
  L4（空 `button` の一覧表示が空欄・既存）/ L5・L7・L11（除外）/ L6（ファイル読込で内部キーを捨てる代替・仕様書側で再検討推奨として参考記録）/
  L9（提案書 12 の参考）。

## refactor_check

- **推奨（境界事例）** → 提案書 [12](../../../instructions/modified_proposal/12_refactor_action_and_internal_key_type_coercion.md)
  （PHASE_BASE `102fdfc`・対象 1 ファイル `domain/config.py` 353 → 361 行）。**M3 該当**: 「キーがあれば `coerce_label`」の 2 行が
  本フェーズで 5 箇所新設。2 行と小さいため境界とし、定性材料（同ファイルに異なる責務のまとまりが 3 つ以上）で推奨に倒した。
  M1 / M2 / M4 / M5 / M6 非該当。**ユーザー判断 = 見送り**（2026-09-23。効果が小さく 5 箇所が同一ファイル内で近接。
  `current.md`「別タスク化候補」の「定数・直値の重複」へ送り、同型がさらに増えたら再判定）。

## 残件

- **idea_35**（空 / 未知 / **非文字列だった** `type` の文字入力を止めるか〔案 B = エラー通知化 / 案 X = 非文字列要素の除去〕・
  ダイアログの空 `type` = hotkey との食い違い）。
- `startup_io.py` の `keymap_set_path`（presentation 層・current.md「別タスク化候補」で追跡中・phase 25 から継続）。
