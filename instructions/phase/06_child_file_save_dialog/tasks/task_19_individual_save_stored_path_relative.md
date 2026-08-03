# task_19_individual_save_stored_path_relative

## 目的

個別保存（keymap / sequence / trigger_set）の直後だけ、runtime が保持する `source_path` が
**config 配下でも絶対パス**になる乖離を解消し、**全経路で config 相対に統一**する
（正本 `spec_detail/data_schema.md` **§5.7**）。

現状: ファイルダイアログが返す絶対パスが `stored` としてそのまま runtime へ入る
（`config_service.save_keymap_file:152-153` / `save_sequence_file:197-198` /
`trigger_set_file_io.save_trigger_set_to_path:62`）。読込・一括保存の経路は相対で入るため**表記が混在**し、
過去に「絶対で記録 → config 内外判定が外れる」事故（v0.3-B）の起点になった箇所でもある。
**永続化される JSON は現状でも §5.7 どおり相対**なので、直すのは runtime の表記のみ。

レイヤ制約: **application（`config_service.py`）+ presentation（`trigger_set_file_io.py`）**。
**domain 不変・スキーマ不変・保存される JSON のバイト列は不変**（＝挙動変更ではなく表記の統一）。

判断根拠: Codex のフェーズ完了レビュー（2026-08-03・medium）→ **実装を直す**をユーザーが選択
（対案「正本の文言を v0.5-J へ弱めて混在を許容」は不採用）。

## 対象範囲

### 1. `keyseq/application/config_service.py` — stored を正規化して返す

| 関数 | 現状 | 変更 |
|---|---|---|
| `save_keymap_file:144` | `stored_path = path`（呼び出し元の表記のまま） | `stored_path = self.to_config_relative_or_absolute(resolved_path, config_root)` |
| `save_sequence_file:189` | 同上 | 同上 |

- `resolved_path`（書き込み用の絶対パス）の算出と `repository.save_json` への受け渡しは**変更しない**
  （stored と resolved の分離は維持したまま、stored の表記だけ正規化する）。
- **config の外を選んだ場合は絶対のまま**返る（`to_config_relative_or_absolute` の既定動作＝ §5.7 どおり）。
- `config_root` が空文字で渡る呼び出しがある場合の挙動を**現状から変えない**こと
  （空なら正規化できないため `path` のままでよい。既存の `_resolve_config_relative_path` の扱いに合わせる）。

### 2. `keyseq/presentation/controllers/config_io/trigger_set_file_io.py` — tracker へ入れる値を正規化

`save_trigger_set_to_path:62` の `set_trigger_set_source_path(path)` を、
**`config_service.to_config_relative_or_absolute(path, self._app.config_root)` の結果**に差し替える。

- `save_trigger_set_file` へ渡す `path` は**そのまま**（内部で resolved 化される）。
- `previous_source_path` との比較は `canonical_path` 経由なので**表記に依存せず**、変更不要。
- 完了メッセージ・`showinfo` に出すパス（`info_message`）は**ユーザー向け表示なので現状のまま**でよい。
- trigger_set 配下の各 sequence の `source_path` は `_build_trigger_set_payloads` が既に
  正規化済みの値を返しているため**変更不要**（`config_service.py:1177-1182`）。

### 3. 実装中に判明した根本原因への対応（**当初の対象範囲外・実施済み**）

1 の変更だけでは**既存テスト 5 件が落ち、worktree ルートに `user/` が生成**された
（暫定仕様 v0.5-J で直した「相対を cwd 基準で書く」症状の再発）。原因は共有ヘルパ側にあったため、
以下も本タスクに含めた。

| ファイル | 変更 |
|---|---|
| `config_service.to_config_relative_or_absolute` | 入口で `_resolve_config_relative_path(path, config_root)` を通してから `abspath` する。**この関数は入力が「絶対 or cwd 相対」前提**で、config 相対を渡すと cwd 基準の絶対パスへ化けていた |
| `config_service._merge_parent_ref` | 正規化前に挟んでいた `os.path.abspath(parent_path)` を削除（同じ症状で `_parent_refs` が汚染された） |
| `config_service.resolve_config_path`（新規・公開） | 記録用の表記を書き込み・存在確認に使える形へ解決する薄いラッパ |
| `presentation/config_paths.json_dialog_initial_dir` | source_path を `resolve_config_path` で解決してから `dirname` / `isdir` する（相対 stored だと「前回保存した場所」に開かず既定へフォールバックしていた） |

**絶対パスを渡す既存呼び出し（`keyseq/` 配下に約 21 箇所）は挙動不変**
（`_resolve_config_relative_path` は絶対パスをそのまま返すため）。

### 設計メモ / 制約

- **不変条件**: `dirty_tracker.trigger_set_source_path` と `data[INTERNAL_TRIGGER_SET_SOURCE_PATH]` は
  常に一致（入口は `dirty_state` の 2 メソッドのみ）。正規化した値を入口へ渡すこと。
  **内部キーへ直接代入しない**。
- **パス同一性の判定に表記を持ち込まない**。今回の変更で比較ロジックを増やさない
  （比較は `canonical_path` / `is_path_within` を使う。`_sequence_save_path_changed` だけは
  両オペランドとも解決済み絶対パスでの `normcase` 比較で、実質同値）。
- 保存される JSON の内容は**一切変わらない**。既存のバイト列比較テストは無修正で pass するはず。

## 含まない

- 索引（keymap_set / trigger_set に書かれるパス）の表記変更 → **現状で §5.7 どおり**。触らない
- 実機の `config/` に絶対パスで既に記録済みの `_parent_refs` / 起動設定の**移行処理**
  （申し送り④＝不要と判断済み）
- `keymap_file_io.py` / `sequence_file_io.py` の変更（1 の戻り値を使うだけで自動的に相対になる。
  **この 2 ファイルに差分が出る場合は設計を見直す**）
- 個別保存 3 経路の共通化 → [idea_06](../../../backlog/idea_06_individual_json_io_unification.md)（保留）
- `/refactor_check` の提案書（`05_refactor_child_file_save_dialog.md`）の実施 → **未承認**

## 確認

python は**リポジトリルートの `.venv`**（worktree 相対 `../../../.venv/Scripts/python.exe`）を使う。

1. `-m compileall -q keyseq main.py tests_ui` が clean
2. `-m unittest discover -s tests` が全 pass（現状 144 から減らない）
3. `-m unittest discover -s tests_ui` が全 pass（現状 153 + 追加分）
4. `-m tests.smoke_app` が pass
5. **追加テスト（受入条件 28）**: 個別保存 3 経路それぞれで、**config 配下の絶対パス**を保存先に指定したとき
   ① runtime / tracker の `source_path` が**config 相対表記**になる
   ② 実際に書き込まれたファイルが**指定した絶対パスの位置**にある
   ③ 保存された JSON のバイト列が変更前と同一
   ④ **config の外**を指定した場合は `source_path` が**絶対のまま**である
6. 追加テストが**変更前の実装では落ちる**こと（①で絶対が返るため）

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は**不要**（表記の統一のみで UI 挙動・保存結果は不変）。ただし完了後に
  **task_10 の完了判定をやり直す**（deep-reviewer / Codex のフェーズ完了レビューを再実施し、
  §5.7 と実装の整合を確認する）。
