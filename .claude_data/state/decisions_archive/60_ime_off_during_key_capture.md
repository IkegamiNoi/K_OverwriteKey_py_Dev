# decisions_archive / phase 60: キーの取得中は IME を OFF にする

対応表: phase 60 / 暫定 44（v0.4・凍結）/ decisions 60。起票元: idea_46（2026-10-16・phase 59 task_04a の実機目視から分離）。
完了 2026-10-16。presentation（取得の寿命の部品 `key_capture_ime.py`・8 入口の配線・`tk_keys.is_unresolved_capture_key`・案内の文言）+ infrastructure（`own_ime_status.py`・状態なし）。**JSON スキーマ不変**。送信側の `ime_control.py` は不変。
正本 = `key_input.md` §7.4「取得の入口」「取得中の IME」「判別できないキー」・§7.7（相互参照）/ `features.md` §4.3（参照へ）/ 地図 = `codebase_map.md`（phase 60 の節）。

## 確定した設計判断（ユーザー 2026-10-16）

| # | 判断 | 採らなかった案と理由 |
|---|---|---|
| 1 | 方式 = 開閉を記録して OFF・終了で復元 | 入力コンテキストを外す（`ImmAssociateContext`）= Tk の窓のどの HWND に効くか未確認・後から作られる子ウィジェットは外れない |
| 2 | API = 自スレッド向けの `ImmGetContext` / `ImmSetOpenStatus`（ルートの窓の HWND） | 送信用の `WM_IME_CONTROL` = 別プロセス向け・IME 窓の推定と時間制限が要る（deep-reviewer M7・probe で同じく効くことを確認） |
| 3 | 取得の寿命だけを持つ小さな部品を各入口の既存の開始・停止の関数から呼ぶ | 取得処理を丸ごと共通部品へ寄せる = 8 入口の差（開始のきっかけ・Esc の意味・KeyRelease）が大きく過剰な共通化（ユーザーの質問に対するメインの推奨） |
| 4 | `??` は全入口で記録せず取得を続ける・案内の欄がある入口（#2・#3・#4・#6）だけ「このキーは取得できません。別のキーを押してください。（Escでキャンセル）」 | 欄の新設 = 過剰。旧文言「IME が ON の場合は OFF に」= 自動で OFF になるので誤った案内（deep-reviewer M5） |
| 5 | 取得中に手で ON にされても OFF にし直さない（受容） | `??` を受けたら OFF にし直す = 変換中の文字が確定して誤った値が記録される（deep-reviewer H2） |
| 6 | 取得中のフック再開（#1・#7）はスコープ外 → idea_48 | 本フェーズで `start_hook` を変える = IME と独立した別の判断 |

## タスク中の判断

### 【起票】モード = **暫定仕様先行**（入口が 8 ファイルに跨る）
- 暫定 44: v0.1 → deep-reviewer 修正要（H1 対象の HWND が曖昧 / H2 再 OFF で誤記録 / H3 重なりの穴 / M1〜M7）→ **H1 は probe で解消**（Tk の全 HWND が同じ入力コンテキスト〔HIMC〕と既定の IME 窓を共有・自プロセスでは外枠への問い合わせも正しく読める・Tcl/Tk 8.6.15）→ v0.2 →
  Codex 敵対的 needs-attention（高: 取得中にフックを再開できる〔`start_hook` は停止の数を見ない・メイン実測で確認〕/ 高: 再開始の OFF で誤記録 / 中: 印の消去条件）→ v0.3（再開始は何もしない・数が残る終了は印に触らない・フック再開は受容 + idea_48）→ ユーザー確定 v0.4
### 【task_01】HWND は暫定 44 §4.1 の「取得を受ける窓」ではなく、タスク定義でルートの窓の `winfo_id()` に（破棄途中・破棄後の窓の HWND を使わないため。入力コンテキストは共有なので結果は同じ）/ 非 Windows のテストが setUp の `_get_api` の差し替えを受けて失敗 → setUp のないクラスへ（メイン）/ reviewer の任意指摘でルートの hwnd を使うテストを追加（メイン）
### 【task_02】Escape の `event_generate` はフォーカスが無いと届かない → 既存の作法 `acquire_focus` を前置（メイン）
### 【task_03】画面の枠の編集の窓の Esc は段階式（選択の解除が先）→ テストは `on_escape` を閉じるまで繰り返す（メイン）/ #8 の開始を `__init__` の `grab_modal` の直前へ（初期化の途中の例外で OFF が残る経路を狭める・reviewer の任意指摘）/ ユーザーの実機目視 OK（8 入口・終了で戻る・#7 の再クリック・取得中に手で ON）
### 【task_04 統合確認】tests 1686 / tests_ui 1105 / smoke OK・codex-reviewer 指摘なし・deep-reviewer 完了可 → ユーザー確定（2026-10-16）
- M1（採用・task_05 で反映）: 正本の旧文言（`features.md:481`・`key_input.md:89`）・§4.3 の受容・#1 の挙動の変更・`codebase_map.md` の箇所。全入口の扱いは `key_input.md` §7.4 を主に置く
- L1（記録）: `unbind("<Destroy>", funcid)` が自分の結び付けだけを外すのは Python 3.13 以降（現環境 3.14.6）。それより前はフック再開（`hook_controller.py:64`）・grab 復元（`modal.py:187`）の `<Destroy>` を巻き込む
- 除外: L2（#1 の停止キー ↔ トグルキーの切替で IME が一瞬 ON に戻る・表示のちらつきだけ）/ L3（#7 で元キーの名前が空になる端のケース・起きない見込み）
- 保留: L4（入力コンテキストが NULL・`ImmSetOpenStatus` が 0 のときはログが出ない）/ L5（入口の重なりの UI テスト・実機目視なし〔単体テストのみ〕）/ L6（既存の tests_ui は本物の既定インスタンスを共有〔漏れはない〕・`window: object` の型注釈）

### 【task_05 /refactor_check】不要（2026-10-16）
- 範囲 `git diff c99719d..HEAD -- keyseq/`（12 ファイル・+261 / -15）。M1（最大 `keyboard_window.py` 533 行 +10）・M2・M4・M5（0 件）・M6（`"??"` の直値は `tk_keys.UNRESOLVED_KEY_NAME` の定義のみ）は非該当
- M3 の候補（`begin_key_capture` 8 か所・`end_key_capture` 7 か所・`is_unresolved_capture_key` の分岐 8 か所）は、設計判断 #3 の「共通部品を各入口の既存の開始・停止から 1 行で呼ぶ」呼び出し口で、処理は部品と判定関数の 1 か所に集約済み（片方を直してももう片方を直す必要がない）→ 非該当
- phase 59 の境界の候補（current.md の別タスク化候補）を再評価: 取得の入口は共通化しない（#3）・`??` は判定関数に集約済み → 候補の記述を更新（idea_46 への言及を削除）

### 【task_05 完了判定前レビュー】Codex 敵対的 approve（指摘なし）/ deep-reviewer 修正して採用（2026-10-16）
- 反映: 中-1（current.md の別タスク化候補に idea_46 への古い記述）/ 低-1（「アプリの終了では戻さない」→「特別な復元はしない・窓の破棄で戻ることはある」）/ 低-2（HWND をルートにした理由を記録）/ 低-3（presentation → infrastructure の直接 import の根拠を codebase_map へ）
- 保留: 低-4（Python 3.13 以降の前提は地図のみ・L1 で記録済み）/ 除外: 低-5（codebase_map の節の並び・既存の書き方）・低-6（#8 の Spinbox の受容は正本に入れない・実害なし）
