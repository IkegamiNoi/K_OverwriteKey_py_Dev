# decisions_archive / phase 67: 出力シーケンスのマウススクロール

対応表: phase 67 / 暫定 50（v0.4・凍結）/ decisions 67。起票元: ユーザー要望（2026-10-21・出力シーケンスのアクションの種類に「マウススクロール」を追加したい）。
完了 2026-10-21。domain（`domain/mouse_scroll.py`・`config.py` の一覧の書式）+ application（`ActionExecutor._execute_mouse_scroll`）+ infrastructure（`InputGateway.scroll_mouse`）+ presentation（`action_mouse_scroll_fields.py`・`action_dialog.py`・`action_list_rendering.py`）。**JSON スキーマ = 種類 `mouse_scroll` の追加**（既存キーの削除・意味変更なし）。
正本 = `data_schema.md` §5.11.1・§5.11.10 / `features.md` §4.2 冒頭・§4.2.8・§4.2.9・§4.2.12・§4.6 / 地図 = `codebase_map.md`「アクションの実行」「マウス操作」の phase 67 の項。

## 確定した設計判断（ユーザー 2026-10-21）

| # | 判断 | 採らなかった案と理由 |
|---|---|---|
| 1 | 1 つの種類 `mouse_scroll` で向き up / down / left / right | 上下だけ = 横スクロールの要望に足りない |
| 2 | 量はノッチ数（既定）と生の値（120 = 1 ノッチ）の選択式・使わない欄はグレー（ユーザーの「その他」回答） | どちらか一方だけ |
| 3 | 座標は任意（あれば移してから・無ければ今の位置）・取得は mouse_click と同じ手段 | 必須 / 座標なし |
| 4 | 1 ノッチずつ間隔なしで 1 回の `SendInput` にまとめる（生の値は 120 ずつ + 端数） | 間隔の指定 = 待機・ループで組める / まとめて 1 事象 = 1 ノッチ扱いのアプリがある |
| 5 | 上限 ノッチ 100・生の値 12000 / 既定 ノッチ 1 | 上限なし = 桁の打ち間違いで大量に回る |
| 6 | FailSafe を外す（既存の `move_cursor`・key_hold と同じ） | 有効 = 座標の無い行は pyautogui を通らず効かない・mouse_click でも止めていない |
| 7 | `unit` はキー無し・空だけ notch・非文字列はエラー（§5.1 の共通規則に足さない） | 非文字列も notch = 取り違えで量が 120 倍 |
| 8 | 不正な行は止まる系（key_hold と同じ・`execute()` が False）・通知に direction/unit/amount/座標/ラベル | mouse_click と同じ止まらない扱い = 向き・量の取り違えが誤操作になる |
| 9 | pyautogui のスクロールは使わず ctypes の `SendInput` | pyautogui = Windows の hscroll が縦に回る・量が生のまま・例外を握りつぶす（`_pyautogui_win.py:507-560` を実読） |

## タスク中の判断

### 【起票】モード = **暫定仕様先行**（JSON スキーマ・ダイアログ・実行・一覧に跨る・タスク 3）
### 【暫定 50】v0.1 → deep-reviewer 修正して採用（高 2 = 座標の移し方と FailSafe の前提〔`move_cursor` の見落とし〕/ 中 = x/y の判定は key_hold と同じ・「送った」は `execute()` の戻り値・通知の内容・正本反映の漏れ / 低 = SendInput の注記・受容する制約・一覧とダイアログの細部）→ v0.2 → Codex 敵対的 needs-attention 3 件（不正な単位が編集だけで notch になる → 未選択で OK 拒否 / `3.0` の復元で再保存できない → 解析後の整数で復元 / FailSafe は 4 隅〔`pyautogui/__init__.py:2169-2171`・v0.2 の「左上 1 点」は誤り〕）→ v0.3 → ユーザー確定（§8 Q1〜Q5 推奨どおり）= v0.4
### 【/phase_start 整合確認】reviewer 採用（軽微 2 件 = task_01 の unit の記述の自己矛盾・task_02 に呼び出し先の表示枠の確認）→ 反映
### 【task_01】codex-implementer・verifier: 新規テスト 5 件 fail = Codex のテストの誤り（trim で受け入れる `" up "` を不正として扱った・Mock の `release_owner` が反復できない・2 回目の送信の戻り値の不足）→ メインがテストを修正・既存テストの未知の種類の文言の期待値を更新 → tests 1815 / tests_ui 1130 / smoke OK・reviewer 採用（参考: `config.py` の種類の比較を定数へ → 反映）
### 【task_02】codex-implementer・verifier: 新規テスト 4 件 fail = Codex のテストの誤り（`cget("state")` を文字列と比較・非アクティブ時に `focus_get()` が None）→ メインが修正（`str()`・`focus_lastfor()`）→ tests 1815 / tests_ui 1141 / smoke OK・reviewer 採用（参考: `_parsed_amount` の冗長な分岐）
### 【task_03 実機目視】暫定 50 §9 / task_03 の 1〜6 = ユーザー OK（2026-10-21）
### 【task_03 正本反映】`data_schema.md` §5.11.1（種類の表・未知の種類の文言・止まる系の列挙）・§5.11.10 新設 / `features.md` §4.2 冒頭・§4.2.8・§4.2.9 の表・§4.2.12・§4.6（一覧の表示形式・出力シーケンスの編集・開いたときの入力先）/ `codebase_map.md`（アクションの実行・マウス操作の phase 67 の項）
### 【task_03 完了判定前レビュー】deep-reviewer 完了可（中 2・低 7）/ Codex 敵対的 needs-attention（medium 1）→ ユーザー確定（2026-10-21・推奨どおり）
- 修正して採用 → task_03a: Codex 1（`amount` の欠けた既存行をダイアログが既定値で埋め、ラベルだけの編集で実行できる行になる → 対象の欄を空にして OK で拒否）/ deep L4（`_parsed_amount` の冗長な分岐）/ deep L5（座標の取得中のボタンの状態のテスト 4 件）/ `/refactor_check` M6
- 採用（正本の文言・メインが直接）: deep M1（`unit` も trim + 小文字で判定）/ M2（隠れる欄のフォーカスの移し先に key_hold・mouse_scroll の欄）/ L1（止まる系の列挙の括弧書きのかかり先）/ L2（向きは読み取り専用のドロップダウン・負の `mouseData` の 2 の補数）/ L3（codebase_map の一般則の注記）
- 保留: deep L6（executor のテストの抜け = 持ち主が None・通知に座標）/ L7（`amount` の文字列で `"3_0"`・`"+3"` も受け入れる・実害小）
### 【task_03 /refactor_check】M6 該当（`action_mouse_scroll_fields.py` に domain の定数〔`UNIT_NOTCH` / `UNIT_DELTA` / `ACTION_TYPE_MOUSE_SCROLL` / `WHEEL_DELTA` / `DEFAULT_NOTCHES`〕と同じ直値）→ 提案書は起こさず task_03a で解消（2026-10-21）
- 範囲 `git diff 15b9b41..HEAD -- keyseq/`（7 ファイル・+400）。M1（600 行超なし・最大 `action_dialog.py` 589）・M2（80 行超の関数なし）・M5（0 件）は非該当
- M3: 座標の解析（`key_hold.py` と `mouse_scroll.py`）・座標欄（`action_key_hold_fields.py` と `action_mouse_scroll_fields.py`）は 2 個目 → 非該当 / M4: 種類の全列挙の箇所数は不変（要素が増えただけ）→ 非該当
### 【task_03a】codex-implementer（`action_mouse_scroll_fields.py` = 量の欠けた行は対象の欄を空・定数への置換・冗長な分岐 / テスト = 量の欠けた行 5 件・取得中のボタン 4 件）・reviewer 修正して採用（テストの 1 ケースの誤り = 空の `unit` は notch なのに未選択を期待）・verifier: 同じテストの期待文言の誤り（`""` の量は「量は整数に変換できる値…」）→ メインがテストを 2 か所修正 → tests 1815 / tests_ui 全 pass / smoke OK（参考: 量が無いときも `_parsed_amount` を先に呼ぶ・無害）
