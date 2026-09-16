# phase.md

## フェーズ名

最小化中の grab 預かり（minimize_grab_custody）

## フェーズの目的

**ダイアログを開いたままアプリを最小化すると二度と復元できない**欠陥を是正する。
シェルの復元要求が**非表示になった grab 保持者へ向かう**ため、App には `<Map>` が届かず
誰も復元できない（実測で確定・暫定仕様 15 §1）。**最小化の間だけ grab を預かる**ことで解決する。

**対象レイヤは presentation のみ。スキーマ変更なし。正本は `features.md` §4.6 のみ改訂**
（既存条項 `:92` の限定 + 最小化の条項追加）。

- 起票元: [idea_19](../../backlog/idea_19_minimize_restore_with_child_grab.md)
  （phase 16 task_04 の実機目視 §5-6 で観測。**phase 16 由来ではないことを実機で確認済**）。
- 主入力（暫定仕様）: [15_minimize_grab_custody.md](../../history/15_minimize_grab_custody.md)
  （**v0.4・ユーザー確定済・実装着手可**）。
- モード: **暫定仕様先行モード**。番号対応: phase 17 / 暫定 15 / decisions 17。
- 根拠の再現手段: `diagnostics/`（本フォルダ・`README.md` 参照。**production コードではない**）。

## 確定（ユーザー 2026-09-16）

暫定仕様 15 §2 が正。要点のみ:

- **最小化の間だけ grab を預かる** — App の `<Unmap>` で解除し `<Map>` で張り直す。
  **復元は WM に任せ、`deiconify()` / `lift()` / `focus_force()` を呼ばない**（触ると中間窓が消える）。
- **預かるのは「既に非表示になった保持者」だけ** — `transient` を持たない窓や
  **呼び出し元を先に破棄された子**は最小化で隠れず、症状も起きない（実測）。
- **保持者が最小化中に破棄されていたら、生存かつ表示中の最内モーダルへ張り直す**。
  このため **`modal.py` にアクティブなモーダルの台帳を足すことを許す**（phase 14 の資産に手を入れる）。
- **預かり中に新しいモーダルが開いたら、その「直前の保持者」を預かり中の窓にする**。
- **stdlib ダイアログ（`messagebox` / `filedialog`）は対象外**。`grab_current()` が解決不能なときは
  **預からない・再 grab しない**（あちらの grab を奪わない）。この経路の症状は**残ることを受容**。
- 置き場所は **`presentation/modal.py` の `install_minimize_grab_custody(app)`**（型は `tk.Misc`）。

## スコープ

### 含む

- `keyseq/presentation/modal.py` — 預かり機構（`<Unmap>` / `<Map>` の結線）+ **アクティブな
  モーダルの台帳** + `grab_modal` が預かり状態を見る結線。
- `keyseq/presentation/app.py` — 初期化で `install_minimize_grab_custody(self)` を 1 度だけ呼ぶ。
- `tests_ui/` — 受け入れテスト（新規 1 モジュールの見込み）+ 変異検査。
- 正本反映: `features.md` §4.6（`:92` の限定 + 条項追加）/ `codebase_map.md` の `modal.py` 節。

### 含まない（後送り）

- **stdlib ダイアログが grab 中の最小化**（対象外と確定。症状は残る）。
- **`grab_modal` の既存の復元規則（phase 14）そのものの再設計** — 台帳の追加と
  「預かり中は `previous` を預かり窓にする」以外は触らない。
- **phase 16 の前面維持（`transient`）の設計**（確定済・触らない）。
- **フック制御（phase 15）の変更** / `key_input.md` の改訂。
- [idea_18](../../backlog/idea_18_escape_delivery_flaky_test.md)（テストの flaky）。
- 窓構成の変更（ダイアログをタスクバーに載せる等）。

## このフェーズで読むファイル

1. `instructions/history/15_minimize_grab_custody.md`（主入力・v0.4）
2. `keyseq/presentation/modal.py`（全体。**変更対象**）
3. `keyseq/presentation/app.py`（`:54-` の `__init__` と `:193` の `protocol`。結線を足す位置）
4. `instructions/common/spec_detail/features.md` の §4.6 内「モーダルダイアログの作法」
   （`:90-108`。**正本反映タスクで改訂**）
5. `tests_ui/test_nested_modal_grab.py`（`:26-42` の共有 App と例外監視 / `:260-` の静的検査 /
   `:335` の非 LIFO。**既存アサーションを弱めない**ことの確認用）
6. `instructions/common/codebase_map.md` の `presentation/modal.py` 節（`:253-262`）

**読まない**: `keyseq/application/` / `keyseq/domain/` / `keyseq/infrastructure/` /
`instructions/history/` の凍結済み暫定仕様（04〜14）。

## タスク

1. **task_01**: `modal.py` に**アクティブなモーダルの台帳**を足す（`grab_modal` で追加・
   `<Destroy>` で除去）。**この時点で挙動は変えない**（台帳は誰も読まない）+ 台帳の一貫性テスト。
2. **task_02**: 預かり機構 `install_minimize_grab_custody(app)` の実装（`<Unmap>` / `<Map>` の結線・
   ガード 4 種〔App 限定 / 非表示の保持者のみ / 別窓が grab 中なら上書きしない / 解決不能なら触らない〕）
   + `app.py` からの呼び出し + **預かり中の `grab_modal` が `previous` を預かり窓にする**結線。
2b. **task_02b**（枝番・v0.5 追加）: 暫定仕様 §3-2(8) の**預かりへの差し戻し**
   （最小化中フラグ + `restore_grab` の 1 分岐）。task_03 の A9 を pass にする。
2c. **task_02c**（枝番・v0.6 追加）: §3-2(8) を「`previous` が破棄済みでも差し戻す」へ拡張
   （task_04 二次レビュー H-1）+ `<Unmap>` ガードのテスト追加（M-3）+ `_app_minimized` の
   テスト初期化（M-4）。
3. **task_03**: 受け入れ条件のテスト（暫定仕様 §6 の 1〜12 のうち自動化可能なもの）+ **変異検査**。
4. **task_04**: 統合確認（`tests` / `tests_ui` 全体 + `smoke_app`）+ **二次レビュー**
   （`deep-reviewer` + `codex-reviewer`）+ **ユーザーによる実機目視**
   （①ダイアログを開いたまま Win+D → 復元できる ②復元後もモーダル性が残る
   ③中間ダイアログも表示されている ④3 段ネストでも同じ ⑤通常の最小化ボタンでも同じ）。
5. **task_05（最終・正本反映）**: `features.md` §4.6 の**改訂**（`:92` の限定 + 最小化の条項追加）+
   `codebase_map.md` の `modal.py` 節 + **暫定仕様 15 の凍結** +
   `.claude_data/state/decisions_archive/17_minimize_grab_custody.md` 作成 +
   `instructions/phase/current.md` の完了記載 + `backlog/INDEX.md` の idea_19 行を
   `INDEX_done.md` へ移動 + **`/refactor_check` の実行と判定結果の完了報告への記載**。

タスク定義は着手する順に `tasks/task_NN_<topic>.md` へ起票する（`/task_new`）。

## レビュー方針

共通観点は `.claude/rules/review.md`。本フェーズ固有の観点:

- **ガードの欠落** — 4 種のガード（App 限定 / 非表示の保持者のみ / 別窓が grab 中なら上書きしない /
  解決不能なら触らない）がすべて実装され、テストで固定されているか。
  **1 つ欠けると「見えない窓が入力を握る」「表示中のモーダルから grab を奪う」**に直結する。
- **phase 14 の資産への影響** — `grab_modal` の既存の復元規則（クロージャ記録・`<Destroy>`・
  `add="+"` 結線・初期化の最後の文）を壊していないか。**台帳のリークやゴースト**
  （破棄済みの窓が残る）が起きないか。
- **復元時に窓を触っていないか** — `deiconify()` / `lift()` / `focus_force()` を呼んでいないこと
  （実測で中間窓が消えた。テストで呼び出し 0 回を固定する）。
- **テストハーネス** — `tests_ui` は `setUpClass` で App を共有するため、**iconify したまま
  tearDown すると後続モジュールへ iconic 状態が漏れる**。cleanup で `deiconify()` して戻すこと。
- **スコープ逸脱** — stdlib ダイアログ対応・窓構成の変更・phase 15 / 16 の設計変更を取り込んでいないか。

エージェントの使い分けは `.claude/rules/agent_selection.md`:

- 各タスクの必須レビュー = `reviewer`
- task_04 の統合確認時 = `deep-reviewer` + `codex-reviewer`
- フェーズ完了判定前 = `deep-reviewer` + `codex-adversarial-reviewer`
- テスト実行は `verifier`（Codex は python を実行できない）
