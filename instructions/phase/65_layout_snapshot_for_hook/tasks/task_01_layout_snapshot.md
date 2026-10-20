# task_01_layout_snapshot

## 目的

受け取り・送信・キーボードUI が `LayoutController` の**レイアウトの写し 1 つ**を見るようにし、フックの経路で外部レイアウトの JSON を読み直さない・Tk を触らないようにする（暫定 48 §3）。ユーザーがドロップダウンでレイアウトを選んだときは JSON を読み直す（暫定 48 §2・§3-2）。
**presentation 限定（`layout_controller.py`）。application・infrastructure・JSON スキーマは不変。**

## 対象範囲（presentation 限定・`keyseq/presentation/controllers/layout_controller.py` + テスト）

### `LayoutController`

- `__init__`: 写し `self._active_layout` を足し、初期値は組み込みの既定 `BUILTIN_LAYOUTS[DEFAULT_LAYOUT_ID]`（`keyboard_layouts.py` から import）
- 写しの差し替えの補助（例 `_refresh_active_layout()`）: `self._keyboard_layout_entries.get(self.keyboard_layout_id)` の `.layout`、無ければ組み込みの既定を **1 回の代入で** `self._active_layout` へ入れる
- `sync_keyboard_layout_controls`・`set_keyboard_layout_selection`: `self.keyboard_layout_id = selected` の直後に**毎回**（id が変わらなくても）写しを差し替える。今の解放（id が変わるときだけ `_release_held_inputs_before_layout_change`）の順と条件は変えない（解放 → id → 写し）
- `get_current_keyboard_layout()`: 写しを返すだけにする（:178-193 の `load_layout_from_json` での読み直しと `_set_flash_message` の失敗の通知を削除）
- `resolve_key_name_from_scan_code` / `resolve_scan_code_from_key_name` / `should_debug_special_key_event`: 写しを 1 回ローカル変数に取り出して引く（`keyboard_layout_id` と `_keyboard_layout_entries` を読まない）。`resolve_scan_code_from_key_name` は写しに対して `resolve_layout_scan_code_from_key_name`（組み込みは `scan_code` を持たないので結果は今の None と同じ）
- `on_keyboard_layout_selected`（ユーザーの選択・:288-290）: 選んだ id を `self._app.data["keyboard_layout"]` に入れてから `self.reload_keyboard_layouts()`（解放 → JSON の読み直し → `sync` で id と写し）→ `self.persist_keyboard_layout_selection()`。選んだ id が空（表示名が引けない）ときは今と同じく既定へ
- `set_keyboard_layout_selection`（プログラムからの選択・削除の後 :349 等）は読み直さない（今と同じ）
- 不要になった import（`load_layout_from_json` が他で使われていなければ・`resolve_registered_layout_path` 等）は削除。使われていれば残す

### 設計メモ / 制約

- 写しは不変の `KeyboardLayout`（`frozen=True`）なので複製しない。差し替えは UI スレッドの上の 3 か所（`sync` / `set_keyboard_layout_selection` / それを呼ぶ `reload`）だけ
- `reload_keyboard_layouts` は今どおり「解放 → `collect_keyboard_layouts` → `sync_keyboard_layout_controls`」（写しは `sync` の中で差し替わる）
- 読込失敗の新しい通知は足さない（暫定 48 §3-4）
- ロックは足さない（暫定 48 §5）

## 読むファイル

1. `instructions/history/48_layout_snapshot_for_hook.md` §3・§5・§7
2. `keyseq/presentation/controllers/layout_controller.py`（全体・編集対象）
3. `keyseq/presentation/keyboard_layouts.py:1-40`・`:120-135`・`:272-295`（`KeyboardLayout` / `BUILTIN_LAYOUTS` / `DEFAULT_LAYOUT_ID` / `collect_keyboard_layouts`）
4. `tests/test_layout_controller_scan_code.py`（全体・修正対象。:43 の entries が `object()`・:154-170 は属性を直接書き換え get_current を失敗させる仕込み）
5. `tests/test_layout_controller_registration.py`（スタブの作り方の手本）

## 含まない

- `held_inputs` / `key_repeat` / `input_gateway` の送り方の記録（task_02）
- 正本・codebase_map の更新（task_03）
- ファイルの監視・読込失敗の通知・1 打鍵の中の 2 回の解決の統一（暫定 48 §8・§5）

## 確認

- テスト（`tests/test_layout_controller_scan_code.py` を修正・追加）:
  - 初期の写しは組み込みの既定 / `get_current_keyboard_layout` はファイルを読まない（`load_layout_from_json` を差し替えて呼ばれないこと）・`_set_flash_message` を呼ばない
  - `set_keyboard_layout_selection` / `sync_keyboard_layout_controls` で写しが選んだ entry の layout になる・同じ id でも entries が変われば写しが新しい layout になる・entry が無ければ組み込みの既定
  - `resolve_key_name_from_scan_code` / `resolve_scan_code_from_key_name` が写しを引く（entries を後から書き換えても、差し替えるまでは古い写しの結果）
  - `on_keyboard_layout_selected` が `data["keyboard_layout"]` を入れてから `reload_keyboard_layouts` → `persist_keyboard_layout_selection` の順に呼ぶ
  - 既存の解放のテスト（reload / 選択で release が先）が通る
- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` clean
- `-m unittest discover -s tests` 全 pass / `-m unittest discover -s tests_ui` 全 pass（単独実行）/ `-m tests.smoke_app` pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は **task_03 でまとめて実施**（暫定 48 §7-7 ①）。
