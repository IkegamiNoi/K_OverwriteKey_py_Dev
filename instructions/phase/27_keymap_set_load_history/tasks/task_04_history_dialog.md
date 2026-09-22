# task_04_history_dialog

## 目的

履歴の UI を作る。ファイルメニューに「履歴から読み込む…」を追加し、`ttk.Treeview` の
一覧（直近 + 分類）から構成セットを開き直せるようにする。エントリ・分類の編集は
**操作ごとに永続化し、成功したときだけ一覧へ反映**する（暫定仕様 21 §5 / §6 / §4.3 / §4.4）。

レイヤ制約: **presentation 限定**。`keyseq/domain/keymap_set_history.py`（task_01）と
`keyseq/application/config_service/keymap_set_history.py`（task_02）は**呼ぶだけで変更しない**。
JSON スキーマ不変。`keymap_set_io.py` / `startup_io.py` / `theme.py` は**変更しない**
（`load_keymap_set_path` と `confirm_save_if_dirty` は task_03 の現状のまま使う）。

## 対象範囲（presentation 限定）

### keyseq/presentation/keymap_set_history_text.py（新規・純関数のみ）

表示文字列の唯一の定義。**I/O・ウィジェット・config_root に触らない**
（手本 = `keyseq/presentation/quarantine_manage_text.py`）。

```python
RECENT_NODE_LABEL = "直近（最大 20 件）"
MISSING_SUFFIX = "（見つかりません）"
READ_ONLY_NOTICE = "履歴ファイルを読み込めませんでした。編集できません。"

def format_entry_name(path: str, *, exists: bool) -> str:
    """名前列 = 拡張子なしのファイル名。不在なら MISSING_SUFFIX を付す。"""
```

- 編集操作の失敗理由・確認文言もこのモジュールへ定数 / 関数として置く
  （例: 分類名が空 / 同名 / 分類未存在 / 分類内に既にある / 削除の確認文 / 分類 0 件の通知）。
  **io とダイアログに文言リテラルを散らさない**。
- 件数・ファイル名などの値は関数引数で受け、このモジュールで履歴 dict を解釈しない。

### keyseq/presentation/controllers/config_io/keymap_set_history_io.py（既存・追記）

`record()` は**変更しない**。以下を追記する。**各編集メソッドは必ず
`config_service.load_keymap_set_history` で読み直してから domain 関数を適用**し、
`config_service.save_keymap_set_history` が成功したときだけ `(True, "")` を返す
（メモリ先行更新をしない = 暫定仕様 §4.2 手順 1 / §4.3）。

```python
def open_history_dialog(self) -> None:
    """履歴ダイアログを開く（メニューの入口）。"""

def load_history(self) -> tuple[dict[str, Any], str]:
    """(履歴, contracts.HISTORY_*) を返す。分類は名前順へ整列して返す。"""

def entry_exists(self, stored_path: str) -> bool:
    """保存表記のパスを resolve_config_path で解決して実在を確かめる。"""

def open_keymap_set(self, stored_path: str) -> bool:
    """未保存確認 → パス指定の読込。読込が成功したときだけ True。"""

def add_category(self, name: str) -> tuple[bool, str]
def rename_category(self, old_name: str, new_name: str) -> tuple[bool, str]
def remove_category(self, name: str) -> tuple[bool, str]
def copy_to_category(self, name: str, stored_path: str) -> tuple[bool, str]
def remove_recent(self, index: int) -> tuple[bool, str]
def remove_category_entry(self, name: str, index: int) -> tuple[bool, str]
```

- `load_history`: 分類の並びは task_01 の `sorted_categories` を**ここで**適用して返す
  （ダイアログ側で整列しない）。`recent` は保存順のまま。
- `open_keymap_set`: `self._app.keymap_set_io.confirm_save_if_dirty("読込")` が False なら
  **読込を呼ばず False**（暫定仕様 §6。確認は二重化しない）。True なら
  `keymap_set_io.load_keymap_set_path(resolve_config_path で解決したパス)` を呼び、
  `KEYMAP_SET_LOAD_OK` のときだけ True を返す。**成否の通知は既存経路が出すので追加しない**。
- 編集 6 メソッド: 読み直した `status` が `contracts.HISTORY_READ_ONLY` なら
  **保存を試みず `(False, 理由)`**。domain 関数が `None`（空名・同名・不存在・重複）を返したら
  `(False, 理由)`。`copy_to_category` の重複は暫定仕様 §6 のとおり
  **「何もしない（メッセージのみ）」**＝保存しない。
- `ConfigService` の公開メソッドだけを使う（`resolve_config_path` /
  `load_keymap_set_history` / `save_keymap_set_history`）。
  **`config_service` の内部モジュールを import しない**（`tests/test_config_service_contracts.py` が赤になる）。
- 例外は `record()` と同様に境界で `(False, 理由)` へ変換する（ダイアログへ例外を出さない）。

### keyseq/presentation/dialogs/keymap_set_history_dialog.py（新規）

`KeymapSetHistoryDialog(tk.Toplevel)`。骨格は `dialogs/orphan_sweep_dialog.py` に合わせる
（`suspend_hook_for_dialog(self)` を 1 回・Escape / `WM_DELETE_WINDOW` → `destroy` /
**`__init__` の最後の文が `grab_modal(self, parent)`**）。`resume_hook_after_dialog` は呼ばない。
`destroy` の override は**持たせない**。

- 生成引数 = `(parent: App, *, controller)`。**履歴の読み書きは controller 経由のみ**。
  domain / application を直接 import しない（表示整形は `keymap_set_history_text` を使う）。
- ウィジェット:
  - 読み取り専用のときだけ `READ_ONLY_NOTICE` のラベルを一覧の上に出す。
  - `ttk.Treeview`（`columns=("path",)` / `show="tree headings"` / 見出し = 名前・パス）+ 縦スクロールバー。
  - 「分類名」`ttk.Entry` + 「＋分類を追加」「分類名を変更」「分類を削除」。
  - 「読み込む」「履歴から削除」「分類へコピー…」「閉じる」。
  - ダブルクリック（`<Double-1>`）は「読み込む」と同じ動作。
- ツリーの構成（暫定仕様 §5.2）: ルート直下に `RECENT_NODE_LABEL` の固定ノードと、
  controller が返した順（= 名前順）の分類ノードを並べる。子ノード = エントリ（名前列 / パス列）。
  既定で直近は展開・分類は折り畳み。
- ノードの同定は `iid → (kind, category_name, index, stored_path)` の dict で持つ
  （`kind` = `"recent_root"` / `"recent_entry"` / `"category"` / `"category_entry"`）。
  **パス文字列から逆引きしない**（同一パスが複数ノードに出るため。暫定仕様 §6）。
- 再描画 `_redraw()`: **controller から履歴を読み直して**ツリーを作り直す。
  選択と展開状態は可能な範囲で復元する。**読込・編集のたびに呼ぶ**（暫定仕様 §6）。
- ボタンの有効 / 無効を選択種別で切り替える（`<<TreeviewSelect>>` と再描画で更新）:
  読み込む・履歴から削除 = エントリ選択時 / 分類へコピー… = **直近配下のエントリ**選択時 /
  分類名を変更・分類を削除 = 分類選択時 / ＋分類を追加 = 常時。
  **読み取り専用のときは「読み込む」「閉じる」以外を無効**（暫定仕様 §5.3）。
- 「読み込む」: `controller.open_keymap_set(path)` が True のときだけ `destroy()`。
  False なら**開いたまま `_redraw()`**（暫定仕様 §6 / 受け入れ #19 #20）。
- 編集操作: 削除系は `messagebox.askyesno` で確認 → controller 呼び出し →
  成功なら `_redraw()` / 失敗なら理由を `messagebox` で出し、
  **一覧は変更しない**（暫定仕様 §4.3）。
- フォント追従（暫定仕様 §5.2）: `ttk.Style(self)` へ
  `style.configure("Treeview", font=TkDefaultFont, rowheight=<TkDefaultFont の linespace + 余白>)`
  と `style.configure("Treeview.Heading", font=TkDefaultFont)` を設定する。
  **名前付きフォント（`tkfont.nametofont("TkDefaultFont")`）を渡す**こと
  （`ui_font_delta_pt` は `theme.apply_global_theme` が既にこのフォントへ反映済みで、
  以後の変更にも追従する）。`theme.py` は変更しない。

#### 分類選択ダイアログ（同一ファイル内の 2 番目の小さいクラス）

「分類へコピー…」のコピー先選択に使う。`CategoryChooserDialog(tk.Toplevel)` を
**同じファイル**へ置く（手本 = `dialogs/preset_dialog.py`。`PresetManagerDialog` と同じネスト関係）。
Listbox + OK / キャンセルのみ。`result: str = ""`（キャンセルは空）。

- **`suspend_hook_for_dialog` を呼ばない**（親が停止中。静的検査の「1 ファイル 1 回」を保つ）。
- `__init__` の最後で `grab_modal(self, parent)`（破棄で grab が親ダイアログへ戻る）。
- 分類が 0 件のときは**開かず**、`keymap_set_history_text` の文言で通知する。

### keyseq/presentation/dialogs/__init__.py（1 行）

`from .keymap_set_history_dialog import KeymapSetHistoryDialog` を末尾へ追加
（`CategoryChooserDialog` は再輸出しない）。

### keyseq/presentation/views/menu_bar.py（1 行）

`file_menu.add_command(label="履歴から読み込む…", command=app.keymap_set_history_io.open_history_dialog)`
を「読込（構成セット）…」（`:12`）の**直後**へ入れる。アクセラレータは付けない。他は触らない。

### 既存テストの更新（列挙の追随）

- `tests_ui/test_dialog_teardown_flows.py:16-26` の `DIALOG_FILES` へ
  `"keymap_set_history_dialog.py"` を追加（アルファベット順の位置）。
  `T2_DIALOG_FILES` は**追加しない**（`destroy` override を持たせないため）。
  同ファイル `:250` / `:264` の docstring の「指定8ファイル」を実数へ更新する。
- `tests_ui/test_nested_modal_grab.py:262-272` の `dialog_classes` へ
  `"keymap_set_history_dialog.py": "KeymapSetHistoryDialog"` を追加する。

### tests_ui/test_keymap_set_history_flow.py（新規）

手本 = `tests_ui/test_quarantine_manage_flow.py`（`setUpClass` で `App()` を 1 つ・
`_patch` ヘルパ・ラベル走査でメニューを叩く形）。**実 `config/` へ書かないよう
`config_service.load_keymap_set_history` / `save_keymap_set_history` を patch する**
（または `config_root` を一時ディレクトリへ差し替える）。確認項目は「確認」節のとおり。

## 設計メモ / 制約

- **ダイアログは自分の表示内容を正としない**（暫定仕様 §6）。編集・読込のあとは必ず
  controller 経由で読み直す。ダイアログ側に履歴 dict を書き換えるロジックを置かない。
- **分類名の入力はインライン Entry**（「＋分類を追加」「分類名を変更」にラベルの「…」が無い＝
  別ウィンドウを開かない、という暫定仕様 §5.3 の表記に合わせる）。
  `simpledialog.askstring` は**使わない**（`grab_modal` を経由しないため、閉じたあと親ダイアログへ
  grab が戻らない）。「分類へコピー…」だけが別ウィンドウ（`CategoryChooserDialog`）。
- 削除は履歴からの除去のみ。**実ファイルには一切触らない**（`os.remove` 等を書かない）。
- 不在判定は**再描画のたびに**行う（開いている間に再チェックはしない。暫定仕様 §6）。
- 新規ファイルは 300 行以内・関数 30 行以内を目安にする（`.claude/rules/implementation.md`）。
- **`record()` を呼ばない**。履歴ダイアログからの読込は `load_keymap_set_path` の内部で
  既に記録される（task_03 の 3 経路）。ダイアログ側で二重に記録しない。

## 読むファイル

1. `instructions/history/21_keymap_set_load_history.md` の **§3 / §4.2〜§4.4 / §5 / §6 / §7 / §8**
   （データモデル・永続化の規則・UI 規定・受け入れ条件）
2. `keyseq/domain/keymap_set_history.py`（全体・165 行。公開関数の戻り値と `None` の意味）
3. `keyseq/application/config_service/keymap_set_history.py`（全体・82 行。`load_history` の
   status と `save_history` の戻り）+ `keyseq/application/config_service/contracts.py:130-132`
4. `keyseq/presentation/controllers/config_io/keymap_set_history_io.py`（全体・20 行。編集対象）
5. `keyseq/presentation/controllers/config_io/keymap_set_io.py:34-49`（`confirm_save_if_dirty`）・
   `:540-572`（`load_keymap_set_path` と `KEYMAP_SET_LOAD_*`）
6. `keyseq/presentation/dialogs/orphan_sweep_dialog.py`（全体・68 行。ダイアログ骨格の手本）/
   `keyseq/presentation/dialogs/preset_dialog.py`（全体・52 行。ネストした子ダイアログの手本）
7. `keyseq/presentation/quarantine_manage_text.py:1-30`（text モジュールの書き方）/
   `keyseq/presentation/controllers/config_io/quarantine_manage_io.py:1-40`（io の書き方）
8. `keyseq/presentation/theme.py:91-115`（`apply_global_theme` の `ttk.Style` 適用範囲。**変更しない**）
9. `keyseq/presentation/views/menu_bar.py:7-22`（追加位置）
10. `keyseq/presentation/modal.py:65-90`（`grab_modal` の前提）
11. テスト: `tests_ui/test_quarantine_manage_flow.py:1-50,118-140`（手本）/
    `tests_ui/test_dialog_teardown_flows.py:16-33,248-285`（列挙と静的検査）/
    `tests_ui/test_nested_modal_grab.py:259-300`（`dialog_classes` と静的検査）

## 含まない

- **正本反映**（`data_schema.md` §5.12 新設 / `features.md` §4.6 / `codebase_map.md` /
  暫定仕様 21 の凍結 / `decisions_archive/27` / `current.md` / `/refactor_check`）= **task_05**。
- `record()` の変更・記録契機の追加や削除（task_03 で確定済み）。
- `keymap_set_io.py` / `startup_io.py` / `theme.py` / `domain` / `application` の変更。
- 暫定仕様 §10 のスコープ外（分類の入れ子・D&D・分類 → 分類のコピー・任意ラベル・読込日時・
  検索・一括操作・`*.broken*.json` の管理 UI・`last_used_directory` の復活・構成セット以外の履歴）。
- 実機目視（本タスクの完了後に**ユーザーへ依頼**する）。

## 確認

`verifier` へ委任して `.venv` で実測する（Codex は python を実行できない）。

```
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests -v
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui -v
../../../.venv/Scripts/python.exe -m tests.smoke_app
```

- 静的: compileall clean。`tests` = **556 ran OK（skipped 7）で不変**。
- `tests_ui` = **471 + 新規テスト件数**で OK（既存の減少・失敗が無いこと）。
- smoke = `SMOKE OK`。
- **副作用ゼロ**: 上記 4 コマンドの実行後に `keymap_set_history.json` /
  `keymap_set_history.broken*.json` が **worktree ルート**と **`config/` 直下**の双方へ
  生成されていないこと（`config/config.json` の mtime も不変）。

新規テスト（`tests_ui/test_keymap_set_history_flow.py`）で確認する項目:

1. ファイルメニューのラベル列で「履歴から読み込む…」が「読込（構成セット）…」の**直後**にあり、
   invoke で `open_history_dialog` が 1 回呼ばれる（受け入れ #1）。
2. ツリー構成: 直近の固定ノード + 分類が**名前順**（`casefold`・同値は保存順）。
   エントリの名前列 = 拡張子なしファイル名 / パス列 = 保存表記。既定で直近は展開・分類は折り畳み。
3. 不在ファイルのエントリに `MISSING_SUFFIX` が付き、**自動削除されない**（受け入れ #18）。
4. 読み込む: ①成功 → `destroy` される ②読込失敗 → 開いたまま・再描画が走り当該エントリが残る
   ③未保存確認でキャンセル → `load_keymap_set_path` が呼ばれず開いたまま（受け入れ #19）。
5. 未保存確認の中で履歴が更新された場合、再描画後のツリーが**読み直した内容**に一致する（受け入れ #20）。
6. 履歴から削除: 同一パスが直近と分類の両方にある状態で、**選択した側だけ**が消える（受け入れ #16）。
   実ファイル削除の API（`os.remove` 等）が呼ばれない（受け入れ #17）。
7. 永続化失敗（`save_keymap_set_history` が `(False, 理由)`）で**一覧が変わらず**理由が表示される
   （分類追加・分類削除・コピー・エントリ削除の 4 操作。受け入れ #12）。
8. 分類の追加・リネーム・削除（配下ごと）ができ、**空名・同名が拒否**される（受け入れ #13 #14）。
9. 分類へコピー: 直近のエントリをコピーでき**直近側は残る**。同一分類内に重複を作らない
   （2 回目は保存が呼ばれずメッセージのみ）。分類 0 件ではチューザを開かず通知のみ（受け入れ #15）。
10. ボタンの有効 / 無効が選択種別（未選択 / 直近ルート / 直近エントリ / 分類エントリ / 分類）で切り替わる。
11. `HISTORY_READ_ONLY` のとき `READ_ONLY_NOTICE` が表示され、**読み込む・閉じる以外が無効**
    （受け入れ #11 の UI 側）。
12. ダイアログ作法（受け入れ #23）: Escape / `WM_DELETE_WINDOW` / 読込成功のいずれで閉じても
    `hook.get_hook_pause_count()` が開く前の値へ戻り、grab が親（App）へ戻る。
    `CategoryChooserDialog` を閉じたあと grab が**履歴ダイアログへ**戻る。
13. `ttk.Style` に `Treeview` / `Treeview.Heading` のフォントが `TkDefaultFont` で設定され、
    `rowheight` が 0 より大きい値で設定される。

## 完了条件

- 上記「確認」が pass（compileall clean / `tests` 556 不変 / `tests_ui` 増分のみ / smoke OK /
  副作用ゼロ）。
- **`reviewer` のレビューで採用**（`.claude/rules/review.md` の 5 観点 + phase.md「レビュー方針」の
  本フェーズ固有観点のうち、永続化の成否と UI の確定順序 / 再描画が永続化済みの内容を見ているか /
  依存方向〔ダイアログ → controller → application〕/ テストがリポジトリルートを汚していないか）。
- 実機目視は**本タスクの完了報告後にユーザーへ依頼**する（UI が出るのは本タスクから）。
  目視の観点: メニュー項目の位置 / 折り畳みと名前順 / フォントサイズ ±3 での行の見え方 /
  読み込む・削除・コピー・分類編集の一巡。
