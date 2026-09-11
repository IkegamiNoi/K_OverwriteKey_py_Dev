# idea_16_wm_close_skips_destroy_override.md

## 概要

ダイアログを **× で閉じると Python 側の `destroy()` override が呼ばれない**ため、
その中に書かれた **`resume_hook_after_dialog()` が走らず、フック停止カウンタがずれたまま残る**。
以後ダイアログを開いてもフックが自動停止しなくなり、**編集中のキー入力が誤爆し得る**。
**該当は 9 ダイアログ中 5 クラス**（`protocol("WM_DELETE_WINDOW")` を登録していないもの）。

## 起票経緯（2026-09-11）

出所: phase 14 task_04 の起票前調査（§3-6 の扱いをユーザーと詰める過程で判明）。
「初期化に失敗して残ったウィンドウは × で閉じられるか」を確認する過程で、
× 閉じの破棄経路が `destroy()` override を通らないことを実測で確認した。
**grab の復元は `<Destroy>` イベントに結線されているため × でも正しく働く**
（[phase 14](../phase/14_nested_modal_grab_restore/phase.md) の成果には影響しない）。
**phase 14 以前から存在する独立した不具合**のため、本フェーズには合流させない。

## 現状

**実測（`.venv` の python で確認）**

```
count while open        = 1
count after tcl-destroy = 1   ← 0 に戻らない
```

`ActionDialog` を開いて Tcl レベルで破棄（= WM の × と同じ経路）したところ、
`hook.get_hook_pause_count()` が 1 のままだった。
別の最小再現でも、Tcl レベル破棄では `<Destroy>` イベントのみが発火し、
Python の `destroy()` override は呼ばれないことを確認した。

**仕組み**

- 8 クラスが `__init__` で `suspend_hook_for_dialog()` を呼び、`destroy()` override で
  `resume_hook_after_dialog()` を呼ぶ（`dialogs/` 各ファイル）。
- `HookController` の停止は**ネスト対応のカウンタ**
  （`controllers/hook_controller.py:24-42`）。`suspend` はカウンタが 1 になった瞬間だけ
  `stop_hook()` を呼び、`resume` は 0 に戻った瞬間だけ `start_hook()` を呼ぶ。
- × 閉じで `resume` が飛ぶとカウンタが 1 のまま残る。

**`protocol("WM_DELETE_WINDOW")` を登録していない 5 クラス**（= × で override を通らない）:
`action_dialog.py` / `keymap_edit_dialog.py` / `layout_delete_dialog.py` /
`preset_manager.py` / `trigger_dialog.py`。
登録済みは `orphan_sweep_dialog.py:23` / `quarantine_manage_dialog.py:23` /
`reference_cleanup_dialog.py:54` の 3 クラス。`preset_dialog.py` は
`suspend` も `destroy()` override も持たないため対象外。

**影響**

- フック自体は画面の「開始（フックON）」ボタン（`views/full_view/hook_frame.py:18` /
  `views/compact_view/hook_frame.py:20` → `hook.toggle_hook`）で**手動再開できる**。
  `start_hook()` は停止カウンタを参照しないため。
- **ずれは手動再開では解消しない**。以後 `suspend` はカウンタを 2 にするだけで
  `stop_hook()` を呼ばず、**ダイアログ表示中もフックが生きたまま**になる
  （= 一時停止の目的である誤爆防止が失われる）。確実に戻すにはアプリ再起動が要る。

## 提案（方向性・要設計）

- **案 A: 5 クラスへ `protocol("WM_DELETE_WINDOW", self.destroy)` を追加する**。
  既に登録済みの 3 クラスと同じ形になり、差分は 1 行 × 5。最小。
  ただし「override を書いたら protocol も要る」という暗黙の規約が残り、次の人が同じ穴を開ける。
- **案 B: 後始末を `<Destroy>` バインドへ寄せる**。`grab_modal` と同じ結線にすれば
  閉じ方によらず必ず走る。`destroy()` override と二重に走らないよう整理が要る。
- **案 C: ダイアログ同型スケルトンの共通化に合流させる**
  （phase 11 の `/refactor_check` 候補送り・phase 14 でも分離した項目）。
  スケルトンを 1 箇所へ寄せるなら、後始末の結線もそこで 1 度だけ書けばよい。
- 併せて **`resume` の取りこぼしを検出する手段**（カウンタが 0 に戻らないまま
  ダイアログが全て閉じた状態を検知する等）を入れるかも検討対象。

## 想定スコープ

- **含む**: `dialogs/` の後始末結線、`HookController` のカウンタ運用の見直し（案 B / C を採る場合）。
- **含まない**: grab の復元（phase 14 で対応済・`<Destroy>` 結線のため × でも働く）。
  フック実装そのもの（`hook_coordinator` 以下）。
- **影響レイヤ**: presentation 限定。スキーマ変更なし。
- **仕様変更**: 正本 `spec_detail/key_input.md` にダイアログ中のフック停止の規定があるため、
  「閉じ方によらず再開する」ことを明文化するなら仕様変更フローが要る見込み。
- **着手時の注意**: 案 C を採るならスケルトン共通化が先行する。単独で急ぐなら案 A が最小。
