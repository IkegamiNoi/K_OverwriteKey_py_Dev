# task_06_spec_promotion

## 目的

phase 14 の**最終タスク（正本反映）**。暫定仕様
[12](../../../history/12_nested_modal_grab_restore.md)（v0.5）で確定した設計を**正本へ昇格**し、
暫定仕様を凍結してフェーズを閉じる。受け入れ条件 **13 / 15** を満たす。

**文書作業のみ。`keyseq/` と `tests_ui/` のコードは 1 行も変更しない**
（`.claude/rules/agent_selection.md`「フェーズ末の正本反映タスクはメインセッションが行ってよい」）。

## 対象範囲（文書のみ）

### 1. 正本への昇格

**(a) `instructions/common/spec_detail/features.md` §4.6 に小節を新設**

`#### 子ファイル保存ダイアログ` と `#### UI と同期する実行系設定` の間に
`#### モーダルダイアログの作法` を置く。**規定は 2 行程度**（暫定仕様 §6-6）。

- 「モーダルダイアログは**閉じるまでモーダルであり続ける**」
- 「**ネストして開いた子を閉じたら親のモーダル性が戻る**」

**実装詳細（ヘルパ名 `grab_modal` / `modal.py`）は書かない**（§6-6 の確定事項）。
保証の限界（stdlib ダイアログは対象外・連鎖破棄時は保証しない）は**1 行で触れる程度**に留める。

**(b) `instructions/common/spec_detail/data_schema/5_10_03_save_contract.md` へ相互参照 1 行**

プリセットの上書き確認 3 択の契約に「**この確認はプリセットマネージャの中から開く（ネスト）**」の
1 行を足し、`features.md` §4.6 のモーダル作法へ参照を張る（§6-6）。

**(c) `instructions/common/codebase_map.md` の更新**

- フォルダ構成のツリー（presentation 直下の共有モジュール群）へ **`modal.py` を追加**する。
  記載例: `modal.py  # grab_modal: モーダル化と破棄時の grab 復元（dialogs/ と controllers/config_io/ の両方から使う）`
  置き場所は `listbox_utils.py` / `reference_cleanup_text.py` と同じ presentation 直下の並び。
- 「主な責務」側にも 1 項目足す（`listbox_utils.py` の記載と同じ粒度）。
  **記録はクロージャに持ちウィジェット属性を増やさない**ことと、
  **`grab_modal` は初期化の最後の文に置く規約**（静的検査で固定）に触れる。

### 2. 暫定仕様 12 の凍結

`instructions/history/12_nested_modal_grab_restore.md` の状態行を
**凍結済**へ変更する（他の凍結済暫定仕様と同じ書式）。
**条項を後続フェーズで実装の根拠に引かない**旨を明記する。

### 3. `ActionDialog` 親付け替えの idea 起票（受け入れ条件 15）

`/idea` で起票する。内容は暫定仕様 **§6-5** が正:

- 現状 `PresetManagerDialog(self.parent, ...)` と **App** を渡している（`action_dialog.py:341`）。
- **grab の復元先は §3-1 の記録で決まり Tk の master とは独立**（v0.1 の
  「付け替えないと復元先が曖昧」は**誤りとして撤回済み**）。**残る論点は `transient` 親の z 順のみ**。
- `PresetManagerDialog` は `parent` を App として使う（`preset_manager.py:80`・`:297`・`:332`）ため、
  付け替えには**親ウィンドウと App 参照を分離する引数追加**が要り `app.py:418` にも波及する。

### 4. `.claude_data/state/decisions_archive/14_nested_modal_grab_restore.md` の作成

`decisions.md` の「2026-09-11 (phase 14 / 暫定仕様 12)」節を含む本フェーズの判断を集約し、
**`decisions.md` 本体には「アーカイブ索引」へ 1 行リンクだけ残す**
（`.claude/rules/task_execution.md`「フェーズ完了時」）。

**必ず残す判断**:

- **§3-6 を回収から構造保証へ改訂**（v0.5・ユーザー確定）。**実行時の挙動は不変**。
  静的検査が規約を固定し、**落ちたら回収機構の要否をユーザーへ諮る**。
- **`<Destroy>` は `add="+"`**（M-5）。`"+"` を外すと復元が無言で消え、**idea_16 の対策と衝突する**。
- **§3-1（誰へ戻すか）と §3-7（そもそも戻してよいか）は別条件**。
- **stdlib ダイアログは対象外**（B1〜B3 は実機で問題なし・**B4 は観点が成立せず未確認**）。
- **テストの罠 2 件**（テストダブルの `bind` は `add=None` が要る / 復元先が未マップだと復元がスキップされる）。
- **分離した項目**: idea_16（× 閉じで `destroy()` override が走らない）/ `ActionDialog` 親付け替え /
  スケルトン共通化 / M-6（静的検査の発見ベース化）。

### 5. `instructions/phase/current.md` の完了記載

- 「現在の参照先」を**完了フェーズのリンクのみ**へ差し替える（**要約は書かない**）。
- 「直近の一連の作業が扱っている領域」を**本フェーズの領域（モーダルの grab 復元）**へ更新し、
  **残件**（idea_16 / M-6 / スケルトン共通化 / stdlib の未検証）を数行で書く。
- 「次採番」を **phase 15** に、暫定仕様の次採番を **13** に更新する。

### 6. `instructions/backlog/INDEX.md` の idea_10 行を `INDEX_done.md` へ移動

状態を `**完了**（phase 14・2026-09-12・正本反映済 → 参照リンク）` にしてから移動する。

### 7. `/refactor_check` の実行

`.claude/commands/refactor_check.md` に従う。**メトリクス収集（手順 1〜2・M1〜M6）は `verifier` へ委任**し、
**判定（手順 3 以降）と提案書起票はメイン**が行う。

**判定対象に必ず含める 3 件**:

1. **ダイアログ同型スケルトンの共通化**（phase 11 からの候補送り・本フェーズで意図的に分離。§6-4）。
2. **M-6**（静的検査を 9 クラスのハードコード列挙から**発見ベース**へ。task_05b で**保留**と確定）。
   **発見ベースにすると「`grab_modal` の呼び出しが消えた」検出が失われる**ため、
   併用形にするかを含めて判定する。
3. **[idea_16](../../../backlog/idea_16_wm_close_skips_destroy_override.md) との合流可否**
   （× 閉じの後始末をスケルトン側で 1 度だけ書く案。**`<Destroy>` を使うなら `add="+"` が前提**）。

判定結果（不要 / 推奨 + 提案書の有無）を**完了報告に記載する**。

## 含まない

- **コードの変更**（`keyseq/` / `tests` / `tests_ui`）。**1 行も触らない**。
- **idea_16 の是正**（× 閉じでフック再開が走らない）。**別 idea として独立管理**。
- **スケルトン共通化・M-6 の実施**（`/refactor_check` は**判定と提案書起票まで**。
  実施はユーザー承認後に別フェーズ）。
- **stdlib ダイアログの grab 対応**（対象外と確定済み）。

## 確認

1. **コード無変更**: `git diff --stat keyseq/ tests/ tests_ui/` が**空**であること。
2. **退行なし**（文書のみだが念のため 1 回）: `python -m unittest discover -s tests` = 417（skip 7）/
   `python -m unittest discover -s tests_ui` = 306 / `python -m tests.smoke_app` が pass。
   python は `..\..\..\.venv\Scripts\python.exe`。**実測は `verifier` へ委任**。
3. **正本のリンク切れがないこと**: 追加した相互参照のパスが実在する
   （`features.md` §4.6 ↔ `5_10_03_save_contract.md`）。
4. **`codebase_map.md` に `modal.py` が載っている**こと（ツリーと責務の 2 箇所）。
5. **暫定仕様 12 が凍結済の書式**になっていること。
6. **`backlog/INDEX.md` に idea_10 の行が無く、`INDEX_done.md` にある**こと。
7. **`decisions.md` 本体に phase 14 の詳細が残っていない**こと（索引 1 行のみ）。
8. `/refactor_check` を実行し、判定結果を完了報告に記載したこと。

## 完了条件

- 上記「確認」1〜8 をすべて満たす。
- **`deep-reviewer` 採用**（フェーズ完了判定前のため `reviewer` ではなく `deep-reviewer`。
  `.claude/rules/agent_selection.md` のレビュー表）+ **`codex-adversarial-reviewer` の敵対的レビュー**。
  **指摘の採否はユーザー判断**。
- **実機目視は不要**（文書のみ・挙動不変。実機確認は task_05 で完了済み）。
- 本タスク完了をもって **phase 14 を完了**とする。
