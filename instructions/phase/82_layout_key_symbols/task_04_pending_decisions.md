# phase 82 task_04 の確認事項（ユーザー判断待ち・2026-11-26）

統合確認は全部 pass（compileall clean・tests 2333 / skip 9・tests_ui 1341・smoke pass・`test_minimize_grab_custody` は全体と単独 3 回とも pass → task_02 の失敗は偶発と確定）。
統合レビュー = deep-reviewer **採用**（高・中なし）/ codex-reviewer 指摘 2 件。以下の 3 点を決めてください。

## 1. Codex 指摘 (2)【P3】レイアウトを切り替えるとキーマップ一覧の複数選択が 1 件に縮む

- 事実（裏取り済み）: task_02 で足した一覧の描き直し（`layout_controller.py:224-225` → `refresh_triggers`）が、末尾で `keymap_panel.refresh_keymap_list_ui(overlap=...)` を選択範囲なしで呼ぶ（`trigger_panel_controller.py:257`）。そのため選択が今のキーマップ 1 件に戻る（`keymap_panel_controller.py:139-141`）。前は、レイアウトを切り替えても `refresh_triggers` を呼ばなかったので、複数選択は残っていた。
- 選択肢:
  - **A（推奨）受容**: 出力シーケンス一覧の選択が「次に実行」へ戻るのと同じく、受容とする（暫定 62 §6 に 1 行足す）。レイアウトの切替はまれな操作で、選び直せば済む。コードは変えない。
  - B 直す: 描き直しの前にキーマップ一覧の選択範囲を取り、`refresh_keymap_list_ui(select=...)` で戻す（`trigger_panel_controller.py:191-199` のトリガー一覧と同じやり方）。枝番のタスク（task_04a）で presentation に数行とテスト。

## 2. Codex 指摘 (1)【P2】key_symbols のキー名の孤立サロゲートで Tk が落ちる

- 実測で**再現しない**（孤立サロゲートを含む文字列を Tk の StringVar に入れても例外は出ない・2026-11-26）。
- **推奨: 除外**（このまま）。

## 3. 正本への反映（task_05）で書く項目（deep-reviewer の T1〜T5）

- T1（中）: `features.md:765` の「使う箇所」に、呼び出し先の表示枠と簡易表示の出力シーケンス欄を足し、`key_symbols` の上書きも書く。
- T2（中）: `features.md:556` のツールチップの「文言が空になったら閉じる」。下敷きがあると、一時メッセージが自動で消えても文言は空にならず警告に替わるので、その挙動を書く。
- T3（低）: `features.md:599-600` の「一時メッセージは 1 行分として測る」に、下敷きも同じと一言足す。
- T4（低）: `codebase_map.md` に新しい API を足す（`KeyboardLayout.key_symbols` / `key_symbols_invalid_reason` / `key_symbol_map`・`_read_key_symbols`・`App.set_flash_underlay`・`LayoutController._refresh_lists_after_layout_change`・`TriggerPanelController._current_key_symbols`）。
- T5（低）: 不正の理由の判定の順（値の型 → キーが空 → 改行）と、空白だけの値が先に書いた同じキーを打ち消すこと。
- **推奨: すべて task_05 に含める**（文書だけの変更）。
- deep-reviewer の L1〜L4（二重の描き直し・枠ごとの dict の生成・`getattr` の書き方・表示名の `[id]`）は低で保留（直さない）を推奨。

## 4. Windows の実機目視

- 手順は `tasks/task_04_integration_and_visual_check.md` の「Windows の実機目視」1〜5。1 を選んだ場合、手順 2 のついでに、キーマップを複数選択してレイアウトを切り替えると 1 件に縮むことも見られる。
