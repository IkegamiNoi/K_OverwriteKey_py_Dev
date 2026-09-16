# phase 17 統合結果（task_04）

対象: `351c4af..HEAD` の phase 17 全差分（起票 + task_01 / 02 / 02b / 03）。
判定と根拠のみを記録する（生ログは載せない）。**本ファイルが task_04 の判定の正**。

> 状態: **完了**（2026-09-16）。**task_02c は完了**（H-1 は解消・`reviewer` 採用）。
> 実機目視 = **M1〜M4 問題なし / M5 は最小化の経路がなく実施不可（欠陥ではない）**。

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
| **task_02c 後の再実測** | `tests` 417 / `tests_ui` **351** / smoke OK / `test_minimize_grab_custody` **A1〜A13 全 pass** |
| **変異検査 M7 / M8**（task_02c） | **期待どおり fail**（M7 → A10 / M8 → A11。復元後バイト一致） |

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
| **H-1**（高） | 最小化中に**預かり窓と新モーダルの両方**が破棄されると、差し戻しが発火せず `<Map>` も台帳フォールバックへ到達せず、**生存・表示中の外側モーダルが非モーダルのまま復元される** | **採用**（ユーザー判断） | 暫定仕様 **v0.6**（§3-2(8) 拡張）+ **task_02c で解消済**（修正前 `grab_current: None` → 修正後 `grab_current: .!toplevel`。**メインセッションで再現確認**） |
| M-1（中） | 最小化で隠れない窓（`KeyboardWindow` は `transient` なし）は**預かり中に操作できる**（復元で grab は戻る） | 修正して採用 | **task_05** で正本へ残存リスクとして明記 |
| M-2（中） | `<Map>` のフォールバックが条文より広い（記録窓が生存かつ非表示でも台帳最内へ） | 修正して採用 | **task_05** で昇格文面を実装に合わせる（実装は変更しない） |
| M-3（中） | `<Unmap>` 側のガード 3 つ（解決不能 / 破棄済み / 既に預かり中）が**テストで未固定** | 修正して採用 | **task_02c で対応済**（A11〜A13。M8 で空振りでないことを確認） |
| M-4（中） | `_app_minimized` が**テストモジュール間でリーク**（`setUp` で patch していない） | 修正して採用 | **task_02c で対応済**（両モジュールの `setUp` で patch） |
| L-1（低） | 型注釈（`_custody_window: tk.Toplevel | None` に `tk.Misc` を代入） | 保留 | mypy 未導入のため据え置き |
| L-2（低） | 最小化中に stdlib ダイアログが grab を持つと預かりが捨てられ、復元後に非モーダルになる | 修正して採用 | **task_05** で「保証の範囲外」へ 1 行（当初「保留」と記載していたが、正本へ追記したため区分を訂正） |
| R-1（参考） | `_custody_window` を廃し `<Map>` で常に台帳最内へ張る代替案 | **不採用** | decisions.md で除外済みの C 案の蒸し返し |

- **H-1 はメインセッションでも裏取り済み**（`P exists/viewable: 1 1 | grab_current: None`）。
  **実装バグではなく v0.5 の条文の残穴**。

### `codex-reviewer` = **実行不能（Codex の利用上限）**

`agent_selection.md` の規定どおり **Claude 側（`deep-reviewer`）へ縮退**した（報告のみ・許可不要）。
フェーズ完了判定前の `codex-adversarial-reviewer`（task_05）は、利用上限の復帰後に実施する。

## 3. 実機目視（ユーザー・2026-09-16 実施）

| # | 手順 | 期待 | 結果 |
|---|---|---|---|
| M1 | ダイアログを開いたまま **Win+D** → 復元 | アプリが復元できる | **OK** |
| M2 | M1 の復元後 | モーダル性が残る | **OK** |
| M3 | M1 の復元後 | 中間のダイアログも含め全窓が表示されている | **OK** |
| M4 | **3 段ネスト**で最小化 → 復元 | M1〜M3 と同じ + LIFO 復元が従来どおり | **OK** |
| M5 | **通常の最小化ボタン** | M1〜M3 と同じ | **実施不可**（下記） |

- **M5 = 実施不可（欠陥ではない）**: モーダル中は Win+D 以外に最小化する経路がない。
  ダイアログは `transient` のためタイトルバーに最小化ボタンがなく、本体の最小化ボタンは grab 中は押せない。
  代わりに試した**タスクバーのアイコンクリックでも最小化されなかった**（ユーザー確認）。
  最小化できなければ復元不能も起きないため、**是正タスクは起票しない**。

**stdlib ダイアログ（`messagebox` / `filedialog`）が開いた状態は対象外**（症状が残るのは確定済み）。

## 4. task_02c（H-1 の最小修正）

- `restore_grab` の差し戻しを **「`previous` を `grab_set()` できなかったすべての場合」** へ組み替え
  （**復元できなかった理由で区別しない**。破棄済みの窓が預かりに入っても `<Map>` の候補ループが
  台帳の最内へ落とす）。**`<Map>` 側・ガード・台帳は無変更**。
- テスト **A10〜A13** 追加（A10 = H-1 の回帰 / A11〜A13 = `<Unmap>` ガードの固定）+
  両テストモジュールの `setUp` で `_app_minimized` を初期化。
- **`reviewer` = 採用（完了可）**。参考指摘 2 件（`grab_set()` が `TclError` かつ非最小化時は
  従来どおり誰も掴まない〔v0.5 以前から同じ・新規劣化ではない〕/ H-1 を直接検証するのは A10 のみ）。
- **Codex は利用上限からの復帰後に実行**（`codex-implementer` で実装）。

## 5. 未解決事項

- task_05 へ送る文書項目: **M-1 / M-2 / L-2**。
- **フェーズ完了判定前の `codex-adversarial-reviewer`**（task_05）は利用上限に注意。
