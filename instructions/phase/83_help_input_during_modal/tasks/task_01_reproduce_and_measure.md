# task_01_reproduce_and_measure

## 目的

ダイアログ（モーダル）を開いている間にヘルプを開くと、絞り込み欄にカーソルが入らない
（[idea_60](../../../backlog/idea_60_help_input_during_modal.md)）。この原因を実測で特定し、直し方の案を出してユーザーが選ぶ。
**コード変更なし**（計測用の一時スクリプトは scratchpad に置き、リポジトリへ入れない）。
関連する正本 = `features.md` §4.6「ヘルプの窓」（1049 行〜）・「モーダルダイアログの作法」（1138 行〜）・`key_input.md` 28〜29 行。

## 対象範囲（実測のみ・コード変更なし）

### 素の tkinter の最小構成（Mac）

- grab_set した Toplevel D（App が transient の親）を置き、次の 3 つの窓の Entry にクリックで入力できるかを確かめる
  - (a) D を master にした Toplevel（transient なし）= 「?」の経路と同じ作り
  - (b) (a) に `transient(D)` を付けたもの
  - (c) App を master にした Toplevel = メニューの経路と同じ作り
- 記録: Entry の `<FocusIn>` / `<KeyPress>` の届き方・`focus_get()`・`grab_current()`

### 実機（Mac）

- 実 App でダイアログを 1 つ開き、「?」でヘルプを開いて絞り込み欄をクリックして文字を打つ
- ダイアログを開いたまま、メニューの「使い方」から開いたヘルプでも同じことを試す（メニューを操作できるかも記録する）
- 入れ子のダイアログ（2 段）の「?」でも試す
- 取れれば `focus_get()`・`grab_current()` の推移を記録する（`modal.py` の `_restore_modal_focus` が動いたかも見る）

### Windows

- 同じ手順を書いてユーザーへ渡し、結果を受け取る（自動の計測はしない）

### 結論のまとめ

- 候補 ①（`modal.py` のフォーカス戻し）・②（macOS で transient でない子の窓）・③（メニュー経由）のどれか、あるいは別の原因かを特定する
- 直し方の案（idea の案 A / B / C ほか）を推奨付きで出し、仕様変更の要否も添えてユーザーが選ぶ
- 記録は `instructions/phase/83_help_input_during_modal/task01_measurement.md` に置く

## 読むファイル

- `keyseq/presentation/help/help_button.py` / `help_window_controller.py` / `help_window.py:1-140`
- `keyseq/presentation/modal.py:57-90, 276-370`（フォーカスの戻し・grab_modal）
- `keyseq/presentation/views/menu_bar.py:75-85`（メニューの経路）
- `tests_ui/test_dialog_help_buttons.py`（実 App とダイアログの作り方の手本）
- `instructions/common/spec_detail/features.md:1049-1082, 1138-1221`

## 含まない

- コードの修正とテストの追加（task_02 以降。方針の決定後に起票）
- 正本・codebase_map の更新・記録（最終タスク）

## 確認

- (a)(b)(c) と実機の各経路について、入力できたか・フォーカスの届き方を記録している
- Windows の結果（ユーザーの報告）を記録しているか、未報告ならその旨を明記している
- 結論が `ファイルパス:行` と計測の結果の両方で裏付けられている

## 完了条件

- 上記確認を満たし、結論（原因・案）を **reviewer 採用**、案をユーザーが選択済み
- 実機目視: Mac は本タスクで実測（自動で足りなければユーザーに確認を頼む）。Windows はユーザー。修正後の目視は task_02 以降

## 結果（2026-11-26・Mac の実測まで）

- 原因・案の比較は [task01_measurement.md](../task01_measurement.md)。Mac（Tk 9.1）ではローカル grab の間、grab の窓以外の Toplevel にクリックが届かない（素の tkinter でも再現）。入れ子のダイアログの実測は未実施
- reviewer = 修正して採用（入れ子の未実施の明記・結論の言い過ぎの修正・task_02 への引き継ぎを記録へ反映済み）
- Windows（2026-11-26・ユーザー）: 「?」から開いたヘルプは操作でき、ダイアログとも行き来できる → 問題は Mac だけ
- 案 D（前面の窓へ grab を移す）を追加で実測（§8・成り立つ）
- ユーザー選択 = 案 D（2026-11-26）→ 正本 `features.md` §4.6 へ macOS の例外を追加（`/spec_update`）
