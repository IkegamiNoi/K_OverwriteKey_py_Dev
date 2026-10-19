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
- **優先度**: ~~低（既定の登録先 `config/user/keylayout/` を使う限り実害が出にくい）~~ →
  **中に引き上げ（2026-10-20）**。**既定の登録先こそ読込のたびに壊れる**ことを確認した（下記「実害の確認」）。
  ただし**後方互換の移行規則が要る**ため、単独タスクではなく設計を伴う。

## 関連

- 分離元: [暫定仕様 10](../history/10_orphan_child_file_sweep.md) §3-3（superset で回避した経緯）。
- 正本: `spec_detail/data_schema.md` **§5.7**（パス表記。stored と resolved の分離）。

## 実害の確認（2026-10-20・phase 63 の実機目視中に発見）

出所: phase 63 の実機目視で使っていた Operation_check worktree の
`config/user/keymap_sets/phase62.json`。`external_keyboard_layouts` に**同じ jis.json を指す 9 件**が
`config\user\keylayout\jis.json`（最新・`\` 区切り）→ `config/config/user/...` → … →
`config/config/config/config/config/config/config/config/config/user/keylayout/jis.json` と、
**`config/` が 1 段ずつ増えた形で溜まっていた**。

**原因（実測・2026-10-20 時点の行番号）**: 上記「現状」の非対称そのもの。
- 登録: `presentation/controllers/layout_controller.py:302` が `to_rel_if_possible(path)` で
  **base_dir（= `dirname(config_root)`）基準**の相対表記（`config\user\keylayout\jis.json`）を保持。
- 保存: `application/config_service/split_payloads.py:478` が runtime 値をそのまま書く。
- 読込: `application/config_service/split_loading.py:557` が **config_root 基準**で解決
  （→ `<root>/config/config/user/...`）、同 `:560-562` が **base_dir 基準**の相対へ戻す
  （→ `config/config/user/...`）。**読込 1 回ごとに全要素へ `config/` が 1 段増える**。
- 表示側 `presentation/keyboard_layouts.py:285`（`_resolve_layout_path`）は base_dir 基準で解決するため、
  増えたパスは存在せず `:288` の `except: continue` で**黙って読み飛ばされる**（レイアウトが消える）。
- 消えたので利用者が再登録すると、`layout_controller.py:303` の重複判定は**文字列比較**のため
  `config\user\...` と `config/config/user/...` を別物とみなし通過 → **起動のたびに 1 件ずつ溜まる**
  （9 件 = 9 回の「起動 → 消えた jis を再登録 → 保存」と整合）。

**再現手順**
1. 外部レイアウト追加で `config/user/keylayout/jis.json` を登録し、構成セットを保存する
   （JSON 上は `config\user\keylayout\jis.json`）。
2. アプリを再起動する（読込）→ runtime は `config/config/user/keylayout/jis.json` になり、
   レイアウト一覧から jis が消える。何か保存すると JSON にもこの値が書かれる。
3. 再起動のたびに 1 段増える。単体での再現（`.venv` で確認済み）:
   `split_loading.normalize_external_keyboard_layouts` を `config_root=<root>/config`・
   入力 `config\user\keylayout\jis.json` で 3 回通すと
   `config/config/user/…` → `config/config/config/user/…` → `config/config/config/config/user/…`。

**着手時の追加注意**
- 既存テスト `tests/test_config_service.py:1947-1953` が**この非対称な出力を期待値として固定**している
  （config_root 基準で解決 → 親基準の相対）。是正時は期待値の見直しが要る。
- 既に壊れた JSON の救済（`config/config/…` の重複要素の扱い・同一解決先の重複除去）を移行規則に含めるか要判断。
- 重複判定（`layout_controller.py:303`）を解決後パスの比較にするかも併せて検討。
