# 暫定仕様 22: ダイアログの初期キーボードフォーカス（dialog_keyboard_focus）

> 状態: **未凍結・v0.6・ユーザー確定済（2026-09-23）・実装着手可**。本書がこのフェーズの確定設計（フェーズ中は正本を直接改訂しない）。
> フェーズ末タスクで正本 `instructions/common/spec_detail/` へ昇格し本書を凍結する。
> 起票元: [idea_26](../backlog/idea_26_dialog_keyboard_focus.md)（主・phase 27 task_04 の実機目視由来）
> + [idea_18](../backlog/idea_18_escape_delivery_flaky_test.md)（同梱・テストの flaky）。
> 番号対応: phase 28 / 暫定 22 / decisions 28。
> **v0.2 = 起票時レビュー（`deep-reviewer`）+ メインの実測反映**。実装方式を v0.1 の
> 「`focus_lastfor()` 既定」から **明示引数**へ変更（§3.2・§3.3。実測で v0.1 案は反証された）。
> **v0.3 = 敵対的レビュー（`codex-adversarial-reviewer`）反映**。保証の時点を明記（§3.1）/
> 群 A・A' の実 Tk 検証を追加（§5・§8-2）/ 目視手順を固定し skip 件数の報告を義務化（§8-8）/
> 群 C への適用を §9-2 の決定に条件付け（§3.2）。
> **v0.4 = ユーザー確定（2026-09-22・2 回目）**。§9 の 7 件をすべて決着（§2）。
> **正本へ Escape 条項も追加し、群 C の 5 経路へ Escape を実装する**（§3.5。スコープ拡大）。
> **v0.5 = task_05 の統合レビュー（`deep-reviewer` 指摘 H1）を受けた再確定（2026-09-23）**。
> v0.4 の §4 条項「モーダルダイアログは Escape でも閉じられる」は**群 A の 4 経路が Escape 未結線**の
> ため正本へそのまま昇格できないことが判明。**群 A の 4 経路へも Escape を追加**し、
> **Esc に別用途がある状態ではその用途を優先して閉じない**規範を追加する（§3.6。スコープ +1 タスク）。
> **v0.6 = 負荷下確認の範囲限定 + `send_escape` の堅牢化（ユーザー確定 2026-09-23）**。
> §8-7 の判定対象を **Escape 配送 family** に限定し、`after(0)` のフック再開 family は
> **idea_33 として分離**（phase 28 由来でないことを A/B 実測で確認済）。あわせて
> **§6 のヘルパに実時間の deadline を入れる**（§6 末尾。現行は試行間に待ちが無く「20 回」が実質 1 回）。

---

## §1 目的 / 背景

Escape を bind しているのに**キーボードフォーカスをダイアログ内へ移していない**ダイアログがあり、
実使用で Escape が効かない（キーが親の App へ届く）。**既存テストは `focus_force()` を先に呼ぶため
この欠落を検出できない**。フォーカスの所在を `grab_modal`（モーダル化の唯一の入口）の責務として
一本化し、再発しない構造にする。あわせて、同じテスト群が抱える Escape 配送の flaky（idea_18）を
同時に解消する。

**対象レイヤ = presentation のみ**。データスキーマ・domain / application の変更は無い。

### §1.1 現状監査（2026-09-22・メイン実測）

`grab_modal(` の呼び出しは **production 15 箇所**（`def` を除く実測）。フォーカスの扱いで 3 群に分かれる。

| 群 | 対象（`ファイル:行` = `grab_modal` の位置） | フォーカス |
|---|---|---|
| **A. `__init__` 内で明示済** | `action_dialog.py:131`（`:129` で `value_entry`。間に `:130 _sync_capture_ui()` が 1 文ある）/ `keymap_edit_dialog.py:54`（`:53`）/ `keymap_set_history_dialog.py:32`（`:31` tree）/ `:215`（`:214` listbox）/ `preset_dialog.py:40`（`:39`）/ `trigger_dialog.py:53`（`:52`） | **6 経路**。明示あり |
| **A'. 呼び出し側が別（ビルダ内で明示）** | `child_save_dialog.py:243`（依存ダイアログ。`:284` で `save_as_button.focus_set()` をビルダ `_create_dependency_dialog` 内で実行） | **1 経路**。明示あり |
| **B. Escape bind あり・明示なし（本件の欠落）** | `orphan_sweep_dialog.py:26`（bind `:24`）/ `quarantine_manage_dialog.py:26`（bind `:24`）/ `reference_cleanup_dialog.py:57`（bind `:55`） | **3 経路**。欠落 |
| **C. Escape bind なし・明示なし** | `layout_delete_dialog.py:52` / `preset_manager.py:79` / `io_dialogs.py:57` / `hotkey_presets_io.py:87` / **`child_save_dialog.py:26`**（「子ファイルの保存」。`:25` は `WM_DELETE_WINDOW` のみ・Escape bind 無し・ビルダ `_create_action_dialog` に `focus_set` 無し） | **5 経路**。明示なし（§3.5 で Escape を追加する） |

- `grab_modal`（`keyseq/presentation/modal.py:65`・**56 行**）は**フォーカスに一切関与していない**。
  `transient` → `grab_set` → 台帳登録 → `<Destroy>` で grab 復元、のみ。
- `action_dialog.py:275` / `:378`、`keymap_edit_dialog.py:82`、`trigger_dialog.py:79` の `focus_set` は
  **`__init__` 外のメソッド**で、`grab_modal` とは無関係（本件の対象外）。
- 静的検査 `tests_ui/test_nested_modal_grab.py:260`
  `test_grab_modal_is_last_initialization_statement` が、**10 ダイアログクラスの `__init__` 末尾が
  `grab_modal` であること**と、config_io 3 ファイルの `grab_modal` 直後が `wait_window` であることを固定。
- **テストの偽 Toplevel 2 クラスが focus 系メソッドを持たない**:
  `tests_ui/test_child_save_dialog.py:149` `_FakeSaveDialog` / `tests_ui/test_config_io_characterization.py:65`
  `_FakeDialog`（どちらも `transient` / `grab_current` / `grab_set` / `bind` / `protocol` はあるが
  `focus_set` が無い）。実物の `grab_modal` を通すため、**フォーカス適用を足すと `AttributeError` で落ちる**。
- **正本は二重に空白**（idea_26 の記載を訂正）: `features.md`「モーダルダイアログの作法」
  （§4.6 内・170〜213 行）には**フォーカスの条項も「Escape で閉じる」条項も無い**。Escape は
  `key_input.md` §7.2（`:16`）の閉じ方の**列挙に現れるだけ**。idea_26 の「正本の規定: `features.md`
  §4.6（ダイアログ作法。Escape で閉じる）」は**実測では存在しない**。
- **正本の誤り**: `instructions/common/codebase_map.md:308` は「production の 13 箇所はすべて渡している」だが
  **実測 15 箇所**（phase 27 追加分などが未反映）。→ §2.1-5（フェーズ末に訂正）。
- テストの `focus_force()`: `test_dialog_teardown_flows.py:157` / `test_orphan_sweep_flow.py:540` /
  `test_quarantine_manage_flow.py:319` / `test_keymap_set_history_flow.py:304`。

### §1.2 実測（2026-09-22・`.venv` python で probe 実行）

実ダイアログと同じ順序（**未マップのまま `focus_set` → `grab_set`**）を再現し、方式を同条件で比較した。

| 条件 | `focus_get` の行き先 | Escape 到達 |
|---|---|---|
| 1 現状・子へ `focus_set` あり（群 A 相当） | 子 widget | **届く** |
| 2 現状・明示なし（群 B 相当） | **App ルート `.`** | **届かない**（症状を再現） |
| 3 案 B-1（`focus_lastfor()` 既定）・子の明示あり | **窓自身（子の指定を奪う）** | 届く |
| 4 案 B-1・明示なし | 窓自身 | 届く |
| 5 案 B-3（`after_idle` で「窓の外なら窓へ」）・子の明示あり | **窓自身（子の指定を奪う）** | 届く |
| 6 案 B-3・明示なし | 窓自身 | 届く |
| 7 **案 B-2（明示引数）**・窓を指定 | 窓自身 | 届く |
| 8 **案 B-2**・子 widget を指定 | **子 widget** | 届く |

`ActionDialog` の `mouse_click` 経路（`focus_set` の後に `_sync_capture_ui()` が `value_entry` を
`state="disabled"` にする）についても、移動の前後で結果が変わらないことを実測した。

| 条件 | `focus_get` の行き先 |
|---|---|
| 9 通常・`focus_set` → （disabled なし） | Entry |
| 10 通常・（disabled なし）→ `focus_set` | Entry |
| 11 **現状の順序**: `focus_set` → `disabled` 化 → grab | Entry |
| 12 **移動後の順序**: `disabled` 化 → grab → `focus_set` | Entry |

→ **`disabled` 化との前後関係はフォーカスの行き先を変えない**（`focus_set` は
`takefocus`（Tab 巡回）とは独立に効くため）。§3.2 の機械的移動は
`action_dialog.py:129-131` でも安全（ただし §5・§8-2 で実 Tk の回帰確認は行う）。

**判明した機序（設計の土台）**:

1. **未マップの Toplevel に対する `focus_set()` は Tk 内で保留され、マップ後に解決される**。
   保留中は `focus_lastfor()` も `focus_get()` も**その指定を返さない**（probe 3 の F で実測。
   `wait_visibility()` 後に `focus_set` した場合は `focus_lastfor()` が子を返す = probe 2 の A）。
   → **「既存の明示指定の有無を `grab_modal` 側から検出する」方式は原理的に不可能**。
   推測型（B-1 / B-3）は**群 A の初期フォーカスを奪う**（条件 3・5）。
2. **Tk はキーイベントをフォーカス窓へ再配送する**。`event_generate("<Escape>")` は
   **宛先ウィジェットではなくその時点のフォーカスに従う**（probe 2 の D = grab 済みの窓に対して
   生成しても、フォーカスが別窓なら届かない）。
3. **アプリが OS の入力フォーカスを持たないとき、`focus_get()` は `None` を返し、
   `focus_set()` も効かない**（probe 1。背景実行のまま走らせた回で再現）。
   → §5・§6 のテスト設計に直結する（`focus_get()` 依存の検査は環境依存で false red になりうる）。
4. ネストした窓を破棄すると、フォーカスは**外側の窓へ戻った**（probe 3 の H）。→ §2.1-4 の材料。

---

## §2 確定事項（ユーザー 2026-09-22）

- **案 B を採る** = フォーカスの面倒は `modal.grab_modal()` が見る（作法として一本化）。
  個別修正（案 A）は採らない。
- **idea_18（Escape 依存テストの flaky）を本フェーズに同梱する**（触るテストファイルが重なるため）。
- **同型スケルトンの共通化は合流させない**（`suspend_hook_for_dialog` 9 ファイル /
  `bind("<Escape>")` + `protocol("WM_DELETE_WINDOW")` 4 クラス同型。
  `current.md`「別タスク化候補」に残置）。

### §2.1 追加の確定（ユーザー 2026-09-22・2 回目。v0.3 の §9 を決着）

1. **実装方式 = 明示引数（案 B-2）で確定**（§3.2）。推測型は実測で反証済（§1.2）。
2. **群 C（Escape bind なし 5 経路）にフォーカスが入る挙動変化を受容する**（§3.4）。
3. **正本へ Escape 条項も追加し、群 C の 5 経路へ Escape を実装する**（§3.5・§4）。
   → 本フェーズのスコープが広がる（タスク +1〜2）。
4. **フォーカスの復帰（閉じた後・最小化復帰後）はスコープ外**。ただし
   **実機目視のついでに再現確認だけ行う**（§8-10）。再現したら idea として起票し、
   しなければそこで終わり。
5. **`codebase_map.md:308` の「13 箇所」→「15 箇所」はフェーズ末の昇格タスクで訂正する**（§10）。
6. **idea_18 の案 A（ハンドラ直呼び + 結線の静的検査）の併用可否は、§6 の診断結果を見て決める**
   （タスク内の判断。採否と理由を完了報告に記す）。
7. **`focus_get()` 依存の実 Tk 検査には skip ガードを付ける**（§5）。
   **skip 件数は完了報告に記載する**（§8-8）。

### §2.2 追加の確定（ユーザー 2026-09-23・3 回目。H1 の決着）

8. **群 A の 4 経路（`ActionDialog` / `KeymapEditDialog` / `PresetDialog` / `TriggerDialog`）へも
   Escape を追加する**（§3.6）。これにより §4 の条項を例外なしで正本へ昇格できる
   （= `grab_modal` を通る 15 経路すべてが Escape で閉じる）。
9. **Esc に別用途がある状態では、その用途を優先し、ダイアログを閉じない**（§3.6 の規範）。
   ユーザー意図 = 「すでに Escape で閉じるダイアログへ、後から Esc の別用途を足したくなった時も
   同じ形で共存できるようにする」。
10. **実施は phase 28 内（task_05c）**。実機目視は**実装がすべて終わってから 1 回**にまとめる
    （群 B の初期フォーカス + 群 A の新規 Escape・別用途との共存を同時に見る）。

---

## §3 フォーカスの規定

### §3.1 規範（実装が従う条項）

1. **`grab_modal` はモーダル化の際に、キーボードフォーカスをダイアログ内へ要求する**。
   保証の時点は次のとおり（実測 1・3 の制約に合わせる。**無条件の即時保証ではない**）:
   - **アプリが OS の入力フォーカスを持ち、窓がマップされた時点で、フォーカスはダイアログ内にある**。
   - **未マップ・アプリが非アクティブの間は Tk の保留に従う**（要求は残り、条件が整えば解決される）。
   - **二重呼び出し・最小化中の預かり経路では要求を出し直さない**（最初の要求を維持する。§3.2）。
   - 検証の時点は「**ダイアログ生成後に `update()` を回し、アプリが入力フォーカスを持つ状態**」とする
     （§8-1・§8-2 の判定時点）。
2. **入力先を定めているダイアログはそこへ、定めていないダイアログは窓自身へ入れる**。
3. **入口は `grab_modal` の 1 箇所**。フォーカスを `grab_modal` の外で設定しない
   （既存の静的検査「`__init__` の最後は `grab_modal`」と両立する）。
4. **OS レベルの窓のアクティブ化（`focus_force` / `lift`）は行わない**。
   他アプリで作業中のユーザーから入力を奪わないため。本件が扱うのは
   **アプリ内のどのウィジェットへキーが行くか**だけ。
5. 本条項が規定するのは**モーダル化の時点**のみ。閉じた後・最小化復帰後の**フォーカスの復帰**は
   **規定しない**（§2.1-4 でスコープ外。再現確認のみ §8-10 で行う）。

### §3.2 実装方式 = 明示引数（案 B-2）

```python
def grab_modal(window, parent=None, *, focus=None):
    ...
    window.grab_set()
    _apply_initial_focus(window, focus)   # focus が None なら window 自身
```

- **`focus` 省略時はダイアログ自身**（群 B はこれで直る）。
  **群 C（5 経路）も省略呼び出しのため自動的に挙動が変わる**（§2.1-2 で受容済）。
  省略時の既定を群ごとに変えない（作法を 2 通りに割らない）。
- **群 A・A' の明示指定は引数へ移す**（`self.value_entry.focus_set()` を消して
  `grab_modal(self, parent, focus=self.value_entry)` にする）。**二重指定を残さない**
  — 残すと §3.1-3 が崩れ、かつ実測条件 3 のとおり後勝ちで奪われる。
- **`child_save_dialog` の依存ダイアログ**（`:243`）は、ビルダ `_create_dependency_dialog` が
  **`(dialog, save_as_button)` を返す形**へ変える（Toplevel へ属性を生やす形は採らない。
  暗黙の状態を増やさないため）。
- **適用位置 = `grab_set()` の直後**（モーダル化の一部）。
  **二重呼び出しの早期 return 経路（`previous is window` / 預かり中）では触らない**
  （「最初の保持者と破棄ハンドラを維持する」既存方針と揃える）。
- **例外**: `tk.TclError` のみ握る（破棄中の窓へ当たる場合）。**`KeyError` は対象外**
  — `grab_current()` と違い `_nametowidget` による解決を伴わず、手元の widget を直接触るため。
  **`AttributeError` は握らない**（偽 Toplevel の不足を隠すため。§5 で偽物側へメソッドを足す）。
- `grab_modal` は既に 56 行（`modal.py:65-120`）で実装目安 30 行を超えているため、
  フォーカス適用は **`_apply_initial_focus` として関数へ切り出す**。

### §3.3 不採用の案（実測で反証・記録として残す）

- **B-1「`focus_lastfor()` 既定」（v0.1 の推奨）**: 未マップ時は保留中の指定を返さないため、
  **群 A の初期フォーカスを奪う**（§1.2 条件 3）。**反証済**。
- **B-3「`after_idle` で『窓の外なら窓へ』」**: 同じ理由で**群 A を奪う**（§1.2 条件 5）。**反証済**。
- **案 A「3 ダイアログの個別修正」**: 新規ダイアログで再発する余地が残る → ユーザー確定済で不採用。
- なお v0.1 の B-2 不採用理由「呼び出し 13 箇所の見直し」は**二重に誤り**
  （実測 15 箇所 / 省略可引数のため見直しが要るのは群 A・A' の 7 経路だけ）。

### §3.4 想定される挙動変化

- **群 A（6 経路）・A'（1 経路）**: 明示指定を引数へ移すだけで**初期フォーカス先は従来と同じ widget**。
- **群 B（3 経路）**: 窓自身へ入り **Escape が効くようになる**（本件の修正）。
- **群 C（5 経路）**: **キー入力の宛先が親 App から当該窓へ移る**（§2.1-2 で受容）。
  加えて §3.5 により **Escape でも閉じられるようになる**。

### §3.5 Escape の結線（群 C の 5 経路・§2.1-3）

**規範: Escape は「閉じる（×）」と同じ経路へ結線する**。新しい閉じ方を作らない
（既存 4 クラスも `bind("<Escape>")` と `protocol("WM_DELETE_WINDOW")` が同じ関数を指している）。

| 経路 | 現在の「閉じる」（実測） | Escape の結線先 |
|---|---|---|
| `child_save_dialog.py:25`（子ファイルの保存） | `WM_DELETE_WINDOW` → `dialog.destroy`（`result["choices"]` は `None` のまま） | `dialog.destroy` |
| `hotkey_presets_io.py:86` | `WM_DELETE_WINDOW` → `dialog.destroy` | `dialog.destroy` |
| `io_dialogs.py:56` | `WM_DELETE_WINDOW` → **`on_cancel`**（`result["ok"]` は `False` のまま） | **`on_cancel`**（`destroy` 直呼びにしない） |
| `layout_delete_dialog.py:52` | **`WM_DELETE_WINDOW` ハンドラ無し**（Tk 既定の破棄）。「キャンセル」ボタン = `self.destroy`（`result` は `None` のまま） | `self.destroy` |
| `preset_manager.py:79` | **`WM_DELETE_WINDOW` ハンドラ無し**。「キャンセル」ボタン（`:163`）= `self.destroy`（`_temp` の編集は破棄され `data` へ反映されない） | `self.destroy` |

- **いずれも「保存せずに閉じる = キャンセル相当」**で、Escape を足しても**新しい意味は生じない**
  （× と同じ結果になる）。
- **`WM_DELETE_WINDOW` ハンドラが無い 2 件にハンドラを足すかは実装判断**
  （Escape の結線だけで足りる。× の挙動は現状 Tk 既定のままで変わらない）。
- フック停止の解除は `key_input.md` §7.2 の「閉じ方によらず解除される」に従い、
  **Escape 経由でもちょうど 1 回**であること（既存の仕組みに乗るだけ。テストで固定する）。

### §3.6 群 A の Escape と「Esc の別用途」の優先（§2.2-8・§2.2-9）

**規範: Escape に別用途を割り当てている状態では、その用途を優先し、ダイアログを閉じない**。
実現形は「**ダイアログの `<Escape>` ハンドラを 1 つにまとめ、状態で分岐する**」。

```python
def _on_escape(self, _event):
    if self._recording:          # 別用途が有効な間は
        self._stop_recording()   # そちらを優先し
        return "break"           # 閉じない
    self.destroy()               # 通常時は × と同じ（キャンセル相当）
```

#### 実測（2026-09-23・`.venv` python で Tk の bind 解決を probe）

| # | 条件 | 結果 |
|---|---|---|
| A | 同一 widget に `<KeyPress>` と `<Escape>` を両方 bind | Escape 押下では **`<Escape>` のみ発火し `<KeyPress>` は発火しない**（より具体的なパターンが勝つ）。他キーは `<KeyPress>` が発火 |
| B | 同一 widget・同一パターンを `add="+"` で 2 つ | **登録順に両方発火** |
| C | B の 1 つ目が `"break"` を返す | **後続は発火しない** |
| D | 子 widget の `<Escape>` が `"break"` を返す | **親 Toplevel へ伝播しない** |

→ **実測 A が決定的**。現在の「Esc で停止」は `<KeyPress>` ハンドラ内の `keysym == "esc"` 分岐なので、
**素朴に `bind("<Escape>", 閉じる)` を足すと停止処理が発火せずダイアログが閉じる**（退行）。
**実測 B の登録順も使えない**（閉じる側が `__init__` で先に登録されるため先に発火する）。
したがって**状態分岐（単一ハンドラ）が唯一の安全な形**であり、規範として固定する。
実測 C・D により、**将来 Esc の別用途を後から足す場合も同じ形で共存できる**（§2.2-9 の意図を満たす）。

#### 対象（群 A の 4 経路）

| 経路 | Esc の既存用途 | 実装 |
|---|---|---|
| `action_dialog.py:294` | **記録停止**（`_on_key_press` の `key == "esc"`。ヒント「Escで停止」） | 状態分岐（`self._recording`） |
| `trigger_dialog.py:98` | **取得停止**（`_on_capture_keypress`。ヒント「取得中…（Escで停止）」） | 状態分岐（取得中フラグ） |
| `keymap_edit_dialog.py:100` | **取得停止**（同上） | 状態分岐（取得中フラグ） |
| `preset_dialog.py:39` | **なし** | 単純追加（`self.destroy`） |

- **閉じ方は既存の「キャンセル」と同じ結果**にする（新しい閉じ方を作らない。§3.5 の規範を踏襲）。
  4 経路はいずれも `result` を確定せずに破棄すれば「キャンセル相当」になる。
- **別用途側の `<KeyPress>` ハンドラは残す**（Esc 以外のキーの記録・取得は従来どおり）。
  Esc の分岐だけが `<Escape>` ハンドラ側へ移る。
- **群 A は初期フォーカスが `Entry` 等の子 widget**にあるため、`<Escape>` は **Toplevel へ bind** して
  bindtag の伝播で拾う（実測 D のとおり子で `"break"` されない限り届く）。

---

## §4 正本への追記（`features.md`「モーダルダイアログの作法」）

**2 条項**を追記する（作法の変更であり、実装だけに置くと再び正本の空白になるため）。

> * **モーダルダイアログは、開いた時点でキーボードフォーカスをダイアログ内へ移す**
>   （Escape などのキーが親ウィンドウへ抜けない）。**ダイアログごとに定めた入力先があればそこへ、
>   無ければダイアログ自身へ入れる**。**窓の前面化・フォーカス強制は行わない**
> * **モーダルダイアログは Escape でも閉じられる**。**Escape は閉じるボタン（×）と同じ扱いで、
>   保存せずに閉じる（キャンセル相当）**。新しい閉じ方を増やさない
>   （フック停止の解除は `key_input.md` §7.2 のとおり閉じ方によらずちょうど 1 回）
> * **ただし Esc に別用途を割り当てている状態（キーの記録中・取得中など）では、その用途を優先し、
>   ダイアログを閉じない**。**Escape のハンドラはダイアログにつき 1 つにまとめ、状態で分岐する**
>   （別用途を別ハンドラとして重ねない）

**閉じた後・最小化復帰後のフォーカスの復帰は規定しない**（§2.1-4 でスコープ外。§11）。

---

## §5 テストの検出力（`focus_get()` 依存を増やさない）

**実測 3**（アプリが OS フォーカスを失うと `focus_get()` は `None`）のため、
`focus_get()` に依存する検査を増やすと **idea_18 と同じ family のテストが増える**。
そこで**決定論的な検査を主、実 Tk の検査を従**にする。

- **主（決定論的・環境非依存）**: `modal.grab_modal` の単体テストを新設し、偽 window への
  呼び出しを記録して次を固定する。
  - `focus` 省略時は**窓自身**へ、指定時は**その widget** へ `focus_set` する
  - **`focus_force` / `lift` を呼ばない**（§3.1-4。`test_minimize_grab_custody.py:147-161` と同型の固定）
  - **二重呼び出し・預かり中の早期 return では `focus_set` を呼ばない**（§3.2）
- **従（実 Tk・各ダイアログ 1 件まで）**: 次を実 Tk で確認する（手本 =
  `test_keymap_set_history_flow.py:137`）。**アプリが入力フォーカスを取れない環境では skip する
  ガードを付ける**（判定手段は §9-7）。
  - **群 B の 3 ダイアログ**: 生成直後のフォーカスがダイアログ内にあること（修正の確認）。
  - **群 A・A' の回帰確認**（単体テストだけでは「各呼び出し元が正しい引数を渡すこと」も
    「Tk が実際にその widget へ入れること」も担保できないため）:
    `ActionDialog` を **hotkey / text / mouse_click の 3 モード**で開いてフォーカス先が
    `value_entry` であること（`_sync_capture_ui()` の `disabled` 化をまたぐ経路。実測 11・12）+
    残る群 A の 5 経路・A' の 1 経路について**フォーカス先の widget を 1 件ずつ固定**する。
  - **A' はビルダの戻り値が呼び出し側まで渡ること**を固定する（`(dialog, save_as_button)` の変更が
    `grab_modal` の `focus` 引数へ到達しているか）。
- **`focus_lastfor()` による検査は使わない**（未マップ時は窓自身を返すため**修正前も真になる**
  = トートロジーで検出力がない）。
- **偽 Toplevel 2 クラスへ `focus_set` を追加する**（`test_child_save_dialog.py:149` /
  `test_config_io_characterization.py:65`）。**実装側で `AttributeError` を握って回避しない**。
- **静的検査（AST）は追加しない**（`grab_modal` 集約で構造的に保証されるため）。
- **実機目視**（ユーザー担当）を受け入れ条件に含める（§8-8）。テストだけでは完了判定しない。

---

## §6 Escape 依存テストの安定化（idea_18・同梱）

**実測 2・3 により、idea_18 の案 B（配送後に待つだけ）では直らない**。
Tk はキーイベントを**フォーカス窓へ再配送**し、届かなかったイベントは破棄されるため、
待っても来ない。**失敗の根は「配送が遅い」ではなく「アプリ / ダイアログがフォーカスを持たない」**。

- **task の先頭に診断を置く**: 負荷下で対象テストを回し、失敗時の
  `focus_get()` / `focus_displayof()` / `winfo_exists()` を採取して機序を確定する
  （ここで別の機序が判明したら §6 を改訂してから実装へ進む）。
- **ヘルパは「待つ」ではなく「フォーカスを確保してから送る」**:
  ①ダイアログへフォーカスを確保（必要なら `focus_force` + `update`）→
  ②**フォーカスがダイアログ内にあることを確認**（無ければ上限つきで再試行）→
  ③`event_generate("<Escape>")` → ④破棄を上限つきで待つ →
  ⑤上限到達なら**採取した診断情報を添えて fail**（黙って通さない）。
  置き場は `tests_ui` 配下の共有ヘルパ 1 モジュール。
- 適用対象（2026-09-22 実測の Escape 依存テスト全件）:
  `test_dialog_teardown_flows.py:144` / `test_orphan_sweep_flow.py:532` /
  `test_quarantine_manage_flow.py:311` / `test_keymap_set_history_flow.py` の close 経路。
- **案 A（結線済みハンドラの直呼び + 結線の静的検査）の併用可否は §9-6**。
- **連鎖（`setUp` のドレイン検査）は変更しない**（phase 15 task_03 の検出力を保つ。案 C は採らない）。
- **production コードは変更しない**（idea_18 はテストのみの問題）。

### §6.1 確保ループの deadline 化（v0.6・ユーザー確定 2026-09-23）

**規範: 「上限つきで再試行」は回数ではなく実時間の期限（deadline）で切る**。

現行の `send_escape` は `focus_force()` → `app.update()` → 確認、を最大 20 回繰り返すだけで
**試行間に実時間の待ちが無い**。`focus_force()` は OS / WM への**要求**にすぎず、
`app.update()` は**今キューにあるイベントを処理して即戻る**（新しい通知を待たない）ため、
**20 回が CPU 速度で数ミリ秒未満に消化されうる**。
= `attempts=20` は「20 回粘る」ではなく実質「**一瞬だけ試す**」になっている。

- 対処: 試行間に短い実時間待ち（10ms 程度）を入れ、**全体に秒単位の期限**を置く。
  待ちの間も `app.update()` を回し続ける（UI スレッドを止めるとフォーカス通知の処理自体が進まない）。
- **応答が速い回の実行時間は変わらない**（待ちに入る前に成功するため）。遅い回だけ期限まで粘る。
- 失敗の意味が「一瞬試して取れなかった」から「**期限まで粘っても取れなかった**」に変わり、
  **fail が本当の異常を指すようになる**。

---

## §7 層の分担と配置

- `keyseq/presentation/modal.py` — `grab_modal` の引数追加 + `_apply_initial_focus`（**実装の中心**）。
- `keyseq/presentation/dialogs/*` ・ `controllers/config_io/child_save_dialog.py` —
  群 A・A' の `focus_set` を引数へ移す（**7 経路の機械的な移動**）+
  **群 C の 5 経路へ `bind("<Escape>")` を追加**（§3.5。`layout_delete_dialog.py` /
  `preset_manager.py` / `io_dialogs.py` / `hotkey_presets_io.py` /
  `child_save_dialog.py` の「子ファイルの保存」）。
  `keymap_set_history_dialog.py:30` の「フォーカスを移さないと Escape が親（App）へ届き…」コメントは
  責務が `modal.py` へ移るため**整理する**。
- `tests_ui/` — 単体テスト新設・偽 Toplevel への `focus_set` 追加・Escape ヘルパ（§5・§6）。
- `instructions/common/spec_detail/features.md` / `codebase_map.md` — 昇格時（§10）。

---

## §8 受け入れ条件（ドラフト）

1. 群 B の 3 ダイアログで、生成直後のフォーカスがダイアログ内にある（§3.1・§5）。
2. **群 A・A' の 7 経路で初期フォーカス先が従来と同じ widget**。
   検証手段 = ①`grab_modal` の単体テスト（引数で渡した widget へ `focus_set` される）
   ②**実 Tk での回帰確認**（`ActionDialog` の 3 モード + 残る 6 経路のフォーカス先固定・
   A' はビルダ戻り値の到達確認。§5）③移動前後の対象 widget の対応表を完了報告に載せる。
3. `grab_modal` の二重呼び出し・預かり中の経路で `focus_set` を呼ばない（単体テストで固定）。
4. `focus_force` / `lift` を呼ばない（単体テストで固定・§3.1-4）。
5. 静的検査 `test_grab_modal_is_last_initialization_statement` が引き続き green。
6. Escape 依存テスト 4 箇所について、**外す / 残すの判定と理由を完了報告に列挙**した上で
   §6 のヘルパ経由になっている（§5・§6）。
7. **負荷下での再現確認（v0.6 で適用範囲を限定・ユーザー確定 2026-09-23）**:
   idea_18 の実測条件（busy loop 4 本の負荷下）で、**Escape 配送 family について** fail が出ないこと。
   判定対象 = **Escape で閉じる経路を検証するテスト**（`send_escape` 経由のもの +
   `tests_ui/test_dialog_escape_binding.py`）。加えて `tests_ui` 一括を連続 3 回 green（§6）。
   - **`<Destroy>` → `after(0)` のフック再開が取りこぼされる family は本条の対象外**。
     機序が別（Escape を使わない経路でも起き、届かなかったイベントの問題ではない）で、
     **phase 28 由来でないことを A/B 実測で確認済**（base `60372bf` / `6fbeebb` との比較で差なし。
     最も強く出た `quarantine_manage_flow` 4/6 は再測定で 0/10 となり再現しなかった）。
     → **[idea_33](../backlog/idea_33_hook_resume_after_idle_flaky_test.md) として分離**し、本フェーズでは直さない。
8. **実機目視（ユーザー）**: 群 B の 3 ダイアログについて、**アクティブな App から開き、
   ダイアログ内を一切クリックせずに直ちに Escape** を押して閉じること（クリックしてしまうと
   フォーカスが入るため欠落を検出できない）。
   あわせて **§5 の実 Tk 検査が skip された件数を完了報告に記載する**。
   **全件 skip だった場合は、この実機目視の結果が §8-1 の唯一の根拠になる**（その旨も明記する）。
   **実機目視は実装がすべて終わってから 1 回にまとめる**（§2.2-10）。群 A の 4 経路
   （§8-12）について、**①通常時に Escape で閉じる ②記録中 / 取得中に Escape を押すと
   停止するだけでダイアログは閉じない**の 2 点も同じ回で確認する。
9. **群 C の 5 経路が Escape で閉じる**（§3.5）。結線先が §3.5 の表のとおりで、
   **Escape 経由でもフック停止の解除がちょうど 1 回**であること（`key_input.md` §7.2）。
10. **フォーカス復帰の再現確認**（§2.1-4）: 実機目視の際に「内側ダイアログを閉じた後」と
    「最小化から復帰した後」に外側ダイアログで Escape が効くかを確認し、**結果を完了報告に記す**
    （再現したら idea 起票。本フェーズでは直さない）。
11. 正本 `features.md` に §4 の **3 条項**が入り、`codebase_map.md` の `modal.py` 節が追従
    （件数訂正を含む。フェーズ末・§10）。
12. **群 A の 4 経路が Escape で閉じる**（§3.6）。加えて **Esc の別用途が有効な間は閉じない**こと
    （`ActionDialog` の記録中 / `TriggerDialog` ・ `KeymapEditDialog` の取得中）を
    **自動テストで固定**し、**実機目視でも確認**する。
    → これにより **`grab_modal` を通る 15 経路すべてが Escape で閉じる**（§4 の条項が例外なしで成立）。
13. **検出力の補強**（task_05 の `deep-reviewer` 指摘 M1・M3）:
    ①群 A の `keymap_set_history_dialog` の `tree` / `CategoryChooserDialog` の `listbox` について
    **widget 同一性**（`assertIs`）で初期フォーカスを固定する（現行の `startswith` 判定は
    `focus=` を外しても緑になり検出力がない）②群 C の実 Toplevel 2 件（`LayoutDeleteDialog` /
    `PresetManagerDialog`）の Escape を**ハンドラ直呼びから `send_escape` の実配送へ格上げ**する。

---

## §9 決定済み事項の索引（v0.3 の確認事項 7 件・2026-09-22 決着）

v0.3 で挙げた確認事項はすべて **§2.1** で決着した。**本書に未確定の事項は無い**。

| # | 内容 | 決定 | 反映先 |
|---|---|---|---|
| 1 | 実装方式 | **明示引数（案 B-2）で確定** | §3.2 |
| 2 | 群 C にフォーカスが入る挙動変化 | **受容** | §3.4 |
| 3 | 正本への Escape 条項 | **追加する + 群 C へ Escape を実装** | §3.5・§4 |
| 4 | フォーカスの復帰 | **スコープ外 + 再現確認のみ** | §8-10・§11 |
| 5 | `codebase_map.md` の件数誤り | **フェーズ末の昇格タスクで訂正** | §10 |
| 6 | idea_18 案 A の併用 | **§6 の診断結果を見てタスク内で判断** | §6 |
| 7 | 実 Tk 検査の skip ガード | **付ける + skip 件数を報告** | §5・§8-8 |

---

## §10 正本反映（フェーズ末昇格・予定）

- `instructions/common/spec_detail/features.md`「モーダルダイアログの作法」へ §4 の **3 条項**
  （フォーカス + Escape + Esc の別用途優先）を追記。
- `instructions/common/codebase_map.md` の `modal.py` 節（`:303`〜）:
  `grab_modal(window, parent=None, *, focus=None)` への署名更新 + フォーカス責務の記載 +
  **「13 箇所」→「15 箇所」の訂正**（§2.1-5）。
- 実装 = `keyseq/presentation/modal.py` / 群 A・A' の 7 経路 / 群 C の 5 経路（Escape 追加）/
  **群 A の 4 経路（Escape 追加 + Esc の別用途との状態分岐。§3.6）**。
- テスト = `tests_ui/`（単体テスト新設・偽 Toplevel 2 クラス・Escape ヘルパ・対象 4 テスト）。
- idea_26 / idea_18 を `backlog/INDEX_done.md` へ移動。
- 別実装同期: **なし**（presentation 内の作法のため）。

---

## §11 スコープ外（本フェーズでやらない）

- **フォーカスの復帰**（閉じた後・最小化復帰後）の**規定**（§2.1-4）。
  **再現確認だけは §8-10 で行い**、再現したら idea として起票する（本フェーズでは直さない）。
- **同型スケルトンの共通化**（`suspend_hook_for_dialog` / `Escape` + `WM_DELETE_WINDOW`）。
  `current.md`「別タスク化候補」に残す（§2 確定）。
- ダイアログの初期フォーカス位置の UX 設計（どの widget を既定にするかの全面見直し）。
- [idea_32](../backlog/idea_32_grab_modal_static_check_discovery.md)（静的検査の発見ベース化）。

---

## 関連

- [idea_26](../backlog/idea_26_dialog_keyboard_focus.md) / [idea_18](../backlog/idea_18_escape_delivery_flaky_test.md)
- 暫定仕様 [12](12_nested_modal_grab_restore.md) / [14](14_dialog_parent_and_app_separation.md) /
  [15](15_minimize_grab_custody.md)（いずれも凍結済。`grab_modal` の現行仕様は正本が正）
- 正本: `instructions/common/spec_detail/features.md`「モーダルダイアログの作法」/
  `key_input.md` §7.2 / `instructions/common/codebase_map.md:303`〜
