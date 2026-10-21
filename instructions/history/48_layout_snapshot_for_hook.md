# 暫定仕様 48: 受け取りと送信が同じレイアウトの写しを使う（layout_snapshot_for_hook）

> 状態: **凍結（2026-10-21・正本反映済）**。正本が最新。本書は経緯記録として凍結（v0.3）。
> 正本: `key_input.md` §7.1「フックの実行時のキー名の出どころ」/ §7.7「レイアウトの写し」「押したままのキーは押したときの送り方で送る」・`features.md` §4.6「レイアウトの JSON の `scan_code`」。判断は `.claude_data/state/decisions_archive/65_layout_snapshot_for_hook.md`。
> 凍結時の補足: §5 の「今回の切替では離れず…残り」は、読み直しで id も変わるときは窓を閉じた後の 2 回目の解放で離れる（完了判定前レビューで判明・正本は「残り得る」と記載）。
> 起票元: [idea_51](../backlog/idea_51_layout_snapshot_for_hook.md)（2026-10-18・暫定 45 の Codex 敵対的レビューから分離 + phase 62 の完了判定前レビューの追記）。2026-10-21 ユーザーが着手を判断。

---

## §1 目的 / 背景

フックの受け取り（キー名の解決）が**打鍵ごとに外部レイアウトの JSON を読み直し**、送信は**登録時に読んだ値**を引くため、起動中に JSON を書き換えると受け取りと送信が食い違う。読み直しはフックのスレッドで行われ、失敗時は Tk を操作する。
また、押したままのキー（key_hold）の離しは**離す時点のレイアウトでキー名を引き直す**ため、離しに失敗したまま切り替えると別の走査コードへ離しを送って成功扱いになり、元のキーが OS 上で押されたまま残る（記録も消える）。
**受け取り・送信・画面がレイアウトの写し 1 つを見るようにし、押したままのキーは押したときの送り方で送る**。

### 現状監査（2026-10-21・メインが直読み・deep-reviewer が裏取り）

- `LayoutController.get_current_keyboard_layout`（`presentation/controllers/layout_controller.py:178-193`）: 外部レイアウトなら**呼ぶたびに `load_layout_from_json` で読み直す**（:183-186）。失敗すると `_set_flash_message`（Tk・文言「構成セットの読込に失敗したため…」）を呼び、登録時の `entry.layout` を返す（:188-192）
- 呼び出し元: フックのスレッドの `resolve_key_name_from_scan_code`（:378-381 → `hook_controller.py:297`・`app.py:157`〔`KeyStateManager`〕・`app.py:194`〔`InputRouter`〕）/ 画面の枠の編集の窓（`keymap_panel_controller.py:460`）/ キーボードUI（:42・:169）/ デバッグ判定（:400）
- 送信側 `resolve_scan_code_from_key_name`（:383-387）は `entry.layout`（登録時の値）を引き、entry が無ければ None。`InputGateway` へ注入（`app.py:138`）
- 写しの元: `_keyboard_layout_entries`（`__init__` で `{}`・:28-29 / `reload_keyboard_layouts` で丸ごと差し替え・:205-211）と `keyboard_layout_id`（:236・:273 で差し替え）の**2 つの属性**を読み手が別々に読む
- 差し替えの前の解放: `reload_keyboard_layouts`（:206）と選び直し（:235・:272 〔id が変わるときだけ〕）が `_release_held_inputs_before_layout_change`（:213-225）→ `held_inputs.release_all()`。解放の失敗は `hook.show_action_error`（モーダルの messagebox・`hook_controller.py:401`）で知らせる
- スレッド: アクションの実行は `after(0)` で **UI スレッド**（`hook_controller.py:308-311`・:334-339）。keyseq の別スレッドは file_line の読込（`file_line_loader.py:83`）と遅延呼び出し（`delayed_calls.py:33`・行き先は `after` で UI スレッドへ戻る〔`app.py:204`・`hook_controller.py:350-354`〕）だけ。**写しの読み手で UI スレッドの外にいるのはフックのスレッドだけ**
- **押したままのキーの記録**（`application/held_inputs.py`）: `HeldInput(name, owner, order)`（:16-20）を `(kind, scan, extended)` の identity（押した時点のレイアウトで `input_gateway.key_identity` が引く・:85-87）で持つ。**離し・一時的な離し・押し直し・リピートの送り直しは `record.name`（キー名）を `input_gateway.press_key` / `release_key` に渡し、gateway がその時点のレイアウトで引き直す**（:145・:184・:207・:243・:257）。`release_key(key)`（:180-185）は identity も今のレイアウトで引き直す。押し直し（`resume_keyboard`）は公開の `press_key(owner, name)` を経由する（:257）。`_release_records` は離す前に `_stop_repeat` を呼ぶ（:205）
- リピーター（`application/key_repeat.py`）: 送信の callback は `send(key)`（キー名だけ・:35-41・:101）
- gateway（`infrastructure/input_gateway.py:198-222` `_resolve_key`）: テンキー → 拡張キー（vk と走査コード）→ keyboard の名前（**キー名で `keyboard.press` / `release`**・:288・:300）→ レイアウトの `scan_code`（注入された関数・:211-221）の順。**レイアウトに依存するのは最後の「layout」だけ**
- 組み込みのレイアウトは `scan_code` を持たない（`scan_code` は JSON の読込でだけ入る・`keyboard_layouts.py:252`）。`KeyboardLayout` は不変（`frozen=True`・:22-23）
- 依存: application は `held_inputs.py` で infrastructure を import していない（gateway を型を知らずに呼ぶ）
- 正本: `key_input.md:13`・:201（4 は登録済みのレイアウトを引く）・:205-214（レイアウトが変わる前に離す・受容 :212〔受け取りは呼ぶたびに読み直す〕・:213〔離しの失敗と切替〕・:214〔ロックを持たない〕）/ `features.md:713`

## §2 確定事項（ユーザー 2026-10-21）

- idea_51 を phase 65 で扱う・暫定仕様先行モード
- **外部レイアウトの JSON の変更は、選び直し・読み直し（起動・追加・削除・構成の読込）のときだけ反映する**（ファイルの監視はしない）
- **押したままのキーは押したときの値で送る**（`held_inputs` の記録に送り方を持たせる。phase 62 で受容した「離しの失敗と切替で記録が消える」を直す）
- **ユーザーがレイアウトを選んだときも外部レイアウトの JSON を読み直す**（同じレイアウトの選び直しでも。Codex 敵対的 high の指摘・2026-10-21 ユーザー確定。§3-2）
- **1 打鍵の中で受け取りの判定と押下状態の記録が別の写しで名前を引き得るのは受容**（切替の瞬間だけ・今の作りでも起きる。Codex 敵対的 medium の指摘・2026-10-21 ユーザー確定。§5）

## §3 レイアウトの写し（presentation・`LayoutController`）

1. `LayoutController` に**写し** `_active_layout`（不変の `KeyboardLayout` 1 つ）を持つ。**初期値は組み込みの既定**（`BUILTIN_LAYOUTS[DEFAULT_LAYOUT_ID]`・`__init__` で入れる）。読み手は 1 回の参照で取り出す
2. 差し替えは **UI スレッドだけ**で、1 回の代入で行う（`entries[keyboard_layout_id].layout`・無ければ組み込みの既定）。差し替える契機:
   - `sync_keyboard_layout_controls` と `set_keyboard_layout_selection` で `keyboard_layout_id` を決めた直後に**毎回**（id が変わらなくても。読み直しで同じ id の中身が変わるため）
   - `reload_keyboard_layouts` は entries を差し替えた後に `sync_keyboard_layout_controls` を呼ぶ（:211）ので、そこで差し替わる
   - **ユーザーがドロップダウンで選んだとき**（`on_keyboard_layout_selected`・:288-290・フル表示と省略表示の 2 つのコンボ）: 選んだ id を `data["keyboard_layout"]` に入れてから `reload_keyboard_layouts()` を呼ぶ（解放 → JSON の読み直し〔entries の差し替え〕→ `sync` で id を決めて写しを差し替え）→ 今と同じく保存（`persist_keyboard_layout_selection`）。読み直しで選んだレイアウトが外れたら（JSON が壊れた等）既定へ戻る（§3-4 と同じ）。プログラムからの `set_keyboard_layout_selection`（削除の後 :349 等）は読み直さない（今と同じ）
   - **差し替えの前の `release_all` は今の順のまま**（解放 → 写しの差し替え）
3. 読み手はすべて写しを引く:
   - `get_current_keyboard_layout()` → 写しを返す（**ファイルを読み直さない・Tk を操作しない**。:183-192 の読み直しと失敗の通知を削除）
   - `resolve_key_name_from_scan_code` / `resolve_scan_code_from_key_name` / デバッグ判定 → 写しを 1 回取り出して引く（`keyboard_layout_id` と `_keyboard_layout_entries` を別々に読まない）
   - 最初の読み直しの前は組み込みの既定を引く。組み込みは `scan_code` を持たないので、送信側の結果は今（entry が無ければ None）と同じ
4. 外部レイアウトの読込失敗は**読み直しのとき**（`collect_keyboard_layouts`）だけ起き、今と同じく一覧から黙って外れ、選んでいれば既定へ戻る（`data["keyboard_layout"]` も書き換わる・:232・:237）= 受容（今と同じ。削除する通知は文言も内容と合っていなかった）
5. 結果: 起動中に JSON を書き換えても、選び直し・読み直しまでは受け取りも送信もキーボードUI も**古い写しのまま一致**し、選び直し（同じレイアウトでも）・読み直しの後は全部新しい値になる

## §4 押したままのキーを押したときの送り方で送る（application `held_inputs`・`key_repeat` + infrastructure `input_gateway`）

1. gateway に「キー名 → **送り方**」の解決と、送り方での送信を分けて公開する:
   - `resolve_send(key) -> KeySend`: `KeySend` は**infrastructure の不変の値**（`frozen=True` の dataclass）。中身 = 解決の種類（numpad / extended / keyboard / layout）・値（`_resolve_key` の結果。extended は vk と走査コード）・**キー名**（keyboard の種類は今と同じくキー名で `keyboard.press` / `release` するため）
   - `press_send(send)` / `release_send(send)` / `identity_of(send) -> (scan, extended)`（今の `key_identity` の中身）
   - 既存の `press_key(key)` / `release_key(key)` / `key_identity(key)` は `resolve_send` + 上の関数で書き直す（呼び出し元・送り方・挙動は不変）
2. **application は `KeySend` の型を import しない**: `HeldInput` に `send: object | None`（中身を知らない値・キーボードのとき）を足し、gateway から受け取った値をそのまま gateway へ返すだけにする（application → infrastructure の依存を増やさない）
3. **押すとき**（`press_key(owner, key)`）: `resolve_send(key)` を 1 回だけ呼び、identity（`identity_of`）と記録の送り方を同じ値から作る。送信は `press_send`、補償の離し（`_press` の `release`）は `release_send`（同じ送り方）
4. 記録のある押したままのキーの次の送信は**記録の送り方**を使う（今のレイアウトで引き直さない）:
   - 離す: `_release_records`（`release_owner` / `release_all` / `release_keyboard`）・`release_key` で記録が見つかったとき（4-6）
   - text の前後の一時的な離し（`_suspend_keyboard`）と押し直し（`resume_keyboard`）: 押し直しは公開の `press_key` を経由せず、**記録の送り方で `press_send` する内部の道筋**にする（identity・送り方を引き直さない）。押し直しの失敗の補償（補償の離しが成功すれば記録を消す・:112-117）は今と同じ
5. **リピートの送り直し**: `KeyRepeater` の送信の callback を `send(identity, key)` に変える（`key_repeat.py:35-41`・:101。key は表示・エラー用に残す）。`held_inputs._send_repeat(identity, key)` は identity の記録の送り方で `press_send` する。**記録が無ければ送らずリピートを止める**（離された・切り替わった後に古い対象を送らない）。リピートの失敗の後始末（`_repeat_failed`）も identity の記録で離す
6. `release_key(key)`（key_hold の「離す」アクション）: 今のレイアウトで identity を引き、**記録があればその送り方で離す**。記録が無ければ今のレイアウトで引いて離す（今と同じ）
   - 受容: 離すアクションのキー名が切替の後に別のキーへ解決されるときは記録と一致せず、今のレイアウトのキーを離す（記録のキーは `release_all` 等で離れる）
   - 受容: キー名が今のレイアウトで解決できないときは今と同じく ValueError（記録は `release_all` 等で離れる）
7. 離しに失敗した記録は今と同じく残り、**再試行は記録の送り方で送る**（別の走査コードへ送って成功扱いにならない）

## §5 切替の前後の隙間（受容の整理）

- 写しの読み手のうち UI スレッドの外にいるのはフックのスレッドだけ（§1）。各解決は差し替えの直前と直後のどちらかの写しを使い（1 回の参照なので 1 回の解決の中では混ざらない）、差し替えと同時に届いた 1 打鍵が古い写しで解決されるのは受容。ロックは足さない
- **1 打鍵の中の 2 回の解決は混ざり得る（受容・§2）**: `InputRouter.handle` はキー名を引いた後（`input_router.py:95`）に `KeyStateManager.handle_event` を呼び、記録の側でもう一度引く（`key_state_manager.py:63`・:95-105）。この間に写しが差し替わると、判定は古い名前・押下状態の記録は新しい名前になり、次の押下のリピートの判定がずれ得る。切替の瞬間に押したときだけで、今の作り（打鍵ごとの読み直し）でも同じ。解決済みの名前を渡す形は本フェーズではしない
- :214 の隙間の実際の経路は、**解放の失敗を知らせるモーダルの窓**（`show_action_error`）が入れ子のイベントループを回す間に、予約済みの key_hold が UI スレッドで押されること。本書の後は「その記録は古い写しの送り方で記録され、今回の切替では離れず切替の後も押したまま残り、後で記録の送り方（古い値）で離れる」= 受容（キーが残り続けることはない）

## §6 確認事項（ユーザー判断）

- なし（§2 で確定。v0.2 の判断はメイン: `KeySend` は application では中身を知らない値〔依存方向〕/ リピートの記録が無ければ止める / 解決できないキー名は今と同じエラー）

## §7 受け入れ条件（ドラフト）

1. フックの受け取りはファイルを読まず、UI スレッドの外で Tk を操作しない（§3-3）
2. 起動中に外部レイアウトの JSON を書き換えても、選び直し・読み直しまでは受け取り・送信・キーボードUI が同じ（古い）値を使い、読み直しの後は全部新しい値になる（§3-5）
3. **切替の後に残った押したままのキーの記録**（離しに失敗した記録・§5 の窓の間に押した記録）は、押したときの送り方で離れる・押し直される（§4-4・§4-7）
4. リピートの送り直しは記録の送り方で送り、記録が無ければ送らず止まる（§4-5）
5. 既存の `press_key` / `release_key` / `key_identity` の送り方と挙動は不変（keyboard の種類はキー名で送る・§4-1）
6. tests / tests_ui / smoke が通る
7. 実機目視: ① jis.json を選んだまま JSON の `muhenkan` の `scan_code` を書き換えても、選び直す（**同じ jis.json をドロップダウンで選び直す**・別のレイアウトを経由して戻す）・再起動するまではキーボードUI の表示も受け取りも変わらず、選び直した後は変わる ② jis.json の `muhenkan`（レイアウトの `scan_code` で送るキー）を key_hold で押したまま別のレイアウトへ選び直すと離れる（今と同じことの確認）

## §8 スコープ外

- ファイルの変更の監視・自動の読み直し（§2）
- 読込失敗の通知の追加（§3-4）
- レイアウトの JSON の書式
- 送信の最中の物理の入力（idea_53・保留）

## §9 正本反映（フェーズ末昇格・予定）

- `key_input.md` §7.7: :201（登録済みのレイアウト → 写し）・:205-214（解放の後に写しを差し替える・受容 :212 を削除・:213 を「押したときの送り方で送る」へ・:214 を §5 の受容へ）/ §7.1 :13（フックの実行時のキー名は写しを引く）
- `features.md` §4.6 :713（外部レイアウトの JSON の変更は選び直し・読み直しのときに反映）
- `codebase_map.md`: `LayoutController`（写し）・`held_inputs`（送り方の記録）・`key_repeat`（送信の callback）・`input_gateway`（`KeySend` / `resolve_send` / `press_send` / `release_send` / `identity_of`）
- 実装: `keyseq/presentation/controllers/layout_controller.py`・`keyseq/application/held_inputs.py`・`keyseq/application/key_repeat.py`・`keyseq/infrastructure/input_gateway.py`
- テスト（偽 gateway・偽リピーターの更新を含む）: `tests/test_layout_controller_scan_code.py`（:43 の `object()` の entries・:154-170 の書き直し）・`tests/test_held_inputs.py`・`tests/test_held_inputs_repeat.py`・`tests/test_action_executor_key_hold.py`・`tests/test_sequence_runner_key_hold.py`・`tests/test_key_repeat*.py`（あれば）・`tests/test_input_gateway_send.py`

## 関連

- [idea_51](../backlog/idea_51_layout_snapshot_for_hook.md)
- [暫定 45](45_special_keys_from_layout_only.md)（凍結・§6 の受容）/ phase 62 task_04b（構成の読込でも読み直す）
- 正本 `key_input.md` §7.1・§7.7 / `features.md` §4.6

## 改訂履歴

- v0.1（2026-10-21）: 起票
- v0.3（2026-10-21）: Codex 敵対的 needs-attention 2 件をユーザー判断で反映 = ユーザーの選び直しでも JSON を読み直す（§3-2）/ 1 打鍵の中の 2 回の解決の混在は受容（§5）。ユーザー確定・実装着手可
- v0.2（2026-10-21）: 起票時 deep-reviewer「修正して採用」を反映 = `KeySend` にキー名（keyboard の種類は名前で送る）・extended は vk も / `KeySend` は infrastructure の値で application は中身を知らない / リピートの callback に identity を渡し記録が無ければ止める / 写しの初期値と毎回の差し替え・最初の読み直し前の送信側 / 受け入れ条件 3 の範囲と実機目視の差し替え / 偽 gateway のテストの追加 / 押し直しの内部の道筋 / 解決できないキー名 / 行番号の修正 / 「実行用のスレッド」の誤りを §5 の窓の経路へ / 読込失敗で既定へ戻る受容
- 凍結（2026-10-21）: phase 65 task_03 で正本へ反映
