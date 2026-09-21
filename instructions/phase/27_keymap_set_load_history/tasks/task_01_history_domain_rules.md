# task_01_history_domain_rules

## 目的

構成セットの読み込み履歴の**規則**を domain の純関数として実装する（暫定仕様 21 §3「データモデル」/
§4.2「積み方」/ §6「操作の規定」/ §7「層の分担」）。型不正の正規化・重複統合・上限 20 の適用・
分類の整列と編集を、**ファイル I/O にもパス解決にも依存しない形**で閉じる。

レイヤ制約: **domain 限定・新規ファイルのみ**。`keyseq/domain/config.py` を含む既存コードは
**一切変更しない**。application / presentation / JSON スキーマには触れない。
**`config_root` に依存しない**（パスの解決・比較キーの生成は application の責務。§7）。

## 対象範囲（domain 限定・新規ファイル 1 つ + テスト 1 つ）

### keyseq/domain/keymap_set_history.py（新規）

履歴データの形は `{"recent": [{"path": str}, ...], "categories": [{"name": str, "entries": [{"path": str}]}]}`。
**すべての関数は入力を変更せず、新しいオブジェクトを返す**（純関数）。
比較キーは引数 `key_of: Callable[[str], str]` で受け取る（呼び出し側が §5.7 の
「解決 → `normpath` → `normcase`」を与える。domain 側では中身を解釈しない）。

- `MAX_RECENT: int = 20` — 直近履歴の上限（§3）。
- `normalize_history(raw: Any, *, max_recent: int = MAX_RECENT) -> dict[str, Any]`
  - `raw` が dict でなければ空の履歴（`{"recent": [], "categories": []}`）を返す。
  - `recent` / `categories` / 各分類の `entries` が list でなければ空扱い。
  - 要素が dict でなければ除去。`path` が非文字列、または trim して空なら**要素ごと除去**。
    残す `path` は **trim 済みの文字列**（小文字化しない）。
  - 分類の `name` が非文字列、または trim して空なら**分類ごと除去**。`name` は trim 済み。
  - 分類名が重複していたら**先に現れた方を残す**（後続は分類ごと除去。比較は trim 後の完全一致・
    大文字小文字を区別する）。
  - `recent` は **先頭から `max_recent` 件へ切り詰める**。
  - **順序は保持する**（並べ替えない）。未知のキーは保持しない（上記の形へ揃える）。
- `is_recent_head(history, path, *, key_of) -> bool`
  - `recent` の先頭が `path` と同一（`key_of` で比較）なら True。`recent` が空なら False。
- `push_recent(history, path, *, key_of, max_recent=MAX_RECENT) -> dict[str, Any]`
  - `recent` から同一パスの要素を**すべて**取り除き、先頭へ `{"path": path}` を挿入し、
    `max_recent` 件へ切り詰めた履歴を返す。`categories` は変更しない。
  - **先頭一致の判定はこの関数では行わない**（呼び出し側が `is_recent_head` で判断する。§4.2-3）。
- `remove_recent_at(history, index) -> dict[str, Any] | None`
  - `recent` の `index` 番目を除去した履歴を返す。範囲外なら `None`（変更なし）。
- `add_category(history, name) -> dict[str, Any] | None`
  - trim した `name` が空、または既存分類と同名（trim 後の完全一致・大文字小文字を区別）なら `None`。
  - それ以外は末尾へ `{"name": name, "entries": []}` を足した履歴を返す。
- `rename_category(history, old_name, new_name) -> dict[str, Any] | None`
  - `old_name` の分類が無い / trim した `new_name` が空 / **他の**分類と同名なら `None`。
  - 同じ名前への変更（trim 後に一致）も `None`（変更なし）。
- `remove_category(history, name) -> dict[str, Any] | None`
  - 該当分類を**配下の `entries` ごと**除去した履歴を返す。無ければ `None`。
- `add_to_category(history, name, path, *, key_of) -> dict[str, Any] | None`
  - 該当分類が無ければ `None`。その分類に**同一パス**（`key_of` で比較）が既にあれば `None`。
  - それ以外は分類の `entries` の**末尾**へ `{"path": path}` を足した履歴を返す。
- `remove_category_entry_at(history, name, index) -> dict[str, Any] | None`
  - 該当分類の `entries` の `index` 番目を除去した履歴を返す。分類が無い / 範囲外なら `None`。
- `sorted_categories(history) -> list[dict[str, Any]]`
  - 分類を**名前の昇順**で並べた list を返す（比較は `str.casefold()`。同値なら元の順序）。
    履歴そのものは変更しない（表示用。§5.2）。

### tests/test_keymap_set_history.py（新規）

`key_of` にはテスト用の単純な関数（例: `str.lower` や恒等関数）を渡す。最低限、次を固定する。

- `normalize_history`: 非 dict / `recent` が list でない / 要素が dict でない /
  `path` が非文字列・空白のみ / 分類名が非文字列・空 / **分類名の重複は先勝ち** /
  **21 件以上は 20 件へ切り詰め** / **順序が保持される** / trim される。
- `is_recent_head`: 先頭一致 True / 不一致 False / 空の `recent` で False /
  **`key_of` が同一視する別表記で True**。
- `push_recent`: 新規は先頭へ / 既存の同一パスは**取り除いてから先頭へ**（件数が増えない）/
  上限で最古が落ちる / **引数の履歴が変更されない**（元のオブジェクトと別物であること）。
- `add_category` / `rename_category` / `remove_category`: 空名・空白のみは `None` /
  同名は `None` / リネームできる / **削除で配下の entries ごと消える** / 存在しない名前は `None`。
- `add_to_category`: 追加できる / **同一分類内の重複は `None`** / 別分類には同じパスを入れられる /
  存在しない分類は `None`。
- `remove_recent_at` / `remove_category_entry_at`: 除去できる / 範囲外は `None`。
- `sorted_categories`: `casefold` 昇順・同値は元の順序・履歴を変更しない。

### 設計メモ / 制約

- **`os` / `os.path` を import しない**。パス解決・`normcase` は application 側（task_02）。
  `key_of` の中身を domain で仮定しない（テストでも任意の関数を渡せること）。
- 型正規化の書き方は `keyseq/domain/config.py` の `coerce_label`（trim のみ・非文字列は空）に倣う。
  ただし**同ファイルへは追記しない**（`file_organization_rules.md` / 肥大化回避）。
- 「変更なし・不可」を `None` で返す設計にしているのは、呼び出し側（task_03 / task_04）が
  「何もしない + メッセージ」と「書き込む」を区別するため。**例外にしない**（正常系の分岐のため）。
- 関数は 30 行以内を目安にする（`.claude/rules/implementation.md`）。共通の内部ヘルパを作ってよいが、
  **公開面は上記の関数と `MAX_RECENT` のみ**とする。

## 読むファイル

- `instructions/history/21_keymap_set_load_history.md` の **§3 / §4.2 / §6 / §7**（このタスクの根拠）
- `keyseq/domain/config.py:70-95` 付近の `coerce_key_name` / `coerce_label`（型正規化の書き方の手本。**変更しない**）
- `tests/test_domain_config.py:1-60`（domain 単体テストの書き方・命名の手本）
- `instructions/phase/27_keymap_set_load_history/phase.md` の「タスク」節（前後タスクの境界）

## 含まない

- **履歴ファイルの読み書き・破損時の退避**（task_02。`ConfigService` 側）
- **保存表記への正規化と比較キー（`key_of`）の生成**（task_02。`config_root` が要るため）
- **記録の呼び出し点への接続 / `record()` / パス指定の共通読込入口**（task_03）
- **履歴ダイアログ・Treeview・メニュー項目・整形関数**（task_04）
- **正本 `spec_detail/` の改訂・`codebase_map.md` の追記・暫定仕様の凍結**（task_05）
- `INTERNAL_MODULE_NAMES` / `DIALOG_FILES` の更新（それぞれ task_02 / task_04）
- 既存ファイル（`domain/config.py` を含む）への変更

## 確認

1. 静的確認: `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests` が clean。
2. 新規テスト単体: `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_keymap_set_history -v` が
   **全 pass**（上記「tests/test_keymap_set_history.py」の項目をすべて含むこと）。
3. 既存テストの退行なし: `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` が
   **pass 518 以上**（phase 26 完了時点 518・skip 7 が基準。**減っていたら退行**）。
4. `keyseq/domain/keymap_set_history.py` に **`import os` が無い**こと（`grep` で確認）。
5. `git diff --stat` の変更が **新規 2 ファイルのみ**であること（既存ファイルの変更が無い）。

※ テストの実行は `verifier` が行う（Codex は python を起動できない。`.claude/rules/agent_selection.md`）。

## 完了条件

- 上記確認 1〜5 が pass・**reviewer 採用**（観点: 暫定仕様 §3 / §4.2 / §6 との適合・
  依存方向〔domain が `config_root` や `os` に依存しないこと〕・後続タスクの先取りが無いこと）。
- 実機目視: **不要**（UI が出るのは task_04。目視は task_04 でまとめて実施する）。
