# decisions_archive / phase 36: config_service の分割と巨大関数の分割

対応表: phase 36 / 暫定なし（直接改訂モード）/ decisions 36。
起票元: `current.md`「別タスク化候補 > application / config_service」の 2 項（phase 09〜11 / phase 34 由来）・ユーザー要望（2026-09-26）。
完了 2026-09-27。**挙動不変のリファクタ・JSON スキーマ不変・正本（spec_detail）の改訂なし**。記録先 = `codebase_map.md` の ConfigService 節。

## 確定した設計判断

| # | 判断（ユーザー 2026-09-26） | 採らなかった案と理由 |
|---|---|---|
| 1 | `config_service/__init__.py` から **2 ブロック**を切り出す: 個別キーマップの保存計画一式 → `keymap_save_plan.py` / シーケンス・トリガー一覧ファイルの読み書き → `child_file_io.py` | 保存計画一式のみ = 約 950 行止まり / 3 ブロック = シーケンス正規化・掃除・ID・ディレクトリ（753-864 行）はまとまりが弱く雑多な名前になる |
| 2 | 切り出し先は `service` を第 1 引数に取る module 関数。外から呼ばれるメソッドだけ `ConfigService` に同シグネチャの 1 行委譲を残す（保存計画一式は外部参照 0 のため委譲なし） | — |
| 3 | 80 行超の関数 5 つは**同じファイル内**で補助関数へ分割（1 関数 1 タスク） | — |
| 4 | パス基盤メソッドは動かさない（**理由は後に誤りと判明**・下記「完了判定前レビュー」） | — |

## 結果（task_01〜07）

| タスク | 対象 | 結果 |
|---|---|---|
| task_01 | 保存計画一式 12 メソッド → `keymap_save_plan.py`（229 行） | `__init__.py` 1135 → 932 |
| task_02 | ファイル IO 4 メソッド → `child_file_io.py`（144 行） | `__init__.py` 932 → 840 |
| task_03 | `split_loading.build_runtime_data_from_split` | 154 → 23 行（補助 8 関数） |
| task_04 | `save_plan_execution.save_runtime_data` | 125 → 42 行（補助 5 関数） |
| task_05 | `split_payloads.build_split_save_payloads` | 120 → 41 行（補助 6 関数） |
| task_06 | `config_io/child_save_rows.collect_child_save_rows` | 99 → 30 行（補助 5 関数） |
| task_07 | `domain/config.ensure_config_compatibility` | 158 → 40 行（補助 8 関数・BOM 維持） |

- 各タスク: codex-implementer → verifier（tests 674〔skip 7〕/ tests_ui 576 / smoke 全 pass・件数不変）→ reviewer 完了可。
- task_03 はレビューの参考指摘（補助関数間の状態を文字列キーの `dict[str, Any]` で受け渡し）を**修正して採用**し、`_KeymapLoadState` dataclass にした。
  以降のタスク定義に「文字列キーの状態 dict を使わない」を明記。
- task_04 は `warnings.warn(..., stacklevel=2)` を本体に残した（補助関数へ移すと警告の発生位置が変わるため）。
- task_05 の呼び出し 2 か所の引数の折り返しの詰めは、本体の行数目安のためとして採用（引数は不変）。
- task_07 は `data.get("keymaps")`（deepcopy 前）からの読取と `trigger_memo` の `id(raw)` 共有検出、`keymap_triggers` の関数内 import を維持。

## 完了判定前レビュー

- **deep-reviewer = 完了可**（コード修正不要）。**codex-adversarial-reviewer = approve（指摘なし）**。
- **前提の誤り（deep-reviewer 指摘 1・メインが実測で確認）**: `patch("keyseq.application.config_service.os.path", ntpath)` は
  `config_service` の名前空間ではなく **`os` モジュールの `path` 属性をプロセス全体で**差し替える
  （`posixpath` で差し替えると `os.path` と `keymap_save_plan.os.path` の両方が差し替わることを実測）。
  本当の制約は「`__init__.py` が `os` を import していること」「`from os.path import ...` で事前束縛しないこと」だけ。
  → **ユーザー判断（2026-09-27）= 記述を直して閉じる**。`codebase_map.md`（件数の食い違い 5 箇所 / 4 テストも修正）・phase.md を訂正。
  パス基盤の移動は「別タスク化候補」へ。
  なお Windows では `os.path` が元から `ntpath` のため、この 5 つの patch は実質的に効いていない（参考）。
- 保留として「別タスク化候補」へ送ったもの: 引数の多い位置指定の補助関数（`_append_split_trigger_set_payloads` / `_build_split_trigger_set_entry` 13〜15 個 /
  `_append_trigger_set_row` 13 個）/ `ensure_config_compatibility` の内部キー 4 要素タプル / テストの無い経路
  （`keep_legacy_copy=True`〔本番は常に False〕・`post_save_warnings=None` の警告・アクティブキーマップの補完）。
- 除外: 1 行委譲の行長・`service` の型注釈の不揃い（整形のみ）。

## refactor_check

**推奨 → 提案書 [14](../../../instructions/modified_proposal/14_refactor_config_service_split.md)**（ユーザー 2026-09-27: 提案書を起票）。
- M1: `split_loading.py` 666 → 787（+121・補助関数への分割による増分）→ 項目 1 = ホットキープリセット関連 9 関数（71-297 行）を `hotkey_presets_files.py` へ。
- M2〜M6: 該当なし（verifier 実測・PHASE_BASE = `1b37653`）。`split_payloads.py` の既存 80 行超の 2 関数（`build_keymap_payloads` 100 / `build_trigger_set_payloads` 106）は phase 36 で未変更のため候補送り。
- **実施済**: ユーザー判断（2026-09-27）= phase 36 末の追加タスク → task_09 で実施。9 関数を無変更で `hotkey_presets_files.py`（234 行）へ移し、`split_loading.py` 787 → 559 行。
  呼び出し元の差し替え = `__init__.py` 11 / `orphan_scan.py` 1 / テスト 5（期待値不変）。verifier 全 pass（tests 674・skip 7 / tests_ui 576 / smoke）・reviewer: 移動は無変更と確認・参考指摘（`codebase_map.md` がタスクの対象外で変更）は定義どおりメインの反映分のため問題なし。
