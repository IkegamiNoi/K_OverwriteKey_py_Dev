# Current Phase

このファイルは、現在どのフェーズ定義を読むべきかを示すためのルーティングファイルです。
**完了フェーズの要約はここに蓄積しない**（`.claude_data/state/decisions.md`「アーカイブ索引」+
`decisions_archive/<phase>.md` が正）。**例外は「直近の一連の作業が扱っている領域」の数行のみ**
（「フェーズ完了時の指示」節を参照）。

## 現在の参照先

- **アクティブなフェーズ = [phase 28](28_dialog_keyboard_focus/phase.md)**
  （ダイアログの初期キーボードフォーカス・2026-09-22 起票）。
  主入力 = [暫定仕様 22](../history/22_dialog_keyboard_focus.md)（**v0.4・ユーザー確定済**）。
  起票元 = [idea_26](../backlog/idea_26_dialog_keyboard_focus.md)（主）+
  [idea_18](../backlog/idea_18_escape_delivery_flaky_test.md)（同梱）。
  番号対応: phase 28 / 暫定 22 / decisions 28。
  **確定**: フォーカスの責務を `grab_modal` へ集約（**明示引数**。推測型は実測で反証済）/
  群 C の 5 経路へ **Escape を追加**し正本へ Escape 条項も入れる /
  **フォーカスの復帰はスコープ外**（再現確認のみ）/ 同型スケルトンの共通化は合流させない。
  **進捗: task_01〜04 + task_05b 完了**（`grab_modal` へ `focus` 引数を集約・群 A/A' の 7 経路移行 /
  実 Tk の初期フォーカス検査 / 群 C の 5 経路へ Escape 結線 / **idea_18 解消** /
  検出力補強 M1・M3。`tests_ui` 484 → **504**・一括 green）。
  **task_05（統合確認）は実測・レビュー実施済で実機目視待ち**。
  **スコープ拡大（ユーザー確定 2026-09-23）**: 統合レビューで
  **正本条項「モーダルは Escape でも閉じられる」が群 A 4 経路と矛盾**することが判明し、
  **群 A（action / keymap_edit / preset / trigger）へも Escape を追加**する方針に。
  **Esc に別用途がある間（記録中・取得中）はその用途を優先して閉じない**
  （実現形 = **単一 `<Escape>` ハンドラ + 状態分岐**。Tk の bind 解決順を実測して確定）。
  → 暫定仕様 22 を **v0.5** へ改訂（§2.2 / §3.6 新設・§4 を 3 条項へ・§8-12/13 追加）。
  **次 = v0.5 のユーザー確定 → task_05c（群 A の Escape）→ 統合確認の再実行 → 実機目視 1 回 → task_06**。
- 直前の完了フェーズ = [phase 27](27_keymap_set_load_history/phase.md)（2026-09-22）。
  **それ以前の完了フェーズは `.claude_data/state/decisions.md`「アーカイブ索引」→
  `decisions_archive/<phase>.md` が正**（要約をここへ積まない）。
- **直近の一連の作業が扱っている領域 = 構成セットの読み込み履歴**（phase 27）。
  正本は `data_schema.md` **§5.12「構成セットの読み込み履歴」**（新設）+ §5.4（遅延作成の対象外）/
  `features.md` §4.6 / `codebase_map.md`。
  実装 = `domain/keymap_set_history.py`（規則の純関数）/
  `application/config_service/keymap_set_history.py`（読み書き・退避・記録）/
  `presentation/controllers/config_io/keymap_set_history_io.py`（記録の単一の口 + ダイアログのフロー）/
  `dialogs/keymap_set_history_dialog.py` / `config_io/keymap_set_io.py` の
  **共通読込入口 `load_keymap_set_path`** / `views/menu_bar.py`。
  **記録は読込・保存が成功し空でないパスが確定したときの実保存先**（初期代入 / 新規作成 / Import /
  例の復元 / **起動時の自動読込**は除外）・**先頭一致 no-op** で通常の起動はディスクに触らない・
  **破損ファイルは `*.broken*.json` へ退避**（連番 5 で打ち止め → そのセッションは読み取り専用）・
  **永続化に成功してから UI を確定**する。
  **残件** = ①[idea_26](../backlog/idea_26_dialog_keyboard_focus.md)（ダイアログがキーボードフォーカスを
  取らず Escape が効かない。**テストが `focus_force()` で隠している**点を含む）②暫定仕様 21 §10 の
  スコープ外（分類の入れ子・D&D・検索・`*.broken*.json` の管理 UI）。
  判断は [decisions_archive/27](../../.claude_data/state/decisions_archive/27_keymap_set_load_history.md)。
- 過去のリファクタ計画・提案書は `instructions/modified_proposal/`（**10 まで起票済**・次採番は「次採番」節が正）。
  実施状況と判断は「次採番」節および `decisions.md` の「計画NN」節が正。
  **提案書由来の計画はフェーズ番号を消費していない**。
- テンプレート導入前の経緯・過去仕様は `instructions/history/archive/` を参照（凍結済み）。

## 次採番

- **phase 28 は 2026-09-22 起票・進行中**（`28_dialog_keyboard_focus` / 暫定 22 / decisions 28）。
  次フェーズは **`29_<topic>`**・decisions も **29** を使う（欠番が出た場合はここに明記し、再利用しない）。
  （phase 27 は 2026-09-22 完了 = `27_keymap_set_load_history` / 暫定 21〔凍結〕/ decisions 27〔アーカイブ済〕）
  保存系リデザインの予定: **β=phase 06〔完了〕/ γ=phase 07〔完了〕/ プリセット=phase 08〔完了〕**。
  → **保存系リデザインは一巡完了**。その派生 = **phase 09〔完了〕**（idea_08）。
- 暫定仕様（`instructions/history/NN_<topic>.md`）はフェーズとは**独立採番**。
  04〜21 は起票済（04=α / 05=β / 06=γ〔凍結〕/ 07=プリセット〔凍結〕/
  08=個別プリセット〔**v0.10・凍結**〕/ 09=参照元の掃除〔**v0.5・凍結**〕/
  10=孤児ファイルの棚卸し〔**v0.8・凍結**〕/
  11=config_service の公開面〔**v0.3・凍結**〕/
  12=ネストしたモーダルの grab 復元〔**v0.5・凍結**〕/
  13=ダイアログ後始末の確実な実行〔**v0.4・凍結**〕/
  14=ネストしたダイアログの前面維持〔**v0.5・凍結**〕/
  15=最小化中の grab 預かり〔**v0.7・凍結**〕/
  16=フル表示メイン領域の幅配分〔**v0.5・凍結**〕/
  17=フル表示ヘッダの幅〔**v0.3・凍結**〕/
  18=フル表示の縦方向の最小サイズ〔**v0.5・凍結**〕/
  19=マウスのドラッグ操作〔**v0.5・凍結**〕/
  20=JSON 読込の型不正の扱い統一〔**v0.3・凍結**〕/
  21=構成セットの読み込み履歴〔**v0.5・凍結**〕/
  22=ダイアログの初期キーボードフォーカス〔**v0.4・ユーザー確定済・未凍結**〕）。
  次採番は **`23_<topic>`**。
- リファクタ提案書（`instructions/modified_proposal/NN_*.md`）も独立採番。**10 まで起票済**
  （07 = phase 09 の `/refactor_check` 由来・**実施済＝計画07** / 08 = phase 11 由来・**実施済＝計画08** /
  **09 = phase 13 由来・実施済＝計画10**〔`collect_forbidden_refs` を 100 行 → 26 行へ分割〕/
  **10 = phase 19 由来・実施済＝phase 19 task_07**）・
  次採番は **`11_<topic>`**。**「計画09」は提案書を持たない**（`/spec_split` による正本の分割で、
  規範は `.claude/commands/spec_split.md`。**提案書 09 とは別物**）。

## 次フェーズ候補（参考）

（`instructions/backlog/INDEX.md` の idea から着手候補を 1〜3 件リンクする。
**完了した候補の履歴はここに残さない**〔完了 idea は `backlog/INDEX_done.md` が正〕）

（**idea_26 / idea_18 は phase 28 で着手中**のためここから外した）

- [idea_23](../backlog/idea_23_key_press_release_actions.md)（キーを押す / 離すアクションの追加。
  2026-09-18 ユーザー要望・優先度低）

**保留中**（着手条件つき・トリガーが発生するまで着手しない）: [idea_04](../backlog/idea_04_font_settings_controller.md) /
[idea_06](../backlog/idea_06_individual_json_io_unification.md)。条件は `backlog/INDEX.md` の状態列が正。

## 別タスク化候補

（継続保留、ソース変更を伴う細かい負債。`/refactor_check` からの追記先もここ。
**領域別に並べ、由来フェーズは各項の末尾に括弧で示す**。
idea へ昇格したものはここに残さない〔2026-09-22 に idea_27〜32 を昇格〕）

### ダイアログ・モーダル

- **同型スケルトンの共通化**。`suspend_hook_for_dialog` が **9 ファイル**、
  `bind("<Escape>")` + `protocol("WM_DELETE_WINDOW")` が **4 クラスで完全同型**
  （`keymap_set_history` / `orphan_sweep` / `quarantine_manage` / `reference_cleanup`。2026-09-22 実測）。
  phase 14 で `transient` + `grab_set` は `grab_modal` へ集約済、phase 15 で `destroy()` override は解消済で、
  **残るのはこの 2 種**。**phase 28（idea_26 の案 B）へは合流させないとユーザーが判断済**
  （2026-09-22。フォーカス集約とは別の責務でスコープが倍近くなるため）。
  なお phase 28 の task_03 で**群 C の 5 経路へ Escape を追加する**ため、
  `bind("<Escape>")` + `protocol("WM_DELETE_WINDOW")` の同型箇所は**増える**見込み
  （着手判断はその後に再評価する）（phase 11 / 14 由来）
- `presentation/modal.py`（120 行）で `grab_current()` の try/except と
  `winfo_exists()` / `winfo_viewable()` の try/except が**それぞれ 3 箇所**（M3 の境界）。
  **意図的に意味が違う**ため共通化しない（`grab_modal` は解決不能を「保持者なし」と扱い、
  預かり側は**解決不能と `None` を区別する**〔暫定仕様 15 §3-2(5)〕/ `<Unmap>` は「非表示」、
  他 2 箇所は「生存かつ表示中」）。**4 箇所目が同じ意味で増えたら**判定ヘルパ抽出を再判定（phase 17 由来）
- `dialogs/action_dialog.py` が **418 行**で実装目安 300 行を超過（M1 の 600 行には未達）。
  `ActionDialog.__init__` も **113 行**（既存の巨大関数）。次に増えたら再判定（phase 22 由来）
- `controllers/config_io/child_save_dialog.py` が **369 行**（M1 非該当だが実装目安超過）+
  `_add_text_cell` の戻り値が素の dict（Phase β 由来）

### application / config_service

- `keyseq/application/config_service/__init__.py` が **841 行**（2026-09-22 実測。
  phase 09=734 → 10=767 → 11=828 と増え続けている）。**M1 は「600 行超 かつ +100 行以上」**のため
  近年のフェーズでは非該当だが**分割は保留のまま**。ただし**テストが
  `patch("keyseq.application.config_service.os.path", ntpath)` で名前空間を差し替えるため
  `ConfigService` 本体とパス基盤メソッドを動かせない**制約があり、分割方針の設計判断が別途必要。
  実ロジックを持つのは `relocate_individual_hotkey_presets`（約 40 行）で他はほぼ 1 行委譲
  （phase 09 / 10 / 11 由来）
- 個別 JSON IO の共通化は [idea_06](../backlog/idea_06_individual_json_io_unification.md) が保持
  （**残る着手条件は「共通化の実需」1 つ**）。以下は**その近接領域**としてここで追跡する:
  - `config_io/` の `try/except Exception → messagebox.showerror → return False` が
    **6 ファイル・14 箇所**規模（2026-09-22 実測）。各箇所はメッセージ・保存対象が独立のため M3 非該当に
    倒しているが、さらに増えるなら共通化の再検討対象（phase 08 由来）
  - `controllers/config_io/` の IO クラス骨格（`__init__` + `run_*` → `config_service` 呼び出し →
    `format_*` → `messagebox`）と `presentation/*_text.py` の整形関数が **3 系統目**に達した（phase 11 由来）

### 定数・直値の重複（M6 の境界）

- 履歴ファイル名の語幹が 2 箇所に直値（`config_service/__init__.py:27` の
  `KEYMAP_SET_HISTORY_RELATIVE_PATH = "keymap_set_history.json"` と
  `config_service/keymap_set_history.py:23` の `f"keymap_set_history.broken{suffix}.json"`）。
  **同値ではないため M6 非該当**だが、相対パス定数を変えると退避先の命名だけ黙ってずれる。
  語幹を定数化するか退避先を相対パス定数から導出する（挙動不変の小修正・数行）（phase 27 由来）
- `pane_width_rules.DEFAULT_LIST_CHARS = 26` が**未使用**で、`views/full_view/keymap_box.py:19` /
  `views/full_view/trigger_box.py:20` / `views/compact_view/trigger_box.py:18` が
  `width=26` の直値のまま（**compact 側も同値**。2026-09-22 実測）（phase 18 由来）
- 子カテゴリ列挙（`CHILD_KEYMAP` / `CHILD_TRIGGER_SET` / `CHILD_SEQUENCE`）が 8 ファイルに散在し、
  うち phase 10 の 2 ファイル（`config_service/parent_refs_cleanup.py` /
  `presentation/reference_cleanup_text.py`）は **`save_plan.CHILD_*` を import せず同値の文字列直値**。
  子の種類は仕様上 3 種で固定のため**優先度低**。まとめて触るときはここも対象にする（Phase β / phase 10 由来）
- `KEYBOARD_LAYOUT_COMBO_WIDTH` がボタン文言のモジュール `hook_button_texts.py` に同居
  （使う側は full_view / compact_view の 2 箇所）（phase 19 由来）
- `controllers/hook_controller.py` の `register_hook_buttons` と `apply_fixed_button_widths` の
  幅適用 2 行が同型（軽微）（phase 19 由来）
- `infrastructure/input_gateway.py` の `press_key` / `release_key` の「拡張キー判定 → 分岐」が同型
  （**2 箇所**。M3 の 3 箇所目が出たらヘルパ抽出を再判定する）（phase 21 由来）

### デッドコード・据え置き（実害なし）

- `InputGateway.register_key_hook` の未使用は
  [idea_31](../backlog/idea_31_input_gateway_dead_register_key_hook.md)
- `dirty_tracker.trigger_set_imported` が**読み手不在の残置状態**
  （production は書き込み 3 箇所のみで読むのはテストだけ。2026-09-22 実測）（Phase β 由来）
- `views/full_view/full_view.py:57` の `action_list` alias（`self.action_list = self.sequence_box.action_list`）は
  **据え置き**。`trigger_list` と違い production（`controllers/trigger_panel_controller.py` が
  `app.full_view.action_list` を 13 箇所で使用）の**生きた参照経路**であり、計画04 §1.3-2 の
  「App → View → Widget のパス」を満たす。所有 Widget 経由（`full_view.sequence_box.action_list`）へ
  統一したくなった場合のみ単独タスク化する
  （判断根拠は [decisions_archive/01](../../.claude_data/state/decisions_archive/01_view_ref_cleanup.md)）（phase 01 由来）
- `presentation/app.py:77` の `self.keymap_set_path = self.paths.resolve_keymap_set_path()` と、
  `config_paths.resolve_keymap_set_path()` の**引数なし分岐が実質デッド**
  （起動時に `startup_io` が必ず上書きするため）。`DEFAULT_KEYMAP_SET_FILENAME` を ConfigPaths 側へ
  寄せる代替案も挙動同値のため据え置き。まとめて触りたくなった時のみ単独タスク化する
  （判断根拠は [decisions_archive/05](../../.claude_data/state/decisions_archive/05_keymap_set_new_and_default_dir.md)）（phase 05 由来）
- `controllers/config_io/startup_io.py:19` の `keymap_set_path`（`str(startup.get(...) or "").strip()`）は
  config.json の生値を読むが**presentation 層**のため phase 25 のスコープ外。実害は
  「存在しないパスとして無視される」のみ。あわせて**「空」の定義が字面上非対称**
  （`split_payloads.py:363` の据え置き条件は `.strip()` しない）だが、
  **`entry_loaded=True` かつ値が空白のみ**という組み合わせは 3 経路のいずれからも生成されず**到達不能**
  （config.json を手編集した場合のみ）。触るなら `.strip()` 側へ揃える 1 行修正（phase 25 / 26 由来）
- `to_x` 欠落時に一覧表示が `(100, 200)→(, )` になる（実行はエラーになる）（phase 22 由来）
- `features.md` §4.2（シーケンス実行）から `data_schema.md` §5.11 への参照が無い（発見性のみ）（phase 22 由来）

### テスト負債

- `grab_modal` の静的検査の発見ベース化は
  [idea_32](../backlog/idea_32_grab_modal_static_check_discovery.md)
- `tests/test_input_gateway_drag.py::test_initial_move_failure_restores` が `mouseUp` の
  **非呼び出し**を固定していない / ドラッグ 4 キーの**ファイル層での永続化往復**テストが無い（phase 22 由来）
- `tests_ui/test_full_view_header_width.py` / `test_header_button_widths.py` は保存予約の遅延を
  延ばしていない（現状は予約取消で実害なし・揺れたら phase 19 task_03 と同じ対処）（phase 19 由来）
- Escape 依存テストの不安定（負荷下で 5 件が連鎖して落ちる）は
  [idea_18](../backlog/idea_18_escape_delivery_flaky_test.md)

### レビュー保留（判断待ち・判断は decisions_archive が正）

- phase 18 完了判定前レビューの保留 3 件（ドラッグで元の希望幅へ戻したとき最小幅が更新されない場合 /
  `pane_measure.py` の SequenceBox 構造依存 / phase 18 以前の tests_ui が実 config を読む）。
  判断は [decisions_archive/18](../../.claude_data/state/decisions_archive/18_full_view_resizable_panes.md)
- 一時メッセージのラベルを App 属性で直接参照する案（phase 01 の「生やし」解消と衝突）。
  判断は [decisions_archive/20](../../.claude_data/state/decisions_archive/20_full_view_min_height.md)
- `controllers/pane_layout/pane_layout_controller.py` は **281 行**でドラッグ・レイアウト適用・
  ウィンドウ幅の保存の 3 まとまりを持つ。phase 20 で「高さの処理は独立したまとまりではない」として
  **分割不要と再判定済**。次にまとまりが増えたら再判定する（phase 18 / 20 由来）

## 作業開始時の指示

Claude は作業開始時に、このファイルで指定された参照先の `phase.md` を必ず読んでください。
次フェーズ未確定時はユーザーに方針確認すること。

## フェーズ完了時の指示

- 正本反映タスクの完了後、フェーズを完了扱いにする前に `/refactor_check`
  （`.claude/commands/refactor_check.md`）を実行し、リファクタ要否の判定結果を完了報告に含めること。
- フェーズ完了時は本ファイルの「現在の参照先」を差し替える。**完了フェーズはリンクのみを残し、
  要約は書かない**（要約は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正）。
  代わりに「**直近の一連の作業が扱っている領域**」を数行で置き、**いま何の続きを見ているのか**と
  **その領域の残件**が分かるようにする（2026-09-08 のユーザー判断。過去フェーズの要約を並べない）。

起票元 idea があるフェーズは、`instructions/backlog/INDEX.md` の該当行を完了 / クローズ状態に
更新して `instructions/backlog/INDEX_done.md` へ移動すること
（チェックリストは `.claude/rules/task_execution.md`「フェーズ完了時」）。

## 新フェーズ作成時の更新ルール

新しいフェーズ用フォルダを作成した場合は、`## 現在の参照先` を新フェーズの `phase.md` に更新してください。
フォルダ名は `instructions/phase/` 直下で**連番プレフィックス付き**（`NN_<topic>`）にしてください。
起票手順は `/phase_start`（`.claude/commands/phase_start.md`）に従うこと。

## 注意

このファイルには、実装順序・タスク詳細・チェック内容・完了フェーズの経緯を書かないでください
（**「直近の一連の作業が扱っている領域」の数行だけは例外**。「フェーズ完了時の指示」節を参照）。
それらは各フェーズフォルダ内の `phase.md` および `decisions_archive/<phase>.md` に記載してください。
