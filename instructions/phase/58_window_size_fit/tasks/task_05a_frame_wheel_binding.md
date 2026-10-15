# task_05a_frame_wheel_binding

## 目的

フル表示の 3 枠で、枠（`LabelFrame`）の余白（padding 10px）と見出しの上のマウスホイールでも枠をスクロールする（暫定 42 §3.4「`LabelFrame`・Canvas・中身の Frame などの容器」）。
task_05 の deep-reviewer 指摘 1（ユーザー確定 2026-10-15・decisions の phase 58 節）。**presentation 限定（views/full_view）・domain / application 不変・スキーマ不変。**

## 対象範囲（presentation・フル表示のスクロール領域 + テスト）

### `keyseq/presentation/views/full_view/scroll_area.py`

- `bind_wheel` で、今のスクロール領域から下への結び付けに加えて、**親の枠（`self.master` = `LabelFrame`）本体にも** `<MouseWheel>` → `_on_mousewheel` を結び付ける（`add="+"`）。枠の他の子へは広げない（子はスクロール領域だけ）
- `bind_all` は使わない・一覧と一覧のスクロールバーの除外（`skip`）は今のまま

### テスト（`tests_ui/test_full_view_scroll_areas.py` に追加）

- スクロールバーが出ている枠（例: `window_min_height - 150` の高さ・作法は既存の `test_wheel_scrolls_containers_but_not_lists_or_delay_value`）で、**枠（LabelFrame）本体**の上の `<MouseWheel>`（delta=-120）で枠の `canvas.yview()` が進む
- スクロールバーが出ていない高さ（`app.winfo_reqheight()`）では、枠本体の上のホイールで `canvas.yview()` が変わらない
- 後始末は既存の `_restore` / `addCleanup` の作法

## 読むファイル

1. `instructions/history/42_window_size_fit.md` §3.4
2. `keyseq/presentation/views/full_view/scroll_area.py`（全体）
3. `tests_ui/test_full_view_scroll_areas.py`（全体・編集対象）

## 含まない

- 一覧のスクロールバーの上のホイールの自動テスト・3 枠同時のスクロールバーの自動テスト（保留・decisions phase 58）
- 正本反映（task_06）

## 確認

（実行は verifier・`.venv` python）
- `compileall -q keyseq main.py tests tests_ui` clean
- `tests_ui/test_full_view_scroll_areas.py`・`test_full_view_min_size.py`・`test_full_view_min_height.py`・`test_full_view_panes.py` pass
- `unittest discover -s tests` / `-s tests_ui` / `-m tests.smoke_app` 全 pass（件数が減っていない）

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視は不要（task_06 前にユーザーが任意で確認）
