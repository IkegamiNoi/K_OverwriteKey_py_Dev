# task_04a_capture_hook_fixes

## 目的

task_04 の完了判定前レビューで見つかった取得用のフックの 3 件を直す（2026-10-21 ユーザー判断で採用）。暫定 49 §3-2（§7.1 と同じ順）・§3-4（最後の押下から）・§3-6（古い名前を渡さない）に実装を合わせる。
**presentation 限定（`key_capture_hook.py` 数行 + テスト 3 件）・挙動は仕様どおりへ・スキーマ不変。**

## 対象範囲（presentation 限定）

- `keyseq/presentation/key_capture_hook.py`
  1. `_target_name`: `resolve_name` の名前が `domain.numpad_keys.is_numpad_key_name` に当たれば対象外（deep-reviewer 指摘 1・実行時の `input_router.py:192` と同じ）
  2. `_handle_event`: 世代を callback の入口（名前の解決の前）で読み、受け渡しに使う（Codex 敵対的 medium 1）
  3. 余韻（owner = 0）の経路でも押下中の時刻は押下のときだけ更新する（Codex 敵対的 medium 2 = deep 指摘 3）
- `tests/test_key_capture_hook.py`: 上の 3 件のテストを 1 件ずつ

## 読むファイル

1. `keyseq/presentation/key_capture_hook.py:120-170`
2. `keyseq/application/input_router.py:184-196`（実行時の解決）

## 含まない

- 正本の文言（task_04 で実施）・deep 指摘 8・9（保留）

## 確認

- `compileall` clean / tests 全 pass / tests_ui 全 pass / smoke pass

## 完了条件

- 上記確認・**reviewer 採用**。メインが直接修正（数行）。
- 実機目視: 不要（3 件とも実機目視の 8 項目の挙動を変えない〔jis.json の 4 キーはテンキーの名前でない・世代と余韻の離しは境界の時刻だけ〕）。
