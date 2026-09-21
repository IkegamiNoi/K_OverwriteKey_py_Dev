# task_03_history_record_wiring

## 目的

履歴の**記録を単一の口に閉じ**、暫定仕様 21 §4.1 の呼び出し点へ接続する。あわせて、履歴ダイアログ
（task_04）が使う**パス指定の共通読込入口**を追加する（現状 `load_keymap_set_from` は引数を取らず
成否も返さないため、パス指定で読む公開入口が無い。暫定仕様 §1-5 / §7）。

レイヤ制約: **presentation 限定**。`keyseq/domain/keymap_set_history.py`（task_01）と
`keyseq/application/config_service/keymap_set_history.py`（task_02）は**呼ぶだけで変更しない**。
JSON スキーマ不変。**既存の読込・保存の挙動とメッセージ文言を変えない**（記録の追加のみ）。

## 対象範囲（presentation 限定）

### keyseq/presentation/controllers/config_io/keymap_set_history_io.py（新規）

記録の**単一の口**。`orphan_sweep_io.py` / `quarantine_manage_io.py` と同じ形の薄いコントローラ。

```python
class KeymapSetHistoryIo:
    def __init__(self, app) -> None:
        self._app = app

    def record(self, path: str) -> tuple[bool, str]:
        """構成セットを開いた状態になったことを履歴へ記録する。"""
        return self._app.config_service.record_keymap_set_history(
            path, config_root=self._app.config_root,
        )
```

- **これ以外のロジックを持たせない**（判定・通知は呼び出し側）。
- ダイアログを開くメソッドは **task_04** で足す。ここでは作らない。
- **`record()` は例外を外へ出さないこと（必須）**。`config_service.record_keymap_set_history` の
  呼び出しを `try` で包み、例外は `(False, 理由)` へ変換する（理由に `str(exc)` を含める）。
  理由: **4 つの呼び出し点はいずれも既存の `try` ブロックの内側**にあり、例外が漏れると
  ①`startup_io.py` の `except Exception: pass` に吸われて**読込成功済みの構成セットを捨てて
  空データ起動**する ②`save_keymap_set_to` が成功した保存を「保存失敗」と表示する
  ③`load_keymap_set_path` が成功した読込を「読込失敗」と表示する。
  いずれも暫定仕様 §4.3「履歴の失敗で読込・保存を巻き戻さない」に反する。
  **単一の口＝境界でここだけ塞げば 4 経路すべてが守られる**。

### keyseq/presentation/app.py（既存・2 行）

- import を 1 行（`orphan_sweep_io` / `quarantine_manage_io` と同じ直接 import の形。
  `config_io/__init__.py` の `__all__` には**足さない**＝新しめのコントローラの慣例に合わせる）。
- `self.keymap_set_history_io = KeymapSetHistoryIo(self)` を `:159-169` のコントローラ生成群へ追加。
  他のコントローラと同じ位置（`:159-169`）で生成すれば足りる（v0.5 で起動時の記録が無くなったため、
  `load_startup_and_config` との順序制約は無い）。

### keyseq/presentation/controllers/config_io/keymap_set_io.py

**(1) パス指定の共通読込入口を追加**（モジュール定数 2 つ + メソッド 1 つ）

```python
KEYMAP_SET_LOAD_OK = "ok"
KEYMAP_SET_LOAD_FAILED = "failed"

def load_keymap_set_path(self, path: str) -> str:
    """パス指定で構成セットを読み込む。未保存確認は呼び出し側の責務。"""
```

- 本体は**現在の `load_keymap_set_from` の `try` ブロック（`:541-557`）をそのまま移す**。
  `data` の読込 → `keymap_set_path` 代入 → `apply_loaded_data_to_ui` → `_indices` / 選択の初期化 →
  `refresh_triggers` / `refresh_actions` → `dirty_tracker.set_dirty(False)` →
  **成功通知（flash「読み込みました。」+ `messagebox.showinfo`）**。**文言と順序を変えない**。
- 成功通知の**後**に `self._app.keymap_set_history_io.record(path)` を呼び、
  失敗なら `_set_flash_message(reason, auto_clear=False)`（§4.3）。戻り値は `KEYMAP_SET_LOAD_OK`。
- 例外時は現行どおり flash + `messagebox.showerror` を出し、`KEYMAP_SET_LOAD_FAILED` を返す。
  **失敗時は記録しない**。

**(2) `load_keymap_set_from` を共通入口へ委譲**（挙動不変）

```python
def load_keymap_set_from(self):
    if not self.confirm_save_if_dirty("読込"):
        return
    path = filedialog.askopenfilename(...)   # 既存のまま
    if not path:
        return
    self.load_keymap_set_path(path)
```

**(3) `set_startup_keymap_set`**: `self._app.keymap_set_path = path`（`:651`）の**直後**に
`self._app.keymap_set_history_io.record(path)` を呼ぶ。**通知は出さない**（設計メモ参照）。

**(4) `save_keymap_set_to`**: 保存成功の**完了メッセージを出した後**に
`self._app.keymap_set_history_io.record(self._app.keymap_set_path)` を呼ぶ
（`:132` で代入された**正規化後の実保存先**を渡す。ユーザー指定パスではない）。
失敗なら `_set_flash_message(reason, auto_clear=False)`。

### keyseq/presentation/controllers/config_io/startup_io.py（**v0.5 で記録しない方針へ変更**）

- **起動時の自動読込では記録しない**（暫定仕様 v0.5 §4.1）。
  既に入れてある `self._app.keymap_set_history_io.record(resolved_keymap_set_path)`（`:32`）を
  **削除し、このファイルを元の状態へ戻す**（`git diff` が空になること）。
- 理由: 起動時に記録すると**実アプリを起動するだけの `tests_ui` 9 モジュールが実 `config/` へ
  履歴ファイルを書く**（実測）。正本 §5.4 の遅延作成方針との衝突も経路ごと消える。
### tests_ui/test_config_io_characterization_keymap_set_startup.py / tests_ui/test_config_io_characterization.py（既存・patch 追加）

- 両ファイルの setUp は `config_root` 等へ **`os.getcwd()` を代入する**（前者 `:120-122` / 後者 `:181`）。
  記録が走ると**リポジトリルートへ `keymap_set_history.json` が生成される**ため、
  `patch.object(ConfigService, "record_keymap_set_history", return_value=(True, ""))` を
  setUp で開始し `addCleanup` で戻す（既存の patch の書き方に合わせる）。
- **他のテストでも履歴ファイルが生成されたら同じ patch を足す**（確認 7 で検出する）。

### tests/smoke_app.py（**v0.5 で不要になったため元へ戻す**）

- 起動時に記録しなくなるため、smoke への patch は**不要**。
  追加した `patch.object(...)` と関連 import を**取り除き、元の 17 行の状態へ戻す**
  （`git diff` が空になること）。
### tests_ui/test_keymap_set_history_record.py（新規）

`ConfigService.record_keymap_set_history` を patch して**呼び出しの有無と引数**を固定する。

- **記録される**: ①メニュー読込の成功 ②起動セット指定の成功 ③別名保存の成功
  ④上書き保存の成功 ⑤`load_keymap_set_path` の成功。
- **記録されない**: ⑥読込の失敗 ⑦**起動時の自動読込（成功・失敗を問わない。v0.5）**
  ⑧`new_config` ⑨`import_config` ⑩`restore_default` ⑪未保存確認のキャンセルで読込を中止した場合。
- **アプリを起動しただけでは履歴ファイルが作られない**こと（`App()` を作るだけのテストで
  `record_keymap_set_history` が呼ばれないことを固定する。v0.5 の要点）。
- **引数**: 保存時は**正規化後の実保存先**（`self._app.keymap_set_path` の値）が渡ること。
- **戻り値**: `load_keymap_set_path` が成功で `KEYMAP_SET_LOAD_OK`、失敗で `KEYMAP_SET_LOAD_FAILED`。
- **記録失敗時の通知**: `record_keymap_set_history` が `(False, "理由")` を返したとき、
  読込経路と保存経路で**ステータスバーに理由が出る**こと。
  `set_startup_keymap_set` の経路では**出ない**こと（起動時の経路は v0.5 で記録しない）。
- **記録の例外が漏れない**: `record_keymap_set_history` が**例外を送出**するようにした場合でも、
  ①保存が「保存失敗」と表示されない ②読込が「読込失敗」と表示されないこと
  （呼び出し点が既存の `try` の内側にあるため。起動時の経路は v0.5 で無くなった）。
  成功・失敗のメッセージが従来どおりであること。

### 設計メモ / 制約

- **通知を出す経路は 2 つだけ**（`load_keymap_set_path` と `save_keymap_set_to`）。
  理由: `set_startup_keymap_set` は起動設定の保存失敗時に自前の flash を出して return するため
  （`keymap_set_io.py:661-663`）、§4.3「既存経路の通知を上書きしない」に当たる。
  起動時の経路は v0.5 で記録しなくなったため、通知の検討対象外。**この方針はタスク定義の確定事項**として扱う。
- **記録は成功通知の後**に行う（先に呼ぶと、記録失敗の flash を成功メッセージが上書きしてしまう）。
- **`load_keymap_set_path` は未保存確認をしない**。確認は呼び出し側（`load_keymap_set_from` と
  task_04 の履歴ダイアログ）が行う。§6「確認を二重化しない」に対応する。
- 記録の呼び出しは**必ず `keymap_set_history_io.record()` 経由**にする。
  `config_service.record_keymap_set_history` を各所から直接呼ばない（テストで 1 箇所を
  patch できる形を保つため。暫定仕様 §4.1）。
- **`app.py:76` の初期代入では記録しない**（暫定仕様 §4.1 の除外。触らないこと）。
- 既存メソッドの**メッセージ文言・引数・戻り値を変えない**（`load_keymap_set_from` は
  従来どおり戻り値なしでよい）。

## 読むファイル

- `instructions/history/21_keymap_set_load_history.md` の **§4.1 / §4.3 / §6 / §7**（根拠）
- `keyseq/presentation/controllers/config_io/keymap_set_io.py:32-47`（未保存確認）/
  `:101-146`（`save_keymap_set_to`）/ `:529-557`（`load_keymap_set_from`）/ `:626-665`（`set_startup_keymap_set`）
- `keyseq/presentation/controllers/config_io/startup_io.py`（全体・75 行）
- `keyseq/presentation/controllers/config_io/orphan_sweep_io.py:1-30`（薄いコントローラの書式の手本）
- `keyseq/presentation/app.py:150-200`（コントローラ生成と `load_startup_and_config` の呼び出し順）
- `keyseq/application/config_service/keymap_set_history.py`（task_02・81 行。`record` の戻り値の確認）
- `tests_ui/test_config_io_characterization_keymap_set_startup.py:110-130`（setUp と patch の書き方）
- `tests_ui/test_quarantine_manage_flow.py:1-60`（tests_ui の書式の手本）

## 含まない

- **履歴ダイアログ・`ttk.Treeview`・メニュー項目「履歴から読み込む…」・整形関数** = **task_04**
- **`DIALOG_FILES` / `T2_DIALOG_FILES` の更新** = **task_04**（本タスクはダイアログを作らない）
- **正本 `spec_detail/` の改訂・`codebase_map.md` の追記・暫定仕様の凍結** = **task_05**
- `keyseq/domain/keymap_set_history.py` / `keyseq/application/config_service/keymap_set_history.py`
  の変更（task_01 / task_02 で確定済み。**不足を見つけたら実装せず報告する**）
- `app.py:76` の初期代入や `resolve_keymap_set_path()` の引数なし分岐の整理（別件・`current.md` の候補）
- 読込・保存のメッセージ文言の改善、未保存確認の仕様変更

## 確認

1. 静的確認: `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests tests_ui` が clean。
2. 新規テスト: `..\..\..\.venv\Scripts\python.exe -m unittest tests_ui.test_keymap_set_history_record -v`
   が**全 pass**（上記「tests_ui/test_keymap_set_history_record.py」の項目をすべて含むこと）。
3. 退行なし: `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` が
   **556 pass 以上**（task_02 完了時点 556・skip 7）。
4. `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` が
   **449 + 新規件数** で pass（基準 449）。**fail は単独実行で再現するか必ず確かめる**（既知フレークあり）。
5. `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` が `SMOKE OK`。
6. **副作用（最重要）**: 上記をすべて実行した後、**worktree ルートと `config/` 直下に
   `keymap_set_history.json` / `keymap_set_history.broken*.json` が生成されていないこと**。
   `config/config.json` の mtime が不変であること。`user/` / `quarantine/` が増えていないこと。
7. **挙動不変の確認**: `git diff` で `load_keymap_set_from` の「未保存確認 → ファイル選択 → 読込」
   という流れとメッセージ文言が変わっていないこと（移設のみで、文言の追加・削除が無いこと）。
8. `config_service.record_keymap_set_history` の直接呼び出しが
   **`keymap_set_history_io.py` の 1 箇所のみ**であること（`grep` で確認）。

※ テストの実行は `verifier` が行う（Codex は python を起動できない）。

## 完了条件

- 上記確認 1〜8 が pass・**reviewer 採用**（観点: 暫定仕様 §4.1 の呼び出し点と除外経路の一致・
  記録が単一の口に閉じていること・**既存の読込/保存の挙動とメッセージが変わっていないこと**・
  通知方針が設計メモどおりであること・依存方向・後続タスクの先取りが無いこと）。
- 実機目視: **不要**（UI の追加は task_04。目視は task_04 でまとめて実施する）。
