# phase.md

## フェーズ名

呼び出しのステップ実行と呼び出し先の表示（call_step_and_view）

## フェーズの目的

出力シーケンスの呼び出しの行ごとに「一括（現行）/ ステップ」を選べるようにし、ステップでは呼び出し先の中も 1 押下ずつ進め、呼び出し先の停止の行を効かせる。
呼び出し先の中で止まっているときは、呼び出し先の写しと位置・経路を表示する枠（フル表示 = 出力シーケンスの一覧の下 / 省略表示 = トリガー一覧の下）を開く。
**domain / application / presentation の全レイヤ。JSON は呼び出しの行に `step`（任意・無ければ一括）と `config/config.json` に `call_view_heights` を足す（後方互換）。**

- 起票元: ユーザー要望（2026-10-04・「呼び出し先がどう進んでいるか分からない・停止が効かない」）。
- 主入力（暫定仕様）: [31_call_step_and_view.md](../../history/31_call_step_and_view.md)（v0.6・ユーザー確定済 2026-10-05。§4.5 の参照による連動が §4.2〜§4.4 の文脈の記述に優先）
- モード: **暫定仕様先行モード**。番号対応: phase 45 / 暫定 31 / decisions 45。

## 確定（ユーザー 2026-10-04）

暫定 31 §2 のとおり。要点: 呼び出しの行のチェックボックスで一括 / ステップ（既定は一括）・ステップの単発は 1 押下 = 呼び出し先 1 ステップ（押下の合間 = 単発の呼び出しの一時停止）・
連続実行は呼び出し先の停止の行で一時停止（呼び出しが終わる形なら終える）・枠は止まったときだけ開き文脈が無くなれば閉じる・経路を見出しに・境界線の位置は config.json に保存（フル / 省略で別）・
ダイアログを開いたときの打ち切りは受容。

## スコープ

### 含む

- 呼び出しの行の `step`・編集ダイアログのチェックボックス・一覧の表示名 `[call step]`（暫定 31 §3）
- ステップの実行（段の印・単発・連続実行・入れ子・停止の行と文脈ごとの「送った」の印・一時停止と再開）（§4）
- 表示の要約と runner からの通知の口・カウンターの再通知（§5.3）
- フル表示 / 省略表示の枠・境界線・開閉と表示する文脈の選び方・高さの保存（§5.1・§5.2・§6）
- 正本反映（§12）

### 含まない（後送り）

- 暫定 31 §11 のとおり（経路のクリック・手動の開閉・枠からの編集・写しとの差の表示・トリガーごとの高さ・省略表示への出力シーケンス欄・横スクロール）
- ダイアログを開いたとき（フック停止）に文脈を残すこと（受容）

## このフェーズで読むファイル

1. 暫定 `instructions/history/31_call_step_and_view.md`（全文）
2. 正本 `features.md` §4.2.1・§4.2.5・§4.2.8・§4.2.9・§4.2.10・§4.6（一覧の表示形式・出力シーケンスの編集・フル表示の幅配分）/ `data_schema.md` §5.4・§5.11.6
3. `keyseq/application/call_context.py`・`keyseq/domain/call_graph.py`・`keyseq/application/sequence_steps.py`
4. `keyseq/application/sequence_runner/{sequence_runner,call_wait,call_run_to_end,input_acceptance,wait_stop}.py`
5. `keyseq/domain/config.py:140-160`・`keyseq/domain/sequence_control.py:165-190`
6. `keyseq/presentation/dialogs/action_control_fields.py`・`controllers/trigger_panel/action_edit.py:355-375`
7. `keyseq/presentation/views/full_view/sequence_box.py`・`views/compact_view/compact_view.py`・`controllers/action_list_rendering.py`
8. `keyseq/presentation/controllers/pane_layout/pane_layout_controller.py`（幅の保存の手本）・`controllers/config_io/startup_io.py`
9. `instructions/common/codebase_map.md`「出力シーケンスの制御アクション」節
10. 影響の確認: `keyseq/presentation/controllers/hook_controller.py:45-51`・`:155-163`（停止操作で文脈を捨てる・task_02・03）/ `keyseq/presentation/app.py`（起動設定の読込と配線・task_05）

## タスク

- task_01: 呼び出しの行の `step`（読込・表示名 `[call step]`・編集ダイアログのチェックボックス・複製で写す）（§3） — **完了・実機目視 OK（2026-10-04）**（codex-implementer・reviewer 採用・tests 1130 / tests_ui 792 / smoke pass）
- task_01a（2026-10-04 実機目視でのユーザー判断・暫定 31 v0.5）: ステップを標準に反転（JSON `all: true` = 一括・表示 `[call]` / `[call all]`・チェックボックス「一括で実行」） — **完了・実機目視 OK（2026-10-04）**（codex-delegating-implementer〔Luna サブエージェント 2 名使用・自己申告〕・reviewer 採用〔実行の assert の変更 0 件を機械照合〕・tests 1166 / tests_ui 794 / smoke pass）
- task_02: ステップの実行の土台と単発（段の印〔§4.1〕・1 押下 = 1 ステップ・押下の合間 = 単発の呼び出しの一時停止・待機と間隔・処理中の同じキーは無視・履歴は呼び出し全体で 1 段・単発の一時停止 → 再開で続きから〔§10-6〕）（§4.1・§4.2・§4.4） — **実装完了**（2026-10-04。codex-delegating-implementer〔Luna サブエージェント使用・自己申告〕・処理中の同じキーの無視の条件をメインで「ステップの文脈」へ訂正〔タスク定義の誤り〕・reviewer 採用・tests 1139 / tests_ui 792 / smoke pass。統合確認は task_03a・実機目視 OK〔2026-10-04〕）
- task_03: 連続実行のステップ（呼び出し先の停止の行・文脈ごとの「送った」の印・停止の後の分岐〔一時停止 / 終える〕・一括の互換・連続実行の一時停止 → 再開で続きから〔§10-6〕）（§4.3・§4.4） — **実装完了**（2026-10-04。codex-delegating-implementer〔Luna サブエージェント使用・自己申告〕・連続実行の呼び出しの開始で step を渡していなかった入口も修正・reviewer 採用・tests 1152 / tests_ui 792 / smoke pass。統合確認は task_03a・実機目視 OK〔2026-10-04〕）
- task_03a（2026-10-04 task_02・03 の統合確認〔deep-reviewer 採用 / codex-reviewer P2〕から）: 入れ子の一括の呼び出しの後のステップの区切り（P2）・単発で stopped の防御・送った印の持ち越しの修正（R1）・テスト追加 — **実装完了**（codex-implementer・reviewer 修正要 ×3 → 採用・tests 1165 / tests_ui 792 / smoke pass。実機目視 OK〔2026-10-04〕）
- task_04: 表示の要約と通知の口（runner → UI のコールバック・表示する文脈の選び方・カウンターの再通知）（§5.2・§5.3 の application 側） — **完了**（2026-10-04。codex-delegating-implementer〔Luna サブエージェント使用・自己申告〕・reviewer 修正して採用〔カウンターの再通知の漏れ → commit を包む口へ統一・runner 側を call_view_notice.py へ改名〕・tests 1184 / tests_ui 794 / smoke pass。キーマップの並べ替え〔app_state の forget / rekey〕での表示の残りは task_05 で確認）
- task_05: フル表示の枠（出力シーケンスの一覧の下・境界線・開閉・読み取り専用の一覧と `▶`・経路の見出し）と高さの保存（`call_view_heights`）（§5.1〜§5.3・§6） — **実装完了・実機目視待ち**（2026-10-04。codex-delegating-implementer〔Luna サブエージェント使用・自己申告〕・reviewer 修正要 → 採用〔is_open の Tcl_Obj 比較・最小幅で境界線が切れる → 一覧の要求幅を最小幅の基準へ〕・メインで修正: 保存した高さが開き直しで反映されない〔paneconfigure の再配置が sash_place を戻す → update_idletasks を先に〕・テストのドラッグの update 待ち・再通知の重複を外す。tests 1191 / tests_ui 803 / smoke pass。実機目視 2026-10-05: 動作 OK・改善要望 → 暫定 31 v0.6 / task_05a・task_08 系）
- task_05a（2026-10-05 task_05 の実機目視でのユーザー判断・暫定 31 v0.6）: 枠を常設の Expander に（起動時は閉・参照中で自動で開く・自動で閉じない・開閉はトリガーごと・見出しのクリックで開閉）・境界線を控えめに（§5.1・§5.2） — **実装完了・実機目視待ち**（2026-10-05。codex-implementer・reviewer 修正要〔開いたとき見出しが本体の下・最小の高さ・簡易 app の call_view〕→ 採用・メインで修正: テストが隠れた一覧を比べていた・既定の高さに閉じた見出しを足す・SequenceBox の call_view 参照を遅延。tests 1191 / tests_ui 809 / smoke pass）
- task_08（2026-10-05・§4.5.1・§4.5.5）: 参照中の印と押下の番号つきの戻す履歴・まとめて戻す・連鎖をたどる関数（application の状態層・挙動不変の土台） — **完了**（2026-10-05。codex-implementer・reviewer 採用・メインで修正: 新規テストのデータ誤り 3 点〔印の付け過ぎ・位置が範囲外・HistoryEntry の引数順〕・commit_press の冗長な return。tests 1210 / tests_ui 809 / smoke pass）
- task_09（§4.5.1〜§4.5.4）: 単発の実行を参照による連動へ（印を立てる・押下で最上段を進める・完了で呼び出し元を進める・一括の範囲・単発は写しを使わず押下ごとに組み立てて書き戻す）— **完了**（2026-10-05。codex-delegating-implementer〔Luna サブエージェント使用・自己申告〕・app.py に list_trigger_keys の 1 引数〔メイン許可〕・reviewer 修正要 ×2〔完了の判定: 位置 0 の推定 → 末尾に達した事実の記録〕→ 採用・混在テスト 2 件を書き直し〔表示の復元の確認は task_11 へ〕。tests 1237 / tests_ui 809 / smoke pass。連続実行は task_10 まで写しのまま）
- task_10（§4.5.2・§4.5.3・§4.5.6）: 連続実行（送ったを実行 1 回ごと・停止の行・一時停止中への合流・完了での位置だけの前進・写しの廃止）— **完了**（2026-10-05。codex-delegating-implementer〔Luna サブエージェント使用・自己申告〕・共通処理を linked_call.py へ・写し〔collect_call_snapshot・CallEntry・start_call〕を削除・§10-4a は §4.5.6 で置き換え・reviewer 採用 → テスト 4 件の失敗〔実装 2・テスト 2〕を直して再レビュー採用。tests 1243 / tests_ui 809 / smoke pass）
- task_11（§4.5.1・§4.5.7・§5.3）: 後始末の統合（停止操作・ダイアログ・キーマップ切替で印を残す・編集等で消す）と表示の要約の問い合わせ方式・task_05a の枠を連動の要約へ — **完了**（2026-10-05。codex-delegating-implementer〔Luna サブエージェント使用・自己申告〕・停止で未開始の続きの予約を取り消すと印が消える不具合を修正・呼び出し元のキー変更で印は移る〔メイン判断・task_07 で §4.5.1 の文言を直す〕・reviewer 採用。tests 1263 / tests_ui 810 / smoke pass）
- task_11a（2026-10-05 task_08〜11 の統合確認〔deep-reviewer 修正して採用 / codex-reviewer P1・P2〕から）: 一時停止中の単発の文脈を捨てると古い位置・印を書き戻す（H1=P1）・末尾の待機の取り消しで完了が伝わらない（M1）・待機中の呼び出し先の判定が直接の参照先だけ（M2=P2）・last_trigger の無条件更新（L3）・写しの残り（L5） — **完了**（2026-10-05。codex-implementer・reviewer 修正要 ×3〔M2 を事前の走査から「段に入る時点の判定 + 押下の巻き戻し」へ・送った後は巻き戻さず一時停止〔メイン判断〕・連続実行は文脈ごとの送った〕→ 採用。tests 1272 / tests_ui 810 / smoke pass。§4.2.10 のずれ〔1 手目が呼び出しの連続実行で開始時に単発の待機を取り消さない〕は task_11b へ持ち越し）
- task_11b（同・仕様判断待ち）: M3（連続実行中の呼び出し先の位置をユーザーが変えた場合）・M4（一時停止中の連続実行のトリガーが呼び出し先として完了）・L1（伝播で進める一時停止中の呼び出し元の待機・停止の行）・L2（まとめて戻す対象の検査）— 暫定 31 §4.5.8 でユーザー確定（M3 = 実行中は呼び出し先を外から変えない・一時停止中は可）・**完了・実機目視待ち**（2026-10-05。codex-delegating-implementer〔Luna サブエージェント 3 名・自己申告〕・§4.2.10 は開始時に単発の待機だけを選んで取り消す形へ〔task_11a の回避策を撤去〕・reviewer 修正して採用・メインで修正: 内部状態の assert を外す・未使用の prepare_target を削除・テストファイル名を内容名へ。tests 1284 / tests_ui 813 / smoke pass。要ユーザー確認: 連続実行の T が待機中の U を呼ぶときは §4.2.10 の取り消しを優先〔§4.5.2 の無視は単発の T のみ〕）
- 実施順: task_05a → task_08 → task_09 → task_10 → task_11（統合確認: deep-reviewer + codex-reviewer）→ task_06 → task_07
- task_06: 省略表示の枠（トリガー一覧の下・表示の切替で同じ文脈）（§5.1・§5.2） — **完了・実機目視待ち**（2026-10-05。codex-delegating-implementer〔Luna サブエージェント使用・自己申告〕・枠の置き場を host 2 つに一般化し開閉は共有・省略表示の既定の高さが切替途中の高さで決まる不具合を 1 回差し戻して修正・reviewer 採用。tests 1284 / tests_ui 824 / smoke pass）
- task_07: 正本反映（暫定 31 §12 の昇格・凍結）・`codebase_map.md`・`decisions_archive/45_call_step_and_view.md`・current.md の完了記載・`/refactor_check`。起票元 idea なし

## レビュー方針

- 各タスク: `reviewer`（5 観点）・既存テスト（tests / tests_ui / smoke）の通過を完了条件に含める
- 重点: 一括の呼び出しの既存の挙動が変わらないか（とくに「送った」・一時停止・捨てる契機）/ 押下の合間の状態と一時停止の受付の区別 / 停止の後に呼び出しが終わる形 /
  runner → UI の依存方向（注入のコールバック）/ フル表示の最小の高さ・横の幅の配分が変わらないか / config.json の既存キーとの揃い
- task_02・03 は実行の中核のため、両方の完了後に `deep-reviewer` + `codex-reviewer` で統合確認。完了判定前に `deep-reviewer` + `codex-adversarial-reviewer`
- 実機目視（ユーザー）: task_01（ダイアログ・表示名）・task_02/03（単発・連続実行の動き）・task_05/06（枠）
