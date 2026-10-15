# 暫定仕様 43: キーボードUI の左右の修飾キーの区別と割り当て禁止のキー（keyboard_ui_left_right_modifiers）

> 状態: **未凍結・v0.4・ユーザー確定済（2026-10-15）・phase 59 の主入力（v0.2 = 起票時 deep-reviewer「修正して採用」・Codex 敵対的 needs-attention 2 件の反映 / v0.3 = §4 のユーザー判断の反映・Windows キーと Caps Lock の割り当て禁止を追加・差分の deep-reviewer「修正して採用」の反映 / v0.4 = AltGr 配列の右 Alt を標準の id `alt_gr`〔キー名 `alt gr`〕で書き分けて割り当て禁止に・ドイツ語配列の見本を同梱・差分の deep-reviewer「修正して採用」の反映）**。本書がこのフェーズの確定設計（フェーズ中は正本を直接改訂しない）。
> フェーズ末タスクで正本 `instructions/common/spec_detail/` へ昇格し本書を凍結する。
> 起票元: ユーザー要望（2026-10-15・キーボードUI は入力では左右を区別できるが、表示・編集が左右を区別せず、左右両方の枠に同じ割り当てが出て左のキーにしか効かない）。番号対応: phase 59 / 暫定 43 / decisions 59。

---

## §1 目的 / 背景

キーボードUI（キーボード表示のウィンドウ）で、左右の修飾キー（Shift・Ctrl・Alt・Windows）の枠を**左右別のキー**として表示・編集できるようにする。
枠のラベル（`Ctrl` 等）は変えず、内部で引くキー名だけを左右で分ける。
あわせて、抑止しても OS 側の動作が止まらない **Windows キー（左右）・Caps Lock・AltGr 配列の右 Alt** を、キーマップの元キーと切替キーに割り当てられないようにする（§3.5・§3.6）。

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
  deep-reviewer もフックが渡す組（scan_code・左右別の仮想キー・拡張フラグ）で `to_name` / `get_event_names` → `normalize_name` を計算し同じ結果（配列 0x0411・修飾の状態によらない。AltGr の配列では右 Alt が `alt gr`）。**実機のフックで届く名前は未実測**（実機目視で確かめる・§2）
* キーの取得の名前（`presentation/tk_keys.py`）: 通常の取得（表 `:45-55`・関数 `normalize_tk_key_event` `:71-78`）は左右を共通名へ。ただし**通常の取得はどれも修飾キー単独を捨てる**（`controllers/key_capture.py:137` 等・キーマップの編集・トリガー・直接切替キーのダイアログ）。key_hold の取得（`:80-94`）だけ左右を区別（`left windows` 等）。キーボードUI の編集中の送信先の取得も通常の名前（`keyboard_window.py:496-510`）で、修飾キー単独は割り当てない
  → 元キー `ctrl` / `shift` / `alt` / `windows` を単独で作れる経路は、**今のキーボードUI で修飾キーの枠をクリックすること**（共通名になる）と手編集だけ
* 正本: `features.md`「キーボード表示のウィンドウ（phase 55）」（:657 付近）に左右の扱いの記述は無い。レイアウト JSON の書式（`layout_id` / `keys` / `id` / `scan_code`）を規定した正本の節は無い
* 既存テストで `_LOOKUP_KEY_BY_ID` を直接見るものは無い（`tests_ui/test_task05_overlap_ui.py:242-247`・`test_task06_keymap_management_ui.py:138-146`・`test_trigger_effective_row.py:158-162` は `_display_map` / `_kind_map` を見る）

---

## §2 確定事項（ユーザー 2026-10-15）

* **枠のラベルはそのまま**（`Ctrl` / `Shift` / `Alt` / `Win`）。内部で左右を区別して、枠ごとに左右別のキーを表示・編集する
* **レイアウトの id → キー名の対応を左右で分ける**。左は今のキー名のまま（既存のキーマップの `ctrl` 等は左として効き続ける）、右は `right ctrl` 等（§3.1）
* **レイアウト JSON の書式は変えない**（任意の `"key"` 等の新しい記述方法は足さない。左右は既定の id で区別する）
* `config/user/keylayout/jis.json` に左右の Ctrl・Alt・Windows の行を既定の id で足す
* **右 Alt**: JIS・US 等（AltGr を使わない配列）では `alt_r` → `right alt` で**割り当て可**。**AltGr 配列**（ドイツ語等。右 Alt が `alt gr` で届く）では、レイアウトの JSON で右 Alt を**標準の id `alt_gr`**（キー名 `alt gr`）で書き、Windows キーと同じく**割り当て禁止**にする。入力配列はアプリが判定せず、**レイアウトのファイルが表す**（v0.4・§3.6）。AltGr 配列の実機確認はせず自動テストだけ（未確認として記録）
* **ドイツ語配列（AltGr 配列）の見本のレイアウト**を同梱する（右 Alt = `alt_gr`）
* **修飾キーの行の `scan_code` は「書かない」と規定するだけ**（コードで防がない）（§3.3）
* **Windows キー（左右）と Caps Lock は割り当て禁止**（抑止しても OS 側の動作〔スタートメニュー・Caps のロックの切替〕が止まらず、置き換えたキーと本来の機能が両方動くため）。
  **キーボードUI**（専用の色・クリックで編集を始めない・割り当ての入口でも拒否）と**切替キーの取得**（キーマップの編集ダイアログ・切替キーのまとめて設定ダイアログ）の両方で禁止する（§3.5）
* 右 Alt のキー名は keyboard ライブラリの表どおり（`right alt`）で実装し、実機目視で確かめる（食い違えばそのフェーズの中で表を直す）。左右 Windows（`left windows` / `right windows`）は割り当て禁止のため表示にしか効かず、表の値で確定する

---

## §3 設計

### §3.1 id → キー名の対応

キーボードUI が枠の id から引くキー名（表示・色・クリック範囲・編集の元キー）:

| id | キー名 | 備考 |
|---|---|---|
| `shift_l` / `shift_r` | `shift` / `right shift` | 左は今のまま |
| `ctrl_l` / `ctrl_r` | `ctrl` / `right ctrl` | 左は今のまま |
| `alt_l` / `alt_r` | `alt` / `right alt` | 左は今のまま。右は JIS・US 等で割り当て可（JIS は実機目視で確かめる） |
| `alt_gr`（新しい標準の id） | `alt gr` | AltGr 配列のレイアウトの右 Alt に使う。割り当て禁止（§3.5・§3.6） |
| `windows_l` / `windows_r` | `left windows` / `right windows` | 今は両方 `windows`。割り当て禁止（§3.5） |

* 根拠: 実行時にフックが届ける名前（§1 の表）と同じ名前で引けば、キーボードUI で設定した元キーがそのキーの押下で効く
* 修飾キー以外の id の対応（`grave` → `` ` `` 等・`keyboard_window.py:36-46`）は変えない
* `_LOOKUP_KEY_BY_ID` は固定の対応表のまま（配列の判定は持たない）。`alt_gr` の行を足すだけ

### §3.2 キーボードUI の挙動（左右を分けた結果）

* 表示: 左右の枠にそれぞれのキー名の割り当て（キーマップの送信先・トリガー・停止 / トグルキー）を出す。色（種類）も枠ごと
* 編集: 右の枠をクリックすると元キー `right ctrl` で編集を始め、割り当てると `right ctrl` → 送信先のマッピングができる（左は `ctrl`）。編集中の強調はクリックした側の枠だけ
* **右クリックでのクリア**も枠のキー名で行う（`keyboard_window.py:443-453` → `keymap_panel_controller.py:642`）: 右の枠を右クリックすると `right ctrl` の割り当てを消し、左の `ctrl` には触らない（今は左右どちらを右クリックしても共通名を消す）
* 直接切替キー（`KM<n>`・`keyboard_window.py:172-179`）・停止 / トグルキーの表示も枠ごとのキー名で引く。編集中のタイトルは `編集中: right ctrl` / `編集中: left windows` のようにそのキー名になる（`features.md`「キーボード表示のウィンドウ」のタイトルの書式のまま）
* 編集中の送信先の取得（キーを押して決める）は今のまま（修飾キー単独は割り当てない・組み合わせの名前は通常の取得の名前）
* キーマップの照合・フック・送信（`key_input.md`）は変えない。**画面の枠の表示中**は、Ctrl・Alt・Windows を押している間と修飾キー単独の押下は枠の振り分けで素通しになり、トリガー・置換へ進まない（`key_input.md` §7.3・`input_router.py` `_route_grid_key`。既存の規定のまま）→ 修飾キーの割り当ては枠の非表示中だけ効く

### §3.3 レイアウト JSON

* 書式は変えない。左右の修飾キーは既定の id（`shift_l` 等）で書く
* **左右の修飾キー・Caps Lock・Windows キーの行に `scan_code` を書かない**（書くと実行時の入力のキー名がその id〔例 `shift_r`〕になり、キーマップの照合と押下状態の記録〔`key_state_manager.py:100-101`〕が変わる。さらに左右の Ctrl・Alt は同じ走査コードで拡張フラグでしか区別できない）。規定だけでコードでは防がない（§2）
* `jis.json` の追加（見本の配置。最下段 y = 5.2・高さ 1.0。既存の無変換 x = 3.0〜スペース x = 7.5〜10.5 の前後に置く）:
  `ctrl_l`（`Ctrl`・x 0.0・w 1.0）/ `windows_l`（`Win`・x 1.0・w 1.0）/ `alt_l`（`Alt`・x 2.0・w 1.0）/ `alt_r`（`Alt`・x 10.5・w 1.0）/ `windows_r`（`Win`・x 11.5・w 1.0）/ `ctrl_r`（`Ctrl`・x 12.5・w 1.5）

### §3.4 既存データとの関係

* キーマップ・トリガーの元キー `ctrl` / `shift` / `alt` は左の枠だけに出る（実行時も左のキーでしか効いていなかった = 見た目が実際の挙動に合う）
* 元キー `right ctrl` 等（手編集・key_hold の取得等で入っていたもの）は右の枠に出るようになる
* 元キー `windows`（phase 55 以降に**今のキーボードUI の Win の枠**で作った割り当て・手編集。実行時は左 Windows が `left windows` で届くので一度も効いていない見込み）は**どの枠にも出ない**。キーマップのデータには残る（自動で消さない・受容）
* 既存の元キー `caps lock` / `left windows` / `right windows` の割り当て・切替キーは自動で消さない（読込で拒否しない）。割り当てはキーボードUI の禁止の枠に重ねて表示し右クリックで消せる / 切替キーは編集ダイアログで別のキーへ変える（§3.5）
* キーマップの割り当て（元キー → 送信先）を作る入口はキーボードUI だけ（`keymap_panel_controller.py:606` `assign_keymap_from_keyboard_ui`）。キーマップの編集ダイアログが扱うのは切替キーとラベル

### §3.5 割り当て禁止のキー（v0.3）

* **禁止のキー**: Windows キー（左右）・Caps Lock・AltGr 配列の右 Alt（`alt gr`・§3.6）を、**キーマップの元キー**と**キーマップの切替キー**にできない。
  判定は 1 か所の関数（例 `is_prohibited_assign_key(name)`）で行い、キーボードUI・割り当ての入口・切替キーの検査で共有する。
  判定する名前の集合 = `left windows` / `right windows` / `windows` / `caps lock` / `caps_lock` / `capslock` / `alt gr` / `altgr`（`alt gr` は §3.6）
  （Tk の取得は Caps を `caps_lock` と記録する〔`tk_keys.normalize_tk_keysym('Caps_Lock')`・実測〕。アプリの正規化は小文字化だけで下線を空白にしないため、表記の揺れも含める）
* **キーボードUI**（判定は枠の id ではなく `_LOOKUP_KEY_BY_ID` を通した後の**キー名**で行う。組み込みの US 配列の Caps の id は `caps lock`、jis.json の見本は `caps_lock`）:
  * 禁止のキー名の枠（`windows_l` / `windows_r` / Caps / `alt_gr`）は**専用の色**（「禁止」の種類。既存の種類と区別できる灰色系）で出す。
    ただし**トリガー・停止 / トグルキー・切替キー（`KM<n>`）の役割があればその色を優先**する（禁止の色は役割の無い枠と、キーマップの割り当て〔元キー〕だけの枠に使う）
  * 禁止の枠を左クリックしても**編集を始めない**（何もしない。別の枠を編集中ならその編集を続ける）
  * 既存の割り当て（元キー → 送信先）があれば送信先の文言を出し、**右クリックで消せる**（右クリックで消えるのは割り当てだけ。切替キーは消えない＝従来どおり）
  * 割り当ての入口（`keymap_panel_controller.assign_keymap_from_keyboard_ui`）でも元キーが禁止のキーなら割り当てず、**False を返してエラーを出す**（他の拒否〔単キーのみ等〕と同じ扱い・`messagebox.showerror`）。キーボードUI からは禁止の枠で編集が始まらないので通常は届かない（防御）
* **切替キー**（キーマップの編集ダイアログ・切替キーのまとめて設定ダイアログ。入力欄は読み取り専用で、値は取得でしか入らない）:
  * **取得**: Caps Lock を押しても取得しない（無視して取得を続ける。Windows キーは今も修飾キー単独として無視）
  * **検査**（防御）: 既存の切替キーの検査と同じ層に入れる = 編集ダイアログは `keymap_panel_controller.validate_keymap_switch_assignment`（ダイアログを閉じた後に出す・既存の重なりの検査と同じ扱い）/
    まとめて設定は `application/keymap_switch_batch.validate_switch_batch`（閉じずにその行へフォーカス・既存と同じ）
  * **今の切替キーから変えたときだけ検査する**（既存の切替キーが `caps lock` のキーマップでラベルだけ変えて OK しても拒否しない。`apply_keymap_edit` の `current_switch_key` と同じ考え方）
  * 既存の禁止キーの切替キーを外すには、編集ダイアログで別のキーへ取得し直す（2 つ以上のキーマップがあると空にはできない・`features.md` §4.3）
* 読込（構成セット・keymap ファイル）では検査しない（既存データを拒否しない・一覧のグレー表示もしない・§3.4・§6）

### §3.6 AltGr 配列の右 Alt（v0.4）

* **背景**（keyboard ライブラリ `keyboard/_winkeyboard.py:421-427`・`:501-529`）: AltGr 配列で右 Alt を押すと、Windows は偽の左 Ctrl（走査コード 541・仮想キー 0xA2）と右 Alt（0xA5）の 2 つを送る。
  ライブラリは偽の左 Ctrl を名前 `alt gr` のイベントとしてアプリへ届け、**押下では続く右 Alt を必ずアプリへ見せずに OS へ通す**（抑止できない）。
  → 割り当てると、割り当ての動作と OS 側の右 Alt（離したときのメニューバーの起動、AltGr との組み合わせの文字が Alt との組み合わせとして渡る等）が両方起きる（Windows キーと同じ状況）。
  **解放の順**（右 Alt の解放がアプリへ届くか）は Windows の送出の順しだいで、未確認（ライブラリの既存の挙動・結論〔禁止〕は押下だけで成り立つ）
* **実行時のキー名**: OS が偽 Ctrl を出せば必ず `alt gr`（走査コード 541 は配列の表によらずライブラリが `alt gr` と名付ける・`:424-427`。レイアウトの `scan_code` にも既知の特殊キーにも 541 は無いので `input_router._extract_key_name` は `event.name` を使う）。
  偽 Ctrl を出すかは入力を受けるウィンドウの配列で OS が決める（アプリ・ライブラリの判定に依らない）。`input_router` は変えない（`key_state_manager.py:31` は `alt gr` を `alt` にまとめる＝既存どおり）
* **配列の書き分けはレイアウトのファイルで行う**: 新しい標準の id **`alt_gr`**（キー名 `alt gr`）を足す。AltGr 配列のレイアウトは右 Alt の行を `alt_gr` で書く。JIS・US 等は `alt_r`（`right alt`）。
  アプリは入力配列を判定しない（ユーザーが今の入力配列に合うレイアウトを選ぶ）
* **禁止**: §3.5 の判定の集合に `alt gr` / `altgr` を足す（元キー・切替キーとも）。キーボードUI では `alt_gr` の枠が禁止の色・クリックで編集しない（§3.5 の規則のまま）
* **見本のレイアウト**: `config/user/keylayout/de.json`（`layout_id` = `de`・`display_name` = `Deutsch (QWERTZ)`）を同梱する。`jis.json` と同程度の見本
  （最上段の Esc・F1・F2 / 数字の 1・2 / Q・W・**Z**〔QWERTZ の位置〕/ Caps・A・Enter / 左右の Shift / 最下段の Ctrl・Win・Alt・Space・**AltGr〔`alt_gr`・ラベル `AltGr`〕**・Win・Ctrl）。
  修飾キー・Caps・Windows・AltGr の行は `scan_code` を持たない（§3.3）。座標は jis.json の作法（y = 0.0 / 1.2 / 2.2 / 3.2 / 4.2 / 5.2・高さ 1.0）で重ならないように置く（具体値はタスクで決める）
* **既存の割り当て**（§3.4 と同じく消さない）:
  * 元キー `alt gr` の割り当ては、`alt_gr` の枠があるレイアウト（AltGr 配列）では禁止の枠に重ねて表示し右クリックで消せる。`alt_gr` の枠が無いレイアウト（JIS・US）ではどの枠にも出ない（キーマップのデータには残る・受容）。抑止すると偽 Ctrl だけ止まり右 Alt は OS へ届く（既存どおり・受容）
  * 元キー `right alt` の割り当ては AltGr 配列の PC では届かず効かない（`alt gr` で届くため。二重には動かない・受容）。AltGr 配列のレイアウトでは右 Alt の枠が `alt_gr` なので表示もされない
* **取得のダイアログ**（切替キー）で AltGr 配列の右 Alt を押したときに何が記録されるか（偽の左 Ctrl が先に来るため Ctrl になる見込み）は未確認・スコープ外（§6）。切替キーの検査に `alt gr` を入れるのは、読込以外の経路への保険

---

## §4 確認事項（ユーザー判断・未確定）

（v0.3 で §4-1〜5 はすべてユーザー判断済み → §2 へ移した。未確定事項なし）

* 経緯: §4-1 右 Alt・Windows の名前 → 表どおり + 実機目視 / §4-2 既存の `windows` → 出さない（Windows キーは割り当て禁止になったため）/ §4-3 `scan_code` → 規定だけ /
  §4-4 Windows キーの OS の反応 → 割り当て禁止にして回避 / §4-5 右 Alt の配列 → JIS・US 等のみ

---

## §5 受け入れ条件（ドラフト）

1. 【tests_ui】キーボードUI で左右の Shift・Ctrl・Alt の枠が、それぞれ §3.1 のキー名の割り当て（文言・色）を出す。左右で別の割り当てを出せる（`_key_bounds` / 描画の結果で確かめる）（§3.1・§3.2）
2. 【tests_ui】右 Ctrl の枠をクリックして割り当てると、キーマップに元キー `right ctrl` のマッピングができる。左 Ctrl の枠は `ctrl`（従来どおり）（§3.2）
3. 【tests_ui】編集中の強調はクリックした側の枠だけ・タイトルはそのキー名（§3.2）
4. 【tests_ui】右の枠の右クリックは `right ctrl` だけを消し、左の `ctrl` は残る（§3.2）
5. 【tests_ui】既存のキーマップの `ctrl` / `shift` / `alt` は左の枠だけに出る / 元キー `windows` はどの枠にも出ない（§3.4）
6. 【tests_ui】左右の Win・Caps Lock の枠は禁止の色で、クリックしても編集が始まらない（編集中の別の枠の編集は続く）。役割（トリガー・切替キー等）のある枠はその色。既存の `caps lock` の割り当ては文言が出て右クリックで消せる。`assign_keymap_from_keyboard_ui` に禁止のキーを渡すと False でデータが変わらない（§3.5）
7. 【tests_ui / tests】キーマップの編集ダイアログ・まとめて設定ダイアログで、取得中の Caps Lock は無視される。検査（`validate_keymap_switch_assignment`・`validate_switch_batch`）は禁止のキー（`caps_lock` の表記を含む）を拒否し、まとめて設定は閉じずにその行へフォーカス。今の切替キーが禁止のキーで変えない OK は通る（検査の入力は `key_var` へ直接入れて確かめる）（§3.5）
8. 【実機・画面の枠は非表示・JIS 配列】右 Ctrl・右 Shift・右 Alt の枠に割り当てると、そのキーの押下で効き、反対側のキーでは効かない。左の枠の `ctrl` 等は従来どおり左で効く（§2・§3.1）
9. 【実機・JIS 配列】Caps キーを単独 / Shift 付きで押したときの、フックで届く名前と取得のダイアログで記録される名前を確かめ、どちらも禁止の判定に当たる（JIS の Caps キーは Shift なしで英数〔`VK_OEM_ATTN`〕を送る可能性があり、名前が `caps lock` にならないかもしれない・未確認）。当たらなければそのフェーズの中で判定の集合を直す（§3.5）
10. 【静的】`jis.json` に左右の Ctrl・Alt・Windows の行があり、修飾キー・Caps・Windows の行は `scan_code` を持たない（§3.3）
11. 【tests / tests_ui・実機なし】`alt_gr` の枠のキー名が `alt gr` で禁止の色・クリックで編集しない / `alt_r` の枠は `right alt` で割り当て可 / `alt gr` が割り当ての入口・切替キーの検査で拒否される /
    走査コード 541・名前 `alt gr` の偽のイベントを `InputRouter` に渡すと入力のキー名が `alt gr` になる / `de.json` を読み込めて `alt_gr` の行がある（§3.6。ライブラリが右 Alt を通す挙動・AltGr 配列の実機確認はしない＝未確認として記録）
12. 既存のテスト（compileall / tests / tests_ui / smoke）が通る

---

## §6 スコープ外（本フェーズでやらない）

* キーの取得のダイアログ（通常の取得）で修飾キーの左右を区別すること / キーボードUI の送信先の取得で左右を区別すること
* トリガーのキー・停止 / トグルキー・送信先（キーマップの送信先・hotkey）での Windows キー・Caps Lock の禁止（禁止の理由はトリガーにも当てはまるが、ユーザーの指定の範囲 = 元キーと切替キー）/
  既存の禁止のキーの割り当て・切替キーの自動の削除・移行 / 読込時のグレー表示・理由の表示
* AltGr 配列の実機確認（§2・自動テストだけ）/ ライブラリが通す右 Alt（AltGr 配列）の抑止（禁止で回避・§3.6）/ アプリによる入力配列の判定（レイアウトのファイルで書き分ける）
* AltGr 配列で切替キーの取得のダイアログが右 Alt を何として記録するか（§3.6・未確認）/ 元キー `alt gr` の割り当てを JIS・US のレイアウトのキーボードUI から消すこと（キーマップのデータに残る）
* 画面の枠の表示中に修飾キーの割り当てを効かせること（入力の優先順位の変更が要る）
* キーボードUI の編集中の送信先の取得で、Tk の `keycode`（Windows では仮想キーコード）を走査コードとして解決しているため F1 / F10 / F12 が `kana` / `henkan` / `muhenkan` になる見込みの既存の不具合（`keyboard_window.py:507`・deep-reviewer の指摘・別 idea に起票）
* 押しているキーの枠を光らせる表示（今も無い）
* レイアウト JSON の新しい記述方法（`"key"` 等）・レイアウト JSON の書式の正本化

---

## §7 正本反映（フェーズ末昇格・予定）

* 正本: `features.md`「キーボード表示のウィンドウ（phase 55）」に左右の修飾キーの枠の規則（§3.1 の表・§3.2）・標準の id `alt_gr` と AltGr 配列のレイアウトの書き方（§3.6）・レイアウトの修飾キーの行に `scan_code` を書かない規則（§3.3）・禁止の枠（§3.5）/
  `features.md` §4.3（keymap）に割り当て禁止のキー（元キー・切替キー）
* 実装: `presentation/keyboard_window.py`（`_LOOKUP_KEY_BY_ID`・禁止の色と編集の抑止）/ `controllers/keymap_panel/keymap_panel_controller.py`（`assign_keymap_from_keyboard_ui` の拒否）/
  `dialogs/keymap_edit_dialog.py`・`dialogs/keymap_switch_batch_dialog.py`（取得の無視）/ `keymap_panel_controller.validate_keymap_switch_assignment`・`application/keymap_switch_batch.py`（検査）/
  禁止の判定の関数（置き場はタスクで決める）/ `config/user/keylayout/jis.json`・`config/user/keylayout/de.json`（新規・見本）
* テスト: `tests_ui/` にキーボードUI の左右の枠の表示・編集・禁止の枠のテスト、切替キーのダイアログの禁止のテスト / `tests/` に割り当ての入口の拒否
* `codebase_map.md`（キーボードUI の節）
* タスク見込み: task_01 左右の対応表とテスト / task_02 割り当て禁止（キーボードUI・入口・切替キーのダイアログ）とテスト / task_03 `alt_gr` の id・`de.json` の見本（§3.6）とテスト / task_04 jis.json と実機目視（JIS）/ task_05 統合確認 / task_06 正本反映

---

## 関連

* phase 55（キーボードUIのウィンドウ）/ phase 54（テンキーの区別・`key_input.md` §7.8）/ phase 51（key_hold の左右の修飾キー・`features.md` §4.2.12）
* 正本: `features.md` §4.6「キーボード表示のウィンドウ」/ `key_input.md` §7（送信の拡張キー）
