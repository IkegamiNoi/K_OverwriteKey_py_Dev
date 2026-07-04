# リファクタリング計画書 01（挙動不変・段階実行）

- 作成日: 2026-07-04
- 基準コミット: `0a8bb6a`（本書の行番号はすべてこのコミット時点のもの。実行時に行番号がずれている場合は**メソッド名・クラス名を正として**特定すること）
- 実行環境の前提: Windows 11 / PowerShell / Python は `py` ランチャで起動する（`py --version` → Python 3.14.x。素の `python` コマンドはストアのスタブである可能性があるため使わない）
- 本計画の性質: **機能追加・仕様変更は一切行わない。** 目的はデッドコード削除・重複排除・直値の定数化・小規模なエラー処理改善のみ。
- 併読必須: `AGENTS.md` と `instruction/common/` 配下（特に `architecture_rules.md` / `dev_rules.md` / `json_spec.md`）。本計画は以下の既存ルールに従う:
  - JSON の既存キー削除・意味変更の禁止（後方互換維持）
  - フック仕様（suppress / 停止制御 / ダイアログ中のネスト停止）を壊さない
  - UI 更新は UI スレッド（`after`）で行う構造を維持する

---

## 1. 現状理解（実行者への文脈共有）

### 1.1 何をするアプリか

Python + tkinter + keyboard によるキーボード入力置換シーケンサー。単キー（例: F1）をトリガーとして、ホットキー送信 / テキスト入力 / マウスクリックのシーケンスを実行する。キーマップ（キー→キーの置換）、構成セット（分離 JSON 群）の保存/読込を持つ。エントリポイントは `main.py` → `keyseq.presentation.app.App`。

### 1.2 構造マップ（ファイル・役割・依存）

オニオンアーキテクチャ。依存方向は presentation → application → domain、infrastructure は外部ライブラリの薄いラッパ。

| ファイル | 行数 | 役割 | 依存先 |
|---|---|---|---|
| `main.py` | 11 | App を起動するだけ | presentation.app |
| `keyseq/domain/config.py` | 269 | `DEFAULT_CONFIG`、`ensure_config_compatibility()`（設定 dict の正規化・後方互換変換）、一覧表示文字列の整形関数 | なし（stdlib のみ） |
| `keyseq/domain/key_identifiers.py` | 35 | JIS 特殊キー（無変換/変換/かな/半角全角）のスキャンコード対応表 | domain.config |
| `keyseq/infrastructure/input_gateway.py` | 63 | `keyboard` / `pyautogui` のラッパ（フック登録、キー送信、クリック） | domain.key_identifiers |
| `keyseq/infrastructure/json_repository.py` | 19 | JSON ファイルの読み書き | stdlib |
| `keyseq/application/config_service.py` | 1058 | 分離 JSON（keymap_set / trigger_set / sequence / keymaps / hotkey_presets / startup）の保存・読込、パスの相対/絶対変換、ファイル名スラグ化 | domain.config, infrastructure.json_repository |
| `keyseq/application/trigger_service.py` | 46 | トリガー検索・キー重複判定（全て staticmethod） | domain.config |
| `keyseq/application/keymap_service.py` | 310 | キーマップの CRUD・切替キー管理・マッピング解決（全て staticmethod） | domain.config |
| `keyseq/application/key_state_manager.py` | 112 | 押下中キー集合の管理（修飾キー別名の正規化含む） | domain.config |
| `keyseq/application/input_router.py` | 132 | フックイベント → ルーティング判定（停止キー/トグル/キーマップ切替/トリガー/キーマップ置換）。結果は `InputRoute`（実行アクション列 + accept 可否） | domain.config |
| `keyseq/application/action_executor.py` | 136 | アクション実行（hotkey/text/mouse_click）と、送信中の自己イベント抑止用 send guard カウンタ | infrastructure, input_router |
| `keyseq/application/sequence_runner.py` | 262 | トリガー押下ごとの 1 アクション実行（循環 index）と、連続実行（run_to_end。`after` で 1 アクションずつ進める） | domain.config |
| `keyseq/application/hook_coordinator.py` | 93 | グローバルフック（suppress=True）の登録・解除 | （input_gateway をコンストラクタ注入） |
| `keyseq/application/app_state.py` | 38 | 実行時状態（選択 index、循環 index dict、run_to_end 状態、chain 状態、ロック） | stdlib |
| `keyseq/presentation/app.py` | **3346** | `App(tk.Tk)`。UI 構築・メニュー・全イベントハンドラ・保存/読込フロー・フック開始/停止・キーキャプチャ、をすべて持つ God class | ほぼ全モジュール |
| `keyseq/presentation/views.py` | 645 | `FullView` / `CompactView`（ウィジェット構築のみ。ハンドラは App のメソッドを参照） | dialogs |
| `keyseq/presentation/dialogs.py` | 868 | `ActionDialog` / `PresetManagerDialog` / `PresetDialog` / `TriggerDialog` / `KeymapEditDialog` / `LayoutDeleteDialog` | domain.config |
| `keyseq/presentation/keyboard_window.py` | 391 | キーボード UI（Canvas 描画、クリックでキーマップ編集） | application.keymap_service, keyboard_layouts |
| `keyseq/presentation/keyboard_layouts.py` | 364 | キーボードレイアウト定義（内蔵 US TKL + 外部 JSON 読込・検証） | domain.key_identifiers |
| `keyseq/presentation/theme.py` | 102 | フォントサイズデルタの一括適用 | stdlib |

### 1.3 実行時の主要フロー

1. **起動**: `App.__init__` → `config/config.json`（startup）を読み、`keymap_set_path` があれば分離 JSON 構成を `ConfigService.load_runtime_data_from_keymap_set_path()` で読み込む。無ければ空データで起動。
2. **フック ON**: `start_hook()` → `HookCoordinator.start()` が `keyboard.hook(callback, suppress=True)` を登録。以後すべてのキーイベントが `App._on_input_event` → `InputRouter.handle()` に入る。ルーティング結果のアクションは `self.after(0, ...)` で UI スレッドに移してから `ActionExecutor.execute_router_action()` で実行。戻り値 `route.accept` が False のときそのキー入力は OS に流れない（suppress）。
3. **自己イベント抑止**: `ActionExecutor` がキー送信中は send guard カウンタを立て、`InputRouter` は guard > 0 のときイベントを素通しする（送信したキーで再トリガーしない仕組み。**壊すと無限ループになるため最重要**）。
4. **ダイアログ中の安全化**: 編集ダイアログは開くときに `App.suspend_hook_for_dialog()`（カウンタ式・ネスト対応）、閉じるときに `resume_hook_after_dialog()`。最後のダイアログが閉じたときだけフックが復帰する。
5. **保存**: `save_keymap_set()` / `save_as()` → `ConfigService.save_runtime_data()` が startup / keymap_set / trigger_set / hotkey_presets / keymaps/*.json / sequences/*.json に分割保存。config ルート配下は相対パス（`/` 区切り）、外は絶対パスで格納する。

### 1.4 重要な不変条件（変更してはいけない挙動）

- トリガー dict / keymap dict に付くランタイム内部キー `_sequence_source_path` / `_sequence_imported` / `_sequence_dirty` / `_keymap_source_path` / `_keymap_imported` / `_keymap_dirty` は、`ensure_config_compatibility()` を通しても保持され、ファイル保存時（`_sanitize_runtime_for_storage`）にのみ除去される。
- `run_to_end_delay_ms` の不正値は 300 に、負値は 0 に矯正される。
- キーマップ切替キーは「1 キーマップにつき最大 1 個」。
- 保存 JSON の構造（キー名・階層・パス表現）は 1 バイトも変えない。

### 1.5 洗い出した問題（本計画で扱うもの）

| # | 問題 | 場所 | 種別 |
|---|---|---|---|
| P1 | `ActionDialog` クラスがまるごと二重定義されている（片方は未使用のデッドコード。文字化けコメントとボタン文言 typo 入り） | `views.py:298-645` | 重複/デッドコード |
| P2 | 「キーマップ切替キー専用リスト UI」のハンドラ群が残っているが、対応するウィジェット（`keymap_switch_key_listbox` 等）はどの View も生成しておらず、入口メソッドはどこからも呼ばれない | `app.py:912-1128, 1170-1239` の一部 | デッドコード |
| P3 | `ConfigService` に呼び出し元ゼロのメソッドが 5 個、`App`・`AppState`・`keyboard_layouts` にも未使用メンバ | 複数 | デッドコード |
| P4 | `App` の「State compatibility aliases」プロパティ 13 個中 11 個が未使用 | `app.py:168-238` | デッドコード |
| P5 | chain 実行系（`chain_start_or_toggle` ほか）が UI から一切到達不能（停止側の防御呼び出しのみ残存） | `sequence_runner.py:164-262`, `app_state.py`, `app.py` | デッドコード |
| P6 | `normalize_key_name` が domain 定義と同内容で `app.py` と `keyboard_window.py` に再定義されている | `app.py:47`, `keyboard_window.py:37` | 重複 |
| P7 | Tk keysym → keyboard 表記の変換マップ（13 エントリ）が 5 箇所にコピペされている | `app.py`, `dialogs.py`×3, `keyboard_window.py` | 重複 |
| P8 | `save_keymap_set()` と `save_as()` の本体が丸ごと重複 | `app.py:2437-2497` | 重複/巨大化 |
| P9 | `new_config()` / `restore_default()` / `_apply_loaded_data_to_ui()` で UI 変数同期処理が三重に重複 | `app.py` | 重複 |
| P10 | `_refresh_keymap_switch_ui()` は `_refresh_keymap_list_ui()` の単なる別名で、ほぼ全呼び出し箇所で直前に本体も呼ばれており同一リストを二度再描画している | `app.py:923-924` ほか | 重複/無駄 |
| P11 | run_to_end のデフォルト 300ms と「非負 int 矯正」ロジックが 4 ファイルに散在 | domain/config_service/sequence_runner/app | 直値散在 |
| P12 | デフォルトレイアウト ID `"us_tkl"` の文字列リテラルが domain と config_service に散在（presentation には定数あり） | 複数 | 直値散在 |
| P13 | `App` が `ConfigService` の私有メソッド `_slugify_file_stem` / `_to_config_relative_or_absolute` を直接呼んでいる | `app.py:1695, 2066, 2071` | 責務/命名 |
| P14 | JSON 保存が非アトミック（書き込み中クラッシュで設定ファイルが壊れる） | `json_repository.py:13-18` | エラー処理の穴 |
| P15 | 起動時の構成セット読込失敗が `except Exception: pass` で完全に無音（ユーザーは空データになった理由が分からない） | `app.py:1772-1773` | エラー処理の穴 |
| P16 | 文字化けコメント `# ��\��` が生きているコードに残存 | `dialogs.py:313` | 表記 |

テストが存在しないため、着手前に特性テスト（項目 0）で現挙動を固定する。

---

## 2. 項目 0: 安全網の構築（最初に必ず実行）

### 0-a. 作業前コミットとブランチ

```powershell
# 1) 作業ツリーがクリーンであることを確認（クリーンでなければ中断して報告）
git status

# 2) ベースラインのコミットIDを記録（報告書に残す）
git rev-parse HEAD

# 3) 作業ブランチを切る
git switch -c refactor/01-cleanup
```

### 0-b. ベースライン確認（テスト追加前に一度実行して成功を確認）

```powershell
py -m compileall -q keyseq main.py     # 終了コード 0 であること
py -c "import keyseq.presentation.app" # 例外なく終了すること
```

### 0-c. 特性テストの追加

`tests/` ディレクトリを新規作成し、以下の 8 ファイルを**この内容のまま**作成する（unittest のみ使用。**pytest 等の新規依存を追加してはならない**）。これらは現挙動の固定であり、以降の全項目の完了条件で使う。

GUI・`keyboard`・`pyautogui`・`pynput` を import しないモジュールだけを対象にしているため、テストはヘッドレスで安全に動く。

#### `tests/test_domain_config.py`

```python
import unittest

from keyseq.domain.config import (
    DEFAULT_CONFIG,
    ensure_config_compatibility,
    format_action_list_item,
    format_preset_list_item,
    format_trigger_list_item,
    normalize_key_name,
)


class NormalizeKeyNameTest(unittest.TestCase):
    def test_strip_and_lower(self):
        self.assertEqual(normalize_key_name("  F1 "), "f1")

    def test_none_returns_empty(self):
        self.assertEqual(normalize_key_name(None), "")


class EnsureConfigCompatibilityTest(unittest.TestCase):
    def test_empty_input_returns_defaults(self):
        config = ensure_config_compatibility({})
        self.assertEqual(config["triggers"], [])
        self.assertEqual(config["hotkey_presets"], DEFAULT_CONFIG["hotkey_presets"])
        self.assertEqual(config["hook_stop_key"], "")
        self.assertEqual(config["hook_toggle_key"], "")
        self.assertEqual(config["keyboard_layout"], "us_tkl")
        self.assertEqual(config["external_keyboard_layouts"], [])
        self.assertEqual(config["keymaps"], [])
        self.assertEqual(config["active_keymap_id"], "")
        self.assertEqual(config["keymap_switch_keys"], {})

    def test_non_dict_input_treated_as_empty(self):
        config = ensure_config_compatibility(None)
        self.assertEqual(config["triggers"], [])

    def test_legacy_single_trigger_converted(self):
        legacy = {
            "trigger_key": "F1",
            "actions": [{"type": "text", "value": "a"}],
        }
        config = ensure_config_compatibility(legacy)
        self.assertEqual(len(config["triggers"]), 1)
        trigger = config["triggers"][0]
        self.assertEqual(trigger["key"], "f1")
        self.assertTrue(trigger["suppress"])
        self.assertFalse(trigger["run_to_end"])
        self.assertEqual(trigger["run_to_end_delay_ms"], 300)
        self.assertEqual(trigger["actions"], [{"type": "text", "value": "a", "label": ""}])

    def test_delay_coercion(self):
        def delay_of(value):
            config = ensure_config_compatibility(
                {"triggers": [{"key": "a", "run_to_end_delay_ms": value, "actions": []}]}
            )
            return config["triggers"][0]["run_to_end_delay_ms"]

        self.assertEqual(delay_of("abc"), 300)
        self.assertEqual(delay_of(-5), 0)
        self.assertEqual(delay_of("120"), 120)

    def test_trigger_internal_keys_preserved(self):
        config = ensure_config_compatibility(
            {"triggers": [{"key": "a", "actions": [], "_sequence_dirty": True}]}
        )
        self.assertTrue(config["triggers"][0]["_sequence_dirty"])

    def test_keymap_normalization(self):
        config = ensure_config_compatibility(
            {
                "keymaps": [
                    {"id": "KM1", "label": " main ", "mappings": {"A": "B", "": "x", "c": ""}},
                    {"id": "km1", "mappings": {}},
                    {"mappings": {}},
                    "not-a-dict",
                ],
                "active_keymap_id": "zzz",
                "keymap_switch_keys": {"1": "km1", "2": "km1", "3": "unknown"},
            }
        )
        self.assertEqual(len(config["keymaps"]), 1)
        keymap = config["keymaps"][0]
        self.assertEqual(keymap["id"], "km1")
        self.assertEqual(keymap["label"], "main")
        self.assertEqual(keymap["mappings"], {"a": "b"})
        self.assertEqual(config["active_keymap_id"], "km1")
        self.assertEqual(config["keymap_switch_keys"], {"1": "km1"})


class FormatListItemTest(unittest.TestCase):
    def test_trigger_with_label(self):
        self.assertEqual(format_trigger_list_item(0, {"key": "F1", "label": "copy"}), "01. f1: copy")

    def test_trigger_without_label(self):
        self.assertEqual(format_trigger_list_item(9, {"key": "f2"}), "10. f2")

    def test_action_hotkey(self):
        self.assertEqual(
            format_action_list_item(0, {"type": "hotkey", "value": "ctrl+c"}),
            "01. [hotkey] ctrl+c",
        )

    def test_action_mouse_click(self):
        action = {"type": "mouse_click", "x": 10, "y": 20, "button": "left", "clicks": 2}
        self.assertEqual(format_action_list_item(0, action), "01. [mouse_click] (10, 20) left x2")

    def test_action_with_label(self):
        self.assertEqual(
            format_action_list_item(1, {"type": "text", "value": "abc", "label": "memo"}),
            "02. [text] abc: memo",
        )

    def test_preset(self):
        self.assertEqual(
            format_preset_list_item(0, {"label": "Win+D", "value": "windows+d"}),
            "01. windows+d: Win+D",
        )


if __name__ == "__main__":
    unittest.main()
```

#### `tests/test_key_identifiers.py`

```python
import unittest

from keyseq.domain.key_identifiers import (
    is_special_key_name,
    resolve_known_key_name_from_scan_code,
    resolve_known_scan_code_from_key_name,
)


class KeyIdentifiersTest(unittest.TestCase):
    def test_known_key_to_scan_code(self):
        self.assertEqual(resolve_known_scan_code_from_key_name("MUHENKAN"), 123)
        self.assertIsNone(resolve_known_scan_code_from_key_name("a"))
        self.assertIsNone(resolve_known_scan_code_from_key_name(""))

    def test_scan_code_to_key(self):
        self.assertEqual(resolve_known_key_name_from_scan_code(121), "henkan")
        self.assertEqual(resolve_known_key_name_from_scan_code(999), "")
        self.assertEqual(resolve_known_key_name_from_scan_code("abc"), "")

    def test_is_special_key_name(self):
        self.assertTrue(is_special_key_name("kana"))
        self.assertFalse(is_special_key_name("f1"))


if __name__ == "__main__":
    unittest.main()
```

#### `tests/test_trigger_service.py`

```python
import unittest

from keyseq.application.trigger_service import TriggerService


class TriggerServiceTest(unittest.TestCase):
    def setUp(self):
        self.trigger = {"key": "f1", "actions": []}
        self.data = {
            "triggers": [self.trigger],
            "hook_stop_key": "f12",
            "hook_toggle_key": "f11",
        }

    def test_find_trigger_by_key_normalizes(self):
        self.assertIs(TriggerService.find_trigger_by_key(self.data, " F1 "), self.trigger)
        self.assertIsNone(TriggerService.find_trigger_by_key(self.data, "f2"))

    def test_key_exists_exclude_trigger(self):
        self.assertTrue(TriggerService.key_exists(self.data, "f1"))
        self.assertFalse(TriggerService.key_exists(self.data, "f1", exclude_trigger=self.trigger))

    def test_stop_and_toggle_conflict(self):
        self.assertTrue(TriggerService.is_stop_key_conflict(self.data, "F12"))
        self.assertFalse(TriggerService.is_stop_key_conflict(self.data, "f1"))
        self.assertTrue(TriggerService.is_toggle_key_conflict(self.data, "f11"))


if __name__ == "__main__":
    unittest.main()
```

#### `tests/test_keymap_service.py`

```python
import unittest

from keyseq.application.keymap_service import KeymapService


def make_data():
    return {
        "keymaps": [
            {"id": "km1", "label": "One", "mappings": {"a": "b"}},
            {"id": "km2", "label": "", "mappings": {}},
            {"id": "km3", "label": "Three", "mappings": {}},
        ],
        "active_keymap_id": "km2",
        "keymap_switch_keys": {"1": "km1", "2": "km2"},
    }


class KeymapServiceTest(unittest.TestCase):
    def test_create_keymap_on_empty(self):
        data = {}
        created = KeymapService.create_keymap(data)
        self.assertEqual(created["id"], "keymap_1")
        self.assertEqual(data["active_keymap_id"], "keymap_1")
        second = KeymapService.create_keymap(data)
        self.assertEqual(second["id"], "keymap_2")
        self.assertEqual(data["active_keymap_id"], "keymap_1")

    def test_delete_active_keymap_falls_back(self):
        data = make_data()
        deleted, next_active = KeymapService.delete_keymap(data, "km2")
        self.assertTrue(deleted)
        self.assertEqual(next_active, "km3")
        self.assertEqual(data["keymap_switch_keys"], {"1": "km1"})

    def test_delete_last_keymap_clears_active(self):
        data = {
            "keymaps": [{"id": "km1", "mappings": {}}],
            "active_keymap_id": "km1",
            "keymap_switch_keys": {},
        }
        deleted, next_active = KeymapService.delete_keymap(data, "km1")
        self.assertTrue(deleted)
        self.assertEqual(next_active, "")
        self.assertEqual(data["active_keymap_id"], "")

    def test_set_keymap_switch_key(self):
        data = make_data()
        self.assertTrue(KeymapService.set_keymap_switch_key(data, "3", "km3"))
        # km1 には既に "1" が割当済みなので、別キーの追加は拒否される
        self.assertFalse(KeymapService.set_keymap_switch_key(data, "9", "km1"))
        # 同じ割当のやり直しは「変化なし」= False
        self.assertFalse(KeymapService.set_keymap_switch_key(data, "1", "km1"))
        self.assertFalse(KeymapService.set_keymap_switch_key(data, "5", "nope"))

    def test_get_keymap_by_switch_key(self):
        data = make_data()
        self.assertEqual(KeymapService.get_keymap_by_switch_key(data, "1"), "km1")
        self.assertEqual(KeymapService.get_keymap_by_switch_key(data, "8"), "")

    def test_find_mapping_target_uses_active(self):
        data = make_data()
        data["active_keymap_id"] = "km1"
        self.assertEqual(KeymapService.find_mapping_target(data, "A"), "b")
        self.assertEqual(KeymapService.find_mapping_target(data, "z"), "")
        data["active_keymap_id"] = "km2"
        self.assertEqual(KeymapService.find_mapping_target(data, "a"), "")

    def test_ensure_active_keymap_creates_default(self):
        data = {}
        keymap = KeymapService.ensure_active_keymap(data)
        self.assertEqual(keymap["id"], "default")
        self.assertEqual(data["active_keymap_id"], "default")

    def test_set_and_clear_mapping(self):
        data = make_data()
        data["active_keymap_id"] = "km1"
        keymap_id, changed = KeymapService.set_mapping(data, "X", "Y")
        self.assertEqual(keymap_id, "km1")
        self.assertTrue(changed)
        self.assertEqual(data["keymaps"][0]["mappings"]["x"], "y")
        keymap_id, changed = KeymapService.clear_mapping(data, "x")
        self.assertTrue(changed)
        self.assertNotIn("x", data["keymaps"][0]["mappings"])


if __name__ == "__main__":
    unittest.main()
```

#### `tests/test_key_state_manager.py`

```python
import unittest
from types import SimpleNamespace

from keyseq.application.key_state_manager import KeyStateManager


class KeyStateManagerTest(unittest.TestCase):
    def test_modifier_alias(self):
        manager = KeyStateManager()
        manager.handle_event(SimpleNamespace(name="Left Shift", event_type="down", scan_code=None))
        self.assertTrue(manager.is_pressed("shift"))
        manager.handle_event(SimpleNamespace(name="left shift", event_type="up", scan_code=None))
        self.assertFalse(manager.is_pressed("shift"))

    def test_clear(self):
        manager = KeyStateManager()
        manager.key_down("a")
        manager.clear()
        self.assertEqual(manager.pressed_keys, frozenset())


if __name__ == "__main__":
    unittest.main()
```

#### `tests/test_input_router.py`

```python
import unittest
from types import SimpleNamespace

from keyseq.application.input_router import (
    InputRouter,
    SelectKeymapAction,
    SendKeyAction,
    StopHookAction,
    ToggleModeAction,
    TriggerAction,
)
from keyseq.application.key_state_manager import KeyStateManager


def make_router(
    *,
    send_guard=0,
    pause=0,
    stop_key="",
    toggle_key="",
    custom_enabled=True,
    switch_target="",
    trigger=None,
    keymap_target="",
):
    return InputRouter(
        key_state_manager=KeyStateManager(),
        get_send_guard_count=lambda: send_guard,
        get_hook_pause_count=lambda: pause,
        get_stop_key=lambda: stop_key,
        get_toggle_key=lambda: toggle_key,
        get_custom_input_enabled=lambda: custom_enabled,
        find_keymap_switch_target=lambda key: switch_target,
        find_trigger=lambda key: trigger,
        find_keymap_target=lambda key: keymap_target,
    )


def down(name):
    return SimpleNamespace(event_type="down", name=name, scan_code=None)


class InputRouterTest(unittest.TestCase):
    def test_send_guard_passes_through(self):
        route = make_router(send_guard=1, stop_key="f12").handle(down("f12"))
        self.assertEqual(route.actions, ())
        self.assertTrue(route.accept)

    def test_pause_passes_through(self):
        route = make_router(pause=1, stop_key="f12").handle(down("f12"))
        self.assertEqual(route.actions, ())
        self.assertTrue(route.accept)

    def test_up_event_ignored(self):
        router = make_router(stop_key="f12")
        route = router.handle(SimpleNamespace(event_type="up", name="f12", scan_code=None))
        self.assertEqual(route.actions, ())
        self.assertTrue(route.accept)

    def test_stop_key(self):
        route = make_router(stop_key="F12").handle(down("f12"))
        self.assertEqual(route.actions, (StopHookAction(),))
        self.assertFalse(route.accept)

    def test_toggle_key(self):
        route = make_router(toggle_key="f11").handle(down("f11"))
        self.assertEqual(route.actions, (ToggleModeAction(),))
        self.assertFalse(route.accept)

    def test_custom_input_disabled_passes_through(self):
        trigger = {"key": "f1", "suppress": True, "actions": [{"type": "text", "value": "x"}]}
        route = make_router(custom_enabled=False, trigger=trigger).handle(down("f1"))
        self.assertEqual(route.actions, ())
        self.assertTrue(route.accept)

    def test_keymap_switch_key(self):
        route = make_router(switch_target="km1").handle(down("1"))
        self.assertEqual(route.actions, (SelectKeymapAction(keymap_id="km1"),))
        self.assertFalse(route.accept)

    def test_trigger_suppress_true(self):
        trigger = {"key": "f1", "suppress": True, "actions": [{"type": "text", "value": "x"}]}
        route = make_router(trigger=trigger).handle(down("f1"))
        self.assertEqual(route.actions, (TriggerAction(key="f1"),))
        self.assertFalse(route.accept)

    def test_trigger_suppress_false(self):
        trigger = {"key": "f1", "suppress": False, "actions": [{"type": "text", "value": "x"}]}
        route = make_router(trigger=trigger).handle(down("f1"))
        self.assertEqual(route.actions, (TriggerAction(key="f1"),))
        self.assertTrue(route.accept)

    def test_trigger_without_actions_falls_through_to_keymap(self):
        trigger = {"key": "a", "suppress": True, "actions": []}
        route = make_router(trigger=trigger, keymap_target="b").handle(down("a"))
        self.assertEqual(route.actions, (SendKeyAction(source_key="a", target_key="b"),))
        self.assertFalse(route.accept)

    def test_no_match_passes_through(self):
        route = make_router().handle(down("a"))
        self.assertEqual(route.actions, ())
        self.assertTrue(route.accept)


if __name__ == "__main__":
    unittest.main()
```

#### `tests/test_sequence_runner.py`

```python
import unittest

from keyseq.application.app_state import AppState
from keyseq.application.sequence_runner import SequenceRunner


class FakeScheduler:
    """tk の after / after_cancel の決定的な代替。"""

    def __init__(self):
        self.queue = []
        self._next_id = 1

    def after(self, _delay_ms, callback):
        handle = self._next_id
        self._next_id += 1
        self.queue.append((handle, callback))
        return handle

    def after_cancel(self, handle):
        self.queue = [(h, cb) for h, cb in self.queue if h != handle]

    def run_pending(self, limit=100):
        count = 0
        while self.queue and count < limit:
            _, callback = self.queue.pop(0)
            callback()
            count += 1


def make_runner(triggers):
    state = AppState()
    scheduler = FakeScheduler()
    performed = []

    def find_trigger(key):
        for trigger in triggers:
            if trigger["key"] == key:
                return trigger
        return None

    runner = SequenceRunner(
        state=state,
        find_trigger=find_trigger,
        perform_action=performed.append,
        select_trigger=lambda key: None,
        refresh_actions=lambda: None,
        update_status=lambda: None,
        after=scheduler.after,
        after_cancel=scheduler.after_cancel,
    )
    return runner, state, scheduler, performed


A1 = {"type": "text", "value": "one"}
A2 = {"type": "text", "value": "two"}


class SingleStepTest(unittest.TestCase):
    def test_actions_cycle_one_per_press(self):
        trigger = {"key": "f1", "run_to_end": False, "actions": [A1, A2]}
        runner, state, _scheduler, performed = make_runner([trigger])
        runner.handle_key("f1")
        self.assertEqual(performed, [A1])
        self.assertEqual(state.indices["f1"], 1)
        runner.handle_key("f1")
        self.assertEqual(performed, [A1, A2])
        self.assertEqual(state.indices["f1"], 0)  # 循環して先頭へ
        runner.handle_key("f1")
        self.assertEqual(performed, [A1, A2, A1])

    def test_unknown_key_does_nothing(self):
        runner, _state, _scheduler, performed = make_runner([])
        runner.handle_key("f9")
        self.assertEqual(performed, [])


class RunToEndTest(unittest.TestCase):
    def make_run_to_end_runner(self):
        trigger = {"key": "f1", "run_to_end": True, "run_to_end_delay_ms": 0, "actions": [A1, A2]}
        return make_runner([trigger])

    def test_runs_all_actions_then_stops(self):
        runner, state, scheduler, performed = self.make_run_to_end_runner()
        runner.handle_key("f1")  # 1アクション目は同期実行される
        self.assertEqual(performed, [A1])
        scheduler.run_pending()
        self.assertEqual(performed, [A1, A2])
        self.assertIsNone(state.run_to_end_key)
        self.assertEqual(state.indices["f1"], 0)

    def test_same_key_toggles_pause_and_resume(self):
        runner, state, scheduler, performed = self.make_run_to_end_runner()
        runner.handle_key("f1")
        self.assertEqual(performed, [A1])
        runner.handle_key("f1")  # 実行中に同キー → 一時停止
        self.assertTrue(state.run_to_end_paused)
        self.assertEqual(scheduler.queue, [])  # 予約がキャンセルされている
        runner.handle_key("f1")  # 再開
        self.assertFalse(state.run_to_end_paused)
        scheduler.run_pending()
        self.assertEqual(performed, [A1, A2])
        self.assertIsNone(state.run_to_end_key)


if __name__ == "__main__":
    unittest.main()
```

#### `tests/test_config_service.py`

```python
import os
import tempfile
import unittest

from keyseq.application.config_service import ConfigService
from keyseq.infrastructure.json_repository import JsonRepository


def strip_internal(item):
    return {k: v for k, v in item.items() if not k.startswith("_")}


def make_runtime_data():
    return {
        "triggers": [
            {
                "key": "f1",
                "suppress": True,
                "label": "copy",
                "run_to_end": False,
                "run_to_end_delay_ms": 300,
                "actions": [{"type": "text", "value": "hello", "label": ""}],
            }
        ],
        "hotkey_presets": [{"label": "Alt+Tab", "value": "alt+tab"}],
        "hook_stop_key": "f12",
        "hook_toggle_key": "",
        "keyboard_layout": "us_tkl",
        "keyboard_show_physical_key_labels": False,
        "debug_jis_special_key_events": False,
        "external_keyboard_layouts": [],
        "keymaps": [{"id": "km1", "label": "Main", "mappings": {"a": "b"}}],
        "active_keymap_id": "km1",
        "keymap_switch_keys": {"1": "km1"},
    }


class SaveLoadRoundTripTest(unittest.TestCase):
    def test_round_trip_preserves_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            service = ConfigService(JsonRepository())
            saved, startup = service.save_runtime_data(
                "",
                make_runtime_data(),
                config_root=root,
                startup_data={},
                split_base_dir="",
            )
            self.assertEqual(startup["keymap_set_path"], "user/keymap_sets/default.json")

            for rel in (
                "config.json",
                os.path.join("user", "keymap_sets", "default.json"),
                os.path.join("user", "trigger_sets", "default.json"),
                os.path.join("user", "hotkey_presets", "default.json"),
                os.path.join("user", "keymaps", "km1.json"),
                os.path.join("user", "sequences", "copy.json"),
            ):
                self.assertTrue(os.path.exists(os.path.join(root, rel)), rel)

            loaded = service.load_runtime_data_from_keymap_set_path(
                os.path.join(root, "user", "keymap_sets", "default.json"),
                config_root=root,
            )
            self.assertEqual(
                [strip_internal(t) for t in loaded["triggers"]],
                [strip_internal(t) for t in saved["triggers"]],
            )
            self.assertEqual(
                [strip_internal(k) for k in loaded["keymaps"]],
                [strip_internal(k) for k in saved["keymaps"]],
            )
            self.assertEqual(loaded["hotkey_presets"], saved["hotkey_presets"])
            self.assertEqual(loaded["active_keymap_id"], "km1")
            self.assertEqual(loaded["keymap_switch_keys"], {"1": "km1"})
            self.assertEqual(loaded["hook_stop_key"], "f12")
            self.assertEqual(loaded["keyboard_layout"], "us_tkl")


class KeymapFileIoTest(unittest.TestCase):
    def test_save_and_load_keymap_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = ConfigService(JsonRepository())
            path = os.path.join(tmp, "my_map.json")
            saved = service.save_keymap_file(
                path, {"id": "km1", "label": "Main", "mappings": {"A": "B"}}
            )
            self.assertEqual(saved["_keymap_source_path"], path)
            self.assertFalse(saved["_keymap_imported"])
            self.assertFalse(saved["_keymap_dirty"])

            payload = JsonRepository().load_json(path)
            self.assertEqual(payload, {"label": "Main", "mappings": {"a": "b"}})

            loaded = service.load_keymap_file(path, used_keymap_ids=set(), imported=True)
            self.assertEqual(loaded["id"], "my_map")  # ファイル名から id が生成される
            self.assertEqual(loaded["mappings"], {"a": "b"})
            self.assertTrue(loaded["_keymap_imported"])


class SequenceFileIoTest(unittest.TestCase):
    def test_save_and_load_sequence_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = ConfigService(JsonRepository())
            path = os.path.join(tmp, "seq.json")
            trigger = {
                "key": "f1",
                "label": "copy",
                "run_to_end": True,
                "run_to_end_delay_ms": "abc",  # 不正値は 300 に矯正される
                "actions": [{"type": "hotkey", "value": "ctrl+c"}],
            }
            saved = service.save_sequence_file(path, trigger)
            self.assertEqual(saved["run_to_end_delay_ms"], 300)
            self.assertEqual(saved["_sequence_source_path"], path)

            loaded = service.load_sequence_file(path, imported=True)
            self.assertEqual(loaded["label"], "copy")
            self.assertTrue(loaded["run_to_end"])
            self.assertEqual(loaded["actions"], [{"type": "hotkey", "value": "ctrl+c"}])
            self.assertTrue(loaded["_sequence_imported"])


class PathHelperTest(unittest.TestCase):
    # 注意: R14 でメソッドが公開名に変わったら、このテストの呼び出しも新名に更新する
    def setUp(self):
        self.service = ConfigService(JsonRepository())

    def test_slugify_file_stem(self):
        self.assertEqual(self.service._slugify_file_stem("a/b:c"), "a_b_c")
        self.assertEqual(self.service._slugify_file_stem("con"), "con_")
        self.assertEqual(self.service._slugify_file_stem("  "), "")
        self.assertEqual(self.service._slugify_file_stem("..name.."), "name")

    def test_to_config_relative_or_absolute(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "config")
            inside = os.path.join(root, "user", "x.json")
            outside = os.path.join(tmp, "outside.json")
            self.assertEqual(
                self.service._to_config_relative_or_absolute(inside, root), "user/x.json"
            )
            self.assertEqual(
                self.service._to_config_relative_or_absolute(outside, root),
                os.path.abspath(outside).replace("\\", "/"),
            )


if __name__ == "__main__":
    unittest.main()
```

#### `tests/smoke_app.py`（unittest discover の対象外。手動スモーク用）

```python
"""アプリを 2 秒だけ起動して自動終了するスモークテスト。

注意: フック開始は行わない（グローバルフックを張らない）。
GUI が開ける環境（通常のデスクトップセッション）で実行すること。
"""
from keyseq.presentation.app import App


def main():
    app = App()
    app.after(2000, app.destroy)
    app.mainloop()
    print("SMOKE OK")


if __name__ == "__main__":
    main()
```

### 0-d. 安全網の完了条件

```powershell
py -m unittest discover -s tests -v   # 全テストが OK（fail/error 0）
py tests/smoke_app.py                 # 最後に SMOKE OK と表示される
git add tests/
git commit -m "test: リファクタリング前の特性テストとスモークテストを追加した。"
```

- テストが 1 つでも失敗する場合、**本計画の記述と実コードに食い違いがある**ということなので、コードを変えるのではなく失敗内容を報告して中断すること（テスト期待値の書き間違いの可能性を人間が判断する）。
- 以降の全項目で使う「標準検証」を定義する:

> **標準検証** =
> `py -m compileall -q keyseq main.py`（終了コード 0）
> → `py -m unittest discover -s tests -v`（全件 OK）
> → `py tests/smoke_app.py`（SMOKE OK 表示、ウィンドウが一瞬開いて閉じる）

---

## 3. 作業項目リスト（この順に実行。1 項目 = 1 コミット）

> 共通ルール:
> - 各項目の作業前に `git status` がクリーンであることを確認する。
> - 各項目の完了条件を満たせなければ `git checkout -- .`（未コミットなら）または `git revert HEAD`（コミット済みなら）で戻し、中断して報告する。
> - 行番号は基準コミット `0a8bb6a` 時点。**先行項目の削除により後続項目の行番号は上にずれる**ため、必ず記載のシンボル名で検索して特定すること。

---

### R1: views.py の重複 ActionDialog（デッドコード）を削除

- **対象**: `keyseq/presentation/views.py:298-645`（`class ActionDialog` 全体）、同ファイル冒頭の import、`FullView._cur_sel_or`（204-209 行）、`CompactView._cur_sel_or`（291-296 行）
- **問題**: `dialogs.py` の `ActionDialog` と同内容のクラスが `views.py` にも丸ごと存在する。`app.py` は `dialogs.py` 側だけを import しており（`app.py:7-14`）、`views.py` 側は完全な死物。加えて `_cur_sel_or` は両 View に定義されているが呼び出し元ゼロ。
- **どう変えるか**:
  1. `views.py` の `class ActionDialog(tk.Toplevel):` から**ファイル末尾まで**を削除する（views.py に ActionDialog より後のコードは無い）。
  2. `FullView._cur_sel_or`（`def _cur_sel_or` で検索、FullView 内）と `CompactView._cur_sel_or`（CompactView 内）の 2 メソッドを削除する。
  3. これで未使用になる import を削除する: `from tkinter import messagebox`（5 行目）、`from pynput import mouse`（8 行目）、`from keyseq.presentation.dialogs import PresetManagerDialog`（10 行目）。`tk` / `ttk` / `TYPE_CHECKING` は FullView/CompactView が使うので**残す**。
- **完了条件**:
  ```powershell
  git grep -n "class ActionDialog" -- keyseq/presentation/views.py   # ヒット 0 件
  git grep -n "_cur_sel_or" -- keyseq                                # ヒット 0 件
  ```
  → 標準検証がすべて通る。スモークでウィンドウが正常に開く。
- **リスク / 戻し方**: リスクほぼゼロ（未参照コードの削除のみ）。失敗時は `git revert HEAD`。
- **依存**: 項目 0

---

### R2: app.py の「キーマップ切替キー専用リスト UI」ハンドラ群（デッドコード）を削除

- **対象**: `keyseq/presentation/app.py` の以下のメソッドとフィールド
  - `_selected_keymap_switch_key_index`（943-946 行）
  - `_sync_keymap_switch_key_buttons`（948-957 行）
  - `_refresh_keymap_switch_key_list_ui`（959-992 行）
  - `_on_keymap_switch_key_list_select`（1043-1045 行）
  - `_on_keymap_switch_key_focus_index_change`（1050-1052 行）
  - `_start_keymap_switch_key_add_capture`（1058-1075 行）
  - `_start_keymap_switch_key_change_capture`（1077-1085 行）
  - `_start_keymap_switch_key_capture`（1087-1107 行）
  - `_stop_keymap_switch_key_capture`（1109-1128 行）
  - `_on_keymap_switch_key_capture_keypress`（1170-1218 行）
  - `_remove_keymap_switch_key`（1220-1239 行）
  - `_get_sorted_keymap_switch_items`（912-921 行）
  - `__init__` 内のフィールド初期化 3 行（131-133 行）: `self._capturing_keymap_switch_key = False` / `self._keymap_switch_capture_target_id = ""` / `self._keymap_switch_capture_original_key = ""`
- **問題**: これらは `keymap_switch_key_listbox` と追加/変更/削除ボタンの UI 用ハンドラだが、そのウィジェットを生成するコードは `views.py` にもどこにも存在しない（`hasattr` ガードで常に素通り）。入口となる 3 メソッド（add/change capture, remove）はどこからも呼ばれていない。切替キーの編集は現在 `KeymapEditDialog`（`_edit_selected_keymap` → `_apply_keymap_edit`）経由で行われている。
- **どう変えるか**: 上記メソッド・フィールドを削除する。
  - **削除してはいけないもの（要注意）**:
    - `_validate_keymap_switch_assignment`（1130-1168 行）— `_apply_keymap_edit` から呼ばれる生きたコード。
    - `_refresh_keymap_switch_ui`（923-924 行）— 名前が似ているが別物。R13 まで残す。
    - `KeymapService` 側の switch key 系メソッド — 生きている。
- **完了条件**:
  ```powershell
  git grep -n "keymap_switch_key_listbox" -- keyseq        # 0 件
  git grep -n "_capturing_keymap_switch_key" -- keyseq     # 0 件
  git grep -n "_get_sorted_keymap_switch_items" -- keyseq  # 0 件
  git grep -n "_validate_keymap_switch_assignment" -- keyseq  # 2 件（定義 + _apply_keymap_edit の呼出）が残っていること
  ```
  → 標準検証。スモーク後、可能なら手動確認: アプリを起動し「キーマップ管理 > 追加 > キーマップ変更」で切替キーを設定できること（`py main.py` で起動して手動操作。終わったら閉じる）。
- **リスク / 戻し方**: 削除対象の選定ミス（似た名前のメソッドを消す）が最大リスク。上記の grep 4 本で機械的に検証できる。失敗時は `git revert HEAD`。
- **依存**: 項目 0

---

### R3: その他の呼び出し元ゼロのデッドコードを削除

- **対象と根拠**（すべて「定義以外の参照が 0 件」であることを削除前に `git grep` で再確認すること）:
  | 場所 | シンボル |
  |---|---|
  | `config_service.py:43-46` | `load_if_exists`（呼び出し元は下記 2 つの削除対象のみ） |
  | `config_service.py:55-65` | `load_runtime_data` |
  | `config_service.py:82-102` | `try_load_split_runtime_data` |
  | `config_service.py:112-122` | `resolve_startup_config_path` |
  | `config_service.py:133-136` | `save` |
  | `config_service.py:991-992` | `_to_config_relative_path` |
  | `app.py:2428-2435` | `App._load_if_exists`（`config_service.load_if_exists` の唯一の生きた呼び出し元だが、このメソッド自体が未使用） |
  | `keyboard_layouts.py:255-260` | `save_layout_to_json` |
  | `keyboard_layouts.py:263-279` | `layout_to_dict`（`save_layout_to_json` からのみ参照） |
  | `app_state.py:36-38` | `AppState.request_main_thread` |
- **問題**: 読み手が「どこから呼ばれるのか」を探す時間を浪費する。特に `ConfigService` は生きた保存/読込経路（`save_runtime_data` / `load_runtime_data_from_keymap_set_path`）と紛らわしい。
- **どう変えるか**: 上記を削除する。**`load` / `load_legacy_runtime_data` / `export_runtime_data` / `load_startup` / `save_startup` / `resolve_startup_relative_path` / `new_empty_data` / `normalize_runtime_data` は使用中なので消さない。**
- **完了条件**:
  ```powershell
  git grep -nE "load_if_exists|try_load_split_runtime_data|resolve_startup_config_path|save_layout_to_json|layout_to_dict|request_main_thread" -- keyseq  # 0 件
  git grep -n "def save(" -- keyseq/application/config_service.py  # 0 件
  ```
  → 標準検証（特に `tests/test_config_service.py` が全件 OK であること）。
- **リスク / 戻し方**: `load` を誤って消すと `load_legacy_runtime_data`（Import 機能）が壊れる。grep と unittest で検出できる。失敗時は `git revert HEAD`。
- **依存**: 項目 0

---

### R4: App の未使用 state エイリアスプロパティを削除

- **対象**: `app.py:168-238`（「State compatibility aliases」ブロックの一部）
- **問題**: `AppState` 導入時の互換用プロパティ 13 個のうち、実際に使われているのは `_selected_trigger_idx` と `_indices` の 2 つだけ。残り 11 個（`_lock`, `_reentry_guard`, `_run_to_end_key`, `_run_to_end_paused`, `_run_to_end_after_id`, `_chain_running`, `_chain_paused`, `_chain_key`, `_chain_thread`, `_chain_stop_event`, `_chain_pause_event`）は参照ゼロ。
- **どう変えるか**: 上記 11 プロパティ（setter 含む）を削除する。`_selected_trigger_idx`（property + setter, 152-158 行）と `_indices`（property + setter, 160-166 行）は**残す**。
- **完了条件**:
  ```powershell
  git grep -nE "def _lock|def _reentry_guard|def _run_to_end_key|def _run_to_end_paused|def _run_to_end_after_id|def _chain_" -- keyseq/presentation/app.py  # 0 件
  ```
  → 標準検証。
- **リスク / 戻し方**: ほぼゼロ。失敗時は `git revert HEAD`。
- **依存**: 項目 0

---

### R5: 到達不能な chain 実行系を削除

- **対象**:
  - `sequence_runner.py:163-262`: `chain_start_or_toggle`, `stop_chain`, `_chain_worker`, `_finish_chain`, `is_chain_running`, `refresh_status`, `set_hooks` と、ファイル冒頭の `import threading` / `import time`（chain 以外で未使用なら）
  - `app_state.py`: `chain_running`, `chain_paused`, `chain_key`, `chain_thread`, `chain_stop_event`, `chain_pause_event` の 6 フィールドと、不要になる `import threading`（`lock: threading.Lock` が残るので **threading import は残す**）
  - `app.py`: `self.sequence_runner.stop_chain(force=True)` の呼び出し 2 箇所（`stop_hook` 内 2973 行、`toggle_custom_input_enabled` 内 2998 行）
- **問題**: chain 実行（ワーカースレッドでシーケンスを最後まで流す機構）は開始経路 `chain_start_or_toggle` がどこからも呼ばれず到達不能。停止側の防御呼び出しだけが残り、実質常に no-op。run_to_end 機構（`after` ベース）が同じ役割を担っている。
- **どう変えるか**:
  1. まず `git grep -n "chain" -- keyseq` を実行し、ヒットが上記対象（と R4 で削除済みのエイリアス）だけであることを確認する。**想定外のヒットがあれば削除せず中断して報告。**
  2. 上記をすべて削除する。`sequence_runner.py` の `import time` は chain 専用なので削除、`import threading` も chain 専用なので削除（`SequenceRunner` 本体は使っていない）。
  3. 削除は git 履歴に残るため、将来 chain 機能を再開する場合は本コミットを revert すれば復元できる。
- **完了条件**:
  ```powershell
  git grep -in "chain" -- keyseq   # 0 件
  ```
  → 標準検証（`tests/test_sequence_runner.py` が OK であること）。スモークで起動確認。
- **リスク / 戻し方**: 「未完成の将来機能を消してしまう」懸念があるが、到達不能である以上現機能への影響はゼロ。復元は `git revert <このコミット>` 一発。
- **依存**: R4（chain エイリアスプロパティが先に消えていること）

---

### R6: normalize_key_name の重複定義を domain に一本化

- **対象**: `app.py:47-48`、`keyboard_window.py:37-38`
- **問題**: `keyseq.domain.config.normalize_key_name` と同一実装のモジュールローカル関数が 2 ファイルに再定義されている。将来片方だけ変更されると正規化が食い違う。
- **どう変えるか**:
  - `app.py`: 47-48 行の `def normalize_key_name(...)` を削除し、38-41 行の `from keyseq.domain.config import (...)` に `normalize_key_name` を追加する。
  - `keyboard_window.py`: 37-38 行の定義を削除し、`from keyseq.domain.config import normalize_key_name` を追加する。
- **完了条件**:
  ```powershell
  git grep -n "def normalize_key_name" -- keyseq   # 1 件（keyseq/domain/config.py のみ）
  ```
  → 標準検証。
- **リスク / 戻し方**: 実装が同一（`(s or "").strip().lower()`）なので挙動不変。失敗時は `git revert HEAD`。
- **依存**: 項目 0

---

### R7: Tk keysym 正規化マップを 1 箇所に共通化

- **対象**:
  - `app.py:3276-3293` `App._normalize_tk_key_for_trigger`
  - `dialogs.py:256-276` `ActionDialog._normalize_tk_key`
  - `dialogs.py:677-694` `TriggerDialog._normalize_tk_key`
  - `dialogs.py:795-811` `KeymapEditDialog._normalize_tk_key`
  - `keyboard_window.py:312-341` `KeyboardWindow._normalize_tk_key`
- **問題**: 「Tk keysym → keyboard ライブラリ表記」の 13 エントリの辞書が 5 箇所にコピペされている（内容は全箇所同一。KeyboardWindow のみ追加でスキャンコード解決のフォールバックを持つ）。
- **どう変えるか**:
  1. 新規ファイル `keyseq/presentation/tk_keys.py` を作成（辞書は `keyboard_window.py` からも参照するため公開名にする）:
     ```python
     from __future__ import annotations

     # Tk keysym -> keyboard ライブラリの単キー表記
     TK_KEYSYM_TO_KEYBOARD_NAME = {
         "control_l": "ctrl", "control_r": "ctrl",
         "shift_l": "shift", "shift_r": "shift",
         "alt_l": "alt", "alt_r": "alt",
         "super_l": "windows", "super_r": "windows",
         "win_l": "windows", "win_r": "windows",
         "return": "enter",
         "escape": "esc",
         "space": "space",
         "tab": "tab",
         "backspace": "backspace",
         "prior": "page up",
         "next": "page down",
     }


     def normalize_tk_keysym(keysym: str) -> str:
         """Tk の keysym を keyboard ライブラリの単キー表記に寄せる。"""
         k = (keysym or "").lower()
         return TK_KEYSYM_TO_KEYBOARD_NAME.get(k, k)
     ```
  2. `app.py` の `_normalize_tk_key_for_trigger`、`dialogs.py` の 3 つの `_normalize_tk_key` は、メソッドを残したまま本体を `return normalize_tk_keysym(keysym)` の 1 行に差し替える（呼び出し箇所が多いため、呼び出し側は変更しない）。辞書リテラルは全箇所から削除する。
  3. `KeyboardWindow._normalize_tk_key` のみ、マップ非ヒット時に `resolve_key_id_from_scan_code(...)` へフォールバックする既存の分岐構造を**そのまま**保ち、辞書だけ共通のものに差し替える:
     ```python
     def _normalize_tk_key(self, event: object) -> str:
         keysym = str(getattr(event, "keysym", "") or "")
         k = keysym.lower()
         if k in TK_KEYSYM_TO_KEYBOARD_NAME:
             return TK_KEYSYM_TO_KEYBOARD_NAME[k]
         resolved = resolve_key_id_from_scan_code(self._layout, getattr(event, "keycode", None))
         if resolved:
             return normalize_key_name(resolved)
         return k
     ```
- **完了条件**:
  ```powershell
  git grep -c "control_l" -- keyseq   # tk_keys.py の 1 ファイルのみにヒットすること
  ```
  → 標準検証。スモーク後、可能なら手動確認: トリガー追加ダイアログの「キー入力で取得」で F1 を押すと `f1` が入ること、Enter キーが `enter` になること。
- **リスク / 戻し方**: キーキャプチャ系の回帰。マップ内容は変えていないため、変換結果は不変のはず。手動確認で異常があれば `git revert HEAD`。
- **依存**: R1（views.py 内の重複コピーが先に消えていること。消えていないと差し替え漏れが起きる）

---

### R8: dialogs.py の文字化けコメントを修正

- **対象**: `dialogs.py:313`（`self.mouse_frame.grid_remove()  # ��\��`）
- **問題**: エンコーディング事故で壊れたコメントが残っている（元は「非表示」）。
- **どう変えるか**: コメントを `# 非表示` に置き換える。ファイルは UTF-8 のまま保存する。
- **完了条件**:
  ```powershell
  git grep -n "�" -- keyseq   # 0 件（PowerShell では git grep -n "�" -- keyseq でも可）
  ```
  → 標準検証。
- **リスク / 戻し方**: ゼロ（コメントのみ）。
- **依存**: R1（views.py 側の文字化け行はデッドコードごと削除済みであること）

---

### R9: run_to_end のデフォルト値と非負 int 矯正を domain に一元化

- **対象**: `domain/config.py`、`config_service.py`、`sequence_runner.py`、`app.py`
- **問題**: デフォルト 300ms のリテラルと「int 変換失敗→デフォルト、負→0」のロジックが 4 ファイルに散在。リテラル `300` の全出現箇所（基準コミット時点、コメント除く）:
  `domain/config.py:14,29,82,100,104` / `config_service.py:456,784,794` / `sequence_runner.py:129,133` / `app.py:280,2649,2658,2662,2681,2684`
- **どう変えるか**:
  1. `domain/config.py` に追加（`DEFAULT_CONFIG` の直前）:
     ```python
     DEFAULT_RUN_TO_END_DELAY_MS = 300


     def coerce_nonnegative_int(value: Any, default: int) -> int:
         try:
             number = int(value)
         except Exception:
             number = int(default)
         if number < 0:
             number = 0
         return number
     ```
  2. `domain/config.py`: `ensure_config_compatibility` の delay 矯正ブロック（100-107 行）を
     `t["run_to_end_delay_ms"] = coerce_nonnegative_int(t.get("run_to_end_delay_ms", DEFAULT_RUN_TO_END_DELAY_MS), DEFAULT_RUN_TO_END_DELAY_MS)` に置換。`DEFAULT_CONFIG` 内の 2 箇所（14, 29 行）とレガシー変換ブロック内の 1 箇所（82 行）も定数参照にする。
  3. `config_service.py`: `_coerce_nonnegative_int` の本体を `return coerce_nonnegative_int(value, default)` に委譲（import 追加）。`300` リテラル 3 箇所（456, 784, 794 行）を `DEFAULT_RUN_TO_END_DELAY_MS` に置換。
  4. `sequence_runner.py` `_run_to_end_step` の delay 矯正（129-135 行）を
     `delay = coerce_nonnegative_int(trig.get("run_to_end_delay_ms", DEFAULT_RUN_TO_END_DELAY_MS), DEFAULT_RUN_TO_END_DELAY_MS)` に置換（import 追加）。
  5. `app.py`:
     - `_build_ui` 内 `self.run_to_end_delay_var = tk.StringVar(value="300")`（280 行）→ `value=str(DEFAULT_RUN_TO_END_DELAY_MS)`
     - `_sync_run_to_end_ui`（2649, 2658-2665 行）: `set("300")` → `set(str(DEFAULT_RUN_TO_END_DELAY_MS))`、矯正ロジック → `d = coerce_nonnegative_int(t.get("run_to_end_delay_ms", DEFAULT_RUN_TO_END_DELAY_MS), DEFAULT_RUN_TO_END_DELAY_MS)`
     - `update_run_to_end_delay`（2679-2684 行）: `v = int(s)` の矯正 → `v = coerce_nonnegative_int(s, DEFAULT_RUN_TO_END_DELAY_MS)`、`old_v = int(t.get("run_to_end_delay_ms", 300) or 300)` → `old_v = coerce_nonnegative_int(t.get("run_to_end_delay_ms", DEFAULT_RUN_TO_END_DELAY_MS), DEFAULT_RUN_TO_END_DELAY_MS)`
       ※ `old_v` の元コードは `or 300` により **0 を 300 に変換する**が、`old_v` は「変更有無の判定」にしか使われず、0→300 になるのは delay が 0 のときのみ（このとき新値 v も 0 なら「変更なし」扱いだったのが「変更あり」扱いに変わり得る）。厳密同値にするため、`old_v` だけは元の式 `int(t.get("run_to_end_delay_ms", DEFAULT_RUN_TO_END_DELAY_MS) or DEFAULT_RUN_TO_END_DELAY_MS)` をリテラルだけ定数化して残すこと（ロジックは変えない）。
- **完了条件**: 標準検証（`test_domain_config.py` の `test_delay_coercion` と `test_config_service.py` の `SequenceFileIoTest` が矯正挙動の不変を保証する）。加えて:
  ```powershell
  git grep -n "300" -- keyseq
  # ヒットが以下だけであること:
  #   keyseq/domain/config.py の「DEFAULT_RUN_TO_END_DELAY_MS = 300」（定数定義）
  #   views.py:193 と app.py の「"00300" 等を…」のコメント 2 行
  ```
- **リスク / 戻し方**: 置換漏れがあっても挙動は同じ（同値ロジック）なので実害なし。失敗時は `git revert HEAD`。
- **依存**: 項目 0

---

### R10: デフォルトレイアウト ID "us_tkl" を定数化

- **対象**: `domain/config.py:48,147-151`、`config_service.py:637`、`keyboard_layouts.py:34`
- **問題**: `"us_tkl"` のリテラルが domain と application に散在。presentation には `DEFAULT_LAYOUT_ID` 定数が既にあるが、依存方向の制約（domain は presentation を import できない）で共有されていない。
- **どう変えるか**:
  1. `domain/config.py` に `DEFAULT_KEYBOARD_LAYOUT_ID = "us_tkl"` を追加し、同ファイル内のリテラル（`DEFAULT_CONFIG["keyboard_layout"]` と `ensure_config_compatibility` 内 3 箇所）を定数参照に置換。
  2. `config_service.py:637` の `"us_tkl"` 2 箇所を定数参照に置換（import 追加）。
  3. `keyboard_layouts.py:34` を `DEFAULT_LAYOUT_ID = DEFAULT_KEYBOARD_LAYOUT_ID`（domain から import）に変更。既存の `DEFAULT_LAYOUT_ID` という名前は presentation 層で広く使われているため**名前は変えない**。
- **完了条件**:
  ```powershell
  git grep -n '"us_tkl"' -- keyseq   # 1 件（keyseq/domain/config.py の定数定義のみ）
  ```
  → 標準検証。
- **リスク / 戻し方**: ほぼゼロ。失敗時は `git revert HEAD`。
- **依存**: 項目 0

---

### R11: save_keymap_set / save_as の重複本体を共通化

- **対象**: `app.py:2437-2497`
- **問題**: 保存処理の try ブロック（正規化 → split_base_dir 確認 → `save_runtime_data` → 状態更新 → フラッシュ表示）が両メソッドで完全に重複している。片方だけ修正される事故が起きやすい。
- **どう変えるか**（スケッチ。フラッシュ文言の違い「保存しました。/別名で保存しました。」を必ず維持する）:
  ```python
  def save_keymap_set(self, *, show_success_dialog: bool = True) -> bool:
      return self._save_keymap_set_to(
          self.keymap_set_path,
          flash_message="保存しました。",
          show_success_dialog=show_success_dialog,
      )

  def save_as(self, *, show_success_dialog: bool = True) -> bool:
      suggested_path = self._suggest_keymap_set_dialog_path()
      path = filedialog.asksaveasfilename(
          title="別名で保存（keymap_set）",
          initialdir=self._suggest_keymap_set_dialog_dir(),
          initialfile=os.path.basename(suggested_path),
          defaultextension=".json",
          filetypes=[("JSON", "*.json"), ("All", "*.*")]
      )
      if not path:
          return False
      return self._save_keymap_set_to(
          path,
          flash_message="別名で保存しました。",
          show_success_dialog=show_success_dialog,
      )

  def _save_keymap_set_to(self, path: str, *, flash_message: str, show_success_dialog: bool) -> bool:
      try:
          save_path = self._normalize_keymap_set_save_path(path)
          split_base_dir = self._choose_split_base_dir_for_keymap_set(save_path)
          self.data, startup_payload = self.config_service.save_runtime_data(
              save_path,
              self.data,
              config_root=self.config_root,
              startup_data=self._startup_settings,
              keep_legacy_copy=False,
              split_base_dir=split_base_dir,
          )
          self.keymap_set_path = save_path
          self.startup_path = self._preferred_startup_path()
          self._startup_settings = startup_payload
          self._clear_individual_dirty_flags()
          self._set_dirty(False)
          self._set_flash_message(flash_message)
          if show_success_dialog:
              messagebox.showinfo("保存", f"保存しました:\n{save_path}")
          return True
      except Exception as e:
          self._set_flash_message(f"保存失敗: {e}", auto_clear=False)
          messagebox.showerror("保存失敗", str(e))
          return False
  ```
- **完了条件**: 標準検証。加えて手動確認: `py main.py` で起動し、「保存」→ 成功ダイアログにパスが出ること、「別名で保存...」→ ファイル選択 → フラッシュに「別名で保存しました。」が出ること、タイトル下のファイル状態が「保存済み」になること。確認後アプリを閉じる。
- **リスク / 戻し方**: 保存フローの回帰（最重要データ経路）。`test_config_service.py` が ConfigService 層を、手動確認が UI 層を担保する。失敗時は `git revert HEAD`。
- **依存**: 項目 0

---

### R12: 設定読込後の UI 変数同期を 1 メソッドに集約

- **対象**: `app.py` の `new_config`（2413-2419 行）、`restore_default`（2599-2605 行）、`_apply_loaded_data_to_ui`（2577-2583 行）
- **問題**: 「stop_key_var / toggle_key_var / keyboard_show_physical_key_labels_var を data から再設定し、レイアウトコンボを同期する」処理が 3 箇所にコピペされている。
- **どう変えるか**: 以下を追加し、3 箇所の該当ブロックをこの呼び出しに置換する:
  ```python
  def _sync_control_vars_from_data(self) -> None:
      """data の内容を制御キー表示・レイアウト選択などの共有 Var へ反映する。"""
      if hasattr(self, "stop_key_var"):
          self.stop_key_var.set(str(self.data.get("hook_stop_key", "")))
      if hasattr(self, "toggle_key_var"):
          self.toggle_key_var.set(str(self.data.get("hook_toggle_key", "")))
      if hasattr(self, "keyboard_show_physical_key_labels_var"):
          self.keyboard_show_physical_key_labels_var.set(
              bool(self.data.get("keyboard_show_physical_key_labels", False))
          )
      self._sync_keyboard_layout_controls()
  ```
  `_apply_loaded_data_to_ui` に残るその他の処理（`_trigger_set_source_path` リセット、`_clear_individual_dirty_flags`、`_set_dirty(False)`）はそのまま残す。`new_config` / `restore_default` の後続処理（`state.reset_indices()` 等）も変えない。
- **完了条件**: 標準検証。手動確認: 「ファイル > 新規作成」でトリガー一覧が空になり停止キー表示が空になること、「ファイル > 例を復元」で F1/F2 のトリガーが表示されること。
- **リスク / 戻し方**: 低（同一文の抽出）。失敗時は `git revert HEAD`。
- **依存**: 項目 0

---

### R13: `_refresh_keymap_switch_ui` エイリアスを解消（同一リストの二重再描画をやめる）

- **対象**: `app.py:923-924` の定義と、その全呼び出し箇所（`_add_keymap` / `_rename_keymap_label` / `_delete_keymap` / `_apply_keymap_edit` / `activate_keymap_by_id` / `assign_keymap_from_keyboard_ui` / `clear_keymap_from_keyboard_ui` / `_refresh_triggers` 内）
- **問題**: `_refresh_keymap_switch_ui()` は `_refresh_keymap_list_ui()` を呼ぶだけの別名。現存する全呼び出し箇所で直前に `_refresh_keymap_list_ui(...)` も呼ばれており、同じ Listbox を毎回 2 回作り直している。
- **どう変えるか**:
  1. `git grep -n "_refresh_keymap_switch_ui" -- keyseq` で全箇所を列挙する。
  2. 各呼び出し箇所を確認し、直前（同じ処理ブロック内）に `_refresh_keymap_list_ui(...)` の呼び出しがある場合は `self._refresh_keymap_switch_ui()` の行を削除する。無い場合は `self._refresh_keymap_list_ui()` に置き換える（基準コミット時点では全箇所が前者のはず）。
  3. 定義（923-924 行）を削除する。
- **完了条件**:
  ```powershell
  git grep -n "_refresh_keymap_switch_ui" -- keyseq   # 0 件
  ```
  → 標準検証。手動確認: キーマップの追加・名前変更・削除・選択で一覧表示（`>` マーカー、切替キー表示）が正しく更新されること。
- **リスク / 戻し方**: 再描画回数が 2→1 になるだけで最終状態は同一。表示崩れがあれば `git revert HEAD`。
- **依存**: R2（似た名前の `_refresh_keymap_switch_key_list_ui` が先に消えていること。取り違え防止）

---

### R14: App から呼ばれる ConfigService 私有メソッドを公開名に変更

- **対象**: `config_service.py` の `_slugify_file_stem` / `_slugify_keymap_file_stem` / `_to_config_relative_or_absolute`、および `app.py` の参照 3 箇所（1695, 2066, 2071 行）
- **問題**: `App` が別クラスの `_` 付きメソッドを直接呼んでおり、私有/公開の境界が嘘になっている。
- **どう変えるか**:
  1. `config_service.py` 内で `_slugify_file_stem` → `slugify_file_stem` にリネームし、**全参照**（同ファイル内 821, 840 行と定義、`app.py` 2066, 2071 行）を更新する。
  2. `_slugify_keymap_file_stem`（1005-1006 行）は単なる転送なので削除し、その呼び出し 3 箇所（859, 864, 870 行）を `slugify_file_stem` 直呼びに置換する。
  3. `ConfigService._to_config_relative_or_absolute` → `to_config_relative_or_absolute` にリネームし、`config_service.py` 内の全参照（579, 631, 632, 669, 736, 767, 845 行と定義）を更新する。
     - 注意: `app.py` には **App 自身の**同名私有ラッパー `App._to_config_relative_or_absolute`（1694-1695 行）がある。これは App 内部用なので**名前は変えず**、本体の呼び出し先だけ新名 `self.config_service.to_config_relative_or_absolute(path, self.config_root)` に更新する。
  4. `app.py:2066, 2071` の `self.config_service._slugify_file_stem(...)` を新名 `slugify_file_stem` に更新する。
  5. **`tests/test_config_service.py` の `PathHelperTest` の呼び出しも新名に更新する**（テストファイル内に注意書きあり）。
- **完了条件**:
  ```powershell
  git grep -nE "_slugify_file_stem|_slugify_keymap_file_stem|_to_config_relative_or_absolute" -- keyseq/application tests  # 0 件
  git grep -n "config_service\._" -- keyseq/presentation/app.py   # 0 件（App から ConfigService の私有メンバへのアクセスが無い）
  git grep -nE "slugify_file_stem|to_config_relative_or_absolute" -- keyseq   # 参照が残っていること（>0 件）
  ```
  → 標準検証（リネーム漏れは unittest / compileall では検出できないケースがあるため、**grep が主たる検証**）。
- **リスク / 戻し方**: 機械的リネームの置換漏れ。grep 2 本で機械検証できる。失敗時は `git revert HEAD`。
- **依存**: 項目 0（テスト更新を含むため）、R3（`_to_config_relative_path` が削除済みで紛れがないこと）

---

### R15: JSON 保存をアトミック化（一時ファイル + os.replace）

- **対象**: `infrastructure/json_repository.py:13-18` `save_json`
- **問題**: 書き込み途中でプロセスが落ちると設定ファイルが半端な内容で壊れる。分割保存（1 回の保存で最大 6 ファイル以上書く）ではリスクが増幅される。
- **どう変えるか**:
  ```python
  def save_json(self, path: str, data: Any) -> None:
      directory = os.path.dirname(path)
      if directory:
          os.makedirs(directory, exist_ok=True)
      temp_path = f"{path}.tmp"
      with open(temp_path, "w", encoding="utf-8") as file:
          json.dump(data, file, ensure_ascii=False, indent=2)
      os.replace(temp_path, path)
  ```
  - ファイルの最終内容・フォーマット（indent=2, ensure_ascii=False）は不変。
  - 書き込み失敗時に `.tmp` が残り得るが、次回保存で上書きされるため掃除処理は追加しない（スコープ最小化）。
- **完了条件**: 標準検証（`test_config_service.py` の保存系テストがそのまま通ること = 保存内容の不変を担保）。加えて:
  ```powershell
  py -c "from keyseq.infrastructure.json_repository import JsonRepository; import tempfile, os, json; d=tempfile.mkdtemp(); p=os.path.join(d,'x.json'); JsonRepository().save_json(p, {'a':1}); print(json.load(open(p, encoding='utf-8'))); print(os.path.exists(p+'.tmp'))"
  # 出力: {'a': 1} と False
  ```
- **リスク / 戻し方**: `os.replace` は同一ボリューム内なら Windows でもアトミック。失敗時は `git revert HEAD`。
- **依存**: 項目 0

---

### R16: 起動時の構成セット読込失敗を無音にしない

- **対象**: `app.py:1752-1776` `_load_startup_and_config` の `except Exception: pass`（1772-1773 行）
- **問題**: startup.json に構成セットパスが記録されていてファイルも存在するのに読込で例外が出た場合、完全に無音で空データ起動になる。ユーザーは設定が消えたように見える。
- **どう変えるか**: `except Exception: pass` を以下に置換する（起動をブロックしない**ステータスバー表示のみ**。ダイアログは出さない）:
  ```python
  except Exception as e:
      self._set_flash_message(
          f"構成セットの読込に失敗したため、空の状態で起動しました: {e}",
          auto_clear=False,
      )
  ```
  ※ `_load_startup_and_config` は `_build_ui()` の後に呼ばれるため `flash_message_var` は利用可能。
- **完了条件**: 標準検証。手動確認（任意）: `config/config.json` の `keymap_set_path` が指す JSON を一時的に壊して起動し、ステータスバー中央にメッセージが出ること。**確認後は必ずファイルを元に戻す**（`git checkout` 対象外の生成物なのでバックアップを取ってから行う。config/ 配下を触りたくない場合はこの手動確認を省略してよい）。
- **リスク / 戻し方**: 表示が 1 行増えるのみ（挙動フローは不変）。これは厳密には「無音→可視化」の UX 変更であることを最終報告に明記すること。失敗時は `git revert HEAD`。
- **依存**: 項目 0

---

### R17: 最終検証とドキュメント整合確認

- **対象**: リポジトリ全体
- **やること**:
  1. 標準検証をフルで実行。
  2. `py main.py` で起動し、以下の手動シナリオを一通り実施して閉じる:
     - トリガー追加（キー入力で取得）→ アクション追加（hotkey: `ctrl+c`）→ 開始（フックON）→ トリガーキー押下でアクションが実行される → 停止（フックOFF）
     - 省略表示 ⇔ フルに戻す
     - キーボードUIを開いて閉じる
     - 保存 → 再起動 → 内容が復元される
  3. `instruction/common/codebase_map.md` / `architecture_rules.md` を読み、今回の変更（デッドコード削除・共通化）と矛盾する記述が**ないこと**を確認する。矛盾があればその行だけ修正する（基準コミット時点では chain・切替キーリスト UI ともドキュメントに記載がないため、修正不要の見込み）。
  4. 全項目のコミット一覧（`git log --oneline <ベースライン>..HEAD`）と、スキップ・失敗した項目の有無を最終報告にまとめる。
- **完了条件**: 上記すべて完了し、`git status` がクリーン。
- **依存**: R1〜R16 のうち実施したすべて

---

## 4. やらないことリスト（実行者は以下を行ってはならない）

1. **app.py の分割・God class 解消**（Mixin 化、コントローラ抽出、View へのロジック移動など）。UI の自動テストが無い現状ではリスクが効果を上回る。将来の計画書で扱う。
2. **機能追加・仕様変更・UI 文言変更**。例外は R16 のフラッシュメッセージ追加のみ（本計画で明示済み）。
3. **保存 JSON の構造・キー名・パス表現の変更**。`config.json` / `keymap_set.json` 等のフォーマットは 1 バイトも変えない（R15 は書き込み手順のみの変更で内容は不変）。
4. **依存ライブラリの追加・更新・削除**。pytest / black / ruff 等の導入も禁止。テストは unittest（標準ライブラリ）のみ。
5. **一括整形（フォーマッタ適用）や、変更対象外の行の「ついで修正」**。diff は各項目の記載範囲に限定する。
6. **キーキャプチャ 3 系統（停止キー/トグルキー/ダイアログ内キャプチャ）の共通化**。ほぼ同型のコードだが、フック一時停止との絡みで挙動リスクが高いため今回は対象外。
7. **付録（§5）に挙げた潜在バグの修正**。バグ修正は挙動変更であり、本計画のスコープ外。発見しても直さず報告に含めるだけにする。
8. **`suppress` / send guard / フック一時停止カウンタまわりのロジック変更**。1 文字も触らない。
9. **`config/` 配下のユーザーデータの変更・削除**（R16 の手動確認で一時的に触る場合はバックアップ必須・原状復帰必須）。
10. **フックを張ったまま放置しないこと**。手動確認でフック ON にした場合は必ず停止してからアプリを閉じる。

## 5. 付録: 発見済みの潜在バグ（今回は修正しない。報告のみ）

実行者への注意: 以下は「テストが変な値を期待している」と感じたときの答え合わせでもある。**現挙動が正**として特性テストを書いている。

1. `App.rename_trigger`（app.py:2756-2797）: キーを変えずラベルだけ変更した場合でも `self._indices` から当該キーの実行位置が削除され、「次に実行する行」が先頭に戻る。
2. `FullView` と `CompactView` の両方が `app.topmost_chk` に代入しており、後勝ちで CompactView の参照だけが残る（現状 App 側から未使用のため実害なし）。
3. `ActionDialog._capture_mouse_position`（dialogs.py）: 座標取得中にダイアログを閉じると pynput の Listener スレッドがクリックされるまで残る（daemon なのでプロセス終了は妨げない）。
4. `App._stop_stop_key_capture` 等の `self.unbind("<KeyPress>")` は、ルートウィンドウの `<KeyPress>` バインドを全解除する（現状 `<KeyPress>` を同時に複数バインドする経路はキャプチャ系のみで、相互排他されているため実害なし）。

## 6. 実行者への指示文（この計画書を渡すときにそのままコピペする）

```
あなたはこのリポジトリのリファクタリング実行者です。
instruction/modified_proposal/01_refactoring_plan.md を最初から最後まで読み、記載どおりに作業してください。

厳守事項:
- 計画書の「項目 0」（安全網）から着手し、以降 R1 → R17 の順に 1 項目ずつ実施する。
- 1 項目 = 1 コミット。コミットメッセージは日本語で「何をしたか」を書く（例: 「refactor: views.py の重複 ActionDialog を削除した。」）。
- 各項目の作業前に git status がクリーンであることを確認する。
- 各項目の「完了条件」をすべて満たしてからコミットする。満たせない場合は、その項目の変更を破棄（git checkout -- . / git revert）して作業を中断し、何がどう失敗したかを報告する。勝手に別の直し方を試さない。
- 計画書の「やらないことリスト」に該当する変更は、たとえ改善に見えても行わない。
- 行番号は基準コミット時点のもの。ずれている場合はシンボル名（クラス名・メソッド名）で特定する。計画書の記載と実コードが食い違う場合は作業せず報告する。
- Python は py コマンドで実行する（例: py -m unittest discover -s tests -v）。
- 挙動を変えないことが最優先。テスト（tests/）の期待値は変更禁止（R14 で指示されたメソッド名の追従更新のみ例外）。

最終成果物:
- refactor/01-cleanup ブランチ上の一連のコミット
- 実施した項目 / スキップした項目 / 各項目の検証結果を列挙した報告
```
