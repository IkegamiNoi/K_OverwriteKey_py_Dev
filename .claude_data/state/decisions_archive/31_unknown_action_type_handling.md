# decisions_archive / phase 31: 種類が不正なアクションの実行

対応表: phase 31 / **暫定仕様 24**（v0.5・凍結）/ decisions 31。
起票元: [idea_35](../../../instructions/backlog/idea_35_unknown_action_type_handling.md)
（phase 30 で案 B として分離・phase 30 完了判定前の `codex-adversarial-reviewer` high の対処）。
完了 2026-09-24。**application 限定 + presentation の委譲 1 行・スキーマ不変・挙動変更**（種類が不正なら送らない）。
正本 = `spec_detail/data_schema.md` §5.11.1（phase 30 の「`value` を文字列入力」条項を置換）/ §5.11.5（既知の制約 1 項）+ `codebase_map.md`。

## 問題

アクション要素の `type` が **無い / 空 / 未知 / 非文字列**のとき、実行すると `value` を**文字列として前面アプリへ入力していた**
（`action_executor.py` 末尾のフォールバック）。phase 30 の読込時正規化で、truthy な非文字列（`["hotkey"]` 等）も
「`AttributeError` で無送信」→「文字入力」に変わっていた。

## 確定した設計判断（ユーザー 2026-09-24）

| # | 判断 | 採らなかった案と理由 |
|---|---|---|
| 1 | **案 B = 何も送らず実行時エラーとして通知** | 現状維持（文字入力）= 想定外の文字が他アプリへ入る |
| 2 | **案 X（非文字列 `type` の要素を読込時に除去）は採らない** | phase 30 の正規化で空になり案 B でエラーになる。除去すると次の保存でファイルから消え、直す機会が無い |
| 3 | **通知 = 既存 `show_action_error`（案 b）**。原因・種類・ラベルは最終行「エラー:」の文 | 案 a（`on_runtime_error` の `messagebox`）= 多重表示抑止が無く、種類・値の表示を自前で組む。冒頭の定型文「送信キーに間違いがあります」は hotkey 寄りだが、原因は最終行で伝わる（ユーザー確認） |
| 4 | **シーケンスは止める（案 S）**: run_to_end は停止・単発は index を進めない。executor が送った / 送らなかったを返す | 案 C（`x` / `y` 不正時と同じく続ける）= 通知後のフォーカスの戻り先へ同じシーケンスの後続が自動で送られる恐れ・全要素不正時の連続表示 |
| 5 | **hotkey 検証エラー・`x` / `y`〔`to_x` / `to_y`〕不正・送信例外の扱いは変えない**（前 2 つと mouse_click の送信失敗は executor が `True`。**hotkey / text の送信例外は従来どおり `execute` の外へ抜ける**） | 同じリスクを持つが範囲外（変えるなら別 idea） |
| 6 | **`type` の無いアクションへの互換措置はしない** | 旧来の text 扱いは初回実装 `4f53178` の「不明タイプはテキスト扱い」= **防御的な既定で旧形式互換ではない**（裏取り済）。§5.1「既存キーの意味変更禁止」の設計変更による例外として正本に明記 |
| 7 | **通知へ渡す `action` は `type` を文字列化した浅いコピー**（確定前 codex-adversarial high 1） | 生の非文字列を渡すと `show_action_error`（`hook_controller.py:241`）の `.strip()` で落ち、「送らなかった」が runner に届かない |
| 8 | **通知の表示中の入力は既知の制約として受容**（確定前 codex-adversarial high 2） | 表示中もフックは止まらず、ユーザー操作の正常なアクションは前面の窓（通知ダイアログ含む）へ送られる。種類が不正なアクション自体は常に送られない。**既存の全エラーダイアログ共通**で、「通知中の実行禁止」は範囲外 |
| 9 | **runner の判定は `is False` のときだけ**（task_02 起票時） | `not result` = `None` を返す既存の呼び出し元（テストの `performed.append`）まで止まる |

## 実施結果

- task_01（`e247608`）: `ActionExecutor.execute -> bool`・種類は `isinstance` で非文字列を空扱い・不正なら送らず
  `on_action_error(コピー, err)` → `False`・text フォールバック削除 + `tests/test_action_executor_type.py`（6 件・実 `show_action_error` 経由を含む）。
  reviewer = 完了可・指摘なし。
- task_02（`31466fc`）: `SequenceRunner` が `is False` で run_to_end を停止 / 単発は index を進めない・`App._perform_action` が戻り値を返す +
  `tests/test_sequence_runner.py` に本物の executor × runner のテスト 6 件（通知中の pause / resume 再入・既存経路が止まらない）。
  reviewer = 完了可。
- task_03: 正本 §5.11.1 / §5.11.5 + `codebase_map.md`（「アクションの実行」小節）/ 暫定 24 凍結 / 本アーカイブ / current.md / idea_35 → INDEX_done。
- 実測: compile clean / `tests` **577**（skip 7・+12）/ `tests_ui` **532** / smoke OK。
  tests_ui 1 回目に `test_dialog_escape_binding` で 2〜3 件 flaky（task_01 前後・task_02）→ 再実行で全 pass。idea_33 へ観測追記
  （「再開要求が 0 回」の形 = idea_18 系統の可能性）。
- 実機目視: **任意としユーザー判断で省略**（UI から不正な種類を作れず手編集 JSON のみの経路・単体 / 組み合わせテストで固定）。

## 完了判定前レビュー（2026-09-24）

- `codex-adversarial-reviewer` = **approve**（重大な指摘なし。静的レビューのみ・個別の根拠は薄い）。
- `deep-reviewer` = **修正要（文書のみ・コード修正不要）**。production 3 ファイルは暫定 24 §3 と一致、受け入れ条件 1〜6 はテストで充足。
  **ユーザー確認のうえ反映**:
  - **M1**: 「送信例外も `True`」は誤り。**hotkey / text の送信例外は従来どおり `execute` の外へ抜ける**（`True` になるのは mouse_click の送信失敗のみ）。
    挙動は phase 31 以前から不変でコードは正しい → `codebase_map.md` / 本アーカイブ #5 / phase.md / task_01 / task_02 の記述を訂正。
  - **M2**: 正本 §5.11.1 に「**run_to_end も位置は不正なアクションに残り、次はそこから始まる**」を追加（暫定 24 §3.2 から昇格時に落ちていた）。
  - **M3**: 完了の記録がレビュー前に確定していた → 本節を追加し、ユーザー確認後に完了として確定。
  - **L1 / L2**: 正本の「hotkey の送信エラーと同じ通知」→「hotkey の検証エラーと同じ『送信エラー』の通知」/ 止まらない条件に `to_x` / `to_y` 不正を追加。
  - **L5 / L6**: `codebase_map.md` の `_perform_action` を「dialogs 向け契約」から外し runner への注入と明記 / 「`None` を返す呼び出し元」→「注入される実装」。
  - 保留・参考: L3（§5.1「要素が成立しない」との関係の注記。§5.11.1 が除去しないと明記済みで矛盾ではない）/
    L4（hotkey 検証エラー時の単発進行の組み合わせテスト・通知中の入れ子 `_run_to_end_step`。いずれもコード上は無害）。

## refactor_check

- **不要**（PHASE_BASE `6c20dd6`・対象 3 ファイル: `action_executor.py` 165 → 182 / `sequence_runner.py` 156 → 160 / `app.py` 570 → 570）。
  M3 の候補 = `_run_to_end_step` の `stop_run_to_end()` → `_select_trigger(key)` → `return` が 2 → 3 箇所。共通部は既存メソッド 2 つの呼び出しのみで、
  追加分は index を戻さない点で意図的に異なるため「迷えば非該当」を適用。`current.md`「別タスク化候補」へ 1 行記録。
  M1 / M2 / M4 / M5 / M6 非該当（新規関数は `_invalid_type_message` 約 9 行・種類の列挙の出現数は不変・申し送りコメントなし）。

## 暫定仕様の版履歴

v0.1 起票 → v0.2 起票時 `deep-reviewer`（修正要 11 件: run_to_end の安全性 / 案 b の再評価 / フォールバックの由来 /
§4 文言の抜け / 見つけやすさ / executor の型防御 / 受け入れ条件 / 行番号）→ v0.3 §5-1〜§5-3 ユーザー確定 →
v0.4 確定前 `codex-adversarial-reviewer`（high 2 件）→ v0.5 ユーザー確定 → 凍結。

## 残件

- **通知（実行時エラーダイアログ全般）の表示中の実行禁止・フック停止**（既知の制約 §5.11.5・必要なら別 idea）。
- `x` / `y` 不正・hotkey 検証エラーでシーケンスを止めるか（同上）。
- 一覧表示の「不正」表記・通知へのトリガーキー / 行番号・読込時の警告（暫定 24 §7）。
