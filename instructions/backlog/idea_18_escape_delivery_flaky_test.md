# idea_18_escape_delivery_flaky_test.md

## 概要

`tests_ui/test_dialog_teardown_flows.py` の **`test_t2_escape_resumes_quarantine_once` が
CPU 負荷下で不定期に fail する**。`event_generate("<Escape>")` の配送がタイミングに依存するため。
**失敗するとフック停止カウンタが 1 残り、同クラスの後続 4 件が setUp のドレイン検査で
連鎖して落ちる**（1 件の不安定が 5 件の赤になる）。**production の欠陥ではない**。

## 起票経緯（2026-09-13）

出所: [phase 16](../phase/16_dialog_transient_parent/phase.md) task_04 の統合確認。
一括実行が約 3 割で fail したため切り分けたところ、**phase 16 の差分とは無関係**で
**phase 15 の時点から存在していた**ことが判明した（下記「現状」の実測）。
ユーザー判断（2026-09-13）で**別 idea へ分離**し、phase 16 では記録のみとした。

## 現状

- 該当テスト: `tests_ui/test_dialog_teardown_flows.py:144-162`。
  `dialog.focus_force()` → `self.app.update()` → `dialog.event_generate("<Escape>")` →
  `self.app.update()` の順で、**Escape が配送されなければダイアログが閉じず**
  `resume.assert_called_once_with()` が「0 回」で落ちる。
- **同じ機構の別テストでも観測**（2026-09-19・phase 24 task_01 の統合確認）:
  `tests_ui/test_quarantine_manage_flow.py:326`
  `test_escape_and_window_close_keep_action_empty (close='escape')` が一括実行で 1 度だけ fail
  （`get_hook_pause_count()` が `1 != 0`）。**単独実行 20/20 pass・一括の再実行も 446 全 pass** で、
  当該フェーズの差分（型正規化）とは無関係。本 idea と同じ Escape 配送依存。
- **連鎖の仕組み**: 同クラスは `setUpClass` で `App` を共有し、各テストの冒頭で
  `get_hook_pause_count() == 0` を確認する（phase 15 task_03 で入れたドレイン）。
  t2 が閉じ損ねるとカウンタが 1 のまま残り、**後続 4 件が setUp で落ちる**。
- **実測（2026-09-13）**:

  | 条件 | 結果 |
  |---|---|
  | 現在（phase 16）・単独実行・通常負荷 | 12 回すべて pass |
  | 現在・単独実行・CPU 負荷下（busy loop 4 本） | 6 回中 **1 回 fail** |
  | **phase 15 時点（`0beb1b4`）・単独実行・CPU 負荷下** | 6 回中 **2 回 fail** |

  → **phase 16 由来ではない**。負荷下でのみ再現する既存の弱さ。
- 既知の注意点として `.claude_data/state/handoff.md` に
  「`event_generate("<Escape>")` は非表示ウィンドウでは配送されない」がある。
  当該テストは `focus_force()` を行っているが、**負荷下ではそれでも取りこぼす**。

## 提案（方向性・要設計）

- **案 A: Escape 依存をなくす** — 結線されたハンドラを直接呼ぶ（`dialog.event_generate` の
  代わりにバインド先を呼ぶ）。**配送タイミングに依存しなくなる**が、
  **「Escape が結線されている」ことの検証が弱くなる**ため、結線の有無は静的検査で別途固定する。
- **案 B: 配送を待つ** — `event_generate` 後にダイアログの破棄をポーリングで待つ
  （上限つき）。**検証内容は変えずに安定させられる**が、待ち時間の分だけ遅くなる。
- **案 C: 連鎖を切る** — 各テストの `setUp` でカウンタを 0 へ強制的に戻す。
  **赤の件数は 5 → 1 に減る**が、**根本原因は残る**（むしろ検出が弱くなる恐れ）。
- **推奨は案 B**（検証内容を保ったまま安定する）。案 A と併用してもよい。

## 想定スコープ

- **含む**: `tests_ui/test_dialog_teardown_flows.py` の当該テスト（と、同じ形の
  Escape 依存テストが他にあれば棚卸し）。
- **含まない**: production コードの変更（**本件はテストのみの問題**）。
  phase 15 の受け入れ条件そのものの見直し。
- **影響レイヤ**: テストのみ。**仕様変更なし**。
- **優先度**: 低〜中（**通常の実行では再現しないが、並行作業中の一括実行で偽の赤になる**）。
