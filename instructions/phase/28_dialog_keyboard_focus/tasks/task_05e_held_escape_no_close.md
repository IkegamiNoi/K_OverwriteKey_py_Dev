# task_05e_held_escape_no_close

## 目的

記録中・取得中に Esc を**押しっぱなし**にすると、キーリピートの 2 発目以降が通常時の Escape として
扱われ、**停止 → 閉じる**になる退行（task_05c で混入・ユーザーが実機で確認）を直す。
規範は暫定仕様 22 **v0.7 §3.6.1**（停止に使った Esc を離すまでは Escape で閉じない）。
あわせて §8-14② のとおり、群 A の「閉じない」検査の送り方を期限つきのフォーカス確保へ揃える（M2）。

レイヤ制約: **presentation 限定**（`keyseq/presentation/dialogs/` の 3 ファイル）+ `tests_ui/`。
domain / application・スキーマは不変。`modal.py` は変更しない。

## 対象範囲（presentation 3 ダイアログ + tests_ui）

### 1. keyseq/presentation/dialogs/action_dialog.py / trigger_dialog.py / keymap_edit_dialog.py

3 ファイルとも同じ形で直す（停止処理を持つのはこの 3 経路のみ。`preset_dialog.py` は対象外）:

- **印（例: `self._escape_held = False`）**を `__init__` で初期化する（`<Escape>` の bind より前）。
- `_on_escape` を次の分岐にする（**ハンドラは 1 つのまま**・§3.6 の規範を維持）:
  1. **記録中 / 取得中 → 停止し、印を立てて `"break"`**（**印の有無より先に判定する**）
  2. 印が立っている → 何もせず `"break"`（**抑止するのは閉じる動作だけ**）
  3. それ以外 → 従来どおり `self.destroy()`
- `self.bind("<KeyRelease-Escape>", <印を消す関数>)` を `__init__` で**常時**結線する（`<Escape>` の bind の隣）。
  印を消す関数は `"break"` を返さない（他の KeyRelease 処理を止めない必要は無いが、止める理由も無い）。
- **印を立てるのは Escape による停止のときだけ**。ボタン・記録完了など Esc 以外の停止では立てない
  （`_stop_recording` / `_stop_capture` 本体には手を入れない）。
- `__init__` の最後の文が `grab_modal(...)` であることは維持する（静的検査
  `tests_ui/test_nested_modal_grab.py` の `test_grab_modal_is_last_initialization_statement`）。

### 2. tests_ui/escape_delivery.py

- `_acquire_focus(app, dialog, focus_timeout, progress)` を**公開名**（例: `acquire_focus(app, dialog, *, focus_timeout=2.0)`）で
  使えるようにする。`send_escape` はそれを使う形に揃え、**挙動（期限・1 周目は待たない・待機中も `update`）は変えない**。
  旧名を残す互換ラッパは作らない（呼び出し元は同ファイル内のみ）。

### 3. tests_ui/test_dialog_escape_binding.py

- `_assert_escape_stops_without_closing`（`:163-181`）の `focus_force()` + `update()` 1 回 + 確認を、
  **2. の公開した確保関数**に置き換える（アサートの中身は変えない）。
- **押しっぱなしのテストを追加**（3 経路を subTest で。既存 `test_group_a_active_escape_stops_then_second_escape_closes`
  と同じ組み立て）:
  1. 記録 / 取得を開始 → Escape（停止・窓は残る・印あり）
  2. **KeyRelease を挟まずに** Escape をもう 1 回（リピート相当）→ **窓は残る**・フック停止の解除は 0 回
  3. `<KeyRelease-Escape>` を送る → 印が消える
  4. Escape → **閉じる**・フック停止の解除はちょうど 1 回
- **印が残ったままの再開**のテストを追加（3 経路）: 停止（Escape）→ KeyRelease を送らずに記録 / 取得を再開 →
  Escape → **停止する（窓は残る）**。判定順を逆にすると赤になること（§3.6.1）。
- 既存の `test_group_a_active_escape_stops_then_second_escape_closes` は、停止と 2 回目の Escape の間に
  `<KeyRelease-Escape>` を送る形へ直す（実キー操作の順序に合わせる。**アサートは弱めない**）。

### 設計メモ / 制約

- **`<KeyRelease-Escape>` と `ActionDialog` の記録用 `<KeyRelease>`（`:284` で `add="+"`）の関係を確認すること**。
  同一 widget では具体的なパターン（`<KeyRelease-Escape>`）だけが発火するため、記録中に Esc 以外を離したときの
  `_on_key_release` は影響を受けない。Esc を離すのは停止後（`<KeyRelease>` は `:293` で unbind 済）なので
  記録処理と競合しない。**この前提が崩れる経路を見つけたら実装を止めて報告**。
- 実測（暫定仕様 §3.6.1）: Windows の Tk はリピート中に KeyRelease を挟まない。テストは
  `event_generate` で順序を作るので OS に依存しない。
- 状態分岐の条件を増やすだけで、**新しい閉じ方は作らない**（通常時の Escape は従来どおり `destroy`）。

## 読むファイル

1. `instructions/history/22_dialog_keyboard_focus.md` の **§3.6 / §3.6.1 / §8-12 / §8-14**
2. `keyseq/presentation/dialogs/action_dialog.py:125-140` / `:266-300`（`_on_escape` と記録の開始・停止）
3. `keyseq/presentation/dialogs/trigger_dialog.py:48-100`
4. `keyseq/presentation/dialogs/keymap_edit_dialog.py:48-105`
5. `tests_ui/escape_delivery.py`（全体・約 70 行）
6. `tests_ui/test_dialog_escape_binding.py:1-70`（setUp と共通部）/ `:139-215`（群 A のテスト）

## 含まない

- 正本 `features.md` への反映（**task_06**。v0.7 §4 の文言で書く）。
- `PresetDialog`（Esc の別用途なし）/ 群 B・C の Escape。
- 押下中の Esc を**記録対象**にする等の記録仕様の変更。
- idea_33（`after(0)` のフック再開 flaky）/ idea_34（最小化復帰後のフォーカス）。
- python の実行（Codex は実行できない。実測は `verifier`）。

## 確認

`.venv` の python（`..\..\..\.venv\Scripts\python.exe`）で `verifier` が実施する。

1. `python -m compileall -q keyseq` clean。
2. `python -m unittest tests_ui.test_dialog_escape_binding -v` 全 pass（追加した押しっぱなしのテスト 3 subTest を含む）。
3. **変異検査**: 3 ダイアログの `_on_escape` から「印が立っていたら閉じない」分岐を一時的に外すと、
   押しっぱなしのテストが**赤になる**こと / 判定順（記録・取得中 → 印）を逆にすると**再開のテストが赤になる**こと
   （確認後は元へ戻す。`git diff` で戻ったことを確認）。
4. `python -m unittest tests_ui.test_nested_modal_grab` pass（`grab_modal` が `__init__` の最後の文）。
5. `python -m unittest discover -s tests` 556 ran OK（skipped 7・不変）。
6. `python -m unittest discover -s tests_ui` 全 pass（507 + 追加分）。
7. `python -m tests.smoke_app` が `SMOKE OK`。

## 完了条件

- 上記確認 pass・**`reviewer` 採用**。
- **実機目視 A3（ユーザー）**: ActionDialog（記録中）/ TriggerDialog・KeymapEditDialog（取得中）で
  「Esc を押しっぱなし → 止まるだけで窓は残る → 離してもう一度 Escape → 閉じる」を確認する（§8-14③）。
  本タスクで実施する（task_06 へ持ち越さない）。

## 完了記録（2026-09-23）

- **状態 = 完了**。実装 = `codex-implementer`（production は 3 ダイアログ各 +8 行・tests_ui 2 ファイル）。
- 実測（`verifier`）: compile clean / `test_dialog_escape_binding` 8 OK（押しっぱなし 3 subTest・再開 3 subTest を含む）/
  **変異検査**: 印の分岐を外す → 押しっぱなしのテスト 3 subTest が赤 / 判定順を逆にする → 再開のテスト 3 subTest が赤
  （いずれも復元を `git diff` で確認）/ `test_nested_modal_grab` 11 OK / `tests` 556 OK（skipped 7）/
  `tests_ui` **509 OK ×2**（507 → +2）/ smoke OK。
- レビュー = `reviewer` **完了可**（参考 2 件: `_escape_held` の直接参照〔`__init__` を通らない経路なし〕/
  `acquire_focus` の `progress` 引数〔`send_escape` の診断維持に必要〕。いずれも修正不要）。
- **実機目視 A3（ユーザー・2026-09-23）**: アクション / トリガー / キーマップの 3 経路とも想定どおり
  （押しっぱなし → 止まるだけで窓は残る → 離して Escape → 閉じる）。
