# phase 17 統合結果（task_04）

対象: `351c4af..HEAD` の phase 17 全差分（起票 + task_01 / 02 / 02b / 03）。
判定と根拠のみを記録する（生ログは載せない）。**本ファイルが task_04 の判定の正**。

> 状態: **進行中**。残り = ①**task_02c**（H-1 の最小修正・Codex の利用上限復帰待ち）
> ②**ユーザーによる実機目視 M1〜M5**（未実施）。

## 1. 統合確認（`verifier` 実測・`.venv` の python）

| 項目 | 結果 |
|---|---|
| `compileall -q keyseq main.py tests tests_ui` | clean |
| `unittest discover -s tests` | pass 417 / skip 7 |
| `unittest discover -s tests_ui` | pass **347**（**3 回実行して毎回同一**） |
| `tests.smoke_app` | SMOKE OK |
| 単独実行（minimize_grab_custody 9 / modal_grab 22 / nested_modal_grab 11 / dialog_teardown_flows 10 / dialog_transient_parent 2 / app_ui_flows 74） | すべて pass |
| `user/` `quarantine/` の生成 | なし |
| 変異検査 M1〜M6（task_03 時点） | **すべて期待どおり fail**（空振りなし・復元後バイト一致） |

- **[idea_18](../../backlog/idea_18_escape_delivery_flaky_test.md) の flaky は今回 3 回とも発現せず**
  （切り分け対象の失敗自体が発生しなかった）。

## 2. 二次レビュー

### `deep-reviewer`（フェーズ横断）= **条件付き完了可**

5 観点は仕様適合性・依存方向・責務分離・不要変更が OK、チェック漏れのみ NG（M-3）。
phase 14 / 16 の資産（`add="+"` 結線・クロージャ記録・二重呼び出しガード・非 LIFO の内側優先・
`transient`・`suspend_hook_for_dialog`）はいずれも無変更であることを実測で確認。
`deiconify` / `lift` / `focus_force` の呼び出しは 0 件（A4 が固定）。

| # | 指摘 | 区分 | 対応 |
|---|---|---|---|
| **H-1**（高） | 最小化中に**預かり窓と新モーダルの両方**が破棄されると、差し戻しが発火せず `<Map>` も台帳フォールバックへ到達せず、**生存・表示中の外側モーダルが非モーダルのまま復元される** | **採用**（ユーザー判断） | 暫定仕様 **v0.6**（§3-2(8) 拡張）+ **task_02c** で最小修正 |
| M-1（中） | 最小化で隠れない窓（`KeyboardWindow` は `transient` なし）は**預かり中に操作できる**（復元で grab は戻る） | 修正して採用 | **task_05** で正本へ残存リスクとして明記 |
| M-2（中） | `<Map>` のフォールバックが条文より広い（記録窓が生存かつ非表示でも台帳最内へ） | 修正して採用 | **task_05** で昇格文面を実装に合わせる（実装は変更しない） |
| M-3（中） | `<Unmap>` 側のガード 3 つ（解決不能 / 破棄済み / 既に預かり中）が**テストで未固定** | 修正して採用 | **task_02c**（A11〜A13） |
| M-4（中） | `_app_minimized` が**テストモジュール間でリーク**（`setUp` で patch していない） | 修正して採用 | **task_02c** |
| L-1（低） | 型注釈（`_custody_window: tk.Toplevel | None` に `tk.Misc` を代入） | 保留 | mypy 未導入のため据え置き |
| L-2（低） | 最小化中に stdlib ダイアログが grab を持つと預かりが捨てられ、復元後に非モーダルになる | 保留 | **task_05** で「保証の範囲外」へ 1 行 |
| R-1（参考） | `_custody_window` を廃し `<Map>` で常に台帳最内へ張る代替案 | **不採用** | decisions.md で除外済みの C 案の蒸し返し |

- **H-1 はメインセッションでも裏取り済み**（`P exists/viewable: 1 1 | grab_current: None`）。
  **実装バグではなく v0.5 の条文の残穴**。

### `codex-reviewer` = **実行不能（Codex の利用上限）**

`agent_selection.md` の規定どおり **Claude 側（`deep-reviewer`）へ縮退**した（報告のみ・許可不要）。
フェーズ完了判定前の `codex-adversarial-reviewer`（task_05）は、利用上限の復帰後に実施する。

## 3. 実機目視（ユーザー・**未実施**）

| # | 手順 | 期待 | 結果 |
|---|---|---|---|
| M1 | ダイアログを開いたまま **Win+D** → 復元 | アプリが復元できる | 未 |
| M2 | M1 の復元後 | モーダル性が残る | 未 |
| M3 | M1 の復元後 | 中間のダイアログも含め全窓が表示されている | 未 |
| M4 | **3 段ネスト**で最小化 → 復元 | M1〜M3 と同じ + LIFO 復元が従来どおり | 未 |
| M5 | **通常の最小化ボタン** | M1〜M3 と同じ | 未 |

**stdlib ダイアログ（`messagebox` / `filedialog`）が開いた状態は対象外**（症状が残るのは確定済み）。

## 4. 未解決事項

- **task_02c 未実施**（H-1 の最小修正 + M-3 / M-4）。**Codex の利用上限の復帰待ち**
  （ユーザー判断: `implementer` へフォールバックせず待つ）。
- **実機目視 M1〜M5 が未実施**。
- task_05 へ送る文書項目: **M-1 / M-2 / L-2**。
