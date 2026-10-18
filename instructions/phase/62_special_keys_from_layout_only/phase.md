# phase.md

## フェーズ名

特殊キーの名前をレイアウトだけが決める（special_keys_from_layout_only）

## フェーズの目的

JIS の特殊キー（無変換・変換・かな・半角/全角）の名前を、コードに直書きした既知の表ではなく**選んでいるレイアウトの `scan_code` だけ**で決める。
受け取る側（フックの実行時・画面の枠の編集の窓）と送る側（出力・キーマップの送信先）の両方でレイアウトを名前の出どころにし、既知の表は削除する。
あわせて、今は検査を通るのに送れない `muhenkan` 等を、レイアウトの `scan_code` で実際に送れるようにする。
**影響レイヤ = domain（既知の表の削除）・presentation（レイアウトの解決・`LayoutController`・`app.py` の注入）・infrastructure（`InputGateway` の送信・検査・同じキーの判定）。application はレイアウトが変わるときの離しの呼び出し先（`held_inputs.release_all`）のみ。**レイアウトの JSON に任意キー `extra_scan_codes` を追加（v0.4・既存キーは不変）。設定・キーマップの JSON は不変。**

- 起票元: [idea_49](../../backlog/idea_49_special_keys_from_layout_only.md)（2026-10-17・phase 61 の起票時の議論から分離）。
- 主入力（暫定仕様）: [45_special_keys_from_layout_only.md](../../history/45_special_keys_from_layout_only.md)（v0.4・ユーザー確定済）。
- モード: **暫定仕様先行モード**。番号対応: phase 62 / 暫定 45 / decisions 62。

## 確定（ユーザー 2026-10-18）

- 受け取る側は既知の表を外し、レイアウトの `scan_code` だけで名前を引く（引けなければ `event.name`）（暫定 45 §2・§3）
- 送る側は テンキー → 拡張キー → keyboard → 選んでいるレイアウトの `id` → `scan_code` の順に引く。既知の表は削除する（§2・§4・§5）
- 特殊キーを書いていないレイアウト（既定の US TKL 等）では `muhenkan` 等は送れない。後方互換は考慮しない（§2）
- **v0.4（2026-10-18・実機目視の実測から）**: この PC では無変換 = 241・変換 = 242 でフックに届く（IME の割り当てで走査コードが変わる）。レイアウトの行に受け取り専用の `extra_scan_codes` を書けるようにし、jis.json に 241 / 242 を足す（§3.1・案 B）。送信（123 / 121）は実機で OK
- レイアウトが変わるとき（読み直し・選ぶ id の変更）は、置き換える前に押したままのキーをすべて離す（§6・案 B）。起動中の JSON の書き換えによる受け取りと送信のずれは受容し、同じ写しを使う形は [idea_51](../../backlog/idea_51_layout_snapshot_for_hook.md) へ分離

## スコープ

### 含む

- 受け取る側の既知の表への落とし込みの撤去・デバッグ出力の判定の置き換え（§3）
- 送る側の解決の一本化・レイアウトの `scan_code` を `SendInput` の走査コード入力で送る経路・検査と同じキーの判定・`InputGateway` への関数の注入（§4）
- 既知の表と参照元・関係するテストの削除 / 置き換え（§5）
- レイアウトが変わる前の `release_all`（§6）
- 受け取り用の追加の走査コード `extra_scan_codes`（§3.1）
- 実機目視（ユーザー・JIS キーボード・jis.json）（§7 #12）
- 正本反映（§9）

### 含まない（後送り）

- キーの取得（Tk）で JIS の特殊キーを取る（idea_50）/ 受け取りと送信で同じレイアウトの写しを使う（idea_51）
- 既存の構成の `muhenkan` 等の移行・警告 / レイアウトの JSON の書式変更（§8）

## このフェーズで読むファイル

1. 暫定仕様 45（全節。§1 の現状監査が読む箇所の索引）
2. `keyseq/domain/key_identifiers.py`
3. `keyseq/presentation/keyboard_layouts.py:327-352`（`resolve_layout_key_id_from_scan_code` / `resolve_key_id_from_scan_code`）
4. `keyseq/presentation/controllers/layout_controller.py:178-260` / :357-390（取得・読み直し・選択・名前の解決・デバッグ出力）
5. `keyseq/infrastructure/input_gateway.py:133-190`（`SendInput` の経路）/ :246-350（送信・検査・同じキーの判定）
6. `keyseq/presentation/app.py:130-240`（`InputGateway` と `LayoutController` を作る順）
7. `keyseq/application/held_inputs.py:194-222`（`release_all`）
8. テスト: `tests/test_key_identifiers.py`・`tests/test_input_gateway_send.py`・`tests/test_keyboard_layout_files.py`
9. 正本: `key_input.md` §7.1 / §7.4 / §7.7 / §7.8・`features.md` §4.6「レイアウトの JSON」・`codebase_map.md`

## タスク

- task_01: 受け取る側（§3）。`resolve_key_id_from_scan_code` の既知の表への落とし込みを撤去してレイアウトだけで引く関数へ一本化・デバッグ出力の判定の置き換え・テスト（`tests/test_keyboard_layout_files.py:6` / :38 の置き換えを含む）。送信側の既知の表の参照は task_02 まで残る（仕様どおりの途中の状態）
- task_02: 送る側と既知の表の削除（§4・§5）。`keyboard_layouts` の純関数・`LayoutController` の「キー名 → 走査コード」・`InputGateway` の解決の一本化と走査コードでの送信・注入（`app.py`）・既知の表と参照元の削除・テスト
- task_03: レイアウトが変わる前の離し（§6）・テスト。**実装後にユーザーの実機目視**（§7 #12）
- task_03b: 受け取り用の追加の走査コード `extra_scan_codes`（暫定 45 §3.1・v0.4 で追加〔2026-10-18 の実機目視で無変換・変換が 241 / 242 で届くと判明〕）。読込・`KeySpec`・受け取りの照合・デバッグ出力の判定・見本 jis.json・テスト。**実装後にユーザーの実機目視**（無変換・変換の受け取り）
- task_04: 正本反映（§9）・暫定 45 の凍結・`decisions_archive/62_special_keys_from_layout_only.md`・decisions.md の索引・current.md の完了記載・idea_49 を INDEX_done へ・`/refactor_check`・完了判定前レビュー

## レビュー方針

- 各タスク: `reviewer`（5 観点）・既存テスト（tests / tests_ui / smoke）の通過を完了条件に含める
- 重点:
  - 依存の向き: infrastructure がレイアウトを直接読まない（関数を外から受け取る・§4.4）
  - 送信側の引きが UI スレッドの外で安全: ファイルの読み直しも Tk の操作もしない（§4.4）
  - 解決の順（テンキー → 拡張 → keyboard → レイアウト）が送信・検査・同じキーの判定で一致している（§4.1）
  - keyboard が知る名前の送信が変わっていない（§7 #6）
  - 既知の表の参照が残っていない（§5）
  - 離しは置き換えの前に呼ばれ、id が変わらない選び直しでは離さない（§6）
- 完了判定前: `deep-reviewer` + `codex-adversarial-reviewer`
