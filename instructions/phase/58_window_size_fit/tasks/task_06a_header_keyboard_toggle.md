# task_06a_header_keyboard_toggle

## 目的

省略表示の上部の「フック」「表示」の見出しを、キーボードでも開閉できるようにする（Tab で見出しを選び Enter / Space で開閉）。
「表示」を閉じると「フルに戻す」ボタンが隠れ、表示切替のショートカットは無いため、キーボードだけではフル表示へ戻れない（task_06 の Codex 敵対的レビューの指摘・裏取り済み・ユーザー確定 2026-10-15）。
**presentation 限定（views/compact_view・controllers/compact_header_controller）・domain / application 不変・スキーマ不変。**

## 対象範囲（presentation・省略表示の上部の見出し + テスト）

### `keyseq/presentation/controllers/compact_header_controller.py`

- `register_section` で、開いたときの見出し（`heading`）と閉じた見出し（`collapsed_heading`）の両方を `takefocus=True` にし、`<Return>` / `<space>`（`<KP_Enter>` も）で `toggle(name)` を呼ぶ（`"break"` を返す）
- キー操作で開閉したときは、**フォーカスを同じ区画の今見えている見出しへ移す**（閉じた → 閉じた見出し / 開いた → 開いたときの見出し）。
  マウスのクリックで閉じたときの規則（フォーカスがその枠の中ならトリガー一覧へ）は変えない。
  実装は `toggle(name, *, from_keyboard: bool = False)` 等で分ける（クリックの経路は今のまま）
- 保存（両方の値を 1 回）・最小の高さの測り直しはクリックと同じ

### テスト（`tests_ui/test_compact_header_view.py` に追加）

1. 閉じた「表示」の見出しにフォーカスを置き `<Return>` → 開き、フォーカスが開いたときの見出しにある・`write_startup` が両方の値で 1 回
2. 開いた「フック」の見出しで `<space>` → 閉じ、フォーカスが閉じた見出し（`▸ フック`）にある（トリガー一覧ではない）
3. 両方の見出しの `takefocus` が真（Tab の移動先に入る）
4. マウスのクリックで閉じたときは従来どおりトリガー一覧へ移る（既存の `test_closing_section_moves_focus_to_trigger_list` が通ること）
- 後始末は既存の作法（開閉の状態を元へ戻す）

## 正本（メインが同タスクで更新）

- `features.md` §4.6「省略表示の上部の開閉」: 見出しは Tab で選べ Enter / Space で開閉・キー操作で開閉したときのフォーカス・「表示」を閉じた受容の文言（「キーボード操作の表示切替は効く」を削り、見出しをキーで開いて戻れる旨へ）
- `codebase_map.md` の CompactHeaderController の行・decisions_archive/58 に判断を 1 行

## 読むファイル

1. `keyseq/presentation/controllers/compact_header_controller.py`（全体）
2. `keyseq/presentation/views/compact_view/compact_view.py`・`hook_frame.py:14-21`・`display_frame.py:12-20`（見出しの生成）
3. `tests_ui/test_compact_header_view.py`（全体・編集対象）

## 含まない

- 表示切替のショートカットの新設 / フル表示の上部
- 提案書 24 のリファクタ（task_07_refactor）

## 確認

（実行は verifier・`.venv` python）
- `compileall -q keyseq main.py tests tests_ui` clean
- `tests_ui/test_compact_header_view.py` pass（追加 1〜4 を含む）
- `unittest discover -s tests` / `-s tests_ui` / `-m tests.smoke_app` 全 pass

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視は任意（ユーザー: 省略表示で Tab → 見出しで Enter / Space）
