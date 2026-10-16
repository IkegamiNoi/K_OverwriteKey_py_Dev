# task_02_spec_promotion

## 目的

phase 61 の正本反映とフェーズ完了の記録（直接改訂モード）。**文書のみ（コード不変）**。

## 対象範囲（文書のみ）

* `instructions/common/spec_detail/key_input.md` §7.4: キーボードUI の編集（#7）の名前の作り方を 1 項追記（順序 = テンキー → keysym の表 → VK を走査コードへ変換してレイアウトの `scan_code` だけで引く〔既知の特殊キーの表へは落とさない〕→ keysym の小文字 / 変換できないときは keysym / 受容 = US 入力配列の「`」はフックの実行時と名前が違う・jis.json 以外では特殊キーが名前にならない・JIS の特殊キーは IME に横取りされ `??` で届き取得できない〔idea_50〕）
* `instructions/common/codebase_map.md`: `keyboard_window.py` と `keyboard_layouts.py` の行への追記（phase 61 の独立した節は作らない）
* `.claude_data/state/decisions_archive/61_keyboard_ui_vk_to_scan_code.md` / `decisions.md` の索引 / `instructions/phase/current.md` の完了記載 / idea_47 を `INDEX.md` から `INDEX_done.md` へ
* `/refactor_check`（メトリクスは verifier）・完了判定前レビュー（`deep-reviewer` + `codex-adversarial-reviewer`）

## 読むファイル

1. `instructions/phase/61_keyboard_ui_vk_to_scan_code/phase.md`（確定）
2. `instructions/backlog/idea_50_capture_jis_special_keys.md`（実測）

## 含まない

* コードの変更 / idea_49・idea_50

## 確認

* 正本・地図に #7 の名前の作り方と受容が載る / 完了判定前レビューの採用

## 完了条件

- 上記確認・完了判定前レビューの採用・`/refactor_check` の判定の記録。
