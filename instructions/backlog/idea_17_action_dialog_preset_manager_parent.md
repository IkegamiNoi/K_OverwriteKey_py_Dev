# idea_17_action_dialog_preset_manager_parent.md

## 概要

`ActionDialog` からプリセット編集を開くとき、**親として App を渡している**
（`action_dialog.py:341`）。実際の呼び出し元は `ActionDialog` なので、
**`transient` 親が実体と食い違う**。**z 順（重なりの前後）だけが論点**で、
**grab の復元先には影響しない**。付け替えるなら
**「親ウィンドウ」と「App 参照」を引数で分離する**必要がある。

## 起票経緯（2026-09-12）

出所: [phase 14](../phase/14_nested_modal_grab_restore/phase.md) の受け入れ条件 15
（暫定仕様 [12](../history/12_nested_modal_grab_restore.md) §6-5 で
「本フェーズ外・フェーズ末に独立 idea として起票する」とユーザーが確定）。

**v0.1 で書いた「付け替えないと 3 段ネストの復元先が曖昧になる」は誤りで撤回済み**。
grab の復元先は**開く前の保持者の記録**で決まり、**Tk の master とは独立**している
（`keyseq/presentation/modal.py`）。phase 14 の 3 段ネストのテストも
**全段が App の子のまま**で期待どおり動いている。

## 現状

- `action_dialog.py:341` は `PresetManagerDialog(self.parent, title=...)` を呼ぶ。
  `ActionDialog.parent` は **App**（`action_dialog.py:17` の `__init__(self, parent: App, ...)`）。
  したがって**マネージャの master と `transient` 親はどちらも App** になる。
- `PresetManagerDialog` は受け取った `parent` を**App として使う**。
  `self.parent.hook`（`:80`）/ `self.parent.data`（`:167`・`:227`）/
  `self.parent.config_service`（`:175`・`:183`）/ `self.parent.keymap_set_path`（`:178`・`:186`）/
  `self.parent.validate_hotkey`（`:297`・`:332`）。
  **単純に `ActionDialog` を渡すと全部壊れる**。
- もう 1 つの呼び出し元 `App.open_preset_manager`（`app.py:418`）は `PresetManagerDialog(self, ...)` で、
  **こちらは親も App も同一で正しい**。引数を分離するなら**この呼び出しも追随が要る**。

## 提案（方向性・要設計）

- **案 A: 引数を分離する** — `PresetManagerDialog(parent, *, app=None)` のような形にし、
  **`master` と `transient` の親はウィジェット側、業務参照は `app` 側**へ振り分ける。
  `app` 省略時は `parent` を App とみなせば `app.py:418` は無変更で済む。
  `action_dialog.py` だけ `PresetManagerDialog(self, app=self.parent, ...)` になる。
- **案 B: App 参照を属性から辿る** — `self.parent` の代わりに
  `self.winfo_toplevel()` や既存の App 取得口から辿る。引数は増えないが、
  **どのウィジェットからも App へ辿れる前提**を新たに置くことになる。
- **案 C: 現状維持** — z 順以外に実害が無いため触らない。
  **他のダイアログ（`PresetDialog` は `preset_manager.py:282` で `self` を渡している）と
  作法が揃っていない**点だけが残る。

**着手するなら `ActionDialog` 以外の同型箇所も棚卸しする**
（`dialogs/` は `parent` を App としても親ウィジェットとしても使う設計のため、
同じ食い違いが他にもあり得る）。

## 想定スコープ

- **含む**: `dialogs/preset_manager.py` の引数設計、`action_dialog.py` / `app.py` の呼び出し追随、
  同型箇所の棚卸し。
- **含まない**: grab の復元（phase 14 で完了・**本件とは独立**）。
  ダイアログ同型スケルトンの共通化（別項目。ただし**着手時期が重なるなら合流を検討する価値がある**）。
- **影響レイヤ**: presentation 限定。スキーマ変更なし。
- **仕様変更**: 見込みなし（正本に `transient` 親の規定は無い）。
  ただし `features.md` §4.6 のモーダル作法へ 1 行足すかは着手時に判断。
- **優先度**: **低**（z 順のみ・実害の報告なし）。
