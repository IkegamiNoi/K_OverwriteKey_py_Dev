# idea_10_nested_modal_grab_restore.md

## 概要

**モーダルダイアログの中から別のモーダルダイアログを開いて閉じると、親ダイアログの grab が
復元されず、親が開いたままメインウィンドウを操作できてしまう**。Tk は
**grab を持つウィンドウの破棄で grab を解放するだけで、直前の grab を戻さない**ため。
**`wait_window()` の直後に「自分が生存していれば `grab_set()` を取り直す」**を入れれば直るが、
**ネストが起き得る箇所を洗い出して一括で揃える**必要がある。

## 起票経緯（2026-08-15）

出所: **phase 09 task_07g の暫定仕様 v0.10 に対する `codex-adversarial-reviewer` 指摘（High 2）**。
新設する 3 択ダイアログ（上書き確認）が `PresetManagerDialog` の中から開くため指摘されたが、
調査の結果**既存の「追加」「編集」（`PresetDialog`）が同じ状態**であり、**アプリ全体の課題**と判断。
**task_07g では対象外とし（新経路だけ挙動が不揃いになるため）idea へ分離**した（ユーザー判断）。

## 現状

- `PresetManagerDialog` は生成時に `grab_set()`（[dialogs.py:492](../../keyseq/presentation/dialogs.py)）。
- そこから `add()` / `edit()` が `PresetDialog` を開く
  （[dialogs.py:604](../../keyseq/presentation/dialogs.py) / [dialogs.py:637](../../keyseq/presentation/dialogs.py)）。
  `PresetDialog` も自身で `grab_set()` する。
- **`PresetDialog` を閉じた時点で grab の保持者が居なくなり**、マネージャが開いたままでも
  メインウィンドウが操作可能になる。
- 同型の `grab_set` + `transient` + `wait_window` は `dialogs.py` に複数（`:167` / `:728` / `:781` /
  `:886` / `:988`）、`controllers/config_io/child_save_dialog.py`（`:24` / `:241`）にもある。
  **どこがネストし得るかの棚卸しが要る**。

### 実害の想定

マネージャは**開いた時点の一覧・個別/グローバルの状態**を保持する。モードレスな隙に
メインウィンドウで**別の構成セットを読み込む / 新規作成する / 保存する**と、その後の OK で
**書込先は「今の」構成セット・書く内容は「前の」セットで編集していた一覧**という食い違いが起き得る
（phase 09 で潰してきた「表示と書込先の不一致」が UI 操作の隙から入る経路）。
**【S】の上書き確認は内容比較なので、この経路は捕まえられない**ことがある。

## 提案（方向性・要設計）

1. **`wait_window()` 直後に親が `grab_set()` を取り直す**（`winfo_exists()` で生存確認してから）。
   最小差分。呼び出し側ごとに書くため**漏れやすい**。
2. **ヘルパを 1 本用意して集約する**（例: `open_modal(dialog, parent)` = `transient` / `grab_set` /
   `wait_window` / 親の grab 復元 を一括で行う）。ネストの有無に関わらず同じ作法になる。
   既存の `grab_set` 箇所をこのヘルパへ寄せる範囲をどこまでにするかが設計判断。
3. **例外・× で閉じた場合も復元されること**を保証する（`try` / `finally` 相当）。

## 想定スコープ

- **含む**: `dialogs.py` と `controllers/config_io/child_save_dialog.py` のモーダル生成箇所の棚卸し、
  復元処理の追加、ネスト経路の tests_ui（**実 Toplevel を `after` で閉じ、`grab_current` を確認する**形）。
- **含まない**: モーダル自体の設計変更（モードレス化・非同期化）、ダイアログの UI 刷新。
- **影響レイヤ**: presentation のみ。**仕様変更なし**（正本 `spec_detail/` に grab の規定は無く、
  「モーダルである」という前提の実装漏れの是正）。ただし着手時に
  **「どこまでをモーダルとして保証するか」を明文化するか**は要判断。
- **優先度**: 中〜低（踏むには「ダイアログを開いたまま裏を操作する」必要がある）。
  ただし**追加・編集は日常操作**なので露出そのものは広い。
