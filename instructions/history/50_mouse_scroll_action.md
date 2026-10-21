# 暫定仕様 50: 出力シーケンスのマウススクロール（mouse_scroll_action）

> 状態: **凍結（2026-10-21・正本反映済）**。正本が最新。本書は経緯記録として凍結（v0.4）。
> 正本: `data_schema.md` §5.11.1・§5.11.10・`features.md` §4.2・§4.6・`codebase_map.md`。判断は `.claude_data/state/decisions_archive/67_mouse_scroll_action.md`。
> 起票元: ユーザー要望（2026-10-21・出力シーケンスのアクションの種類に「マウススクロール」を追加したい）。番号対応: phase 67 / 暫定 50 / decisions 67。

---

## §1 目的 / 背景

出力シーケンスの行で**マウスのホイールを回す（縦・横のスクロール）**操作を送れるようにする。新しい種類 `mouse_scroll` を足す。

### 現状監査（2026-10-21）

- 種類は hotkey / text / mouse_click / system / file_line / key_hold（`data_schema.md` §5.11.1）。スクロールは無い（`keyseq/` に scroll / wheel の送信なし・grep で確認）。
- アクションは辞書のまま扱い、種類ごとの型・列挙は無い。読込の正規化は `keyseq/domain/config.py` の `normalize_actions`（種類を問わない）。新しい種類で読込・保存の経路は変わらない。
- 実行の分岐 = `keyseq/application/action_executor.py:110-151`（`execute()`）・未知の種類の文言 = 同 `:201`。mouse_click = `:307-350` → `InputGateway.click_mouse` / `drag_mouse`。key_hold のマウスの行の検証 = `keyseq/domain/key_hold.py`（`parse_key_hold`）。
- 送信の具象 = `keyseq/infrastructure/input_gateway.py`。マウスは pyautogui（`:398-440`）。カーソルの移動だけの `move_cursor`（`:237-244`・FailSafe を外し待ちなし）が既にある。mouse_click は `pyautogui.click(x=,y=)`（FailSafe 有効・`PAUSE` 0.1 秒の待ち）。pyautogui の FailSafe の点は画面の 4 隅（`pyautogui/__init__.py:573` で左上・`:2169-2171` で残り 3 隅を追加。主画面の大きさで決まる）。pyautogui の関数の呼び出しの前に判定し、カーソルが 4 隅にあれば例外（`:587-596`）。キーの送信の一部は ctypes の `SendInput`（`_MOUSEINPUT` 構造体も定義済み・`:65-82`・`_send_input_api` `:157`）。
- **pyautogui のスクロールは使わない**（`.venv/Lib/site-packages/pyautogui/_pyautogui_win.py:507-560` を実読）: ①Windows の `_hscroll` は `_scroll`（縦の `MOUSEEVENTF_WHEEL`）を呼ぶだけで**横に回らない** ②量は `mouseData` へそのまま渡る（1 ノッチ = 120 を呼び手が掛ける必要）③送信の `PermissionError` / `OSError` を握りつぶす。
- ダイアログ = `keyseq/presentation/dialogs/action_dialog.py`（種類の候補 `:52`・OK の検証 `:189-`・種類ごとの欄の表示 `:428-466`・座標の取得 `:312-336`〔pynput で次のクリック位置〕）。key_hold のマウス欄 = `action_key_hold_fields.py`（座標の取得を再利用）。
- 一覧 = `domain/config.py` の `format_action_list_item`（`:432-`）/ 省略表示の「次に実行」 = `presentation/controllers/action_list_rendering.py:49-76`。
- **「送った」と止まる系は `execute()` の戻り値で決まる**: `False` = 止まる系（`run_to_end.py:250-253`・`sequence_runner.py:120-125`・`call_run_to_end.py:188`・`call_wait.py:181`）。mouse_click は常に `True`（`action_executor.py:141-143`）。止まる系の通知は `_report_held_error`（`:265-269`・持ち主の押下中を離してから `_on_action_error`）で、表示は「種別 / 値（`action["value"]`）/ エラー」（`hook_controller.py:385-394`）。
- 正本: `data_schema.md` §5.11 / `features.md` §4.2（冒頭 `:37` の通常アクションの列挙・§4.2.8 の「送った」・§4.2.12 のエラー時の解放）・§4.6（一覧の表示形式・出力シーケンスの編集）。

## §2 確定事項（ユーザー 2026-10-21）

- **向きは上下左右**（1 つの種類で `direction` = up / down / left / right）
- **量の単位は「ノッチ数」と「生の値（120 = 1 ノッチ）」の両方を選べる**。既定はノッチ数。ダイアログでは選んでいない方の入力欄をグレーアウトする（選択式）
- **座標は任意**: 指定があればそこへカーソルを移してからスクロール、無ければ今のカーソル位置。座標の取得は mouse_click と同じ手段（key_hold のマウスの行と同じ扱い）
- **複数ノッチは 1 ノッチずつ連続で送る・間隔の指定は置かない**（ゆっくり回したいときは待機・ループで組む）
- **v0.3 の確認事項 Q1〜Q5 を推奨どおり確定**（§8）: 上限 ノッチ 100・生の値 12000 / 既定 ノッチ 1（生の値 120）/ FailSafe 無効（`move_cursor`）/ `unit` は キー無し・空だけ notch・それ以外はエラー / 一覧は `[スクロール] 下 3`

## §3 JSON（`data_schema.md` §5.11 に §5.11.10 として追加予定）

```json
{"type": "mouse_scroll", "direction": "down", "unit": "notch", "amount": 3, "label": ""}
{"type": "mouse_scroll", "direction": "right", "unit": "delta", "amount": 60, "x": 400, "y": 200, "label": ""}
```

| キー | 型 | 意味 |
|---|---|---|
| `direction` | str | `up` / `down` / `left` / `right`（実行時に trim + 小文字で判定）。それ以外・非文字列は実行時エラー |
| `unit` | str | `notch` = ノッチ数 / `delta` = 生の値（120 = 1 ノッチ）。**キー無し・空（trim 後）は `notch`**。それ以外の文字列・非文字列は実行時エラー（§8 Q4） |
| `amount` | int | 量。`notch` は 1〜100・`delta` は 1〜12000（= 100 ノッチ）の整数。受け入れ = 整数・整数の値の実数（`3.0`）・`int()` で変換できる文字列（`"3"`）。**bool・整数でない実数（`2.7`）は不正**。欠落・変換不能・範囲外は実行時エラー |
| `x` / `y` | int | 任意（両方そろえて書く）。**判定は key_hold の `x` / `y` と同じ**（キーの有無で指定ありを判定・`null` でもキーがあれば指定あり → 変換不能・`domain/key_hold.py:63-72`）。片方だけ・変換不能は実行時エラー（mouse_click の「座標不正は止まらない」とは違う） |
| `label` | str | 一覧表示用（他の種類と同じ） |

- **読込の正規化は他の種類と同じ**（`direction` / `unit` / `amount` / `x` / `y` は読込で書き換えず実行時に判定する。§5.1 の型不正の共通規則〔`config.py:175` の対象〕には足さない・key_hold の `edge` / `value` と同じ）
- **旧版アプリ**は `mouse_scroll` を未知の種類として読み、実行時に「種類が不正です」で止まる（§5.11.1・受容）
- 未知の種類の文言を「種類が不正です（hotkey / text / mouse_click / mouse_scroll / system / file_line / key_hold のいずれか）」へ改める

## §4 実行

1. 検証（§3 の実行時エラー）。不正なら何も送らない
2. 座標の指定があれば、カーソルをその画面の絶対座標へ瞬時に移す（**既存の `move_cursor` を使う = FailSafe を外し・待ちなし**。key_hold のマウスの行と同じ・§8 Q3）
3. ホイールの事象を送る:
   - 縦（up / down）= `MOUSEEVENTF_WHEEL`・横（left / right）= `MOUSEEVENTF_HWHEEL`
   - 符号: up = 正・down = 負 / right = 正・left = 負（Windows の WHEEL / HWHEEL の定義どおり）
   - **ノッチ**: 量 N → 1 事象あたり ±120 を N 個
   - **生の値**: 量 D → 120 ずつに分け、端数を最後に（例 300 → 120, 120, 60）
   - **1 回の `SendInput` で全事象をまとめて送る**（間隔なし・物理入力が間に挟まらない）。`SendInput` の戻り値が送った数に満たなければ例外（キーの送信と同じ `OSError`）
   - 実装の注記: `INPUT_MOUSE`（= 0）・`MOUSEEVENTF_WHEEL`（0x0800）・`MOUSEEVENTF_HWHEEL`（0x1000）の定数を足す。`mouseData` は DWORD なので負の値は 2 の補数（-120 → `0xFFFFFF88`）で入れる（テストで値を固定する）
4. **send guard の対象外**（マウスの事象はキーフックが見ないため・mouse_click と同じ）
5. 戻り値: 送れたら `True`・§3 の実行時エラーと送信の例外は `False`（止まる系）。runner 側の変更は要らない

### 受容する制約

- 座標を指定しても、その位置の窓がスクロールされるとは限らない（Windows の「非アクティブウィンドウをホバーしたときにスクロールする」が OFF だとフォーカスのある窓へ届く）。移動とホイールの間に物理のマウスの動きが入り得る（key_hold と同じ）
- 横のホイール（HWHEEL）に応じるかはアプリ次第
- `SendInput` が途中までしか送れなかったとき（戻り値 < 個数）は一部が送られたまま止まり、再実行で全量を送り直す。UIPI で拒否された入力は戻り値で分からない（キーの送信と同じ）

### エラーの扱い（止まる系）

- §3 の実行時エラー・送信の例外は **key_hold と同じ「止まる系」**: そのトリガーの実行を終え、位置はエラーの行に残る。通知は `_report_held_error` の経路（持ち主の押下中を離してから知らせる）で、**メッセージに理由と `direction=… unit=… amount=…`（座標があれば `x=… y=…`）とラベル（空でなければ）を含める**（通知の「値」の欄は `value` が無いので空になるため）
- `features.md` §4.2.12 の「実行を終える実行時エラーなら知らせる前に押下中のキーを離す」に mouse_scroll も含める
- mouse_click の「座標不正は止まらない」とは分ける（新しい種類で旧来の互換の縛りが無く、向き・量の取り違えは誤操作につながるため）

### 他の規定への組み込み

- **通常アクション**（`features.md` §4.2 冒頭・§4.2.9 の呼び出し先の行の表）に加える。送る行としての数え方は hotkey と同じ（待機の「直前に送った行」〔§4.2.5〕・戻す履歴の段・停止の読み飛ばしの「送った」〔§4.2.8〕・止まる系のエラーで終わったものは数えない）
- 確認して実行・呼び出し・ステップ実行などは通常アクションとして既存どおり（特別扱いしない）

## §5 ダイアログ（`features.md` §4.6「出力シーケンスの編集」に追加予定）

- 種類の候補に `mouse_scroll` を加える（ダイアログを開くすべての文脈・mouse_click の直後）
- 入力欄（mouse_scroll のときだけ表示・他の種類の欄は従来どおり非表示）:
  - **向き**: 上 / 下 / 左 / 右（読み取り専用のドロップダウン・既定 下）
  - **量**: 「ノッチ数」「生の値（120 = 1 ノッチ）」のラジオボタン（既定 ノッチ数）と、それぞれの入力欄（既定 ノッチ数 = 1・生の値 = 120）。**選んでいない方の欄はグレーアウト**（`state="disabled"`・値は残す）
  - **「座標を指定する」+ X / Y + 座標の取得**（key_hold のマウスの行と同じ部品・同じ取得手段）。チェックが外れていれば X / Y はグレーアウト。新しい取得ボタンは `_set_mouse_capture_state`（`action_dialog.py:307-310`）に加えて mouse_click・key_hold の取得と同時に動かないようにする
- 既存の行を開いたとき:
  - **単位**: `unit` が notch（キー無し・空を含む）ならノッチ・`delta` なら生の値を選ぶ。**不正な単位（それ以外の文字列・非文字列）はどちらも選ばない**（両方の欄を使える状態にし、`amount` は両方の欄に出す）。どちらかを選ぶまで OK は「単位を選んでください」で拒否する（編集だけで量の意味が変わるのを防ぐ）
  - **量**: §3 で有効な値は**解析後の整数**を欄に出す（`3.0` → `3`・`"3"` → `3`）。不正な値は元の値をそのまま文字にして出す（直すため）。選ばなかった方の欄は既定値
  - **向き**: 4 つ以外なら「下」を出す（向きは向きの欄で目に見えるので、単位と違い選ばせ直さない）
  - `x` / `y` のキーがあれば「座標を指定する」を ON（値は量と同じく、有効なら整数・不正なら元の値の文字）
- **OK**: 種類の検査（`action_dialog.py:189`）に `mouse_scroll` を加え、§3 の実行時エラーに当たる入力を拒否し理由を出す（ダイアログは閉じない・検査は domain の `parse_mouse_scroll` を使う）。保存は `type` / `direction` / `unit` / `amount`（選んだ方の欄の値）/ `label`、座標を指定したときだけ `x` / `y`（外したら書かない）
- **開いたときの入力先**: 値の欄が無いので種類のドロップダウン（mouse_click と同じ）。種類の切替で隠れる欄にフォーカスがあればドロップダウンへ移す判定（`_focus_is_hidden_for_type`・`:475-494`）に新しい欄を加える

## §6 一覧の表示（`features.md` §4.6「一覧の表示形式」に追加予定）

| 行 | 表示例 |
|---|---|
| ノッチ | `[スクロール] 下 3` |
| 生の値 | `[スクロール] 右 60 (生)` |
| 座標あり | `[スクロール] 下 3 (100, 200)` / `[スクロール] 右 60 (生) (100, 200)` |
| 不正な行（§3 の実行時エラーに当たる行） | `[mouse_scroll] <direction の値>`（`direction` が無い・非文字列なら `[mouse_scroll]` だけ） |

- ラベルがあれば末尾に `: ラベル`（key_hold と同じく `[type]` の接頭辞を付けない分岐・`config.py:445-471` / `action_list_rendering.py:59`）。フル表示の一覧・省略表示のシーケンス欄と「次に実行」の要約・呼び出し先の表示枠で同じ書式

## §7 構成（実装の置き場）

- domain: `keyseq/domain/mouse_scroll.py`（新規・`key_hold.py` と同じ形）= 種類名の定数・`MouseScrollSpec`（向き・単位・量・座標）・`parse_mouse_scroll`（§3 の検証・エラー文言）・事象の量の列への分解（§4-3）・一覧の値の書式（§6）
- application: `ActionExecutor.execute()` に分岐を足し、`parse_mouse_scroll` → `InputGateway.scroll_mouse(...)`。エラーは止まる系の通知へ
- infrastructure: `InputGateway.scroll_mouse(vertical: bool, deltas, x, y)`（座標があれば移動 → `SendInput` で WHEEL / HWHEEL をまとめて送る）
- presentation: `action_dialog.py` の種類の候補・欄の表示切替・OK の検証（欄は肥大化を避け `action_mouse_scroll_fields.py` へ分ける・`action_key_hold_fields.py` と同じ形）/ `config.py` の `format_action_list_item`・`action_list_rendering.py` の要約に分岐

## §8 確認事項（**2026-10-21 ユーザー確定・すべて推奨どおり**）

- **Q1 量の上限**: ノッチ 100・生の値 12000 を上限にする（誤入力〔桁の打ち間違い〕で大量に回すのを防ぐ）。推奨: この値
- **Q2 既定値**: 新規はノッチ 1（生の値の欄は 120）。推奨: この値
- **Q3 FailSafe**（カーソルが画面の 4 隅にあると pyautogui が例外を出す安全機構）: **無効（key_hold と同じ・既存の `move_cursor`）**。理由: ①座標の無い行は `SendInput` だけで送り pyautogui を通らないので、有効にしても座標のある行だけに効くちぐはぐな安全策になる ②mouse_click でも FailSafe の例外は通知するだけでシーケンスを止めていない（`action_executor.py:332-333`）③スクロールは押したままの状態を作らない。失うもの = 座標のある行の実行前にカーソルを 4 隅へ寄せて止める操作。推奨: 無効
- **Q4 `unit` の不正**: キー無し・空だけ `notch`・**非文字列はエラー**（単位を取り違えると量が 120 倍変わるため厳格に。§5.1 の共通規則には足さない）。推奨: この扱い
- **Q5 一覧の書式**: §6（`[スクロール] 下 3`）。key_hold の `[押す]` と同じく日本語の表示名にする。推奨: この書式

## §9 受け入れ条件（ドラフト）

1. 4 方向 × 2 単位で、指定の量だけスクロールする（縦はメモ帳・ブラウザ等、横は横スクロールできる窓で目視）（§4）
2. 座標を指定した行はその位置で、無い行は今のカーソル位置でスクロールする（§4）
3. 生の値で 120 未満（例 60）を送ると、対応するアプリで細かく動く（端数の分割・§4）
4. 不正な行（向き・単位・量・座標）は送らずに止まる系のエラーになり、押下中のキーを離してから知らせる（§3・§4）
5. ダイアログ: 単位の切替で使わない欄がグレーになる・座標の取得が使える・OK で不正を拒否する・既存の行を開くと元の値が復元される・`amount: 3.0` の行をラベルだけ変えて保存できる（`3` で保存）・不正な単位の行は単位を選ぶまで保存できない（§5）
6. 一覧・省略表示・次に実行の要約・呼び出し先の表示枠が §6 の書式（§6）
7. 既存の種類の挙動・JSON は変わらない（tests / tests_ui / smoke が通る）

## §10 スコープ外

- スクロールの間隔・速度（ゆっくり回す）の指定（待機・ループで組む）
- key_hold のようにスクロールを「押したまま」続ける操作
- 画面の枠（screen_grid）でのスクロール
- ホイールの押し込み（中ボタン）は mouse_click の `middle` で既にある

## §11 正本反映（フェーズ末昇格・予定）

- `data_schema.md` §5.11.1（種類の表・未知の種類の文言・止まる系の列挙 `:443-444`）・§5.11.10 新設（§3・§4 の実行規定とエラー）
- `features.md` §4.2 冒頭（通常アクション）・§4.2.5（直前に送った行）・§4.2.8（送った）・§4.2.9 の表（通常アクションの列挙 `:277`）・§4.2.12（エラー時の解放）・§4.6（一覧の表示形式・出力シーケンスの編集・開いたときの入力先 `:826`）
- `codebase_map.md`（アクションの実行・マウス操作の節に `domain/mouse_scroll.py`・`scroll_mouse`・ダイアログの欄）
- 実装: `domain/mouse_scroll.py`（新規）・`domain/config.py`・`application/action_executor.py`・`infrastructure/input_gateway.py`・`presentation/dialogs/action_dialog.py`・`action_mouse_scroll_fields.py`（新規）・`presentation/controllers/action_list_rendering.py`
- テスト: `tests/`（parse・分解・書式・executor の分岐とエラー・gateway の事象の組み立て）/ `tests_ui/`（ダイアログ・一覧の書式）
- JSON スキーマ: **種類の追加**（既存キーの削除・意味変更なし）

## 関連

- 正本: `data_schema.md` §5.11 / `features.md` §4.2・§4.6
- 似た作り: phase 51（key_hold・暫定 35）= 種類の追加とマウスの座標の任意指定
