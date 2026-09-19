# task_02_spec_and_close

## 目的

phase 23 の**正本反映と記録**（フェーズ最終タスク）。task_01 で実装が §5.11 の規定へ追従したため、
正本 `data_schema.md` §5.11 の**【実装未追従】注記を削除**し、判断履歴・ルーティング・起票元 idea の
クローズまでを行う。

レイヤ制約: **文書作業のみ**。コード変更なし（`.claude/rules/agent_selection.md`
「メインセッションが直接行ってよい作業」= フェーズ末の正本反映タスク）。

## 対象範囲（文書のみ）

### instructions/common/spec_detail/data_schema.md

- §5.11 冒頭の【実装未追従】の箇条書き（idea_24 へのリンクを含む 3 行）を**削除**する。
- 規定本文（「要素は `ensure_config_compatibility` を通る読込経路で正規化し、dict 以外の要素は除去する」）は、
  **実装が「読込経路（split 読込・個別 sequence 単体読込の双方）で正規化する」形になった**ことに合わせ、
  経路の書き方のみ実態へ揃える（**規定の内容＝dict 以外を除去する、は変更しない**）。
- 他の節（§5.1 / §5.2 / §5.6 の参照行）は変更しない。

### instructions/common/codebase_map.md

- `normalize_actions` の新設により記述の更新が要るか確認する。**要らなければ変更しない**
  （`.claude/rules/implementation.md`「実装後の必須対応」= クラス構成 / 関数責務 / JSON 構造 / UI 構成に
  変更がある場合のみ更新）。

### .claude_data/state/decisions_archive/23_sequence_payload_action_normalization.md（新規）

- phase 23 の判断履歴を集約する（既存の `decisions_archive/22_mouse_drag_action.md` の書式に倣う）。
  記載する判断: ①案 A 採用（案 B 不採用の理由）②直接改訂モードの選択理由（正本の規定は既に正・注記削除のみ）
  ③`label: ""` 付与という挙動変更の許容と既存テスト期待値の更新 ④保存 JSON の形は不変であることの実測確認。

### .claude_data/state/decisions.md

- 「アーカイブ索引」へ 1 行追加する。

### instructions/phase/current.md

- 「現在の参照先」の phase 23 項を**完了記載**へ更新し、「直近の一連の作業が扱っている領域」を
  phase 23 の内容へ差し替える（完了フェーズはリンクのみ・要約は書かない。current.md「フェーズ完了時の指示」）。
- 「次採番」節は task_01 で 24 へ更新済（再変更しない）。

### instructions/backlog/INDEX.md / INDEX_done.md

- idea_24 の行を完了状態（→ phase 23 / 完了日）へ更新し、`INDEX_done.md` へ**移動**する。

### instructions/phase/23_.../phase.md

- 「タスク」一覧へ完了状態を反映する（task_01 / task_02）。

## 読むファイル

- `instructions/common/spec_detail/data_schema.md` §5.11 冒頭（削除対象の注記）
- `.claude_data/state/decisions_archive/22_mouse_drag_action.md`（書式の手本・冒頭のみ）
- `.claude_data/state/decisions.md`「アーカイブ索引」節
- `instructions/phase/current.md`「現在の参照先」「フェーズ完了時の指示」
- `instructions/backlog/INDEX.md` の idea_24 行 / `INDEX_done.md` の末尾（移動先の書式）
- `instructions/common/codebase_map.md` の config / domain 関連節（更新要否の判断のみ）

## 含まない

- コードの変更（task_01 で完了。本タスクでコードに触らない）
- `actions[]` のスキーマ拡張・他の個別 JSON 読込経路の正規化（フェーズのスコープ外）
- `button` 非文字列の扱いの修正（phase 22 からの別タスク化候補・未着手のまま残す）
- main へのマージ（ユーザーが行う）

## 確認

1. `data_schema.md` §5.11 から【実装未追従】の注記が消えていること。
   **§5.11 以外の【実装未追従】（`:105` のレガシー別名保存パスの件）は別件なので残す**
2. `idea_24` への参照が正本から消え、backlog 側が `INDEX_done.md` に移っていること
   （`INDEX.md` に idea_24 の行が残っていないこと）
3. `decisions.md` の索引リンクが実在ファイルを指すこと
4. `/refactor_check` を実行し、判定結果（要否・根拠 M1〜M6）を完了報告に含めること
5. 文書のみの変更だが、念のため静的確認:
   `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui`

## 完了条件

- 上記確認 1〜5 が pass・**reviewer 採用**（観点: 正本の記述と実装の整合・記録の漏れ）。
- 実機目視: **不要**（UI 変更なし）。
- 本タスク完了をもって phase 23 を完了とする。
