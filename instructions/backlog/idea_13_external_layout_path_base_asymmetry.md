# idea_13_external_layout_path_base_asymmetry.md

## 概要

**`external_keyboard_layouts[].path` の解決基準と保存表記が非対称で、ファイル内の値がどちらの基準か一意に決まらない。**
読み込みは `config_root` 基準で解決するのに、runtime へは `dirname(config_root)` 基準の相対表記で保持し、
保存はその runtime 値をそのまま書く。結果として**保存された値を読み直すと解決先がずれ得る**。

## 起票経緯（2026-09-06）

出所: **暫定仕様 10（孤児ファイルの棚卸し）v0.3 の `codex-adversarial-reviewer` 指摘（Medium）**。
孤児検出が参照集合を作る際にこの非対称へ突き当たり、暫定仕様 10 では
**両基準で解決した superset を参照集合へ入れる**（安全側）ことで回避した。
**非対称そのものの是正は phase 11 のスコープ外**として本 idea へ分離した。

## 現状（2026-09-06 実測）

- 読み込み: `split_loading.normalize_external_keyboard_layouts:526` が
  `_resolve_config_relative_path(stored_path, config_root)`（**config_root 基準**）で解決する。
- runtime 保持: 同 `:529-531` が `os.path.relpath(runtime_path, dirname(config_root))` で
  **親基準の相対表記**へ変換する（`..` で始まらない場合のみ）。
- 保存: `split_payloads.build_keymap_set_payload:342` が
  `safe_deepcopy(runtime["external_keyboard_layouts"])` を**そのまま書き出す**。
- したがって「保存 → 読み込み」を経ると、**親基準で書かれた値を config_root 基準で解決する**ことになる。

## 想定スコープ

- **含む**: 解決基準の統一（読み書きで同一基準にする / 共有関数化）、後方互換の移行規則
  （既存 JSON に両基準の値が混在し得る）、正本 `spec_detail/` への明記。
- **含まない**: 孤児検出側の superset 対応（暫定仕様 10 / phase 11 で対応済み）。
- **影響レイヤ**: application（`split_loading` / `split_payloads`）+ 正本仕様。
- **仕様変更**: あり（パス表記の規定 = 正本 §5.7 の適用範囲）。**着手時は仕様変更フロー必須**。
- **優先度**: 低（既定の登録先 `config/user/keylayout/` を使う限り実害が出にくい）。
  ただし**後方互換の移行規則が要る**ため、単独タスクではなく設計を伴う。

## 関連

- 分離元: [暫定仕様 10](../history/10_orphan_child_file_sweep.md) §3-3（superset で回避した経緯）。
- 正本: `spec_detail/data_schema.md` **§5.7**（パス表記。stored と resolved の分離）。
