# 暫定仕様 43: キーボードUI の左右の修飾キーの区別（keyboard_ui_left_right_modifiers）

> 状態: **未凍結・v0.2・主入力（起票時 deep-reviewer「修正して採用」・Codex 敵対的 needs-attention 2 件の反映・§4 はユーザー判断待ち）**。本書がこのフェーズの確定設計（フェーズ中は正本を直接改訂しない）。
> フェーズ末タスクで正本 `instructions/common/spec_detail/` へ昇格し本書を凍結する。
> 起票元: ユーザー要望（2026-10-15・キーボードUI は入力では左右を区別できるが、表示・編集が左右を区別せず、左右両方の枠に同じ割り当てが出て左のキーにしか効かない）。番号対応: phase 59 / 暫定 43 / decisions 59（予定）。

---

## §1 目的 / 背景

キーボードUI（キーボード表示のウィンドウ）で、左右の修飾キー（Shift・Ctrl・Alt・Windows）の枠を**左右別のキー**として表示・編集できるようにする。
枠のラベル（`Ctrl` 等）は変えず、内部で引くキー名だけを左右で分ける。

### 現状監査（2026-10-15・codex-explorer の調査 + メインの裏取り）

* レイアウトの id はすでに左右で分かれている: 既定レイアウト `presentation/keyboard_layouts.py:101-121`（`shift_l` / `shift_r` / `ctrl_l` / `ctrl_r` / `alt_l` / `alt_r` / `windows_l` / `windows_r`）/
  `config/user/keylayout/jis.json:17-18`（`shift_l` / `shift_r` だけ。Ctrl・Alt・Windows の行は無い・18 キーの見本）
* **畳んでいる箇所**: `presentation/keyboard_window.py:27-35` の `_LOOKUP_KEY_BY_ID` が左右の id を共通名（`shift` / `ctrl` / `alt` / `windows`）へ写し、
  `:373-377` で表示の文言（`_display_map`）・色（`_kind_map`）・クリック範囲（`_key_bounds`）をこの共通名で引く。クリックで始める編集の元キー（`_editing_source_key`）もこの共通名（`:381`・`:435-462`）
  → 左右の枠に同じ割り当てが出て、右の枠をクリックしても左（共通名）のキーマップを書き換える
* キーマップの元キー・トリガーのキーは `normalize_key_name`（trim + 小文字化のみ・`domain/config.py:85-87`）で保存・照合し、`ctrl` と `right ctrl` は**別のキー**（`application/input_router.py:107-150` の照合は名前の一致・左右の同一視なし）
* 実行時の入力のキー名（`input_router.py:184-198`）: テンキー → レイアウトの `scan_code` を持つキーの id（`presentation/controllers/layout_controller.py:358` → `keyboard_layouts.py:327-340`。今 `scan_code` を持つのは JIS の特殊キー 4 つと `domain/key_identifiers.py` の既知の 4 つだけ）→ `event.name`。
  修飾キーは `scan_code` を持たないので `event.name` で決まる
* keyboard ライブラリ（`.venv`）の名前の表（`keyboard._winkeyboard.to_name`・2026-10-15 にメインが出力）: 左 Ctrl = `ctrl` / 右 Ctrl = `right ctrl`（拡張フラグ付き `Right Control` → 正規化）/ 左 Shift = `shift` / 右 Shift = `right shift` /
  左 Alt = `alt` / 右 Alt = `right alt` / 左 Windows = `left windows` / 右 Windows = `right windows`（公式の仮想キー名も `left windows` / `right windows`）。
  deep-reviewer もフックが渡す組（scan_code・左右別の仮想キー・拡張フラグ）で `to_name` / `get_event_names` → `normalize_name` を計算し同じ結果（配列 0x0411・修飾の状態によらない。AltGr の配列では右 Alt が `alt gr`）。**実機のフックで届く名前は未実測**（§4-1）
* キーの取得の名前（`presentation/tk_keys.py`）: 通常の取得（表 `:45-55`・関数 `normalize_tk_key_event` `:71-78`）は左右を共通名へ。ただし**通常の取得はどれも修飾キー単独を捨てる**（`controllers/key_capture.py:137` 等・キーマップの編集・トリガー・直接切替キーのダイアログ）。key_hold の取得（`:80-94`）だけ左右を区別（`left windows` 等）。キーボードUI の編集中の送信先の取得も通常の名前（`keyboard_window.py:496-510`）で、修飾キー単独は割り当てない
  → 元キー `ctrl` / `shift` / `alt` / `windows` を単独で作れる経路は、**今のキーボードUI で修飾キーの枠をクリックすること**（共通名になる）と手編集だけ
* 正本: `features.md`「キーボード表示のウィンドウ（phase 55）」（:657 付近）に左右の扱いの記述は無い。レイアウト JSON の書式（`layout_id` / `keys` / `id` / `scan_code`）を規定した正本の節は無い
* 既存テストで `_LOOKUP_KEY_BY_ID` を直接見るものは無い（`tests_ui/test_task05_overlap_ui.py:242-247`・`test_task06_keymap_management_ui.py:138-146`・`test_trigger_effective_row.py:158-162` は `_display_map` / `_kind_map` を見る）

---

## §2 確定事項（ユーザー 2026-10-15）

* **枠のラベルはそのまま**（`Ctrl` / `Shift` / `Alt` / `Win`）。内部で左右を区別して、枠ごとに左右別のキーを表示・編集する
* **レイアウトの id → キー名の対応を左右で分ける**。左は今のキー名のまま（既存のキーマップの `ctrl` 等は左として効き続ける）、右は `right ctrl` 等
* **レイアウト JSON の書式は変えない**（任意の `"key"` 等の新しい記述方法は足さない。左右は既定の id で区別する）
* `config/user/keylayout/jis.json` に左右の Ctrl・Alt・Windows の行を既定の id で足す
* 右 Alt・Windows キーの実際のキー名は実測して決める（§4-1）

---

## §3 設計

### §3.1 id → キー名の対応

キーボードUI が枠の id から引くキー名（表示・色・クリック範囲・編集の元キー）:

| id | キー名 | 備考 |
|---|---|---|
| `shift_l` / `shift_r` | `shift` / `right shift` | 左は今のまま |
| `ctrl_l` / `ctrl_r` | `ctrl` / `right ctrl` | 左は今のまま |
| `alt_l` / `alt_r` | `alt` / `right alt` | 左は今のまま。右は §4-1 の実測で確定 |
| `windows_l` / `windows_r` | `left windows` / `right windows` | 今は両方 `windows`。§4-1・§4-2 |

* 根拠: 実行時にフックが届ける名前（§1 の表）と同じ名前で引けば、キーボードUI で設定した元キーがそのキーの押下で効く
* 修飾キー以外の id の対応（`grave` → `` ` `` 等・`keyboard_window.py:36-46`）は変えない

### §3.2 キーボードUI の挙動（左右を分けた結果）

* 表示: 左右の枠にそれぞれのキー名の割り当て（キーマップの送信先・トリガー・停止 / トグルキー）を出す。色（種類）も枠ごと
* 編集: 右の枠をクリックすると元キー `right ctrl` で編集を始め、割り当てると `right ctrl` → 送信先のマッピングができる（左は `ctrl`）。編集中の強調はクリックした側の枠だけ
* **右クリックでのクリア**も枠のキー名で行う（`keyboard_window.py:443-453` → `keymap_panel_controller.py:642`）: 右の枠を右クリックすると `right ctrl` の割り当てを消し、左の `ctrl` には触らない（今は左右どちらを右クリックしても共通名を消す）
* 直接切替キー（`KM<n>`・`keyboard_window.py:172-179`）・停止 / トグルキーの表示も枠ごとのキー名で引く。編集中のタイトルは `編集中: right ctrl` / `編集中: left windows` のようにそのキー名になる（`features.md`「キーボード表示のウィンドウ」のタイトルの書式のまま）
* 編集中の送信先の取得（キーを押して決める）は今のまま（修飾キー単独は割り当てない・組み合わせの名前は通常の取得の名前）
* キーマップの照合・フック・送信（`key_input.md`）は変えない。**画面の枠の表示中**は、Ctrl・Alt・Windows を押している間と修飾キー単独の押下は枠の振り分けで素通しになり、トリガー・置換へ進まない（`key_input.md` §7.3・`input_router.py` `_route_grid_key`。既存の規定のまま）→ 修飾キーの割り当ては枠の非表示中だけ効く

### §3.3 レイアウト JSON

* 書式は変えない。左右の修飾キーは既定の id（`shift_l` 等）で書く
* **左右の修飾キーの行に `scan_code` を書かない**（書くと実行時の入力のキー名がその id〔例 `shift_r`〕になり、キーマップの照合と押下状態の記録〔`key_state_manager.py:100-101`〕が変わる。さらに左右の Ctrl・Alt は同じ走査コードで拡張フラグでしか区別できない）。§4-3
* `jis.json` の追加（見本の配置。最下段 y = 5.2・高さ 1.0。既存の無変換 x = 3.0〜スペース x = 7.5〜10.5 の前後に置く）:
  `ctrl_l`（`Ctrl`・x 0.0・w 1.0）/ `windows_l`（`Win`・x 1.0・w 1.0）/ `alt_l`（`Alt`・x 2.0・w 1.0）/ `alt_r`（`Alt`・x 10.5・w 1.0）/ `windows_r`（`Win`・x 11.5・w 1.0）/ `ctrl_r`（`Ctrl`・x 12.5・w 1.5）

### §3.4 既存データとの関係

* キーマップ・トリガーの元キー `ctrl` / `shift` / `alt` は左の枠だけに出る（実行時も左のキーでしか効いていなかった = 見た目が実際の挙動に合う）
* 元キー `right ctrl` 等（手編集・key_hold の取得等で入っていたもの）は右の枠に出るようになる
* 元キー `windows`（phase 55 以降に**今のキーボードUI の Win の枠**で作った割り当て・手編集。実行時は左 Windows が `left windows` で届くので一度も効いていない見込み）は §4-2
* キーマップの編集ダイアログ（通常の取得）で元キー `right ctrl` の割り当てを取り直すと、修飾キー単独は取得できないため元キーは変えられない / 送信先として左右は区別しない（受容・§6）

---

## §4 確認事項（ユーザー判断・未確定）

1. **右 Alt・左右 Windows の実際のキー名**: keyboard ライブラリの表では `right alt` / `left windows` / `right windows`（§1）。
   **提案**: 表どおりで実装し、実機目視で「キーボードUI で右 Alt・左右 Win の枠に割り当て → そのキーを押して効く」ことを確かめる。食い違えばそのタスクの中で表を直す（JIS 配列で右 Alt が `alt gr` で届く等）。
   理由: 実機のフックの名前はメインからは押して確かめられず、表の値が最も確からしい
2. **既存の元キー `windows` の扱い**: 今のキーボードUI の Win の枠で作った割り当ては元キー `windows` で、実行時は左 Windows が `left windows` で届くため効いていない見込み。§3.1 では `windows` はどの枠にも出なくなる。
   **提案**: 出さない（実際に効かない割り当てを枠に出さない）。メインのキーマップ一覧には残るがキーボードUI では見えない割り当てになる（**受容**・必要なら手で消すか、キーボードUI で左の Win の枠に割り当て直す）。
   代案: `left windows` の割り当てが無いときだけ、左の Win の枠に `windows` の割り当てを出す（効かない割り当てが見える）
3. **修飾キーの行の `scan_code`**: **提案 = 案 A**（「書かない」と規定するだけ・コードで防がない）。
   案 B = 走査コードの解決で修飾キーの 8 つの id を無視する（書かれても安全・入力の経路の変更が増える）
4. **左右の Windows キーを元キーにしたときの OS の反応**: キーマップの元キーは押下だけを抑止し離す方は通す（`input_router.py:98-100`）。左右の Windows キーの割り当ては本フェーズで初めて実際に効くため、離したときにスタートメニューが開く等の OS の反応が起きうる。
   **提案**: 実機目視（§5-6）で観察し、起きたら**受容**して記録する（抑止の方式の変更は別 idea）。
5. **右 Alt の名前と対象の配列**（Codex 敵対的の指摘）: 実行時の右 Alt の名前は配列で変わり、AltGr を使う配列（ドイツ語等）では `alt gr`、JIS・US 等では `right alt`。照合は名前の完全一致なので、固定の 1 つの名前ではどちらかの配列で効かない。
   **提案**: 本フェーズの対象は **AltGr を使わない配列（JIS・US 等）** とし、`alt_r` → `right alt` で固定する。AltGr の配列への対応はスコープ外（§6）。実機目視で JIS の右 Alt が `right alt` で効くことを確かめる（§4-1）。
   代案: 実行時の配列を見て `right alt` / `alt gr` を切り替える（入力の経路と表示の両方に配列の判定が要る）

---

## §5 受け入れ条件（ドラフト）

1. 【tests_ui】キーボードUI で左右の Shift・Ctrl・Alt・Windows の枠が、それぞれ §3.1 のキー名の割り当て（文言・色）を出す。左右で別の割り当てを出せる（`_key_bounds` / 描画の結果で確かめる）（§3.1・§3.2）
2. 【tests_ui】右 Ctrl の枠をクリックして割り当てると、キーマップに元キー `right ctrl` のマッピングができる。左 Ctrl の枠は `ctrl`（従来どおり）（§3.2）
3. 【tests_ui】編集中の強調はクリックした側の枠だけ・タイトルはそのキー名（§3.2）
4. 【tests_ui】右の枠の右クリックは `right ctrl` だけを消し、左の `ctrl` は残る（§3.2）
5. 【tests_ui】既存のキーマップの `ctrl` / `shift` / `alt` は左の枠だけに出る（§3.4）
6. 【実機・画面の枠は非表示】右 Ctrl・右 Shift・右 Alt・左右 Windows の枠に割り当てると、そのキーの押下で効き、反対側のキーでは効かない（JIS 配列）。左の枠の `ctrl` 等は従来どおり左で効く。Windows キーを離したときの OS の反応を観察する（§4-1・§4-4）
7. 【静的】`jis.json` に左右の Ctrl・Alt・Windows の行があり、`scan_code` を持たない（§3.3）
8. 既存のテスト（compileall / tests / tests_ui / smoke）が通る

---

## §6 スコープ外（本フェーズでやらない）

* キーの取得のダイアログ（通常の取得）で修飾キーの左右を区別すること / キーボードUI の送信先の取得で左右を区別すること
* 元キー `windows` の既存の割り当ての移行（§4-2・自動で書き換えない）
* AltGr を使う配列での右 Alt（`alt gr`）の対応（§4-5）
* 画面の枠の表示中に修飾キーの割り当てを効かせること（入力の優先順位の変更が要る）
* キーボードUI の編集中の送信先の取得で、Tk の `keycode`（Windows では仮想キーコード）を走査コードとして解決しているため F1 / F10 / F12 が `kana` / `henkan` / `muhenkan` になる見込みの既存の不具合（`keyboard_window.py:507`・deep-reviewer の指摘・別 idea に起票）
* 押しているキーの枠を光らせる表示（今も無い）
* レイアウト JSON の新しい記述方法（`"key"` 等）・レイアウト JSON の書式の正本化

---

## §7 正本反映（フェーズ末昇格・予定）

* 正本: `features.md`「キーボード表示のウィンドウ（phase 55）」に左右の修飾キーの枠の規則（§3.1 の表・§3.2）とレイアウトの修飾キーの行に `scan_code` を書かない規則（§3.3）
* 実装: `presentation/keyboard_window.py`（`_LOOKUP_KEY_BY_ID`）/ `config/user/keylayout/jis.json`
* テスト: `tests_ui/` にキーボードUI の左右の枠の表示・編集のテスト（`_display_map` / `_kind_map` / `_key_bounds` / 編集の元キー）
* `codebase_map.md`（キーボードUI の節）
* タスク見込み: task_01 対応表とテスト / task_02 jis.json と実機目視（§4-1）/ task_03 正本反映

---

## 関連

* phase 55（キーボードUIのウィンドウ）/ phase 54（テンキーの区別・`key_input.md` §7.8）/ phase 51（key_hold の左右の修飾キー・`features.md` §4.2.12）
* 正本: `features.md` §4.6「キーボード表示のウィンドウ」/ `key_input.md` §7（送信の拡張キー）
