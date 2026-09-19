# task_01_shared_action_normalization

## 目的

正本 `data_schema.md` §5.11 の規定「`actions[]` の要素は dict とし、dict 以外の要素は除去する」に
実装を追従させる。現在 `ensure_config_compatibility` の内部にある actions 正規化ループを
**domain の公開関数へ切り出し**、個別 sequence JSON 単体読込経路
（`ConfigService._normalize_sequence_payload`）からも同じ関数を呼ぶ（idea_24 の案 A）。

レイヤ制約: **domain / application 限定**。presentation 不変・**JSON スキーマ不変**
（新キーの追加・既存キーの意味変更をしない）。

## 対象範囲（domain + application 限定・関数切り出しと呼び替えのみ）

### keyseq/domain/config.py

- `ensure_config_compatibility` 内（現 `175-185` 行）の actions 正規化ループを、
  モジュールレベルの公開関数として切り出す。

  ```python
  def normalize_actions(actions: Any) -> list[dict[str, Any]]:
  ```

  - 引数が `list` でなければ空リストを返す。
  - 要素が `dict` でなければ除去する。
  - `dict` 要素は `safe_deepcopy` したうえで `a["label"] = (a.get("label") or "").strip()` を設定する。
  - **挙動は現在のループと同値**にする（判定順・整形内容を変えない）。
- `ensure_config_compatibility` は該当ループを削除し、`t["actions"] = normalize_actions(t.get("actions"))`
  へ置き換える。
- 他の整形（`key` / `label` / `suppress` / `run_to_end` / `run_to_end_delay_ms`）には触らない。

### keyseq/application/config_service/__init__.py

- `_normalize_sequence_payload`（現 `454-465` 行）の `"actions"` の値を、
  `safe_deepcopy(...) if isinstance(...) else []` から `normalize_actions(sequence.get("actions"))` へ置き換える。
- import 文（現 `7-15` 行の `from keyseq.domain.config import (...)`）へ `normalize_actions` を追加する。
  **application 側で正規化規則を再実装しない**（domain の関数を呼ぶだけ）。
- 同関数の他のキー（`label` / `run_to_end` / `run_to_end_delay_ms`）は変更しない。

### tests/test_domain_config.py

- `normalize_actions` の単体テストを追加する（下記「確認」の項目 1〜4）。

### tests/test_config_service.py

- `SequenceFileIoTest`（現 `1718` 行〜）に、非 dict 要素を含む sequence JSON を
  `load_sequence_file` した際に除去されることのテストを追加する。
- **既存テストの期待値更新**: `1737` 行の
  `self.assertEqual(loaded["actions"], [{"type": "hotkey", "value": "ctrl+c"}])` は、
  共有関数を通すことで `label` が付与され `[{"type": "hotkey", "value": "ctrl+c", "label": ""}]`
  になる。**これは意図した追従**（`ensure_config_compatibility` 経由の既存経路と同じ形になる。
  `tests/test_domain_config.py:182` が同じ形を期待している）ため、期待値側を更新する。

### 設計メモ / 制約

- `_normalize_sequence_payload` は `load_sequence_file` / `save_sequence_file` /
  `split_loading.py:485` の 3 箇所から呼ばれる。`split_loading` 側は後段で
  `ensure_config_compatibility` を通る（`split_loading.py:498`）ため、**二重に正規化されても結果は同値**
  であることを確認する（冪等）。冪等でない実装にしない。
- `label` 付与は §5.11 の「`label` は一覧表示用の任意の文字列」と整合し、
  §5.1 の「既存キーを能動削除しない」にも反しない（追加のみ）。
- 関数名・配置は `keyseq/domain/config.py` の既存関数（`normalize_hotkey_presets` 等）の
  命名・配置に揃える。新規ファイルは作らない。

## 読むファイル

- `instructions/common/spec_detail/data_schema.md` §5.11 冒頭（規定と【実装未追従】注記）
- `keyseq/domain/config.py:110-200`（`safe_deepcopy` / `ensure_config_compatibility` の trigger 正規化）
- `keyseq/application/config_service/__init__.py:1-20`（import）と `:454-465`（`_normalize_sequence_payload`）
- `keyseq/application/config_service/__init__.py:181-200`（`load_sequence_file`・呼び出し文脈の確認）
- `keyseq/application/config_service/split_loading.py:480-500`（もう 1 つの呼び出し元・二重正規化の確認）
- `tests/test_domain_config.py:165-215`（actions 正規化の既存テストの書き方）
- `tests/test_config_service.py:1718-1740`（`SequenceFileIoTest` の既存テスト）

## 含まない

- 正本 `data_schema.md` §5.11 の【実装未追従】注記の削除（**task_02**）
- `decisions_archive/23` / `current.md` / backlog INDEX の更新・`/refactor_check`（**task_02**）
- keymap / trigger_set など**他の個別 JSON 読込経路**の正規化見直し（スコープ外・idea_24 の「含まない」）
- `actions[]` 要素のスキーマ拡張・型厳格化（`type` の検証・`x` / `y` の型矯正など。スコープ外）
- `format_action_list_item` など表示整形側の変更・UI / ダイアログの変更（スコープ外）
- `split_loading.py` のインライン trigger 側（`:476`）の経路変更（既に規定どおりのためスコープ外）

## 確認

python は必ずリポジトリルートの `.venv` を使う（worktree からは `..\..\..\.venv\Scripts\python.exe`）。

1. `normalize_actions([])` / `normalize_actions(None)` / `normalize_actions("x")` がいずれも `[]` を返す
2. `normalize_actions([{"type": "text", "value": "a"}, "bad", 1, None, ["x"]])` が
   `[{"type": "text", "value": "a", "label": ""}]` を返す（非 dict 要素の除去）
3. `normalize_actions([{"type": "text", "label": "  x  "}])` の `label` が `"x"`（前後空白の除去）
4. 入力 dict を破壊しない（`safe_deepcopy` 済みで、戻り値を変更しても入力側が変わらない）
5. `load_sequence_file` が、`"actions": [{"type": "hotkey", "value": "ctrl+c"}, "bad", 5]` を含む
   JSON に対して `[{"type": "hotkey", "value": "ctrl+c", "label": ""}]` を返す
6. `ensure_config_compatibility` の既存テストが全 pass（挙動同値の確認）
7. 静的確認: `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui`
8. 既存テスト全 pass: `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests`
   （`tests/test_config_service.py:1737` の期待値更新を含む）

## 完了条件

- 上記確認 1〜8 が pass・**reviewer 採用**。
- 実機目視: **不要**（読込経路の内部正規化のみで UI 変更がないため）。
  UI を伴う最終確認が必要になった場合は task_02 でまとめて扱う。
