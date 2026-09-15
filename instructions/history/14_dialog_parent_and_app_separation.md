# 暫定仕様 14: ネストしたダイアログの前面維持（dialog_transient_parent）

> 状態: **凍結済（2026-09-15・phase 16 完了・v0.5）**。**経緯の参照用**であり、
> **本書の条項を実装の根拠に引かない**。
> **正本 = `spec_detail/features.md` §4.6「モーダルダイアログの作法」（前面維持の 2 条項を追加）**
> **+ `codebase_map.md`（`presentation/modal.py` の節。`grab_modal` の第 2 引数の意味）**。
> 昇格時の判断は `.claude_data/state/decisions_archive/16_dialog_transient_parent.md`。
> 起票元: [idea_17](../backlog/idea_17_action_dialog_preset_manager_parent.md)
> （phase 14 の受け入れ条件 15・暫定仕様 12 §6-5 で「フェーズ外・独立 idea」とユーザーが確定した分離項目）。
> **presentation 限定・スキーマ不変**（正本は `features.md` §4.6 のみ改訂）。
> 番号対応: phase 16 / 暫定 14 / decisions 16。
>
> **v0.5（2026-09-15・凍結）**: 完了判定前レビューを受け、**`features.md` §4.6 へ前面維持の
> 2 条項を追加**（§7・ユーザー採用）。実機目視の結果も反映。**§1-④ の受容根拠 1「UI からは到達しない」は
> 実機で裏付けられた**ため**維持**（task_04 の指摘 1「根拠が誤り」は**取り下げ**。詳細は
> `instructions/phase/16_dialog_transient_parent/integration_result.md` §5）。参照行を `:311` → `:335` へ更新。
>
> **v0.4（2026-09-13・ユーザー確定）**: §5 の確認事項を**推奨どおり確定**し §2 へ移した。
> **非 LIFO で閉じたときに前面維持の指定が消える点（§1-④）も受容で確定**。**設計は確定・実装着手可**。
>
> **v0.3（2026-09-13）**: 確定前の `codex-adversarial-reviewer` レビューを反映。
> ①**追随が要る既存テストは 3 件ではなく 4 件**だった（`test_nested_modal_grab.py:185` を見落としていた）
> ②その結果 v0.2 の受け入れ条件 6「既存テストの書き換えが発生しないこと」は**正しい実装でも達成不能**
> だったため、「**引数契約の追随のみ許容し、grab・生存・復元先のアサーションを弱めない**」へ書き換え
> ③**前面維持の相手を先に破棄すると、残る窓の前面維持が失われる**（実測）ことを §1-⑤ へ追記し、
> **受容の根拠と受け入れ条件**を明記した。
>
> **v0.2（2026-09-13）**: 起票時 `deep-reviewer` レビュー（高 3 / 中 5 / 低 3）を反映し、
> **設計を「所有関係ごと付け替える案」から「前面維持の指定だけを付け替える案」へ変更**（ユーザー確定）。
> **v0.1 の前提「影響は z 順のみ」が誤り**だった（所有関係を変えると**破棄が連鎖する**）。
> あわせて **App 参照の引数分離と属性名の改名は不要になった**ため §3・§5 を差し替え、
> 既存テストへの影響（`confirm_overwrite` の呼び出し固定 3 件）を §3-3 と §8 へ追記した。

---

## §1 目的 / 背景

ネストして開いたダイアログが、**呼び出し元より前面に留まらない**。
アクション編集からプリセット編集を開いた状態で**アクション編集を掴んで動かすと前面に出てしまい**、
放すとプリセット編集の下へ戻る（**ユーザーが実機で確認・2026-09-13**）。
掴み取り（grab）が効いているため操作は届かないが、**前後関係だけが崩れる**。

原因は、**ネストしたダイアログが「App より前」としか指定されていない**こと。
呼び出し元との前後は指定されていないため、順序が保証されない。

### 「親」が指す 3 つの役割（本書の用語）

同じ `parent` 引数が 3 つの別々の役割を兼ねているため、混同しやすい。**本書は明確に分ける**。

| 役割 | 実体 | 決めるもの | 本フェーズで変えるか |
|---|---|---|---|
| **役割 1: 所有関係** | `tk.Toplevel(master)` | **破棄の連鎖**（親を壊すと子も壊れる） | **変えない** |
| **役割 2: 前面維持** | `window.transient(...)` | **重なりの前後** | **これだけ直す** |
| **役割 3: App 参照** | `parent.hook` / `parent.data` 等 | 業務処理の委譲先 | **変えない**（App が正しい） |

### 現状監査（2026-09-13・すべて実測。`codex-explorer` の調査をメインが `ファイルパス:行` で裏取り）

**① 食い違いは 2 件**（`dialogs/` の生成 16 件 + `controllers/config_io/` のローカル `Toplevel` 5 件を全数確認）

| # | 箇所 | 役割 2 の現状 | あるべき姿 |
|---|---|---|---|
| 1 | `dialogs/action_dialog.py:339` | `PresetManagerDialog(self.parent, ...)` → 前面維持の相手が **App** | **`ActionDialog`** |
| 2 | `controllers/config_io/hotkey_presets_io.py:82` | `grab_modal(dialog, self._app)` → 前面維持の相手が **App**。呼び出し元は `PresetManagerDialog`（`preset_manager.py:364` → `app.py:456` のコールバック経由） | **`PresetManagerDialog`** |

**正しく実装されている例**: `preset_manager.py:282`・`:312` の `PresetDialog(self, ...)`。
**プリセット編集 → プリセット追加は前面維持が効いている**（ユーザーが実機で確認）。

**② 役割 1 を動かすと破棄が連鎖する**（`.venv` の python で実測）

```
tk.Toplevel(root) -> 別窓 A（App の子）/ tk.Toplevel(mid) -> 別窓 B（mid の子）
mid.destroy() 後 → A: 生存 / B: 破棄済み
```

**正本 `features.md:96-98` の ③「開いた順と違う順で閉じた（内側がまだ開いている。内側のモーダル性を
優先する）」が、この連鎖と衝突する**。しかも `features.md:95` が例示する組
（**プリセットマネージャ → 上書き確認**）そのものが該当する。
phase 14 の `tests_ui/test_nested_modal_grab.py:335`
（`test_non_lifo_manager_destroy_does_not_steal_confirmation_grab`。**v0.5 で行番号を更新**）は
この契約を検証している。
→ **役割 1 は動かさない**（§2）。

**③ 役割 2 の付け替えは grab 復元に影響しない**

`presentation/modal.py:20` の `previous` は **`grab_current()` の記録**であり、
`transient` とも `master` とも独立している。**phase 14 の保証は無傷**。

**④ 前面維持の相手を先に破棄すると、残る窓の前面維持は失われる**（`.venv` の python で実測）

```
b = Toplevel(root); b.transient(a)   → b.wm_transient() = a
a.destroy() 後                        → b は生存・表示されたまま / b.wm_transient() = ''（空）
```

つまり**非 LIFO で閉じた場合**（上書き確認を残したままプリセット編集を破棄）、
残る上書き確認は**生存も grab も保つ**が、**「App より前」という指定まで失う**。
現状（相手が App）なら App より前は保たれるので、**この一点だけは現状より弱くなる**。

**受容する**。根拠は 3 つ:

- **UI からは到達しない** — 上書き確認が grab を持つ間、プリセット編集は操作できない。
  この経路を通せるのは**プログラムから破棄するテストだけ**
  （`test_nested_modal_grab.py:335` = `test_non_lifo_manager_destroy_does_not_steal_confirmation_grab`）。
  **実機実測（2026-09-15）**: 上書き確認を出した状態では**背面のプリセット編集は × を含めて操作できず**、
  非 LIFO で閉じる操作自体が実行不能だった（タイトルバーの × も grab に阻まれて届かない）。
  **`WM_DELETE_WINDOW` が未登録＝× で直接破棄される**（コード上は事実）ことは、
  **この経路が UI から到達可能であることを意味しない**。
- **正本 ③ の保証（内側が残る・モーダル性を優先する）は守られる** — 失うのは前後の指定だけで、
  **生存と grab は変わらない**。
- **塞ぐには新しい仕組みが要る** — 相手の破棄を捕まえて前面維持を App へ張り直す結線が必要になり、
  **UI から到達しない経路のために可動部を増やす**ことになる（`anti_patterns.md` 3）。

**⑤ 役割 3（App 参照）は現状で正しい**

`PresetManagerDialog` は `parent.hook` / `data` / `config_service` / `config_root` /
`keymap_set_path` / `validate_hotkey` / `hotkey_presets_io` / `save_hotkey_presets` を使う
（`preset_manager.py` の 24 箇所）。**App 以外を渡すと動かない**。
本フェーズは役割 2 だけを分けるため、**引数分離も属性名の改名も不要**。

## §2 確定事項（ユーザー 2026-09-13）

- **役割 2（前面維持の指定）だけを直す**。**役割 1（所有関係）は App のまま動かさない**。
  - 理由: 観測された症状は前後関係のみで、**役割 1 を動かしても症状の改善は増えない**。
    一方で**正本の保証（外側を先に閉じても内側が残る）が変わる**。
  - **v0.1 の「案 A・引数分離」は撤回**（役割 1 を動かす前提だったため）。
- **対象は食い違い 2 件とも**（§1-①）。**上書き確認（食い違い 2）は実機未確認**だが、
  **コード上は同型**のため同時に直し、確認は統合タスクの実機目視で行う。
- **正本 `spec_detail/` は改訂しない**（役割 1 を動かさないため ③ の射程は不変）。
  **作法の明文化と静的検査も行わない**（ユーザー選択）。
- **同じ引数を他のダイアログへ予防的に広げない**（§3-4）。他 7 クラスは生成元が
  `controllers/` のみで食い違いが無く、今必要のない引数を増やすことになる。
  将来 `dialogs/` から別の `dialogs/` を開く箇所が増えたときに、その都度足す。
- **非 LIFO で閉じたときに前面維持の指定が消える点（§1-④）は受容する**。
- **モードは暫定仕様先行**。番号対応: phase 16 / 暫定 14 / decisions 16。

## §3 設計

**共通の考え方**: `grab_modal(window, parent)` の**第 2 引数が役割 2**（`modal.py:25` の
`window.transient(parent)`）。**ここに呼び出し元のウィンドウを渡す**。
`tk.Toplevel(...)` の引数（役割 1）と `self.parent`（役割 3）は**触らない**。

### 3-1. `PresetManagerDialog` に前面維持の相手を受け取る引数を足す

```python
def __init__(self, parent: App, title: str = "プリセット編集", *,
             transient_parent: tk.Misc | None = None):
```

- **`super().__init__(parent)` は無変更**（役割 1 = App）。
- **`self.parent = parent` も無変更**（役割 3 = App）。
- 末尾の `grab_modal(self, parent)`（`:72`）を
  **`grab_modal(self, transient_parent if transient_parent is not None else parent)`** にする。
  **`grab_modal` が `__init__` の最後の文であることは変えない**
  （phase 14 の静的検査 `test_nested_modal_grab.py:262-276` が固定）。
- **既定は `parent`**（= App）。これは**役割の取り違えを許す抜け道ではなく**、
  「前面維持の相手を指定しなければ所有関係と同じ」という**素直な既定**。
  `app.py:418` の `PresetManagerDialog(self, title=...)` は**無変更で従来どおり**。
- **引数名は `transient_parent`**（役割 2 であることを名前で示す。`owner` は役割 1 と紛らわしいため使わない）。

### 3-2. 呼び出しの追随

| 箇所 | 変更後 |
|---|---|
| `dialogs/action_dialog.py:339` | `PresetManagerDialog(self.parent, title=..., transient_parent=self)` |
| `app.py:418` | **無変更** |

### 3-3. 上書き確認ダイアログ（食い違い 2）

`controllers/config_io/hotkey_presets_io.py` の `confirm_overwrite` に
**キーワード必須**の引数を足す。

```python
def confirm_overwrite(self, *, stored_path: str, existing: list | None,
                      transient_parent: tk.Misc) -> str:
```

- **既定値を置かない** — 呼び出し元は `preset_manager.py:364` の**1 箇所だけ**で、
  既定を置くと**初日から到達しない分岐**になる（`anti_patterns.md` 3）。
- **`tk.Toplevel(self._app)`（`:47`）は無変更**（役割 1 = App）。
  **`grab_modal(dialog, ...)`（`:82`）だけ**をこの引数にする。
- 呼び出し側 `preset_manager.py:364` が **`transient_parent=self`** を渡す。
- **application 層は通らない** — コールバック `on_overwrite_conflict` は
  `preset_manager.on_ok` 内で定義され、`app.save_hotkey_presets`（`app.py:423-429`）は
  それを 2 引数で呼ぶだけ（`:457`）。**`save_hotkey_presets` のシグネチャは変えない**。
- **既存テスト 4 件が呼び出し形を固定している**ため追随が要る（実測）。
  - `tests_ui/test_app_ui_flows.py:1201`・`:1261`・`:1313` — `PresetManagerDialog.on_ok(dialog)` を
    スタブに対して直接呼ぶ形。期待値へ **`transient_parent=dialog`** を足す。
  - `tests_ui/test_nested_modal_grab.py:185` — 実ダイアログ経路。期待値へ
    **`transient_parent=<そのマネージャ>`** を足す。
  **いずれも引数契約の追随のみ**で、grab・生存・復元先のアサーションには手を触れない。

### 3-4. 触らないもの

- **役割 1（`tk.Toplevel` の引数）と役割 3（`self.parent`）** — 全クラスで無変更。
- **`presentation/modal.py`** — `grab_modal` の実装も引数名も変えない
  （役割 2 を渡す先というだけ。phase 14 の資産に手を入れない）。
- **`PresetDialog`** — 既に正しい（`preset_manager.py:282`・`:312`）。
- **他 7 ダイアログ** — 生成元が `controllers/` のみで食い違い無し。
  **予防的に引数を足さない**（`anti_patterns.md` 3）。

## §4 テスト方針

`tests_ui/` に置く。phase 14・15 の手法を流用（実 `Toplevel` /
`update_idletasks()` + viewable アサート / `report_callback_exception` の監視 / `addCleanup`）。

- **前面維持の相手が呼び出し元になること** — アクション編集からプリセット編集を開き、
  **`manager.wm_transient()` が `ActionDialog` を指す**ことを見る。
- **所有関係が変わっていないこと** — **`manager.master` は App のまま**
  （phase 14 のテストと同じ観点。**役割 1 を動かしていない証拠**として明示的に固定する）。
- **既定の非変更** — `app.py:418` 経路（`PresetManagerDialog(app)`）では
  **前面維持の相手も App のまま**。
- **上書き確認の相手** — `confirm_overwrite` の `grab_modal` に
  **プリセット編集が渡る**こと。実ダイアログを立てにくい場合は
  **`grab_modal` の第 2 引数を観測**する（スタブは生成引数の確認に限り、
  **grab の観測は実ダイアログで行う** — スタブは `winfo_exists` / `grab_current` を持たない。
  暫定仕様 12 の注記）。
- **phase 14 / 15 の非退行** — ネストの grab 復元とフック停止解除のテストが全て pass。
  **書き換えてよいのは §3-3 の引数契約の追随 4 件だけ**。
  **grab・生存・復元先・`master` に関するアサーションを弱めるのは禁止**
  （弱めたくなったら設計の前提が崩れているので止めてユーザーへ諮る）。
- **変異検査**: ①`transient_parent` を渡さない ②`grab_modal` の第 2 引数を `parent` へ戻す、
  のそれぞれで**対応するテストが落ちる**こと。

## §5 受け入れ条件（ドラフト）

1. **アクション編集から開いたプリセット編集の前面維持の相手が `ActionDialog`** になっている（§3-1・§3-2）。
2. **上書き確認の前面維持の相手がプリセット編集**になっている（§3-3）。
3. **所有関係は全クラスで無変更**（`manager.master` は App のまま・§3-4）。
4. **`app.py:418` の経路は挙動が変わらない**（既定 = 親・§3-1）。
5. **`save_hotkey_presets` のシグネチャが変わっていない**（application 層に波及していない・§3-3）。
6. **phase 14 の grab 復元と phase 15 のフック停止解除が退行していない**。
   **既存テストの変更は §3-3 の引数契約の追随 4 件のみ**で、
   **grab・生存・復元先・`master` のアサーションが弱まっていない**。
6b. **非 LIFO で閉じても残る窓が壊れない** — 上書き確認を残したままプリセット編集を破棄しても、
   **上書き確認は生存し grab を保つ**（既存 `test_nested_modal_grab.py:335` が担保）。
   **前面維持の指定が消えることは受容済**（§1-④）。
7. 既存の `tests` / `tests_ui` が全て pass し `smoke_app` が通る
   （`confirm_overwrite` の呼び出し固定 3 件の追随を含む）。
8. **実機目視**: ①アクション編集 → プリセット編集を開き、**アクション編集を掴んで動かしても
   プリセット編集が前面に残る**（v0.1 で確認された症状が消えている）
   ②プリセット編集 → 上書き確認で、**上書き確認が前面に残る**。

## §6 スコープ外（本フェーズでやらない）

- **役割 1（所有関係）の付け替え**と、それに伴う正本 `features.md` ③ の改訂（§2）。
- **正本への作法の明文化と静的検査**（ユーザー確定）。
- **App 参照の引数分離・属性名の改名**（役割 2 だけを直すため不要になった。v0.1 から撤回）。
- **grab 復元の仕組み**（phase 14）/ **フック停止解除の仕組み**（phase 15）。
- **ダイアログ同型スケルトンの共通化** / **静的検査の発見ベース化**（`current.md` の候補送り）。
- **他 7 ダイアログへの予防的な引数追加**（§5-1）。
- **application / domain / infrastructure の変更**。

## §7 正本反映（フェーズ末昇格・予定）

- **`features.md` §4.6 へ 2 条項を追加**（**v0.5 で改訂。当初は「改訂なし」の予定だった**）。
  「ネストして開いた子は呼び出し元より前面に留まる」「呼び出し元を先に閉じたら前面維持の指定は
  戻らない（生存と grab は変わらない）」。**役割 1 を動かさないため `features.md` ③ の射程は不変**。
  当初の非改訂根拠「正本に `transient` 親の規定は無い」は、**規定が無いこと自体が追加すべき理由**
  であって非改訂の根拠にならない（phase 16 完了判定前レビューの指摘 1・ユーザー採用 2026-09-15）。
- **`codebase_map.md`** — `PresetManagerDialog` の引数が 1 つ増えるため、記述があれば 1 行更新する。
- 実装ファイル: `dialogs/preset_manager.py` / `dialogs/action_dialog.py` /
  `controllers/config_io/hotkey_presets_io.py`。
- テスト: `tests_ui/`（新規または既存への追記）+
  **期待値の追随 4 件**（`test_app_ui_flows.py:1201`・`:1261`・`:1313` /
  `test_nested_modal_grab.py:185`）。

## 関連

- 起票元: [idea_17](../backlog/idea_17_action_dialog_preset_manager_parent.md)
  （**idea の「引数で分離する必要がある」は役割 1 を動かす前提の記述**。本書 v0.2 では不要）
- 前フェーズ: [phase 15](../phase/15_dialog_teardown_on_close/phase.md)（後始末）/
  [phase 14](../phase/14_nested_modal_grab_restore/phase.md)（grab 復元。**本件の分離元**）
- 正本: `spec_detail/features.md` §4.6「モーダルダイアログの作法」（**今回は改訂しない**）
