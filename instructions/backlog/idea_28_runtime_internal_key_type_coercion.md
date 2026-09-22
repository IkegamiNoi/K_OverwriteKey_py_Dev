# idea_28_runtime_internal_key_type_coercion.md

## 概要

**runtime 専用の内部キー**（`_keymap_source_path` 等・§5.8.2）が §5.1「型不正の共通規則」に
**未追従**。`ensure_config_compatibility` が生値のまま素通しし、
`save_path_resolution.py:127` の `str(...)` を経て**保存先パスの候補に Python の repr が混入し得る**。
正本 §5.7 が「**本節の規定が正**であり、実装側を追従させる」と明記しているため、**実装修正が既定**。

## 起票経緯（2026-09-22）

phase 25（パス系の型正規化）完了判定前の `deep-reviewer` 指摘 B。
phase 25 は**永続化されるパス系フィールド**を対象としたため内部キーはスコープ外とし、
`instructions/phase/current.md`「別タスク化候補」へ送っていた。
2026-09-22 の current.md 整理でユーザー判断により idea へ昇格。

## 現状

- 内部キーの定義: `config_service/__init__.py:35` の `INTERNAL_KEYMAP_SOURCE_PATH = "_keymap_source_path"` 等。
  一覧と規約は正本 `data_schema/5_08_02_runtime_internal_keys.md`
- 読取: `save_path_resolution.py:127`
  `source_path = str(keymap.get(service.INTERNAL_KEYMAP_SOURCE_PATH) or "").strip()`
  → 非文字列でも `str()` で**文字列化されてしまう**（phase 25 で潰したのと同型の残存箇所）
- 正本 `data_schema.md` §5.7 の末尾に
  「runtime 専用の内部キー（`_keymap_source_path` 等・§5.8.2。永続化しない）は**現時点で本規則に追従していない**
  （手編集の単一 JSON で非文字列を入れると生値のまま残る）」と明記済
- **実害**: 内部キーは永続化されないため通常経路では発生しない。個別 JSON を手編集して
  非文字列を入れた場合のみ、保存先ファイル名の算出に repr 文字列が使われ得る

## 提案（方向性・要設計）

- phase 25 と同じく **`coerce_label`（trim のみ・小文字化しない）**で受けるのが素直。
  適用点は ①`ensure_config_compatibility` 側で載せる時点に寄せる か
  ②読み手（`save_path_resolution.py`）側で潰す か の選択
- ①は内部キーを載せる入口が複数（keymap / sequence / trigger_set）あるため、
  入口の棚卸し（§5.8.8 の台帳）とセットで見る

## 想定スコープ

- 含む: `config_service` の内部キー読み書き経路 + テスト。§5.7 の ※ 注記の削除（追従完了時）
- 含まない: 永続化されるパス系フィールド（phase 25 で対応済）
- 影響レイヤ: application / domain。**正本の規定は既にあるため仕様変更は不要**（注記の削除のみ）
