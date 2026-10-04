# phase.md

## フェーズ名

呼び出しのステップ実行と呼び出し先の表示（call_step_and_view）

## フェーズの目的

出力シーケンスの呼び出しの行ごとに「一括（現行）/ ステップ」を選べるようにし、ステップでは呼び出し先の中も 1 押下ずつ進め、呼び出し先の停止の行を効かせる。
呼び出し先の中で止まっているときは、呼び出し先の写しと位置・経路を表示する枠（フル表示 = 出力シーケンスの一覧の下 / 省略表示 = トリガー一覧の下）を開く。
**domain / application / presentation の全レイヤ。JSON は呼び出しの行に `step`（任意・無ければ一括）と `config/config.json` に `call_view_heights` を足す（後方互換）。**

- 起票元: ユーザー要望（2026-10-04・「呼び出し先がどう進んでいるか分からない・停止が効かない」）。
- 主入力（暫定仕様）: [31_call_step_and_view.md](../../history/31_call_step_and_view.md)（v0.5・ユーザー確定済）
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
- task_05: フル表示の枠（出力シーケンスの一覧の下・境界線・開閉・読み取り専用の一覧と `▶`・経路の見出し）と高さの保存（`call_view_heights`）（§5.1〜§5.3・§6） — **実装完了・実機目視待ち**（2026-10-04。codex-delegating-implementer〔Luna サブエージェント使用・自己申告〕・reviewer 修正要 → 採用〔is_open の Tcl_Obj 比較・最小幅で境界線が切れる → 一覧の要求幅を最小幅の基準へ〕・メインで修正: 保存した高さが開き直しで反映されない〔paneconfigure の再配置が sash_place を戻す → update_idletasks を先に〕・テストのドラッグの update 待ち・再通知の重複を外す。tests 1191 / tests_ui 803 / smoke pass）
- task_06: 省略表示の枠（トリガー一覧の下・表示の切替で同じ文脈）（§5.1・§5.2）
- task_07: 正本反映（暫定 31 §12 の昇格・凍結）・`codebase_map.md`・`decisions_archive/45_call_step_and_view.md`・current.md の完了記載・`/refactor_check`。起票元 idea なし

## レビュー方針

- 各タスク: `reviewer`（5 観点）・既存テスト（tests / tests_ui / smoke）の通過を完了条件に含める
- 重点: 一括の呼び出しの既存の挙動が変わらないか（とくに「送った」・一時停止・捨てる契機）/ 押下の合間の状態と一時停止の受付の区別 / 停止の後に呼び出しが終わる形 /
  runner → UI の依存方向（注入のコールバック）/ フル表示の最小の高さ・横の幅の配分が変わらないか / config.json の既存キーとの揃い
- task_02・03 は実行の中核のため、両方の完了後に `deep-reviewer` + `codex-reviewer` で統合確認。完了判定前に `deep-reviewer` + `codex-adversarial-reviewer`
- 実機目視（ユーザー）: task_01（ダイアログ・表示名）・task_02/03（単発・連続実行の動き）・task_05/06（枠）
