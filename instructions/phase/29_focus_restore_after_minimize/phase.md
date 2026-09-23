# phase.md

## フェーズ名

最小化から復元した後のキーボードフォーカス（focus_restore_after_minimize）

## フェーズの目的

モーダルダイアログを開いたままアプリを最小化 → 復元したとき、**モーダル性（grab）だけでなくキーボードフォーカスも
最内の表示中モーダルへ戻す**（最後にフォーカスがあった widget へ）。復元後にクリックしなくても Escape 等がダイアログへ届くようにする。

- **対象レイヤ = presentation のみ**（`keyseq/presentation/modal.py`）。**データスキーマ・domain / application の変更は無い**。
- 起票元: [idea_34](../../backlog/idea_34_focus_restore_after_minimize.md)（phase 28 task_05 の実機目視 C② で再現）。
- 主入力（暫定仕様）: [23_focus_restore_after_minimize.md](../../history/23_focus_restore_after_minimize.md)
  （**v0.3・ユーザー確定済・実装着手可**）。
- モード: **暫定仕様先行モード**。番号対応: phase 29 / 暫定 23 / decisions 29。

## 確定（ユーザー 2026-09-23）

- **App の `<Map>` で grab を返した直後に、即時で `focus_set`** する（暫定仕様 §3.1-4。キュー経由の復元では
  `<FocusIn>` が `<Map>` より先に届くため `<FocusIn>` 待ちは戻らないと実測で反証・§1.2）。
- **戻し先の窓 = 復元処理後の grab 保持者が台帳 `_active_modals` に同一性で含まれ表示中ならその窓**（1 つの定義で全経路を覆う・§3.1-2）。
  widget は `focus_lastfor()`（無ければ窓自身）。stdlib ダイアログ・台帳外・非表示は触らない。
- **使うのは `focus_set` のみ**。`deiconify` / `lift` / `focus_force` は呼ばない（既存テスト a4 を維持）。
  **正本の最小化の条項は API 単位へ言い換え**、それに伴うアクティブな窓・重なり順の変化は許容する（§2-1）。
- **最小化中に開いたモーダルには復帰を行わない**（初期フォーカス要求を優先・§3.1-6）。
- **閉じた後のフォーカスは規定しない** / **最小化を伴わない再アクティブ化は対象外**（実機目視で記録のみ）。

## スコープ

### 含む

- `modal.py`: フォーカス復帰の関数（例 `_restore_modal_focus(app)`）と `return_custody` からの呼び出し
  （預かりが空の経路も通す）/ 最小化中に `grab_modal` された窓の記録と除外。
- `tests_ui/test_minimize_grab_custody.py`: 暫定仕様 §5 の ①〜⑨ の単体検査（期待値はダイアログごとの具体 widget）。
- 実機目視（暫定仕様 §6-6 の ①〜⑦）。
- 正本反映（`features.md` §4.6 / `codebase_map.md` の `modal.py` 節）・暫定仕様 23 の凍結・`decisions_archive/29`・
  `current.md`・idea_34 の `INDEX_done.md` 移動・`/refactor_check`。

### 含まない（後送り）

- 最小化を伴わない再アクティブ化（Alt+Tab で最小化されていない窓へ戻る・クリック）でのフォーカス復帰（暫定仕様 §7）。
- 閉じた後のフォーカスの規定 / stdlib ダイアログが開いている間の最小化 / 最小化中に開いたモーダルが復元できるか。
- idea_33（フック再開 flaky）/ 同型スケルトンの共通化（`current.md` 別タスク化候補）。

## このフェーズで読むファイル

1. `instructions/history/23_focus_restore_after_minimize.md`（主入力。§1.2 / §3 / §5 / §6）
2. `keyseq/presentation/modal.py`（全体・133 行。`install_minimize_grab_custody` / `grab_modal` / `restore_grab`）
3. `tests_ui/test_minimize_grab_custody.py`（全体・321 行。組み立てと a2 / a4 / a6 / a9 / a10）
4. `keyseq/presentation/dialogs/action_dialog.py:48-49`（`value_entry` = 初期フォーカス先）/ `:59-62`（`action_label_entry` = §5 ⑨ の別の入力欄）/ `:120-135`（`grab_modal(..., focus=self.value_entry)`）
5. 正本: `instructions/common/spec_detail/features.md` §4.6「モーダルダイアログの作法」（`:170-225` 付近）/
   `instructions/common/codebase_map.md` の `modal.py` 節（`:303`〜）

## タスク

- **task_01**: `modal.py` にフォーカス復帰を実装（§3.1-1〜6・§3.2）+ 単体検査 ①〜⑨（§5）。presentation + tests_ui
- **task_01b**: 実機目視①不合格を受けた v0.5 の条件つき `focus_force`（§3.1-3・§3.2）+ 検査 ⑩〜⑭。presentation + tests_ui
- **task_02**: 統合確認（`verifier`・変異検査を含む）+ 実機目視（暫定仕様 §6-6 の ①〜⑦）
- **task_03**: 正本反映（`features.md` §4.6 の最小化の条項・初期フォーカスの条項・「規定しない」の一文の改訂 +
  `codebase_map.md` の `modal.py` 節）+ 暫定仕様 23 の凍結 + `decisions_archive/29` 作成 + `current.md` 更新 +
  idea_34 を `backlog/INDEX_done.md` へ移動 + `/refactor_check`

## レビュー方針

- task_01 = `reviewer`（重点: §3.1-2 の定義が全経路で一意か / 既存の grab 復元〔a1〜a13〕を壊していないか /
  `focus_force` / `lift` / `deiconify` を呼んでいないか / 期待値が実装をなぞるだけの検査になっていないか）。
- task_02 = `deep-reviewer` + `codex-reviewer`（統合）。
- task_03（フェーズ完了判定前）= `deep-reviewer` + `codex-adversarial-reviewer`。**昇格する文言は既存条項と突き合わせる**
  （phase 28 で「保存せずに閉じる」が既存条項と矛盾した教訓）。
- **自動テストでは OS フォーカスを持たずアクティブ化の経路を通らないことが多い**（暫定仕様 §5 注記）。
  **中間窓が消えないこと・実際に文字が届くことの最終確認は実機目視**で行う。
