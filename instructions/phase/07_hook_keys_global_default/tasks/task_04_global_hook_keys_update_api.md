# task_04_global_hook_keys_update_api

## 目的

hook キーの**全体デフォルトを `config/config.json` へ書き込む経路を新設**し、**成否を返す**ようにする。
現状 `StartupIo.write_startup` は例外を `messagebox.showerror` で表示するだけで**戻り値を持たない**ため、
呼び出し側が「保存できたか」を判断できない（＝握り潰し）。これを解消し、後続タスク（task_06 の
capture 所有者切替）が**保存成功時のみ** UI / ランタイムを確定できるようにする。

- 根拠: [暫定仕様 06](../../../history/06_hook_keys_global_default.md) §5 後半（全体デフォルト更新 API は
  成否を返す・失敗時は旧値維持または未保存を明示）/ §7 受入条件 **4**（OFF 時のキー編集が
  config.json を成否付きで即永続化）と **7**（保存失敗時に UI / ランタイムを確定させない）。
- **レイヤ制約**: **presentation 限定**（`keyseq/presentation/controllers/config_io/startup_io.py` のみ）。
  application（`config_service/`）・domain（`config.py`）は**変更しない**
  （書き込みの実体は既存の `ConfigService.save_startup` を使う。presentation が
  `config/config.json` を直接開いて書くことは禁止 = phase.md レビュー方針 6）。
- **本タスクは API の新設と成否伝搬まで**。呼び出し元の UI 配線は task_05 / task_06。

## 対象範囲（presentation 限定・`startup_io.py` の 2 メソッド）

### 1. `StartupIo.write_startup` を**成否付き**にする

```python
    def write_startup(self, data: dict[str, any]) -> bool:
```

- **既存の振る舞いは変えない**（`base` の組み立て・`config_path` の除去・`ui_font_delta_pt` の
  `coerce_font_delta`・失敗時の `messagebox.showerror` はそのまま）。
- 変更点は戻り値のみ: **成功で `True` / 例外を捕捉したら `False`**。
- `self._app._startup_settings = base` の代入は**現状どおり `try` の中（保存成功後）に置く**
  ＝ 失敗時は in-memory の旧値が維持される（暫定仕様 §5「失敗時は旧値へロールバック」）。
  **この位置を動かさない**。
- 既存の呼び出し元（`app.py:257` のフォントサイズ変更 / `keymap_set_io.py:636` の keymap_set パス記録）は
  戻り値を無視するため**変更しない**。

### 2. `StartupIo.write_global_hook_keys` を新設する

```python
    def write_global_hook_keys(self, *, stop_key: str, toggle_key: str) -> bool:
        """hook キーの全体デフォルトを config/config.json へ保存する（成否を返す）。"""
```

- 両キーを `normalize_key_name(str(value or ""))` で正規化する
  （`keyseq.domain.config` から import。presentation からの直接 import は既存多数の踏襲）。
- 正規化した 2 キーを `write_startup({"hook_stop_key": ..., "hook_toggle_key": ...})` へ渡し、
  **その戻り値をそのまま返す**。
- **必ず 2 キーとも書く**（片方だけの更新 API にしない。clear は空文字を渡して表現する）。
- **`app.data`（ランタイム）や ui_vars は触らない**。反映は呼び出し側（task_06）の責務。

### 設計メモ / 制約

- **書き込みは `write_startup` の 1 経路に集約する**。`ConfigService.save_startup` を
  `StartupIo` 以外から直接呼んだり、config.json を別途 read-modify-write したりしない。
  理由: `_startup_settings`（in-memory の起動設定）と config.json の内容が**乖離する**と、
  次の `write_startup`（フォント変更・keymap_set パス記録）が**古い `_startup_settings` を土台に
  上書きして hook キーを消す**。これが本タスクで最も壊しやすい点。
- 読み出し側は task_02 の `split_loading.load_global_hook_keys(service, config_root=...)`
  （+ 公開 API `ConfigService.apply_global_hook_key_defaults`）が既に完成している。
  **読み出しロジックを本タスクで作らない・触らない**（解決点は 2 本のまま）。
- keymap_set 保存時のカスケード（`keymap_set_io.py:116` が
  `save_runtime_data(startup_data=self._app._startup_settings)` を渡す）は
  `build_startup_payload` が `startup_data` を丸ごとコピーするため、**全体デフォルトは自動的に維持される**。
  ここに hook キー用の分岐を足さない（確認節でテストとして固定する）。
- `write_startup` の `messagebox.showerror` は**残す**（失敗を握り潰さないための既存の可視化）。
  戻り値の追加はこれと排他ではない。

## 含まない

- **チェックボックス UI**（task_05）/ **capture・clear の所有者切替、dirty 非汚染、
  ON⇄OFF の表示切替と個別値のセッション内保持**（task_06）。
  本タスクで新設する API を**呼ぶコードは書かない**（呼び出し元は task_06）。
- **保存成功時に `app.data` / ui_vars を更新する処理**（task_06）。本 API はランタイムを触らない。
- **読み出し**（task_02 完了済み）/ **keymap_set への保存**（task_03 完了済み）/
  **domain の移行判定**（task_01 完了済み）。
- フック層（`input_router` / `hook_controller` / `keyboard_window` / `app.py`）の変更。
- `write_startup` の既存呼び出し元 2 箇所を「成否を見る」形へ改修すること（本フェーズの要件外）。
- 正本 `spec_detail/` への反映（task_08）。

## 確認

python は**リポジトリルートの `.venv`**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。

1. `-m compileall -q keyseq main.py tests tests_ui` が clean。
2. **`write_startup` の成否テスト**（既存の `write_startup` テストがある
   `tests_ui/test_startup_font_characterization.py` へ追加）:
   - 保存成功時に **`True`** を返し、`_startup_settings` が更新される
   - `save_startup` が例外を投げたとき **`False`** を返し、**`_startup_settings` が更新されない**
     （旧値維持・受入条件 7）。**このテストは `messagebox.showerror` を個別 patch すること**
     （tests_ui の `setUp` に fail-fast ガードがあり、patch しないとガードで落ちる）
3. **`write_global_hook_keys` のテスト**（同上または
   `tests_ui/test_config_io_characterization_keymap_set_startup.py`。実 IO で config.json を検証）:
   - 指定した 2 キーが正規化されて（`"F1"` → `"f1"`）config.json に書かれ、**`True`** を返す
   - **既存の起動設定が保たれる**（`keymap_set_path` / `ui_font_delta_pt` が消えない = マージ動作）
   - 空文字を渡すと 2 キーとも `""` で書かれる（clear 操作の表現）
   - 保存失敗時に **`False`** を返し、config.json / `_startup_settings` が変化しない
4. **往復テスト**（task_02 の読み出しと接続することの確認）:
   - `write_global_hook_keys(stop_key="F1", toggle_key="F2")` の後に
     `split_loading.load_global_hook_keys(config_service, config_root=...)` が `("f1", "f2")` を返す
5. **keymap_set 保存で全体デフォルトが消えないこと**:
   - 全体デフォルトを書いた後に keymap_set を保存し、config.json の
     `hook_stop_key` / `hook_toggle_key` が**保持されている**
6. `-m unittest discover -s tests` が全 pass（現在 168 件。本タスクは presentation 限定のため
   **増減しない想定**。増えたら理由を報告）。
7. `-m unittest discover -s tests_ui` が全 pass（現在 159 件 + 追加分。**件数を報告**）。
8. `-m tests.smoke_app` が pass。

## 完了条件

- 「確認」1〜8 がすべて pass（テスト実測は `verifier` が行う。Codex は python を実行できない）。
- **reviewer 採用**（`.claude/rules/review.md` の 5 観点 + phase.md レビュー方針の
  **4「保存失敗時の扱い」**〔失敗時に `_startup_settings` を確定させていないか〕と
  **6「層の分離」**〔presentation が config.json を直接書いていないか / 書き込み経路が
  `write_startup` の 1 本に集約されているか〕）。
- **実機目視は本タスクでは実施しない**（API 新設のみで UI からの呼び出し元がまだ無いため）。
  Phase γ の実機目視は **task_07** でまとめて実施する。
