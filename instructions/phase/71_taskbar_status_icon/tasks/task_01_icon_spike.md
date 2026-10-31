# task_01_icon_spike

## 目的

暫定 54 §3.3・§5 の方式を、Windows 11 の実機で確かめて決める（試作・スパイク）。
確かめる点: ①`iconphoto` の差し替えがタスクバーのボタンに出るか ②`-default`（`iconphoto(True, …)`）が**開いている**子窓にも効くか
③16 / 32 px を渡したとき、タスクバー・タイトルバーで形が見分けられるか ④①で出ないとき AppUserModelID の設定で出るか。
**製品コードは変更しない**（スクリプトは scratchpad に置き、リポジトリへ入れない）。

## 対象範囲（試作スクリプト + 暫定仕様の改訂のみ）

### 試作スクリプト（scratchpad・使い捨て）

- tkinter だけで、暫定 54 §4.3 の寸法の印（●■‖）を 16 / 32 px の透過の正方形に描き、ルートへ設定する。
- ボタン: 状態の切替（ON → OFF → 一時停止）/ 子窓を開く / 子窓へ個別に設定する。
- 起動引数で AppUserModelID の設定（`shell32.SetCurrentProcessExplicitAppUserModelID`・最初の窓を作る前）の有無を切り替える。
- `.venv` の python.exe で起動する（アプリと同じ動かし方）。

### `instructions/history/54_taskbar_status_icon.md`

- 結果を §1 の現状監査へ追記し、§3.3・§5 の案 A / B を確定して §9-1 を解消する。必要なら §4.3 の寸法・色を調整する。版を v0.4 にする（ユーザー確認後）。

### 設計メモ / 制約

- 試作のコードは本実装の手本にしない（本実装は task_02・03 で暫定 54 に従って行う）。
- 試作は製品コードではないため、メインセッションが書いて動かす（Codex は python を動かせない・実装委任の対象外）。

## 読むファイル

- `instructions/history/54_taskbar_status_icon.md`（§3.3・§4.3・§5）

## 含まない

- `bundled_paths` の昇格・`hook_display_state`・`badge_shapes`（task_02）
- `StatusIcon`・サンプル画像・`update_status` の結線・AppUserModelID の本実装（task_03）

## 確認

- ユーザーの実機目視: ①〜④の結果（タスクバーのボタン・タイトルバー・開いている子窓・後から開いた子窓）。
- 暫定 54 v0.4 の改訂内容がユーザーの確認した結果と一致していること。

## 完了条件

- 上記確認 pass・暫定 54 v0.4 をユーザー確認・**reviewer 採用**（改訂した暫定 54 の差分が試作の結果と矛盾しないか）。
- 実機目視は本タスクで実施する。
