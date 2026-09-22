# decisions_archive/27: 構成セットの読み込み履歴管理（phase 27）

期間: 2026-09-21 〜 2026-09-22（完了）。モード: **暫定仕様先行**（主入力 = `instructions/history/21_keymap_set_load_history.md`・v0.5 で凍結）。
正本の昇格先 = `spec_detail/data_schema.md` **§5.12**（新設）+ §5.4（1 行）/ `features.md` §4.6 / `codebase_map.md`。

---

## 問題

構成セットを開き直す手段がファイル選択ダイアログしかなく、よく使うセットを行き来するのに毎回パスを辿る必要があった。
ユーザー要望（2026-09-21）= 「メニューに『履歴から読み込む』を追加し、直近 20 件 + 分類を折り畳み UI で扱いたい」。

## 現状監査（2026-09-21）

- **`ttk.Treeview` はリポジトリ初採用**（既存 9 ダイアログはすべて `Listbox`）。tkinter に Expander は無く、
  分類＝親 / 履歴＝子のツリーで折り畳みを実現する。Treeview は他ウィジェットのフォント指定が効かず `ttk.Style` が要る。
- **パス指定で構成セットを読む公開入口が無かった**（`load_keymap_set_from` は引数を取らず成否も返さない）。
- `confirm_save_if_dirty` は未保存時に `save_as` を実行し得る＝**読込操作の途中で保存が起き履歴が変わる**。
- ハードコード列挙が **3 つ**（`INTERNAL_MODULE_NAMES` = 実ファイル集合と完全一致を assert /
  `DIALOG_FILES` / **`test_nested_modal_grab.py:262` の `dialog_classes`**。3 つ目は task_04 起票時の洗い出しで発見）。

## 確定した設計判断（ユーザー確定 2026-09-21・一部 09-22）

- **保存先 = 新規 JSON `config/keymap_set_history.json`（固定）**。config.json にキーを増やさない
  （phase 26 で整理した書き込み契機に再び絡めない）。`user/` 配下を避けたのは**参照側の走査ディレクトリ**に
  指定され得るため。候補側は固定 4 ディレクトリで設定不可なので、配置によらず孤児候補にはならない。
- **分類は 1 階層・名前順で自動整列**（推奨の「追加順」ではなくユーザーが名前順を選択）。任意ラベル・読込日時は持たない。
- **記録の契機 = 読込または保存が成功し空でないパスが確定したとき、その実保存先**（2026-09-21 に見直し）。
  当初は「読込成功のみ」だったが、**別名保存が `keymap_set_path` を新パスにする**（`keymap_set_io.py:132`）ため
  「開く動作をしていないのに開いていると認識する」非対称が生じるとのユーザー指摘で変更。
  保存種別で分岐しない（`normalize_keymap_set_save_path` が保存先を書き換えるため「上書きならパスは同じ」が成立しない）。
  **除外** = `app.py:76` の初期代入 / `new_config` / `import_config` / `restore_default`。
- **先頭一致 no-op**（`recent` の先頭が同一パスなら書き込まない・判定は永続化済みの内容）。
  正本 §5.4「起動時に config.json を作らない」との衝突を経路別の例外ではなく共通規則で解消した。
  `loaded_at` は廃止（持つと毎起動で書き換えになる）。
- **起動時の自動読込では記録しない**（**v0.5 改訂・2026-09-22**）。task_03 の実測で、起動時に記録すると
  **App を生成するだけの `tests_ui` 9 モジュールが実 `config/` へ履歴ファイルを書く**ことが判明したため
  （`.gitignore` の `config/` 除外で `git status` に出ず、発見が遅れた）。先頭一致 no-op は維持（無駄書き防止として意味が残る）。
- **破損ファイルは退避してから作り直す**（`keymap_set_history.broken.json` → 連番・**5 で打ち止め**）。
  ユーザー案の `config/quarantine/` は**棚卸しの所有領域**（中身は実行単位 + manifest 前提・正本 §5.4 は
  「隔離未実行の環境に作らない」）のため採らなかった。退避に失敗したセッションは**読み取り専用**。
- **永続化に成功してから UI を確定する** / **履歴の失敗で読込・保存を巻き戻さない** /
  **ダイアログは自分の表示を正とせず、操作のたびに永続化済みの内容を読み直して再描画する**。
- **孤児棚卸しは履歴を参照と見なさない**（走査範囲・孤児判定は不変）。

## 実装上の判断

- **記録は単一の口 `record()`**（`controllers/config_io/keymap_set_history_io.py`）。
  既存 characterization テストが `config_root` に `os.getcwd()` を入れるため、patch 可能にしないと
  **リポジトリルートへ履歴ファイルが生成される**（起票時レビュー H1）。
- **`record()` は境界で例外を握り `(False, 理由)` へ変換する**（task_03 の差し戻し 1 で是正）。
  呼び出し点 3 経路がいずれも既存の `try` の内側にあり、漏らすと
  ①起動経路で**読込済みの構成セットを捨てて空データ起動** ②成功した保存を「保存失敗」と表示
  ③成功した読込を「読込失敗」と表示、になっていた。**reviewer は見逃し、メインの直読みで検出**。
- **パス指定の共通読込入口 `KeymapSetIo.load_keymap_set_path`** を追加（既存 `load_keymap_set_from` の
  try ブロックを移設・文言不変）。メニュー読込と履歴ダイアログの双方がこれを使う。
- **UI の入力方式**（task_04・メイン判断）= 分類名は**インライン Entry**、コピー先だけ別窓
  （`CategoryChooserDialog`。暫定仕様 §5.3 のラベルで「…」が付くのがコピーだけ、という表記に合わせた）。
  **`simpledialog.askstring` は使わない**（`grab_modal` を経由せず、閉じたあと親ダイアログへ grab が戻らない）。
- **task_04 レビュー指摘 2 件 = 修正して採用**: ①ダイアログが `status == "read_only"` と**契約値を
  リテラル複製**（`reviewer` 指摘）→ controller の `is_read_only()` へ集約 ②`copy_to_category` の比較キーが
  `normpath`/`normcase` の**自前実装**（**メインの直読みで検出**・reviewer は挙げず）→ 公開単一点
  `ConfigService.canonical_path` へ委譲。`resolve_config_path` は `abspath` を通さないため厳密には非等価だった。
- **実機目視（2026-09-22）で 2 件**: ①**Escape でダイアログが閉じない** — 診断スクリプトで
  **生成直後の Tk フォーカスが App ルート `.` のまま**と実測。`grab_modal` の直前で `focus_set()` して解消。
  **既存テストは `focus_force()` 後に `event_generate` していて不具合を隠していた**ため、
  フォーカス位置を直接検証するテストを追加。②枠の拡縮が名前列にも及ぶ → 名前列 `stretch=False` /
  パス列 `stretch=True`。**横断適用（`orphan_sweep` 等も同じ欠落）は [idea_26](../../../instructions/backlog/idea_26_dialog_keyboard_focus.md) へ分離**。
- **正本昇格時の判断（task_05）**: 暫定仕様 §9 の保留事項
  「`data_schema/5_08_09_orphan_sweep.md` へ補記するか」→ **補記しない**。
  走査の不完全性 ⑤「keymap_set として解釈できなかった JSON」が既に一般規則として覆っており、
  参照側に `config/` を指定した場合は **`config/config.json` も同じ条件**で、それを個別列挙していないため。

## 実測・レビュー

- 最終実測（task_04 修正後）: compile clean / `tests` **556 OK**（skip 7・**フェーズ通して不変**）/
  `tests_ui` **483 OK**（449 → **+34**）/ smoke OK / **副作用ゼロ**（worktree ルート・`config/` 直下とも
  履歴ファイル未生成・`config.json` の mtime 不変）。
- レビュー: 起票時 `deep-reviewer` → 確定前 `codex-adversarial-reviewer`（指摘 5 件全件採用）→
  各タスク `reviewer` → フェーズ完了判定は `deep-reviewer` + `codex-adversarial-reviewer`。
- 教訓: **レビュアーの「問題なし」は網羅の証明ではない**。①例外ガードの欠落 ②公開単一点の再実装は
  いずれもメインの直読みで見つかった。**設計規則の単一点（公開 API）がある箇所は、実装がそれを
  呼んでいるかを `ファイルパス:行` で確認する**。
- 教訓: **テストが `focus_force()` のような「通してしまう前処理」を挟んでいないか**を疑う。
  緑でも実使用で壊れている経路が残る。

## フェーズ完了判定レビューの採否（2026-09-22・ユーザー判断）

`deep-reviewer`（判定 = 修正要）と `codex-adversarial-reviewer`（needs-attention）の指摘。

**メインが文書で修正（採用）**:

- **H1 = UI・編集の規範条項が正本のどこにも無い**（`deep-reviewer`）。§5.12 はデータと永続化に寄せ、
  `features.md` §4.6 を 1 項目へ圧縮した結果、**同名禁止 / 分類内の重複禁止 / 削除の粒度 /
  不在表示 / 閉じる条件 / 再描画 / 2 列 Treeview とフォント追従**が**コードにしか存在しない**状態だった。
  → **§5.12.7「分類とエントリの編集」を新設**（データ規則）+ **`features.md` §4.6 へ UI の子ビュレット**
  （既存の孤児棚卸し・隔離の管理と同じ書き方）。旧 §5.12.7 は §5.12.8 へ繰り下げ。
- **M2-1 = 退避の連番の表現が実装と逆に読める** → 「退避先は `broken` 〜 `broken5` の**最大 5 個**。
  すべて埋まっていたら退避しない」へ（実装 `keymap_set_history.py:21` と
  `tests/test_config_service.py:2725-2743` が正）。
- **M3 = `current.md` のテスト記載が誤り**（application のテストは `tests/test_config_service.py` 側）。
- **L2 = 「読込以外を無効」は閉じるまで無効に読める** → 「編集操作を無効」へ。
- **L5 = `decisions.md` 索引の refactor_check 表記**を他行と揃えて「不要（根拠）」へ。

**ユーザー判断（2026-09-22）**:

- **【読み取り専用のラッチ】→ 正本を都度判定へ正す**（`deep-reviewer` M2-2 / Codex [medium]）。
  正本 §5.12.5 は「**そのセッション**は書き込みを行わない」と書いていたが、実装は
  `load_history` のたびに判定し直す（`keymap_set_history.py:19-32`）。
  **データ保全の不変条件（壊れたファイルを保全せずに上書きしない）は都度判定でも保たれ**、
  ラッチを入れると一時的なロック・権限エラーのあとアプリを再起動するまで履歴が使えなくなるため、
  **正本の文言を都度判定へ正した**（実装は無変更）。
- **【編集失敗時の再描画】→ 失敗時も再描画する**（`deep-reviewer` M5）。暫定 §6 は「操作のたびに
  読み直して再描画」だが実装は成功時のみ（`keymap_set_history_dialog.py:148-154`）。
  破損退避の直後に編集が拒否されると、ディスクは空なのに一覧が古い内容を表示したまま残る。
  → **task_06 で修正**（`_finish_edit` で成否によらず再描画してから理由を表示）。
- **【未知キー】→ 保持しないことを正本に明記**（`deep-reviewer` M4）。読み手がこのアプリだけで
  `version` も持たない新規ファイルのため、保持の複雑さに見合う利用者がいない。§5.12.2 に 1 行追加。
- **【多重起動時の 2 件】→ 受容**（Codex [high] 退避先の TOCTOU / [medium] 削除時の index 陳腐化）。
  **いずれもアプリの二重起動時のみ成立**する（単一インスタンス内では削除の直前に必ず `_redraw()` が
  入り index は最新。`_copy_entry` はパス指定で index を使わない）。phase 11 で同種の TOCTOU 2 件を
  受容済み（`decisions_archive/11` §3-12-6 / §3-12-7）で、その判断と揃える。

**既知の flaky（テスト側・production の欠陥ではない）**: 完了判定時の実測で `tests_ui` 全体が
3 回中 1 回落ちた（毎回別テスト・いずれも Escape で閉じる経路の `get_hook_pause_count()` が `1 != 0`）。
単体実行は安定。**[idea_18](../../../instructions/backlog/idea_18_escape_delivery_flaky_test.md) の既知症状**で、
今回追加した `tests_ui/test_keymap_set_history_flow.py::test_close_routes_restore_hook_and_parent_grab` も
同じ family に入った（`focus_force()` + `event_generate("<Escape>")` の形）。

## refactor_check（2026-09-22）

**判定 = 不要**（M1〜M6 該当なし。対象 = `keyseq/` の 11 ファイル・+663 / -2 行）。

- **M1 非該当**: 600 行超のファイルはあるが増分が小さい（`config_service/__init__.py` 841 行 = **+10** /
  `keymap_set_io.py` 702 行 = **+15**）。新規は 49〜223 行。
- **M2 非該当**: 80 行超の関数なし（最大でも 26 行）。**M5 非該当**: 申し送り・TODO の新規追加 **0 件**。
- **M3 非該当**: text / dialog / io の 3 層構成は `reference_cleanup` / `orphan_sweep` /
  `quarantine_manage` と同じだが、**中身は別物でコピーではない**（片方を直しても他へ波及しない）。
  構成の踏襲は意図した規約であり、重複ではない。
- **M4 非該当**: `ConfigService` の委譲メソッドは 65 → 68（+3）だが、**フィールド追加のたびに
  全箇所を直す形ではない**（1 行ファサード）。`keymap_set_history_io` の編集 6 メソッドも
  共通ヘルパー `_edit` 経由の薄いラッパー。
- **M6 非該当**: `KEYMAP_SET_LOAD_OK = "ok"` と `contracts.HISTORY_OK = "ok"` は**値が同じだけの
  別概念**（phase 12 の「値の重複を統合しない」判断と同じ理由で統合しない）。
  ただし**履歴ファイル名の語幹が 2 箇所に直値で入っている**
  （`__init__.py:27` の相対パス定数と `keymap_set_history.py:23` の退避先生成）点は
  同値ではないため M6 非該当としつつ、`current.md`「別タスク化候補」の **Phase 27 項**へ送った。

## 残件

- [idea_26](../../../instructions/backlog/idea_26_dialog_keyboard_focus.md) — `orphan_sweep` /
  `quarantine_manage` / `reference_cleanup` も Escape を bind しつつフォーカス未設定（実使用で効かない）。
  既存テストが `focus_force()` で隠している点も含めて横断で直す。
- スコープ外（暫定仕様 §10）= 分類の入れ子 / D&D / 分類 → 分類のコピー / 任意ラベル・読込日時 /
  検索・一括操作 / `*.broken*.json` の管理 UI / `last_used_directory` の復活 / 構成セット以外の履歴。
