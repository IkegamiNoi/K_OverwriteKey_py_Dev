# task_18_share_state_sole_wording

## 目的

子ファイル保存の一覧ダイアログで、共有状況「単独」が**既存ファイルを上書きすることを伝えていない**
問題を、**表示文言の変更だけ**で解消する（暫定仕様 05 **v0.7-R** / §5・受入条件 **27**）。

共有状況の 5 値のうち保存先にファイルが無いのは「新規作成」だけで、「単独」は**既存ファイルの上書き**を
意味するが、語からそれが読み取れない（2026-08-02 の実機目視で判断に迷いが発生）。

レイヤ制約: **presentation 限定**（`config_io/child_save_rows.py` の表示文言 1 箇所）。
**application / domain 不変・スキーマ不変・挙動不変**（判定名・既定ラジオ・保存計画は変えない）。

## 対象範囲（presentation 限定・表示文言のみ）

### 1. `keyseq/presentation/controllers/config_io/child_save_rows.py`

`share_text_for` の `SHARE_SOLE` の戻り値を変更する。

| 判定 | 現在 | 変更後 |
|---|---|---|
| `SHARE_SOLE` | `"単独"` | `"この構成のみが所有・既存を上書き"` |

- **他の 4 値（`SHARE_NEW` / `SHARE_SHARED` / `SHARE_OTHER_PARENT` / `SHARE_UNKNOWN` /
  `SHARE_NEW_COLLIDES`）の文言は変更しない**。
- **定数名・判定ロジック（`judge_share_state`）・`default_action_for` は変更しない**。
  `SHARE_SOLE` は引き続き `ACTION_SAVE` を既定とする。
- `keymap_set_io.py` の `share_state in (SHARE_SOLE, SHARE_NEW)`（依存確認の提示条件・v0.4-D）と
  `share_state != SHARE_SOLE`（A2 の対象行・v0.3-A2）は **判定名で書かれているため変更不要**。
  **文言で分岐している箇所が無いことを確認**した上で、無ければ触らない。

### 2. テスト

**受入条件 27 の 3 点**を満たす形で追加・更新する（新規ファイルは作らない）。

| # | 追加先 | 内容 |
|---|---|---|
| 1 | `tests/`（`share_text_for` を扱う既存ファイル。無ければ `tests_ui/test_child_save_dialog.py`） | `share_text_for(SHARE_SOLE)` が **`"この構成のみが所有・既存を上書き"` と完全一致**する |
| 2 | 同上 | 既存ファイルの `_parent_refs` が現在の上位のみの状態を作り、`collect_child_save_rows`（または `build_row`）経由で得た行の `share_state == SHARE_SOLE` / `share_text` が新文言 / `default_action == ACTION_SAVE` |
| 3 | `tests_ui/test_child_save_dialog.py` | `font.nametofont("TkDefaultFont").measure()` で、**新文言の幅が `share_text_for(SHARE_SHARED)` 相当の最長文言（「N 個の上位で共有中・全てに影響します」）の幅以下**である |

- **既存テストの fixture 更新は、レイアウト境界を検証しているテストだけ**に限る
  （`ChildSaveRow(..., "単独", ...)` の直書きは全 16 箇所あるが、**共有状況列の幅がレイアウト判定に
  効くテスト**〔最小サイズ・可変列の境界比較 = 受入条件 14b / 22 相当〕のみ新文言へ差し替える）。
  それ以外の直書き fixture は**触らない**（文言に依存しない検証であり、更新は不要変更になる）。
- 既存の `SHARE_SOLE` 依存テスト（依存確認が出ない / A2 の対象外 / v0.4-I の置換元）が
  **無修正で pass** することを確認する（挙動不変の担保）。

### 設計メモ / 制約

- **表示文言以外を変えない**。特に **v0.4-I を trigger_set へ拡張しない**
  （2026-07-30 に却下済み。採ると v0.4-D の「単独なら確認を出さない」が空振りする）。
- 「単独」は**一覧ダイアログの共有状況列にしか現れない**（依存確認は単独のとき出ず〔v0.4-D〕、
  A2 は単独行を対象外とする）。他の UI 面へ波及していないことを確認してから変更する。
- 共有状況は**固定幅列（省略表示の対象外）**。新文言が既存の最長文言より長くなると
  最小サイズ要件〔v0.3-C / v0.4-C〕を悪化させるため、テスト 3 で担保する。

## 含まない

- 受入条件 15 / 16 / 17b / 24b・task_04 / task_12 の本文で「単独」を**判定名**として書いている箇所の
  書き換え（**据え置き**。暫定仕様 v0.7 節に「判定名を指す」と定義済み。ユーザー確定 2026-08-02）
- 他の共有状況（新規作成 / 共有中 / 別の構成 / 所有元不明）の文言変更
- `SHARE_SOLE` の**判定条件**や既定ラジオの変更・v0.4-I の適用範囲拡大
- 正本 `spec_detail/` への昇格・暫定仕様の凍結 → **task_10**

## 確認

python は**リポジトリルートの `.venv`**（worktree 相対 `../../../.venv/Scripts/python.exe`）を使う。

1. `-m compileall -q keyseq main.py tests_ui` が clean
2. `-m unittest discover -s tests` が全 pass（現状 142 から減らない）
3. `-m unittest discover -s tests_ui` が全 pass（現状 152 + 追加分）
4. `-m tests.smoke_app` が pass
5. 追加テスト 3 件が**変更前の実装では落ちる**こと（文言変更を検出できること）

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は **[manual_check_plan.md](../manual_check_plan.md) の R11** で実施（ユーザー）。
  R4〜R9 の再確認は不要（挙動不変のため）。
