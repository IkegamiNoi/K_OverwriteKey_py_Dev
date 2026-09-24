# phase.md

## フェーズ名

grab_modal の静的検査の発見ベース化（grab_modal_static_check_discovery）

## フェーズの目的

`tests_ui/test_nested_modal_grab.py:260` の `test_grab_modal_is_last_initialization_statement` は、
検査対象を**ハードコードの列挙**（`dialogs/` 10 クラス + `controllers/config_io/` 3 ファイル）で持つため、
列挙に足し忘れたダイアログを素通りする。**既に 1 件素通りしている**
（`dialogs/keymap_set_history_dialog.py:195` の `CategoryChooserDialog`・phase 27 で追加・`grab_modal` は :212）。
対象の**発見を走査**へ寄せ、新規ダイアログが自動で検査対象に入るようにする。
**`grab_modal` の呼び出しが消えた**ことの検出（件数アサート）は失わない。

**tests_ui 限定・production 不変・JSON スキーマ不変・正本（spec_detail）の改訂なし**。
検査する規約（`codebase_map.md:342-345`「呼び出しは初期化の最後の文」）そのものは変えない・緩めない。

- 起票元: [idea_32](../../backlog/idea_32_grab_modal_static_check_discovery.md)（phase 14 の `/refactor_check`〔deep-reviewer M-6〕から分離）。
- 主入力（暫定仕様）: なし（直接改訂モード。正本の改訂も無い）。
- モード: **直接改訂モード**。番号対応: phase 33 / 暫定 なし / decisions 33。

## 確定（ユーザー 2026-09-24）

- **案 A'（継承で発見）**を採る。
  - 系統 A: `dialogs/` 配下で **`Toplevel` を継承するクラス**を走査で発見し、各クラスに既存の
    「`__init__` 内で `grab_modal` はちょうど 1 回」「`__init__` の最後の文」を課す。
    **発見条件を「`grab_modal` を呼んでいること」にしない**（呼び出しが消えたクラスが対象から外れて素通りするため）。
    発見が 0 件で素通りしないよう**件数の下限**もアサートする。
  - 系統 B: `controllers/config_io/` 配下で **`grab_modal` を呼ぶファイルの集合**が期待件数の辞書のキーと
    一致することを確かめ、件数の期待値（`child_save_dialog.py`=2 / `io_dialogs.py`=1 / `hotkey_presets_io.py`=1）は据え置く。
  - 案 B（発見のみ・消失検出を失う）/ 案 C（列挙据え置き + 足し忘れ検出のみ）は採らない。
- **phase 15 側の静的検査**（`tests_ui/test_dialog_teardown_flows.py:18` の `DIALOG_FILES`・フック停止）は**対象外・別フェーズも立てない**。
  守る約束が「トップレベルのダイアログはフックを止める」で、ネストした子（`PresetDialog` / `CategoryChooserDialog`）は
  意図的に止めないため、構文からは対象を判別できず、発見ベースにしても「止め忘れ」は検出できない。
  **既知の限界として decisions_archive/33 に理由を残す**のみ（idea 起票もしない）。

## スコープ

### 含む

- `tests_ui/test_nested_modal_grab.py` の `test_grab_modal_is_last_initialization_statement` の書き換え
  （系統 A・系統 B の発見ベース化。検査内容〔最後の文 / 初期化関数または try の直下 / 直後は待機だけ〕は不変）。
- `keyseq/presentation/` 配下で `grab_modal` を呼ぶファイルが `dialogs/` か `controllers/config_io/` のどちらかにあることの確認
  （両系統の外へ新規の呼び出しが増えたとき素通りしないため。`modal.py` の定義は除く）。

### 含まない（後送り・触らない）

- production コード（`CategoryChooserDialog` は現状で規約を満たすため修正不要の見込み。**満たさなかった場合は
  テストを緩めず作業を止めてユーザーへ諮る**〔`codebase_map.md:344-345`・phase 14 の確定運用〕）。
- phase 15 側の静的検査（`DIALOG_FILES` / `T2_DIALOG_FILES`）の変更。
- `features.md` §4.6 のモーダルの作法そのもの・`grab_modal` の実装。

## このフェーズで読むファイル

1. [idea_32](../../backlog/idea_32_grab_modal_static_check_discovery.md)（経緯・案 A/B/C）
2. `tests_ui/test_nested_modal_grab.py:1-12, 260-330`（書き換え対象の検査と import）
3. `keyseq/presentation/dialogs/keymap_set_history_dialog.py:195-212`（今回新たに対象へ入る `CategoryChooserDialog`・読むだけ）
4. `tests_ui/test_dialog_teardown_flows.py:18-43`（phase 15 側の列挙・棲み分けの確認のみ・変更しない）
5. `instructions/common/codebase_map.md:342-345`（静的検査の記載位置）

## タスク

- task_01: 静的検査の発見ベース化（系統 A・系統 B・呼び出し場所の確認）
- task_02: 記録（`codebase_map.md:343` 付近へ発見ベースであることを 1 行 / decisions_archive/33〔phase 15 側の既知の限界を含む〕/
  current.md〔「テスト負債」の idea_32 行を削除〕/ idea_32 → INDEX_done / `/refactor_check`〔`keyseq/` の変更 0 件ならスキップ〕）

## レビュー方針

- 共通観点は `.claude/rules/review.md`。
- **本フェーズ固有**:
  - **検査内容が弱まっていないか**: 系統 A の「ちょうど 1 回」「最後の文」、系統 B の件数・構造検査が残っているか。
  - **発見条件**が `Toplevel` 継承であり、`grab_modal` の有無に依存していないか（消失の素通り防止）。
  - **0 件で素通りしないか**（下限のアサート・`tk.Toplevel` と `Toplevel` の両方の書き方を拾うか）。
  - 変更前の列挙 10 クラス + `CategoryChooserDialog` がすべて発見されること（実測で確認）。
  - production・phase 15 側の静的検査に差分が無いか。
