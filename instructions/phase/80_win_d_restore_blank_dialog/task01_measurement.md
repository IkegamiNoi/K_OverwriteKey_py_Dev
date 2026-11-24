# task01_measurement.md — 再現と原因の実測（2026-11-24・Windows 11・Python 3.14 の .venv・Tk 8.6.15〔配布物と同じ〕）

計測スクリプトは scratchpad の一時物（リポジトリへ入れない）。実 App を `tests_ui/test_minimize_grab_custody.py` と同じ作り方で起こし、
窓ごとのイベント・状態・modal.py の台帳を 50ms ごとに記録した。

## 再現の条件

- **transient を 3 段以上つないだ窓が、App の最小化 → 復元で中身の HWND（`winfo_id`）を失う**。窓枠（`wm_frame`）は入れ子の窓すべてで別の HWND に作り直され、3 段目以降だけ中身の HWND が破棄される（`IsWindow=0`）。
- 3 段になる経路（コード）:
  - App → アクションの追加・編集 → プリセット管理（`action_dialog.py:669` `transient_parent=self` → `preset_manager.py:88` の `grab_modal`）→ **プリセット追加 / 編集**（`preset_manager.py:303`・`:334` → `preset_dialog.py:45` `grab_modal(self, parent)`）
  - 同じくプリセット管理 → **上書き確認**（`preset_manager.py:401` `transient_parent=self`）
- **Win+D に固有ではない**。idea_61 起票時に iconify で再現しなかったのは 2 段で試したため。

### 段数 × 戻し方（3 段目 = 最内の窓・取り込みの白の割合は隠す前 0.27〜0.28）

| 段数（経路） | iconify → deiconify | Win+D → ShowWindow(SW_RESTORE)（タスクバー相当） | Win+D 2 回 | ユーザーのタスクバーのクリック |
|---|---|---|---|---|
| 1（App → 管理） | 中身あり | — | — | — |
| 2（App → 管理 → 追加） | 中身あり・白 0.27 | 中身あり・白 0.27 | 中身あり・白 0.28 | 白くならない（目視） |
| **3（App → アクション → 管理 → 追加）** | **白 1.00** | **白 1.00・`IsWindow=0`** | **白 1.00（5/5）** | **白くなる（ユーザーの普段の目視）** |

3 段・Win+D → SW_RESTORE の記録（抜粋）: 戻すと App の `<Map>` の後に追加の窓で `<Unmap>`/`<Map>` が繰り返し届き、
管理・アクション・App には `<Expose>` が届くが**追加には届かない**。台帳は `_custody_window` = 追加 → 復帰後 None（grab は追加へ戻る）・`_hidden_by_minimize` は空のまま（Windows では入れ子の窓が既に viewable=0 のため `modal.py:112-117` の withdraw は走らない）。

## 原因

- **Tk（8.6.15・Windows）の挙動。機構は未特定**。素の tkinter（keyseq 不使用）でも同じ: root ← T1 ← T2 ← T3 の transient の連鎖で T3（4 段なら T3・T4）の中身の HWND が破棄される。
  2 段・全員を root の transient にした形・3 段目だけ root の transient にした形では起きない。Tk の親（master）と transient の食い違いは無関係。
- **keyseq の最小化の預かりは原因ではない**: `modal.py:136` `_take_custody` と `:151` `_return_custody` を何もしない関数に差し替えても再現する（これで `_deferred_check`〔`:100`〕・`_deferred_return`〔`:166`〕・`_return_grab`〔`:190`〕も走らない。Windows の `install_minimize_preparation`〔`windows/backend.py:54`〕は何もしない）。
- 中身の HWND が無いため、描き直し（`RedrawWindow`・`update_idletasks`・`event_generate("<Expose>")`）では直らない（3 つとも白のまま。`RedrawWindow` は中身の HWND に対して失敗）。

## 回避の候補（実測）

| 案 | 内容 | 結果 | 正本との関係 |
|---|---|---|---|
| X | 最小化の間だけ 3 段目以降の transient を外して withdraw し、復元で transient を付け直して表示し直す（`modal.py` の `_deferred_check` / `_deferred_return` に差し込み） | iconify・タスクバー相当では中身が残る。Win+D 2 回で 17 回中 3 回、プリセット管理が withdrawn のまま残る（下の X-1） | §4.6「復元の際、アプリは窓を表示し直したり前面へ持ち上げたりしない」（`features.md:1168`）に反する → 仕様変更（Windows の 3 段目以降の例外）。なお既存の `modal.py:112-113`（withdraw）・`:172-176`（deiconify）は、最小化で隠れなかった窓を既に表示し直している（Mac の経路） |
| Y | 3 段目以降を作るとき transient を App（または 1 段目）にする | 素の tkinter では起きない形 | §4.6「ネストして開いた子は呼び出し元より前面に留まる」（`features.md:1156-1159`）に反する・前面維持の退行の恐れ（phase 14） |
| — | 自分で withdraw するだけ / 2 段目から外す | 防げない（4 段で破棄） | — |
| Z | 直さず既知の制限として記録 | — | 仕様変更なし |

## ユーザーの選択（2026-11-24）= 案 X

### 案 X の付け直しの時機（追加の実測・3 段）

| 手順 | 結果 |
|---|---|
| X-1: 復元で transient を付け直してから表示し直す | Win+D 2 回で 17 回中 3 回、プリセット管理が withdrawn のまま（付け直しの直後に管理へ `<Unmap>`） |
| X-2: X-1 の前に、他のモーダルが表示されるのを待つ | 悪化（15 回中 13 回）。待つ判定はすぐ成立し、付け直しの後に管理が隠れる |
| X-3: 先に transient なしで表示し直して grab を戻し、300ms 後に付け直す | Win+D 2 回は 10/10 成功（待ち 0ms でも 5/5）。iconify の経路では付け直しの直後に追加が withdrawn になる（3/3） |
| **X-4: X-3 + 付け直しで withdrawn になったら表示し直す** | **iconify・Win+D → タスクバー相当・Win+D 2 回 × 各 4 回 = 12/12 成功**（中身の HWND が残る・白くない・3 枚とも normal・grab は最内） |

- X-4 の「withdrawn になったら表示し直す」は症状への後追いの対処で、付け直しで withdrawn になる**機構は未解明**（iconify の経路でだけ起きる）。標本は 12 回と小さい。待ち 300ms の最小値も未検証。

## task_02 で確かめること（reviewer 指摘の取り込み）

- 対象の判定は transient の連鎖を辿って深さ 3 以上（上書き確認・4 段も対象）。Windows 限定で、OS の差は OS バックエンド経由に置く（modal.py に Windows 固有の分岐を直書きしない）
- 4 段・タスクバーの実クリック（ユーザーの目視）・付け直すまでの間の前後関係とちらつき・タスクバーに別の窓として出ないか
- 正本 §4.6 の他の条項との組み合わせ: 前面維持（`features.md:1156-1159`）・grab の戻し先と「別の窓が既にモーダルなら奪わない」（`:1163-1171`）・最小化の間に内側を閉じた / 開いた（`:1172-1173`・phase 17 の tests_ui A9・A10 系。外した窓が閉じられたら付け直さない）・フォーカスの復帰と強制アクティブ化・最小化の間に開いたモーダル（`:1174-1185`）・キーボード表示ウィンドウ（`:1186-1190`）
- 待ち時間は固定値だけでなく状態の確認と併用できるか（X-2 の失敗を踏まえる）
