# task_03_hook_keys_save_behavior

## 目的

keymap_set 保存時の hook キーの書き出しを**個別指定フラグに従わせる**。
個別指定 ON なら従来どおり個別値を保存し、**OFF なら個別値を空文字にクリアして
`hook_keys_individual: false` を書き出す**（`data_schema.md` の既存キー削除禁止に従い
**キー自体は残す**）。これにより「OFF のまま保存すると個別値は機能的に消え、保存後は再 ON しても空」
という契約が成立する。

- 根拠: [暫定仕様 06](../../../history/06_hook_keys_global_default.md) §5（保存時の挙動）/ §2 /
  §7 受入条件 **3**（ON なら個別値が保存される）と **5**（OFF 保存で空文字化 + フラグ false）。
- **レイヤ制約**: **application 限定**（`keyseq/application/config_service/split_payloads.py` のみ）。
  domain（task_01 完了済）・presentation・フック層・`split_loading.py`（task_02 完了済）は**変更しない**。
- **本フェーズで初めて保存 JSON の内容が変わるタスク**。差分が hook 関連キーのみであることを確認する
  （phase.md レビュー方針 1「後方互換」）。

## 対象範囲（application 限定・`split_payloads.py` の 1 関数）

### `keyseq/application/config_service/split_payloads.py` の `build_keymap_set_payload`

現在の hook キー 2 行（`:331-332`）:

```python
        "hook_stop_key": normalize_key_name(runtime.get("hook_stop_key", "")),
        "hook_toggle_key": normalize_key_name(runtime.get("hook_toggle_key", "")),
```

を、**個別指定の判定に従う形**へ置き換える。

1. `return` の直前で個別指定を判定する:

   ```python
   hook_keys_individual = resolve_hook_keys_individual(runtime)
   ```

   - `resolve_hook_keys_individual` は `keyseq.domain.config` から import する
     （task_01 で新設済み・このモジュールは既に `normalize_key_name` 等を同所から import している）。
2. payload の hook キー 3 項目を次の並びで書き出す（`hook_toggle_key` の**直後**に新キーを置く）:

   | キー | ON（真） | OFF（偽） |
   |---|---|---|
   | `hook_stop_key` | `normalize_key_name(runtime.get("hook_stop_key", ""))` | `""` |
   | `hook_toggle_key` | `normalize_key_name(runtime.get("hook_toggle_key", ""))` | `""` |
   | `hook_keys_individual` | `True` | `False` |

- **キーは常に 3 つとも書き出す**（OFF でも `hook_stop_key` / `hook_toggle_key` を省略しない = 既存キー削除禁止）。
- **`runtime` を書き換えない**（payload 生成関数は副作用を持たない。runtime の hook キーは
  OFF のとき「解決済みの全体デフォルト値」を保持しており、フック層がこれを直読みする。
  ここでクリアするとフックが即座にキーを失う）。
- **他のキー（`trigger_set_path` / `keymaps` / `keyboard_layout` 等）の値・並びは変更しない**。

### 設計メモ / 制約

- **判定に `runtime.get("hook_keys_individual")` を直接使わず `resolve_hook_keys_individual(runtime)` を通す**
  理由: `save_runtime_data` 経由なら冒頭の `ensure_config_compatibility` でフラグが必ず入るが、
  `build_keymap_set_payload` を直接呼ぶ経路（既存テスト等）ではフラグが無い。
  純関数側は「フラグがあればそれに従い、無ければ正規化後どちらか非空で ON」なので、
  **フラグ無しの旧 runtime は従来どおり個別値が保存される**（後方互換）。
  `.get()` の真偽で見ると `false` とキー無しを区別できず移行規則が壊れる（task_01 の申し送りと同根）。
- **OFF 時に書くのは `""` であって runtime の値ではない**。OFF の runtime は全体デフォルトが
  注入された値を持つため（task_02）、`runtime.get(...)` をそのまま書くと
  **全体デフォルトが keymap_set へ焼き付いてしまい**、次回読込で「個別値あり」に見える
  （移行判定が誤発火する）。これが本タスクで最も壊しやすい点。
- 新キーの型は **bool**（JSON の `true` / `false`）。文字列や 0/1 にしない。
- レガシー一括保存（`_sanitize_runtime_for_storage` 経由の legacy コピー）は runtime をそのまま
  書き出すため `hook_keys_individual` が含まれるようになるが、**追加のみで既存キーは減らない**ため
  対応不要（意図的に触らない）。

## 含まない

- **`config/config.json` への全体デフォルト書き込みと成否付き更新 API**（task_04）。
  `startup_io.write_startup` / `build_startup_payload` は**変更しない**。
- **UI チェックボックス**（task_05）/ **capture の所有者切替・dirty 非汚染・ON⇄OFF の表示切替と
  個別値のセッション内保持**（task_06）。本タスクは「保存時に何を書くか」だけを決める。
- **読込側の解決**（task_02 で完了済み。`split_loading.py` は触らない）。
- **domain の移行判定**（task_01 で完了済み。`domain/config.py` は触らない）。
- フック層（`input_router` / `hook_controller` / `keyboard_window` / `app.py`）の変更。
- 「OFF 保存後に、セッション内で保持している個別値も破棄する」処理 → **task_06 の担当**
  （保持先が UI 側の状態であり本タスクの範囲外。task_06 起票時に申し送る）。
- 正本 `spec_detail/` への反映（task_08）。

## 確認

python は**リポジトリルートの `.venv`**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。

1. `-m compileall -q keyseq main.py tests tests_ui` が clean。
2. **既存の payload 完全一致テストの更新**（`tests/test_save_plan.py` の
   `build_keymap_set_payload` 期待値・現 `:100-111`）:
   - フィクスチャの runtime は `hook_stop_key: "f12"` でフラグ無し → **移行判定で ON** となり、
     期待値の変更は **`hook_keys_individual: True` の 1 キー追加のみ**。
     `hook_stop_key` / `hook_toggle_key` の値は**変わらない**（変わったら実装が誤り）。
3. **新規単体テスト**（`tests/test_save_plan.py` または `tests/test_config_service.py`。
   既存の書き方に合わせる）:
   - **ON（`hook_keys_individual: True` + 個別値あり）** の runtime → payload に個別値がそのまま入り
     `hook_keys_individual` が `True`（受入条件 3）
   - **OFF（`hook_keys_individual: False` + runtime に全体デフォルト由来の非空値あり）** の runtime →
     payload の `hook_stop_key` / `hook_toggle_key` が **`""`**、`hook_keys_individual` が `False`。
     **キー自体は payload に存在する**（`assertIn` で確認・受入条件 5）
   - **OFF 保存で runtime 側が書き換わらない**こと（呼び出し後も runtime の hook キーが非空のまま）
   - **フラグ無し + 個別値あり**の runtime → 従来どおり個別値が保存され `hook_keys_individual: True`
     （後方互換・受入条件 6）
   - **フラグ無し + 両キー空**の runtime → `""` + `hook_keys_individual: False`
4. **往復（保存 → 読込）の特性テスト**（`tests/test_config_service.py`。実 IO・一時ディレクトリ）:
   - config.json に全体デフォルトがある状態で **OFF の runtime を `save_runtime_data` → 保存された
     keymap_set.json の hook キーが `""`**（全体デフォルトが焼き付いていない）
   - その keymap_set を読み直すと **OFF のまま**（`hook_keys_individual` が `False`）で、
     runtime の hook キーには**全体デフォルトが再注入**される（受入条件 1・5 の往復整合）
5. `-m unittest discover -s tests` が全 pass（現在 164 件 + 追加分。**件数を報告**）。
6. `-m unittest discover -s tests_ui` が全 pass（159 件）。落ちた場合は
   **保存 JSON へのキー追加に伴うテスト側追従か、実装の範囲逸脱か**を切り分けて報告する。
7. `-m tests.smoke_app` が pass。

## 完了条件

- 「確認」1〜7 がすべて pass（テスト実測は `verifier` が行う。Codex は python を実行できない）。
- **reviewer 採用**（`.claude/rules/review.md` の 5 観点 + phase.md レビュー方針の
  **1「後方互換」**〔既存キーを削除していないか / 保存 JSON の差分が hook 関連キーのみか〕と
  **5「セッション内復活の境界」**〔OFF 保存後に個別値が残らないか〕）。
- **実機目視は本タスクでは実施しない**（UI 変更が無く、全体デフォルトを書く手段がまだ無いため）。
  Phase γ の実機目視は **task_07** でまとめて実施する。
