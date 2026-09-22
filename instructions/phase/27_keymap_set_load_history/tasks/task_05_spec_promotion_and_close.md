# task_05_spec_promotion_and_close

## 目的

phase 27 の設計（暫定仕様 21 v0.5）を**正本へ昇格**し、暫定仕様を凍結してフェーズを閉じる。
昇格先は暫定仕様 §9 の表が正。**文書作業のみ**で、実装・テストは変更しない
（`.claude/rules/agent_selection.md`「フェーズ末の正本反映タスクはメインセッションが直接行う」）。

レイヤ制約: **コード差分ゼロ**。`keyseq/` ・ `tests/` ・ `tests_ui/` を一切変更しない。

## 対象範囲（文書のみ）

### 1. instructions/common/spec_detail/data_schema.md — §5.12 を新設

現在の最終節は §5.11（`:371`）。その後ろへ **§5.12「構成セットの読み込み履歴」**を追加する。
**本体へ直書きする**（`data_schema.md` は INDEX だが、子ファイルへ実体を出しているのは
§5.8 と §5.10 のみ。他節と同じ扱いにする）。含める内容（暫定仕様 §3 / §4 が出典）:

- **ファイル位置** = `config/keymap_set_history.json`（`config.json` と同階層・固定パス。
  `config.json` にキーを追加しない）。`user/` 配下を避ける理由（参照側の走査ディレクトリに
  指定され得る）も 1 行で残す。
- **スキーマ** = `recent`（新しい順・最大 20・先頭が最新）/ `categories`（`name` + `entries`）。
  `path` は §5.7 の保存表記に従う。**`version` キーは持たない**（hotkey presets に揃える）。
- **型不正の扱い**（§5.1 の共通規則の下位規定）= list でなければ空扱い / 非 dict 要素は除去 /
  `path` が非文字列・trim して空なら要素ごと除去 / 分類名が非文字列・空なら分類ごと除去 /
  分類名の重複は先に現れた方を残す / `recent` が 21 件以上なら読込時に 20 件へ切り詰め。
- **「無い」と「読めない」を区別する**（読めなかった場合に空で上書きしない）。
- **記録の契機** = 読込または保存が成功し空でないパスが確定したとき、その**実保存先**。
  **除外** = `app.py` の初期代入 / 新規作成 / Import / 例の復元 / **起動時の自動読込**（v0.5）。
  起動時に記録しない理由（起動しただけで履歴ファイルを作らない = §5.4 の遅延作成方針と整合）も残す。
- **積み方** = 先頭が同一パスなら書き込まない（判定は永続化済みの内容）/ 同一パスは全除去して
  先頭へ挿入 / 21 件目以降を捨てる（不在エントリも枠を数える）/ 原子的置換で書く。
  同一性判定は §5.7 の比較専用表記に従う。
- **遅延作成** = 起動時のディレクトリ骨格作成（§5.4 `ensure_split_config_dirs`）の対象に**加えない**。
- **読めないときの退避** = `keymap_set_history.broken.json` → `broken2` … **連番 5 で打ち止め**。
  退避に失敗したらそのセッションは書き込まず**読み取り専用**として扱う。`config/quarantine/` は使わない。
- **永続化に成功してから UI を確定する**（失敗した編集を一覧へ反映しない）。
  履歴の失敗で構成セットの読込・保存を巻き戻さない。

**節番号・既存の見出しは変更しない**。§5.11 以前の本文に手を入れない。

### 2. instructions/common/spec_detail/features.md — §4.6 へ 1 行

`### 4.6 UI 構成`（`:34`）配下の「メニュー・個別保存」節（`:113` 付近）で、
「ファイルメニューの通常読込は「読込（構成セット）…」」の**直後**へ
「履歴から読み込む…」の行を足す（位置 = 通常読込の直後・`data_schema.md` §5.12 を参照）。
ダイアログの規定（一覧の構成・ボタン・編集は即時永続化・読み取り専用）は
**§5.12 側に寄せ、features.md には UI の存在と位置だけ**を書く（重複記述にしない）。

### 3. instructions/common/codebase_map.md — 4 箇所へ追記

- **presentation のフォルダ構成**（`:34-118`）= `dialogs/keymap_set_history_dialog.py` /
  `keymap_set_history_text.py` / `controllers/config_io/keymap_set_history_io.py`。
- **コントローラ**（`:176-318`）= `KeymapSetHistoryIo` の責務
  （記録の単一の口 `record()` + 履歴ダイアログの開閉と編集 6 メソッド。
  **編集は「読み直し → domain → 保存成功のみ反映」**）。
- **ConfigService**（`:332-458`。パッケージ表のファイル数も更新する）=
  `config_service/keymap_set_history.py` と公開メソッド
  `load_keymap_set_history` / `save_keymap_set_history` / `record_keymap_set_history`。
  **domain の `keyseq/domain/keymap_set_history.py`**（純関数群）も記載する
  （既存の domain 記載箇所に合わせる。無ければアーキテクチャ節へ 1 行）。
- **メニュー / ステータス**（`:503-512`）= ファイルメニューへ「履歴から読み込む…」。
- あわせて **`keymap_set_io.load_keymap_set_path`（パス指定の共通読込入口）**と
  **記録の呼び出し点 3 経路**（読込の共通入口 / 起動セット指定 / 保存成功）を
  コントローラ節へ 1〜2 行で残す。

### 4. instructions/common/spec_detail/data_schema/5_08_09_orphan_sweep.md — 補記の要否判断

暫定仕様 §9 の保留事項。**走査範囲・孤児判定は不変**（候補側は固定 4 ディレクトリで、
履歴ファイルが孤児候補になることはない）。**参照側に `config/` を指定した環境では
非 keymap_set として警告に載り得る**点を補記するかを判断し、**判断結果を完了報告に書く**
（補記する場合は 1〜2 行。しない場合は「不要」と理由）。

### 5. instructions/history/21_keymap_set_load_history.md — 凍結

ヘッダのブロック引用を凍結表記へ置き換える（手本 = `instructions/history/20_individual_json_type_normalization.md:1-6`）:

- 状態 = **凍結（2026-09-22・正本反映済）**。正本が最新。本書は経緯記録として凍結。
- 昇格先 = `data_schema.md` §5.12 / `features.md` §4.6 / `codebase_map.md`（+ §4 の判断結果）。
- **本書の条項を実装の根拠に引かない**（正本が正）。
- v0.1〜v0.5 の履歴行は**残す**（経緯記録）。本文の §1〜§10 は書き換えない。

### 6. .claude_data/state/decisions_archive/27_keymap_set_load_history.md（新規）

`decisions.md` の「2026-09-21〜 (phase 27: …)」節（`:548` 以降）の内容を集約して移す。
構成は `decisions_archive/26_startup_entry_preservation.md`（79 行）に合わせ、
**80〜120 行程度**に収める。少なくとも次を落とさない:

- 起票時の確定（保存先・記録契機・除外経路・先頭一致 no-op・退避先の判断とその理由）
- **v0.5 改訂の経緯**（起動時記録が `tests_ui` から実 `config/` を汚した実測 → 起動時は記録しない）
- task_03 の差し戻し（例外ガード無しで「成功を失敗と表示」「空データ起動」になっていた欠陥）
- task_04 の判断（UI の入力方式 / `simpledialog` 不採用の理由 / 指摘 2 件の修正して採用）
- **実機目視で見つかった 2 件**（フォーカス未設定で Escape が届かない / 列の stretch）と
  横断分は [idea_26](../../instructions/backlog/idea_26_dialog_keyboard_focus.md) へ分離した旨
- 残件（あれば）

移設後、`decisions.md` 本体からは phase 27 節の本文を削除し、
**「アーカイブ索引」へ 1 行**（`- decisions_archive/27_keymap_set_load_history.md — <概要>`）を足す。

### 7. instructions/phase/current.md — 完了記載と次採番

- 「現在の参照先」の phase 27 項を**完了**へ書き換え（`- [phase 27](...) は 2026-09-22 完了。`）。
  **アクティブなフェーズが無い**状態にする。
- 「直近の一連の作業が扱っている領域」を **phase 27（構成セットの読み込み履歴）**へ差し替える
  （正本の該当節 / 実装ファイル / テスト / 要点 / 残件 / `decisions_archive/27` へのリンク）。
  既存の phase 26 項は 1 行の完了記載へ縮める（既存の書式に合わせる）。
- 「次採番」節 = phase 28 / 暫定 22 / decisions 28 を**明記**（暫定 21 を**凍結済**へ更新）。
- **起票元 idea は無い**ため `backlog/INDEX_done.md` への移動は**不要**
  （`idea_26` は今フェーズ起票の新規ネタなので INDEX.md に未着手のまま残す）。

### 8. /refactor_check の実行

`.claude/commands/refactor_check.md` に従う。**メトリクス収集（手順 1〜2・M1〜M6）は `verifier` へ委任**し、
判定（手順 3 以降）と提案書起票の要否はメインが行う。**判定結果を完了報告に記載する**
（提案書の起票が必要な場合はユーザー承認を得てから）。

## 設計メモ / 制約

- **正本へ書くのは確定した規範のみ**。暫定仕様の検討過程・却下案・レビュー経緯は正本へ持ち込まない
  （それらは暫定仕様と `decisions_archive/27` に残る）。
- **実装に合わせて仕様を緩めない**。昇格作業中に「正本へ書くと実装と食い違う」箇所を見つけたら、
  書き換えずに**作業を止めてユーザーへ報告**する（`.claude/rules/spec_change_workflow.md` の検出基準 A/D）。
- 既存節の**節番号・見出しは変更しない**（`data_schema.md` §5.8.9 等の外部参照が壊れる）。
- `data_schema.md` は現在 441 行。§5.12 追加後に肥大化が問題になるかは `/spec_split` の判定に委ねる
  （本タスクでは分割しない）。

## 読むファイル

1. `instructions/history/21_keymap_set_load_history.md`（**§3 / §4 / §5 / §8 / §9 / §10**。昇格の出典）
2. `instructions/common/spec_detail/data_schema.md:242-263`（§5.7 パス保存ルール）・`:75-149`（§5.4。
   遅延作成とディレクトリ骨格）・`:371-441`（§5.11。最終節の書式と末尾）
3. `instructions/common/spec_detail/features.md:108-124`（§4.6「メニュー・個別保存」）
4. `instructions/common/codebase_map.md:34-118`（フォルダ構成）・`:176-318`（コントローラ）・
   `:332-458`（ConfigService）・`:503-512`（メニュー）
5. `instructions/common/spec_detail/data_schema/5_08_09_orphan_sweep.md`（走査範囲の該当箇所のみ）
6. `instructions/history/20_individual_json_type_normalization.md:1-14`（凍結ヘッダの手本）
7. `.claude_data/state/decisions_archive/26_startup_entry_preservation.md`（全体・79 行。アーカイブの手本）
8. `.claude_data/state/decisions.md` の phase 27 節（`:548` 以降）と「アーカイブ索引」節
9. `instructions/phase/current.md`（「現在の参照先」「次採番」節）
10. 実装の実体（記述の裏取り用・**必要な範囲のみ**）:
    `keyseq/domain/keymap_set_history.py` / `keyseq/application/config_service/keymap_set_history.py` /
    `keyseq/presentation/controllers/config_io/keymap_set_history_io.py`

## 含まない

- **コードとテストの変更**（`keyseq/` ・ `tests/` ・ `tests_ui/`）。差分ゼロで完了すること。
- `idea_26`（ダイアログのフォーカス横断修正）の着手。**別フェーズ**。
- 暫定仕様 §10 のスコープ外項目の仕様化（分類の入れ子・D&D・検索・`*.broken*.json` の管理 UI 等）。
- `data_schema.md` の `/spec_split` 分割の実施（判定のみ。実施はユーザー承認後の別作業）。
- `/refactor_check` で挙がった改善の**実施**（提案書の起票要否の判断まで）。
- `handoff.md` の再生成（`/save_handoff` で別途行う）。

## 確認

- **コード差分ゼロ**: `git diff --stat -- keyseq tests tests_ui` が空であること。
- 標準検証 4 本が**前回と同値**であること（`verifier` へ委任。compile clean / `tests` 556 ran OK
  〔skip 7〕/ `tests_ui` 483 ran OK / smoke `SMOKE OK`）。文書変更なので値が動いたら異常。
- **正本の反映漏れチェック**: 暫定仕様 §8 の受け入れ条件 27 項目のうち、**規範として正本へ
  残すべき条項**（ファイル位置 / スキーマ / 型不正 / 記録契機と除外 / 上限・重複・先頭 no-op /
  遅延作成 / 退避と読み取り専用 / 永続化と UI の順序 / UI の入口）が §5.12・§4.6 に
  すべて現れていることを逐一照合する。
- **リンクの実在確認**: 追記した相対リンク（`decisions_archive/27` / `idea_26` / 正本の節参照）が
  すべて解決すること。
- **節番号の一意性**: `data_schema.md` に §5.12 が 1 つだけ存在し、§5.11 以前が無改変であること
  （`git diff` で確認）。
- `/refactor_check` の判定結果（要否と根拠）が出ていること。

## 完了条件

- 上記「確認」がすべて pass。
- **フェーズ完了判定のレビューを 2 系統で実施**（`.claude/rules/agent_selection.md` の表）:
  `deep-reviewer`（正本の記述と実装の整合・条項の欠落と矛盾・より単純な代替）+
  `codex-adversarial-reviewer`（敵対的レビュー）。**指摘の採否はユーザー確認を経る**。
- `.claude/rules/task_execution.md`「フェーズ完了時」のチェックリストを満たす
  （正本昇格 + 暫定仕様の凍結 / `decisions_archive/27` / `current.md` の完了記載と次採番 /
  `/refactor_check` の実行と結果の記載）。**起票元 idea が無いため INDEX_done 移動は対象外**。
- 実機目視は**不要**（UI の変更を伴わない文書タスク。task_04 で実施済み・OK）。
