# task_08_spec_promotion

## 目的

phase 09 の確定設計（暫定仕様 08 **v0.10**）を**正本 `instructions/common/spec_detail/` へ昇格**し、
暫定仕様書を**凍結**する。併せてフェーズ完了処理（`decisions_archive` 作成 / `current.md` 更新 /
起票元 idea のクローズ / `/refactor_check`）を行う。

反映対象は暫定仕様 08 **§7 正本反映**の表が正（`data_schema.md` §5.10 / §5.10.4 / §5.5 / §5.4 /
§5.8.8 / §5.1 + `codebase_map.md`）。

**レイヤ制約**: **文書のみ**。`keyseq/` 配下のソース・`tests/` ・`tests_ui/` は**一切変更しない**
（実装は task_01〜07g で完了済・実機目視も 2026-08-16 に完了）。
正本と実装が食い違う点を見つけた場合は**独断で正本を実装に合わせて緩めず**、
`.claude/rules/spec_change_workflow.md` に従いユーザーへ報告する。

## 対象範囲（文書のみ・変更ファイル単位）

### 1. `instructions/common/spec_detail/data_schema.md`

暫定仕様 08 §7 の表のとおり改訂する（**節番号・見出しは変更しない**。既存の記述順を保つ）。

- **§5.10（プリセットライブラリ）— 改訂**: 「グローバル既定 + keymap_set 個別指定」の 2 系統へ。
  - データモデル（§3-1）: config.json の `hotkey_presets_path` 既定値 =
    **`user/hotkey_presets/global/default.json`** / keymap_set の
    `hotkey_presets_individual`（bool・既定 false）+ `hotkey_presets_path`（個別パス）を
    **payload で常に出力**・**§5.7 の表記へ正規化**。
  - **解決順序**（§3-2。個別 → 読めなければグローバル → どちらも読めなければ置き換えない）。
  - **移行規則**（§3-5。**フラグは値で判定 / フラグキーが無ければ残置 `hotkey_presets_path` も
    引き継がない**。**手動移行の 2 段**＝ファイル移動 + config.json の明示値の書き換え。
    `global/` は**予約ディレクトリ**で起動時に作成される）。
  - **保存先と書き手**（§3-3。書き手はマネージャ 1 本 / 保存先算出は application /
    **【O3】既定パスへ寄せる →【O4】`global/` 配下・グローバルと同一なら拒否 →【S】上書き確認 →
    書き込み** の順序 / **OFF での OK はグローバルへ書く** / **dirty は
    `hotkey_presets_path` の値が変化したときだけ** / 保存カスケードは書かない /
    **別名保存は個別ファイルを複製**（コピー先に実体があれば複製しない・コピー元が無ければ複製しない）。
  - **UI**（§3-4。切替チェック・保存先表示の出し分け【R】・トグルでの読み直しと破棄確認【I】・
    **OFF で開いた時点の一覧確定【I2】**・**3 択の上書き確認【S/v0.10】**・
    未保存なら ON 不可【F】【Q】）。
  - **既知の制約**（【M】同一 stem の無警告共有 / 複製失敗時は keymap_set の保存ごと中止 /
    フラグキーを持つ keymap_set で `hotkey_presets_path` を手編集した場合は記録パスが保存先になる）。
- **§5.10.4 — 改訂**（暫定仕様 §7 の該当行）: 「読めないときは入口経路ごとの内容で確定する
  （Import ならインライン値）」が **OFF でマネージャを開いた場合には当てはまらない**こと
  （【I2】で表示元＝グローバル / 組込既定へ確定する）と、**【I2】は runtime への注入ではなく
  ダイアログ内の表示用再読込**であることを併記。**【S】の上書き確認**も追記
  （「破損でも上書きする」は維持しつつ、個別への書き込みでは確認が挟まる）。
- **§5.5 — 改訂**: 「keymap_set.json は hotkey preset を参照しない」→ **個別指定時は参照する**。
- **§5.4 — 調整**: 「hotkey_presets は keymap_set の子ではない」を個別指定の導入に合わせて調整。
  **子ファイル（§5.8 の保存計画）にはしない**ことは維持。
- **§5.8.8（入口台帳）— 改訂**: **E1〜E4 は常にグローバル / E5（Import）は強制 OFF**。
  **OFF 復帰時のグローバル再読込**を E1〜E5 のどれでもない**新しい供給点**として追記し、
  **プリセット単独の注入 API は増やさない**ことを明記（トグル時の読み直しは表示更新であり、
  runtime への反映は OK 時の 1 本のまま）。
- **§5.1 — 改訂**: 「生成停止」対象キーの記述を、`hotkey_presets_path` は
  **個別指定時に出力する**へ改める。

### 2. `instructions/common/codebase_map.md`

プリセットの**解決点**（個別 / グローバルの分岐 = `split_loading`）・**保存先算出は application 側**
（`save_path_resolution`）・**切替 UI の所在**（`PresetManagerDialog`）・
**トグル時の読み直しは表示のみ**・**上書き確認の判定 = application / モーダル = presentation**
（`hotkey_presets_io` の自作 Toplevel）を反映する。既存の記述粒度に合わせ、増やしすぎない。

### 3. `instructions/history/08_per_keymap_set_presets.md`（凍結）

先頭の状態行を **「凍結済（v0.10・正本へ昇格済）」** へ更新し、昇格先（`data_schema.md` の該当節 /
`codebase_map.md`）を明記する。**本文の条項は書き換えない**（経緯の参照用として保存）。

### 4. `.claude_data/state/decisions_archive/09_per_keymap_set_presets.md`（新規）

phase 09 の判断履歴を集約する。**最低限含める項目**:

- **v0.5 →v0.6 の反転（【O3】拒否 → 既定パスへ寄せる）** / **v0.7 の【O4】保存先ガード** /
  **v0.8 の 3 改訂（【§3-5】残置パス遮断 /【I】再採用 +【H2】撤回 /【O2】config 外の読み出し許容）** /
  **v0.9 の【S】【I2】** / **v0.10 の【S】3 択化**（各採用理由と却下案。暫定仕様 §4 の表が素材）
- **dirty 規則**（`hotkey_presets_path` の値が変化したときだけ）
- **task_05b が task_05c で置き換わった経緯**
- 実機目視の記録（**v0.8 分＝ 2026-08-15 / v0.9・v0.10 分＝ 2026-08-16 に OK**）と、
  そこで発見された不具合 → 是正タスク（07c / 07d / 07e / 07g）の対応
- 除外・分離した指摘（**ネストしたモーダルの grab 復元 → idea_10**／原子性・状態表記 = 除外）

`.claude_data/state/decisions.md` の**アーカイブ索引へ 1 行追加**し、**進行中だった phase 09 の節は
アーカイブへ集約して索引行に置き換える**（既存フェーズと同じ形式に合わせる）。

### 5. `instructions/phase/current.md`

- 「現在の参照先」を **phase 09 完了**の形へ更新し、**旧フェーズの要約行は残さない**
  （要約は `decisions.md` 索引 + `decisions_archive/09_*.md` が正）。
- **次採番の明記**（次フェーズ = `10_<topic>` / 暫定仕様 = `09_<topic>`）。
- 暫定仕様 08 の状態表記を**凍結済**へ更新。
- 「次フェーズ候補」の idea_08 行を**完了**へ更新する。

### 6. `instructions/backlog/INDEX.md` → `INDEX_done.md`

起票元 **idea_08** の行を完了 / クローズ状態へ更新し、`INDEX_done.md` へ移動する
（`.claude/rules/task_execution.md`「フェーズ完了時」）。**idea_10 は未着手のまま INDEX に残す**。

### 7. `/refactor_check`

`.claude/commands/refactor_check.md` に従い実行する（**メトリクス収集は `verifier` へ委任**・
判定と提案書起票はメイン）。判定結果を完了報告に含める。
提案書の起票は**「推奨」と判定された場合のみ**行う（起票までが本タスクの範囲。
**リファクタの実施はユーザー承認後**で、本タスクには含まない）。

### 設計メモ / 制約

- **正本の記述は「現在の仕様」だけを書く**。版の変遷（v0.5 → v0.6 の反転など経緯）は
  **`decisions_archive` 側**に置き、正本へ持ち込まない。
- **節番号・見出しは変えない**（`/spec_split` の分割規約と参照の安定性のため）。
  分量が閾値に達した場合の分割は**本タスクでは行わない**（必要なら別途 `/spec_split`）。
- 暫定仕様の**条項記号（【O3】【S】等）を正本へそのまま持ち込まない**。正本は記号なしの
  仕様文として書く（記号は暫定仕様・decisions_archive 側の語彙）。
- **§5.9（hook キー）と同型**の構造なので、記述の粒度・順序はそちらに揃える。

## 含まない

- **ソース・テストの変更**（実装は task_01〜07g で完了。差異を見つけたら報告のみ）
- **`/refactor_check` で「要」と判定された場合のリファクタ実施**（提案書起票までで、
  実施は別フェーズ / ユーザー承認後）
- **idea_10（ネストしたモーダルの grab 復元）の着手**（別タスク・別フェーズ）
- 正本の**分割（`/spec_split`）**・他フェーズ由来の記述整理

## 確認

- `data_schema.md` の **§5.10 / §5.10.4 / §5.5 / §5.4 / §5.8.8 / §5.1** が改訂され、
  暫定仕様 08 §7 の表の**全行が反映済み**であること（行ごとに突き合わせる）。
- 受入条件 **1〜21 の各条件**が、正本のいずれかの記述で説明できること
  （＝実装だけがあって正本に無い規則が残っていない）。
- 正本に**暫定仕様への依存が残っていない**こと（正本だけ読めば仕様が確定する）。
- `instructions/history/08_per_keymap_set_presets.md` が**凍結表記**になっていること。
- `decisions_archive/09_per_keymap_set_presets.md` が作成され、`decisions.md` の索引に
  1 行追加されていること（進行中の phase 09 節が残っていないこと）。
- `current.md` が phase 09 完了・次採番明記の状態であること。
- `backlog/INDEX.md` に idea_08 が残っていないこと / `INDEX_done.md` に移動していること。
- **文書のみの変更であることを確認**したうえで、退行が無いことを実測する（`verifier`）:
  - `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
  - `-m unittest discover -s tests` が pass（現行 **238**）
  - `-m unittest discover -s tests_ui` が pass（現行 **223**）
  - `-m tests.smoke_app` が pass
- `/refactor_check` を実行し、判定結果（要 / 不要と根拠）を得ていること。

## 完了条件

- 上記「確認」がすべて pass。
- **`deep-reviewer` の採用**を得ている（本タスクは**正本反映 + フェーズ完了判定**にあたるため、
  `.claude/rules/agent_selection.md` の表に従い `reviewer` ではなく `deep-reviewer` を使う。
  観点 = **正本整合 / 受入条件の網羅 / 暫定仕様との差異 / 過不足**）。
  Codex 側（`codex-adversarial-reviewer`）を併用し、指摘の採否はユーザー判断で決着させる。
- **実機目視は本タスクでは行わない**（task_07 で完了済 = 2026-08-15 / 2026-08-16）。
- `/refactor_check` の判定結果を**完了報告に記載**した（CLAUDE.md / `current.md` の指示）。
- 本タスクの完了をもって **phase 09 を完了**とする。
