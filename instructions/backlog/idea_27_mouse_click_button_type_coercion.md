# idea_27_mouse_click_button_type_coercion.md

## 概要

`mouse_click` の `button` が**非文字列だと `AttributeError` で落ちる**。
`keyseq/application/action_executor.py:119` の
`button = (action.get("button") or "left").strip().lower()` が **`try` の外**にあり、
x / y のような「不正なら通知して return」の保護が効かない。

## 起票経緯（2026-09-22）

phase 22（マウスのドラッグ操作）完了判定前の `deep-reviewer` 指摘 6。
`instructions/phase/current.md`「別タスク化候補」に **phase 22 から 5 フェーズ据え置かれていた**ため、
2026-09-22 の current.md 整理でユーザー判断により idea へ昇格。

## 現状

- 実装: `action_executor.py:119`（`_execute_mouse_click` の冒頭）。直後の `x` / `y` は
  `try/except` で `_on_runtime_error` へ流すが、`button` は素通し。
  非文字列（数値・list 等）を入れると `.strip()` が `AttributeError` になり、
  シーケンス実行が**そのアクションで中断**する
- 値の妥当性自体は `action_executor.py:127-128` で `left` / `right` / `middle` 以外を `left` に倒している
- ドラッグ経路（`_execute_mouse_drag`）も同じ `button` を受け取る
- 正本 `data_schema.md` §5.11.2: 「`button` … **文字列で**これ以外の値なら `left` として扱う
  （**非文字列は未定義**）」→ **仕様側が「未定義」と明記しているため、直すなら仕様判断が要る**

## 提案（方向性・要設計）

- **案 A**: §5.11.2 の「非文字列は未定義」を §5.1「型不正の共通規則」に合わせて
  「非文字列は空扱い＝既定 `left`」と規定し、実装を `str(action.get("button") or "")` 等で追従させる
  （idea_24 / idea_25 と同じ「実装を仕様へ追従」型。ただし**今回は仕様側の改訂が先**）
- **案 B**: 実装だけ防御的にし（`try` の中へ入れる）、仕様は「未定義」のまま据え置く
- 読込時正規化（domain の `normalize_actions`）で吸収する案もあるが、
  §5.11 の他フィールドとの一貫性を見て決める

## 想定スコープ

- 含む: `action_executor.py` の 1〜数行 + テスト。案 A なら `data_schema.md` §5.11.2 の改訂
- 含まない: `x` / `y` / `clicks` 等の他フィールドの型規則の見直し
- 影響レイヤ: application（+ 案 A なら正本仕様）。**仕様変更フロー必須**
