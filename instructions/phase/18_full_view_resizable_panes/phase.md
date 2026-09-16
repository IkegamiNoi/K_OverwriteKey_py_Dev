# phase.md

## フェーズ名

フル表示メイン領域の幅配分と境界線ドラッグ（full_view_resizable_panes）

## フェーズの目的

フル表示のメイン領域（**キーマップ管理 | トリガー一覧 | 出力シーケンス**）で、
**アプリ幅の変更で伸縮する枠をトリガー一覧にし**、**境界線のドラッグで両端の枠の幅を変えられる**ようにし、
**その幅を `config/config.json` に保存して再起動後も復元する**。

**対象レイヤは presentation（+ tkinter 非依存の純関数）。`config.json` にキー `full_view_pane_widths` を追加
（後方互換・既存キーの削除 / 意味変更なし）。domain / application / infrastructure は変更しない。**

- 起票元: [idea_20](../../backlog/idea_20_full_view_resizable_panes.md)（ユーザー要望 2026-09-16）。
- 主入力（暫定仕様）: [16_full_view_resizable_panes.md](../../history/16_full_view_resizable_panes.md)
  （**v0.3・ユーザー確定済・実装着手可**）。
- モード: **暫定仕様先行モード**。番号対応: phase 18 / 暫定 16 / decisions 18。

## 確定（ユーザー 2026-09-16）

暫定仕様 16 §2 が正。要点のみ:

- **ウィンドウ幅の変更はトリガー一覧だけが受ける** / **境界線 2 本のドラッグの差分もトリガー一覧が吸収**
  （ウィンドウ幅・反対側の枠は変わらない = 可動範囲を制限。**中ボタンのドラッグは無効**）。
- **一覧も枠に合わせて横に広がる**。**最小幅 = 中身が切れない幅**（一覧は 10 文字相当）。
- **ウィンドウ最小幅 = 両端の表示幅 + トリガー一覧の最小幅**（フル表示中のみ・省略表示の幅 270 を妨げない）。
- **保存はドラッグを離したとき・`write_startup` 経由**。**希望幅と表示幅を分け、ドラッグで実際に変わった側だけ保存**。
- **既定幅は現状と同じ見た目**。**収まらない場合は最終値を計算してから一括適用**（広げる → 画面幅超過なら表示だけ縮める）。

## スコープ

### 含む

- tkinter 非依存の**純関数**（保存値の検証 / 最小幅の算出 / 可動範囲 / 収まらない場合の計算）+ `tests/`。
- `views/full_view/full_view.py`（`tk.PanedWindow` 化）/ `keymap_box.py` / `trigger_box.py`（一覧を横に広げる）。
- 幅を扱う**コントローラ**（新規。ドラッグ制御・最小幅 / `wm minsize` 更新・保存・復元）。
- `app.py` の結線（構築後の復元・フォント変更後の再計算・省略表示との切替順）。
- `tests_ui/`（新規 1 モジュールの見込み。**実際の `config/config.json` を書かない**）。
- 正本反映: `features.md` §4.6 / `data_schema.md` §5.4（`full_view_pane_widths` + config.json 作成契機）/ `codebase_map.md`。

### 含まない（後送り）

- 省略表示（CompactView）のレイアウト変更 / 縦方向のサイズ変更 / ウィンドウ位置・サイズの保存。
- ヘッダ領域の配置変更と、ヘッダが要求幅より狭くなったときの切れ（既存の挙動）。
- ダイアログ類のサイズ保存 / キーボード操作によるサッシュ移動。
- domain / application / infrastructure の変更（`write_startup` と keymap_set 保存経路は**無変更**で値が保持される）。

## このフェーズで読むファイル

1. `instructions/history/16_full_view_resizable_panes.md`（主入力・v0.3）
2. `keyseq/presentation/views/full_view/full_view.py` / `keymap_box.py` / `trigger_box.py` / `sequence_box.py`
3. `keyseq/presentation/app.py`（`:54-` の `__init__`・`:263-284` フォント変更・`:326-378` 表示切替）
4. `keyseq/presentation/controllers/config_io/startup_io.py`（`:39-59` `write_startup`）/ `keyseq/presentation/startup_settings.py`
5. `instructions/common/codebase_map.md` の UI 構成節（`:441-`）とコントローラ一覧
6. `instructions/common/spec_detail/features.md` §4.6 冒頭（`:34-57`）/ `data_schema.md` §5.4（`:41-93`）
7. 既存テストの型: `tests_ui/test_app_ui_flows.py`（共有 App の作り方）/ `tests_ui/test_startup_font_characterization.py`（起動設定の差し替え方）

**読まない**: `keyseq/domain/` / `keyseq/infrastructure/` / `keyseq/application/`（task_04 の保持確認で
`save_runtime_data` の呼び出しを通すときのみ入口だけ）/ 凍結済み暫定仕様（04〜15）。

## タスク

1. **task_01**: 純関数（保存値の検証・最小幅の算出・可動範囲・収まらない場合の最終値計算・既定幅の算出）+ `tests/` の単体テスト（境界値を含む）。**UI へは未結線**。
2. **task_02**: FullView を `tk.PanedWindow` 化（両端 `stretch="never"`・トリガー一覧 `stretch="always"`）+ 一覧と親フレームを横に広げる + **幅コントローラの骨格（最小幅の実測・既定幅の初回適用）**。**既定幅での配置が変更前と一致**すること・ウィンドウ幅変更でトリガー一覧だけ変わること・最小幅で中身が切れないことを `tests_ui` で固定。保存・ドラッグ制御はまだ入れない。
3. **task_03**: 幅コントローラの拡張（ドラッグの可動範囲制限・中ボタン無効・`wm minsize` の更新・希望幅と表示幅・収まらない場合の一括適用）+ `app.py` 結線（フォント変更後の再計算・省略表示への切替順）+ `tests_ui`。
4. **task_04**: 保存と復元（ドラッグを離したときの `write_startup`・変化が無ければ書かない・起動時の検証と復元）+ **keymap_set 保存でも値が残る**ことのテスト。
5. **task_05**: 統合確認（`tests` / `tests_ui` 全体 + `smoke_app`）+ 二次レビュー（`deep-reviewer` + `codex-reviewer`）+ **ユーザーによる実機目視**。
6. **task_06（最終・正本反映）**: `features.md` §4.6 / `data_schema.md` §5.4 / `codebase_map.md` への昇格 + **暫定仕様 16 の凍結** + `decisions_archive/18_full_view_resizable_panes.md` + `current.md` 完了記載 + idea_20 を `INDEX_done.md` へ + **`/refactor_check`**。

タスク定義は着手する順に `tasks/task_NN_<topic>.md` へ起票する（`/task_new`）。

## レビュー方針

共通観点は `.claude/rules/review.md`。本フェーズ固有の観点:

- **押し出し・潰れ** — サッシュを限界まで動かしても反対側の枠が変わらないか / ウィンドウ縮小で両端が縮まないか
  （`PanedWindow` の標準動作に戻っていないか）。
- **希望幅と表示幅の混同** — 自動補正された表示幅が保存されていないか（最小幅で止まった無効ドラッグを含む）。
- **省略表示との干渉** — `wm minsize` の解除が幅 270 の適用より前か / 省略表示中のフォント変更で幅が変わらないか。
- **永続化の経路** — `write_startup` 以外で `config.json` を書いていないか / 実テストで実際の config を汚していないか /
  keymap_set 保存で値が消えないか。
- **責務分離** — FullView が「生成と配置のみ」を保ち、計算は純関数・状態はコントローラにあるか。
- **既存 UI の退行** — 既定幅で見た目が変わっていないか / 既存 `tests_ui` のアサーションを弱めていないか。

エージェントの使い分けは `.claude/rules/agent_selection.md`:

- 各タスクの必須レビュー = `reviewer` / 実装 = `codex-implementer` / テスト実行 = `verifier`
- task_05 の統合確認時 = `deep-reviewer` + `codex-reviewer`
- フェーズ完了判定前 = `deep-reviewer` + `codex-adversarial-reviewer`
