# task_08_promote_to_spec

## 目的

phase 08 の**最終タスク（正本反映）**。暫定仕様 07（**v0.6**・ユーザー確定済）の内容を正本
`instructions/common/` へ昇格し、暫定仕様を凍結してフェーズを閉じる。

**レイヤ制約**: **文書のみ**。`keyseq` / `tests` / `tests_ui` は**一切変更しない**
（コード差分が出たらこのタスクの逸脱）。

## 対象範囲

### 1. `instructions/common/spec_detail/data_schema.md`（正本）

反映項目は暫定仕様 07 **§7「v0.6 追記・task_08 で反映する具体項目」**が正。要点:

- **§5.1**: 既存キー削除禁止に対する**明示の例外**（keymap_set の `hotkey_presets_path` は
  **生成停止＝再保存で自然に消える**。能動削除はしない）。§5.9.1 の「hook 3 キーは常に出力」と
  対比されるため、例外である旨を書かないと矛盾に見える
- **§5.4**: 「hotkey_presets は共通ファイルを共有・**上書きする**」→ **保存カスケードは書かない**へ改訂
- **§5.5**: 「keymap_set.json は trigger_set / **hotkey preset** / keymap の実体を参照する」→
  **hotkey preset を除外**
- **§5.8.8**（runtime を新規化・置換する入口）: **入口台帳**（`apply_global_defaults` を呼ぶ
  **E1〜E5 の 5 経路** / 通常読込が供給する経路 / 供給不要な再正規化）を追記
- **§5.9.2**: 「注入はすべての入口に適用する」の記述を **`apply_global_defaults` 経由**へ更新し、
  **ON→OFF だけが単独注入**である旨を明記
- **新設 §5.10「hotkey プリセットの全体ライブラリ」**（§5.9 と同じ構成で書く）:
  データモデル（config.json の `hotkey_presets_path`・既定 `user/hotkey_presets/default.json`・相対・
  **空文字/非文字列も既定へ縮退**・**アプリは書かない＝読むだけ**）/ 解決順序（`list | None` の供給規則・
  **読み出し側で正規化**）/ 編集と保存の契約（**唯一の書き手はプリセットマネージャ**・成否付き・
  失敗時は確定しない・dirty を汚さない）/ **契約上の制約**（`None` 時の経路差・破損上書き・
  旧「別ディレクトリ保存」の孤児プリセット・Export のインライン値は Import 時に置き換わる）

### 2. `instructions/common/codebase_map.md`（正本）

- hook キーの全体デフォルト注入を呼ぶのは「**4 経路**」→ **`apply_global_defaults` を呼ぶ 5 経路**へ更新
- 「hook キーの解決点は 4 つ」の記述へ `apply_global_defaults` /
  `load_global_hotkey_presets(_path)` / `save_global_hotkey_presets` を追加。
  **ON→OFF は単独注入 / 通常読込は `apply_global_defaults` を経由しない**旨を明記
- `config_io/` の分割クラス一覧へ **`HotkeyPresetsIo`** を追加し、
  **「プリセットファイルを書くのはこの 1 本のみ」**を明記
- `App.save_hotkey_presets` / `open_preset_manager` が **dirty を汚さない**こと
- 保存カスケード（`save_runtime_data`）が**プリセットを書かない**こと
- `domain/config.py` に `normalize_hotkey_presets`（純関数）が増えたこと

### 3. 暫定仕様 07 の凍結

`instructions/history/07_hotkey_presets_global.md` の冒頭 status を
**凍結済（正本へ昇格・参照専用）**へ変更し、正本の該当節（`data_schema.md` §5.10 等）への
ポインタを書く。**本文の条項は書き換えない**（経緯として保全）。

### 4. `.claude_data/state/decisions_archive/08_hotkey_presets_global.md`（新規）

`decisions.md` の phase 08 節（task_01〜task_07b）を集約して作成し、
`decisions.md` 側は**「アーカイブ索引」へ 1 行リンクを残して該当節を削除**する
（`.claude/rules/task_execution.md`「フェーズ完了時」）。

### 5. `instructions/phase/current.md`

- 「現在の参照先」から phase 08 を外し、**完了フェーズは要約を置かず**アーカイブ参照へ
- **次採番の明記**（次フェーズ = `09_<topic>` / 暫定仕様の次採番 = `08_<topic>`）
- 「保存系リデザイン」の対応表を **プリセット = phase 08〔完了〕**へ更新

### 6. `instructions/backlog/INDEX.md`

起票元 idea は無いが、**後続 [idea_08](../../backlog/idea_08_per_keymap_set_preset_ownership.md)
（keymap_set 個別プリセット）の行を「着手可」へ更新**する（本フェーズ完了が着手条件だったため）。
※ idea_08 は**完了ではない**ので `INDEX_done.md` へは移動しない。

### 7. `/refactor_check` の実行

`.claude/commands/refactor_check.md` に従い判定する（メトリクス収集は `verifier` へ委任・
判定と提案書起票はメイン）。**判定結果を完了報告に必ず含める**。

## 含まない

- **コードの変更**（`keyseq` / `tests` / `tests_ui`）。リファクタが必要と判定されても
  **本タスクでは実施しない**（提案書起票までがユーザー承認前の範囲）
- keymap_set ごとの個別プリセット（idea_08・後続フェーズ）
- 正本の**他フェーズ由来の記述**への手入れ（§5.8 / §5.9 の本題は phase β / γ の成果。
  今回触るのは上記に挙げた箇所のみ）

## 確認

- `git diff` に **`keyseq/` / `tests/` / `tests_ui/` の差分が無い**こと（文書のみ）
- 正本の**節番号・見出しを変更していない**こと（新設 §5.10 の追加のみ）
- 暫定仕様 07 が**凍結表記**になっていること
- `decisions.md` の phase 08 節が**アーカイブへ移り、索引に 1 行残っている**こと
- `current.md` に**次採番**が明記され、完了フェーズの要約が残っていないこと
- `/refactor_check` の判定結果が出ていること

## 完了条件

- 上記確認をすべて満たす。
- **フェーズ完了判定のレビュー**を実施する（`.claude/rules/agent_selection.md` のレビュー表）:
  **`deep-reviewer`（Claude 側）+ `codex-adversarial-reviewer`（Codex 側）**。
  観点 = 正本と実装の整合 / 昇格漏れ / 既存節との矛盾 / 凍結・アーカイブの手続き漏れ。
- 完了報告に **`/refactor_check` の判定結果**を含める（`instructions/phase/current.md` の規定）。

---

## 実施記録（2026-08-09）

### フェーズ完了判定レビュー

- **`codex-adversarial-reviewer` = needs-attention**（High 1 / Medium 1）
- **`deep-reviewer` = 修正要（差戻しではない）**。昇格の網羅性・手続きは充足、指摘 10 件（高 1 / 中 3 / 低 6）
- **両レビュアーが独立に同じ High を指摘**（実測で再現済み）:
  非文字列の `label` / `value` で `normalize_hotkey_presets` が `AttributeError` →
  E1（`App.__init__`）が捕捉せず**起動不能**。phase 08 以前は空データ起動へ縮退していた。
  → **ユーザー確定 = 要素単位で除去** → 正本 §5.10.2 を確定 → **task_08b で実装**

### 指摘への対応

| 指摘 | 対応 |
|---|---|
| 高: 起動不能（両レビュアー） | 正本 §5.10.2 へ規則追加 + **task_08b** で実装 |
| 中: §5.10.4 の `None` 時内訳が **E5（Import）** で不正確 | **E5 ＝インライン値**を明記（凍結済 v0.6 §3-2 と整合） |
| 中: §5.10.1「アプリは書かない」の前提 | **「手編集はアプリ終了中に」**を追記（config.json は保存で丸ごと書き直され、未知キーは起動時スナップショット依存） |
| 中: `codebase_map.md` のツリーに `hotkey_presets_io.py` が無い | 追加 |
| 低: `current.md` の対応表が「プリセット=phase 08〔次〕」のまま | 〔完了〕へ修正 |
| 低: archive の区切り重複 | 整形 |
| 低: 指摘 7〜9（`resolve_config_path` の書き方 / 「正規化はここ 1 箇所」の誤読 / 書き手側は正規化を通さない） | **保留**（誤読の余地のみで実害なし） |
| 低: 指摘 10（`features.md` へプリセットマネージャの挙動を書く） | **除外**（phase γ の前例どおり契約は `data_schema.md` 側） |

### `/refactor_check`

**不要**（M1〜M6 該当なし。詳細と候補送り 2 件は `decisions_archive/08_hotkey_presets_global.md`）。
