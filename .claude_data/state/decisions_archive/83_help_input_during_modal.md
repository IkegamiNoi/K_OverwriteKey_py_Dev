# decisions_archive: phase 83 ダイアログを開いている間にヘルプを操作できるようにする

直接改訂モード（task_01〜02）→ 暫定仕様先行モード（2026-11-26 から・暫定 [63](../../../instructions/history/63_help_follows_front_dialog.md) v0.6・凍結）・JSON スキーマ不変・起票元 idea_60。

要点: 原因 = macOS の Tk 9.1 のローカル grab の間、grab の窓以外の Toplevel にクリックが届かない（Windows は grab の窓の Tk の子なら届く）。対策 = ①macOS だけ、前面のヘルプへ grab を受け渡す（`help/grab_handoff.py`・`WindowBackend.hands_grab_to_active_child_window`）②ヘルプを、いちばん手前のダイアログ（なければ App）の子へ作り直して付け替える（`help_window_controller.py`・`modal.py` の `set_modal_front_listener` / `front_modal` / `last_input` / `resolve_grab_holder`）。付け替えでは状態を引き継ぎ、付け替えのあとダイアログの最後の入力先へ `focus_force` で戻す（このプロセスの窓が前面のときだけ）。Tk 9.1（macOS）はこのヘルプへの `deiconify` で内部が落ちることがあり、表示中は `deiconify` しない・最小化からは作り直して出す・窓のイベントの中で窓の状態を読まない、で回避した。正本 = `features.md` §4.6「ヘルプの窓」の「ダイアログとの関係」・「モーダルダイアログの作法」・`key_input.md`。

## タスクと実装エージェント

- task_01 原因の実測（コード変更なし）・task_02 macOS の grab の受け渡し = fbf2d9bc（中間）・task_02 の実装 = codex-delegating-implementer（子なし）+ メインの軽微修正 1（`test_welcome_window` の前提）・reviewer 採用・実機目視 OK
- 暫定 63 の起票と確定（案 E）・task_03 前提の実測（Mac / Windows）= aa0a3196・c9953b16・7a8ec77d
- task_04 modal.py の口と grab の持ち主の解決 = 7a8ec77d・codex-delegating-implementer（テストを Luna の子へ委譲 = 自己申告）+ メインの軽微修正 2・reviewer 採用
- task_05 ヘルプの付け替え本体 = 8fcee257・codex-delegating-implementer（子 2 = 自己申告）+ メインの修正多数（親が生きている破棄・`App.state` の上書き・スクロール・初期フォーカス・予約し直し・Tk の deiconify のクラッシュ対策）・reviewer 採用（2 回目）
- task_06 統合確認と実機目視・task_06a 統合レビューの採用分 = 8a546f3c・c4e793fe・task_06a = codex-delegating-implementer（子なし）・verifier（Mac・tests 2247 / tests_ui 84 モジュール 1388 件・失敗 0）・reviewer 採用・実機目視 Mac / Windows とも 14 項目 OK
- task_07 正本反映・完了（本記録）= メイン（文書のみ）

## 残存リスク

- 独立したダイアログを開いた順と違う順で閉じると、戻し先が既に閉じていて grab がどこにも戻らない（既存・正本の作法の「戻らない場合 ①」どおり・ヘルプと無関係・Codex 敵対的 1）
- 選択ダイアログ（`choice_dialog`）の Tk の親と前面維持の相手が同じ窓（既存の作り・Codex 敵対的 5）
- メッセージボックス・OS のファイルの窓・カーソルグリッドの編集窓の間はヘルプを操作できない（受容）
- Tk 9.1（macOS）の `deiconify` の不具合への回避（Tk の版が変わると要らなくなる・効かなくなる恐れ）。`<<NotebookTabChanged>>` はその場で窓の状態を読む（task_06a の reviewer の参考 ①・実機の繰り返しの目視では落ちない）
- Cmd+H で App を隠している間の付け替え（`wait_visibility` が戻らない恐れ・deep L5・未実測）/ Welcome の初回のヘルプは付け替えの対象外（deep L1）/ 「最前面に表示」ON のときの重なり（deep L3・目視で問題なし）
- ヘルプの付け替えは作り直しのため、本文の選択範囲・カーソル位置は引き継がない（受容）。閉じるときは一瞬消えて出直す（目視で許容）
- 作り直しで表示を待つ一瞬（`wait_visibility` の間）に `wait_window` を使うダイアログが開くと、そのダイアログを閉じるまでヘルプが付いてこない（Codex 敵対的〔完了判定前〕1・人の操作で重なることはまずない）
- macOS の grab の受け渡しで、持ち主が破棄の途中のとき、ヘルプの破棄で `grab_set` が破棄途中の持ち主へ向かうことがある（実害は小さい・付け替え後に新しい持ち主が grab を持つ・暫定 63 §5）
- probe のため一時的に `defaults write org.python.python ApplePersistenceIgnoreState -bool YES` を入れ、2026-11-28 にユーザーの許可を得て元に戻した。macOS は Python が落ちると次の起動で「ウインドウを再度開きますか？」で止める（画面のロックの間も Tk が止まる）＝ Mac で落ちうる probe を流すときの注意

## 2026-11-26〜 (phase 83: ダイアログを開いている間にヘルプの絞り込み欄へ入力できない)

### 【task_01】原因 = macOS の Tk 9.1 のローカル grab の間、grab の窓以外の Toplevel にクリックが届かない（2026-11-26・実測）
- 素の tkinter でも再現（ダイアログの子・transient の子・App の子のどれも入らない）。Windows は「?」から開いたヘルプを操作でき、ダイアログとも行き来できる（ユーザー確認）。記録 = `instructions/phase/83_help_input_during_modal/task01_measurement.md`
- 正本 `features.md` §4.6「ヘルプの窓」の「ダイアログの「?」がこれを補う」が Mac で成り立っていない（検出基準 A）
### 【task_01】案 A'（Mac だけ「?」から開いたヘルプをダイアログの transient のモーダルにし、閉じたら grab をダイアログへ戻す）→ **除外**（2026-11-26・ユーザーが一度選んだのち保留にし、案 D を選択。ヘルプの間はダイアログを操作できないため）
- 理由: Mac でヘルプを操作できるようになり、モーダルの意味（App 本体を操作できない）を保てる。Windows の今の動き（ダイアログとヘルプの行き来）を変えない
- 案 A（両 OS）→ **除外**: Windows で今できる行き来がなくなる / 案 B（ヘルプの間は grab を外す）→ **除外**: モーダルの意味が崩れる / 案 C（受け入れ）→ **除外**: Mac ではダイアログの間にヘルプを使う手段がない
- 影響範囲: presentation（help の開き方）+ infrastructure（`WindowBackend` に OS の差の 1 メソッド）・正本 `features.md` §4.6 に Mac の例外（`/spec_update`）・直接改訂モードのまま（単一ファイル・タスク 2〜3）
### 【task_01】案 D（Mac で、ヘルプの `<Activate>` で grab をヘルプへ・`<Deactivate>` でダイアログへ戻す）を素の tkinter で実測 → **成り立つ**（2026-11-26）
- 行き来でき、App 本体は操作できないまま。窓を切り替えた直後の 1 回目のクリックは前面にするだけ。`<FocusIn>` を合図にする形は戻れず不可。記録 = task01_measurement.md §8
### 【task_01】Mac の直し方 = 案 D → **採用**（2026-11-26・ユーザー判断）
- 理由: ダイアログとヘルプを行き来でき、App 本体は操作できないまま（モーダルの意味を保つ）。1 回目のクリックが前面にするだけになるのは受容
- 影響範囲: presentation（ヘルプの開き方・grab の受け渡し）+ infrastructure（`WindowBackend` に OS の差の 1 メソッド）・正本 `features.md` §4.6（`/spec_update`）・実アプリとの組み合わせ（入れ子・最小化・フォーカスの戻し・他アプリへの切り替え）は task_02 の最初に確かめる
### 【task_01】正本 `features.md` §4.6「ヘルプの窓」に macOS の例外を追加（2026-11-26・ユーザー承認「その案で改訂」・`/spec_update`）
- 1054 行に例外の注記、「?」の項に grab の受け渡しの条項を追加。ヘルプは transient にしない（Mac で transient の子は親より常に上になり、ダイアログが隠れるおそれ）。transient なしで案 D が成り立つかは task_02 の最初に確かめ、成り立たなければ止めて相談する
### 【task_02 目視の別件】ヘルプを開いたあとに別のダイアログ（`grab_modal`）を開くとヘルプが操作できない（Mac・Windows・2026-11-26 ユーザー報告）→ 案 E **採用**（2026-11-26・ユーザー判断）
- 場面: メニューから開いたヘルプ → アクションの追加 / 「?」から開いたヘルプ → プリセット編集。新しいダイアログの grab の外にヘルプが出るため（Windows は grab の部分木の外・Mac は grab の窓以外）
- 案 E = ヘルプを、いちばん手前のダイアログの子へ作り直して付け替える（状態を引き継ぐ・閉じたら 1 つ前の親へ戻す）。Mac 実測は task01_measurement.md §10（66〜150 ms・状態は保たれる）。目視用の一時スクリプト = `spike/help_follow_spike.py`
- 「閉じる」（親でないダイアログが開いたらヘルプを閉じる）→ **除外**: ヘルプの本文が見えなくなり、戻っても再表示されない / 自動で開き直す（新しい親の子にするだけ）→ 案 E に含む / 別プロセス化・grab を使わないモーダル → **除外**: 規模が見合わない
- 影響: 正本 §4.6「ヘルプの窓」の複数の条項（メニューから開いたヘルプの制限・「?」の項・macOS の例外の相手）。task_02 の受け渡し（相手 = 固定の親）は相手を「その時点の親」に変える
### 【暫定 63 起票】v0.1 → deep-reviewer 修正要（高 3・中 9・低 7）→ v0.2 で反映（2026-11-26）
- 主な反映: 閉じる経路は台帳から外れたあと `after_idle` で持ち主を選び直して作り直す（同期だと入れ子・App の終了中に作った窓が消える = deep の実測）/ 知らせる口 `set_modal_front_listener` は存在の通知のあと・どの return でも通る / 利用者の閉じ（×・Escape・`close()`）に印 / 初期フォーカスを入れない / 新しいヘルプは持ち主のすぐ下（`focus_force` を使わない・正本の作法に合わせる）/ 戻す順 / 本文はコントローラが保持 / カーソルグリッドの編集窓は対象外（確認事項 4 の提案を変更）/ Mac でヘルプが grab を持つ間の新しいダイアログの親・前の持ち主にヘルプを使わない
- 閉じる経路の「破棄後に作り直す」と「持ち主のすぐ下に置く」は未実測 → 実装タスクの最初（A0）
### 【暫定 63】v0.3 の確認事項 1〜4 = 提案どおり確定（2026-11-26・ユーザー）/ Codex 敵対的レビュー needs-attention 7 件 → 推奨どおり v0.4 に反映（2026-11-26・ユーザー）
- 採用: 2（grab の持ち主がヘルプならその親とみなす共通の規則 = grab_modal の前の持ち主・最小化の預かり・_grab_holder）/ 3（窓の消え方を 4 つに分け、新しい窓ができるまで古い窓と控えを残す）/ 4（止めるのは終了の確定後だけ・確認の間は付け替える）/ 6（付け替えはフォーカスに触らない）/ 7（ヘルプは持ち主のすぐ下・隠れたらダイアログを動かす = 受容・正本 1198〜1202 行付近を §9 に追加）
- スコープ外（残存リスク）: 1（非 LIFO で閉じると grab が戻らない = 正本の作法どおりの既存挙動・modal.py:375-387 で裏取り）/ 5（choice_dialog の親と前面維持の相手が同じ = 既存の作り）
### 【task_03】暫定 63 の前提の実測 → フォーカスが奪われる（§11）→ 案 X（持ち主が覚えている入力先へ focus_force で戻す）を実測し有効（§12）→ 暫定 63 v0.5 で §3.6 を改訂（2026-11-27・ユーザー承認「その内容で改訂」）
- v0.5: 付け替え後、表示を待って lower(持ち主) → 持ち主の最後の入力先（開いた直後は grab_modal の初期の入力先）へ focus_force。持ち主が App・App が前面にない・入力先が無いときは戻さない。modal.py が台帳の窓ごとに最後の入力先を覚える。状態を戻している間は控えへ書き込まない。A14 を強化・A15 を追加。正本の作法「開いた時点では…フォーカス強制は行わない」の例外として昇格時に記す
- 代案「フォーカスに触らない（v0.4）」→ **除外**（打った文字がどこにも入らない）/「閉じる」へ戻る → **除外**（ユーザーが案 X を選択）
### 【task_05】Tk 9.1（macOS）の deiconify のクラッシュへの対策 → **採用**（2026-11-27・reviewer 採用）
- 現象: 新しいコントローラで作ったヘルプに `deiconify` すると `WmDeiconifyCmd` → `TkWmMapWindow` で SIGSEGV。落ちる・落ちないが読み出す値の組み合わせで入れ替わる（Tk の内部の不具合とみる・probe で切り分け）
- 対策: 表示中の窓に `deiconify` しない / 最小化・非表示のヘルプを前に出すときは控えから同じ持ち主の子として作り直す（§4.6「最小化を解除して前面へ出す」と同じ見た目）/ 窓の状態の控えは `<Map>` / `<Configure>` の中で読まず `after_idle` で 1 回にまとめる。Windows でも最小化からの復帰は作り直しになる（本文の選択範囲・カーソル位置は失われる = 受容）（→ task_06a で Mac〔aqua〕だけに変更・Windows は `deiconify`）
- 環境: probe のため `defaults write org.python.python ApplePersistenceIgnoreState -bool YES`（ユーザー承認・検証後に許可を取って戻す）
### 【task_06】統合レビュー（deep-reviewer 修正要・codex-reviewer 4 件）→ 推奨どおり採用（2026-11-27・ユーザー「推奨どおり進める」）→ 暫定 63 v0.6・task_06a
- task_06a で直す: H1 / codex P1（付け替えのあとのフォーカスの戻しの判定を「このアプリの窓が前面か」へ・`is_app_foreground` はメイン窓の判定でダイアログの間はいつも偽）/ M1（下に置く・入力先を戻すのは付け替えのときだけ）/ M2 + codex P2（作り始めの持ち主と今の持ち主が違えば成功・失敗とも予約し直す・「?」で明示した親は持ち主が変わらない限り動かさない）/ codex P2（絞り込み・タブ・見出しはその場で控える・窓の位置と状態・スクロールは after_idle）/ codex P3（最小化からの作り直しは成功するまで控えを変えない）/ L2（最小化のテストを本番と同じく transient なしに）/ `tests_ui/test_app_ime_shutdown.py` の仮の App に help を足す（統合の検証のエラー 2）
- 決定: M3 = Tk の deiconify 対策は Mac（aqua）だけ / M4 = App の最小化中は付け替えを待ち元に戻したときに行う / M5 = 最後のダイアログを閉じたあとの入力先は task_06 の目視 11 で決める
- task_07 へ: M6（正本 1155「閉じた後の戻り先は規定しない」の例外）/ M7（④の判定）/ 正本の書き換え箇所の一覧（deep Q2・Q4）/ task_05 の Tk 対策の条項
- 様子見（目視）: L1（Welcome のヘルプ）・L3（最前面 ON のときの重なり）・L5（Cmd+H で隠している間）・L4 は codex P2 の直しに含む
### 【task_06】実機目視 = Mac・Windows とも 14 項目すべて問題なし（2026-11-28・ユーザー）→ M5 = 最後のダイアログを閉じたあとの入力先は今の動きのまま（App 本体へキー入力が届く）で確定・暫定 63 §3.6 に反映
- 2026-11-28: ユーザーの許可を得て `defaults delete org.python.python ApplePersistenceIgnoreState` で Python の設定を元に戻した（元は未設定）
### 【task_07】完了判定前レビュー（deep-reviewer 修正要・Codex 敵対的 needs-attention 4 件）→ 推奨どおり採用（2026-11-28・ユーザー「推奨どおり進める」）
- コード（task_07a・codex-implementer）: Codex 2 = `modal.is_own_process_foreground` は前面の窓が分からないとき（Windows の NULL・macOS の `None`）に真になっていた（`win32_window.py:233`・`macos/window_backend.py:136` は別の用途のための甘い判定）→ `WindowBackend.foreground_own_window()` が `None` でないか（両 OS とも、このプロセスの窓が前面と確かに言えるときだけ値を返す）で判定する / Codex 3・deep 4 = 初回の Welcome のヘルプを前に出すとき表示中でも `deiconify`（`welcome_window.py:174`）→ 表示中は `deiconify` しない・最小化 / 非表示は Windows = `deiconify`・Mac（aqua）= 作り直す（初回の Welcome は控えを持たないのでタブだけ戻す）
- 文書（task_07・メイン）: deep 1（codebase_map の古い行）・deep 2（入力先を戻すのは付け替えのときだけ・新しく開くとき / 最小化から作り直すときは除く）・deep 3（最小化の項の二重記載を参照に縮める）・deep 6（暫定 63 の細目 4 つ = 終了の確認の間も付け替える・入力先が既に無いときは戻さない・本文の読込に失敗した窓の引き継ぐ範囲と最前面 / フォントは作り直した時点・隠れたらダイアログを動かせば出せる / Windows の最前面 ON）・Codex 4（Windows の最前面 ON の例外・持ち主が App なら下に置かない）・deep 7（残存リスクの追加・task_05 の記録の補足）・deep 8（INDEX_done の並び）・deep 5（/refactor_check の記録）
- 残存リスクへ（直さない）: Codex 1 = 作り直しで表示を待つ一瞬（`wait_visibility` の間）に `wait_window` を使うダイアログが開くと、そのダイアログを閉じるまでヘルプが付いてこない（人の操作で重なることはまずなく、作りを大きく変える必要があるため）
- /refactor_check（verifier のメトリクス）: **不要**。M1 該当なし（600 行超は app.py のみで +2・+100 行以上は help_window_controller.py の +222 で 296 行）/ M2 該当なし（grab_modal 88 行は元から・変更 +25）/ M3 該当なし（ログして吸収する try/except の定型）/ M4 該当なし（最小化の判定 3 か所はそれぞれ意味が違う・書き出しと復元は対）/ M5 0 件 / M6 該当なし（"iconic" 等は Tk の固定文字列・既存定数なし）。境界: help_window_controller.py は責務のまとまりが 3 つ以上（付け替え・控え・最小化からの復帰・Tk の対策）で 300 行に近い → 別タスク化候補（`instructions/backlog/deferred_tasks.md`）に 1 行

