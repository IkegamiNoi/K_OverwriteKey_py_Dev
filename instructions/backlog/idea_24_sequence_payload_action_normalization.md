# idea_24_sequence_payload_action_normalization.md

## 概要

**個別 sequence JSON を単体で読み込む経路が `actions` の正規化を通らない**。
`ensure_config_compatibility` を通る経路（split 読込）では dict 以外の要素が除去され `label` が整形されるが、
個別読込では `actions` をそのままコピーするため、**dict 以外の要素が runtime へ載る**。
正本 `data_schema.md` §5.11 では **【実装未追従】**として明記済で、**規定（除去する）が正**。

## 起票経緯（2026-09-19）

出所 = phase 22（マウスのドラッグ操作）の**完了判定前 `deep-reviewer` 指摘 3**。
phase 22 で §5.11「アクション要素」を新設した際、「dict 以外は読込時に除去する」と書いたことで
既存の未追従が顕在化した（**phase 22 以前からの既存挙動**であり、ドラッグ固有の問題ではない）。
判断は [decisions_archive/22](../../.claude_data/state/decisions_archive/22_mouse_drag_action.md)。

## 現状

- 通る経路: `keyseq/application/config_service/split_loading.py` → `ensure_config_compatibility`
  （`keyseq/domain/config.py` で dict 以外を除去し `label` を整形）。
- 通らない経路: `keyseq/presentation/controllers/config_io/sequence_file_io.py` →
  `ConfigService.load_sequence_file` → `ConfigService._normalize_sequence_payload`。
  `actions` は `safe_deepcopy` するだけで、要素の型検査をしない。
- 影響: 非 dict 要素が載ると `keyseq/domain/config.py` の表示整形（`action.get`）で `AttributeError`。
  手書き / 別実装由来の JSON でのみ起こる縁辺ケース。
- 正本: `instructions/common/spec_detail/data_schema.md` §5.11 冒頭（【実装未追従】の注記あり）。

## 提案（方向性・要設計）

- 案 A: `_normalize_sequence_payload` の `actions` に、`ensure_config_compatibility` と同じ
  要素正規化（dict 以外の除去 + `label` 整形）を適用する。**正規化ロジックは domain 側へ寄せて共有する**
  （application が整形規則を二重に持たないようにする）。
- 案 B: 個別読込経路も `ensure_config_compatibility` を通す。影響範囲が広く、sequence 単体の
  payload 形と噛み合うかの確認が要る。
- いずれも**挙動変更**（現在は例外になっていた入力が読めるようになる）ため、着手時は
  `.claude/rules/spec_change_workflow.md` に従って影響を確認する。

## 想定スコープ

- 含む: `application/config_service` の sequence 単体読込 + `domain/config` の正規化関数の共有化、対応する単体テスト。
- 含まない: `actions` 要素のスキーマ拡張・UI・他の個別 JSON（keymap / trigger_set）の正規化見直し。
- 影響レイヤ: application / domain。正本仕様の変更は不要（§5.11 の規定に実装を追従させるだけ）。優先度低。
