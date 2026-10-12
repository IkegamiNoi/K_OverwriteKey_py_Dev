# decisions_archive / phase 56: 画面の枠でカーソル移動・クリック

対応表: phase 56 / 暫定 40（v0.7・凍結）/ decisions 56。起票元: ユーザー要望（2026-10-12・画面に枠を出し、キーで枠を選んでカーソルを中心へ・Enter でクリック・Space で細分化・境界をドラッグで編集して記録）。
完了 2026-10-13。domain（形の純関数）+ application（状態機械・振り分け）+ infrastructure（モニタ・カーソル・窓のスタイル）+ presentation（枠の窓・編集の窓・ダイアログ）。**JSON スキーマ変更あり**（keymap の任意キー `grid`）。
正本 = `data_schema.md` §5.6.1・`features.md` §4.7・`key_input.md` §7.3 / §7.4・`nonfunctional.md`「画面の枠の座標系」/ 地図 = `codebase_map.md`「画面の枠（phase 56）」。

## 確定した設計判断（ユーザー）

| # | 判断 | 採らなかった案と理由 |
|---|---|---|
| 1 | 枠 ON の keymap がアクティブな間だけ枠を出し、その間はトリガー・置換の代わりに枠の操作キーが効く | 常時表示 / ホットキーで出す = 既存の keymap の切替で出し入れできる |
| 2 | 追加のダイアログ（まとめて設定の新規の行）にも「枠を使う」/ 枠だけの構成でもフックを開始・再開できる | 編集ダイアログだけ = 追加のたびに 2 手 |
| 3 | 最上段の Esc は素通し・BackSpace は suppress（v0.6） | BackSpace も素通し（v0.5）= 誤って届くと文字を消す |
| 4 | 最上段は段ごとに列を独立・既定 3 × 4・画面ごとに比率で記録 | 全段同じ列 = タスクバー・×ボタンに合わせられない |
| 5 | DPI の状態は今のまま（SYSTEM_AWARE）・拡大率の混在は検証せず受容（task_01 の実測で成立） | 枠の窓だけ / アプリ全体を Per-Monitor 対応 = 既存 UI の見た目が変わる・不要 |
| 6 | カーソル移動・クリックは **pyautogui**（`_pause=False`・FAILSAFE を一時的に外す） | Win32 `SetCursorPos` + `SendInput` = 精度・速さは同等だが、Mac 対応の予定があり既存のマウス操作と経路をそろえる |
| 7 | 画面の識別子 = 矩形由来の `<幅>x<高さ><左><上>` | `szDevice` = 配置を変えても変わらず識別に使えない（task_01 の実測） |
| 8 | 編集の窓のキーの取り込みだけフックと同じ名前に（テンキー → 配列 → 修飾なしの文字 → Tk）。既存のキー取得は変えない（idea_45） | アプリ全体の変換表を直す = 影響の確認が大きい・JIS の記号は表だけでは合わない |
| 9 | 表記は「段」（段は列を内包・段はまとめて追加と削除）。一度「行」にして戻した | 「行」= 列と同格に見える |
| 10 | 細分化のキーはクリックしてキーを押す（v0.7・敵対的レビューで空白を含む名前を入れられない穴） | 行ごとの入力欄（空白区切り）/ 1 欄で `,` 区切り = `num 1` や `,` を表せない |
| 11 | キーの表示位置を keymap ごとに中央 / 左上（v0.7）。左上 = UI フォント + 暗い下地（角にぴったり）・中央 = 下地なし | 2 倍の太字・全体の下地 = 実機で試した上で現在の形を選んだ。配色は idea_44 |
| 12 | `label_position` は左上のときだけ書く（v0.7・敵対的レビュー） | 常に書く = v0.6 の `grid` を保存し直すと差分が出る |
| 14 | 起票時レビュー（deep-reviewer・修正要 16 件 → v0.2）の採用: 予約キーは固定分だけ読込時に検査し設定で変わる分は編集の OK でだけ拒否 / suppress は和集合で段に依存させない / ctrl・alt・windows の押下中は素通し / 最上段の既定は JSON に持たず組み込み定数 | 段ごとに suppress を変える = Space の直後に打ったキーが漏れる |
| 15 | 暫定 40 の敵対的レビュー（Codex・needs-attention 5 件 → v0.4）全件採用: DPI の前提の訂正（pyautogui の import で SYSTEM_AWARE）→ 検証は本番の起動経路で / 状態の世代 / 画面は識別子で保持 / Shift は振り分け時に採取 / 再開の条件にも grid | — |
| 16 | 編集の窓が背面に回るのは不具合として直す（task_06 の目視）。重なり順 = 操作パネル → 編集の窓 → 他（モーダルの作法の「前面化しない」の例外） | — |
| 13 | 統合レビューの採否（task_07・推奨どおり）: 今直す = 1 × 1・窓が無いときの suppress（畳んで再試行しない）・on_font_changed の例外・自分の切替キーを予約から除く・LastError | — |

## 結果（タスク）

- task_01 画面・座標の検証スパイク（scratchpad の probe・ユーザーの実機）→ 既定案で成立（自アプリが前面のとき Toplevel の作成で前面を取られる発見）
- task_02 domain と JSON の 4 経路（codex-implementer）→ reviewer 修正要（重複・公開面・private import 等）→ 修正
- task_03 状態機械と振り分け・開始の条件（codex-implementer）→ reviewer 採用 + 補強テスト
- task_04 infrastructure・枠の窓・配線（codex-delegating-implementer）→ テスト 3 件をメインが修正 → reviewer 採用 → 実機目視 OK
- task_05 ダイアログの「枠を使う」（codex-implementer）→ 既存テストの結果 dict の完全一致をメインが追従 → reviewer 採用
- task_06 編集の窓（codex-delegating-implementer）→ 構造テスト（grab_modal は dialogs 直下）で dialogs へ移動・テスト修正（メイン）→ reviewer 修正要 1 件 → 実機目視で 6 件の指摘 → 修正（vk_to_char はメイン）→ 2 回目の目視で追加の要望 4 件 → task_06b
- task_06b 暫定 40 v0.7（codex-delegating-implementer）→ reviewer 修正要（パネルの KeyPress の直結・列数が空で例外）→ 修正 → 実機で文字の見た目を調整（メイン）→ 目視 OK
- task_07 統合確認（verifier・deep-reviewer + codex-reviewer）→ 構造テスト（子のダイアログの区分）をメインが登録 → 採用分を codex-implementer で修正 → reviewer 採用
- task_08 正本反映・暫定 40 凍結・本書・refactor_check

## 統合レビュー（task_07）の低・参考の扱い

- 保留: L1（sync のたびに枠を描き直す）/ L3（細分化は OK で常に検査 → 正本 `features.md` §4.7 に明記済み）/ L5（中央のフォントを毎回作る）/ L6（キー名の解決が keymap_panel_controller にある → idea_45 と一緒に）
- 除外: L4（左上の文字の位置と余白の規則の差・実機 OK）/ L8（修飾キーの列挙が冗長）
- 残存リスク: `-topmost` の自アプリの窓（省略表示等）との重なり順は実機目視頼み / 手で書いた `grid` は初回の保存で比率が正規化された値に変わる / 拡大率の混在は検証外

## refactor_check

**推奨** → [提案書 22](../../../instructions/modified_proposal/22_refactor_screen_grid.md)（ユーザー判断待ち）。
M3・M4（keymap の `grid` をそのまま写す分岐が 3 か所に同形で増えた）・M6（`assignment.py` の振り直しの段が `AUTO_ASSIGN_ORDER` と同じ直値）。
既知: 色の重複 → idea_44 / `keymap_panel_controller.py` 641 行と枠の関数の置き場所 → task_07 L6・idea_45。M1・M2・M5 非該当。

## 完了判定前レビュー（task_08）

- deep-reviewer = 修正要: M1（再列挙が空で suppress が残る・実装）/ M2（自動割当の順・振り直し・重複の範囲が正本に無い）・L1（本書にレビュー由来の判断が無い）・L3（refactor_check の既知の根拠）・L4（採番の表記）・L5（編集の窓の前面化はモーダルの作法の例外）・L6（関数名）・L7（codebase_map の既存の行）→ **文書は反映済** / L8 保留 / L9 保留・除外
- codex-adversarial = needs-attention 2 件（裏取り済）: [high] Tab・クリックの直前の再列挙が空だと窓が無いまま suppress が続く（= deep M1）/ [medium] 自分の切替キーを予約から除くと停止・トグルの予約まで消える
- **ユーザー判断（2026-10-13）: 2 件とも実装を直す** → task_08a（再列挙が空なら状態を変える前に例外 → 既存の失敗処理で畳む / 予約 = {停止, トグル} ∪（全切替キー − 自分の元の切替キー））→ reviewer 採用。正本は変えない（記述どおりに動かす修正）
- 提案書 22 の実施 = **(a) phase 56 の末尾に task_09_refactor**（ユーザー判断）
