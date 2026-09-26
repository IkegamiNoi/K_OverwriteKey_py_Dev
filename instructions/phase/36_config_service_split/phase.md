# phase.md

## フェーズ名

config_service の分割と巨大関数の分割（config_service_split）

## フェーズの目的

phase 34 までに肥大化した保存・読込まわりを、**挙動を変えずに**分割する。

- `keyseq/application/config_service/__init__.py`（**1135 行**）から 2 つのまとまりを同パッケージの新モジュールへ切り出す。
- 80 行超の関数 5 つを、同じファイル内で内部ブロックごとの補助関数へ分ける。

**挙動不変のリファクタ・JSON スキーマ不変・正本（spec_detail）の改訂なし**。対象レイヤ = application（config_service）/ domain（`config.py`）/
presentation（`config_io/child_save_rows.py`）。公開面（`ConfigService` のメソッド名・シグネチャ・`contracts`）は変えない。

- 起票元: `current.md`「別タスク化候補 > application / config_service」の 2 項（phase 09〜11 / phase 34 由来）・ユーザー要望（2026-09-26）。
- 主入力（暫定仕様）: なし（直接改訂モード。正本の改訂も無い）。
- モード: **直接改訂モード**。番号対応: phase 36 / 暫定 なし / decisions 36。

## 確定（ユーザー 2026-09-26）

- `__init__.py` から切り出すのは **2 ブロック**:
  1. 個別キーマップの保存計画一式（`_save_keymap_with_plan` 〜 `_apply_saved_keymap_state`・`__init__.py:265-461`・約 197 行）→ 新モジュール `keymap_save_plan.py`
  2. シーケンス / トリガー一覧ファイルの読み書き（`load_sequence_file` / `save_sequence_file` / `load_trigger_set_file` / `save_trigger_set_file`・`__init__.py:463-591`・約 129 行）→ 新モジュール `child_file_io.py`
  - 見込み: 1135 → 約 850 行。
- 切り出し先は既存の `save_plan_execution.py` 等と同じ形（`service` を第 1 引数に取る module 関数）。`ConfigService` には**外から呼ばれるメソッドだけ 1 行委譲として残す**。
- **パス基盤のメソッド（`canonical_path` / `is_path_within` / 親参照ヘルパ等・`__init__.py:1017-1121` 付近）は動かさない**。
  テスト 5 箇所が `patch("keyseq.application.config_service.os.path", ntpath)` で名前空間を差し替えるため
  （`tests/test_config_service.py:739, 2259, 2630` / `tests/test_config_paths.py:113` / `tests/test_child_save_rows.py:288`）。
- 公開面の検査テスト（`tests/test_config_service_contracts.py:14` の `INTERNAL_MODULE_NAMES`）へ新モジュール名 2 つを足す（テスト側の必要な追随）。
- 80 行超の関数 5 つは**同じファイル内**で補助関数へ分ける（1 関数 1 タスク・新ファイルなし）。
- 採らなかった案: 保存計画一式のみ（約 950 行に留まる）/ 3 ブロック（シーケンスの正規化・掃除・ID・ディレクトリ〔753-864 行〕はまとまりが弱く、雑多な名前のモジュールになりやすい）。

## スコープ

### 含む

- 上記 2 ブロックの切り出しと `ConfigService` 側の委譲化・`INTERNAL_MODULE_NAMES` への追加。
- 80 行超の関数 5 つの分割（行数は 2026-09-26 実測）:
  `split_loading.py::build_runtime_data_from_split`（154 行）/ `save_plan_execution.py::save_runtime_data`（125）/
  `split_payloads.py::build_split_save_payloads`（120）/ `config_io/child_save_rows.py::collect_child_save_rows`（99）/
  `domain/config.py::ensure_config_compatibility`（158）。
- `codebase_map.md` の該当節の追随（新モジュールの記載）。

### 含まない（後送り・触らない）

- パス基盤メソッドの移動・`os.path` の patch を使うテストの書き換え。
- `__init__.py` のその他のまとまり（起動時ロード・個別キーマップ読込・シーケンス正規化・ホットキープリセット等）。
- 挙動の変更・バグ修正（見つけたら作業を止めて報告し、別タスク化候補へ）。
- phase 34 統合レビュー保留の L-1 / L-7。

## このフェーズで読むファイル

1. `keyseq/application/config_service/__init__.py:1-62`（import・定数）/ `:134-591`（切り出し対象と呼び出し元）
2. `keyseq/application/config_service/save_plan_execution.py:1-40`（既存の切り出し先の書き方の手本）
3. `tests/test_config_service_contracts.py:1-20`（`INTERNAL_MODULE_NAMES`）
4. 関数分割の各タスクでは、その関数と同ファイル内の呼び出し先のみ（タスク定義で行範囲を指定）
5. `instructions/common/codebase_map.md` の config_service 節（task_08 で追随）

## タスク

- task_01: 個別キーマップの保存計画一式を `keymap_save_plan.py` へ切り出す — **完了**（2026-09-26・1135 → 932 行・tests 674〔skip 7〕/ tests_ui 576 / smoke pass・reviewer 完了可）
- task_02: シーケンス / トリガー一覧ファイルの読み書きを `child_file_io.py` へ切り出す — **完了**（2026-09-26・932 → 840 行・tests 674〔skip 7〕/ tests_ui 576 / smoke pass・reviewer 完了可）
- task_03: `split_loading.py::build_runtime_data_from_split` の分割 — **完了**（2026-09-26・本体 154 → 23 行・補助 8 関数 + `_KeymapLoadState`〔レビュー後に状態 dict を型付き dataclass へ〕・tests 674 / tests_ui 576 / smoke pass・reviewer 完了可）
- task_04: `save_plan_execution.py::save_runtime_data` の分割 — **完了**（2026-09-26・本体 125 → 42 行・補助 5 関数・tests 674 / tests_ui 576 / smoke pass・reviewer 完了可）
- task_05: `split_payloads.py::build_split_save_payloads` の分割
- task_06: `config_io/child_save_rows.py::collect_child_save_rows` の分割
- task_07: `domain/config.py::ensure_config_compatibility` の分割
- task_08: 記録（`codebase_map.md` の追随 / decisions_archive/36 / current.md〔完了記載・「別タスク化候補」の 2 項を更新〕/ `/refactor_check`）

各タスク = codex-implementer（テスト実行なし）→ verifier（compile / tests / tests_ui / smoke）→ reviewer。

## レビュー方針

- 共通観点は `.claude/rules/review.md`。
- **本フェーズ固有**:
  - **挙動不変**: 処理の順序・例外の扱い・戻り値・副作用（書込み順・dirty フラグの更新順）が変わっていないか。
    既存テストの期待値を変えていないか（変えてよいのは `INTERNAL_MODULE_NAMES` への追加のみ）。
  - **patch 対象の維持**: `config_service.os.path` の差し替えが効くべきメソッドを `__init__.py` から動かしていないか。
    他のテストが patch している名前空間（`patch.object` 含む）が移動で外れていないか。
    切り出すブロック 1 にも `os.path.abspath`（`__init__.py:276`）があるため、新モジュールでは `import os` + `os.path.xxx` の
    ドット記法を保ち、`from os.path import ...` で事前束縛しない（起票時レビューの参考指摘）。
  - **公開面**: `ConfigService` の公開メソッド名・シグネチャが不変か。presentation から新モジュールを直接 import していないか（contracts テストで検出）。
  - **依存方向**: 新モジュールが `__init__.py`（ConfigService）を import していないか（循環）。
  - 関数分割: 補助関数がおおむね 30 行目安に収まり、分割後の本体が処理の流れとして読めるか。無関係な整形・改名を含めていないか。
