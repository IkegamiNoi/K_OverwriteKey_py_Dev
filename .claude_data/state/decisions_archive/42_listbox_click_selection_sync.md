# decisions_archive / phase 42: 一覧のクリックで選択と下線がずれる不具合の修正

対応表: phase 42 / 暫定なし（直接改訂モード・正本の改訂なし）/ decisions 42。起票元: ユーザー要望（2026-10-02・「1 回のクリックで下線だけ移動し、フォーカス〔選択〕が移動しないことがある」）。
完了 2026-10-02。JSON スキーマ変更なし・presentation のみ。地図 = `codebase_map.md` の `listbox_utils.py` の項。

## 確定した設計判断（ユーザー）

| # | 判断 | 採らなかった案と理由 |
|---|---|---|
| 1 | クリック（`<<ListboxSelect>>`）は選択の行を正、キー操作（`<KeyRelease>`）は従来どおり下線の行を正 | すべて選択を正 = 2026-06-21 のキー操作の同期の意図が崩れる |
| 2 | 押している間の `<<ListboxSelect>>` は帯だけ動かし、離したとき `after_idle` で選択の行へ下線を合わせて状態へ反映（完了判定前レビュー） | 押した時点で反映 = ドラッグで途中の行ごとに状態が書き換わる・切替拒否後に離した時点の下線だけずれる |

## 結果（タスク）

| タスク | 内容 | 実装 |
|---|---|---|
| task_01 | `prefer_selection`・3 一覧の入口の分離・テスト・実機目視 OK | codex-implementer |
| task_01a | 押下中の印と離したときの反映（`bind_listbox_click_selection_sync`）・Tk のクラスバインドを通すテスト・実機目視 OK | codex-implementer（既存テストのスタブ 1 行はメイン） |
| task_02 | codebase_map・本アーカイブ・current.md・`/refactor_check` | メイン |

## /refactor_check

- **不要**（M1〜M6 該当なし。対象 7 ファイル・+125 / -14）。`trigger_panel_controller.py` が 606 行（600 超・ただし増分 +25 で M1 非該当）→ 別タスク化候補へ。

## 教訓

- **Tk の標準の挙動（クラスバインドの順序）を `bind Listbox <...>` と `info body ::tk::Listbox*` で実測してから直す**（押下で選択・離しで下線・ドラッグで選択だけ動く）。
- 新しい経路（ドラッグ）で状態が書き換わる副作用は、単一タスクのレビューと実機目視では見えず、完了判定前の上位レビューで見つかった。
- テストは Tk の実際のクラスバインドを `event_generate` で通し、変異検査で検出力を確かめる。

## フェーズ中の判断ログ（decisions.md から移動）

#### 【起票】方針 = ユーザー確定（2026-10-02）
- 原因（Tk 8.6 のクラスバインドで裏取り）: `<1>` で選択 → `<<ListboxSelect>>`、下線（active）は `<ButtonRelease-1>` で後から移る。`listbox_utils.sync_listbox_selection_to_focus` はフォーカスがあると active を正とするため、クリック時に選択を古い下線の行へ戻す。
- 採用: `<<ListboxSelect>>` では選択された行を正 / `<KeyRelease>` では従来どおり下線の行を正（2026-06-21 の同期の意図を保つ）。対象 = トリガー・シーケンス・キーマップ一覧。


#### 【task_02 完了判定前レビュー】deep-reviewer 完了可 / Codex 敵対的 needs-attention（2026-10-02・ユーザー判断 = 推奨どおり）
- deep M1 = Codex Medium（キーマップの切替拒否後、離した時点の `activate @x,y` で下線だけクリックした行へ・以前から）/ deep M2（ドラッグで行ごとに状態が書き換わる・task_01 で新規。Tk の `tk::ListboxMotion` で裏取り）
  → **採用**（task_01a）: 押している間の `<<ListboxSelect>>` は帯だけ動かし、離したとき `after_idle` で選択の行へ下線を合わせて状態へ反映。副次で deep L1（Shift / Ctrl クリック）も解消。
- deep L2（例外時のフォールバック）→ 除外 / L3（テストが Tk のクラスバインドを通していない）→ task_01a のテストで補う。
- `/refactor_check`: 不要（M1〜M6 該当なし）。`trigger_panel_controller.py` 594 行は M1 の基準 600 に近い → 別タスク化候補へ。
- 【task_01a】codex-implementer 実装 → tests 1039 / tests_ui 645（新規 9 件・3 回連続安定）/ smoke pass。既存テストのスタブ 1 行（`on_action_list_mouse_release`）はメインが追加。
  変異検査（押下中の印と離したときの反映を無効化）で拒否・ドラッグ 3 件・Shift クリックの 5 件が落ちる → reviewer 完了可。
  参考指摘（破棄後の `after_idle`〔pack_forget 切替のため稀〕/ 離しが届かない異常系で印が残る / 未使用の引数）→ **受容**（記録のみ）。
