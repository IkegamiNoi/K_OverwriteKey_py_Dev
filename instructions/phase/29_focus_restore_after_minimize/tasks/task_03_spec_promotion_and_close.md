# task_03_spec_promotion_and_close

## 目的

phase 29 の設計（暫定仕様 23 v0.5）を**正本へ昇格**し、暫定仕様を凍結してフェーズを閉じる。昇格先は暫定仕様 §8 が正
（条項は §3.1・残存リスクは §7）。**文書作業のみ**（`.claude/rules/agent_selection.md`「フェーズ末の正本反映タスクはメインが直接行う」）。

レイヤ制約: **コード差分ゼロ**（`keyseq/` ・ `tests/` ・ `tests_ui/` を変更しない）。

## 対象範囲（文書のみ）

### 1. `instructions/common/spec_detail/features.md` §4.6「モーダルダイアログの作法」（`:170`〜）

- **初期フォーカスの条項**（`:174-178`）: 「窓の前面化・フォーカス強制は行わない」は維持（初期フォーカスでは例外なし）。
- **「閉じた後・最小化から復元した後…規定しない」**（`:187-189`）を分ける: **閉じた後は規定しない** / 最小化から復元した後は下の最小化の条項へ。
- **最小化の条項**（`:207-208`「窓の表示・前面を操作しない」）を改訂し、フォーカス復帰を追加（暫定仕様 §3.1-1〜3・§3.1-6）:
  - 復元の際、アプリは**窓を表示し直したり前面へ持ち上げたりしない**（OS が戻した表示状態のまま）。
  - **復元後、キーボードフォーカスを表示中の最も内側のモーダル（= モーダル性を戻した窓）の、最後にフォーカスがあった入力先へ戻す**
    （初期フォーカス先ではない入力欄にいた場合もそこへ）。それに伴うアクティブな窓・重なり順の変化は許容する。
  - **復元の時点でアプリ自身が前面に出ているのにダイアログへキーが届かない状態なら、ダイアログを強制的にアクティブにする**
    （他のアプリが前面のときは強制しない＝入力を奪わない）。**API 名は書かない**（codebase_map 側）。
  - **最小化中に開いたモーダルには、その回の復元でフォーカスを戻さない**（開いたときの入力先の指定を優先。次回以降の復元では戻す）。
- **保証の範囲外**（`:215-219`）へ追記（§7 の残存リスク）: ①他のアプリが前面かどうかは判定した時点のもので、その直後に前面が変わった場合は
  ダイアログをアクティブにしうる ②最小化中に開いたモーダルでは、復元時にアプリがフォーカスを持たないと 2 回目の復元で入力先が窓自身になりうる。
- 既存の見出し・他条項は変えない。

### 2. `instructions/common/codebase_map.md` の `modal.py` 節（`:304`〜）

- `:103` のツリー行と `:304-306` の見出しに「最小化復元時のフォーカス復帰」を追記。
- `:312-313` の「推測型（`focus_lastfor()` / `after_idle`）は不採用」を **初期フォーカスでは** と範囲を限定。
- `install_minimize_grab_custody` の項（`:337-345`）に: `<Map>` で grab を返した後（**App の `<Map>` 全般で**）`after_idle` で
  `_restore_modal_focus` を予約 / 戻し先 = 予約実行時の `grab_current()` が台帳にあり表示中で最小化中に開いた窓でなければ、その
  `focus_lastfor() or window` へ `focus_set` / **`focus_get() is None` かつ `_is_app_foreground(app)` なら同じ先へ `focus_force`** /
  `_is_app_foreground` = 専用 `WinDLL("user32")` の `GetForegroundWindow`（`restype=HWND`）と `wm_frame()` の比較・**presentation 唯一の
  `ctypes`**・失敗は偽。**即時に `focus_set` しない理由**（実 App の 3 段ネストで外側の窓が戻らない）。
- `:345` の「`deiconify` / `lift` / `focus_force` を呼ばない（中間窓が消える）」を正確に: **`deiconify` は中間窓が消える**・`lift` は不要 /
  `focus_force` は上の条件のときだけ。
- モジュール状態に `_opened_while_minimized`（その回の復元まで）を追加（「3 つ」→「4 つ」）。固定テストに `tests_ui/test_modal_app_foreground.py`。
- 記述は実装の実体（`keyseq/presentation/modal.py`）で裏取りしてから書く。

### 3. `instructions/history/23_focus_restore_after_minimize.md` — M1 の注記と凍結

- 凍結前に `deep-reviewer` M1 の注記: §2 の v0.3 確定 1（「`focus_force` を呼ばない」）・§4-1・§1.2 末尾（「入力を奪わないのは Tk / OS の側で保たれる」）
  へ「→ v0.5 で改訂（§3.1-3）」を 1 行ずつ。
- ヘッダを凍結表記へ（手本 = `22_dialog_keyboard_focus.md:1-12`）: 状態 = 凍結（2026-09-23・v0.5・正本反映済）/ 昇格先 / 判断履歴の参照 /
  **本書の条項を実装の根拠に引かない**。履歴行は残し本文は書き換えない。

### 4. `.claude_data/state/decisions_archive/29_focus_restore_after_minimize.md`（新規）

`decisions.md` の phase 29 節（`:551`〜末尾）を集約（80〜120 行目安・手本 = `decisions_archive/28`）。少なくとも:
v0.1〜v0.3 の確定経緯 / v0.4（即時 `focus_set` の退行と `after_idle`）/ **v0.5（実機①不合格 → 測定 4 → 候補 A・B・C → A 採用）**/
敵対的レビュー 2 件と deep-reviewer M1・M2・L1〜L5 の判定 / 実機目視の結果 / 教訓（API 復元の probe は実操作の前面化順を再現しない・
素の Tk の probe は実 App で崩れる）/ `/refactor_check` の結果。
移設後、`decisions.md` 本体から phase 29 節を削除し、「アーカイブ索引」へ 1 行。

### 5. `instructions/phase/current.md` — 完了記載と次採番

phase 29 を完了へ（アクティブなフェーズ無し）/ 「直近の作業領域」を phase 29 へ差し替え / 次採番 = **phase 30 / 暫定 24 / decisions 30** /
暫定 23 を凍結へ。

### 6. `instructions/backlog/` — idea_34 を完了へ

`INDEX.md` の idea_34 行を `**完了**（phase 29・2026-09-23・正本反映済）` にして `INDEX_done.md` へ移動。

### 7. `/refactor_check`

`.claude/commands/refactor_check.md` に従う。**PHASE_BASE = `d8a250f`**（phase 29 起票コミット）。メトリクス収集は `verifier`、判定はメイン。
結果を完了報告と `decisions_archive/29` 末尾に記載（提案書起票はユーザー承認後）。

## 設計メモ / 制約

- **正本へ書くのは確定した規範のみ**（反証済みの方式・レビュー経緯は暫定仕様と archive に残す）。正本は**ユーザーから見た挙動**で書き、
  API 名・判定式は codebase_map へ（deep-reviewer M1）。
- 実装に合わせて仕様を緩めない。正本へ書くと実装と食い違う箇所を見つけたら、**作業を止めてユーザーへ報告**。
- 既存節の節番号・見出しは変更しない。別実装同期は**なし**（§8）。

## 読むファイル

1. `instructions/history/23_focus_restore_after_minimize.md`（§1.2 測定 4 / §2 / §3.1 / §3.2 / §7 / §8）
2. `instructions/common/spec_detail/features.md:170-230`
3. `instructions/common/codebase_map.md:100-105` / `:304-350`
4. `keyseq/presentation/modal.py`（裏取り）
5. `instructions/history/22_dialog_keyboard_focus.md:1-12` / `.claude_data/state/decisions_archive/28_dialog_keyboard_focus.md`（手本）
6. `.claude_data/state/decisions.md`（アーカイブ索引 + `:551`〜）/ `instructions/phase/current.md` / `instructions/backlog/INDEX.md`・`INDEX_done.md`

## 含まない

- コードとテストの変更（差分ゼロ）。deep-reviewer L2〜L5（テストの補強等）の実施。
- 最小化を伴わない再アクティブ化・閉じた後のフォーカスの規定（§7）/ idea_33。
- `/refactor_check` で挙がった改善の**実施**（起票要否の判断まで）/ `handoff.md` の再生成（`/save_handoff`）。

## 確認

- **コード差分ゼロ**: `git diff --stat 9012f52 -- keyseq tests tests_ui` が空。
- 標準検証 4 本が前回と同値（`verifier`: compile clean / `tests` 556 OK〔skip 7〕/ `tests_ui` 532 OK / smoke OK）。
- **反映漏れ照合**: 暫定仕様 §8 の各項目・§3.1-1〜3・§3.1-6・§7 が `features.md` / `codebase_map.md` に現れること。
- 追記した相対リンクが解決すること。`features.md` の差分が §4.6 の対象条項に限られること。
- `/refactor_check` の判定結果が出ていること。

## 完了条件

- 上記確認がすべて pass。
- **フェーズ完了判定のレビュー 2 系統**: `deep-reviewer`（正本の記述と実装の整合・既存条項との矛盾）+ `codex-adversarial-reviewer`。
  **指摘の採否はユーザー確認を経る**（task 単位の `reviewer` はこの 2 系統で代える）。
- `task_execution.md`「フェーズ完了時」のチェックリスト（昇格 + 凍結 / archive / current.md / idea_34 の INDEX_done 移動 / `/refactor_check`）を満たす。
- 実機目視は不要（task_02 で実施済み）。

## 完了記録（2026-09-23）

- **状態 = 完了**（phase 29 完了）。コード差分ゼロ（`git diff --stat 9012f52 -- keyseq tests tests_ui` 空）。
- 反映: `features.md` §4.6（「閉じた後は規定しない」の分離 / 最小化の条項へフォーカス復帰・条件つき強制アクティブ化・最小化中に開いた窓 /
  保証の範囲外へ残存リスク 2 件）/ `codebase_map.md` の `modal.py` 節 / 暫定仕様 23 を v0.5 で凍結（M1 注記）/
  `decisions_archive/29` 新規・`decisions.md` 索引 1 行 / `current.md`（アクティブ無し・次 = phase 30 / 暫定 24 / decisions 30）/
  idea_34 を `INDEX_done.md` へ / `/refactor_check` = **不要**（`modal.py` 187 行・+54・M1〜M6 該当なし。テスト 603 行は別タスク化候補へ 1 行）。
- 標準検証（`verifier`）: compile clean / `tests` 556 OK（skipped 7）/ `tests_ui` 532 OK / smoke OK / 追記リンクすべて解決。
- フェーズ完了判定レビュー: `codex-adversarial-reviewer` needs-attention 1 件 + `deep-reviewer` 修正要（軽微）F1〜F11 →
  **F1〜F10 を修正して採用・F11 保留**（ユーザー承認）。**本定義の「初期フォーカスの条項は維持」は F1 で改め**、
  「開いた時点では」の範囲限定と最小化の条項への参照を加えた（暫定仕様 §8 のとおり）。
