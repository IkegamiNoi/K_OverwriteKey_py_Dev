# task_06_spec_promotion

## 目的

phase 18 の最終タスク（正本反映）。暫定仕様 16（**v0.5**）§7 に従い、
①正本 `features.md` §4.6 へ**フル表示の幅配分・境界線ドラッグ・幅の保存と復元**の規定を追加
②`data_schema.md` §5.4 へ `config.json` のキー **`full_view_pane_widths`** / **`full_view_window_width`** と「config.json が作られる契機」の追加
③`codebase_map.md` へ `controllers/pane_layout/` パッケージ・`pane_width_rules.py`・FullView の `PanedWindow` 構成を追記
④**暫定仕様 16 を凍結** ⑤フェーズ完了処理（decisions_archive / current.md / backlog / `/refactor_check` / 完了判定前レビュー）を行う。
**文書作業のみ。コード・テスト不変。スキーマはキー追加（後方互換）の記述のみ。**

## 対象範囲（文書限定）

### 1. `instructions/common/spec_detail/features.md` §4.6

- `#### View`（`:36-41`）の後に **`#### フル表示の幅配分`** を新設する。暫定仕様 16 の §2・§3 の**振る舞い**だけを書き、実装名（クラス・メソッド）は書かない:
  - 3 枠（キーマップ管理 / トリガー一覧 / 出力シーケンス）の間に境界線。**ウィンドウ幅の増減はトリガー一覧だけが受ける**。
  - 境界線ドラッグで両端の幅を変える。**差分はトリガー一覧が吸収しウィンドウ幅は変わらない**。**反対側の枠を押し縮めない**・トリガー一覧は最小幅で止まる。**中ボタンでは動かない**。
    ドラッグ中はボタン列等を再配置に巻き込まない（移動の適用は間引く）。
  - 各枠の最小幅 = 中身（ボタン・チェックボックス・見出し・間隔入力）が切れない幅（一覧は 10 文字相当）。
    ウィンドウ最小幅 = 両端の表示幅 + トリガー一覧の最小幅。**両端はウィンドウ縮小で縮まない**。
  - **希望幅と表示幅**: 保存するのはドラッグした境界線に接する側の希望幅。フォント拡大等で最小幅へ自動で広げた表示幅は保存しない。
    表示幅が変わらなかったドラッグは希望幅を更新しない。**初回ドラッグ時は動かしていない側の既定幅も希望幅として保存される**（decisions 18 の F7。仕様どおり）。
  - 既定幅 = 変更前と同じ見た目（一覧 26 文字の構成）。**既定ウィンドウ幅 780 のときの配置を基準に算出**（ウィンドウ幅だけ保存された場合も広げた分はトリガー一覧が受ける）。
  - 収まらない場合: ウィンドウを必要幅へ広げる。画面幅を超えるなら出力シーケンス → キーマップ管理の順に表示だけ最小幅まで縮める（保存値は変えない）。最終値を先に計算して 1 回で適用。
  - 省略表示への切替・省略表示中のフォント変更との関係（§3-4 の要点）。
  - **ウィンドウ幅の保存**（v0.5）: フル表示時のウィンドウ幅を、**幅が変わってから 500ms 変化がなければ保存**する。
    **最大化・最小化・省略表示中 / アプリが自動で決めた幅 / 保存済みと同じ幅は保存しない**。ユーザーが幅を変えた後は、自動で決まった幅へ戻した場合も保存する。
    **終了時には保存しない**（最後の変更から 500ms 以内に閉じる・最大化する・省略表示へ切り替えた変更は保存されない = 受容）。高さ・位置・最大化状態は保存しない。
  - 保存に失敗したときのエラー表示中は、他のダイアログと同様にフックを停止する。
- `#### モーダルダイアログの作法` 等の既存節は変更しない。

### 2. `instructions/common/spec_detail/data_schema.md` §5.4（`:41-`）

- `orphan_sweep_scan_dirs` の項（`:59-`）の前に 2 キーの項を追加（実施時に前へ置いた。内容に影響なし）:
  - **`full_view_pane_widths`** = `{"keymap": <正の int px>, "sequence": <正の int px>}`（希望幅・トリガー一覧は保存しない）。
    **不正（非 dict / 欠け / bool を含む非 int / 0 以下）はキー全体を無視して既定幅**（ファイルは書き換えない）。最小幅未満は表示だけ最小幅。書き込み契機 = 境界線のドラッグを離したとき（希望幅が変わった場合のみ）。
  - **`full_view_window_width`** = `<正の int px>`（フル表示時のウィンドウ幅）。**bool を含む非 int / 1 未満は無視して 780**。画面幅を超える値は画面幅に切り詰めて開く（保存値は書き換えない）。
    書き込み契機 = ウィンドウ幅を変えたとき（500ms 間引き・保存値と異なるときのみ）。
  - 両キーとも**書き込みは起動設定の書き出し経路 1 本**（keymap_set 保存で丸ごと書き直されても値が残る。`orphan_sweep_scan_dirs` と同じ機構）。キーが無ければ既定で動く（後方互換）。
- `:57` 付近「`config/config.json` 本体は…**最初に設定が永続化された時点**で作成する（…）」の列挙に
  「**境界線のドラッグを離したとき** / **ウィンドウ幅を変えたとき**」を追加する。

### 3. `instructions/common/codebase_map.md`

- ディレクトリツリー（`controllers/` 配下 `:44-63` 付近）に `pane_layout/`（`__init__.py` / `pane_layout_controller.py` / `pane_measure.py`）を、
  presentation 直下に `pane_width_rules.py` を追加（1 行コメント付き）。
- **`## UI構成` の FullView 節（`:446-`）**: メイン領域が `PanedWindow`（両端 `stretch="never"`・トリガー一覧 `stretch="always"`・境界線 12px）であることを 1〜2 行。
- **`### コントローラ（controllers/）`（`:168-`）**へ `PaneLayoutController`（`app.pane_layout`）の責務を追記:
  最小幅の実測（`pane_measure.py`）・既定幅の初回適用・ドラッグ（可動範囲・中ボタン無効・移動の間引き・希望幅の更新と保存）・
  `wm minsize` の更新・収まらない場合の一括適用・フォント変更 / フル表示復帰時の再計算・**自動決定幅の記録と無効化**・
  **ウィンドウ幅の間引き保存（App の `<Configure>` で予約 / 実行時に判定 / `on_close` と `<Destroy>` で取消）**。
  `pane_width_rules.py` = tkinter 非依存の純関数（保存値の検証・最小幅・可動範囲・収まらない場合の最終値・既定幅・780 基準）。
- App 節（`:113-`）の `on_close` / 省略表示切替に関わる記述があれば、終了時に幅を保存しないこと・予約を取り消すことへ合わせる（該当記述が無ければ追加しない）。
- `StartupIo`（`:196`）の行に「保存失敗の表示中はフックを停止」を追記。

### 4. `instructions/history/16_full_view_resizable_panes.md` の凍結

- ヘッダ状態行を「**凍結済・v0.5**（2026-09-17・phase 18 完了）。正本 = `features.md` §4.6「フル表示の幅配分」/ `data_schema.md` §5.4 / `codebase_map.md`。**条項を実装の根拠に引かない**」へ。
  判断履歴 = `decisions_archive/18_full_view_resizable_panes.md` へのリンクを付ける。本文は変更しない。

### 5. フェーズ完了処理（`.claude/rules/task_execution.md`「フェーズ完了時」）

1. **`.claude_data/state/decisions_archive/18_full_view_resizable_panes.md`** を作成（`17_minimize_grab_custody.md` の型: 対応表 / 問題 / 確定した設計判断の表〔採らなかった案と理由〕/ 版ごとの経緯 v0.1〜v0.5 / 受容した制約 / 残存・後送り〔idea_21・idea_22〕）。
   `decisions.md` の **phase 18 節（`:539-` 末尾まで）を移して削除**し、「アーカイブ索引」の表へ 18 の 1 行を追加する。
2. `instructions/phase/current.md`: phase 18 を完了へ（完了日・コミット・次採番 = phase 19 / 暫定 17 / decisions 19 を明記）。
3. `instructions/backlog/INDEX.md` の **idea_20 行を完了状態にして `INDEX_done.md` へ移動**（暫定 16 凍結済・phase 18 へのリンク）。
4. **`/refactor_check`**（メトリクス収集は `verifier`、判定と提案書起票はメイン）。
5. **完了判定前レビュー**: `deep-reviewer` + `codex-adversarial-reviewer`（**縮退しない**・ユーザー指示）。対象 = phase 18 の全差分（`main` との差分）と正本反映の文面。
   指摘の採否はユーザー判断。

## 読むファイル

- 編集対象（全体）: `instructions/common/spec_detail/features.md` / `instructions/history/16_full_view_resizable_panes.md` §2・§3・§5・§7
- `instructions/common/spec_detail/data_schema.md:41-90`（§5.4）
- `instructions/common/codebase_map.md:30-110`（ツリー）/ `:111-240`（責務）/ `:440-470`（UI構成）
- `.claude_data/state/decisions.md:9-40`（索引の型）/ `:539-`（phase 18 節）
- 手本: `.claude_data/state/decisions_archive/17_minimize_grab_custody.md` / `instructions/phase/17_minimize_grab_custody/tasks/task_05_spec_promotion.md`
- 照合用（実装）: `keyseq/presentation/controllers/pane_layout/pane_layout_controller.py` / `keyseq/presentation/pane_width_rules.py`

## 含まない

- コード・テストの変更（`/refactor_check` が「要」でも、実施は提案書起票 → ユーザー承認後の別計画）
- `key_input.md` §7.2 の改訂（「ダイアログ中はフックを停止」の既存規定の適用であり、条項追加は不要）
- idea_21（ヘッダ幅）/ idea_22（縦方向の最小サイズ）
- main へのマージ（ユーザー判断）

## 確認

- **正本の文面が実装と一致**: `features.md` / `data_schema.md` の追加条項それぞれについて根拠となる実装の行
  （`pane_width_rules.py` の検証関数・`pane_layout_controller.py` の保存予約と判定・`startup_io.py:57-62`）をメインが照合し、完了報告に対応表を載せる。
- **リンク実在**: 暫定仕様 16 のヘッダ → `decisions_archive/18_full_view_resizable_panes.md`、`INDEX_done.md` の idea_20 行のリンク先がすべて実在する（`ls`）。
- `instructions/backlog/INDEX.md` に idea_20 の行が残っていない（`grep`）。
- `decisions.md` に phase 18 節が残らず、索引に 18 の行がある（`grep`）。
- `git diff --stat` が**文書ファイルのみ**（`keyseq/` `tests/` `tests_ui/` に差分なし）。
- `/refactor_check` の判定（要 / 不要）と根拠メトリクスを完了報告に含める。
- `deep-reviewer` + `codex-adversarial-reviewer` の結果と採否を完了報告に含める。

## 完了条件

- 上記確認をすべて満たし、**`reviewer` 採用**（正本反映の文面と実装の整合確認に限定）。
- 完了判定前レビュー（`deep-reviewer` + `codex-adversarial-reviewer`）の指摘をユーザーが採否判断済み。
- 実機目視は不要（task_05 で完了済み）。

## 完了記録（2026-09-17）

- 正本反映: `features.md` §4.6「フル表示の幅配分」新設 / `data_schema.md` §5.4 に 2 キーと config.json 作成契機 / `codebase_map.md` にツリー・PaneLayoutController・StartupIo・FullView 構成。
  暫定仕様 16 を v0.5 で凍結。`decisions_archive/18` 作成・`decisions.md` の phase 18 節を移設。idea_20 を `INDEX_done.md` へ。
- **正本と実装の対応**（`reviewer` が条項ごとに根拠行を確認）: トリガー一覧のみ伸縮 = `full_view.py:58-60` / 中ボタン無効 = `pane_layout_controller.py:58-59` /
  押し出し防止 = `pane_width_rules.py:103-113` / 希望幅の更新 = `pane_width_rules.py:121-131` / 780 基準 = `pane_width_rules.py:20-22` /
  一括適用 = `pane_layout_controller.py:89-106` / 間引き保存と判定 = `pane_layout_controller.py:208-239` / 保存値の検証 = `pane_width_rules.py:13-17,52-61` /
  失敗表示中のフック停止 = `startup_io.py:57-62`。
- `/refactor_check` = **不要**（M1〜M6 該当なし・`keyseq/` 10 ファイル）。境界の観察 2 件は `current.md` 別タスク化候補へ。
- 完了判定前レビュー: `deep-reviewer`（修正要・軽微）+ `codex-adversarial-reviewer`（中 2）→ ユーザー採否（推奨どおり）:
  テスト遮断 = **task_06b** / 文書 5 件 = 反映 / Codex 2 件 = 受容（正本の受容制約へ）/ 3 件 = 保留。詳細は `decisions_archive/18`。
- `reviewer`（task_06）: 文面は実装と整合。指摘は完了処理の未了のみ → 上記で解消。
