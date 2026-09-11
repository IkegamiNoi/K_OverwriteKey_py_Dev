# 暫定仕様 13: ダイアログ後始末の確実な実行（dialog_teardown_on_close）

> 状態: **未凍結・v0.4・ユーザー確定済・実装着手可・主入力**。本書がこのフェーズの確定設計（フェーズ中は正本を直接改訂しない）。
> フェーズ末タスクで正本 `instructions/common/spec_detail/` へ昇格し本書を凍結する。
> 起票元: [idea_16](../backlog/idea_16_wm_close_skips_destroy_override.md)
> （phase 14 task_04 の起票前調査で実測により発見・2026-09-11 起票）。
> **正本違反の是正であり、仕様追加ではない**（`key_input.md` §7.2 が既に現状を禁じている）。
>
> **v0.2（2026-09-12）**: 起票時 `deep-reviewer` レビュー（指摘 16 件）を反映。
> **①アプリ終了時の前提が誤りだった**（現状でも `destroy()` は走る）ため §1-⑦ / §4-3 を書き直し
> **②登録方式を代替 A（`HookController` へ寄せる）へ変更**（ユーザー確定）
> **③実行タイミングを代替 B（`after(0)` 遅延）へ変更**（ユーザー確定）
> ④非ダイアログ経路（try/finally 形）を明示的にスコープ外へ ⑤受け入れ条件に phase 14 の非退行を追加
> ⑥正本違反の主論拠を差し替え ⑦行番号の誤り 3 件を訂正。
>
> **v0.3（2026-09-12）**: 確定前の `codex-adversarial-reviewer` レビューを反映。
> **`after(0)` 遅延だけでは受け入れ条件 4 を満たせない**という条項間の矛盾を解消
> （**try/finally 形の 5 系統は同期解除のままなので、終了時に `start_hook()` が走り得る**）。
> **終了ガードを `HookController` に持たせる**方式を §4-3 へ追加し、§9 と条件 4 を整合させた。
>
> **v0.4（2026-09-12・ユーザー確定）**: §6 の確認事項 2 件を**推奨どおり確定**し §2 へ移した。
> **設計は確定・実装着手可**。

---

## §1 目的 / 背景

ダイアログを **× で閉じると Python 側の `destroy()` override が呼ばれない**ため、
その中に書かれた **`resume_hook_after_dialog()` が走らず、フック停止カウンタがずれたまま残る**。

**正本 `key_input.md` §7.2 は「UI 編集中（キャプチャ・ダイアログ等）はフックを停止する
（ネスト対応: 多重に停止要求が重なっても、すべて解除されるまで再開しない）」と規定している。**
**現状はこの前段「UI 編集中はフックを停止する」に明示的に違反する**。
カウンタが 1 のまま残ると、**次にダイアログを開いても `suspend` はカウンタを 2 にするだけで
`stop_hook()` を呼ばず、ダイアログ表示中もフックが生きたままになる**
（`controllers/hook_controller.py:24-30`）。編集中のキー入力が誤爆し得る。
したがって `.claude/rules/spec_change_workflow.md` の既定どおり **正本が正・実装を直す**。

### 現状監査（2026-09-12・すべて `.venv` の python で実測）

**① × 閉じでは Python の `destroy()` override が呼ばれない**

Tcl レベルの破棄（WM の × と同じ経路）では **`<Destroy>` イベントのみ発火**し、
Python の `destroy()` override は呼ばれない。実アプリでも `ActionDialog` を開いて
Tcl レベルで破棄すると `hook.get_hook_pause_count()` が **1 のまま 0 に戻らない**。

**② `protocol("WM_DELETE_WINDOW")` の登録有無で挙動が分かれる**

| クラス | suspend | protocol 登録 | × で `destroy()` が走るか |
|---|---|---|---|
| `action_dialog.py` | ○ | **なし** | **走らない** |
| `keymap_edit_dialog.py` | ○ | **なし** | **走らない** |
| `layout_delete_dialog.py` | ○ | **なし** | **走らない** |
| `preset_manager.py` | ○ | **なし** | **走らない** |
| `trigger_dialog.py` | ○ | **なし** | **走らない** |
| `orphan_sweep_dialog.py` | ○ | あり（`:25`） | 走る |
| `quarantine_manage_dialog.py` | ○ | あり（`:25`） | 走る |
| `reference_cleanup_dialog.py` | ○ | あり（`:56`） | 走る |
| `preset_dialog.py` | — | なし | **override 自体が無い**（対象外） |

**③ `destroy()` override の中身は 3 種類ある**（後始末の性質が違う）

| 処理 | 該当 | ウィジェットに触るか | 飛んだときの実害 |
|---|---|---|---|
| `resume_hook_after_dialog()` | 8 クラス | **触らない** | **カウンタがずれて回復不能**（本件の本体） |
| `_stop_capture()` / `_stop_recording()` | `keymap_edit` / `trigger` / `action` | **触る**（`configure` / `unbind`） | **なし**（自ウィジェットへのバインド解除で、破棄されるので実質無意味） |
| `scan_dirs` の収集（`listbox.get`） | `orphan_sweep` | **触る** | 編集内容が失われる。**ただし protocol 登録済なので × でも走る** |

**④ 【最重要】子ウィジェットは親の `<Destroy>` より先に破棄される**

`Toplevel` の `<Destroy>` ハンドラから子 `Listbox` へ触ると
**`TclError: invalid command name ...`** になる。子の `<Destroy>` が先に発火し、
親のハンドラが走る時点で**子は既に存在しない**。
→ **破棄イベントに載せてよいのは「ウィジェットに触らない後始末」だけ**。

**⑤ `<Destroy>` は既に `grab_modal` が使っている**

`keyseq/presentation/modal.py:46` が `window.bind("<Destroy>", restore_grab, "+")` を呼ぶ
（phase 14 task_05b で `"+"` 化済み）。**追加のハンドラを足しても互いに潰し合わない**。
ただし**同じイベントが子ウィジェットの破棄でも発火する**ため、
**`event.widget is window` の判定が要る**。

**⑥ フック再開の影響範囲（v0.2 で追記・危険度が上がった）**

`HookController.resume_hook_after_dialog`（`controllers/hook_controller.py:32-42`）は
カウンタが 0 に戻った時だけ `start_hook()` を呼ぶ。`start_hook()`（`:74-105`）は:

- **`validate_hook_configuration()` が重複キー検出時に `messagebox.showerror` を同期で開く**
  （`:168`・`:183`・`:185`）。**破棄イベントの中で入れ子のモーダルループが回り grab も奪う**。
- **`hook_coordinator.start()` が OS のグローバルフックを登録する**（`:88`）。
- `layout.refresh_keyboard_window()` / `trigger_panel.update_status()` がウィジェットに触る（`:104-105`）。

**⑦ 【v0.2 で訂正】アプリ終了時は現状でも `destroy()` override が走る**

v0.1 は「終了時も走らない」と書いていたが**誤り**。実測:

```
root.destroy()     -> ['python-destroy-ran']   # 子の Python destroy が再帰的に呼ばれる
tcl destroy root   -> []                        # Tcl レベルなら呼ばれない
```

`App.on_close`（`app.py:527-539`）は **`stop_hook()` の後に `self.destroy()`** を呼ぶため、
**ダイアログを開いたままアプリを閉じると、今日でも後始末が走り `start_hook()` が
終了処理の最中に動き得る**（`hook_was_active_before_dialog` が真なら）。
**これは案 B が新たに生む危険ではなく、既存の潜在バグ**である。本フェーズで一緒に塞ぐ。

**⑧ 同じカウンタを触る非ダイアログ経路が 5 系統ある**（スコープ外・§9）

`config_io/io_dialogs.py` / `config_io/child_save_dialog.py`（3 箇所）/
`controllers/keymap_panel_controller.py` は **try/finally 形**で対になっており、
**`<Destroy>` を持たない素の `Toplevel` や非ウィンドウ処理**のため本件の対象外。
`controllers/key_capture.py` と `keyboard_window.py` も同じカウンタを触るが、
**ダイアログの閉じ方の問題ではない**ため本フェーズでは扱わない（§9 で明示的に除外）。

## §2 確定事項（ユーザー 2026-09-12）

- **後始末を `destroy()` override から破棄イベントへ寄せる**（案 B）。
  閉じ方（OK / キャンセル / Escape / × / プログラムからの `destroy` / アプリ終了）によらず
  必ず走る形にする。**`protocol` を 5 クラスへ足すだけの案 A は採らない**
  （暗黙の規約が残り、アプリ終了経路も塞げないため）。
- **【v0.2・代替 A】登録は `HookController` へ寄せる**。汎用ヘルパ `on_teardown` は作らない。
  **`suspend_hook_for_dialog(window)` が停止と解除登録を原子的に行う**（§4-1）。
- **【v0.2・代替 B】後始末は破棄イベントの中で同期実行せず `after(0)` で遅延する**（§4-2）。
- **【v0.3】終了ガードを `HookController` に持たせる**。アプリ終了が確定したら
  **どの解除経路からもフックを再開しない**（§4-3）。
- **【v0.4】空になる `destroy()` override は削除する**（4 クラス: `layout_delete` /
  `preset_manager` / `quarantine_manage` / `reference_cleanup`）。
  「何もしない override」を残さない。
- **【v0.4】意味が空になる既存テストは書き換える**。`tests_ui/test_app_ui_flows.py:1325-1341` は
  override 削除後に `tk.Toplevel.destroy` の patch へ解決し**検証内容が空になる**ため、
  **「保存が走らないこと」を見る観測点へ移す**（フックの再開は本フェーズの新規テストが見る）。
- **ダイアログ同型スケルトンの共通化とは合流しない**（`/refactor_check` の候補送りのまま）。
- **モードは暫定仕様先行**。番号対応: phase 15 / 暫定 13 / decisions 15。

## §3 後始末の分類（設計の土台）

**後始末を 2 種類に分け、置き場所を変える**。

- **T1: 状態の後始末**（アプリ側の状態を戻す。**ウィジェットに触らない**）
  → **破棄イベントへ寄せる**。閉じ方によらず必ず走る。
  現時点の該当は **`resume_hook_after_dialog()` の 1 つだけ**。
- **T2: ウィジェットに触る後始末**（値の収集・ウィジェットの再設定）
  → **`destroy()` override に残す**。破棄イベントの時点では子が既に破棄されている（§1-④）。
  該当は `scan_dirs` の収集 / `_stop_capture` / `_stop_recording`。

**この分類を作法として正本へ昇格する**（§8）。新しい後始末を足す人が迷わないようにするのが目的。

## §4 実装方針

### 4-1. 【代替 A】`HookController` が停止と解除登録を原子的に行う

```python
def suspend_hook_for_dialog(self, window: tk.Misc | None = None) -> None:
    """フックを一時停止する。window を渡すと、その破棄時に自動で解除する。"""
```

- **`window` 省略時は現行と完全に同じ挙動**（既存の try/finally 形 5 系統は無変更・§1-⑧）。
- `window` を渡したときだけ `window.bind("<Destroy>", handler, "+")` で解除を予約する。
  **`"+"` 必須**（`grab_modal` を潰さない）。
- **`event.widget is window` でなければ何もしない**（子ウィジェットの破棄で発火するため）。
- **解除は 1 度だけ**（`grab_modal` の `restored` フラグと同型）。
- **利点**: 各ダイアログの差分が **`suspend_hook_for_dialog(self)` への 1 行置換 +
  `destroy()` override から 1 行削除**だけになる。登録忘れ・順序ミス・過剰 decrement の
  余地が構造的に消え、終了ガードも `HookController` 内に収まる。

### 4-2. 【代替 B】解除は `after(0)` で遅延する

破棄イベントのハンドラでは**予約だけ**を行い、実行はイベントループへ回す。

- **理由 3 つ**: ①`start_hook()` が**同期でメッセージボックスを開き得る**（§1-⑥）ため、
  破棄処理の途中で入れ子のモーダルループを回さない ②**`grab_modal` の復元処理と
  同一イベント内で競合させない**（phase 14 の保証を退行させない）
  ③**アプリ終了時は保留中の `after` が実行されない**ため §1-⑦ の危険が構造的に消える。
- **代償（受容）**: `wait_window()` から戻った直後は**まだ再開前**になる。
  連続してダイアログを開くとカウンタが一時的に 1 多いままになるが、**最終値は正しい**。
  むしろ停止・再開のばたつきは減る。
- **テスト上の注意**: 検証には `update()` でイベントループを 1 回回す必要がある。
- **予約の主体**: `after` は**破棄されるダイアログではなく App（または `HookController` が持つ
  ウィジェット参照）に対して呼ぶ**。破棄済みウィジェットの `after` は使えない。

### 4-3. アプリ終了時の扱い（**v0.3 で書き直し**）

§1-⑦ のとおり**現状でも終了時に後始末が走る**。`after(0)` 遅延（4-2）はこのうち
**ダイアログ 8 クラスの経路だけ**を塞ぐ。**これだけでは不十分**である。

**【敵対的レビューの指摘・採用】非ダイアログ経路は同期解除のまま残るため、
終了時に `start_hook()` が走り得る**。具体例: `child_save_dialog.py:22-29` は
`suspend → dialog.wait_window() → finally: resume` の形で、
**`App.on_close` が `stop_hook()` → `self.destroy()` と進むと `wait_window()` が復帰し、
`finally` の同期解除でカウンタが 0 に戻って `start_hook()` が呼ばれる**。
`after(0)` は無関係に起こる。**「try/finally で対になっている」ことは終了時の安全を保証しない**。

**規定: `HookController` に終了ガードを持たせる**。

- **アプリ終了が確定した時点でガードを立てる**。`App.on_close` が
  `confirm_save_if_dirty` を通過した直後（`stop_hook()` の前後どちらでもよいが、
  **`self.destroy()` より前**）に立てる。
- **ガードが立っている間、`start_hook()` は何もしない**（`resume_hook_after_dialog` は
  カウンタの計算まで行い、**再開だけを行わない**）。
- **これは同期解除・遅延解除の両方に効く**ため、受け入れ条件 4 が経路によらず成立する。
- **`after(0)` 遅延（4-2）は引き続き必要**。ガードは「終了が確定した後」しか守れず、
  **破棄処理の途中で入れ子のメッセージボックスが開く問題（§1-⑥）と
  grab 復元との競合は遅延でしか解けない**ため。**2 つは役割が違う**。

**`window.master.winfo_exists()` による終了判定は採らない** — `Tk.destroy` は
子を先に破棄してから自分を壊すため、**この経路では常に真を返して機能しない**（レビュー指摘）。
**Tcl レベルでの終了**（`root` を直接 `destroy`）ではガードを立てる機会が無いが、
その場合は Python の後始末自体が走らない（§1-⑦ の実測）ため危険は生じない。

### 4-4. 各ダイアログの変更（8 クラス）

1. `__init__` の `suspend_hook_for_dialog()` を **`suspend_hook_for_dialog(self)` へ置換**。
2. `destroy()` override から **`resume_hook_after_dialog()` の行だけを削る**。
   **二重実行を避けるため必ず削る**（残すと OK 経路で 2 回走る）。
3. **T2 が残るクラスは `destroy()` override を維持する**
   （`orphan_sweep` / `keymap_edit` / `trigger` / `action`）。
   **T2 が無くなる 4 クラス**（`layout_delete` / `preset_manager` / `quarantine_manage` /
   `reference_cleanup`）の override の扱いは §6-1。
4. **`grab_modal` は `__init__` の最後の文のまま**（phase 14 の規約・静的検査が固定）。
   suspend は初期化の冒頭にあるので**衝突しない**。

## §5 テスト方針

`tests_ui/` に実 `Toplevel` を使ったテストを置く。**phase 14 の手法をそのまま使う**
（`update_idletasks()` + viewable アサート / 変異検査 / `report_callback_exception` の監視）。

- **× 閉じ（Tcl レベル破棄）で解除が走ること** — `dialog.tk.call("destroy", str(dialog))` で
  破棄し `update()` を回した後、**カウンタが 0 に戻る**ことを見る。
  **`protocol` 未登録の代表 1〜2 クラス**で見る（全 8 クラスは静的検査が守る）。
- **OK / キャンセル経路で二重に走らないこと** — `resume_hook_after_dialog` の呼び出し回数が
  **ちょうど 1 回**であることを固定する。
- **子ウィジェットの破棄では走らないこと**（`event.widget` 判定の回帰）。
- **アプリ終了時に `start_hook()` が走らないこと**（§4-3。`after` が実行されないことの固定）。
- **phase 14 の非退行** — ネストしたダイアログを × で閉じたとき、**grab が親へ復元される**こと。
- **静的検査（対象を明示限定する）**: **`dialogs/` の 8 クラスに限り**、
  ①`suspend_hook_for_dialog` は**必ず `self` を渡して呼ぶ**
  ②`destroy()` override に `resume_hook_after_dialog` が**残っていない**
  を AST で固定する。**`controllers/` の try/finally 形（§1-⑧）は対象外**とする
  （phase 14 の既存静的検査が `finally: resume_hook_after_dialog` を要求しているため、
  対象を限定しないと**既存検査と正面衝突する**）。
- **既存テストの棚卸し**（§6-2 で扱いを確定する）: `tests_ui/test_app_ui_flows.py:1325-1341`
  （`object.__new__` + `destroy` 直呼び）/ `test_quarantine_manage_flow.py:295-330` /
  `test_orphan_sweep_flow.py:514-523` / `test_nested_modal_grab.py:36-37`。

## §6 確定した判断（v0.4 でユーザー確定・§2 へ反映済）

- **6-1. 空になる `destroy()` override → 削除する**（4 クラス）。
- **6-2. 意味が空になる既存テスト → 書き換える**（§2 参照）。
- **6-3. 正本への昇格範囲 → §8 の 3 点**（`key_input.md` §7.2 / `features.md` §4.6 / `codebase_map.md`）。

## §7 受け入れ条件

1. **× 閉じでフック停止カウンタが 0 に戻る**（§1-① の実測が逆になる）。
2. **OK / キャンセル / × / プログラム破棄のいずれでも、解除がちょうど 1 回走る**（§4-4）。
   **Escape は結線している 3 クラスのみ**が対象（残り 5 クラスに Escape 経路は無い）。
3. **子ウィジェットの破棄では解除が走らない**（§4-1）。
4. **アプリ終了時に `start_hook()` が走らない**（§4-3。**現状からの挙動変更**）。
   **ダイアログ 8 クラスの経路と、非ダイアログの try/finally 経路の両方で確認する**
   （後者は `child_save_dialog` のように **`wait_window` の `finally` で同期解除する形**を
   終了経路で通し、`start_hook` の呼び出しが 0 回であることを見る）。
5. **`dialogs/` の 8 クラスすべてが `suspend_hook_for_dialog(self)` を呼んでいる**
   （静的検査で固定・§5）。**`controllers/` の try/finally 形は無変更**。
6. **`destroy()` override に `resume_hook_after_dialog` が残っていない**（§4-4）。
7. **T2 の後始末は `destroy()` override に残っている**（`scan_dirs` の収集が従来どおり効く）。
8. **phase 14 の grab 復元が退行しない**（ネスト経路のテストが全て pass し、
   × 閉じでも親へ復元される）。
9. 既存の `tests` / `tests_ui` が全て pass し `smoke_app` が通る（退行なし）。
10. **実機目視**: フック ON の状態でダイアログを × で閉じ、**次にダイアログを開いたとき
    フックが止まる**こと（＝カウンタがずれていない）。
11. 正本反映（§8）と `codebase_map.md` の更新が済んでいる。

## §8 正本反映（フェーズ末昇格・予定）

- **`spec_detail/key_input.md` §7.2** — 「**停止要求は閉じ方によらず解除される**」の 1 句を足す。
- **`spec_detail/features.md` §4.6「モーダルダイアログの作法」** — **後始末の作法**を足す
  （T1 = 状態の後始末は閉じ方によらず走る / T2 = ウィジェットに触る後始末は
  閉じる操作の側で行う。**実装詳細＝メソッド名は書かない**。phase 14 の昇格と同じ流儀）。
- **`codebase_map.md`** — `HookController` の責務へ「**ウィンドウを渡すと破棄時に自動解除する**」を追記。
- 実装ファイル: `keyseq/presentation/controllers/hook_controller.py`（window 引数 + 終了ガード）
  + `keyseq/presentation/app.py`（`on_close` でガードを立てる）+ `dialogs/` の 8 ファイル。
- テスト: `tests_ui/`（新規 1 ファイルまたは既存への追記）+ 既存テストの棚卸し（§6-2）。

## §9 スコープ外（本フェーズでやらない）

- **非ダイアログ経路の 5 系統**（§1-⑧ の try/finally 形）の**形は変えない**
  （対になっており、閉じ方による取りこぼしが無いため）。
  **ただし §4-3 の終了ガードはこれらにも効く**（ガードは `HookController` 側にあるため）。
  **「対象外」なのは結線方式の変更だけで、終了時の安全は本フェーズで担保する**。
- **`key_capture.py` / `keyboard_window.py` の編集モード** — 同じカウンタを触るが
  **ダイアログの閉じ方の問題ではない**。**正本 §7.2 の「キャプチャ」側の射程だが本フェーズでは扱わない**
  （必要なら別 idea を起票する）。
- **ダイアログ同型スケルトンの共通化**（`current.md` の候補送り・§2 で分離を確定）。
- **静的検査の発見ベース化**（phase 14 の `deep-reviewer` M-6・保留中）。
- **[idea_17](../backlog/idea_17_action_dialog_preset_manager_parent.md)**（`ActionDialog` の親付け替え）。
- **`_stop_capture` / `_stop_recording` の設計見直し**（T2 のまま据え置く。実害なし）。

## 関連

- 起票元: [idea_16](../backlog/idea_16_wm_close_skips_destroy_override.md)
- 直前フェーズ: [phase 14](../phase/14_nested_modal_grab_restore/phase.md)（grab 復元。
  **`<Destroy>` を `"+"` 結線にしたのは本件の布石**）/
  判断は [decisions_archive/14](../../.claude_data/state/decisions_archive/14_nested_modal_grab_restore.md)
- 正本: `spec_detail/key_input.md` §7.2（フックの停止制御）/
  `spec_detail/features.md` §4.6（UI 構成・モーダルダイアログの作法）
