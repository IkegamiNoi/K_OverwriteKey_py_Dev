# phase.md

## フェーズ名

スクロールのアクションの向きの反転（scroll_direction_setting）

## フェーズの目的

出力シーケンスの `mouse_scroll` の行が送る向きを、アプリの設定で縦・横それぞれ反転できるようにする（Mac のナチュラルなスクロールなど、OS 側で向きを入れ替えて使う人向け）。
**対象は domain（`ScrollInvert` と正規化・反転の純関数）・application（`ActionExecutor` が呼び出し時に読む callable で反転を受ける）・presentation（設定メニューのサブメニュー・保存・i18n・ヘルプ本文）。infrastructure の backend は変えない。JSON スキーマ = config.json に任意キー `scroll_invert` を追加（既定は反転なし・後方互換）**。

- 起票元: [idea_58](../../backlog/idea_58_scroll_direction_setting.md)（2026-11-15 phase 75 task_11a の Mac 実機目視でのユーザー要望）。
- 主入力（暫定仕様）: [62_scroll_direction_setting.md](../../history/62_scroll_direction_setting.md)（v0.4・ユーザー確定済）。
- モード: **暫定仕様先行モード**（config.json・メニュー・文言・application・正本 3 冊に跨る・タスク 3 以上）。番号対応: phase 82 / 暫定 62 / decisions 82。

## 確定（ユーザー 2026-11-26）

- 方式 = config.json のグローバル設定 `scroll_invert` = `{"vertical": bool, "horizontal": bool}`・縦横別・既定は反転なし・application で符号を反転（暫定 62 §2・§3）。アクションごとの指定・Mac の OS の設定への自動追従は採らない。
- メニュー = 設定 > サブメニュー「スクロールの向き」> チェック「縦を反転」/「横を反転」（「物理キー名を表示」の下の区切りの後・「フォントサイズ」の上）。ヘルプに 1 文。ダイアログ・一覧には反転中を出さない（§2）。
- 起票時 deep-reviewer（修正して採用・setter 案は保留）と Codex 敵対的レビュー 指摘 2〜5 を反映（v0.4）。指摘 1（多重起動で config.json が上書きされる・全設定に既存の問題）はスコープ外 → [idea_70](../../backlog/idea_70_config_overwrite_on_multiple_instances.md)。

## スコープ

### 含む

- domain: `ScrollInvert`（frozen dataclass）・`coerce_scroll_invert`・`apply_scroll_invert`（暫定 62 §3・§4）
- application: `ActionExecutor` の任意の引数 `get_scroll_invert` と `_execute_mouse_scroll` での反転の適用（§4）
- presentation: 起動時の読込・実行に使う値の保持と差し替え・設定メニューのサブメニューと保存（`menu_commands.defer`・保存済みと同じなら書かない・失敗で戻す）・`ui_vars` の BooleanVar・ja / en の文言・ヘルプ本文の 1 文（§5・§2）
- テスト: domain・executor の単体テスト、メニューの切替と保存の tests_ui、`tests/test_menu_bar_deferral.py` の期待値の変更（§9）
- Windows / macOS の実機目視（ユーザー・§7-8）

### 含まない（後送り）

- アクションごとの反転・OS の設定の読み取り / 自動追従・OS の設定の変更・アプリ内の画面のマウスホイールの向き（§8）
- 多重起動での config.json の上書き（idea_70）

## このフェーズで読むファイル

1. [暫定仕様 62](../../history/62_scroll_direction_setting.md)（§1 の `ファイルパス:行` が実装の起点）
2. `keyseq/domain/mouse_scroll.py`（`scroll_deltas`）
3. `keyseq/application/action_executor.py`（`__init__`・`_execute_mouse_scroll`）
4. `keyseq/presentation/app.py`（起動設定の読込・`ActionExecutor` の組み立て・`set_ui_language` の保存失敗の前例）・`keyseq/presentation/controllers/config_io/startup_io.py`（`write_startup`）
5. `keyseq/presentation/views/menu_bar.py`（設定メニュー）・`keyseq/presentation/views/menu_command_queue.py`・`keyseq/presentation/ui_vars.py`
6. `keyseq/shared/i18n/locales/ja.json`・`en.json`（`menu.settings.*`）・`keyseq/presentation/help/content/help_ja.json`・`help_en.json`（mouse_scroll の説明・312 行付近）
7. 既存テスト: `tests/test_mouse_scroll.py`・`tests/test_action_executor_mouse_scroll.py`・`tests/test_menu_bar_deferral.py`
8. 正本 `instructions/common/spec_detail/data_schema.md` §5.4・§5.11.10 / `features.md` §4.6（設定メニュー・言語）・§4.8（メニューの処理）/ `instructions/common/codebase_map.md` の該当節

## タスク

- task_01: domain（`ScrollInvert`・`coerce_scroll_invert`・`apply_scroll_invert`）+ application（`ActionExecutor` の `get_scroll_invert` と反転の適用）と tests（暫定 62 §3・§4・§7-1〔値の正規化〕〜3・6）
- task_02: presentation（起動時の読込と値の保持・設定メニューのサブメニュー・保存と失敗時の戻し・`ui_vars`・ja / en の文言・ヘルプ本文）と tests_ui・`tests/test_menu_bar_deferral.py` の期待値の変更（§5・§7-1〔起動時の読込・config.json が読めないとき〕・4・5・5a・7・7a）
- task_03: 統合確認（tests / tests_ui / smoke）と Windows / macOS の実機目視（ユーザー・§7-8）
- task_04: 正本反映（暫定 62 を `data_schema.md` §5.4・§5.11.10 / `features.md` §4.6・§4.8 / `codebase_map.md` へ昇格・`ui_terms.md` は用語を足す場合・暫定 62 を凍結）+ `decisions_archive/82` と `decisions.md` の索引 + current.md の完了記載 + idea_58 を `INDEX_done.md` へ + `/refactor_check`

## レビュー方針

- 共通観点は `.claude/rules/review.md`。各タスクは `reviewer`、統合確認は `deep-reviewer` + `codex-reviewer`、フェーズ完了判定前は `deep-reviewer` + Codex 敵対的レビュー
- 固有の観点: 反転が符号だけを変え、量・分け方・座標・backend の OS への渡し方（macOS の横の符号）を変えていないか / executor が Tk の変数を読んでいないか（不変の値を 1 回の代入で差し替え）/ 保存がメニューの遅延を通り、失敗でチェックと実行の値が保存済みに戻るか / 構成セットを未保存にしていないか / `get_scroll_invert` が None のとき今までどおりか
