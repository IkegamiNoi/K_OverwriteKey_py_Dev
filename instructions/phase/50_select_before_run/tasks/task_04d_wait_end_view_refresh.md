# task_04d_wait_end_view_refresh

## 目的

単発の待機が明けたとき、一覧の選択が待機していたトリガー K 以外（別のトリガー X）なら選び直さない（`features.md` §4.2.11・暫定 34 §2-8）。この経路が**表示を描き直さない**ため、
待機明けに呼び出しの連動（§4.2.9）で X の位置が進んでも、X のシーケンス欄・ステータスが古いまま残る（完了判定前の Codex 敵対的 high・ユーザー採用 2026-10-09）。
選択を残すときも**今選ばれているトリガーの表示を描き直す**。application 限定・presentation / domain 不変・スキーマ不変・仕様不変（選択は変えない）。

再現の形: X = `[call A, c]`・A = `[a, b, 待機]`。X で a を送る → A を直接押して b と待機 → 待機中に一覧で X を選ぶ → 待機が明けると連動で X の位置は c へ進むが、X の欄は「call A」が次に実行のまま。

## 対象範囲（application 限定）

### `keyseq/application/sequence_runner/send_wait.py`（:66-68）
- 今: 注入口が無い、または選ばれているキーが K なら `_select_trigger(key)`。それ以外は何もしない
- 変更: 選ばれているキーが K 以外の**キー**（None でない）なら、**そのキーを `_select_trigger` で選び直す**（同じ行を選び直すだけ＝選択は変わらず、UI 側の `select_trigger_by_key` がシーケンス欄・ステータスを描き直す）。
  選ばれているキーが None（グレーの行・一覧が空）なら従来どおり何もしない。注入口が無い・K のときは従来どおり K を選ぶ
- 新しい注入口・新しい関数は足さない（既存の `_get_selected_trigger_key` と `_select_trigger` だけで行う）

### テスト `tests/test_sequence_runner_select_before_run.py`
- 既存の期待値を新しい動きへ追随（選択のキーは変わらないこと + 選ばれているキーの選び直しが 1 回呼ばれること）:
  `test_single_wait_reselects_only_when_selection_is_still_its_key`（`selected["key"] = "f2"` の 2 か所: `selections == ["f2"]`）/
  `test_single_wait_keeps_selection_made_by_trigger_press`（待機明けの後 `selections == ["f2", "f2"]`）/
  `test_repeated_waits_keep_selection_made_by_trigger_press`（待機明けごとに "f2" が 1 つずつ増える）。いずれも `selected["key"] == "f2"` は維持
- 選ばれているキーが None のときは待機明けに何も選ばないことのテストを 1 本追加
- **回帰テストを 1 本追加**: X = `[call A, c]`（ステップの呼び出し `{"type": "system", "op": "call", "target": "<A のキー>"}`）・A = `[a, b, 待機]` で上の再現の手順を踏み、
  待機明けの後に「選択は X のまま」「X が選び直された（`selections` の最後が X）」「X の位置が c（インデックス 1）」を確かめる。呼び出しの組み立ては同ファイルの既存の呼び出しのテスト（:373-486）に倣う

## 読むファイル

- `keyseq/application/sequence_runner/send_wait.py`（全体）
- `keyseq/application/sequence_runner/sequence_runner.py:40-80`（注入口）
- `tests/test_sequence_runner_select_before_run.py`（全体・`make_runner` と呼び出しのテストの組み立て）
- `instructions/common/spec_detail/features.md` §4.2.11 の「単発の待機が明けたときの選び直し」

## 含まない

- presentation の変更（`select_trigger_by_key` は既に描き直す）
- 待機明け以外の経路（file_line・呼び出し・連続実行の選択）
- 正本の改訂（task_05 で §4.2.11 に「選択を残すときも表示は描き直す」を 1 行足す）

## 確認

- 上記テストの追随と追加（実行は verifier）
- tests / tests_ui / smoke 全体 pass（verifier）
- reviewer（5 観点）
