# phase.md

## フェーズ名

個別 sequence JSON 単体読込の actions 正規化（sequence_payload_action_normalization）

## フェーズの目的

個別 sequence JSON を単体で読み込む経路にも `actions[]` の要素正規化（dict 以外の除去 +
`label` 整形）を適用し、正本 `data_schema.md` §5.11 の規定へ**実装を追従**させる。
**正規化ロジックは domain 側へ関数として切り出して共有**し、application が整形規則を
二重に持たないようにする（idea_24 の案 A）。

- 起票元: [idea_24](../../backlog/idea_24_sequence_payload_action_normalization.md)
  （phase 22 完了判定前 deep-reviewer 指摘 3・2026-09-19）。
- 主入力（暫定仕様）: なし（直接改訂モード）。
- モード: **直接改訂モード**。番号対応: phase 23 / decisions 23。
  **正本の規定 §5.11 は変更しない**（変更は【実装未追従】注記の削除のみ）。

## 確定（ユーザー 2026-09-19）

- idea_24 の**案 A** を採る（案 B = 個別読込も `ensure_config_compatibility` を通す、は採らない）。
- 正本 §5.11「dict 以外の要素は除去する」が正。実装側を追従させる。
- 挙動変更が生じる（従来は読込後の一覧表示で `AttributeError` になっていた入力が、
  非 dict 要素を捨てて読めるようになる）ことを許容する。

## スコープ

### 含む

- `keyseq/domain/config.py`: `ensure_config_compatibility` 内の actions 正規化ループを
  公開関数（例 `normalize_actions`）へ切り出し、同関数から呼ぶ（挙動同値）。
- `keyseq/application/config_service/__init__.py`: `_normalize_sequence_payload` の `actions`
  を `safe_deepcopy` のみから上記共有関数の呼び出しへ置き換える。
- 上記に対応する単体テスト（`tests/`）の追加。
- 正本 `data_schema.md` §5.11 の【実装未追従】注記の削除。

### 含まない（後送り）

- `actions[]` 要素のスキーマ拡張（キー追加・型厳格化）。
- keymap / trigger_set など**他の個別 JSON 読込経路**の正規化見直し。
- UI・ダイアログの変更。`format_action_list_item` 等の表示整形の変更。
- `split_loading.py` のインライン trigger 側の経路変更（`ensure_config_compatibility` を
  通るため既に規定どおり）。

## このフェーズで読むファイル

1. `instructions/common/spec_detail/data_schema.md` §5.11（規定・追従先）
2. `keyseq/domain/config.py`（`ensure_config_compatibility` の actions 正規化ループ / `safe_deepcopy`）
3. `keyseq/application/config_service/__init__.py`（`_normalize_sequence_payload` / `load_sequence_file` / `save_sequence_file`）
4. `keyseq/application/config_service/split_loading.py`（`_normalize_sequence_payload` の呼び出し元・二重正規化の確認）
5. `tests/test_config_service.py`（`load_sequence_file` の既存テスト）

## タスク

- task_01: domain へ actions 正規化関数を切り出し、sequence 単体読込へ適用する（+ 単体テスト）
- task_02: 正本反映と記録（§5.11 の【実装未追従】注記削除 / decisions_archive/23 /
  current.md / backlog INDEX → INDEX_done / `/refactor_check`）

## レビュー方針

- 共通観点は `.claude/rules/review.md`。
- **本フェーズ固有**:
  - 切り出した関数が `ensure_config_compatibility` 経由の既存挙動を変えていないか（挙動同値の確認）。
  - `_normalize_sequence_payload` が domain の規則を**再実装していない**か（二重定義の禁止）。
  - `save_sequence_file` も同じ関数を通るため、保存直後の戻り値の形が変わっていないか。
  - 依存方向（application → domain のみ。逆流がないこと）。
