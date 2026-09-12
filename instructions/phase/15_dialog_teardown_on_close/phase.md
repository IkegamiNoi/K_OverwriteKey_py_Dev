# phase.md

## フェーズ名

ダイアログ後始末の確実な実行（dialog_teardown_on_close）

## フェーズの目的

ダイアログを **× で閉じても後始末が走る**ようにし、**フックの停止カウンタがずれない**ようにする。
現状は Python の `destroy()` override が × 閉じで呼ばれず、`resume_hook_after_dialog()` が飛ぶため、
**以後ダイアログを開いてもフックが止まらず、編集中のキー入力が誤爆し得る**。

**対象レイヤは presentation のみ。スキーマ変更なし。挙動変更は
「後始末が閉じ方によらず走ること」と「アプリ終了中にフックを再開しないこと」の 2 点に限る**。

**正本違反の是正であり仕様追加ではない** — `spec_detail/key_input.md` §7.2 は
「UI 編集中（キャプチャ・ダイアログ等）はフックを停止する」と既に規定しており、
現状はこれを満たしていない。

- 起票元: [idea_16](../../backlog/idea_16_wm_close_skips_destroy_override.md)
  （phase 14 task_04 の起票前調査で実測により発見・2026-09-11）。
- 主入力（暫定仕様）: [13_dialog_teardown_on_close.md](../../history/13_dialog_teardown_on_close.md)
  （**v0.4・ユーザー確定済・実装着手可**）。
- モード: **暫定仕様先行モード**。番号対応: phase 15 / 暫定 13 / decisions 15。

## 確定（ユーザー 2026-09-12）

暫定仕様 13 §2 が正。要点のみ:

- **後始末を `destroy()` override から破棄イベントへ寄せる**（案 B）。
  `protocol` を 5 クラスへ足すだけの案 A は採らない（暗黙の規約が残り、終了経路も塞げない）。
- **登録は `HookController` へ寄せる** — `suspend_hook_for_dialog(window)` が
  **停止と解除予約を原子的に行う**。汎用ヘルパは作らない。
  **`window` 省略時は現行と完全に同じ挙動**（try/finally 形の 5 系統は無変更）。
- **解除は `after(0)` で遅延する** — 破棄イベントの中で同期実行しない
  （フック開始が**同期でメッセージボックスを開き得る**ため / phase 14 の grab 復元と競合させない）。
- **終了ガードを `HookController` に持たせる** — アプリ終了が確定したら
  **どの解除経路からもフックを再開しない**。
- **空になる `destroy()` override は削除する**（4 クラス）。
- **意味が空になる既存テストは書き換える**（`tests_ui/test_app_ui_flows.py:1325-1341`）。
- **ダイアログ同型スケルトンの共通化とは合流しない**。

## スコープ

### 含む

- `keyseq/presentation/controllers/hook_controller.py` — `suspend_hook_for_dialog` の
  `window` 引数対応 + 解除予約（`<Destroy>` 結線 + `after(0)` 遅延）+ **終了ガード**。
- `keyseq/presentation/app.py` — `on_close` で終了ガードを立てる。
- `keyseq/presentation/dialogs/` の **8 クラス** — `suspend_hook_for_dialog(self)` への置換 +
  `destroy()` override から `resume_hook_after_dialog()` の削除（+ 空になる 4 件の override 削除）。
- 受け入れ条件のテスト（× 閉じ / 二重実行なし / 子ウィジェット破棄 / 終了時 /
  **phase 14 の grab 復元の非退行** / 静的検査）。
- 既存テストの棚卸しと書き換え（暫定仕様 §5・§2）。
- 正本反映（`key_input.md` §7.2 / `features.md` §4.6 / `codebase_map.md`）。

### 含まない（後送り）

- **非ダイアログ経路 5 系統の結線方式の変更**（try/finally 形は**形を変えない**。
  ただし**終了ガードはこれらにも効く**）。
- **`key_capture.py` / `keyboard_window.py` の編集モード** — 同じカウンタを触るが
  **ダイアログの閉じ方の問題ではない**（必要なら別 idea）。
- **ダイアログ同型スケルトンの共通化** — `current.md` の候補送りのまま。
- **静的検査の発見ベース化**（phase 14 の `deep-reviewer` M-6・保留中）。
- **[idea_17](../../backlog/idea_17_action_dialog_preset_manager_parent.md)**（`ActionDialog` の親付け替え）。
- **`_stop_capture` / `_stop_recording` の設計見直し**（T2 のまま据え置く。実害なし）。

## このフェーズで読むファイル

1. `instructions/history/13_dialog_teardown_on_close.md`（主入力・v0.4）
2. `keyseq/presentation/controllers/hook_controller.py`（`:24-42` の suspend / resume・`:74-105` の start_hook）
3. `keyseq/presentation/app.py`（`:527-539` の `on_close`）
4. `keyseq/presentation/dialogs/` の 8 ファイル（`preset_dialog.py` は対象外）
5. `keyseq/presentation/modal.py`（`<Destroy>` の `"+"` 結線・phase 14 の成果）
6. `tests_ui/test_nested_modal_grab.py`（静的検査と `<Destroy>` 系テストの先例。
   **`:300-303` が try/finally 形を要求している**点に注意）
7. `tests_ui/test_app_ui_flows.py:1325-1341`（書き換え対象）/
   `tests_ui/test_quarantine_manage_flow.py:295-330` / `tests_ui/test_orphan_sweep_flow.py:514-523`

**読まない**: `keyseq/application/` / `keyseq/domain/` / `keyseq/infrastructure/`。
`instructions/history/` の凍結済み暫定仕様。

## タスク

1. **task_01**: `HookController` の `suspend_hook_for_dialog(window)` 対応 + `after(0)` 遅延解除 +
   **終了ガード** + `app.on_close` からガードを立てる。ヘルパ単体のテストを追加する。
   **`dialogs/` はまだ触らない**（`window` 省略時の挙動が現行と同じであることを先に固める）。
2. **task_02**: `dialogs/` の 8 クラスへ適用。`suspend_hook_for_dialog(self)` への置換 +
   `destroy()` override から resume を削除 + **空になる 4 件の override を削除**。
   **`grab_modal` は `__init__` の最後の文のまま**（phase 14 の静的検査が固定）。
   **呼び出し形の変更でアサーションが直接壊れる既存テストの最小修正も本タスクに含む**
   （各タスクを green で完結させるため。観測点の移設を伴う書き換えは task_03）。
3. **task_03**: 受け入れ条件のテストを追加（× 閉じ / 二重実行なし / 子ウィジェット破棄 /
   **アプリ終了時に `start_hook()` が走らない**〔ダイアログ経路と try/finally 経路の両方〕/
   **phase 14 の非退行** / 静的検査〔**対象を `dialogs/` の 8 クラスに限定**〕）+
   既存テストの書き換え（**task_02 で直した分を除く**。`test_app_ui_flows.py:1325-1341` の
   観測点移設が主）。
4. **task_04**: 統合確認（`tests` / `tests_ui` 全体 + `smoke_app`）+ **二次レビュー**
   （`deep-reviewer` + `codex-reviewer`）+ **ユーザーによる実機目視**
   （フック ON の状態で × 閉じ → 次のダイアログでフックが止まるか）。
5. **task_05（最終・正本反映）**: 正本へ昇格（`key_input.md` §7.2 に 1 句 /
   `features.md` §4.6 へ後始末の作法 / `codebase_map.md` 更新）+ **暫定仕様 13 の凍結** +
   `.claude_data/state/decisions_archive/15_dialog_teardown_on_close.md` 作成 +
   `instructions/phase/current.md` の完了記載 + `backlog/INDEX.md` の idea_16 行を
   `INDEX_done.md` へ移動 + **`/refactor_check` の実行と判定結果の完了報告への記載**。

タスク定義は着手する順に `tasks/task_NN_<topic>.md` へ起票する（`/task_new`）。

## レビュー方針

共通観点は `.claude/rules/review.md`。本フェーズ固有の観点:

- **二重実行** — `destroy()` override と破棄イベントの両方で解除が走っていないか。
  **ちょうど 1 回**であること。
- **`event.widget` 判定** — 子ウィジェットの破棄で解除が走っていないか
  （`<Destroy>` は子の破棄でも発火する）。
- **phase 14 との干渉** — `grab_modal` の `"+"` 結線を潰していないか。
  **grab 復元が退行していないか**。`grab_modal` が `__init__` の最後の文のままか。
- **終了ガードの網羅** — **ダイアログ経路だけでなく try/finally 経路でも**
  終了時に `start_hook()` が走らないこと。
- **`window` 省略時の非変更** — 既存の try/finally 形 5 系統の挙動が変わっていないか。
- **静的検査の対象限定** — `controllers/` の try/finally 形を巻き込んでいないか
  （phase 14 の既存静的検査と衝突する）。
- **スコープ逸脱** — スケルトン共通化・`key_capture` / `keyboard_window`・親付け替えを
  取り込んでいないか。

エージェントの使い分けは `.claude/rules/agent_selection.md`:

- 各タスクの必須レビュー = `reviewer`
- task_04 の統合確認時 = `deep-reviewer` + `codex-reviewer`
- フェーズ完了判定前 = `deep-reviewer` + `codex-adversarial-reviewer`
- テスト実行は `verifier`（Codex は python を実行できない）
