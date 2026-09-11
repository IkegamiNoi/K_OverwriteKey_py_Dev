# phase.md

## フェーズ名

ネストしたモーダルの grab 復元（nested_modal_grab_restore）

## フェーズの目的

モーダルダイアログの中から別のモーダルを開いて閉じたとき、**親の grab を復元して
モーダル性を最後まで保つ**。Tk は grab 保持ウィンドウの破棄で grab を解放するだけで
直前の保持者へ戻さないため、親が開いたままメインウィンドウを操作できてしまう。

**対象レイヤは presentation のみ。スキーマ変更なし。挙動変更は
「モーダルが最後までモーダルであること」の是正に限る**（機能追加ではない）。

- 起票元: [idea_10](../../backlog/idea_10_nested_modal_grab_restore.md)
  （phase 09 task_07g の敵対的レビュー High 2 から分離・2026-08-15）。
- 主入力（暫定仕様）: [12_nested_modal_grab_restore.md](../../history/12_nested_modal_grab_restore.md)
  （**v0.5**・ユーザー確定済・実装着手可。v0.5 で §3-6 を構造保証へ改訂）。
- モード: **暫定仕様先行モード**。番号対応: phase 14 / 暫定 12 / decisions 14。

## 確定（ユーザー 2026-09-10）

暫定仕様 12 §2 が正。要点のみ:

- **復元は子側で行う**（暫定仕様 §4 案 X）。ダイアログが自分の `grab_set()` の前に
  直前の保持者を記録し、破棄時に戻す。`wait_window` 側 20 箇所には触らない。
- **適用は系統 A・B の全 13 箇所**。系統 B（呼び出し側の 4 箇所）を先行し、
  系統 A（ダイアログ 9 クラス）を後続にする。
- **stdlib のダイアログ（`messagebox` / `filedialog`）は対象外**。
  「未検証・実害報告なし」として扱い、**実機目視の 1 項目**としてユーザーへ残す。
- **ダイアログ同型スケルトンの共通化は合流させない**。フェーズ末の `/refactor_check` で再判定。
- **`ActionDialog` の親付け替えは本フェーズ外**。フェーズ末に独立 idea として起票する。
- **正本へ 2 行の作法規定を追加する**（`features.md` §4.6 + `5_10_03_save_contract.md` の相互参照）。

## スコープ

### 含む

- `keyseq/presentation/modal.py`（新規）— 記録・モーダル化・復元をまとめたヘルパ。
- 系統 B の 4 箇所（`controllers/config_io/` の `child_save_dialog.py` ×2 /
  `hotkey_presets_io.py` / `io_dialogs.py`）のヘルパ適用。
- 系統 A の 9 クラス（`dialogs/` 配下）のヘルパ適用。
- 復元契約 8 条（暫定仕様 §3）の実装 — 特に **grab 取得後に初期化を残さない（§3-6・v0.5 で改訂）/
  非 LIFO 終了で grab を奪わない / コールバック例外では子を閉じない**の 3 条。
- `tests_ui/` のネスト経路 3 系統 + 契約 3 条のテスト。`_FakeSaveDialog` の拡張要否判断。
- 正本反映（`features.md` §4.6 / `data_schema/5_10_03_save_contract.md` / `codebase_map.md`）。

### 含まない（後送り）

- **grab 以外の後始末** — 親が先に閉じた後、`wait_window` から戻った後続処理が
  破棄済みウィジェットを触る問題（暫定仕様 §8）。本フェーズは grab の復元のみ保証する。
- **モーダル自体の設計変更**（モードレス化・非同期化）と UI 刷新。
- **ダイアログ同型スケルトンの共通化** — phase 11 の `/refactor_check` 候補送り。
- **stdlib ダイアログの grab** — 実機目視のみ。
- **`ActionDialog` の親付け替え** — フェーズ末に idea 起票。
- **`transient` / `grab_set` の順序統一を目的とした並べ替え** — ヘルパ適用の結果として
  揃うのは可だが、それ自体を目的にしない。

## このフェーズで読むファイル

1. `instructions/history/12_nested_modal_grab_restore.md`（主入力・**v0.5**）
2. `keyseq/presentation/dialogs/` の 9 ファイル
   （`action_dialog` / `keymap_edit_dialog` / `layout_delete_dialog` / `orphan_sweep_dialog` /
   `preset_dialog` / `preset_manager` / `quarantine_manage_dialog` / `reference_cleanup_dialog` /
   `trigger_dialog`）
3. `keyseq/presentation/controllers/config_io/child_save_dialog.py` /
   `hotkey_presets_io.py` / `io_dialogs.py`
4. `keyseq/presentation/controllers/hook_controller.py`（子側 nest 管理の先例・`:24-38`）
5. `tests_ui/test_app_ui_flows.py`（`:72`・`:1327-1338`・`:1374` = `PresetManagerDialog` の既存パターン）
6. `tests_ui/test_quarantine_manage_flow.py:286`（`grab_current()` アサートの先例）
7. `tests_ui/test_child_save_dialog.py:149-196`（`_FakeSaveDialog` スタブ）
8. `keyseq/presentation/app.py:448-460`（上書き確認で `False` を返す経路）

**読まない**: `keyseq/application/` / `keyseq/domain/` / `keyseq/infrastructure/`（本フェーズは
presentation 限定）。`instructions/history/` の凍結済み暫定仕様。

## タスク

1. **task_01**: `keyseq/presentation/modal.py` 新設 + 系統 B の 4 箇所へ適用。
   復元契約 8 条を実装し、ヘルパ単体のテストを追加する。
2. **task_02**: 系統 A の 9 クラスへ適用。`__init__` の `grab_set` / `transient` をヘルパ呼び出しへ
   置き換え、`object.__new__` 経路（`tests_ui/test_app_ui_flows.py:72`）でも例外を出さないこと。
   - **`grab_modal` は初期化の最後に呼ぶ**（§3-6。`action_dialog.py:123` は grab 取得後に
     `_sync_capture_ui()` を呼ぶため、順序の見直しが要る）。
   - **`grab_modal` は `<Destroy>` を `"+"` なしで bind する**ため、同じウィンドウへ別の
     `<Destroy>` ハンドラを足すと**復元が無言で消える**（task_01 の `reviewer` 指摘・保留扱い）。
     9 クラスへ適用する際に該当が出たら、その時点でユーザーへ報告する。
3. **task_03**: ネスト経路 3 系統のテストを `tests_ui/` へ追加
   （プリセット編集 → 追加・編集 / アクション編集 → プリセット編集 / プリセット編集 → 上書き確認）。
   `_FakeSaveDialog` の拡張要否をここで判断する。
4. **task_04**: 契約 3 条のテスト（初期化失敗 / 非 LIFO 終了 / コールバック例外）を追加。
   **§3-6 は暫定仕様 v0.5（2026-09-11 ユーザー確定）で「grab 取得後に初期化を残さない
   構造 + 静的検査」へ改訂済**（回収機構は実装しない）。あわせて系統 B の 4 箇所で
   `protocol` / `bind` の登録を `grab_modal` の前へ移す（挙動同値の行移動）。
5. **task_05**: 統合確認（`tests` / `tests_ui` 全体 + `smoke_app`）+ **二次レビュー**
   （`deep-reviewer` + `codex-reviewer`）+ **ユーザーによる実機目視**
   （暫定仕様 §7-14 の stdlib ダイアログ 4 経路 + ネスト経路 + 退行確認）。
   - **task_05b**（枝番）: 二次レビューの指摘のうちユーザーが採用した分の反映
     （docstring / `bind` を `"+"` 付きへ / テスト 3 本 / 仕様の文書整合）。**M-6 は保留**。
6. **task_06（最終・正本反映）**: 正本へ昇格（`features.md` §4.6 に小節新設 /
   `data_schema/5_10_03_save_contract.md` に相互参照 1 行 / `codebase_map.md` 更新）+
   暫定仕様 12 の凍結 + `ActionDialog` 親付け替えの idea 起票 +
   `.claude_data/state/decisions_archive/14_nested_modal_grab_restore.md` 作成 +
   `instructions/phase/current.md` の完了記載 + `instructions/backlog/INDEX.md` の
   idea_10 行を `INDEX_done.md` へ移動 + **`/refactor_check` の実行と判定結果の完了報告への記載**
   （CLAUDE.md / `.claude/rules/task_execution.md`「フェーズ完了時」）。
   `/refactor_check` ではダイアログ同型スケルトンの共通化（本フェーズで分離した項目）を
   改めて判定対象にする。

タスク定義は着手する順に `tasks/task_NN_<topic>.md` へ起票する（`/task_new`）。

## レビュー方針

共通観点は `.claude/rules/review.md`。本フェーズ固有の観点:

- **復元条件の取り違え** — 暫定仕様 §3-1（**記録した保持者**に「自分自身のとき」条件を付けない）と
  §3-7（**破棄時点の保持者**が自分か誰も居ないときだけ戻す）は別の条件である。
  片方を他方で置き換えていないか。§3-1 を誤って絞るとネスト経路 3 が復元されない。
- **復元の自動発火を過信していないか** — 破棄フックは `__init__` 途中の例外では発火しない。
  **v0.5 の §3-6 では回収を実装せず、`grab_modal` を初期化の最後の文に置く構造で担保する**。
  grab 取得後に処理が残っていないか（静的検査で固定）。
- **モーダル性を壊していないか** — コールバック例外で子を閉じてしまっていないか（§3-8）。
- **適用漏れ** — `grep "grab_set"` でヘルパ以外の直呼びが残っていないか（全 13 箇所）。
- **スコープ逸脱** — 順序統一目的の並べ替え・スケルトン共通化・親付け替えを取り込んでいないか。

エージェントの使い分けは `.claude/rules/agent_selection.md`:

- 各タスクの必須レビュー = `reviewer`
- task_05 の統合確認時 = `deep-reviewer` + `codex-reviewer`
- フェーズ完了判定前 = `deep-reviewer` + `codex-adversarial-reviewer`
- テスト実行は `verifier`（Codex は python を実行できない）
