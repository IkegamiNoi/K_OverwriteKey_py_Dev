# task_11d_prohibited_key_wording

## 目的

割り当て禁止の文言（3 つ）と、プリセットのダイアログのヒントを、両 OS に合う文言にする（暫定 57 §5.3.4 の「割り当て禁止の文言の Mac 向けの言い換えは task_11 のまま」・**ユーザー判断 2026-11-17: 両 OS 共通の文言（案 A）・ヒントは両 OS に合う例**）。

- 変更は文言のカタログ（`keyseq/shared/i18n/locales/ja.json` / `en.json`）と、その文言をそのまま比べているテストだけ。コードの分岐は足さない（application 層の `keymap_switch_batch.py:36` も同じキーのまま）。
- 割り当て禁止の判定（`domain/key_identifiers.py` の `PROHIBITED_ASSIGN_KEY_NAMES` = Windows 系・Command 系・Caps Lock・AltGr・fn）は変えない。

## 対象範囲（文言とテストのみ）

### `keyseq/shared/i18n/locales/ja.json`

| キー | 今 | 新 |
|---|---|---|
| `keymap_panel.mapping.prohibited_source`（:561） | Windowsキー・Caps Lock・AltGrは置換元キーにできません。 | Windowsキー・Commandキー・Caps Lock・AltGr・fnは置換元キーにできません。 |
| `keymap_panel.switch_key.prohibited`（:582） | Windowsキー・Caps Lock・AltGrは切替キーにできません:\n{key} | Windowsキー・Commandキー・Caps Lock・AltGr・fnは切替キーにできません:\n{key} |
| `application.keymap_switch_batch.prohibited`（:834） | 同上 | 同上 |
| `preset_dialog.hint`（:719） | 例: 内容: windows+d / ラベル: Win+D（ラベルは重複禁止） | 例: 内容: ctrl+c / ラベル: Ctrl+C（ラベルは重複禁止） |

### `keyseq/shared/i18n/locales/en.json`（同じキー・同じ行）

| キー | 新 |
|---|---|
| `keymap_panel.mapping.prohibited_source` | Windows key, Command key, Caps Lock, AltGr, and fn cannot be Source Keys. |
| `keymap_panel.switch_key.prohibited` | Windows key, Command key, Caps Lock, AltGr, and fn cannot be Switch Keys:\n{key} |
| `application.keymap_switch_batch.prohibited` | 同上 |
| `preset_dialog.hint` | Example: Contents: ctrl+c / Label: Ctrl+C (labels must be unique) |

### テスト

- 文言を直接比べている `tests/test_keymap_switch_batch.py:38`・`tests_ui/test_prohibited_assign_keys_ui.py:191` を新しい文言に直す（判定の検査の意味は変えない）。ほかに文言を比べているテストがあれば同じく直す（`grep -rn "Windowsキー\|Windows key, Caps\|windows+d\|Win+D" tests tests_ui`）。

### 文書（メイン）

- 暫定 57 §5.3.4 の「割り当て禁止の文言の Mac 向けの言い換えは task_11 のまま」を、決めた文言（両 OS 共通・task_11d）に書き換える（v0.20・ユーザー承認が前提）。正本 `features.md` §4.6 の文言の更新は task_14（正本反映）で行う（暫定 57 §11 の正本の項目どおり）。

## 読むファイル

- `keyseq/shared/i18n/locales/ja.json:555-590`・`:715-722`・`:830-836`、`en.json` の同じ行
- `instructions/common/spec_detail/ui_terms.md`（英語の表記規則 E1〜E7・キー名の書き方）
- `tests/test_keymap_switch_batch.py:30-45`・`tests_ui/test_prohibited_assign_keys_ui.py:180-195`

## 含まない

- 割り当て禁止の判定・禁止の色の表示（変えない）
- OS ごとに文言を切り替える仕組み（案 B・採らない）
- 正本 `features.md` §4.6 の更新（task_14）

## 確認

- Mac: compileall clean / `-m unittest discover -s tests` が基準線どおり（2131 件前後・失敗 1）/ tests_ui `test_prohibited_assign_keys_ui`・`test_preset_manager_i18n`・`test_task06_keymap_management_ui`・`test_help_window` が失敗 0 / smoke pass。
- `tests/test_i18n*`（ja / en のキーの揃い・プレースホルダ `{key}` の揃い）が pass。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視（Mac・本タスクで実施）: ①キーボードUIで Command の枠に置換元を割り当てようとすると新しい文言が出る ②切替キーに Caps Lock を記録すると新しい文言が出る ③プリセットのダイアログのヒントが新しい例になっている。

## 起票レビュー（reviewer「修正して採用」2026-11-17）の反映 — 上の記述に優先する

- **M1・M2（ヘルプ本文を含める・ユーザー判断 2026-11-17）**: `keyseq/presentation/help/content/help_ja.json` / `help_en.json` の割り当て禁止の説明も直す（対象範囲に追加・暫定 57 v0.20）。
  - `help_ja.json:215`: 「対象はWindowsキー（左右）・Commandキー（左右）・Caps Lock・AltGr配列の右Alt・fnで、置換元キーと切替キーにできません。Windowsキー・Caps Lockは押さえ込んでもOS側の動作が止まらず、置き換えたキーと本来の機能が両方動いてしまうためです。CommandキーはOSのショートカットを守るため、fnはアプリが受け取れないためです。」
  - `help_ja.json:782`（title）: 「Windowsキー・Commandキー・Caps Lock・AltGr・fn」
  - `help_ja.json:786`: 「Windowsキー（左右）・Commandキー（左右）・Caps Lock・AltGr配列の右Alt・fnは、置換元キーと切替キーにできません。AltGr配列の右Altは、アプリが押さえ込めずにOSへ通ることがあります。」
  - `help_en.json:122`: "These are the Windows keys (left and right), the Command keys (left and right), Caps Lock, the right Alt key on an AltGr layout, and fn. They cannot be Source Keys or Switch Keys. Suppressing the Windows keys or Caps Lock does not stop their OS behavior, so both the remapped key and the original function would run. The Command keys are excluded to protect OS shortcuts, and fn cannot be received by the app."
  - `help_en.json:434`（title）: "Windows key, Command key, Caps Lock, AltGr, and fn"
  - `help_en.json:435`: "The Windows keys (left and right), the Command keys (left and right), Caps Lock, the right Alt key on an AltGr layout, and fn cannot be Source Keys or Switch Keys. The app may be unable to suppress the right Alt key on an AltGr layout, so it may reach the OS."
  - ヘルプの見出しの id（`limits.forbidden_keys` 等）は変えない。ヘルプの文言を直接比べるテストは無い（reviewer の grep）。ヘルプの静的テスト（目次・リンク・ja / en の揃い）があれば流す。
- **L1（参考）**: `help_ja.json:590` / `help_en.json:331`（Ctrl・Alt・Windowsキーを押している間は素通し）は禁止の文言ではないので本タスクでは変えない（task_14 で拾う）。
- **L2**: `tests/test_domain_config.py:646`・`tests/test_default_profile.py:24`・`tests_ui/test_config_io_characterization_keymap_set_startup.py:69` の `Win+D` / `windows+d` は既定のプリセットのデータ（`default_profile.py:18`）でヒントの文言ではないので変えない。
- **L3**: 英語の表記は E1〜E7 に合う（`fn` は小文字のまま）。

- **完了（2026-11-17）**: verifier pass・reviewer 採用・Mac 目視 3・4 OK。1・2 は Mac で画面から出す経路がない（Command の枠は禁止の色で編集を始めない・Caps Lock は記録で受け取れない）ため、文言を比べるテストで代える（ユーザー判断）。
