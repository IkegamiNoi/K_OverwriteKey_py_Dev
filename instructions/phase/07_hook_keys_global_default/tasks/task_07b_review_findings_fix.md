# task_07b_review_findings_fix

## 目的

task_07（統合確認）の `deep-reviewer` と `codex-adversarial-reviewer` が挙げた指摘のうち、
**ユーザーが採用を決めた 4 件（A〜D・2026-08-03）**を是正する。

- A: 単一 JSON の Import 経路で全体デフォルトが注入されない（両レビュー一致・**実害あり**）
- B: `apply_global_hook_key_defaults` がフラグを書かないため、全体デフォルトが keymap_set へ
  焼き付く構造的な穴が残る
- C: OFF 保存で keymap_set 書込は成功・後続（config.json 等）が失敗すると、退避した個別値が
  破棄されず**再 ON で復活**しうる
- D: `set_startup_keymap_set` が `write_startup` の成否を見ずに成功表示する

- **D は phase 07 のスコープ外**（hook キーではなく起動 keymap_set パスの既存不具合）だが、
  task_04 で `write_startup` が成否を返すようになったため 1 箇所で直せる。
  **ユーザー判断でこのタスクに含める**（2026-08-03）。
- **レイヤ制約**: application 1 行（B）+ presentation（A・C・D）。domain・View・フック層は**変更しない**。

## 対象範囲

### A. `keyseq/presentation/controllers/config_io/keymap_set_io.py` — `import_config`（`:561` 付近）

`load_legacy_runtime_data` の直後、`apply_loaded_data_to_ui()` の**前**に注入を 1 行追加する:

```python
            self._app.data = self._app.config_service.load_legacy_runtime_data(path)
            self._app.config_service.apply_global_hook_key_defaults(self._app.data, config_root=self._app.config_root)
```

- 理由: この経路だけ解決点を通らないため、OFF（両キー空）なのに全体デフォルトが届かず、
  **キー欄が空のままフックが無反応**になる（受入条件 1 の不変条件が破れる）。
- task_02 の「新規 runtime を生成する 3 箇所」に **Import を 4 箇所目として加える**もの。

### B. `keyseq/application/config_service/__init__.py` — `apply_global_hook_key_defaults`（`:433`）

先頭でフラグの既定値を確定させる:

```python
        runtime.setdefault("hook_keys_individual", False)
        if runtime.get("hook_keys_individual"):
            return runtime
```

- 理由: 保存側 `build_keymap_set_payload` は `resolve_hook_keys_individual(runtime)`
  （フラグが無ければ「非空なら ON」の**移行ヒューリスティック**）で判定する。
  注入 API がフラグを書かないままだと「フラグ無し dict へ注入 → 保存」で
  **全体デフォルトが個別値として焼き付く**（task_03 が「最も壊しやすい点」とした失敗モード）。
- **テスト側の追従が必要**: `tests_ui/test_config_io_characterization_keymap_set_startup.py` の
  スタブ dict 期待値（`{"empty": True, "hook_stop_key": "", "hook_toggle_key": ""}` /
  `{"d": 1, ...}`・**3 箇所**）へ `"hook_keys_individual": False` を追加する。
  これは**実装ではなくテスト側の追従**（実 runtime は `new_default_data()` が既にフラグを持つ）。

### C. `keyseq/presentation/controllers/config_io/keymap_set_io.py` — `save_keymap_set_to`

`discard_retained_hook_keys()` の呼び出しを**現在の `:129`（保存成功後）から
`save_runtime_data` の呼び出し直前**（`skipped_dirty_children = ...` の直後・現 `:112` 付近）へ**移動**する。

- 理由: `save_runtime_data` は **keymap_set（`save_plan_execution.py:138`）→ config.json（`:139`）→
  legacy コピー → 子パス反映**の順に書く。keymap_set 書込後に例外が出ると現在の位置には到達せず、
  ディスク上は OFF・空なのにセッションには退避値が残り、**再 ON で復活 → 次の保存で再永続化**される。
- 移動後の境界は「**保存を実行した時点**」になる。
  - **保存中止（`save_plan is None`）は現在も早期 return するため退避は残る**（この挙動を維持する）。
  - 保存が途中で失敗した場合は退避を失うが、**復活させない方向へ倒す**のが暫定仕様 §2
    「保存後は再 ON しても空」に対して安全側（失われるのは利便性のみ・キーは再入力できる）。

### D. `keyseq/presentation/controllers/config_io/keymap_set_io.py` — `set_startup_keymap_set`（`:638-646`）

`write_startup` の戻り値を見て、**失敗時は成功として確定させない**:

```python
        self._app.keymap_set_path = path
        startup_saved = self._app.startup_io.write_startup(
            {"keymap_set_path": self._app.paths.to_config_relative_or_absolute(path)}
        )
        self.apply_loaded_data_to_ui()
        self._app.state.reset_indices()
        self._app.trigger_panel.refresh_triggers()
        self._app.trigger_panel.refresh_actions()
        self._app.dirty_tracker.set_dirty(False)
        if not startup_saved:
            self._app._set_flash_message("起動時読み込み設定の保存に失敗しました。", auto_clear=False)
            return
        self._app._set_flash_message("起動時読み込み設定を更新しました。")
        messagebox.showinfo("設定", f"次回起動時はこの keymap_set を読み込みます:\n{path}")
```

- **読み込んだデータの UI 反映自体は行う**（runtime は既に差し替わっており、巻き戻しは範囲外）。
  確定させないのは「**次回起動時はこれを読み込みます**」という起動設定の成功表明のみ。
- エラーダイアログは `write_startup` の `showerror` が既に出すため、**二重に出さない**。

### 設計メモ / 制約

- A の注入は既存の公開 API（`apply_global_hook_key_defaults`）を呼ぶだけ。
  **解決ロジックを新たに書かない**（キー解決点は 2 本のまま）。
- B は既定値の確定のみ。**注入の可否判定（フラグが真なら何もしない）は変えない**。
- C は**呼び出し位置の移動のみ**で、`discard_retained_hook_keys` の実装は変えない。
- D は hook キーと無関係の経路。**この 1 箇所以外の `write_startup` 呼び出し元
  （`app.py:257` のフォントサイズ変更）は変更しない**。

## 含まない

- レビュー指摘 **E**（全体デフォルトのキー衝突検証がカレント keymap_set 内に閉じている /
  「明示 `false` + 非空個別値」を読むと個別値が消える）→ **task_08 の正本反映で契約として明記**する
  （実装変更はしない）。
- `resolve_hook_keys_individual` の非 bool 値の扱い（レビュー L2）→ **除外**（過剰実装）。
- `write_startup` の失敗ダイアログ文言（`"startup.json 保存失敗"`・レビュー L1）→ **本タスクでは変更しない**
  （テスト 2 箇所が文言を固定しているため、変えるなら独立タスク）。
- 新機能・仕様変更・リファクタ。

## 確認

python は**リポジトリルートの `.venv`**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。

1. `-m compileall -q keyseq main.py tests tests_ui` が clean。
2. **A のテスト**（`tests_ui/test_config_io_characterization_keymap_set_startup.py`）:
   - config.json に全体デフォルトがある状態で `import_config` を通すと、
     `app.data` の hook キーが**全体デフォルト値**になる（`hook_keys_individual` は `False`）
3. **B のテスト**（`tests/test_config_service.py`）:
   - **フラグを持たない dict** に `apply_global_hook_key_defaults` を適用すると
     `hook_keys_individual` が `False` で**入る**
   - その dict を `build_keymap_set_payload` へ渡すと hook キーが `""` で保存される
     （＝**全体デフォルトが焼き付かない**）
   - 既存の冪等性テストが引き続き pass する
4. **C のテスト**（`tests_ui/test_app_ui_flows.py` または keymap_set 保存系）:
   - ON→OFF の後、`save_runtime_data` が**例外を投げる**保存を実行しても、
     その後の再 ON で個別値が**復活しない**（両キーが `""`）
   - **保存中止**（`_collect_child_save_plan` が `None` を返す）では退避が**残る**（再 ON で復活する）
5. **D のテスト**（`tests_ui/test_config_io_characterization_keymap_set_startup.py`）:
   - `write_startup` が `False` を返すと、成功の `messagebox.showinfo` が**呼ばれない**
   - 成功時は従来どおり `showinfo` が呼ばれる
6. **B のテスト追従**: スタブ dict の期待値 3 箇所へ `"hook_keys_individual": False` を追加した状態で
   既存テストが pass する。
7. `-m unittest discover -s tests` が全 pass（現在 168 件 + 追加分。**件数を報告**）。
8. `-m unittest discover -s tests_ui` が全 pass（現在 176 件 + 追加分。**件数を報告**）。
9. `-m tests.smoke_app` が pass。

## 完了条件

- 「確認」1〜9 がすべて pass（テスト実測は `verifier` が行う）。
- **reviewer 採用**（`.claude/rules/review.md` の 5 観点 + phase.md レビュー方針の
  **1「後方互換」**・**2「キー解決点が 1 箇所か」**・**4「保存失敗時の扱い」**・
  **5「セッション内復活の境界」**）。
- 完了後に **task_07 の実機目視 G1〜G9**（ユーザー実施）へ進む。
