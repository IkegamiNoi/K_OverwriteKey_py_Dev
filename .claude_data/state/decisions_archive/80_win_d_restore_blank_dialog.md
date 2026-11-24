# decisions_archive: phase 80 Win+D から戻したときに入れ子のダイアログが白いまま

直接改訂モード（暫定なし・正本 `features.md` §4.6「モーダルダイアログの作法」の最小化の項に **例外（Windows）** を追加）・JSON スキーマ不変・2026-11-25 完了。起票元 = [idea_61](../../../instructions/backlog/idea_61_win_d_restore_blank_dialog.md)。

要点: 白くなるのは Win+D に固有ではなく、**Tk 8.6.15（Windows）で transient を 3 段以上つないだ窓**（App → アクションの追加・編集 → プリセット管理 → プリセット追加 / 上書き確認）が App の最小化 → 復元で中身の HWND を失うため（素の tkinter でも再現・機構は未特定・記録 = [task01_measurement.md](../../../instructions/phase/80_win_d_restore_blank_dialog/task01_measurement.md)）。
Windows では `modal.py` が最小化の間だけ深さ 3 以上のモーダルの transient を外して隠し、復元で開いた順に表示し直して grab を戻した 300ms 後に付け直す（付け直しで withdrawn なら表示し直す）。OS の差は `WindowBackend.detaches_deep_transients_during_minimize`（Windows = True / macOS = False）。変更レイヤ = presentation（`modal.py`）+ infrastructure（os_backend の窓の契約と 2 実装に 1 メソッドずつ）。

## タスクと実装エージェント

- task_01 再現と原因の実測 27b48e9d = メイン（計測スクリプトは scratchpad の一時物）・reviewer 修正して採用・案 X をユーザー選択 → `/spec_update`（ユーザー承認）。
- task_02 切り離しと付け直し bc40c7c3・9ecfced8 = codex-implementer（Luna high）+ メイン修正 2 点・reviewer 採用（M1 修正済）・Windows 目視 OK（ユーザー）。
- task_02a 完了判定前レビューの採用 4 点 ac0167eb = codex-implementer（Luna high）+ メイン修正 2 点・reviewer 採用。
- task_03 記録・完了（本記録）: tests 2282（skip 9）/ tests_ui 1330 / smoke pass（verifier・task_02a 時点）。refactor_check = 不要。


### 【task_01】原因 = Tk（8.6.15・Windows）で transient を 3 段以上つないだ窓が、最小化からの復元で中身の HWND を失う（2026-11-24・実測）
- Win+D に固有ではない（iconify・タスクバーでも起きる）。2 段では起きない。keyseq の預かり（modal.py）は原因ではない。描き直しでは直らない。記録は `instructions/phase/80_win_d_restore_blank_dialog/task01_measurement.md`

### 【task_01】案 X（最小化の間だけ 3 段目以降の transient を外して隠し、復元で表示し直してから付け直す）→ **採用**（2026-11-24・ユーザー判断）
- 理由: 白くなる症状が実測で消える（X-4 = 先に表示して grab を戻し、遅らせて付け直し、withdrawn なら表示し直す・12/12）。正本の例外を Windows の 3 段目以降に限れる
- 案 Y（3 段目以降の transient を App にする）→ **除外**: 前面維持（§4.6・phase 14/16）の退行の恐れ / 案 Z（記録のみ）→ **除外**: 普段の操作で毎回白くなる
- 影響範囲: `modal.py` の最小化の処理（Windows・OS バックエンド経由）・tests_ui。付け直しで withdrawn になる機構と待ち時間の最小値は未解明（task_02 で確認）

### 【spec_update】features.md §4.6「復元の際、アプリは窓を表示し直さない」に Windows の 3 段目以降の例外を追加（2026-11-25・ユーザー承認）
- 文言はユーザー承認のとおり（前面維持の指定を戻すまでの短い間は前後が入れ替わりうる・最小化の間に閉じた窓には何もしない）。サンプル・JSON の変更なし

### 【task_02】メインの追加修正 2 点（再最小化で記録済みの窓も隠し直す / 隠した窓を開いた順に並べる = reviewer M1）・Windows 目視 OK（2026-11-25）
- タイトルバーの最小化は grab 中に押せず実施不可（既存）。上書き確認の前の OS 標準のファイルの選択が前面だと Win+D で隠れない件 → **保留**（正本の保証の範囲外・ユーザー判断で修正せず idea_67 で確認として残す）

### 【task_03 完了判定前レビュー】deep-reviewer 修正要（軽微）/ codex-adversarial-reviewer needs-attention（medium 2）の採否（2026-11-25・ユーザー判断「推奨どおり」）
- Codex 1（3 段目を外した後に 4 段目の深さが測れない）・deep 3（付け直しの予約の上書きと最小化中の実行）・deep 4（復元後のフォーカスのテスト）・deep 7（契約テスト）→ **採用**（task_02a）
- deep 1（正本の理由の文「外したままだと」は逆 →「外さないと」）→ **採用**（正本を修正）
- deep 2・5・6・11（記録の不足）→ **採用**（task_03）
- Codex 2（付け直し後の表示・grab・フォーカスの再検証）・deep 8（付け直しで withdrawn になる理由の仮説）・deep 9（最小化の間に開いた深い窓）・deep 10（重複の整理）→ **保留**（残存リスクとして記録・deep 10 は refactor_check で判断）

### 【task_03】記録の補い（deep 5・6・11）
- 上書き確認の窓そのものでの目視は**未実施**（その前の OS 標準のファイルの選択の段で Win+D が効かず、上書き確認まで進めなかった。自動テストはプリセット追加と 4 段の経路）
- 付け直すまでの約 300ms にタスクバーへ別の窓として出ないか・前後の入れ替わり・ちらつきは、目視で問題の報告は無いが**個別には観察していない**
- 変更レイヤは presentation のみではなく、infrastructure（os_backend の窓の契約と Windows・macOS の実装）にも 1 メソッドずつ

### 【task_03】refactor_check（メイン実測・PHASE_BASE 3f4ef40b・keyseq 4 ファイル +95 −2）
- M1 = `modal.py` 391 行（600 行未満）/ M2 = 新規関数は最大 28 行（`_detach_deep_transients`）/ M3 = `_transient_depth` と `_belongs_to_app` の同型は 2 か所で非該当（current.md「別タスク化候補」へ 1 行）/ M4・M5（0 件）・M6 = 該当なし → **不要**

## 残存リスク（保留の指摘を含む）

- 付け直しで withdrawn になる機構は未解明（iconify の経路でだけ起きる。deep 8 の仮説 = Tk の `wm transient` は親が表示されていなければ子を withdraw・表示中なら窓枠を作り直す。未確認）。待ち 300ms の最小値は未検証。Tk の版が上がると回避が効かない・余計になる恐れ
- 付け直した後に表示・grab・フォーカスを測り直す仕組みは無い（Codex 2・保留）。シェルの復元が遅れる環境で競合しうる
- 最小化の間に開いた深さ 3 以上のモーダルは外さない（deep 9・現状そのように開く経路は無い）
- Mac では新しいテストを未実行（Mac は False で挙動不変）
