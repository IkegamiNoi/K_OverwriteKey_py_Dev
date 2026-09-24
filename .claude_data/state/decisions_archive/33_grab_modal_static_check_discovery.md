# decisions_archive / phase 33: ダイアログの静的検査の発見ベース化

対応表: phase 33 / 暫定なし（直接改訂モード）/ decisions 33。
起票元: [idea_32](../../../instructions/backlog/idea_32_grab_modal_static_check_discovery.md)（phase 14 の `/refactor_check`〔deep-reviewer M-6〕から分離）。
完了 2026-09-24。**tests_ui 限定・production 不変・スキーマ不変・正本 `spec_detail/` の改訂なし**。
記録先 = `codebase_map.md` の `modal.py` 節（grab_modal の静的検査）と HookController 節（フック停止の静的検査・`NESTED_CHILD_DIALOGS`）。

## 問題

ダイアログの静的検査 2 本が対象を列挙で持ち、phase ごとに手で足していた。
- `tests_ui/test_nested_modal_grab.py`（grab_modal は `__init__` の最後の文）= `dialogs/` 10 クラス + `config_io/` 3 ファイル。
  **足し忘れが既に 1 件あった**: `CategoryChooserDialog`（`dialogs/keymap_set_history_dialog.py:195`・phase 27 `7c643e1` で追加）。
  規約自体は満たしていた（`grab_modal` は `__init__` の最後の文・1 回）ため production の修正は不要だった。
- `tests_ui/test_dialog_teardown_flows.py`（phase 15 の static_1・2 = フック停止は `suspend_hook_for_dialog(self)` 1 回・`resume` を呼ばない）= `DIALOG_FILES` 9 ファイル。

## 確定した設計判断

| # | 判断（ユーザー 2026-09-24） | 採らなかった案と理由 |
|---|---|---|
| 1 | **案 A'**: `dialogs/` 直下の **`Toplevel` 継承クラス**（`tk.Toplevel` / `Toplevel`）を AST で発見し、「`grab_modal` はちょうど 1 回」「`__init__` の最後の文」を課す。発見件数の**下限 11** | 案 B（`grab_modal` を呼ぶクラスを発見・列挙全廃）= 呼び出しが消えたクラスが対象から外れ**消失を検出できない** / 案 C（列挙据え置き + 足し忘れ検出のみ）= 手で足す運用が残る |
| 2 | config_io は **`grab_modal` を呼ぶファイルの集合 = 期待件数の辞書のキー**。件数（2 / 1 / 1）と構造の検査は据え置き | — |
| 3 | （メイン提案・ユーザーへ明示）`keyseq/presentation/` 全体で `grab_modal` の呼び出し場所は `dialogs/` 直下か `config_io/` 直下だけ | — |
| 4 | （追加確定・完了判定前レビュー後）**呼び出しは式文に限らず全 `ast.Call` で数え**、`dialogs/` 内の `grab_modal` 総数 = 発見したクラス数。3 検査は別メソッドへ | 別名 import・多段継承の解決と AST フィクスチャ（codex-adversarial の提案）= 現状 0 件で手間に見合わない → 残るリスクとして記録 |
| 5 | （追加確定）**phase 15 側の static_1・2 も本フェーズで発見ベースに**。static_2 = `dialogs/*.py` 全体で `resume` 0 件。static_1 = 発見クラスのうち**ネストした子の除外リスト** `NESTED_CHILD_DIALOGS`（**(ファイル名, クラス名) の組**: `preset_dialog.py` の `PresetDialog` / `keymap_set_history_dialog.py` の `CategoryChooserDialog`。task_01c で組に変更）以外は `suspend(self)` がちょうど 1 回・子は 0 回（**ファイル単位 → クラス単位**）+ 総数 = トップレベルのクラス数 + 除外リストの名前がすべて発見されること。static_3（`T2_DIALOG_FILES`）は意味で決まる集合のため列挙のまま | 当初は「トップレベルか子かは構文で判別できず、発見ベースにしても止め忘れは検出できない」として対象外にしたが、deep-reviewer M1 の指摘どおり**除外リストを持てば検出できる**ため撤回。別フェーズにせず含めた理由 = 同じ主題・呼び出し発見の補強を共有できる・締め作業が 1 回で済む |

- 「ダイアログとみなす条件」は 2 テストで同じ定義を使う（共有ヘルパ `tests_ui/dialog_discovery.py`: `PRESENTATION` / `DIALOGS` / `parse` / `find_calls` / `dialog_classes`）。
- **発見条件と grab_modal の検査には除外を置かない**（`dialogs/` の `Toplevel` 継承は現状すべてモーダル）。非モーダルの窓が入ったら検査が落ちて判断を促す。
  除外を持つのはフック停止の検査（`NESTED_CHILD_DIALOGS`）だけ。**基準 = 常に親がフックを止めている間にだけ開かれ、自分では止めない子**。
  `PresetManagerDialog` はネストした子としても開かれる（`dialogs/action_dialog.py:414`）が、App 直下（`app.py:440`）からも開くため自分で止める＝**含めない**。
  検査が落ちたとき「除外リストへ足す」か「suspend を足す」かは、この基準で呼び出し経路を見て決める。

## 実施結果

- task_01（`604e445`）: grab_modal 検査の発見ベース化（codex-implementer）。reviewer = 完了可・指摘なし。
- task_01b（`f6ee86d`）: `dialog_discovery.py` 新規・`test_nested_modal_grab.py` を 3 メソッドへ分割し全 `ast.Call` で数える・
  `test_dialog_teardown_flows.py` の `DIALOG_FILES` を廃止し `NESTED_CHILD_DIALOGS` とクラス単位の検査へ（codex-implementer）。reviewer = 完了可・指摘なし。
- task_01c（`23e4dd6`）: `NESTED_CHILD_DIALOGS` を (ファイル名, クラス名) の組へ（完了判定前レビュー 2 回目の codex-adversarial 指摘）。一時改変 3 パターン（別ファイルに同名の `CategoryChooserDialog` をトップレベルとして追加・トップレベルの suspend 削除・子の suspend 追加）すべて FAIL → revert。reviewer = 完了可・指摘なし。
- task_02: `codebase_map.md`（`modal.py` 節・HookController 節）/ 本アーカイブ / current.md / idea_32 → INDEX_done。
- 実測（verifier）: compile clean / 発見 **11 件**（旧列挙 10 + `CategoryChooserDialog`）一致 / 一時改変はすべて FAIL → revert・`keyseq` 差分なし
  （task_01 = 3 パターン。task_01b = 7 パターン: 最後の文でなくなる・dialogs 側の消失・config_io の `_ = grab_modal(...)`・
  `dialogs/` のモジュール関数からの `grab_modal`・トップレベルの suspend 削除・子の suspend 追加・resume 追加）/
  `tests` **577**（skip 7・不変）/ `tests_ui` **537**（+2 = メソッド分割）。
- 実機目視: 不要（テストのみ）。

## 残るリスク（記録のみ）

- `Toplevel` を**別名 import**（`from tkinter import Toplevel as TL`）して継承するクラス・**多段継承**（`class Sub(ActionDialog)`）は発見されない。
  前者は `grab_modal` を呼べば総数検査（呼び出し数 ≠ クラス数）で捕まるが、呼び忘れと `__init__` の最後の文の違反は捕まらない。現状はどちらも 0 件。
- `grab_modal` を**別名 import**（`from ...modal import grab_modal as m`）して呼ぶ形は `find_calls` が数えない。現状 0 件。
- `dialogs/` の**サブフォルダは走査しない**（`glob("*.py")` は非再帰）。既存ダイアログを親専用フォルダへ移すと下限・呼び出し場所の検査で落ちるが、サブフォルダ内の補助モジュールが `resume_hook_after_dialog` を呼んでも static_2 は素通りする（旧版も同じで退行ではない）。
- `dialogs/` の外に置かれたモーダルのクラスは発見されない（旧版も同じで退行ではない。呼び出し場所の検査が `grab_modal` の呼び出しがあれば捕まえる）。

## 完了判定前レビュー（2026-09-24）

- 1 回目（task_01 + 記録の時点）:
  - `deep-reviewer` = **条件付き（完了可寄り）**。M1（phase 15 側の据え置き理由が不正確）/ L1（式文以外・関数形式・入れ子クラスの `grab_modal` が素通り）/
    L2（多段継承）/ L3（記録の未完・phase.md の完了記載が採否確定前）/ L4（1 メソッド約 94 行）。
  - `codex-adversarial-reviewer` = **needs-attention**（medium 2: 別名 import・多段継承で発見が漏れる / 式文以外・別名の呼び出しを見逃す）。
    phase 15 の据え置き判断は妥当と判定（deep-reviewer と見解が分かれた）。
  - **ユーザー判断**: L1・codex 2 = 小さく塗る（追加確定 #4）/ M1 = phase 15 側を本フェーズで発見ベースにする（追加確定 #5・task_01b）/
    L2・codex 1 の別名 import・多段継承 = 残るリスクとして記録 / L3 = 反映 / L4 = task_01b の分割で解消。
- 2 回目（task_01b + 記録の更新後）:
  - `deep-reviewer` = **条件付き（完了可寄り）**。1 回目の M1・L1・L3・L4 は解消・検査は旧版比で同等以上と確認。記録の指摘 M-1（「除外リストは作らない」が `NESTED_CHILD_DIALOGS` と字面で衝突）/ L-1（除外リストの基準の文言）/ L-2（codebase_map の static_2 の範囲）/ L-3（サブフォルダ非走査を残るリスクへ）/ L-6（記録の未完）→ **すべて反映**。L-4・L-5・L-7 は参考（対応なし）。
  - `codex-adversarial-reviewer` = **needs-attention**（medium 1: 子の除外がクラス名だけで、別ファイルの同名トップレベルダイアログが素通り）→ **ユーザー判断で task_01c として修正**（(ファイル名, クラス名) の組）。task 単位の reviewer = 完了可。

## refactor_check

- **スキップ**（PHASE_BASE `d65a6fa`・`git diff --stat d65a6fa..HEAD -- keyseq/` が空＝判定対象の変更ファイル 0 件。
  変更は tests_ui のみで、テストは判定対象外）。新規 `tests_ui/dialog_discovery.py` は 31 行。
