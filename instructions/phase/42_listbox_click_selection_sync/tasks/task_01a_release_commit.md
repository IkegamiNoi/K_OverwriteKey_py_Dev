# task_01a_release_commit

## 目的

phase 42 の完了判定前レビュー（deep-reviewer 完了可・M1/M2 / Codex 敵対的 needs-attention）で採用した修正（ユーザー判断 2026-10-02・推奨どおり）。
「マウスで押している間は選択の帯だけ動かし、ボタンを離したときに選択の行へ下線を合わせてアプリ側の状態へ反映する」。presentation のみ。

- A（deep M1・Codex Medium）: キーマップの切替が拒否されたとき、離した時点の Tk の `activate @x,y` で下線だけクリックした行へ移り、選択（アクティブな行）とずれたまま残る。
- B（deep M2・task_01 で新しく生じた）: ドラッグで行をまたぐたびに `<<ListboxSelect>>`（Tk の `tk::ListboxMotion`・browse）が出て、アプリ側の状態がそのたびに書き換わる
  （キーマップ一覧では元の行へ戻しても一時停止中のものが捨てられる・シーケンス一覧ではループの位置が失われる）。
- 副次: deep L1（Shift / Ctrl を押しながらのクリックで下線だけ動く・以前から）も、離したときに揃う。

## 対象範囲

- 3 つの一覧（トリガー〔フル・省略〕・シーケンス・キーマップ）で:
  - **一覧自体に付けるバインド**（クラスのバインドより先に動く）で押下中の印を管理する: `<ButtonPress-1>` で印を立てる / `<ButtonRelease-1>` で印を下ろし、`after_idle` で「離したときの同期」を予約する
    （Tk のクラスの `<ButtonRelease-1>` の `activate @x,y` の後に走らせるため）。
  - **押下中の `<<ListboxSelect>>`**: 選択の帯の移動だけにして、アプリ側の状態（トリガーの選択 index・シーケンスの実行位置・アクティブなキーマップ）は変えない。
  - **離したときの同期**: 選択の行を正として下線を合わせ（`listbox_utils.sync_listbox_selection_to_focus(..., prefer_selection=True)`）、その行でアプリ側の状態へ反映する（task_01 の `<<ListboxSelect>>` の処理と同じ）。
    切替が拒否された場合は選択がアクティブな行に戻っているので、下線もそこへ戻り、状態は変わらない。
  - 押下中でない `<<ListboxSelect>>`（キーボード由来など）と `<KeyRelease>` は task_01 のまま。
- 押下中の印と予約の管理は `listbox_utils.py` などに小さくまとめてよい（3 つの一覧で同じ形をコピーしない）。予約した `after_idle` は、一覧が破棄されていたら何もしない。
- **守ること**: シーケンス一覧の `_programmatic_action_select` の抑止と「同じ行なら何もしない」（位置が実際に変わったときだけ `reset_loop_frames`）・task_01 のキー操作の同期・ダブルクリックの編集対象。

## テスト（追加・修正まで。実行は依頼しない）

- Tk の実際のクラスバインドを通す（`event_generate("<ButtonPress-1>", x=, y=)` → 必要なら `<B1-Motion>` → `<ButtonRelease-1>` → `update()` で `after_idle` を流す。座標は `bbox` から求める）。
- 3 つの一覧で: 1 回のクリックで選択・下線・アプリ側の状態が揃う（task_01 のテストの置き換え・強化）。
- キーマップ一覧: 切替が拒否される状態（連続実行中を `can_switch_keymap` 等で再現）で別の行をクリック → 離した後も選択・下線・アクティブなキーマップがすべて元の行。
- ドラッグ: 行 A を押して行 B を経由して行 C で離す → 状態の反映は C の 1 回だけ（途中の B で `activate_keymap_by_id` / `reset_loop_frames` が呼ばれない）。A に戻して離したら状態は変わらない。
- Shift を押しながらのクリックで、離した後に選択と下線が揃う（L1）。
- 修正前（task_01 の状態）のコードで、拒否とドラッグのテストが落ちる形にする。

## 読むファイル

- phase.md「このフェーズで読むファイル」1〜4 / `tests_ui/test_listbox_click_selection_sync.py`（task_01 のテスト）
- `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py` の `activate_keymap_by_id`・`refresh_keymap_list_ui`（拒否時に選択を戻す処理）

## 含まない

- 選択モードの変更（browse のまま）/ ダイアログ内の Listbox / 文書（メイン）
