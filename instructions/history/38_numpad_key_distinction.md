# 暫定仕様 38: テンキーの区別（numpad_key_distinction）

> 状態: **未凍結・v0.5・主入力・ユーザー確定済（2026-10-11）・実装着手可**（v0.1 起票時 deep-reviewer「修正して採用」〔高 1・中 5・低 4〕を反映 → v0.2 → §7 の 4 点をユーザー確定 → v0.3 → 確定前の Codex 敵対的 needs-attention〔high 1・medium 1〕をユーザー判断で反映〔§2-9〜10〕→ v0.4 確定 → task_01 の probe で Tk の keysym に `KP_` が付かないと判明・keycode + 拡張ビットで記録を区別する案へ §2-6・§6 を改訂 → v0.5 ユーザー確定）。本書がこのフェーズの確定設計（フェーズ中は正本を直接改訂しない）。
> フェーズ末タスクで正本 `instructions/common/spec_detail/` へ昇格し本書を凍結する。
> 起票元: [idea_43](../backlog/idea_43_numpad_key_distinction.md)（2026-10-11・ユーザー要望）。
> 番号対応: phase 54 / 暫定 38 / decisions 54。

---

## §1 目的 / 背景

**テンキー（numpad）のキーを主キーボードのキーと区別する**。入力の判定・出力（送信）・記録・表示のすべてで、テンキーは専用の名前（`num 1` 等）で扱い、既存の名前（`1` / `end` 等）は主キーボード側のキーだけを指すようにする（出力の記号の名前は §2-8）。
**domain（名前の表・名前の関数）・application（入力の名前の決定）・infrastructure（送信・名前の検査・同じキーの判定）・presentation（記録）。JSON の形は変えない（キー名の値が増える）。既存設定の意味が変わる（§2-3）。**

### 現状監査（2026-10-11・codex-explorer + メイン実測〔.venv の keyboard の名前の表〕+ 起票時 deep-reviewer）

- **keyboard ライブラリの名前ではテンキーを区別できない**: `key_to_scan_codes("1")` と `("num 1")` はともに `(2, 79)`（主キーボードの 1 とテンキーの 1 の両方）。`num .` / `num home` は未定義・`decimal` は `(83,)`。
  記号は**テンキーが先頭**: `*` → `(55, 40)`・`+` → `(78, 39)`・`-` → `(74, 12)`・`/` → `(57397, 53)`。**今のアプリは `+` / `*` / `-` を送るとテンキーのキーを押している**（`keyboard.press` / `send` は先頭のスキャンコードで送る・`key_identity` も先頭）
- フックのイベントは `name`（NumLock オンのテンキー 1 は `1`・オフは `end`）・`scan_code`・`is_keypad`（`(scan_code, vk, is_extended)` が keyboard の `keypad_keys` 表にあれば真・`_winkeyboard.py:442`・:528。`num lock`〔69〕も真）を持つ。**拡張フラグはイベントに無い**
- テンキーのスキャンコード（非拡張）: 0=82 / 1=79 / 2=80 / 3=81 / 4=75 / 5=76 / 6=77 / 7=71 / 8=72 / 9=73 / `.`=83 / `*`=55 / `-`=74 / `+`=78。拡張: Enter=28 / `/`=53。
  NumLock オフでは同じスキャンコードのまま VK が home / end / 矢印等に変わる（本物の矢印・home 等は同じスキャンコードの**拡張**キー）。keyboard の `scan_code_to_vk[79]` は VK_END
- 入力の名前: `application/input_router.py:143-152`・`key_state_manager.py:93-108` の**2 か所**が、注入された `resolve_scan_code`（`app.py:143`・:178 → `layout_controller.py:259` → `keyboard_layouts.py:327`。組み込みの US TKL はスキャンコードを持たないため、名前を返すのは `domain/key_identifiers.py` の JIS の特殊キー 4 件だけ）を優先し、空ならイベントの `name`。`is_keypad` は使っていない。
  **今は NumLock オフのテンキー 1 が `end` のトリガーに反応する**。押している間に NumLock を切り替えると down `1`・up `end` になり押下状態に `1` が残る
- 停止キー・トグルキーも `input_router.py:100-104` の名前の判定（keyboard の `add_hotkey` / `is_pressed` は使っていない）。`input_gateway.py:158-175` の `register_key_hook`（`keyboard.hook_key`）は呼び出し元なし
- 正規化 `domain/config.py:84-89` の `normalize_key_name` は trim + 小文字のみ。重なり判定 `application/key_overlap.py` は正規化後の文字列一致。同じキーの判定 `input_gateway.py:228-247` の `key_identity` は拡張キー表 → `key_to_scan_codes` の先頭
- 送信 `input_gateway.py:180-216`: 拡張キー表（`_EXTENDED_KEYS` :21-40）は Win32 `keybd_event`（`is_replaying` を立てる・:133-146）、他は `keyboard.press` / `release` / `send`。hotkey は拡張キーを含めば順に押して逆順に離す（:196）。正本 `key_input.md` §7.7 は「名前で区別できないテンキーの Enter・`/` は対象外」
- 名前の検査 `input_gateway.py:255-261` の `validate_key_name` は `keyboard.key_to_scan_codes`（例外時は日本語キー名の表）。keyboard の別名 `num plus` / `num minus` / `num sub` / `num del` も通る。hotkey の文法 `domain/hotkey.py` は `+` で区切る（`num +` は書けない）。key_hold は `+` / `,` を含む名前を拒否
- 記録: Tk の keysym を `presentation/tk_keys.py` で変換（`KP_` 系の登録なし。`KP_1` は小文字化で `kp_1`。主キーボードの記号は `asterisk` / `plus` / `minus` 等で保存される既存の問題 :26-28）。hotkey の記録・key_hold の「1 キーを記録」・トリガー / 切替キー / 停止キーの取得（`trigger_dialog.py`・`keymap_edit_dialog.py`・`keymap_switch_batch_dialog.py`・`controllers/key_capture.py`）が使う
- 表示: 組み込みのキーボード表示（`keyboard_layouts.py:37-133` の US TKL）にテンキーは無い（外部レイアウトで追加できる）
- テンキーを明示したテストは無い

## §2 確定事項（ユーザー 2026-10-11）

1. **区別する場面 = 入力の判定・出力（送信）・記録・表示のすべて**
2. **テンキーの名前 = `num` + 数字 / 単語**: `num 0`〜`num 9` / `num add`（+）/ `num subtract`（-）/ `num multiply`（*）/ `num divide`（/）/ `num decimal`（.）/ `num enter`（`+` / `,` と衝突しない・記号の書き方をそろえる）
3. **既存の名前（`1` / `/` / `*` / `-` / `+` / `.` / `enter` / `end` / `home` / 矢印等）は主キーボード側のキーだけを指す**（今テンキーで反応している設定はテンキーで反応しなくなる。データの移行はしない。既存データの `num 1` 等〔今は keyboard の別名で主キーボードの 1 にも反応〕はテンキー専用になる。出力の記号の名前は §2-8）
4. **NumLock に関係なく物理キーで同じ名前**（テンキーの 1 の位置は NumLock オン / オフとも `num 1`。トリガーは NumLock の状態に左右されない。`num 1` を送ると送り先ではそのときの NumLock で 1 か End になる＝物理キーと同じ）
5. **外部レイアウトの `id` より表の名前を優先**（v0.3・ユーザー確定）: 外部レイアウトがテンキーのスキャンコードに独自の `id` を付けている場合も、`is_keypad` なら表の名前を優先する（推奨）。理由: 外部レイアウトの `id` は主キーボードと同じスキャンコードを区別できない（スキャンコードだけで引くため）
6. **記録は Tk の keycode（VK）と拡張ビット（state の `0x40000`）で判定し、16 キーとも区別する**（v0.5・task_01 の probe で keysym に `KP_` が付かず主キーボードと同じと判明。v0.3 の「記録で区別できないキーは受容」を置き換え・ユーザー確定）
7. **組み込みのキーボード表示にテンキーを足さない**（v0.3・ユーザー確定）: 推奨 = **このフェーズでは足さない**（組み込みの US TKL への列の追加・ウィンドウ幅の変更が大きく、外部レイアウトで追加できる）。外部レイアウトでテンキーの `id` を `1` / `end` 等にしているものは、テンキーを押してもハイライトしなくなる（`id` を表の名前に書き換えれば効く）
8. **記号の名前（`*` / `+` / `-`）の出力は文字として従来どおり・「主キーボードだけ」は入力の判定に限る**（v0.3・起票時 deep-reviewer 高・ユーザー確定）: **今は keyboard の名前の解決でテンキーのキーが送られている**（主キーボードの `*` / `+` は shift が要り、配列で位置も違う）。
9. **テンキーの名前を返すのはテンキーのイベントだけ**（外部レイアウトの `id` が表の名前でも、テンキーでないイベントには使わない）（v0.4・確定前 Codex 敵対的 high・ユーザー判断）
10. **`num` のアンダースコアの書き方（`num_1` 等）は別名にせずエラー**（v0.4・確定前 Codex 敵対的 medium・ユーザー判断）
   推奨 = **出力では記号の名前は文字として扱い、従来どおり keyboard の解決に任せる**（テンキーで送られ得る。§2-3 の「主キーボードだけ」は**入力の判定に限る**）。同じキーの判定も実際に送るキーのまま（`+` と `num add` は同じキーとして扱われる＝OS 上も同じキーを押すため正しい）。
   代案 = 主キーボードの位置へ shift つきで送る（配列ごとの対応・暗黙の shift の規定が要り大きい）

## §3 名前の表（domain）

| 名前 | スキャンコード | 拡張 |
|---|---|---|
| `num 0`〜`num 9` | 82 / 79 / 80 / 81 / 75 / 76 / 77 / 71 / 72 / 73 | 非拡張 |
| `num decimal` | 83 | 非拡張 |
| `num multiply` / `num subtract` / `num add` | 55 / 74 / 78 | 非拡張 |
| `num divide` / `num enter` | 53 / 28 | 拡張 |

- domain に 1 つの表として置く（名前 ↔ スキャンコード + 拡張フラグ）。keyboard に依存しない
- `num lock`（69・`is_keypad` は真）は従来どおり（表に含めない・既存の拡張キーの送信）。テンキーのカンマ（ブラジル配列等のスキャンコード 126）は対象外（従来の名前のまま）
- 名前は trim + 小文字で引く（`Num 1` も可）。`num` と数字 / 単語の間は半角空白 1 つ
- **名前の `_` を半角空白に置き換えた形が `num ` で始まり、表に無い名前は `num lock` を除き名前の検査でエラー**（`num1`〔keyboard でも無効〕・`num +` / `num plus` / `num del` / **`num_1` / `num_plus` / `num_add` 等のアンダースコアの書き方**。keyboard は `_` を空白に読み替え `num 1` を `1` に解決するため、検査を通すと主キーボードのキーが送られる）。テンキーの名前の書き方は表の 16 個（半角空白区切り）に絞る。検査を通らない名前は保存・実行されないため、送信・同じキーの判定にもこの規則が及ぶ（v0.4・確定前 Codex 敵対的 medium）
- keyboard の名前 `decimal` / `clear` / `separator` は従来どおり有効（出力では従来どおり送る）。ただし入力ではテンキーが表の名前になるため、**トリガー等に書いても反応しない**（受容・§2-3 の帰結）

## §4 入力の判定

- **名前の決定は domain の純関数 1 つ**（`(scan_code, is_keypad) → 表の名前 | ""`）にし、`input_router.py` と `key_state_manager.py` の両方の `_extract_key_name` が最初に使う（片方だけだと押下状態とトリガーの名前がずれる）。イベントの `is_keypad` は `getattr(event, "is_keypad", False)` で読む（テスト用の偽イベントは属性を持たない）
- フックのイベントが **`is_keypad` が真で、スキャンコードが §3 の表にある**とき、キー名を表の名前にする（`resolve_scan_code`・イベントの `name` より優先）。それ以外は従来どおり
- **テンキーでないイベント（`is_keypad` が偽）では、`resolve_scan_code`（外部レイアウトの `id`）が表の名前を返しても採用せず、イベントの `name` に戻す**（外部レイアウトはスキャンコードだけで引き拡張フラグを見ないため、`id="num 1"`・`scan_code=79` のレイアウトで本物の End が `num 1` になるのを防ぐ。表の名前を返すのはテンキーのイベントだけ）（v0.4・確定前 Codex 敵対的 high）
  - テンキー Enter（28・拡張）と主 Enter（28・非拡張）、テンキーの 1（79・非拡張）と End（79・拡張）は `is_keypad` で分かれる
  - **押している間に NumLock を切り替えても**、down / up とも `num 1` で対になる
- この名前がトリガー・直接置換の元・キーマップの切替キー・停止キー・トグルキー・押下状態（`key_state_manager`）・重なり判定にそのまま使われる（名前の文字列一致の既存の仕組みに乗る）
- 押下状態・確認して実行の長押しの判定（`features.md` §4.2.11・`key_input.md` §7.3）も同じ名前で数える
- 外部レイアウトがテンキーのスキャンコードに独自の `id` を登録していても、`is_keypad` のときは表の名前を優先する（§2-5）
- **Windows の偽の shift**: NumLock オンで shift を押したままテンキーを押すと、OS が「shift の up → テンキー（home / end / 矢印として・非拡張）→ shift の down」を差し込む。テンキーは表の名前になる。差し込まれた shift の up / down は従来どおり `shift` として届く
  （押下状態で一瞬 shift が離れた扱い・`shift` を停止キー等にしていれば down で反応し得る）＝**既存の性質として受容**（task_01 の probe でイベント列を確かめ、違えば改訂）

## §5 出力（送信）

- `press_key` / `release_key` / hotkey の各要素 / 直接置換の先で、名前が §3 の表にあれば**そのスキャンコードと拡張フラグで送る**（NumLock の状態で送り先の解釈が決まる＝物理キーと同じ）。
  **keyboard の名前の API（`press` / `send` / `hook_key` 等）には表の名前を渡さない**（`num 1` は主キーボードの 1 にも解決されるため）
  - **送り方 = `SendInput` のスキャンコード入力**（`KEYEVENTF_SCANCODE`・拡張は `KEYEVENTF_EXTENDEDKEY`）を第 1 案とする。VK を固定して送ると NumLock に関係なく VK どおりに解釈されるため（keyboard の経路で 79 を送ると常に End）。
    VK で送る必要があれば、送る時点の `GetKeyState(VK_NUMLOCK)` で VK を選ぶ。いずれも phase 51 の拡張キーと同じく send_guard の中・keyboard の押下記録に載せない（`is_replaying`）。task_01 の probe でメモ帳に NumLock オン / オフで 1 / End が入ることを確かめて決める
  - hotkey の送信の分岐（拡張キーを含めば順に押して逆順に離す）を「拡張キー**または表の名前**を含むか」に広げる
- hotkey の組み合わせ（`ctrl+num 1`・`shift+num add`）も各要素を同じ規則で送る（修飾キーは従来どおり）。`shift+num 1` の送り先での結果（物理キーと同じく End になるか）は task_01 の probe で確かめる
- **記号の名前（`*` / `+` / `-` / `/` / `.` 等）の送信**: §2-8
- **同じキーの判定**（`key_identity`・phase 51 の押下中の集合・phase 52 のリピートの対象）: 表の名前は表のスキャンコード + 拡張フラグ。それ以外は従来どおり（実際に送るキー）。
  `1`（主キーボードの 1・スキャンコード 2）・`end`（拡張の 79）は `num 1`（非拡張の 79）と別のキー（記号の名前は §2-8 に従う）
- key_hold のリピート（phase 52）は `num 1` 等も対象（修飾キーではない）

## §6 名前の検査・記録・表示

- **名前の検査**（`validate_key_name`・hotkey の検証・key_hold の検証・ダイアログの OK）: 表の名前を有効とする（keyboard に問い合わせる前に表を見る）。`num ` で始まる表外の名前は §3 のとおりエラー
- **記録**（hotkey の記録・key_hold の「1 キーを記録」・トリガー / 切替キー / 停止キー / トグルキーの取得）: Tk のイベントの **keycode（Windows では VK）と拡張ビット（`event.state & 0x40000`）**で表の名前を決め、該当しなければ従来どおり keysym を変換する（`tk_keys.py` に純関数 1 つ・記録を使う各所が keysym の変換の前に呼ぶ）。
  - NumLock オン: VK 96〜105 → `num 0`〜`num 9` / 110 → `num decimal` / 106 → `num multiply` / 109 → `num subtract` / 107 → `num add`（いずれも拡張なし）/ 111 → `num divide` / **13 かつ拡張あり** → `num enter`
  - NumLock オフ（**拡張なし**のとき）: 45 → `num 0` / 35 → `num 1` / 40 → `num 2` / 34 → `num 3` / 37 → `num 4` / 12 → `num 5` / 39 → `num 6` / 36 → `num 7` / 38 → `num 8` / 33 → `num 9` / 46 → `num decimal`（本物の Insert / End / 矢印 / Page / Home / Delete は**拡張あり**なので従来の名前）
  - keysym はテンキーでも主キーボードと同じ（`1` / `End` / `period` / `Return` 等・`KP_` は付かない）ため keysym では判定しない（task_01 の probe）
- **一覧**: キー名をそのまま表示する（`[押す] num 1`・`ctrl+num add`）。書式の変更なし
- **キーボード表示**: §2-7

## §7 確認事項（ユーザー判断）

なし（v0.2 の 4 点は 2026-10-11 にユーザー確定・§2-5〜8 へ移した）。

## §8 受け入れ条件（ドラフト）

自動テスト:
1. 名前の表: 16 名の名前 ↔ スキャンコード + 拡張フラグ・大文字 / 前後空白（§3）
2. 入力の名前の関数: `is_keypad` 真 + 表のスキャンコードは表の名前（NumLock オフ相当の `name="end"` でも `num 1`）。`is_keypad` 偽の `end` / `1` / `enter` は従来の名前。`is_keypad` 真の `num lock`（69）・スキャンコード 126 は従来の名前。`is_keypad` 属性の無いイベントは従来どおり（§3・§4）
3. `input_router` と `key_state_manager` が同じ名前を使う。押している間に NumLock を切り替えた down `1` / up `end`（どちらも `is_keypad` 真）で押下状態が `num 1` の対になって消える（§4）
4. トリガー `num 1` はテンキーの 1 でだけ実行され、主キーボードの 1 では実行されない。トリガー `1` はその逆。`end` は本物の End だけ（§2-3・§4）
5. 重なり判定が表の名前で動く（`num 1` と `1` は重ならない）（§4）
6. 送信: 表の名前の押す / 離す / hotkey の要素が表のスキャンコード + 拡張フラグで送られ、keyboard の名前の API に渡らない。hotkey に表の名前を含むと順に押して逆順に離す。`key_identity("num 1")` ≠ `key_identity("1")` ≠ `key_identity("end")`（§5）
7. 名前の検査: 表の名前は有効・`num +` / `num1` / `num plus` / `num del` / `num_1` / `num_plus` / `num_add` は無効・`num lock` は有効（§3・§6）
7a. 外部レイアウト（`id="num 1"`・`scan_code=79`）で、本物の End（`is_keypad` 偽）は `end`・テンキーの 1 は `num 1` になり、トリガー `num 1` は End で実行されず、両方を押して片方を離しても他方の押下状態が残る（§4）
8. 記録: keycode 97（拡張なし）・35（拡張なし）→ `num 1`・35（拡張あり）→ `end`・13（拡張あり）→ `num enter`・13（拡張なし）→ `enter`・107 → `num add`・111 → `num divide`・191 → 従来の keysym の変換 等（§6）
9. 既存テスト（tests / tests_ui / smoke）が通る

実機目視（ユーザー・ホスト OS・テンキーのあるキーボード）:
10. トリガー `num 1` が NumLock オン / オフともテンキーの 1 で動き、主キーボードの 1 では動かない。トリガー `1`・`end` はテンキーで動かない
11. hotkey `num 1` / `num add` / `num enter` をメモ帳へ送ると、NumLock オンで `1` / `+` / 改行、オフで End の動き等になる（物理キーと同じ）
12. 「1 キーを記録」・hotkey の記録・トリガーの取得でテンキーを押すと、NumLock オン / オフとも表の名前で記録される（§6）

## §9 スコープ外（本フェーズでやらない）

- テンキーのカンマ（スキャンコード 126）・テンキーの `=` 等の特殊なキー
- 既存設定の自動移行（`1` → `num 1` の書き換え等）
- §2-7 で「足さない」なら組み込みのキーボード表示のテンキー
- 主キーボードとテンキーの両方に反応する名前（§2-3 で採らない）
- Tk の記録で記号が `plus` / `minus` 等で保存される既存の問題（`tk_keys.py:26-28`・§2-8 の判断次第で別 idea）

## §10 正本反映（フェーズ末昇格・予定）

- `key_input.md`（キー名の決め方〔入力の判定・偽の shift〕・§7.7 の送信〔「テンキーの Enter・`/` は対象外」の記述を更新・表の名前の送信〕・テンキーの名前の表）
- `data_schema.md`（キー名の値にテンキーの名前が加わる・既存の名前の意味〔§2-3〕・`num ` で始まる表外の名前は検査でエラー）
- `features.md`（トリガー / 置換 / 切替キー等の名前・記録・一覧の例。`features.md:387` の「判定はスキャンコードから引く」の記述の更新）
- `codebase_map.md`（名前の表と名前の関数の置き場・入力の名前の決定・送信）
- 実装（予定）: `domain/`（名前の表・名前の関数）・`application/input_router.py`・`key_state_manager.py`・`infrastructure/input_gateway.py`・`presentation/tk_keys.py` / テスト
- タスク分割の見込み: task_01 probe（送り方・Tk の keysym・偽の shift を 1 本で）/ task_02 domain の表 + 名前の決定 + 検査 / task_03 送信と `key_identity` / task_04 記録 / task_05 統合確認 / task_06 正本反映

## 関連

- [idea_43](../backlog/idea_43_numpad_key_distinction.md) / phase 51（拡張キーの送信・keyboard の記録に載せない）/ phase 52・53（リピート・同じキーの判定）
- 正本 `key_input.md` §7.3・§7.7 / `data_schema.md` §5.11 / `features.md` §4.1・§4.2.12
