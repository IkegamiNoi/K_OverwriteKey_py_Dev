# task_05_spec_promotion

## 目的

phase 16 の最終タスク（正本反映）。
①`codebase_map.md` の `modal.py` 節へ引数の意味を 1〜2 行追記 ②`transient_parent` の
事前条件を docstring へ明記 ③暫定仕様 14 の §1-④ の根拠を実機実測に合わせて更新し**凍結**
④フェーズ完了処理（decisions_archive / current.md / backlog INDEX / `/refactor_check`）
⑤**正本 `features.md` §4.6 へ前面維持の 2 条項を追加**（当初「改訂なし」だったが、完了判定前
レビュー指摘 1 を受け**ユーザーが 2026-09-15 に改訂を採用**。`/spec_update` で実施）。

**presentation の docstring 1〜2 行を除きコード変更なし。domain / application / infrastructure 不変・
スキーマ不変・テスト不変。**

## 対象範囲（文書 + docstring 限定）

### 1. `instructions/common/codebase_map.md`（`:253-259` の `modal.py` 節）

`grab_modal` の第 2 引数の意味を 1〜2 行追記する（task_04 指摘 5 の申し送り。
**`codebase_map.md` に引数の記載は無いため、更新先は `PresetManagerDialog` の項ではなく本節**）:

- 第 2 引数 = **前面維持の相手**（`transient`）。**ネストして開く場合は呼び出し元のダイアログを渡す**。
- **所有関係（`master`）は App のまま**で、この引数では変わらない。

### 2. docstring への事前条件の明記（task_04 指摘 3）

`transient_parent` を受ける 2 箇所に、**「生存中の呼び出し元ウィンドウを渡す」**契約を 1 行ずつ足す。
破棄済みウィジェットを渡すと `TclError` で初期化が中断し、**grab 未取得・フック停止のままの窓が残る**
（実測済・到達可能性は現状ゼロのため**ガードは足さない**）。

- `keyseq/presentation/dialogs/preset_manager.py` — `PresetManagerDialog` の docstring
- `keyseq/presentation/controllers/config_io/hotkey_presets_io.py` — `confirm_overwrite` の docstring

**振る舞いの変更・引数の追加削除・既定値の変更は行わない。**

### 3. 暫定仕様 14 の更新と凍結

- **§1-④ の根拠 1「UI からは到達しない」は現状維持**（task_04 指摘 1 の「修正して採用」は
  **取り下げ**）。理由: **実機目視（2026-09-15）で、上書き確認が grab を持つ間は背面の
  プリセット編集の × 自体が押せず、非 LIFO 破棄は UI から実行できないことを確認した**。
  根拠行に**この実測（日付つき）を 1 行添える**。
- **参照行の更新**: 同項の `test_nested_modal_grab.py:311` は task_03 のテスト追加でずれたため
  **`:335`（`test_non_lifo_manager_destroy_does_not_steal_confirmation_grab`）**へ直す。
- **v0.5 として凍結**。ヘッダを暫定仕様 12 と同形式にする（状態 = 凍結済 / 経緯の参照用 /
  **条項を実装の根拠に引かない** / 正本の所在 = `features.md` §4.6 + `codebase_map.md` の
  `modal.py` 節 / 昇格時の判断 = `decisions_archive/16_dialog_transient_parent.md`）。

### 4. フェーズ完了処理

- `.claude_data/state/decisions_archive/16_dialog_transient_parent.md` を作成（判断履歴の集約。
  §2 の確定 6 件 / task_04 の指摘 1〜6 の判定 / **指摘 1 の再判定（実機実測による取り下げ）** /
  実機目視 5・6 が実行不能だったこと）。`decisions.md` の「アーカイブ索引」へ 1 行追加。
- `instructions/phase/current.md` — 完了記載の更新（**次採番 = phase 17** の明記 /
  「直近の一連の作業が扱っている領域」の数行差し替え。**完了フェーズの要約は書かない**）。
- `instructions/backlog/INDEX.md` の **idea_17 行を完了状態にして `INDEX_done.md` へ移動**。
  **idea_19（Win+D 復元不能）は未着手のまま INDEX.md に残す**。
- **`/refactor_check` の実行**（メトリクス収集 M1〜M6 は `verifier` へ委任・判定はメイン）と、
  判定結果の完了報告への記載。

### 設計メモ / 制約

- 本タスクは**文書作業 + docstring**。`.claude/rules/agent_selection.md`「メインセッションが
  直接行ってよい作業」に該当するため**実装エージェントへ委任しない**。
- 実機目視 5・6 は**実行不能（= 到達不能の裏付け）**として
  [integration_result.md](../integration_result.md) §5 に記録済み。**再試行しない**。
- 6 で観測した Win+D 由来の復元不能は
  [idea_19](../../../backlog/idea_19_minimize_restore_with_child_grab.md) へ分離済み。
  **本フェーズでは扱わない**。

## 含まない

- **`features.md` §4.6 以外の正本改訂**（`data_schema.md` 等は変更しない。
  §4.6 への 2 条項追加は対象範囲 5 で実施）。
- **`transient_parent` の事前条件ガードの実装**（docstring による明記のみ。task_04 指摘 3 の判定）。
- **`PresetManagerDialog` 側の既定（`parent`）の見直し**（task_04 指摘 2 = 保留。
  **3 箇所目の呼び出しが出た時点で再検討**する）。
- **T3 の `wait_window` patch の個体化**（task_04 指摘 4 = 現状維持）。
- **idea_19 の調査・実装**（別フェーズ）/ **idea_18 の対応**（別 idea）。
- **`/refactor_check` が提案したリファクタの実施**（提案書起票まで。実施はユーザー承認後）。

## 確認

- `../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
  （docstring 変更のため実施）。
- `../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui` が **task_04 と同じ pass 数
  （324）**であること（docstring は静的検査の対象外だが、`test_nested_modal_grab.py` の
  AST 検査に影響しないことの確認）。`tests` 側は**変更が及ばないため任意**。
- 文書の相互参照が切れていないこと: 暫定仕様 14 のヘッダから
  `decisions_archive/16_dialog_transient_parent.md` / `features.md` §4.6 /
  `codebase_map.md` へのリンクが実在する。`INDEX_done.md` へ移した idea_17 行のリンク先が実在する。
- `instructions/backlog/INDEX.md` に **idea_17 の行が残っていない**こと / idea_19 が残っていること。
- `/refactor_check` を実行し、判定（要 / 不要）と根拠メトリクスを完了報告に含めること。

## 完了条件

- 上記確認 pass。
- **フェーズ完了判定前レビュー = `deep-reviewer`（Claude 側）+ `codex-adversarial-reviewer`
  （Codex 側・focus text で「暫定仕様 14 の凍結内容と正本非改訂の妥当性 / 指摘 1 の取り下げ根拠 /
  正本との整合」を指定）**。両者の指摘の採否はユーザー確認を経て決める。
- 実機目視は **task_04 で実施済**（1〜4 問題なし / 5・6 は操作自体が実行不能）。**本タスクでは行わない**。
- フェーズ完了処理 4 項目（decisions_archive / current.md / backlog 移動 / `/refactor_check`）が
  すべて済んでいること。
