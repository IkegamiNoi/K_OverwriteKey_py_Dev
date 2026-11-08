# task_08b_visual_check_fixes

## 目的

実機目視（task_09・ユーザー 2026-11-08）の指摘を直す（暫定 56 v0.6 §4・§5.1・§7・§10 の 16・17）。
**presentation（Welcome の窓・復元の親）+ 言語ファイル + テスト。domain / application・JSON スキーマ不変**。

## 対象範囲

### 1. 配列の選択をドロップダウンに（§4 の 2）— `keyseq/presentation/welcome/welcome_window.py`

- `_build_layout` のラジオボタンを、Language と同じ読み取り専用の `ttk.Combobox`（`self.layout_combo`）に替える。項目は今の `(("us_tkl", "US TKL"), ("jis", "JIS"))` の表示名。
  選んだ値は今どおり `self.layout_var`（layout_id）に入れる。`<<ComboboxSelected>>` で `_layout_touched = True`
- 言語の追従（触っていなければ推定値へ）と作り直し後の表示（`layout_var` の値の項目が選ばれている）は今のまま
- `self.layout_buttons` は無くなる。テストを Combobox の操作に直す

### 2. 再表示に基本的な使い方とサンプル設定の欄（§7）— `welcome_window.py`

- `reopen=True` のとき: Language → `_build_usage()`（初回と同じ）→ サンプル設定の欄（`_section("sample_settings")` に説明の Label〔`welcome.sample_description`・`wraplength=520`〕と
  ボタン `self.restore_sample_button`〔文言 = `tr_in(self.language, "menu.file.restore_sample")`〕）→ ボタン行。`self.sample_restore_notice` と言語キー `welcome.reopen.sample_restore` は削除
- ボタンの command: `self.master.keymap_set_io.restore_default(parent=self)`。Welcome は閉じない。終わったら Welcome に戻る（grab を Welcome に戻す。`grab_modal` の既存の作法・`modal.py` を確認）
- 新しい言語キー `welcome.sample_settings`（欄の見出し・ja「サンプル設定」/ en「Sample Settings」）を両方の言語ファイルへ

### 3. 復元の確認の親 — `keyseq/presentation/controllers/config_io/keymap_set_io.py`

- `restore_default(self, parent=None)` と `confirm_save_if_dirty(self, action_name, parent=None)`: `parent` があれば `messagebox.askyesnocancel` / `askyesno` に `parent=parent` を渡す。
  無ければ今と同じ（メニューからの呼び出しの挙動を変えない）
- 未保存の確認で「はい」（保存）を選んだ経路の保存処理のダイアログの親までは変えない（範囲外。報告のみ）

### 4. 文言（§4・§5.1）— `keyseq/shared/i18n/locales/ja.json` / `en.json`

- ja `welcome.sample_description`: 半角の空白を除く → 「数字キーで3つのキーマップ（ショートカット・右手側の文字・テンキー）を切り替えます。まず「開始（フックON）」を押し、メモ帳などで試してください。F1で一時停止/再開、F12でフックを止めます。右手側の文字とテンキーではhで案内を入力します。」
- ja の `welcome.*` の他の折り返す文にも半角の空白があれば同様に除く（`welcome.sample_failed.body` は改行入りの別ダイアログなので対象外）
- ja `sample.guide.right_hand` / `sample.guide.numpad`: 「割り当てはキーボード表示で確かめられます。」→「割り当ては「表示」の欄の「キーボードUI」で確かめられます。」
- en `sample.guide.right_hand` / `sample.guide.numpad`: 「Check the assignments in the Keyboard UI.」→「Check the assignments with “Keyboard UI” in the “Display” section.」（引用符は en.json の既存の “ ” に合わせる）

### 設計メモ / 制約

- 初回の Welcome の構成・結果（`WelcomeResult`）・言語の扱い（再表示は閉じたときに `set_ui_language`）は変えない
- ソースに日本語の文言を書かない。テストの期待値を緩めない
- 表示名 `US TKL` / `JIS` は今どおりソースの固定値でよい（言語に依らない名前）

## 読むファイル

- `keyseq/presentation/welcome/welcome_window.py`（全体・小さい）・`keyseq/presentation/welcome/first_launch.py`
- `keyseq/presentation/controllers/config_io/keymap_set_io.py:40-60`・`:675-705`
- `keyseq/presentation/modal.py`（`grab_modal` とネストの扱いの部分のみ）
- `tests_ui/test_welcome_window.py`（全体）・`tests_ui/test_config_io_characterization_keymap_set_startup.py` の `restore_default` のテスト 1 つ
- `tests/test_sample_config.py` のうち案内文の文言を見るテストがあればその部分
- 言語ファイルは上記キーの行のみ

## 含まない

- 再表示の言語の確認のタイミングの変更（ユーザー判断で今のまま）
- 正本の更新・暫定 56 の凍結（task_09）
- 保存のダイアログの親の変更

## 確認

- tests_ui: 配列の Combobox の初期値（ja = JIS / en = US TKL）・言語の追従・触った後に追従しない・閉じる経路で `WelcomeResult` に Combobox の値が入る（既存のテストを Combobox 版に直す）
- tests_ui: 再表示に `usage_section` と `restore_sample_button` があり、`layout_section` / `start_section` が無い。ボタンで `keymap_set_io.restore_default(parent=window)` が呼ばれ Welcome が開いたまま（モック可）
- tests_ui: `restore_default(parent=x)` で確認の messagebox に `parent=x` が渡る・`parent` なしは今どおり
- tests: ja の `welcome.sample_description` に半角の空白が無い・`sample.guide.*` が `view.display.title` と `view.display.keyboard_ui` の文言を含む（ja / en）
- `python -m compileall -q keyseq`・`python -m unittest discover -s tests`・`python -m unittest discover -s tests_ui`・`python -m tests.smoke_app` が通る（verifier が `.venv` で実行）

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視は task_09 で再確認（ドロップダウン・折り返し・再表示の欄とボタン）
