# phase.md

## フェーズ名

省略表示の出力シーケンス欄（compact_sequence_view）

## フェーズの目的

省略表示のトリガー一覧と呼び出し先の枠の間に、Expander で開閉でき境界をドラッグできる出力シーケンス欄（見る + 次に実行の変更）を足す。
あわせて省略表示のウィンドウの幅・高さの記録・最小の高さ・ステータスの行数の固定を加える。
**presentation 限定・domain / application 不変・keymap_set の JSON スキーマ不変。`config/config.json` にキー 2 つ追加（`compact_sequence_view`・`compact_window_size`・後方互換）。**

- 起票元: ユーザー要望（2026-10-06・「省略表示にシーケンスが呼び出し先のみで、通常シーケンスがない」+ 2026-10-06「省略表示の画面サイズを記録」「縦を短くしたときにステータスが消えないよう最低サイズ」）。
- 主入力（暫定仕様）: [33_compact_sequence_view.md](../../history/33_compact_sequence_view.md)（v0.6・ユーザー確定済 2026-10-07）
- モード: **暫定仕様先行モード**。番号対応: phase 48 / 暫定 33 / decisions 48。

## 確定（ユーザー 2026-10-06〜07）

暫定 33 §2 の 1〜11 が正（本書に再掲しない）。要点: 操作 = 見る + 次に実行の変更（選択の帯・キー操作はフル表示と同じ）/ 開閉は全体で 1 つ・保存 /
並び = トリガー一覧・シーケンス欄・呼び出し先 / 下の欄の最小を優先・見出しは残す / 押している間に対象が変わったら取り消す /
省略表示の幅・高さを記録 / 最小の高さ（ステータス類・トリガー一覧 3 行・見出し）/ 省略表示中のステータス欄 2 行・ステータスバー 1 行。

## スコープ

### 含む

- 暫定 33 §3〜§8・§7.2・§7.3 の実装とテスト
- 既存テストの追随（`tests_ui/test_call_view_compact.py` ほか。暫定 33 §10-10）
- 正本反映（暫定 33 §12）

### 含まない（後送り）

- 暫定 33 §11 のとおり（省略表示の欄からの編集・幅 270 の変更・幅の最小・フル表示の高さの保存・フル表示のキー操作の拒否の抜け 等）

## このフェーズで読むファイル

1. `instructions/history/33_compact_sequence_view.md`（全体）
2. `keyseq/presentation/views/compact_view/`（`compact_view.py`・`trigger_box.py`）・`views/full_view/call_view_frame.py`
3. `keyseq/presentation/controllers/call_view_controller.py`・`presentation/call_view_heights.py`
4. `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py:82-110, 264-330, 583-626`・`trigger_panel/action_edit.py:330-347`
5. `keyseq/presentation/app.py:398-455`・`controllers/pane_layout/pane_layout_controller.py:135-260`・`controllers/hook_controller.py:200-210`・`views/status_bar.py`
6. `keyseq/presentation/controllers/config_io/startup_io.py`・`presentation/startup_settings.py`
7. テスト: `tests_ui/test_call_view_compact.py`・`test_call_view_frame.py`・`test_sequence_list_operations.py`・`test_action_list_rendering.py`

## タスク

- task_01: 次に実行の変更を行番号の共有処理へ抜き出す（有効か / 呼び出し先の実行中の拒否 / 周回のリセット / 描き直し）。フル表示の経路は挙動不変（暫定 33 §4）。`trigger_panel_controller.py` は 633 行（M1 の 600 行超）のため、新しい処理は増やさず抜き出すか別モジュールへ置く（task_02 も同じ） — **完了**（2026-10-07・codex-implementer・reviewer 採用・tests 1308 / tests_ui 844 / smoke pass）
- task_02: 省略表示のシーケンス欄の部品と描画・操作（Expander の見出し・`refresh_actions` から省略表示の一覧へ描く・省略表示中に描き直す経路・クリック / キー / 選択の帯・押している間の取り消し）。開閉はメモリ上のみ（暫定 33 §3・§4・§8） — **完了**（2026-10-07・codex-delegating-implementer〔Luna サブエージェント使用〕・reviewer 採用・tests 1308 / tests_ui 851 / smoke pass。実行中は描き直しのたびにクリックが取り消される＝§2-7 どおり・task_05 の目視項目）
- task_03: 省略表示の 3 段の高さの制御（配置・ドラッグ・保存を 1 か所へ・既定 / 優先順 / 見出しを残す）と `compact_sequence_view` の保存・読込（開閉と高さ・初回は開く）・省略表示中のフォント変更でシーケンス欄の最小を測り直す（暫定 33 §2-5・§2-8・§5・§6・§7） — **完了**（2026-10-07・codex-delegating-implementer〔サブエージェント使用〕・reviewer 修正して採用〔呼ばれない委譲分岐の削除・既存テストの窓の高さに閉じた見出し 1 行分を足す追随＝仕様起因〕→ 新規テスト 2 件の確かめ方の誤り〔0 に縮んだ一覧の古い winfo_height・Tk が上の境界ごと押す順序依存〕と合わせて修正・tests 1319 / tests_ui 858 / smoke pass）
- task_04: 省略表示のウィンドウ（`compact_window_size` の保存・適用・最小の高さ・ステータス欄 2 行 / ステータスバー 1 行〔省略表示中は文言の改行を空白へ置き換える〕）（暫定 33 §2-9〜11・§7.2・§7.3） — **完了**（2026-10-07・codex-delegating-implementer〔サブエージェント使用〕・reviewer 修正して採用〔省略表示で重複通知が累積する読み手の修正〕→ 検証で pack 順によりステータス・閉じた見出しが押し出される不具合を修正〔status_bar・call_view_frame を side=bottom で先に pack・並びは不変〕・既存テスト 4 件を §2-10 に合わせて追随・tests 1323 / tests_ui 867 / smoke pass）
- task_05: 統合確認（tests / tests_ui / smoke・deep-reviewer + codex-reviewer）と**ユーザーの実機目視** — **完了**（2026-10-07・実機目視 OK〔確認 1〜7 問題なし〕。統合レビュー: deep-reviewer 修正して採用 / codex-reviewer P2 1 件〔行の下の空白のクリック → ユーザー判断で「何もしない」〕→ task_05a）
- task_05a: 統合レビューの指摘対応（押したまま外へ出たときの選択の帯・空白のクリック・改行の 1 行化の一本化・重複呼び出しの削除・テストの穴）— **完了**（2026-10-07・codex-implementer・reviewer 採用。検証で見つかった「欄の高さが Tk の都合で要求の高さへ戻る / 古い大きさで境界が押さえ込まれる」不具合をメインで修正〔高さの明示 + 境界を置く前の update_idletasks〕・reviewer 修正して採用〔テストの検査を実測へ〕・tests 1325 / tests_ui 873 ×2 / smoke pass）
- task_06: 正本反映（暫定 33 §12 の昇格・凍結）・`decisions_archive/48_compact_sequence_view.md`・current.md の完了記載・`/refactor_check`。起票元 idea なし（目視時のユーザー要望「ステータスの見切れをツールチップで」は範囲外として idea_40 へ分離・2026-10-07） — **正本反映済・完了判定前レビュー済**（2026-10-07・deep-reviewer 修正して採用〔文書の指摘 M1・L1・L3・L4・L6 は反映済〕/ codex-adversarial-reviewer needs-attention 1 件 = deep-reviewer M2。/refactor_check = 推奨〔M4・M6・提案書 20〕。ユーザー判断: M2・L2 を直す → task_06a / 提案書 20 をこのフェーズ末で実施 → task_07_refactor。凍結・decisions_archive・current.md は task_07 の後 → 実施済・**完了** 2026-10-07）
- task_06a: 完了判定前レビューの指摘対応（省略表示の欄で左右の外で離したときに確定する / グレーの行で拒否の一時メッセージが出る順序） — **完了**（2026-10-07・codex-implementer・reviewer 採用。検証で tests_ui に 1 回だけ出た失敗〔窓の大きさの 500ms の遅延保存が境界ドラッグのテストの書き込み回数に混ざる・task_04 から潜在〕をメインで修正〔該当テスト 5 か所で先に cancel_save〕。Codex が CRLF にした改行を LF へ戻した。tests 1325 / tests_ui 875 ×2 / smoke pass）
- task_07_refactor: 提案書 20（CallViewController の省略表示の分岐を置き場の配置役へ・保存の待ち時間の定数の共有） — **完了**（2026-10-07・codex-delegating-implementer〔サブエージェント不使用〕・reviewer 採用。分岐 7 → 0）

## レビュー方針

- 各タスク: `reviewer`（5 観点）・既存テスト（tests / tests_ui / smoke）の通過を完了条件に含める
- 重点: フル表示の出力シーケンス欄の操作（範囲選択・ドラッグ・キー・編集）が変わらないこと / 呼び出し先の枠の既存規則（トリガーごとの開閉・自動で開く・`call_view_heights`）を壊さないこと /
  2 つの一覧の選択の同期が干渉しないこと / テストが実 `config/` を汚さないこと / フル ⇔ 省略の切替でウィンドウの大きさ・最小サイズが正しく戻ること
- 統合確認（task_05）: `deep-reviewer` + `codex-reviewer` / 完了判定前（task_06）: `deep-reviewer` + `codex-adversarial-reviewer`
- 実機目視（ユーザー）: task_05（開閉・境界のドラッグ・再起動後の保持・クリック / ↑↓・ごく小さい窓・ステータスの行数・省略表示の大きさの記録）
