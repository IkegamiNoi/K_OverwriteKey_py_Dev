# decisions_archive / phase 23: 個別 sequence JSON 単体読込の actions 正規化

対応表: phase 23 / **暫定仕様なし（直接改訂モード）** / decisions 23。
起票元: [idea_24](../../instructions/backlog/idea_24_sequence_payload_action_normalization.md)
（phase 22 完了判定前 `deep-reviewer` 指摘 3・2026-09-19）。
完了 2026-09-19。**挙動追従のみ・スキーマ不変**（正本の規定は変更せず、実装を規定へ合わせた）。
正本 = `spec_detail/data_schema.md` §5.11「アクション要素」（phase 22 で新設・本フェーズで【実装未追従】注記を削除）。

## 問題

`actions[]` の要素正規化（dict 以外の除去 + `label` 整形）が `ensure_config_compatibility` の内部に
しかなく、**個別 sequence JSON を単体で読み込む経路**（FullView の sequence「読込」→
`ConfigService.load_sequence_file` → `_normalize_sequence_payload`）だけがこれを通らなかった。
非 dict 要素が runtime に載り、後から `format_action_list_item` の `action.get` で `AttributeError` に
なる（**例外の発生位置が読込から離れる**）。phase 22 以前からの既存挙動で、手書き / 別実装由来の
JSON でのみ起こる縁辺ケース。

## 確定した設計判断（ユーザー 2026-09-19）

| # | 判断 | 採らなかった案と理由 |
|---|---|---|
| 1 | **案 A を採用**: 正規化を domain の公開関数 `normalize_actions` へ切り出し、`ensure_config_compatibility` と `ConfigService._normalize_sequence_payload` の双方から呼ぶ | **案 B（個別読込も `ensure_config_compatibility` を通す）** = sequence 単体 payload はトップレベルが trigger ではないため形が噛み合うかの確認が要り、影響範囲が広い |
| 2 | **直接改訂モード**（暫定仕様を起こさない） | 正本 §5.11 の規定は phase 22 で確定済で**仕様変更が不要**（変更は【実装未追従】注記の削除のみ）。単一ファイル・文言確定済み・タスク 2 で `spec_change_workflow.md`「モードの選択」の直接改訂の条件を満たす |
| 3 | **`label: ""` の付与という挙動変更を許容**し、既存テストの期待値を更新する | 共有関数は `label` 整形も含むため、単体読込の戻り値にも `label: ""` が付く。`ensure_config_compatibility` 経由の既存経路と**同じ形**になるので、揃えるほうが正しい（`tests/test_domain_config.py:182` が同じ形を期待） |
| 4 | **正規化は読込時のみ**（保存側 `build_sequence_payload` には入れない） | §5.11 の規定が「読込経路で正規化する」であり、保存側の変更はスコープ外。読込で除去されるため runtime に非 dict が載らない |

## 裏取り（実測で確認した事実）

- `save_sequence_file` は `build_sequence_payload` の payload を `save_json` した**後**に
  `_normalize_sequence_payload` を呼ぶ（`keyseq/application/config_service/__init__.py:225-226`）。
  よって本変更で**ディスクへ書かれる JSON の形は変わらない**（`label` が書き足されることはない）。
- `split_loading.py:485` で `_normalize_sequence_payload` を通した後 `:499` で
  `ensure_config_compatibility` を通るため二重に正規化されるが、`normalize_actions` は**冪等**。
- `data_schema.md:105` の【実装未追従】（レガシー別名保存パスの件）は**別件**であり残す。

## 実測・レビュー

- compile clean / `tests` **486**（skip 7）/ `tests_ui` **446** / smoke pass。
- `reviewer`（phase.md 整合）= 指摘なし。`reviewer`（task_01 実装差分）= **採用 / 完了可**（指摘なし）。
- 実機目視 = **不要**（読込経路の内部正規化のみで UI 変更なし）。
- コミット: `bc61ea7`（task_01）。
- `/refactor_check` = **不要**（PHASE_BASE `cd9e6f2`・対象 2 ファイル・M1〜M6 該当なし）。
  M1: `domain/config.py` 345 行 / `config_service/__init__.py` 827 行だが増分は +2/-3 で 100 行未満。
  M2: 新設関数は 11 行。M3: むしろ重複を 1 箇所へ統合した側。M4〜M6: 該当なし（直値・申し送りコメントの追加なし）。

## 残件

- `button` が非文字列のときの扱い（phase 22 からの別タスク化候補）は**未着手のまま**。
- keymap / trigger_set など**他の個別 JSON 読込経路**の正規化見直しは**スコープ外のまま**
  （必要になった時点で新規 idea として起票する）。
