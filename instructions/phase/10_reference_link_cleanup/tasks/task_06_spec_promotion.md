# task_06_spec_promotion

## 目的

phase 10（参照元の掃除）の**フェーズ最終タスク = 正本反映**。暫定仕様先行モードで進めたため、
確定設計 [暫定仕様 09](../../../history/09_reference_link_cleanup.md)（**v0.5**・§7 の昇格表）の内容を
正本 `instructions/common/spec_detail/` へ昇格し、暫定仕様を**凍結**する。
あわせて `.claude/rules/task_execution.md`「フェーズ完了時」のチェックリスト
（`decisions_archive` 作成 / `current.md` 完了更新 / 起票元 idea の `INDEX_done.md` 移動 /
`/refactor_check`）を実施する。

**レイヤ制約**: **文書のみ。production コード・テストは一切変更しない**
（`/refactor_check` は判定と提案書起票までで、リファクタの実施は含まない）。
task_05 の `deep-reviewer` 指摘のうち **H8 / H10 / H11 / H13 / H14** は本タスクで
**実装せず、`/refactor_check` の判定と併せてユーザーへ提示する**（採否はユーザー）。

## 対象範囲（文書限定・コード不変）

### 1. `instructions/common/spec_detail/data_schema.md` §5.8.1 の改訂

暫定仕様 09 §7 の 1 行目・および v0.4 追加行のとおり。既存の節番号・見出しは変更しない。

- **「（陳腐化した参照元の掃除は後続課題）」を本機能の記述へ差し替える**
  — 設定メニューからの**ユーザー操作でまとめて除去できる**こと。
- **「既存キーは削除せず追加のみ行う」に掃除による除去の例外を追記**する
  （掃除は `_parent_refs` の**値のみ**を変更し、**他のキー・子ファイル自体は変更しない**）。
- **検査範囲は「現在の構成セットが参照している子」のみ**＝**全網羅ではない**ことを
  **既知の制約**として明記する（列挙は runtime の source_path 3 種。子は config 外にも置けるため
  ディレクトリ走査でも全網羅にならない）。
- **全件除去時は `[]` を書き、キー自体は残す**（§5.1 の後方互換）。
- **保護対象**: **現在の keymap_set / trigger_set への参照は、実在しなくても除去しない**。
- **未保存（`keymap_set_path` が空）の構成セットでは、先に保存が必要**
  （保存成功時のみ掃除へ進む。理由 = 掃除後の個別保存で参照元が巻き戻るため）。
- **孤児の削除は行わない**（参照元が 0 件になることの**警告表示のみ**）。

### 2. 同 §5.8.4 の注記（必要なら）

暫定仕様 09 §7 の 2 行目。**判定表そのものは変えない**。
`None` と `[]` はいずれも「所有元不明」で**判定は不変**である旨だけを注記する。
既存記述で読み取れるなら**追記しない**（不要な改訂をしない）。

### 3. `instructions/common/spec_detail/features.md`

`#### メニュー・個別保存`（§4.6）へ、**設定メニューの「参照元を掃除…」** を 1 行追記する。
UI 仕様の詳細は書かない（正本の粒度に合わせる）。

### 4. `instructions/common/codebase_map.md`

phase 10 で追加した 4 ファイルの所在と責務を、既存の記載粒度に合わせて反映する。

- `keyseq/application/config_service/parent_refs_cleanup.py`（検査 + `prune_parent_refs`。
  **保護対象の分離** / **書き込み直前の JSON 全体読み直し**）+ `ConfigService` の**委譲 2 本**
- `keyseq/presentation/reference_cleanup_text.py`（提示テキストの純関数・**tkinter 非依存**）
- `keyseq/presentation/controllers/config_io/reference_cleanup_io.py`（フローのみ）
- `keyseq/presentation/dialogs/reference_cleanup_dialog.py` + `views/menu_bar.py` の配線

### 5. 暫定仕様 09 の凍結

`instructions/history/09_reference_link_cleanup.md` の冒頭へ**凍結マーク**を付ける
（**凍結済 = 経緯の参照用。条項を実装の根拠に引かない**旨。既存の凍結済 06 / 07 / 08 と同じ流儀）。
**本文は書き換えない**。

### 6. `.claude_data/state/decisions_archive/10_reference_link_cleanup.md` の作成

`decisions.md` の phase 10 節（`## 2026-08-16〜 (phase 10: 参照元の掃除)` 以下）を切り出す。
切り出し後、`decisions.md` 本体からは当該節を**削除**し、「アーカイブ索引」へ **1 行リンク**を残す。

### 7. `instructions/phase/current.md` の完了更新

- 「現在の参照先」を差し替え、**phase 10 の要約行は残さない**（要約は archive が正）。
- 「直前の完了フェーズ」を phase 10 に更新。
- **次採番の明記**: フェーズ = **`11_<topic>`** / 暫定仕様 = **`10_<topic>`** /
  リファクタ提案書 = `/refactor_check` の結果次第（起票したら次採番を更新）。
- 「次フェーズ候補」の **idea_07 の行を完了へ**、**idea_12**（全走査 + 孤児候補・
  **前提 = phase 10 完了 → 充足**）を候補として明示する。

### 8. `instructions/backlog/INDEX.md` → `INDEX_done.md`

**idea_07** の行を完了 / クローズ状態へ更新し、`INDEX_done.md` へ移動する。

### 9. `/refactor_check`

`.claude/commands/refactor_check.md` に従う。**メトリクス収集（手順 1〜2・M1〜M6）は `verifier` へ委任**し、
**判定（手順 3 以降）と提案書起票はメイン**が行う。

- **注目点**: `keyseq/application/config_service/__init__.py` が **767 行**（phase 09 の 737 → **+30**）。
  **phase 09 から M1 該当で分割保留中**（テストが
  `patch("keyseq.application.config_service.os.path", ntpath)` で名前空間を差し替えるため
  **`ConfigService` 本体とパス基盤メソッドを動かせない**制約がある）。
- 判定結果は**完了報告に含める**。提案書を起票する場合は `instructions/modified_proposal/08_<topic>.md`
  （**次採番 = 08**）。**実施はユーザー承認後**（本タスクでは行わない）。

### 設計メモ / 制約

- **正本は「実装に合わせて緩める」のではなく、ユーザー確定済の暫定仕様 09 v0.5 を転記する**
  （`.claude/rules/spec_change_workflow.md`）。暫定仕様と実装が食い違う箇所を見つけたら
  **勝手に直さずユーザーへ報告**する。
- **節番号・見出しは変更しない**（`data_schema.md` は 650 行。分割は本タスクの対象外。
  必要と判定された場合は `/spec_split` を別タスクで）。
- 文書の分量は `.claude/rules/output_style.md` に従い、**要点のみ**。既存の記載粒度に合わせる。

## 含まない

- **production コード / テストの変更**（本タスクは文書のみ）。
- **task_05 の `deep-reviewer` 指摘 H8 / H10 / H11 / H13 / H14 の実装**
  → **`/refactor_check` の判定と併せて提示するのみ**。採用する場合は
  **提案書（`modified_proposal/08_*.md`）または次フェーズへ**。
- **`config_service/__init__.py` の分割の実施** → `/refactor_check` の判定 + 提案書起票まで。
- **全走査 / 孤児候補の検出**（→ [idea_12](../../../backlog/idea_12_orphan_child_file_sweep.md)）。
- **ネストしたモーダルの grab 復元**（→ [idea_10](../../../backlog/idea_10_nested_modal_grab_restore.md)）。
- **`data_schema.md` の INDEX 分割**（必要と判定されたら別タスクで `/spec_split`）。

## 確認

- `instructions/history/09_reference_link_cleanup.md` **§7 の昇格表 6 行**のそれぞれについて、
  正本側の反映箇所を**行番号付きで示せる**こと（未反映の行を残さない）。
- `grep -n "掃除は後続課題" instructions/common/spec_detail/data_schema.md` が**ヒット 0**。
- `grep -rn "09_reference_link_cleanup" instructions/ .claude_data/` の各ヒットが、
  **凍結済み前提の参照**（経緯の参照用）になっていること。
- `.claude_data/state/decisions.md` に phase 10 節が**残っていない**こと（アーカイブ索引の 1 行のみ）。
- `instructions/backlog/INDEX.md` に **idea_07 の行が無く**、`INDEX_done.md` に**ある**こと。
- 文書のみの変更であることを `git diff --stat` で確認（**`keyseq/` と `tests*/` に差分が無い**）。
- 回帰がないことの確認（**文書変更のみのため軽量**・`verifier` に委任）:
  - `../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
  - `../../../.venv/Scripts/python.exe -m unittest discover -s tests` が **pass 267**
  - `../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui` が **pass 238**（ハングなし）
  - `../../../.venv/Scripts/python.exe -m tests.smoke_app` が pass
  - worktree ルートへ **`user/` が生成されていない**こと
- `/refactor_check` を実施し、**判定結果（要 / 不要と根拠 M1〜M6）を完了報告へ記載**した。

## 完了条件

- 上記「確認」がすべて pass。
- **フェーズ完了判定のレビューを 2 本立てで実施**し（`.claude/rules/agent_selection.md`
  「フェーズ完了判定前」= **`deep-reviewer`** + **`codex-adversarial-reviewer`**・**省略しない**）、
  **指摘の採否がユーザー判断で決着**していること。是正した場合は再確認を通す。
- `.claude/rules/task_execution.md`「フェーズ完了時」の項目
  （昇格 + 凍結 / `decisions_archive/10_reference_link_cleanup.md` / `current.md` 完了更新 /
  idea_07 の `INDEX_done.md` 移動 / `/refactor_check`）が**すべて実施済**。
- **実機目視は本タスクでは行わない**（task_05 で **14 / 14 OK** 完了済）。
