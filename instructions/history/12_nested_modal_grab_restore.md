# 暫定仕様 12: ネストしたモーダルの grab 復元（nested_modal_grab_restore）

> 状態: **凍結済（2026-09-12・phase 14 完了・v0.5）**。**経緯の参照用**であり、
> **本書の条項を実装の根拠に引かない**。
> **正本 = `spec_detail/features.md` §4.6「モーダルダイアログの作法」**
> **+ `data_schema/5_10_03_save_contract.md`（上書き確認がネストであることの相互参照）**
> **+ `codebase_map.md`（`presentation/modal.py` の責務）**。
> 昇格時の判断は `.claude_data/state/decisions_archive/14_nested_modal_grab_restore.md`。
> 起票元: [idea_10](../backlog/idea_10_nested_modal_grab_restore.md)（phase 09 task_07g の暫定仕様 v0.10
> に対する `codex-adversarial-reviewer` 指摘 High 2 から分離・2026-08-15）。
> 番号対応: phase 14 / 暫定 12 / decisions 14。
>
> **v0.2（2026-09-10）**: 起票時 `deep-reviewer` レビューを反映。ネスト経路を 1 本追加（§1・A-1）/
> 復元条件から「自分自身のとき」を削除（§3-1・A-2）/ ヘルパの形を成立する案へ差し替え（§4・C-1）/
> viewable 判定を追加（§3-2・A-3）/ 行番号・件数の誤りを訂正（A-5・A-6）。
>
> **v0.3（2026-09-10）**: §6 の確認事項 6 件をユーザーが確定し §2 へ移した。設計は確定
> （子側復元 + 全 13 箇所 + stdlib 対象外 + スケルトン分離 + 親付け替えは別 idea + 正本 2 行追加）。
> **残るは確定前の敵対的レビューのみ**。
>
> **v0.4（2026-09-10）**: 確定前の `codex-adversarial-reviewer` レビューを反映。
> 復元契約に 3 条追加（§3-6 初期化失敗の回収 / §3-7 非 LIFO 終了で grab を奪わない /
> §3-8 コールバック例外では子を閉じない）。§4 の「生成時例外も同時に消える」を撤回。
>
> **v0.5（2026-09-11・ユーザー確定）**: **§3-6 を「回収（破棄 → 復元 → 再送出）」から
> 「grab 取得後に初期化を残さない構造 + 静的検査」へ改訂**（受け入れ条件 7 も追従）。
> task_02 で 9 クラスとも `grab_modal` が `__init__` の最後の文になり、回収の適用対象が
> 消えたため。**実行時の挙動は変えない**。あわせて系統 B の 4 箇所で `protocol` / `bind` の
> 登録を `grab_modal` の前へ移し、全 13 箇所で不変条件を成立させる（task_04）。
> 初期化失敗時にフック再開が走らない件は **[idea_16](../backlog/idea_16_wm_close_skips_destroy_override.md)**
> へ分離（× 閉じでも起きる既存の不具合で、grab 復元とは独立）。
> 受け入れ条件と §5 テスト方針に対応する 3 ケースを追加。**設計の選択は変更なし**。

---

## §1 目的 / 背景

モーダルダイアログの中から別のモーダルを開いて閉じると、**親ダイアログの grab が復元されず**、
親が開いたままメインウィンドウを操作できてしまう。Tk は grab 保持ウィンドウの破棄で grab を
**解放するだけで、直前の grab を戻さない**ため。

実害は「表示と書込先の不一致」。プリセット編集ダイアログは**開いた時点の一覧と個別/グローバルの
状態**を保持するので、モードレスな隙にメインウィンドウで別の構成セットを読み込む・新規作成する・
保存すると、その後の OK で **書込先は「今の」構成セット / 内容は「前の」セットで編集していた一覧**
という食い違いが起き得る。phase 09 で潰した経路が UI 操作の隙から再び入る。

本フェーズは **presentation 層のみ・スキーマ不変・挙動は「モーダルが最後までモーダルであること」の
是正のみ**とする。

### 現状監査（2026-09-10・v0.2 で訂正）

`wait_window()` の呼び出しは **20 箇所**。棚卸しはこの 20 箇所を分類し尽くす形で行う
（v0.1 でネスト経路を 1 本取りこぼしたため、基準を明示する）。

grab を取る箇所は 2 系統・13 箇所ある。

**系統 A: `tk.Toplevel` サブクラスが自分で `grab_set()` する（9 クラス）**

| ファイル | 行 | 順序 |
|---|---|---|
| `dialogs/action_dialog.py` | 119-120 | `grab_set` → `transient` |
| `dialogs/keymap_edit_dialog.py` | 53-54 | 同上 |
| `dialogs/layout_delete_dialog.py` | 50-51 | 同上 |
| `dialogs/preset_dialog.py` | 38-39 | 同上 |
| `dialogs/preset_manager.py` | 71-72 | 同上 |
| `dialogs/trigger_dialog.py` | 52-53 | 同上 |
| `dialogs/orphan_sweep_dialog.py` | 24-25 | `transient` → `grab_set` |
| `dialogs/quarantine_manage_dialog.py` | 24-25 | 同上 |
| `dialogs/reference_cleanup_dialog.py` | 55-56 | 同上 |

**系統 B: 呼び出し側が素の `tk.Toplevel` に `transient` + `grab_set` + `wait_window` を書く（4 箇所）**

- `controllers/config_io/child_save_dialog.py:24-27`（子ファイル保存の一覧）
- `controllers/config_io/child_save_dialog.py:241-245`（トリガー一覧の依存確認）
- `controllers/config_io/hotkey_presets_io.py:79-82`（プリセット上書き確認）
- `controllers/config_io/io_dialogs.py:54-58`（保存名にラベルを合わせるか）

**ネストが実際に起きる経路 = 3 系統**（v0.1 は 2 系統としていた。3 を追加）

1. `dialogs/preset_manager.py:283`（`add`）/ `:318`（`edit`）→ `PresetDialog`。
   `PresetManagerDialog` は `:71` で grab 済み。閉じた後に grab が戻らない。
2. `dialogs/action_dialog.py:342`（`_open_preset_manager`）→ `PresetManagerDialog`。
   `ActionDialog` は `:119` で grab 済み。**1 と連鎖して 3 段**
   （`ActionDialog` → `PresetManagerDialog` → `PresetDialog`）になる。
   このとき親に **`self.parent`（= App）を渡しており `ActionDialog` 自身ではない**ため、
   `transient` の親も App になり `ActionDialog` より背面へ回り得る。
3. **`dialogs/preset_manager.py:364`（`on_ok` 内の `on_overwrite_conflict`）→
   `controllers/config_io/hotkey_presets_io.py:42` `confirm_overwrite`**（`:79-82` で grab）。
   **本件で最も実害が大きい経路**。`app.py:456-457` は `choice != "overwrite"` で
   `save_hotkey_presets` が `False` を返し、`preset_manager.py:381-382` は
   **`self.destroy()` を呼ばない**。つまり「上書きを承諾しなかったユーザーの手元に、
   **grab を失ったマネージャが開いたまま残る**」。§1 冒頭の実害シナリオそのものが最も起きやすい。
   idea_10 の起票経緯（3 択ダイアログがマネージャの中から開く）とも一致する。
   なお**開く側は `HotkeyPresetsIo`** であり、grab を持っていた `PresetManagerDialog` とは別物である
   （§3-1 の条件設計に効く）。

**ネストしない（順次実行）経路 = 残る 17 の `wait_window`**:
`controllers/keymap_panel_controller.py:262` / `controllers/layout_controller.py:209` /
`controllers/trigger_panel_controller.py:362`・`:403`・`:471`・`:488` / `app.py:418` は
メインウィンドウから開く。`controllers/config_io/` の `orphan_sweep_io.py:28`・`:68` /
`quarantine_manage_io.py:26`・`:45`・`:66` / `reference_cleanup_io.py:43` / `io_dialogs.py:58` /
`child_save_dialog.py:27` も同様。`child_save_dialog.py` の
`confirm_trigger_set_dependency`（`:219`）と `confirm_recalculated_overwrite`（`:288`）は
`keymap_set_io.py:244`・`:260`・`:360` から呼ばれ、一覧ダイアログが閉じた後の逐次呼び出しである。

**stdlib ダイアログを親が grab したまま開く箇所（§6-3 の判断材料）**:

- `dialogs/orphan_sweep_dialog.py:51` — `filedialog.askdirectory(parent=self)` を、
  自分が `:24-25` で grab したまま呼ぶ
- `controllers/config_io/child_save_dialog.py:213` — 一覧ダイアログが開いたまま
  `_ask_save_as_path`（`filedialog.asksaveasfilename`）を呼ぶ（`_resolve_action_targets` は `:209`）
- `controllers/config_io/child_save_dialog.py:265` — 依存確認ダイアログが開いたまま同上
  （`destroy` は `:267` / `:270`）
- `confirm_recalculated_overwrite` は `messagebox.askyesnocancel` に加え `:315` でも同上
- `dialogs/` 配下の `messagebox` / `filedialog` 呼び出しは **18 箇所**

**`destroy()` を override しているのは 9 クラス中 8**（`preset_dialog.py` のみ持たない）。
フック再開などの後始末をそこで行っている。復元処理の置き場所に効く（§4）。

**既存の nest 管理の先例**: フックの停止/再開は**子側**（`__init__` / `destroy`）で
nest-count 管理している（`controllers/hook_controller.py:24-38`）。

**正本の現状**: `spec_detail/` に grab・モーダルの規定は**一切ない**（`grep` 0 件）。
「モーダルである」という暗黙の前提に実装が追いついていない状態であり、
**正本の改訂ではなく新規条項の追加**になる。

---

## §2 確定事項（ユーザー 2026-09-10）

- **起票元は idea_10**。phase 14 として着手する（2026-09-10 ユーザー指示）。
- **モードは暫定仕様先行**（複数ファイルに跨る + 棚卸しが探索的 + タスク 3 以上）。
- **復元の主体 = 子側**（§4 案 X）。ダイアログが自分の `grab_set()` の前に直前の保持者を記録し、
  破棄時に戻す。`wait_window` 側 20 箇所には触らない。根拠は §6-1。
- **適用範囲 = 系統 A・B の全 13 箇所**をヘルパへ寄せる（§6-2 案 B）。
  系統 B の 4 箇所を先行タスク、系統 A の 9 クラスを後続タスクに分ける。
- **stdlib のダイアログ（`messagebox` / `filedialog`）は対象外**。
  「**未検証・実害報告なし**」と明記し、**実機目視の 1 項目としてユーザーへ残す**（§6-3）。
- **ダイアログ同型スケルトンの共通化は本フェーズに合流させない**。
  ヘルパを足場として残し、フェーズ末の `/refactor_check` で再判定する（§6-4）。
- **`ActionDialog` の親付け替えは本フェーズから外す**。独立した idea として起票する（§6-5）。
- **正本へ 2 行の作法規定を追加する** — `features.md` §4.6 に小節を新設し、
  `data_schema/5_10_03_save_contract.md` へ相互参照を 1 行足す（§6-6）。

---

## §3 復元規約（設計本文）

モーダルを開く際に **開く前の grab 保持者を記録し、閉じたらその保持者へ戻す**。規約は次の 8 条。

1. **記録した保持者が `None` でなければ、その保持者へ戻す**。
   `None`（誰も持っていなかった）なら復元しない。
   **「保持者が自分自身のときだけ戻す」という条件は付けない** — §1 のネスト経路 3 は
   開く側（`HotkeyPresetsIo`）と grab 保持者（`PresetManagerDialog`）が別物であり、
   その条件を付けると最も重要な経路が復元されない。
   「もともとモードレスだった親をモーダル化しない」という懸念は **`None` 判定だけで足りる**。
2. **生存かつ表示中のときだけ取り直す** — `winfo_exists()` に加えて `winfo_viewable()` を見る。
   Tk の grab は viewable なウィンドウにしか掛からず、`withdraw` 済み・未マップの相手では
   `TclError: grab failed: window not viewable` になる。`winfo_exists()` は withdraw 済みでも
   真を返すため素通りする（`tests_ui/test_child_save_dialog.py:591`・`:629` は root を
   `withdraw()` しており、この経路を実際に踏む）。
3. **× 閉じでも復元する** — 閉じ方（OK / キャンセル / × / プログラムからの `destroy`）に
   よらず、実際に破棄された時点で復元する。
4. **取り直しの失敗を握りつぶさない** — `tk.TclError` は捕捉してよいが、
   握りつぶすなら理由をコメントで残す（`.claude/rules/python_rules.md`「例外を握りつぶさない」）。
   `grab_current()` 自体も、tkinter 管理外のウィンドウが grab を持つ瞬間に呼ぶと
   `KeyError` になり得るため、記録側も防御する。
5. **保証の限界を明示する** — `wait_window` から復帰して `grab_set()` するまでの
   **無 grab 区間はゼロにできない**。「閉じ切った後にモードレスのまま残らないこと」を保証範囲とし、
   区間ゼロは保証しない。ヘルパを 2 回通しても復元が壊れないこと（冪等）は満たす。
   - **連鎖破棄では復元を保証しない**（**v0.5 で追記**）。親ウィンドウの破棄で子ウィンドウも
     同時に破棄される場合（例: `PresetDialog` の master は `PresetManagerDialog`。
     `preset_manager.py:282`・`:312`）、復元先が破棄途中で `winfo_exists()` /
     `winfo_viewable()` の結果が過渡的になり得る。**保証するのは
     「`TclError` を送出せずアプリ終了を妨げないこと」だけ**で、grab がどこへ戻るかは規定しない。
     連鎖破棄はアプリ終了時か親ごと閉じる場面で起きるため、実害の想定が無い。
6. **grab 取得後に初期化を残さない**（**v0.5 で改訂**） — `grab_modal()` を
   **初期化の最後の文**に置く。grab を取った後に失敗し得るコードが無ければ、
   「grab を握ったままの子が残る」事故はそもそも起こらない。
   例外が `grab_modal()` より前で出れば子はまだ grab を取っておらず、
   **親が grab を保持したまま**になるのでモーダル性は壊れない。
   **待機（`wait_window()`）だけは後に置いてよい**（初期化ではないため）。
   - **回収（破棄 → 復元 → 再送出）は実装しない**。v0.4 まではこれを規定していたが、
     task_02 で 9 クラスとも grab 取得後の初期化が無くなり**適用対象が消えた**ため撤回した
     （ユーザー確定 2026-09-11）。**実行時の挙動は v0.4 の想定と変わらない**
     （どちらでも親が grab を保持したまま残る）。
   - **この規約は静的検査テストで固定する**（§5）。将来 grab 取得後に処理を置く必要が
     生じたら検査が落ちるので、**その時点で回収機構の要否を判断する**
     （落ちること自体が設計判断の呼び出しベルになる）。
   - **残る限界 2 つ**: ①初期化に失敗したウィンドウは破棄されずに残る
     （**grab は持たないので他の操作は妨げない**。× で閉じられる）
     ②停止したフックの再開は `destroy()` override にあるため走らない。
     ②は **× 閉じでも同じ現象が起きる既存の不具合**で、
     [idea_16](../backlog/idea_16_wm_close_skips_destroy_override.md) へ分離した。
7. **非 LIFO 終了で grab を奪わない** — 復元するのは、**破棄の時点で grab を持っているのが
   自分自身か、誰も持っていないとき**に限る。他の生存モーダルが持っているなら復元しない。
   §1 のネスト 3 段はいずれも **App の子**（`action_dialog.py:342` / `hotkey_presets_io.py:45`）で
   連鎖破棄されないため、**中間だけを先に破棄すると最内側の grab を奪える**。
   これは §3-1（**記録した保持者**への条件を付けない）とは**別の条件**である。
   §3-1 は「誰へ戻すか」、本項は「そもそも戻してよいか」を規定する。
8. **コールバック例外では子を閉じない** — Tk はコールバックの例外を
   `report_callback_exception` へ渡すだけで子を破棄しない（`dialogs/preset_dialog.py:41-51` の
   `_ok` は `destroy()` の前に失敗し得る）。**子は開いたまま grab を保ち**、
   その後の実際の閉鎖で復元する。例外そのものを復元の契機にはしない
   （開いている子のモーダル性を壊すため）。

`transient` と `grab_set` の順序は系統 A に 2 種類混在している（§1 表）。
**ヘルパへ寄せた結果として揃うのはよいが、それ自体を目的とした並べ替えはしない**
（挙動差の有無が未検証で、`transient` 直後は一時的に unmapped となり
`grab_set` が not viewable で失敗し得るため。§7 の受け入れ条件にも入れない）。

## §4 実装方針

**ヘルパ 1 本へ集約する**（idea_10 の提案 2）。各呼び出し側に §3 を手書きすると漏れる。

### v0.1 案の不成立（記録）

v0.1 は `open_modal(dialog, parent)` を挙げたが**成立しない**。呼び出しは
`open_modal(PresetDialog(self, ...), self)` の形になり、**引数評価の時点で子の `__init__` が
既に `grab_set` 済み**（`dialogs/preset_dialog.py:38`）。ヘルパ内の `grab_current()` は
**子**を返し、§3-1 の「開く前の保持者」を原理的に取得できない。

### 案 X: 子側で復元する（**採用・2026-09-10**）

Tk 自身の `tk::SetFocusGrab` / `RestoreFocusGrab` と同型。

```python
# keyseq/presentation/modal.py（新規・案）
def grab_modal(window: tk.Toplevel) -> None:
    """window をモーダル化し、破棄時に直前の grab 保持者へ戻す。"""
```

- 子が自分の `grab_set()` の**前**に `grab_current()` を記録し、`<Destroy>` バインド
  （または既存の `destroy()` override）で §3 に従って戻す。
- **利点**: `wait_window` 側 20 箇所を 1 つも触らない。**§1 のネスト経路 3 も自動で直る**
  （開く側が App しか知らなくてよい）。`wait_window` を使わない将来の呼び出しにも効き、
  §6-2 案 A の「次の人が同じ穴を開ける」も塞がる。
  既存の nest 管理（`hook_controller.py:24-38`）が子側であることとも揃う。
- **注意**: 案 X は破棄フックで復元するため、**`grab_set()` 後の初期化で例外が出た場合は
  自動発火しない**（`__init__` を抜けていないため）。**v0.4 まではここで §3-6 の
  明示的な回収を必須としていたが、v0.5 で撤回した**。現在は §3-6 の構造保証
  （`grab_modal()` を初期化の最後の文に置き、grab 取得後に失敗し得るコードを残さない）で
  この問題を回避する。
  v0.3 まで「生成時例外も同時に消える」と書いていたのは誤りで、v0.4 で撤回した。
- **欠点**: 系統 B は素の `Toplevel` なので、結局 4 箇所で 1 行呼ぶ必要がある。
  既存テストが `object.__new__(PresetManagerDialog)` でインスタンスを作り
  `PresetManagerDialog.destroy(dialog)` を直接呼ぶ（`tests_ui/test_app_ui_flows.py:72`・
  `:1327-1338`）ため、**属性未初期化に耐える**必要がある。
- 差分は系統 A の 2 行 + 系統 B の 2 行を**その場で 1 行に置換**する形で収まる。

### 案 Y: 親側でファクトリを受けて開く（不採用）

```python
def open_modal(parent: tk.Misc, factory: Callable[[], tk.Toplevel]) -> tk.Toplevel:
```

記録 → 生成 → `wait_window` → 復元。C-1 の signature 問題と生成時例外を回避できるが、
**`wait_window` 側 20 箇所の書き換え**が要り、ネスト経路 3 のように開く側が
grab 保持者を知らない場合は復元先を渡せない。

**案 X を採用**（ユーザー確定 2026-09-10）。判断の経緯は §6-1。

### 置き場所

`keyseq/presentation/modal.py`（新規）。`dialogs/` と `controllers/config_io/` の**両方**から
使うため、`.claude/rules/file_organization_rules.md` の Feature Shared = レイヤフォルダ直下に当たる。
`config_paths.py` / `listbox_utils.py` と同じ枠。雑多名（`utils` / `helper`）を避け `modal.py` とする。

## §5 テスト方針

`tests_ui/` に**実 Toplevel を使ったネスト経路のテスト**を置く。

**観測手段は確保済み** — `tests_ui/test_quarantine_manage_flow.py:286` が実
`dialog.grab_current()` をアサートしており、grab はテストから観測できる。
`tests_ui/test_app_ui_flows.py:1374` が実 `PresetManagerDialog(self.app)` を生成しているので、
ネストテストの雛形に使える。

**子の閉じ方**: 子は**親のメソッド内部**で生成される（`preset_manager.add()`）ため、
テストから生成前に `after` を仕掛けられない。**子クラスの `__init__` を patch して
生成直後に `self.after(0, self.destroy)` を仕込む**形にする（実装タスクで詰まらないよう手法まで固定）。

固定する条件:

- §1 のネスト経路 **3 系統すべて**。特に経路 3（`PresetManagerDialog` → `confirm_overwrite`）は
  **上書きを承諾せずに閉じた後**にマネージャが grab を保つことを見る。
- × 閉じを 1 本。親が既に破棄されている / `withdraw` 済みのケースで `TclError` にならないこと。
- **初期化失敗**（§3-6・**v0.5 で改訂**）: ①`grab_modal()` **より前**で例外を注入し、
  **親が grab を保持したまま**で例外がそのまま送出されることを見る。
  ②**静的検査**で「9 クラスの `__init__` の最後の文が `grab_modal`」
  「系統 B で `grab_modal` の後に来るのは待機（`wait_window`）だけ」を固定する。
  **回収（破棄 → 復元 → 再送出）のテストは書かない**（実装しないため）。
- **非 LIFO 終了**（§3-7）: App を共通の master とする 3 段で**中間だけを破棄**し、
  最内側が grab を保つことを見る。
- **コールバック例外**（§3-8）: 実際のコールバック経由で例外を起こし、
  通知・子の生存・grab 保持者の 3 点を確認する。

**回帰の基準**: `tests_ui/test_child_save_dialog.py` は
`tk.Toplevel` を `_FakeSaveDialog`（`:149`）へ patch し、`grab_set`（`:180`）も
`wait_window`（`:192`）も no-op である。したがって**同ファイルはフローの回帰基準にはなるが、
grab の回帰基準にはならない**。加えて**このスタブは `winfo_exists` / `grab_current` を持たない**ため、
ヘルパが子に対してそれらを呼ぶ設計（案 X）ならスタブの拡張が要る。実装タスクへ明記する。

---

## §6 判断の記録（すべて確定・ユーザー 2026-09-10）

結論は §2 にまとめてある。本節は**なぜその案を選んだか**と、**確定後も下流に効く条件**を残す。

### 6-1. 復元の主体 — 子側か親側か【最重要】→ **子側（案 X）**

§4 の案 X（子側・推奨）と案 Y（親側ファクトリ）のどちらを採るか。
案 X は `wait_window` 側 20 箇所に触らず、ネスト経路 3 も自動で直る。
案 Y は既存テストの `object.__new__` 経路に影響しないが、書き換え範囲が広く経路 3 を救えない。
**案 X で確定**。**下流条件**: 案 X は `tests_ui/test_app_ui_flows.py:72`・`:1327-1338` の
`object.__new__` 経路を通るため、**復元処理は属性未初期化のインスタンスでも例外を出さない**こと。

### 6-2. 適用範囲 — ネスト経路のみか、全モーダルか → **全 13 箇所（案 B）**

- **案 A: ネスト経路 3 系統だけ直す**。差分最小。ただし**次にネストを増やした人が同じ穴を開ける**。
- **案 B: 系統 A・B の全 13 箇所をヘルパへ寄せる**（推奨）。ネストの有無に関わらず同じ作法になる。
  差分は広いが**挙動は不変**（ネストしない箇所ではヘルパを通しても結果が変わらない）。
- **案 B で確定**。系統 B（4 箇所）を先行し、系統 A（9 クラス）を後続にタスク分割する。

### 6-3. stdlib のダイアログを対象に含めるか → **対象外（未検証と明記）**

§1 のとおり、親が grab したまま stdlib ダイアログを開く箇所が 4 経路ある。

- **対象外で確定**。Windows では両者が**ネイティブのコモンダイアログ**にマップされ、
  OS 側でモーダルになるため Tk の grab を触らない。Tk 内製の描画に落ちる環境では
  `tk::SetFocusGrab` / `RestoreFocusGrab` が **Tk 側で復元を行う**。
- ただし**この判断は未実測であり、自動テストでは事実上検証できない**（ネイティブダイアログが
  ブロックするため）。**「未検証・実害報告なし」として扱う**。
- **下流条件**: フェーズ末の**実機目視項目に 1 行加える** — 「親ダイアログを開いたまま
  ファイル選択またはメッセージボックスを閉じた後、親がモーダルのままか」。
  該当は §1 の 4 経路（`orphan_sweep_dialog.py:51` / `child_save_dialog.py:213`・`:265`・`:315`）。

### 6-4. ダイアログ同型スケルトンの共通化を合流させるか → **分離する**

`current.md` は phase 11 の `/refactor_check` から
「**`Toplevel` + `suspend_hook_for_dialog` / Escape bind / `protocol(WM_DELETE_WINDOW)` /
`transient` + `grab_set` / `destroy` override が 9 ダイアログ中 8 ファイルに広がっている。
着手するなら idea_10 と同じ領域なので合流させる**」を候補送りしている。

- **分離で確定**。本フェーズは grab 復元に絞り、スケルトンは次の `/refactor_check` へ回す。
  フェーズが 2 倍規模になり本題がぼやける。`grab_modal` を先に置けば共通化の**足場**になる。

### 6-5. `ActionDialog` → `PresetManagerDialog` の親を付け替えるか → **本フェーズ外・別 idea**

現状 `PresetManagerDialog(self.parent, ...)` と **App** を渡している（`action_dialog.py:342`）。

- **v0.1 の「付け替えないと 3 段ネストの復元先が曖昧になる」は誤りだったので撤回する**。
  grab の復元先は §3-1 の記録で決まり、Tk の master とは独立している。
  残る論点は `transient` 親の z 順のみ。
- `PresetManagerDialog` は `parent` を App として使う（`preset_manager.py:80`・`:297`・`:332`）ため、
  付け替えには**親ウィンドウと App 参照を分離する引数追加**が要り、`app.py:418` にも波及する。
- **本フェーズから外して確定**。フェーズ末に独立した idea として起票する
  （`/idea`・**フェーズ完了条件に含める**）。

### 6-6. 正本へ「モーダルの保証範囲」を明文化するか → **する（2 行）**

- **`features.md` §4.6 に小節を 1 つ足す**（`#### モーダルダイアログの作法`）。
  規定は「モーダルは閉じるまでモーダルであり続ける」「ネストして開いた子を閉じたら親へ戻る」の
  2 行程度。**実装詳細（ヘルパ名）は書かない**。
- あわせて `data_schema/5_10_03_save_contract.md`（プリセット上書き確認 3 択の契約）へ
  「**この確認はマネージャの中から開く（ネスト）**」の 1 行相互参照を足すと再発を防げる。

---

## §7 受け入れ条件

§6 がすべて確定し、敵対的レビューの指摘も反映したので確定した（v0.4・2026-09-10）。
**v0.5（2026-09-11）で条件 7 を改訂**（§3-6 の構造保証化に追従）。**凍結は task_06 で行う**。

1. `PresetManagerDialog` から `PresetDialog` を開いて閉じた後、`grab_current()` が
   `PresetManagerDialog` を指す（経路 1）。
2. `ActionDialog` から `PresetManagerDialog` を開いて閉じた後、`grab_current()` が
   `ActionDialog` を指す。3 段ネストでも各段で親へ戻る（経路 2）。
3. **`PresetManagerDialog` から上書き確認を開き、「上書きする」以外を選んで閉じた後、
   `grab_current()` が `PresetManagerDialog` を指す**（経路 3・マネージャは開いたまま残る）。
4. 子ダイアログを × で閉じた場合も 1〜3 が成立する（§3-3）。
5. 親が既に破棄されている / `withdraw` 済みの場合に `TclError` を送出しない（§3-2）。
6. もともと grab を持っていなかった親が、子を閉じた後に**モーダル化しない**（§3-1）。
7. **初期化失敗**（**v0.5 で改訂**）: `grab_modal()` より前で例外を注入したとき、
   **親が grab を保持したまま**であり、例外がそのまま送出される。
   加えて **`grab_modal()` が初期化の最後の文である**ことが静的検査で固定されている（§3-6）。
8. **非 LIFO 終了**: 3 段ネストで**中間のダイアログだけをプログラムから破棄**したとき、
   最内側が生存していれば grab は最内側に残る（奪わない）（§3-7）。
9. **コールバック例外**: 実際のコールバック経由で例外を起こしたとき、子は開いたままで
   grab を保持し、その後閉じた時点で親へ戻る（§3-8）。
10. **系統 A・B の全 13 箇所**がヘルパ経由になっている（§6-2）。
    確認手段は `grep "grab_set"` で**ヘルパ以外の直呼びが残っていない**ことを見る。
11. 復元処理が、属性未初期化のインスタンス（`object.__new__` 経路）でも例外を出さない（§6-1）。
12. 既存の `tests/` / `tests_ui/` が全て pass し、`smoke_app` が通る（退行なし）。
13. 正本反映（`features.md` §4.6 の小節 + `5_10_03_save_contract.md` の相互参照）と
    `codebase_map.md` の更新が済んでいる（§9）。
14. **実機目視**: §6-3 の 4 経路で、stdlib ダイアログを閉じた後に親がモーダルのままであること。
15. `ActionDialog` の親付け替えが独立 idea として起票済み（§6-5）。

## §8 スコープ外（本フェーズでやらない）

- **grab 以外の後始末**。親が先に閉じた場合、`wait_window` から戻った後続処理が
  破棄済みウィジェットを触る問題（例: `preset_manager.py:292` 以降）は**本フェーズの対象外**。
  本書が保証するのは **grab の復元のみ**。
- **モーダル自体の設計変更**（モードレス化・非同期化）とダイアログの UI 刷新。
- **ダイアログ同型スケルトンの共通化**（§6-4）。次の `/refactor_check` で再判定。
- **stdlib ダイアログの grab**（§6-3）。未検証・実害報告なしとして扱い、実機目視のみ。
- **`ActionDialog` の親付け替え**（§6-5）。フェーズ末に独立 idea として起票。
- **`transient` / `grab_set` の順序統一を目的とした並べ替え**（§3 末尾）。
  ヘルパへ寄せた結果として揃うのは可。
- `keyseq/application/config_service/__init__.py` の分割（`current.md`「別タスク化候補」に据え置き中）。

## §9 正本反映（フェーズ末昇格・予定）

| 対象 | 内容 |
|---|---|
| `spec_detail/features.md` §4.6 | `#### モーダルダイアログの作法` を新設（2 行） |
| `spec_detail/data_schema/5_10_03_save_contract.md` | 上書き確認がネストである旨の 1 行相互参照（§6-6） |
| `instructions/common/codebase_map.md` | `presentation/modal.py` の追加・責務を記載 |
| 実装 | `keyseq/presentation/modal.py`（新規）/ `dialogs/` 9 ファイル / `controllers/config_io/` 3 ファイル |
| idea 起票 | `ActionDialog` の親付け替え（§6-5）を `/idea` で起票 |
| テスト | `tests_ui/` にネスト経路 3 系統のテストを追加。`_FakeSaveDialog` の拡張要否を判断（§5） |
| 別実装同期 | **なし**（presentation 層のみ・スキーマ不変） |

## 関連

- 起票元: [idea_10](../backlog/idea_10_nested_modal_grab_restore.md)
- 分離元フェーズ: [phase 09](../phase/09_per_keymap_set_presets/phase.md)（task_07g で対象外とユーザー判断）
- 合流候補: `instructions/phase/current.md`「別タスク化候補」の phase 11 `/refactor_check` 候補送り
- 正本: [`spec_detail/features.md`](../common/spec_detail/features.md) §4.6 UI 構成 /
  [`data_schema/5_10_03_save_contract.md`](../common/spec_detail/data_schema/5_10_03_save_contract.md)
