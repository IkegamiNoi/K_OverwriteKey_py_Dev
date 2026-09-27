# decisions_archive / phase 37: 出力シーケンスの制御アクション・第 1 弾

対応表: phase 37 / 暫定 26（v0.6・凍結）/ decisions 37。起票元: ユーザー要望（2026-09-26・出力シーケンスに system 種別を追加したい）。
完了 2026-09-27。**JSON スキーマ変更あり**（`actions[]` に `system` / `file_line` を追加・既存キーは不変）。
正本 = `data_schema.md` §5.11.1・§5.11.5〜5.11.8・§5.13.1 / `features.md` §4.2.1〜4.2.6・§4.5・§4.6 / `codebase_map.md`「出力シーケンスの制御アクション」節。

## 確定した設計判断（ユーザー）

| # | 判断 | 採らなかった案と理由 |
|---|---|---|
| 1 | system 種別（ループ / カウンター +1・0 に / 待機 / 戻す / 先頭へ）+ 独立の file_line 種別 | text の置換記法 `{counter}` = 既存データの意味が変わる（§5.1 違反） |
| 2 | system は押下を消費しない。ループはネスト可・上限 9・周回は中断しても保持 | — |
| 3 | カウンターは名前指定・アプリ全体共有・起動中のみ。**戻すは差分で打ち消す**（v0.3） | 値の書き戻し = 別トリガーの変更を消す / 所有者方式 = 参照が重く他トリガーから 0 にできない |
| 4 | 戻す / 先頭への対象 = 直前のトリガー（専用トリガーから押す）。**単独登録に限定・混在は実行時エラー**（v0.5） | — |
| 5 | 単発の待機は非同期（保留中ステップ + 世代番号）。**待機中も他のトリガーは使える**（v0.3） | 待機中は他を無視 = 単発実行の途中で他のトリガーを使う使い方を妨げる |
| 6 | file_line は 1 始まり・範囲外 3 択・UTF-8 / Shift_JIS（cp932）・**1 MB 上限**（v0.3） | 別スレッド読込 = 状態遷移が増える。→ 遅い I/O は既知の制約とし **idea_38 で次フェーズ対応**（v0.6） |
| 7 | 追加ダイアログに「末尾に追加」（既定 ON・全種別）。ループの移動はループ以外の行とだけ入れ替え | ループ行どうしの入れ替え = 回数の設定が別のループへ移る |
| 8 | ネストの色分け = 深さで青・緑・橙 × 薄・中・濃（上限 9）。ループ行も自分の色 | — |
| 9 | **通常アクション直後に続く system を先行処理**（v0.4・実機目視「次に実行が system の行を指し、その前の行が実行される」） | 表示だけ先読み = 位置と表示が食い違う |
| 10 | **カウンターは先行処理で値を変えず保留し、次の押下で反映**（表示は現在値・v0.5）/ 連続実行の停止時は反映（v0.6）/ ループの周回表示は次の周回のまま | 先行処理で値も変える（v0.4）= file_line の行がずれる |
| 11 | ジャンプは作らない / 停止・他トリガー呼び出しは第 2 弾 / カウンター条件分岐は idea_37 | 先へ進める操作は管理が煩雑 |

## 結果（タスク）

| タスク | 内容 | 実装エージェント |
|---|---|---|
| task_01 | domain の土台（`sequence_control.py`） | codex-implementer（Luna xhigh） |
| task_02 | 実行モデルの中核（`sequence_steps.py`） | Sol medium 単独（子は起動されず） |
| task_03 | 待機 | Sol medium + 子 Luna xhigh（テスト） |
| task_04 | 戻す・先頭へ（`sequence_history.py`） | Sol medium + 子 Luna xhigh ×3 |
| task_05 | file_line（`file_line_reader.py`） | codex-implementer（**Luna high 試行**） |
| task_06 | 編集 UI（`sequence_editing.py` / `action_control_fields.py`） | Sol medium + 子 **Luna high** ×3 |
| task_07 | 一覧の表示と色分け（`action_list_rendering.py`） | codex-implementer（Luna high） |
| task_07b | 統合レビュー指摘（H1 フォーカス同期でのリセット・M1〜M4・L2・L5・L7・L12）| codex-implementer |
| task_07c | 先行処理（v0.4） | Sol medium（子なし） |
| task_07d | カウンターの保留・戻す / 先頭への単独登録（v0.5） | Sol medium + 子 Luna high |
| task_07e | 完了判定前レビュー指摘（追加時の位置・連続実行の世代番号・停止時の保留反映・改名の順序）| codex-implementer |

- 最終実測: `tests` 829（skip 7）/ `tests_ui` 615 / smoke OK。実機目視 OK（ユーザー 2026-09-27・task_07d 後）。
- **Codex の子・Codex 本体が書いたテストの期待値誤り・準備不足が毎タスク 1〜数件**（setUp の前提・cp932 の 0x8160 = U+FF5E・大文字キー・偽 App の属性・古い仕様の期待値・位置引数の順の変更）。
  いずれも verifier の実測で検出しメインで修正。**verifier の実測は省略できない**。

## レビュー

- 起票時: deep-reviewer（修正して採用）→ Codex 敵対的（Luna xhigh / Sol medium の 2 回・実質同じ指摘・Sol は約 2 分 vs Luna 約 13 分）。
- 統合: deep-reviewer（H1 = 一覧の `<KeyRelease>` で位置不変でも周回・履歴・待機がリセット）/ Codex 標準（Luna xhigh 約 9.5 分・1 件 / **Sol medium 約 4.5 分・2 件〔Luna の見落とし 1 件を含む〕**）。
- 完了判定前: deep-reviewer（修正して完了・M-1〜M-6・L-1〜L-8）/ Codex 敵対的（Sol medium 約 2.5 分・file_line の遅い I/O〔→ idea_38〕・連続実行の世代番号）。
- 受容した境界（正本に記載）: 戻す・先頭へだけのトリガーの連続実行 / 通常アクションの無い無限ループでの保留の蓄積 / 新キーの trim は全種別 / file_line の遅い I/O。

## エージェント構成の変更（本フェーズ中・ユーザー判断）

- Codex 実装エージェントを 2 種に: `codex-implementer`（修正箇所が具体的・量が多くない）/ `codex-delegating-implementer`（判断が要る・量が多い・Sol medium + Luna の子）。
- 推論レベルの既定を **Luna high** に（task_05・06 の試行で xhigh と品質差なし・所要時間が短い）。codex-explorer も Luna high。
- `~/.codex/config.toml` の既定をユーザーが **Sol medium** に（Codex レビュー系はプラグイン経由で Sol medium）。
- Codex の子は親の設定で作られた直後に指定モデルへ切り替わる（セッション記録の `turn_context` で確認）。

## 別タスク化候補へ送ったもの

- 統合レビュー Low: L3（`rekey_trigger_set` で移動先側の保留を破棄）/ L4（範囲外の位置の丸め方が旧実装と違う）/ L6（ループの対を削除しても位置補正しない）/
  L8（対応崩れが別の場所にあると張り直さず正しい終わりもエラー）/ L9（既に深さ超過があるとどこにも追加できない）/ L10（肥大）/ L11（file_line は `_write_text` の例外も捕捉）/
  L13（削除確認ダイアログ中はフックが止まらない）/ L14（待機の続きの防御の弱さ）。
- 完了判定前 L-8: `sequence_runner.py` の先行処理の呼び出しが単発・連続で重複。

## refactor_check

- **推奨** → [提案書 15](../../instructions/modified_proposal/15_refactor_sequence_control_actions.md)（M1 `trigger_panel_controller.py` 732 行 +168 / M2 `ActionControlFields.__init__` 84 行 / M6 op 名・文字コード等の直値と深さ上限 9 の直値）。**ユーザー承認 (a) → task_09 で実施済**: `controllers/trigger_panel/`（本体 562 行・`action_edit.py` の `ActionEditFlow`・委譲は初回参照で作る property）/ `ActionControlFields.__init__` 17 行・定数参照。挙動不変（tests 829 / tests_ui 615 / smoke・件数不変）。移動先が自分のメソッドを直接呼んでテストの差し替え口を迂回した件をメインで修正（コントローラ経由に戻す）。
