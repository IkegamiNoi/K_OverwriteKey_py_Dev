# task_01_parent_refs_schema

## 目的

子ファイル（keymap / trigger_set / sequence）JSON に**参照元＝直接の上位ファイルパスの集合**を記録・復元する
基盤を作る（暫定仕様 05 §4「参照元記録（案A・軽量）」）。以降のタスクが使う入力
（§5 の共有状況判定 = **未知 / 単独 / 共有 / 別の上位に属す**）の土台であり、本タスクでは**判定も UI も作らない**。

- レイヤ制約: **application 限定**（`keyseq/application/config_service.py`）。
  presentation は**既存 save 呼び出しへ親パスを渡す引数追加のみ**（判定・分岐ロジックを置かない）。
  domain / infrastructure は不変。
- スキーマ: **子JSON へ追加のみ**（既存キーの削除・意味変更なし。正本 `spec_detail/data_schema.md` の後方互換規定）。
- **既定の挙動は不変**: 親パスが渡らない経路では JSON の出力バイト列が現状と一致すること（後方互換の最優先条件）。

## 対象範囲（application 限定 + presentation は引数配線のみ）

### 1. `keyseq/application/config_service.py` — 定数

`INTERNAL_*` 定数群（`:26-31`）の隣に追加する。

| 定数 | 値 | 用途 |
|---|---|---|
| `PARENT_REFS_KEY` | `"_parent_refs"` | **子JSON ファイル側**のキー（keymap / trigger_set / sequence 共通） |
| `INTERNAL_KEYMAP_PARENT_REFS` | `"_keymap_parent_refs"` | runtime の keymap dict が持ち回る |
| `INTERNAL_SEQUENCE_PARENT_REFS` | `"_sequence_parent_refs"` | runtime の trigger dict が持ち回る |
| `INTERNAL_TRIGGER_SET_PARENT_REFS` | `"_trigger_set_parent_refs"` | runtime（`data`）の**トップレベル**が持ち回る（trigger_set はファイル単位で runtime に入れ物が無いため） |

### 2. 同 — 純関数ヘルパ 2 本（新規・private）

```python
def _normalize_parent_refs(self, value: Any) -> list[str] | None
```
- `value` が list なら、`str` かつ空でない要素のみを `strip()` して**順序を保ったまま重複排除**して返す。
- **キーが無い / list でない場合は `None`**（＝ **未知**）を返す。空 list は `[]`（＝ **既知・参照元ゼロ**）を返す。
  この **`None` と `[]` の区別**が §5 の「未知 → 別名保存既定」の根拠になるため、`or []` 等で潰さないこと。

```python
def _merge_parent_ref(self, refs: list[str] | None, parent_path: str, *, config_root: str) -> list[str]
```
- `parent_path` を `to_config_relative_or_absolute(os.path.abspath(parent_path), config_root)` で保存形へ正規化し、
  `refs`（`None` は空扱い）へ**末尾追加**。比較は `_normalize_path_separators` で正規化した文字列の一致で行い、
  既に含まれるなら追加しない（**重複排除・順序保持**）。`parent_path` が空文字なら `refs`（`None` は `[]`）をそのまま返す。

### 3. 同 — 書き込み（payload 生成）

**共通規則**（全経路で同一）:
- 親パスが渡された場合: 既存 refs（runtime 由来）へ `_merge_parent_ref` した結果を payload の `PARENT_REFS_KEY` へ入れる。
- 親パスが渡されない場合: runtime に refs があればその値をそのまま書き、**`None`（未知）ならキー自体を出力しない**。
- refs は payload の**末尾**に置く（既存キーの順序を変えない）。

| 変更対象 | 変更内容 |
|---|---|
| `_build_keymap_file_payload(keymap)` (`:657`) | 第 2 引数 `*, parent_ref: str = "", config_root: str = ""` を追加し、上記規則で `PARENT_REFS_KEY` を付与 |
| `_build_sequence_payload(trigger)` (`:~745`) | 同上（runtime 側キーは `INTERNAL_SEQUENCE_PARENT_REFS`） |
| `save_keymap_file(path, keymap)` (`:125`) | `*, parent_ref: str = "", config_root: str = ""` を追加。戻り値 `saved` へ**書き込んだ refs** を `INTERNAL_KEYMAP_PARENT_REFS` として設定 |
| `save_sequence_file(path, trigger)` (`:148`) | 同上（`INTERNAL_SEQUENCE_PARENT_REFS`） |
| `save_trigger_set_file(path, data, *, config_root)` (`:169`) | `*, parent_ref: str = ""` を追加。**trigger_set payload 自身**へ refs を付与（親 = `parent_ref`＝ keymap_set）。**各 sequence の親は `path`（trigger_set 自身）** を渡す |
| `_build_trigger_set_payloads(...)` (`:665`) | `*, parent_ref: str = ""` を追加。trigger_set payload へ refs 付与 + 各 sequence payload の親に `trigger_set_path` を渡す |
| `_build_split_save_payloads(...)` (`:456`) | keymaps / trigger_set の親 = `keymap_set_path`、sequences の親 = `trigger_set_path` を流す（`hotkey_presets` は**触らない**） |

### 4. 同 — 読み込み（runtime への復元）

| 変更対象 | 変更内容 |
|---|---|
| `load_keymap_file` (`:100`) | 生 JSON の `PARENT_REFS_KEY` を `_normalize_parent_refs` し、**`None` 以外のときだけ** `INTERNAL_KEYMAP_PARENT_REFS` を keymap dict へ設定 |
| `load_sequence_file` (`:138`) | 同上（`INTERNAL_SEQUENCE_PARENT_REFS`） |
| `_load_triggers_from_trigger_set` (`:~393`) | `sequence_path` から読んだ sequence JSON の refs を trigger dict へ設定（`INTERNAL_SEQUENCE_PARENT_REFS`） |
| `load_trigger_set_file` (`:157`) / `_load_trigger_set`（split 読込経路） | trigger_set ファイル自身の refs を返せるようにし、`_build_runtime_data_from_split` が runtime トップレベル `INTERNAL_TRIGGER_SET_PARENT_REFS` へ格納する |
| keymap の split 読込（`:~370` の runtime keymap 構築） | 読んだ keymap ファイルの refs を `INTERNAL_KEYMAP_PARENT_REFS` へ設定 |

- **キーが無い既存ファイルでは runtime にもキーを作らない**（未知の伝播）。

### 5. 同 — `_sanitize_runtime_for_storage` (`:847`)

新設の内部キー 3 種（keymap / sequence / trigger_set トップレベル）を `pop` する。
**レガシー単一 JSON（Export / `keep_legacy_copy`）へ内部キーを漏らさない**こと。

### 6. presentation — 親パスの配線のみ

`keyseq/presentation/controllers/config_io/` の既存呼び出しに引数を足すだけ。**分岐・判定は書かない**。

| ファイル | 変更内容 |
|---|---|
| `keymap_file_io.py` (`save_keymap_file` 呼び出し 2 箇所) | `parent_ref=self._app.keymap_set_path, config_root=self._app.config_root` を渡す |
| `sequence_file_io.py` (`save_sequence_file` 呼び出し 2 箇所) | 親は**現在の trigger_set パス**。本タスク時点では `self._app.dirty_tracker.trigger_set_source_path`（空なら空文字＝付与なし）を渡す |
| `trigger_set_file_io.py` (`save_trigger_set_file` 呼び出し) | `parent_ref=self._app.keymap_set_path` を渡す |

- `keymap_set_path` が空（新規 / Import 直後 / 空起動。正本 `data_schema.md` §5.4）のときは**空文字が渡り、refs は付与されない**。
  この経路は別名保存で確定パスが決まってから付く — **例外分岐を足さないこと**。

### 設計メモ / 制約

- **`None`（未知）と `[]`（既知・ゼロ）を必ず区別する**。ここを潰すと §5 の安全既定（未知→別名保存）が成立しない。
- 参照元（子→上位の**逆リンク**・共有判定用）と keymap_set の索引（上位→子の**順リンク**・読込経路）は**別物**。
  片方から他方を導出しない（暫定仕様 05 §9）。
- パス比較は `_normalize_path_separators` を通す（Windows の `\` / `/` 混在対策。既存の衝突判定と同じ流儀）。
- 既存の `INTERNAL_KEYMAP_SOURCE_PATH` 系（`:26-31`）の実装パターン（読込で設定・保存で更新・sanitize で除去）を
  そのまま踏襲する。**新しい抽象・共通クラスを作らない**（idea_06 の共通化は task_03 以降の保存計画で扱う）。
- `hotkey_presets` は本フェーズで触らない（暫定仕様 05 §6・§11）。

## 含まない

- **共有状況の判定（§5 の 4 状態）と既定ラジオの決定** → **task_04**
- **保存ダイアログ・行モデル・UI** → **task_05**
- **保存計画（事前検証・依存関係・失敗時の旧索引維持）** → **task_03**
- **trigger_set の source_path 接続（idea_05）と既定命名の keymap_set stem 基準化** → **task_02**
  （本タスクでは `trigger_set_source_path` を**読むだけ**で、分断の解消はしない）
- **参照元の掃除・孤児検出** → idea_07（β 完了後・暫定仕様 05 §11）
- **正本 `spec_detail/` への反映** → task_07（フェーズ中は暫定仕様 05 が正）
- 既存の個別保存ボタンの統合 / hotkey_presets の参照元記録（暫定仕様 05 §11）

## 確認

python は**リポジトリルートの `.venv`**（worktree 相対 `../../../.venv/Scripts/python.exe`）を使う。

1. `-m compileall -q keyseq main.py tests_ui` → clean
2. `-m unittest discover -s tests` → 既存 90 件が pass（新規追加分を含めて fail 0）
3. `-m unittest discover -s tests_ui` → 既存 85 件が pass（fail 0）
4. `-m tests.smoke_app` → pass
5. `tests/test_config_service.py` へ以下を**新規追加**（unittest・既存クラスの流儀に合わせる）:
   - `_normalize_parent_refs`: キー無し → `None` / `[]` → `[]` / `["a","a","b"]` → `["a","b"]`（順序保持）/
     非 list（`"x"` / `None` / `{}`）→ `None` / 空文字・非 str 要素は除外
   - `_merge_parent_ref`: 新規追加される / 既存と重複しても増えない（`/` と `\` の混在でも同一視）/
     `parent_path=""` は無変更 / config_root 内は相対・外は絶対で格納される
   - `save_keymap_file` に `parent_ref` を渡すと JSON に `_parent_refs` が入り、**渡さないと入らない**
   - `_parent_refs` 付きの keymap / sequence を `load_*` → `save_*`（`parent_ref` 無し）で
     **refs が失われない**（round-trip 保持）
   - `_parent_refs` **無し**の既存ファイルを `load_*` すると runtime に内部キーが**作られない**（未知の伝播）
   - `save_runtime_data`: keymap / trigger_set の refs に keymap_set パス、sequence の refs に trigger_set パスが入る
   - `_sanitize_runtime_for_storage` / `export_runtime_data` に新内部キーが**漏れない**
6. **既存の完全一致アサート**（`tests/test_config_service.py:125` の
   `assertEqual(payload, {"label": "Main", "mappings": {"a": "b"}})`）が**修正なしで pass** すること
   ＝「親が渡らなければ出力が変わらない」の回帰確認。落ちた場合は既定挙動を変えてしまっている。

## 完了条件

- 上記確認 1〜6 がすべて pass（実測は `verifier` が `.venv` で行う。Codex の自己申告は完了根拠にしない）。
- **`reviewer` 採用**（観点: 依存方向〔application に UI 依存を持ち込んでいないか / presentation に判定を書いていないか〕・
  後方互換〔既存キー削除なし・親未指定時の出力不変〕・過剰実装〔共通化の先取りをしていないか〕）。
- **実機目視は task_06 でまとめて実施**（本タスクでは不要。UI 変更なし）。
