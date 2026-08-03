# task_20_individual_load_stored_path_relative

## 目的

個別「読込」（keymap / 出力シーケンス / トリガー一覧）で選んだファイルの `source_path` が
**config 配下でも絶対表記のまま** runtime へ入る乖離を解消し、保存経路（task_19）と揃えて
**config 相対へ統一**する（正本 `spec_detail/data_schema.md` **§5.7**）。

task_19 で個別「保存」3 経路を統一したが、**対になる読込 3 経路が未追従**のため表記が混在している
（フェーズ完了レビューで `codex-adversarial-reviewer` / `deep-reviewer` の両方が検出。
ユーザー選択 2026-08-03 = **後続送りではなく今直す**）。

レイヤ制約: **application（`config_service.py`）+ presentation（`config_io/` の 3 コントローラ）**。
**domain 不変・スキーマ不変・保存される JSON のバイト列は不変**（記録表記の統一のみ）。

**アクセスできる場所は変わらない**: config 外のファイルは**絶対のまま**記録する
（相対では表現できないため）。読み込み動作そのものはダイアログが返す絶対パスで行うので、
config 外・非既定サブフォルダのいずれからも従来どおり読める。

## 対象範囲

### 1. `keyseq/application/config_service.py` — loader が stored 表記を返す

| 関数 | 現状 | 変更 |
|---|---|---|
| `load_keymap_file:115` | `config_root` を受け取らず `INTERNAL_KEYMAP_SOURCE_PATH = path` | **キーワード引数 `config_root: str = ""` を追加**し、`to_config_relative_or_absolute(path, config_root)` の結果を入れる |
| `load_sequence_file:180` | 同上（`INTERNAL_SEQUENCE_SOURCE_PATH = path`） | 同上 |
| `load_trigger_set_file:222` | **すでに `config_root` を受け取っている**。内部で各 sequence の `source_path` を索引値から入れる | 索引由来の sequence source_path も `to_config_relative_or_absolute` を通す（既に相対ならそのまま） |

- **`config_root` が空文字のときは従来どおり生の `path` を保持**する（task_19 と同じガード）。
- 読み込み自体（`repository.load_json(path)`）は**引数のパスをそのまま使う**。変えない。

### 2. `keyseq/presentation/controllers/config_io/` — 呼び出し側

| ファイル | 変更 |
|---|---|
| `keymap_file_io.py:112` | `load_keymap_file(...)` へ `config_root=self._app.config_root` を渡す |
| `sequence_file_io.py:105` | `load_sequence_file(...)` へ `config_root=self._app.config_root` を渡す |
| `trigger_set_file_io.py:151` | `set_trigger_set_source_path(path)` を、`to_config_relative_or_absolute(path, config_root)` の結果に差し替える（`config_root` 空文字なら生の `path`。task_19 の保存側と同じ形） |

### 3. **相対 stored の消費側の洗い出し（必須）**

task_19 で **2 度**、相対になった値を消費側が `os.path.abspath` で cwd 基準に解決してしまう事故が出た
（症状 = リポジトリルートに `user/` が生成される / 「別名で保存」が前回の場所に開かない）。
本タスクでも同じ確認を行うこと。

- `keyseq/` 配下で **読込由来の `source_path` を消費している箇所**を洗い、
  `os.path.abspath` / `os.path.dirname` / `os.path.exists` / `os.path.join` へ
  **解決なしで渡している箇所が無いか**確認する。
- 解決が必要な箇所は `ConfigService.resolve_config_path(path, config_root)` を使う
  （`to_config_relative_or_absolute` は入口で解決するため、そのまま渡してよい）。
- 発見した消費側の不備は本タスクで直し、**回帰テストを添える**。

### 設計メモ / 制約

- **不変条件**: `dirty_tracker.trigger_set_source_path` と `data[INTERNAL_TRIGGER_SET_SOURCE_PATH]` は
  常に一致（入口は `dirty_state` のメソッドのみ）。**内部キーへ直接代入しない**。
- `imported` フラグ・`dirty` フラグ・読込後の UI 更新順序は**変更しない**。
- 既存の `_parent_refs` が絶対で記録済みのファイルを読んでも壊れないこと
  （同一性判定は `canonical_path` を通るため表記非依存）。

## 含まない

- 索引（keymap_set / trigger_set に書かれるパス）の表記変更 → 現状で §5.7 どおり
- 実機の `config/` に絶対で記録済みの `_parent_refs` / 起動設定の**移行処理**（不要と判断済み）
- 個別 IO 3 種の共通化 → [idea_06](../../../backlog/idea_06_individual_json_io_unification.md)（保留）
- `/refactor_check` の提案書（`05_refactor_child_file_save_dialog.md`）の実施 → **未承認**

## 確認

python は**リポジトリルートの `.venv`**（worktree 相対 `../../../.venv/Scripts/python.exe`）を使う。

1. `-m compileall -q keyseq main.py tests_ui` が clean
2. `-m unittest discover -s tests` が全 pass（現状 145 から減らない）
3. `-m unittest discover -s tests_ui` が全 pass（現状 156 から減らない）
4. `-m tests.smoke_app` が pass
5. **追加テスト（受入条件 29）**: 個別読込 3 経路それぞれで
   ① **config 配下**のファイルを読むと `source_path` が **config 相対**表記になる
   ② **config 外**のファイルを読むと **絶対のまま**である
   ③ 読み込んだ内容（triggers / keymap / sequence の中身）が従来と同一
   ④ 読込直後に個別「保存」すると**読込元と同じファイル**へ書かれる（表記が変わっても保存先が変わらない）
6. 追加テストが**変更前の実装では落ちる**こと（①で絶対が返るため）
7. 上記 1〜4 の実行後、**worktree ルートに `user/` ディレクトリが生成されていない**こと

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 正本 `data_schema.md` §5.7 は「**本節は保存経路・読込経路の両方に適用する**」と明記済み
  （後続送りを取りやめた時点で【実装未追従】注記は削除済み。本タスクで追加対応は不要）。
- 実機目視は**不要**（記録表記の統一のみで UI 挙動・保存結果・読める場所は不変）。
