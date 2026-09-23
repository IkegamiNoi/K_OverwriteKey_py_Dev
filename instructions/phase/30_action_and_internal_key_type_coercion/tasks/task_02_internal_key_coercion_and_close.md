# task_02_internal_key_coercion_and_close

## 目的

runtime 専用の内部キーのうち**パス系 3 種**（`_keymap_source_path` / `_sequence_source_path` /
`_trigger_set_source_path`・正本 §5.8.2）を、読込時の入口 `ensure_config_compatibility` で
§5.1「型不正の共通規則」に従わせる（idea_28）。正本 §5.7 は「本節の規定が正であり、実装側を追従させる」と
既に定めているため**実装修正が既定**で、正本側は ※ 注記の書き換えのみ。
続けて**フェーズの締め**（正本反映・記録・idea クローズ・`/refactor_check`）を行う。

**domain 限定（`keyseq/domain/config.py`）・application / presentation 不変・JSON スキーマ不変**。

## 棚卸し結果（2026-09-23・メイン直読み。phase.md「起票時の調査」#6）

入口外から非文字列・repr が入る経路は**無い**。**直接改訂モードを継続**する。

| 書き手 | 書く値 | 判定 |
|---|---|---|
| `split_loading.py:312-314`（trigger_set）/ `:396,424`（keymap）/ `:482,492-496`（sequence） | `coerce_label` 済みのパス（phase 25） | 安全 |
| `save_plan_execution.py:290-316` | 保存計画で算出したパス（`str(item["path"])`） | 安全（算出元の内部キーが入口で正規化されれば repr は生じない） |
| `config_service/__init__.py:135,180,199,232` | 呼び出し元が渡したパス / 保存先から算出したパス | 安全 |
| `config_service/__init__.py:299` | `build_trigger_set_payloads` が算出した `sequence_items[].path` | 安全（同上） |
| `presentation/controllers/dirty_state.py:22-28` | `str(path or "").strip()`（呼び出し元は `trigger_set_file_io.py` のファイル選択結果） | 安全 |

**生 JSON の値がそのまま runtime に残る唯一の入口** = `ensure_config_compatibility` の
①`triggers[]` の `_sequence_source_path`（`domain/config.py:197-203`）②`keymaps[]` の `_keymap_source_path`（`:277-283`）
③最上位の `_trigger_set_source_path`（`safe_deepcopy(data)` で素通し・`:160`）。

## 対象範囲

### A. 実装（**`codex-implementer` へ委任**）

#### `keyseq/domain/config.py` の `ensure_config_compatibility`

- `triggers[]`: `_sequence_source_path` が**キーとして存在する場合のみ** `coerce_label` を適用する
  （`_sequence_imported` / `_sequence_dirty` は既存どおり `safe_deepcopy` のまま）。
- `keymaps[]`: `_keymap_source_path` が存在する場合のみ `coerce_label`（`_keymap_imported` / `_keymap_dirty` は既存どおり）。
- 最上位: `_trigger_set_source_path` が存在する場合のみ `config["_trigger_set_source_path"] = coerce_label(...)`。
- キーが無い場合は追加しない。

#### `tests/test_domain_config.py`

- `EnsureConfigCompatibilityTest`（または `PathFieldCoercionTest`）へ下記「確認」の項目を追加する。既存テストは変更しない。

### B. 正本反映と締め（**メインセッション**・A の verifier / reviewer 通過後）

1. 正本 `data_schema.md` §5.7 の ※ 注記（`:259-261`「現時点で本規則に追従していない」）を書き換え:
   「runtime 専用の内部キー（`_keymap_source_path` 等・§5.8.2。永続化しない）の**パス値も読込時に本規則に従う**
   （非文字列は空扱い＝未指定と同じ）」。**§5.1 / §5.8.2 の本文は変えない**。
2. `.claude_data/state/decisions_archive/30_action_and_internal_key_type_coercion.md`（新規）: phase 30 の判断を集約
   （`decisions.md` の phase 30 節を移す）+ `decisions.md`「アーカイブ索引」へ 1 行・本文の phase 30 節を削除。
3. `instructions/phase/current.md`: phase 30 を完了記載へ・「直近の一連の作業が扱っている領域」を差し替え・
   次採番は起票時に更新済（31）のため**再変更しない**。
4. `instructions/backlog/INDEX.md` → `INDEX_done.md`: idea_27 / idea_28 を完了状態で**移動**。
5. `phase.md` のタスク一覧を完了へ。
6. `/refactor_check`（メトリクス収集は `verifier`）→ 判定を完了報告へ記載。
7. フェーズ完了判定前レビュー: `deep-reviewer` + `codex-adversarial-reviewer`（`agent_selection.md`）。

### 設計メモ / 制約

- **パスに `coerce_key_name` を使わない**（小文字化でパスが壊れる。§5.7）。
- 内部キー名は domain では**文字列直値**で持つ（既存の `_sequence_source_path` 等と同じ。
  application の `ConfigService.INTERNAL_*` を import しない＝依存方向を守る）。
- **読み手（約 25 箇所）は無修正**。`str(... or "")` の形は入口正規化後の文字列に対して恒等に働く。
- 挙動変更は「非文字列 → `""`」のみ。`None` 等の falsy 値も `""` になるが、読み手はすべて `or ""` で受けるため同値。

## 読むファイル

1. `keyseq/domain/config.py:84-85`（`coerce_label`）/ `:157-311`（`ensure_config_compatibility`・編集対象）
2. `tests/test_domain_config.py:214-440`（`EnsureConfigCompatibilityTest` / `PathFieldCoercionTest`・手本と追加先）
3. 正本 `instructions/common/spec_detail/data_schema.md` §5.7（`:244-268`）/
   `instructions/common/spec_detail/data_schema/5_08_02_runtime_internal_keys.md`
4. B のみ: `.claude_data/state/decisions_archive/25_path_field_type_normalization.md`（書式の手本）

## 含まない

- 読み手の書き換え（`save_path_resolution.py` / `split_payloads.py` / presentation `config_io/*` 等）
- 内部キーのうちパス以外（`_*_imported` / `_*_dirty` / `_*_parent_refs`）
- 書き手の `str(...)` の書き換え（算出値を受けており入口外の混入経路ではない）
- `startup_io.py` の `keymap_set_path`（presentation 層・current.md「別タスク化候補」で追跡中）
- 空 / 未知の `type` の挙動変更（idea_35）
- `codebase_map.md` の更新（関数の責務は変わらない。B-6 の結果で必要になった場合のみ）

## 確認

- 追加する単体テスト:
  1. `_sequence_source_path` / `_keymap_source_path` / `_trigger_set_source_path` がそれぞれ非文字列
     （`None` / `0` / `False` / `[]` / `{}` / `123` / `["a"]` / `{"a": 1}`）→ `""`
  2. 3 種とも文字列は trim され、**大文字小文字と区切り文字を保持**（`"  User/KeyMaps/A.json "` → `"User/KeyMaps/A.json"`）
  3. 3 種ともキーが無い場合に追加されない
  4. `_sequence_dirty` / `_keymap_dirty` 等の非パス内部キーは従来どおり値が保持される（既存 `test_trigger_internal_keys_preserved` と同型）
- 実測（`verifier`・`.venv` python）:
  - `compileall -q keyseq main.py tests tests_ui` clean
  - `-m unittest discover -s tests` 全 pass（件数は追加分だけ増えること）
  - `-m unittest discover -s tests_ui` 全 pass
  - `-m tests.smoke_app` pass
- `git diff -- keyseq` が `keyseq/domain/config.py` の `ensure_config_compatibility` 内のみであること
- B: 正本・記録ファイルのリンク切れがないこと（相対リンクの実在確認）

## 完了条件

- A: 上記確認 pass・**reviewer 採用**。
- B: 正本反映・記録・idea クローズ・`/refactor_check` 判定を実施し、フェーズ完了判定前レビュー
  （`deep-reviewer` + `codex-adversarial-reviewer`）の指摘をユーザー確認のうえ反映。
- 実機目視は**不要**（内部キーは永続化されず、手編集の単一 JSON でのみ非文字列が入る経路。単体テストで固定する）。
