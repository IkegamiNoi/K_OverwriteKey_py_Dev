# idea_31_input_gateway_dead_register_key_hook.md

## 概要

`InputGateway.register_key_hook`（`keyseq/infrastructure/input_gateway.py:58-75`）に
**呼び出し元が無い**。`keyboard.hook_key` を包む 18 行のデッドコードで、
**削除して問題ないかの確認と削除**が内容。

## 起票経緯（2026-09-22）

phase 21（拡張キーを拡張キーとして送る）完了判定前の `deep-reviewer` 指摘 8。
**phase 21 の差分外の既存デッドコード**という当時の都合で
`instructions/phase/current.md`「別タスク化候補」へ据え置かれていた（ユーザー判断 2026-09-19）。
2026-09-22 の current.md 整理でユーザー判断により idea へ昇格。

## 現状

- 定義: `input_gateway.py:58-75`。`keyboard.hook_key(key, _wrapped, suppress=suppress)` を呼び、
  `_wrapped` が `event_type != "down"` を捨てて押下だけ上位へ渡す
- **呼び出し元 0 件**（2026-09-22 実測）。フック登録の実経路は
  `application/hook_coordinator.py:55` の `register_global_hook`（`keyboard.hook`）のみ
- コメントに「制御キー（停止/トグル）の抑止を安定させる」とあるが、
  **現在の停止 / トグルキーの抑止はグローバルフック側で行っている**（`key_input.md` §7.6）。
  過去の実装の名残と見られる（要確認）

## 提案（方向性・要設計）

- **案 A**: 削除する。`InputGateway` の公開面が 1 つ減る。テストが参照していないことの確認が要る
- **案 B**: 将来使う想定があるなら残し、docstring に「現在未使用」と明記する
- 判断材料: `_wrapped` の「押下のみ渡す」挙動が**他所で再実装されていないか**
  （再実装されているなら共通化の材料になり、単純削除ではなくなる）

## 想定スコープ

- 含む: `input_gateway.py` の該当メソッド + 参照確認（`tests/test_input_gateway_*.py` 含む）
- 含まない: `register_global_hook` / フック登録経路そのものの見直し
- 影響レイヤ: infrastructure のみ。**挙動不変**・仕様変更なし
  （`codebase_map.md` の InputGateway 節に公開面の記載があれば追従）
