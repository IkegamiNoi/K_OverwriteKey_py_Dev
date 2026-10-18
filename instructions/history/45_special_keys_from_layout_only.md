# 暫定仕様 45: 特殊キーの名前をレイアウトだけが決める（special_keys_from_layout_only）

> 状態: **未凍結・v0.5・主入力・ユーザー確定済（2026-10-18）**（v0.1 起票 → v0.2 deep-reviewer「修正して採用」の反映 → v0.3 Codex 敵対的レビューの指摘を §6 案 B で反映〔ユーザー判断〕→ v0.4 実機目視の実測で §3.1 受け取り用の追加の走査コードを追加〔ユーザー判断 案 B〕・Codex 敵対的レビューの指摘 2 件〔修飾キーの禁止の適用・受け取り専用の行の送信〕を反映 → v0.5 実機目視で押下だけが続けて届くキーと判明し §3.1 を取り下げ〔ユーザー判断 A・idea_52 へ〕）。本書がこのフェーズの確定設計（フェーズ中は正本を直接改訂しない）。
> フェーズ末タスクで正本 `instructions/common/spec_detail/` へ昇格し本書を凍結する。
> 起票元: idea_49（2026-10-17・phase 61 の起票時の議論から分離）。番号対応: phase 62 / 暫定 45 / decisions 62。

---

## §1 目的 / 背景

JIS の特殊キー（無変換・変換・かな・半角/全角）の名前を、コードに直書きした既知の表ではなく
**選んでいるレイアウトの `scan_code` だけ**で決める。受け取る側（フックの実行時・画面の枠の編集の窓）と
送る側（出力・キーマップの送信先）の両方でレイアウトを名前の出どころにし、既知の表は削除する。

### 現状監査（2026-10-18）

- 既知の表: `keyseq/domain/key_identifiers.py:6`（`muhenkan` 123 / `henkan` 121 / `kana` 112 / `zenkaku_hankaku` 41）。
  `SPECIAL_KEY_NAMES`・`resolve_known_scan_code_from_key_name`・`resolve_known_key_name_from_scan_code`・`is_special_key_name`
- 受け取る側: `presentation/keyboard_layouts.resolve_key_id_from_scan_code`（:343）= レイアウト → 既知の表。
  `LayoutController.resolve_key_name_from_scan_code`（`layout_controller.py:357`）経由で
  フック（`hook_controller.py:290`・`application/input_router._extract_key_name` :184・`key_state_manager` :100）と
  画面の枠の編集の窓（`keymap_panel_controller.py:460`）が使う。引けなければ `event.name`
- 既定のレイアウト = 組み込みの US TKL（`keyboard_layouts.py:127`）。**`scan_code` を 1 つも持たない**。
  見本の `config/user/keylayout/jis.json` は特殊キー 4 つだけ `scan_code` を持つ（他 20 行は持たない）
- 送る側（`infrastructure/input_gateway.py`）:
  - `validate_key_name`（:338）・`key_identity`（:305）は keyboard → 既知の表
  - **実際の送信（`press_key` :246 / `release_key` :257 / `send_hotkey` :268）は既知の表を見ず keyboard に名前を渡す**。
    2026-10-18 実測: `keyboard.parse_hotkey('muhenkan')` は `ValueError`（not mapped）。
    つまり今は `muhenkan` 等が**検査は通るが送れない**（実行時エラー）。idea_49 の「既知の表の走査コードで送る」は誤り
  - 同実測: keyboard は JIS 環境の OS の名前 `無変換` / `変換` / `半角/全角` / `ひらがな` を知っている（123 / 121 / 41 / 112）。`grave` → 26
- 検査の呼び出し元: `action_executor.py:278`・`hotkey_service.py:20`（利用者に `preset_manager.py:318` / :354 も）・`keymap_add_flow.py:116`・
  `keymap_panel_controller.py:231` / :645・`key_capture.py:162`・`action_dialog.py:238`
- 押下中の同一キー判定: `application/held_inputs._key_identity`（:85）→ `input_gateway.key_identity`
- デバッグ出力（`debug_jis_special_key_events`）: `LayoutController.should_debug_special_key_event`（:360）が
  `is_special_key_name` / `SPECIAL_KEY_NAMES` を使う
- 正本: `key_input.md` §7.4（:89〜93 の受容）・§7.7（送信）・§7.8（:195 同じキーの判定の「JIS の特殊キーの表」）/
  `features.md` §4.6「レイアウトの JSON」/ `codebase_map.md:126`

## §2 確定事項（ユーザー 2026-10-18）

- **受け取る側は既知の表を外し、選んでいるレイアウトの `scan_code` だけで名前を引く**。引けなければ従来どおり
  keyboard の `event.name`（US 入力配列の「`」は `grave` 系になり、`zenkaku_hankaku` にならない）
- **送る側は keyboard ライブラリ → 選んでいるレイアウトの `id` → `scan_code` の順に引く**。既知の表は削除する
- **既定の US TKL など特殊キーを書いていないレイアウトを選んでいるときは、`muhenkan` 等は送れない**（検査でエラー）
- **後方互換は考慮しない**（既存のキーマップ・トリガーの `muhenkan` 等が、jis.json 以外では効かなくなってよい）
- **レイアウトが変わるときは、置き換える前に押したままのキーをすべて離す**（§6・案 B。起動中の JSON 書き換えによる受け取りと送信のずれは受容）
- （v0.4 で追加し v0.5 で取り下げ）受け取り用の追加の走査コード `extra_scan_codes`（§3.1。押下だけのキーへの対応と合わせて idea_52 へ）

## §3 受け取る側（名前の解決）

- `resolve_key_id_from_scan_code` の既知の表への落とし込みをやめ、レイアウトだけで引く関数
  （`resolve_layout_key_id_from_scan_code`）に一本化する。`LayoutController.resolve_key_name_from_scan_code` はそれを使う
  （中間の関数は残さない・恒久互換レイヤー禁止）
- 影響: フックの実行時の名前（トリガー・直接置換の元・切替 / 停止 / トグルキー・押下状態・重なり判定）と画面の枠の編集の窓。
  テンキーの名前を採らないガード（§7.8）は従来どおり
- JIS キーボードで jis.json 以外を選んでいるとき、特殊キーは `event.name`（keyboard が OS から得た名前。
  JIS の Windows では `無変換` 等の見込み・**`event.name` の値は未確認**）になる＝受容
- デバッグ出力の対象の判定: 既知の名前の判定をやめ、**イベントの走査コードが選んでいるレイアウトの `scan_code` を持つ行に当たるとき**に出す
  （jis.json なら特殊キー 4 つ。設定キー `debug_jis_special_key_events` の名前・既定値は変えない）。
  受容: 特殊キーを書いていないレイアウト（US TKL 等）では何も出ない
- 受け取る側の外部レイアウトの取得（`get_current_keyboard_layout` が呼ぶたびに JSON を読み直す・`layout_controller.py:178`）は変えない（既存の挙動・本フェーズの範囲外）

### §3.1 受け取り用の追加の走査コード（v0.4 で確定・**v0.5 で取り下げ** 2026-10-18 ユーザー判断 A）

> **取り下げの理由（2026-10-18 実測）**: 低レベルフックの生の値で、無変換・変換は **1 回押すと押下（`vk=0x1A` / `0x16`・走査コード 241 / 242・`ext=1`）が約 60 ms に 3 回届き、離しは届かない**と分かった。
> MS-IME のキーの割り当てはオフで、`Scancode Map` も置き換えの常駐ツールも無い（OS のキーボードは `PCAT_106KEY`）。キーボード本体が LANG2 / LANG1 として送っている見込み（未確認）。
> この形では、2 回目の押下が送信ガードの最中に届いて素通りし（`input_router.py:88-90`・IME が切り替わる）、3 回目で再び置換して二重送信になる。押下状態にも残る。
> task_03b（722a1e9）は戻した。押下だけのキーへの対応と `extra_scan_codes` の設計は [idea_52](../backlog/idea_52_make_only_keys.md) で扱う。以下は v0.4 の記録として残す（実装の根拠にしない）。

**背景（2026-10-18 実測）**: Windows 11・JIS・MS-IME の PC で、フック（keyboard）に届く走査コードを測った。
無変換 = **241**・変換 = **242**（name は `None`）・半角/全角 = 41・かな = 112。
MS-IME の割り当て（無変換 = IME オフ / 変換 = IME オン）によって、Windows が `VK_IME_OFF` / `VK_IME_ON` に置き換え、走査コードも 241 / 242 に変えていると見られる（phase 61 の `MapVirtualKeyW(0x1A / 0x16)` = 241 / 242 と一致）。
同じ物理キーでも、IME の設定によって走査コードが変わる（割り当てを変えていない環境では 123 / 121 の見込み・未確認）。
前の既知の表も 123 / 121 だけだったので、この環境では元から効いていなかった（退行ではない）。

- **レイアウトの行に任意キー `extra_scan_codes`（整数の配列）を足せる**（JSON スキーマの追加・既存キーは不変）
  - 受け取る側は、イベントの走査コードが **`scan_code` か `extra_scan_codes` のどれかに一致する最初の行**の `id` を名前にする
    - 行の順に見て、行ごとに `scan_code` → `extra_scan_codes` の順に照合する
    - テンキーの名前を採らないガード（§7.8）は同じに効く
  - **送る側は `scan_code` だけを使う**（§4.1-4 は変えない。`extra_scan_codes` は送信・検査・同じキーの判定に使わない）
    - `scan_code` が無く `extra_scan_codes` だけの行は、§4.1-4（レイアウト由来の送信）の候補にならない。
      その `id` が §4.1 の 1〜3（テンキー・拡張キー・keyboard）で決まる名前なら、それで送る（例: `id: "a"` の行は通常の A キーで送る）。決まらなければ送れない
  - **修飾キー・Caps Lock・Windows キー・AltGr の行に `extra_scan_codes` を書かない**（`features.md` §4.6 の `scan_code` の禁止と同じ理由・同じく規定のみでコードでは防がない）。
    これらのキーの走査コードを、別の行の `extra_scan_codes` に書くことも同じく書かない（書くとフックの名前がその `id` に変わり、修飾キーの押下状態・Windows 押下中の素通し等が効かなくなる）
  - 同じ走査コードを複数の行が持つ（`scan_code` 同士・`extra_scan_codes` との重なりを含む）ときは、行の順で最初の行を採る。読込で拒否しない
  - 読込の検証:
    - 無い・`null` → 空として扱う
    - 配列でなければ読込エラー（他の項目の検証と同じく `ValueError`・`keys[i].extra_scan_codes`）
    - 要素は `_coerce_int` で整数にする。整数にできなければ読込エラー
    - 値の範囲は問わない（keyboard は走査コード 0 のとき -VK を渡すため・`keyboard/_winkeyboard.py:529`）
  - `KeySpec` に `extra_scan_codes: tuple[int, ...] = ()` を足す（組み込みの US TKL は空のまま）
  - **キーボードUI の取得**（phase 61・`keyboard_window.py:534` が `resolve_layout_key_id_from_scan_code` を使う）にも同じく効く
    - VK から変換した走査コードが `extra_scan_codes` に当たれば、その `id` になる
    - JIS の特殊キーは今は Tk に届かないため、実害も効果もない（idea_50）
  - デバッグ出力の対象（§3）も `extra_scan_codes` を含めて判定する
- **見本 `config/user/keylayout/jis.json`**: `muhenkan` に `"extra_scan_codes": [241]`、`henkan` に `"extra_scan_codes": [242]` を足す（`scan_code` 123 / 121 は送信用に残す）
- 受容: 送信の 123 / 121 が、241 / 242 の環境でも物理キーと同じ動きになることは、2026-10-18 の実機目視（出力の `muhenkan` で確認済み）による。他の環境・他の IME は未確認

## §4 送る側（名前 → 走査コード）

### §4.1 解決の順

キー名ごとに次の順で決める（先に当たったもので送る）。

1. テンキーの名前（§7.8・従来どおり）
2. §7.7 の拡張キー（従来どおり）
3. keyboard ライブラリが知る名前（`keyboard.key_to_scan_codes` が**成功し、結果が空でない**・従来どおり）
4. **選んでいるレイアウトの行のうち、`normalize_key_name(id)` が `normalize_key_name(キー名)` と一致し `scan_code` を持つ最初の行の `scan_code`（新規）**。
   値が **1〜255 の範囲外なら当たらない**（`wScan` は 16 ビットで、範囲外は ctypes が黙って切り詰め別のキーを送るため。読込の検証〔`keyboard_layouts.py:207`〕は変えない）
5. どれにも当たらなければ「不明なキー」（`ValueError`・従来どおり）

- 3 を 4 より先にする理由: keyboard は OS の今の入力配列から走査コードを決めており、知っている名前はそれが正しい。
  レイアウトは keyboard が知らない名前を補う役に限る
  （受容: レイアウトに keyboard が知る名前の `id` と別の `scan_code` を書くと、受け取りはレイアウトの名前・送信は keyboard の走査コードでずれる。規定のみでコードでは防がない）
- 4 は**送信の時点で選んでいるレイアウト**を引く（レイアウトの切替は即時に効く）
- 受容: 拡張キーの走査コード（例 72 = Up）を書いた行は、受け取りでは本物の Up にも当たるが、送信は拡張なしで送る（テンキーの 8 になる）。規定のみ（`features.md` §4.6 へ反映）
- **1〜5 の判定は `InputGateway` 内の 1 つの関数**にまとめ、`press_key` / `release_key` / `send_hotkey` / `key_identity` / `validate_key_name` が共通に使う
  （今は `press_key` / `send_hotkey` が keyboard へ名前を直接渡している）

### §4.2 送り方

- 4 で決まったキーは **`SendInput` の走査コード入力（`KEYEVENTF_SCANCODE`・拡張なし）**で送る
  （§7.8 のテンキーと同じ経路: send_guard の中・keyboard の押下記録に載せない・keyboard の名前の API に渡さない）
- `send_hotkey`: 組み合わせに 4 のキーを含むときは、拡張キー・テンキーを含むときと同じく記述順に押し逆順に離す
  （`keyboard.send` へまとめて渡すのは、全キーが 3 で決まるときだけ）
- `press_key` / `release_key`（key_hold・キーリピート・直接置換の送信先）も同じ順で決める

### §4.3 検査・同じキーの判定

- `validate_key_name`・`key_identity` も §4.1 の順に一本化する（4 の同じキーの判定 = その `scan_code` + 拡張なし）
- **検査は選んでいるレイアウトで結果が変わる**。保存済みのキーマップ・出力はレイアウトを切り替えても再検査しない。
  送れない名前は実行時エラー（従来の「不明なキー」と同じ扱い）

### §4.4 依存の向き

- infrastructure（`InputGateway`）はレイアウトを直接読まない。**「キー名 → 走査コード | None」を返す関数を外から受け取る**
  （受け取る側の `resolve_scan_code` を `KeyStateManager` へ渡しているのと同じ形）
- 供給元: `LayoutController` に「キー名 → 走査コード」を追加し、その中身は `keyboard_layouts` の純関数
  （レイアウト・キー名 → 走査コード | None）に置く
- **渡し方**: `app.py:133` の `InputGateway(...)` のコンストラクタに遅延評価の lambda（`lambda name: self.layout.resolve_scan_code_from_key_name(name)`）を渡す
  （`LayoutController` は :239 で作られるため。それより前に呼ばれれば例外 → 下の「当たらない」）
- **UI スレッドの外から呼ばれる**（実行用のスレッド・リピートの周期 33 ms）。そのため送信側の引きは**登録済みのレイアウト（`entry.layout`・読込済みの値）を読むだけ**にし、
  ファイルの読み直し・Tk の操作（`_set_flash_message` 等）をしない。読むだけなのでロックは要らない
- 関数が未設定・例外のときは 4 を「当たらない」とみなす（送信全体を止めない）

## §5 既知の表の削除

- `domain/key_identifiers.py` から特殊キーの表と `SPECIAL_KEY_NAMES`・`resolve_known_*`・`is_special_key_name` を削除する
  （割り当て禁止の `PROHIBITED_ASSIGN_KEY_NAMES` / `is_prohibited_assign_key` は残す）
- 参照元（`input_gateway.py`・`keyboard_layouts.py`・`layout_controller.py`）とテスト
  （`tests/test_key_identifiers.py`・`tests/test_input_gateway_send.py:393` 付近の `muhenkan` の同じキーの判定・
  `tests/test_keyboard_layout_files.py:6` / :38 の `resolve_key_id_from_scan_code`）を §3・§4 の形へ置き換える
- 影響なし: `keyboard_window.py:534`（レイアウトの `scan_code` を引く既存の使い方のまま）

## §6 レイアウトが変わるときの離し（ユーザー確定 2026-10-18・案 B）

key_hold 等で §4.1-4 のキーを押したままレイアウトが変わると、離すときに名前を新しいレイアウトで引き直して当たらない（または別の走査コードになる）ため、
キーが OS 上で押されたまま残り得る（離す前の検査 `action_executor.py:278`・同じキーの判定 `held_inputs.py:181`・離し `held_inputs.py:207`・text 送信中の押し直し :257）。

- **送信側が引く値（登録済みのレイアウト `_keyboard_layout_entries` と選んでいる id）を置き換える前に、`held_inputs.release_all()` で押したままのキーをすべて離す**（古い値で離せる）。入口:
  - `reload_keyboard_layouts`（`layout_controller.py:203`）: `_keyboard_layout_entries` を置き換える**前**（追加・削除・構成の読込から呼ばれる。中身が変わったかは見ず毎回）
  - `set_keyboard_layout_selection`（:252）と `sync_keyboard_layout_controls`（:217）: 選ぶ id が**実際に変わるとき**、`keyboard_layout_id` を書き換える前
- 離しに失敗した記録（`release_all` の戻り値の例外）は既存の held の失敗と同じく通知し、切替はそのまま進める
  （受容: 失敗した記録の再試行は新しいレイアウトで引くため離せないことがある。SendInput の失敗はまれで、他のキーの離しの失敗と同じ既存の性質）
- 直接置換は押してすぐ離す（`action_executor.py:296-301`）ので対象外
- 受容: 起動中に外部レイアウトの JSON を書き換えると、受け取る側（呼ぶたびに読み直す・§3）は新しい `scan_code`、送信側（登録時の値・§4.4）は古い `scan_code` を使い、読み直し（再起動・レイアウトの追加 / 削除）まで食い違う。
  受け取りと送信で同じ写しを使う形は idea_51 へ分離
- 不採用の案: gateway が押したときの走査コードを覚える（入口 5 つ・押し直し・スレッド間のロックの扱いが増える）/ 受け取り・送信で同じ写しを使う（案 A・範囲が広がる）

## §7 受け入れ条件（ドラフト）

1. 既知の表とその関数が `keyseq/` から無くなっている（§5）
2. US TKL を選んでいるとき、走査コード 41 のフックの名前が `zenkaku_hankaku` にならない（§3）
3. jis.json を選んでいるとき、走査コード 123 / 121 / 112 / 41 のフックの名前が `muhenkan` / `henkan` / `kana` / `zenkaku_hankaku`（§3・従来どおり）
4. jis.json を選んでいるとき、出力 `muhenkan`・`ctrl+muhenkan`・key_hold の `muhenkan` が走査コード 123 で送られる（§4.1・§4.2）
5. US TKL を選んでいるとき、`muhenkan` の検査がエラーになる（§2・§4.3）
6. keyboard が知る名前（`a`・`grave` 等）の送信・検査が従来どおり（§4.1-3）
7. 自作レイアウトの `{"id": "my_key", "scan_code": 50}` で `my_key` が受け取り・送信とも通る（§3・§4）
8. 組み合わせに 4 のキーを含むとき、記述順に押し逆順に離す（§4.2）
9. 「キー名 → 走査コード」の関数が未設定・例外のとき、4 は当たらず他の名前の送信は通る（§4.4）
10. `keyboard_layouts` の純関数: 大文字小文字・別名の正規化・最初の行の採用・`scan_code` なしの行は当たらない・1〜255 の範囲外は当たらない（§4.1）
11. §6: レイアウトの読み直し・選ぶ id の変更の前に押したままのキーが古い値で離される / id が変わらない選び直しでは離さない / 離しの失敗が通知され切替は進む（単体テスト）
12. 実機目視（JIS キーボード・jis.json）: 半角/全角・かなをキーボードUI で割り当てて反応する（2026-10-18 確認済）/ 出力の `muhenkan`・`zenkaku_hankaku` が物理キーを押したときと同じ動きになる（2026-10-18 確認済）。無変換・変換は利用者のキーボードが押下だけ〔241 / 242〕を送るため対象外（§3.1・idea_52）
13. （取り下げ・v0.5）`extra_scan_codes` の条件は idea_52 へ

## §8 スコープ外（本フェーズでやらない）

- キーの取得（Tk）で JIS の特殊キーを取る（idea_50）
- キーボードUI の取得の名前（phase 61 で済み）
- 既存の構成の `muhenkan` 等の移行・警告（後方互換は考慮しない）
- レイアウトの JSON の書式変更（`scan_code` の意味が送信にも広がるだけで、書式は不変。`extra_scan_codes` は v0.5 で取り下げ）
- 押下だけが続けて届くキー（離しの無い 241 / 242 等）への対応・受け取り用の追加の走査コード（[idea_52](../backlog/idea_52_make_only_keys.md)）
- 受け取りと送信で同じレイアウトの写しを使う・フックのスレッドでの JSON の読み直しをやめる（[idea_51](../backlog/idea_51_layout_snapshot_for_hook.md)）

## §9 正本反映（フェーズ末昇格・予定）

- `key_input.md`: §7.1（フックの名前の出どころ）/ §7.4（:91 の受容の書き換え）/ §7.7（§4.1〜4.4 の送信）/
  §7.8（:195 の「JIS の特殊キーの表」→ レイアウト）
- `features.md` §4.6「レイアウトの JSON」: `scan_code` を書いた行の `id` は受け取りと送信の両方の名前になる・
  keyboard が知る名前の `id` に別の `scan_code` を書かない・拡張キーの走査コードは送信で拡張なしになる・`scan_code` は 1〜255・
  特殊キーを使うなら特殊キーを書いたレイアウトを選ぶ
- `codebase_map.md`: :126（`keyboard_layouts`）・`key_identifiers`・`InputGateway` の注入・`LayoutController` の追加メソッド
- 受容の記録（`key_input.md` §7.1 または §7.4）: キーボードによっては無変換・変換が押下だけ（241 / 242・離し無し・続けて 3 回）で届き、フックで扱えない（§3.1・idea_52）
- 実装: `domain/key_identifiers.py` / `presentation/keyboard_layouts.py` / `presentation/controllers/layout_controller.py` /
  `infrastructure/input_gateway.py` / `presentation/app.py`
- テスト: `tests/test_key_identifiers.py` ほか、送信・検査・名前の解決の単体テスト

## 関連

- [idea_49](../backlog/idea_49_special_keys_from_layout_only.md)・[idea_50](../backlog/idea_50_capture_jis_special_keys.md)（取得の側）・[idea_51](../backlog/idea_51_layout_snapshot_for_hook.md)（レイアウトの写し）
- phase 61（キーボードUI の取得をレイアウトだけで引く）・phase 54（テンキー・§7.8 の送信経路）
- 正本: `key_input.md` §7.4 / §7.7 / §7.8・`features.md` §4.6
