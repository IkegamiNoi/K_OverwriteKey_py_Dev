# 暫定仕様 20: JSON 読込の型不正の扱い統一（individual_json_type_normalization）

> 状態: **未凍結・v0.3・ユーザー確定済（実装着手可）・主入力**。本書がこのフェーズの確定設計（フェーズ中は正本を直接改訂しない）。
> フェーズ末タスクで正本 `instructions/common/spec_detail/` へ昇格し本書を凍結する。
> 起票元: phase 23 完了後のユーザー指示（2026-09-19）= 「keymap / trigger_set の個別読込経路を
> 実際に見直して必要なら直す」。見直しの実測で複数の欠陥と未定義事項を検出した。
>
> v0.1 → v0.2: 起票時レビュー（`deep-reviewer`）+ 確定前レビュー（`codex-adversarial-reviewer`）の
> 指摘を反映。主な訂正 = ①例外経路の棚卸しが不足（actions の `label` でも落ちる）
> ②`suppress` の記述が実装と逆 ③参照先 sequence 経由の再流入 ④共有ローダーのため
> 経路別スコープが成立しない ⑤行番号の誤り。
> v0.2 → v0.3: **ユーザー確定（2026-09-19）**。スコープ = **案 F（全経路へ一斉適用）**、
> §7-2 の 3 条項 = **提案どおり**。確定内容を §2 へ移し、§7 を閉じた。

---

## §1 目的 / 背景

JSON を読み込むとき、**要素の型が不正だった場合の扱いが経路ごとにばらばら**で、
一部の入力では **`AttributeError` で読込そのものが落ちる**。これを
「**除去に寄せる**」方針（ユーザー判断 2026-09-19）で統一し、正本へ明文化する。

phase 23 で sequence の `actions[]` は「dict 以外を除去」へ揃えた（正本 §5.11）。
本フェーズはその続きで、**残る型不正の扱い**を対象にする。

### 現状監査（2026-09-19・`.venv` で実測。v0.2 で訂正）

**原因は 1 つ**: 文字列前提の処理（`normalize_key_name` / `(x or "").strip()`）へ
**非文字列がそのまま渡る**。`x or ""` のため **falsy な非文字列（`0` / `false` / `[]` / `{}`）は
既に空へ倒れており、問題になるのは truthy な非文字列のみ**（`123` / `["a"]` / `{"a":1}` 等）。

例外になる箇所（すべて実測で再現）:

| # | 箇所 | 影響する経路 |
|---|---|---|
| 1 | `config_service/__init__.py:505` `_generate_keymap_id` の `id` | keymap 個別読込 + **split 読込**（`split_loading.py:408` が同じ関数を呼ぶ） |
| 2 | `domain/config.py:144` `normalize_actions` の `label` | **sequence 個別読込 / trigger_set 個別読込 / split 読込 / 単一 JSON** |
| 3 | `domain/config.py:178` `ensure_config_compatibility` の `triggers[].key` | 単一 JSON（runtime 直通） |
| 4 | `domain/config.py:179` 同 `triggers[].label` | 単一 JSON |
| 5 | `domain/config.py:248` 同 `keymaps[].id` | 単一 JSON |
| 6 | `domain/config.py:265` 同 `keymaps[].label` | 単一 JSON |

例外にならないが**無意味な値が載る**箇所（`str()` 強制による Python の repr 文字列化）:

```
keymap   {"mappings": {"a": {"x": 1}}}  → {"a": "{'x': 1}"}
trigger  {"key": {"a": 1}}              → key = "{'a': 1}"
trigger  {"label": ["a"]}               → label = "['a']"
sequence {"label": {"a": 1}}            → 参照元 trigger の label を "{'a': 1}" で上書き
                                          （split_loading.py:485-486 の trigger.update）
```

**比較対象（既に「除去」流儀で正しいもの）**: `normalize_hotkey_presets`（非 dict・非 str の
label/value を除去）/ `normalize_actions` の**要素**判定（非 dict を除去）。

### 経路とローダーの共有関係（v0.2 で追記）

**個別読込と split 読込は同じローダーを共有する**ため、経路で切り分けたスコープは成立しない:

- `_generate_keymap_id` ← `load_keymap_file`（個別）/ `split_loading.py:408`（split）
- `load_triggers_from_trigger_set` ← `load_trigger_set_file`（個別）/ `split_loading.py:447`（split）
- `normalize_actions` ← `ensure_config_compatibility`（split / 単一 JSON）/
  `_normalize_sequence_payload`（sequence 個別・保存後の戻り値）

独立しているのは**単一 JSON（legacy runtime）が `ensure_config_compatibility` へ直接入る経路**のみ。

### 正本の現状

- `spec_detail/data_schema.md` §5.6 に **keymap 個別 JSON の節が無い**（trigger_set / sequence /
  旧形式互換の 3 小節のみ）。`triggers[]` は「`key` / `suppress` / `sequence_path` を持つ」だけで型規定なし。
- §5.11 の `label` にも型規定が無い（「一覧表示用の任意の文字列」）。
- ただし `data_schema/5_08_09_orphan_sweep.md:43-44` が**形状検証**として
  「`mappings` は dict / `triggers` は list / `actions` は list / `hotkey_presets` は list」を既に規定。
  新設節はここと**二重定義にせず相互参照**する。
- §5.7 は既に keymap 個別ファイルの存在を前提にしている（新設節はその位置づけを明記）。
- 本件は `spec_change_workflow.md` 検出基準 **B（仕様書の不備・未定義挙動）**。

## §2 確定事項（ユーザー 2026-09-19）

- **「除去に寄せる」方針を採る**（`actions` の要素判定 / `hotkey_presets` と同じ流儀へ統一する）。
- 正本 §5.6 に **keymap 個別 JSON の節を新設**し、`trigger_set` にも型の規定を加える。
- **読込が `AttributeError` で落ちる箇所を解消する**（§1 の 6 箇所。どこまでを本フェーズで
  直すかは §7-1 の確定による）。
- 挙動変更（これまで repr 文字列として受け入れていた値が消える）を許容する。
- **スコープ = 案 F（全経路へ一斉適用）**（v0.3・2026-09-19 確定）。`coerce_key_name` /
  `coerce_label` を §1 の 6 箇所すべてへ適用し、**単一 JSON 経路も含めて**型不正を統一する。
  経路別に切ると共有ローダーのため破綻し、正本にも経路依存の型規定が残るため。
- **個別条項**（v0.3・2026-09-19 確定）:
  1. trigger の `key` が非文字列 → **空扱いで trigger は残す**（UI で入れ直せる）
  2. `sequence_path` が非文字列 → **空扱い**（参照なし＝インラインの `actions` を使う）
  3. `mappings` の target が非文字列 → **対ごと除去**（source は JSON 由来で常に str）

## §3 共通規則（型不正の 3 分類）

型が不正なときの扱いを、**フィールドの役割**で決める。

| 分類 | 定義 | 扱い |
|---|---|---|
| **R1 要素ごと除去** | 要素の同一性を決めるフィールドのうち、**フォールバック先を持たない**もの（`mappings` の対・`actions` の要素・`hotkey_presets` の要素） | その**要素を丸ごと捨てる** |
| **R2 空扱い** | 付随フィールド（`label` 等）、および**フォールバック先を持つ同一性フィールド**（keymap の `id` → ファイル名 stem ／ trigger の `key` → UI で入れ直せる） | **空文字**として扱い、要素自体は残す |
| **R3 既定値へ倒す** | bool / int のフィールド（`suppress` / `run_to_end` / `run_to_end_delay_ms` / `clicks` 等） | **現状の実装どおり**（本フェーズで変更しない。§5 の注記参照） |

- **正規化は読込時に行う**（§5.11 と同じ）。保存側は runtime の値をそのまま書く。
- **エラーダイアログは出さない**（黙って捨てる）。読込時にファイルは書き換えない。
  ただし**捨てた値は、その後ユーザーが保存操作を行うとファイルから消える**（runtime を書くため）。
- **falsy な非文字列は既に空扱い**（`x or ""`）。本書が変えるのは **truthy な非文字列**のみ。

## §4 keymap 個別 JSON（正本 §5.6 に新設予定）

`config/user/keymaps/` 配下。`id` / `label` / `mappings` を持つ。未定義キーは無視する（§5.1）。

| キー | 型 | 不正時の扱い | 分類 |
|---|---|---|---|
| `id` | str | **空として扱う** → ファイル名の stem 由来へフォールバック → それも空なら `"keymap"` | R2 |
| `label` | str | **空文字**にする | R2 |
| `mappings` | dict（str → str） | dict 以外なら `{}`（既存の形状検証と同じ）。**値（target）が非文字列ならその対を除去** | R1 |

- `mappings` の**キー（source）は JSON 由来のため常に str**（`safe_deepcopy` は json round-trip）。
  規定は **target のみ**でよい（v0.2 訂正）。
- `id` の重複回避（`_2` 付加）、`normalize_key_name`（trim + 小文字化）、
  正規化後に空になる対の除去は**現状どおり**。

## §5 trigger_set 個別 JSON（正本 §5.6 に追記予定）

| キー | 型 | 不正時の扱い | 分類 |
|---|---|---|---|
| `triggers` | list | list 以外なら `[]`（現状どおり・明文化のみ） | — |
| `triggers[]` の要素 | dict | 非 dict は**除去**（現状どおり・明文化のみ） | R1 |
| `key` | str | **空として扱う**（trigger 自体は残す。既存の「空 key」と同じ） | R2 |
| `label` | str | **空文字**にする | R2 |
| `sequence_path` | str | **空として扱う**（参照なし＝インラインの `actions` を使う） | R2 |
| `actions` | list | list 以外なら `[]`（現状どおり）。要素は §5.11（phase 23 で規定済） | — |
| `suppress` | bool | **`bool()` 強制の現状どおり**。`null` / `0` / `""` / `[]` は **False** になる（v0.2 訂正。「既定 true へ倒す」ではない） | R3 |
| `run_to_end` | bool | `bool()` 強制の現状どおり | R3 |
| `run_to_end_delay_ms` | int | 変換不能なら既定 300（現状どおり。`"500"` は 500 へ変換される） | R3 |

- **参照先 sequence の `label`** も同じ規則で正規化する（`trigger.update()` で参照元の
  `label` を上書きするため。v0.2 で追加）。
- `actions[]` の要素の `label` も同じ規則（R2 = 空扱い）で正規化する（§2 の案 F 確定により無条件）。

## §6 実装方針

- 型検査は **domain 層の純関数へ寄せる**（phase 23 の `normalize_actions` と同じ形）。
  application 側に整形規則を二重に持たせない。
- **`normalize_key_name(value: str)` のシグネチャは変えない**。呼び出しが **158 箇所**あり、
  Any 受けにすると全経路の意味が変わるため。
- 代わりに **domain へ入口関数を 2 本足す**（v0.2・`deep-reviewer` D-1 の解消）:
  - `coerce_key_name(value: Any) -> str` … 非 str なら `""`、str なら `normalize_key_name` を通す
  - `coerce_label(value: Any) -> str` … 非 str なら `""`、str なら trim
  application 層（`_generate_keymap_id`）と domain 層の双方がこの関数を呼ぶ形にすれば、
  「型検査は domain へ」と「呼び出し側で判定」が両立する。
- `mappings` の target 除去は `domain/config.py:255-260` の共通コードへ入れる。

## §7 確認事項（**すべて確定済み・2026-09-19**）

本節の論点は §2 へ移した。確定内容は以下のとおり。

- **§7-1 スコープ** → **案 F（全経路へ一斉適用）**で確定（両レビューの推奨）。
  不採用にした案 G（個別読込限定）は、`actions[]` の `label` 由来の `AttributeError` が
  個別読込にも残り「統一した」と言えないこと、共有関数を次フェーズで再度触ることになる
  ことが理由。
- **§7-2 個別条項 3 件** → いずれも本書の提案どおりで確定。
  `mappings` の source 側は JSON 由来で常に str のため論点にならない（v0.2 訂正済）。

## §8 受け入れ条件（ドラフト）

1. `{"id": 123}` / `{"id": ["a"]}` の keymap JSON を単体読込しても**例外が出ず**、
   ファイル名 stem 由来の id になる（§4）。
2. `{"mappings": {"a": {"x": 1}, "b": "c"}}` の単体読込で `{"b": "c"}` のみが残る（§4・R1）。
3. `{"key": {"a": 1}, "label": ["a"]}` の trigger を含む trigger_set の単体読込で、
   `key` / `label` がともに空文字になる（§5・R2）。
4. **`{"actions": [{"type": "text", "label": 123}]}` の sequence / trigger_set 単体読込で
   例外が出ない**（§1 #2）。
5. `ensure_config_compatibility({"triggers":[{"key":5}]})` /
   `({"keymaps":[{"id":7}]})` で例外が出ない（§1 #3〜#6）。
6. **repr 文字列（`"{'a': 1}"` 等）が runtime に載らない**ことを単体テストで確認する
   （個別読込・split 読込・単一 JSON の 3 経路）。
7. 参照先 sequence の `label` が非文字列でも、参照元 trigger の `label` が repr にならない（§5）。
8. 既存テスト全 pass。**ベースライン: `tests` = 486（skip 7）/ `tests_ui` = 446 / smoke pass**。
   件数が減らない。現行の `str()` 強制挙動を固定している既存テストは無い（fixture 調査済）。
9. 正本 §5.6 に keymap 節が新設され、trigger_set の型規定が入っている
   （`5_08_09_orphan_sweep.md` の形状検証とは相互参照にする）。

## §9 スコープ外（本フェーズでやらない）

- `actions[]` の**要素**の型規定（phase 23 で確定済・§5.11 が正）。本書が扱うのは要素内の `label` のみ。
- `hotkey_presets` の読込（既に「除去」流儀で規定どおり）。
- `suppress` / `run_to_end` / `run_to_end_delay_ms` の**既定値への倒し方の見直し**（R3・現状維持）。
- `button` 非文字列の `AttributeError`（`action_executor.py:119`・phase 22 からの別タスク化候補）。
  **実行時**の型不正であり、本書が扱う**読込時**の正規化とは別レイヤ。

## §10 正本反映（フェーズ末昇格・予定）

- 正本: `instructions/common/spec_detail/data_schema.md`
  - **§5.1 直下に「型不正の共通規則」を 1 段落**置き、各表からは参照のみにする
    （R1〜R3 というラベル自体は正本へ持ち込まない。`deep-reviewer` F-2）
  - §5.6 に **keymap 個別 JSON の節を新設**（§4 の表）/ trigger_set に**型の規定を追記**（§5 の表）
  - §5.2（単一 JSON）と §5.11（`label` の型）にも追記（案 F 確定により必須）
  - `data_schema/5_08_09_orphan_sweep.md:43-44` の形状検証と**相互参照**（二重定義にしない）
- 実装: `keyseq/domain/config.py`（`coerce_key_name` / `coerce_label` / mappings の target 除去）/
  `keyseq/application/config_service/__init__.py`（`_generate_keymap_id` / `load_keymap_file`）/
  `keyseq/application/config_service/split_loading.py`（`load_triggers_from_trigger_set`）
- テスト: `tests/test_domain_config.py` / `tests/test_config_service.py`
- `codebase_map.md`: 正規化の配置に変更があれば追記
- 記録: `.claude_data/state/decisions_archive/<NN>.md` の作成 / `instructions/phase/current.md` の更新
  （`task_execution.md`「フェーズ完了時」）
- 別実装同期: 不要（読込の頑健化のみでファイル形式は不変）

## 関連

- phase 23 / [decisions_archive/23](../../.claude_data/state/decisions_archive/23_sequence_payload_action_normalization.md)
  — `actions[]` の正規化を domain へ一本化（本書はその続き）
- [idea_06](../backlog/idea_06_individual_json_io_unification.md) — 個別 JSON I/O の統一。
  本書で触る 3 ローダーは idea_06 の対象と同一で、型正規化を domain へ寄せると前進になる
- 正本 [data_schema.md](../common/spec_detail/data_schema.md) §5.1 / §5.2 / §5.6 / §5.7 / §5.11 /
  [5_08_09_orphan_sweep.md](../common/spec_detail/data_schema/5_08_09_orphan_sweep.md)（形状検証）
