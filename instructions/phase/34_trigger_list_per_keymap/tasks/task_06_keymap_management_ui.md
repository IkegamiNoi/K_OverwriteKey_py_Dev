# task_06_keymap_management_ui

## 目的

キーマップ管理の UI と切替の振る舞いを暫定仕様 25 §8.1〜§8.3（と §3.3 末尾・§5.6 の個別読込の追加規則）に合わせる。
一覧の選択 = アクティブ化、追加時の切替キー必須、削除制限、連続実行中の切替禁止、切替時の再描画、シーケンス実行位置のキーマップ（実体）単位化。

**JSON スキーマ不変**。presentation（`keymap_panel_controller.py` / `keymap_box.py` / `keymap_file_io.py` / `trigger_panel_controller.py` / 編集・追加ダイアログ）と
application（`action_executor.py` の `SelectKeymapAction` / `sequence_runner.py` / `app_state.py` の実行位置）。

## 対象範囲

### §8.1 一覧の選択 = アクティブ化

- キーマップ一覧で行を選択（クリック・矢印キーでの移動）したら、そのキーマップを**アクティブにする**（`on_keymap_list_select` から `activate_keymap_by_id`）。
- **「選択」ボタンを削除**する（`keymap_box.py` の配置と `keymap_panel_controller.select_keymap` の配線。ボタン行の他ボタンの配置は崩さない）。ダブルクリックの編集は維持。
- **アクティブの変更で構成セットを未保存にしない**（一覧の選択・直接切替キーの両経路。現行の `mark_dirty=True` 経路を無くす）。保存時にはその時点のアクティブが書かれる（現行どおり）。
- 帰結（仕様どおり）: 編集・削除・個別の保存 / 読込の対象は常にアクティブなキーマップ。

### §8.3 / §3.3 アクティブ切替時の再描画と実行位置

- アクティブが変わったら（一覧の選択・直接切替キー・削除による変更・読込）、**トリガー一覧・シーケンス欄・キーボードウィンドウ・CompactView の表示を再描画**する（グレー表示の再判定〔task_05〕を含む）。
- アクティブ以外のキーマップの未保存の編集は切替で失わない（runtime に保持・現行の保持で満たされるはず。テストで確認）。
- **シーケンスの実行位置（`_indices`）・トリガー一覧の選択行（`_selected_trigger_idx`）を、トリガー一覧の実体ごとに保持**する（現行は trigger key 単位で全キーマップ共有のため、別キーマップの同じキーの位置を引き継ぐ）。キーは実体の識別子（task_02 の代表 keymap id）+ trigger key 等、実装判断でよい。

### §8.2 連続実行中の切替禁止

- 連続実行中（`run_to_end_key` が設定されている間。**一時停止中を含む**）は、次の経路でアクティブを変えない:
  一覧の選択（選択表示をアクティブの行へ戻す）/ 直接切替キー（`SelectKeymapAction`）/ アクティブなキーマップの削除。
- そのときステータス欄に「連続実行中のためキーマップを切り替えられません」を表示する。
- 判定は application 側（連続実行状態を持つ `sequence_runner` / `app_state`）の問い合わせを 1 つ用意し、presentation の各経路と `action_executor` が共有する。

### §8.1 追加・編集・削除

- **追加**（`add_keymap`）:
  1. 切替キーの無い既存キーマップがあれば、一覧順に 1 つずつ「<名前> に切替キーを設定してください」のエラーダイアログ → OK でそのキーマップの編集ダイアログを開く →
     切替キーが設定されたら次へ / キャンセル・空のままなら**追加を中止**。
  2. 追加ダイアログで**ラベル（任意）と切替キー（必須・空は拒否）**を入力して作成する（切替キーの検証は既存の `validate_keymap_switch_assignment`〔task_05 で拡張済み〕を使う）。
  - キーマップが 0 個の状態は仕様上ありえない（§2-7）が、万一 0 個なら切替キーなしで 1 つ作る（自動作成と同じ規則）。
- **個別読込**（`keymap_file_io.load_keymap_file`・§5.6）: 読み込んだキーマップの追加も上記の追加規則に従う（切替キーの無い既存があれば先に設定 / 読み込んだキーマップにも切替キーを設定させる〔キーマップが 0 → 1 個になる場合を除く〕。キャンセルなら読込を中止し runtime を変えない）。
- **編集**: キーマップが 2 つ以上のときは切替キーを空にできない（拒否してエラー表示）。1 つだけのときは空にできる。
  読込済みデータで切替キーの無いキーマップが複数あっても読込は拒否しない（追加時に 1. で拾う）。
- **削除**: キーマップが 1 つだけのときは削除できない（ボタンを無効化するか、押したらエラー表示。どちらでもよいが一貫させる）。
  未保存のトリガー一覧・シーケンスを持つキーマップの削除確認では、それらが破棄されることを確認文に明示する。
  アクティブの削除は連続実行中は不可（§8.2）。

### テスト（追加・更新）

- 既存テストの期待値更新は、選択ボタン削除・選択 = アクティブ化・未保存にしない・追加フロー・削除制限によるもののみ。アサーションを緩めない。テスト補助で runtime を書き換えない。キーマップ 0 個のフィクスチャを作らない。**未モックの実ダイアログを開かない**（追加フローのエラーダイアログ・編集ダイアログ・追加ダイアログはすべて patch）。
- 新規:
  1. 一覧の選択でアクティブが変わり、構成セットは未保存にならない・トリガー一覧 / キーボード表示が再描画される。直接切替キーでも同様。
  2. 選択ボタンが無い。
  3. 連続実行中（一時停止中を含む）: 一覧の選択は元の行へ戻り、直接切替キー・アクティブの削除も切り替わらず、ステータスに案内が出る。連続実行していなければ切り替わる。
  4. 追加: 切替キーの無い既存がある → エラー → 編集ダイアログ → 設定で次へ / キャンセルで中止。追加ダイアログで切替キー空は拒否・ラベルは任意。
  5. 個別読込が追加規則に従う（キャンセルで runtime 不変）。
  6. 編集: 2 つ以上で切替キーを空にできない / 1 つなら空にできる。
  7. 削除: 1 つだけなら削除できない / 未保存の子を持つキーマップの確認文に破棄の明示。
  8. 実行位置: キーマップ A の f1 で位置を進めて B（同じ f1 あり）に切り替えると B の位置は独立 / A に戻すと A の位置が残る。
  9. アクティブ以外のキーマップの未保存の編集が切替で失われない。

## 読むファイル

- `instructions/history/25_trigger_list_per_keymap.md` §3.3 末尾・§5.6・§8.1〜§8.3（該当節のみ）
- `keyseq/presentation/controllers/keymap_panel_controller.py`（全体）/ `keyseq/presentation/views/full_view/keymap_box.py`（パスは実在のものを探す）
- `keyseq/presentation/controllers/config_io/keymap_file_io.py`（読込部分）/ `keyseq/presentation/controllers/trigger_panel_controller.py`（再描画・選択行・実行位置の箇所）
- `keyseq/application/action_executor.py`（SelectKeymapAction）/ `sequence_runner.py` / `app_state.py`
- キーマップの編集・追加に使うダイアログ（`keyseq/presentation/dialogs/keymap_edit_dialog.py`）
- 手本のテスト: `tests_ui/test_task05_overlap_ui.py`（直近の UI テストの書き方）/ `tests/test_sequence_runner.py:1-60`

## 含まない

- 一時停止ボタン・ステータス・トグルキー表記の改名（**task_07**）
- 連続実行中の構成セット単位の操作（構成セットの読込等）の制限（暫定 §11・スコープ外）
- `features.md` 等 `instructions/` 配下の編集（task_08。選択ボタン削除でキーマップ枠の要求幅が変わる場合は報告に記載する）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq` clean
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` 全 pass（skip 7 据え置き）
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` 全 pass（ハングしないこと）
- `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` pass
- `git grep -n '"triggers"' -- keyseq/presentation` が 0 件 / `git status --short -- instructions` は本タスク定義のみ
- 期待値を更新した既存テストの一覧と理由を報告に含める

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- **実機目視はユーザーが行う**（task_07 の後・task_08 の前にまとめて依頼する。確認項目は task_08 起票時に列挙）。
