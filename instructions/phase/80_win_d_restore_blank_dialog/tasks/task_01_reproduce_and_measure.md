# task_01_reproduce_and_measure

## 目的

Windows で「プリセット管理 → プリセット追加」を開いたまま Win+D で隠し、戻すとプリセット追加が白いまま描かれない
（[idea_61](../../../backlog/idea_61_win_d_restore_blank_dialog.md)）原因を実測で特定し、直す範囲と修正案を決める。
**コード変更なし**（計測用の一時スクリプトは scratchpad に置き、リポジトリへ入れない）。
関連する正本 = `features.md` §4.6「モーダルダイアログの作法」の最小化の項（1163〜1197 行）。

## 対象範囲（実測のみ・コード変更なし）

### 再現

- 実 App（`tests_ui/test_minimize_grab_custody.py` と同じ作り方）でプリセット管理を開き、その子としてプリセット追加を開く
- Win+D を `SendInput` 相当で送り、次の 2 通りで戻す: (a) もう一度 Win+D / (b) App の窓を `ShowWindow(SW_RESTORE)` + 前面化（タスクバーのクリック相当）
- 比較: タイトルバーの最小化相当（`iconify()` → `deiconify()`）

### 記録（窓ごと: App・プリセット管理・プリセット追加）

- イベント: `<Map>` / `<Unmap>` / `<Expose>` / `<Visibility>` / `<Configure>` / `<FocusIn>` の届く順と時刻
- 状態の推移: `wm_state()`・`winfo_viewable()`・`winfo_ismapped()`・`grab_current()`・Win32 の `IsWindowVisible` / `IsIconic`
- modal.py の台帳: `_custody_window`・`_hidden_by_minimize`・`_app_minimized`
- 戻した後のプリセット追加の窓の画面の取り込み（白いままかの判定）

### 範囲の確認

- 入れ子 1 段（App → プリセット管理）でも起きるか・アクションの追加・編集 → プリセット管理 → プリセット追加（3 段）でも起きるか

### 結論のまとめ

- 原因（どの窓に何が届かない / どの処理の順が問題か）・直す範囲・修正案（idea の案 A / B ほか）を
  推奨付きで提示し、ユーザーが選ぶ。grab の預かりの規則を変える必要があれば止めて報告する

## 読むファイル

- `keyseq/presentation/modal.py:1-217`（台帳・預かりと復帰の処理）
- `keyseq/infrastructure/os_backend/windows/backend.py:47-75`（Windows の窓の処理）
- `keyseq/presentation/dialogs/preset_manager.py:67-90, 300-310` / `preset_dialog.py`（再現の窓）
- `tests_ui/test_minimize_grab_custody.py:1-116`（実 App の作り方の手本）
- `instructions/common/spec_detail/features.md:1163-1197`

## 含まない

- コードの修正とテストの追加（task_02）
- 正本・codebase_map の更新・記録（task_03）
- Mac の確認

## 確認

- 計測の結果（イベント列・状態の推移・取り込み画像の判定）を手順 (a)(b) と比較の iconify について記録している
- 自動で再現できない場合は、その旨と、ユーザーの手での再現に切り替えた手順を記録している
- 結論が `ファイルパス:行` と計測の結果の両方で裏付けられている

## 完了条件

- 上記確認を満たし、結論（原因・範囲・修正案）を **reviewer 採用**、修正案をユーザーが選択済み
- 実機目視: 本タスクでは自動の再現で足りなければユーザーに再現の確認を頼む。修正後の目視は task_02

## 結果（2026-11-25 完了）

- 原因・範囲・案の比較は [task01_measurement.md](../task01_measurement.md)。3 段は自動で再現（手での 2 段の再現は白くならず、ユーザーの指摘で 3 段と判明）
- reviewer = 修正して採用（記録の表・コード:行・Tk の版を補完済・task_02 の確認項目を記録へ）
- ユーザー選択 = 案 X（2026-11-24）→ 正本 `features.md` §4.6 へ Windows の例外を追加（`/spec_update`・2026-11-25 承認）
