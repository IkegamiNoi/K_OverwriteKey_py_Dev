# task_01_spec_revision

## 目的

phase 26 の設計を正本へ先に確定する（直接改訂モード・`.claude/rules/spec_change_workflow.md`
「順序の厳守」）。正本 `data_schema.md` §5.4 の条項「保存に成功すると `config/config.json` の
`keymap_set_path` は保存先へ更新される」（`:121`）を、**保存では更新しない（空 / 起動時に読めなかった
場合のみ更新する）** へ差し替える。併せて §5.8.9 の走査経路 3 の根拠文を追従させる。

**文書のみ・実装は task_02**。JSON スキーマ不変（既存キーの書き込み契機のみを変える）。

## 対象範囲（正本ドキュメント限定・2 ファイル）

### `instructions/common/spec_detail/data_schema.md`

`:121` の 1 行を次の内容へ差し替える（箇条書きの階層は既存に合わせる）。

- **保存では `keymap_set_path`（起動エントリ）を更新しない**。変更はファイルメニュー
  「起動時に読む構成セットを指定…」だけが行う（`features.md` §4.6）。**別名保存でも据え置く**
- **例外** = 起動エントリが**未設定**、または**起動時に読めなかった**場合は保存先で更新する
  （自己修復。起動対象を指定しないまま新規作成状態で起動し続けるのを防ぐ）
- **「読めなかった」は起動時の実読込結果で判定する**（保存時にファイルの実在を確かめ直さない）。
  本節の経路 3（未設定 / 不在 / 読込失敗）に該当した起動では、そのセッションの**最初の保存**で
  起動エントリが埋まり、以後は更新しない。**壊れた JSON も自己修復の対象**に含まれる
- 更新しない場合も `config/config.json` の**他のキーは従来どおり書き直す**
  （据え置くのは `keymap_set_path` だけ）
- **別名保存で起動エントリが指すファイル自身を複製した場合も据え置く**。元ファイルが残るため
  起動エントリは有効なままで、次回起動は**別名保存前のファイル**を読む

### `instructions/common/spec_detail/data_schema/5_08_09_orphan_sweep.md`

走査範囲の**経路 3 の根拠文 1 行のみ**（`:26` 付近）を更新する。
現行「通常読込は `config.json` を書かないため、**起動エントリでは代替できない**」を、
**通常読込も保存も起動エントリを書かない**（§5.4）という理由づけへ改める。
**走査範囲の 4 経路そのものは変更しない**。

### 設計メモ / 制約

- 節番号・見出しは変更しない（`.claude/rules/spec_change_workflow.md`「分割後の正本構造」）。
- `data_schema.md:105-110`（`orphan_sweep_scan_dirs` の「config.json は保存で丸ごと書き直される」）は
  **引き続き正しい**ので触らない（保存は今後も config.json 全体を書き直し、据え置くのは
  `keymap_set_path` の値だけ）。
- `features.md:119` はメニュー項目名の記述のみで書き込み契機を含まないため**改訂不要**
  （起票時レビューで確認済）。
- `data_schema.md:143` / `5_08_01_parent_refs.md:50` も空・未保存状態の定義であり**対象外**。
- 経路 3 の箇条書き（`:117`「起動時に `keymap_set_path` が未設定 / 不在 / 読込失敗の場合
  〔無言で空データ起動する〕」）は**変更しない**（通知の追加は phase.md の「含まない」）。

## 読むファイル

- `instructions/common/spec_detail/data_schema.md:104-125` — §5.4 の該当箇所（編集対象）
- `instructions/common/spec_detail/data_schema/5_08_09_orphan_sweep.md:20-32` — 走査範囲 4 経路（編集対象）
- `instructions/phase/26_startup_entry_preservation/phase.md`「確定（ユーザー 2026-09-21）」— 改訂内容の根拠
- `.claude/rules/spec_change_workflow.md`「順序の厳守」「分割後の正本構造」— 改訂の作法

## 含まない

- 実装（`startup_io.py` / `split_payloads.py` 等）とテスト = **task_02**
- `decisions_archive/26` の作成・`current.md` の完了記載・`/refactor_check` = **task_03**
- 起動時に読めなかったときの通知の仕様化（phase.md「含まない」）
- 起動対象の可視化 UI・解除手段の仕様化（phase.md「含まない」）
- `features.md` / `codebase_map.md` の更新（本タスクでは不要。task_02 の実装で
  クラス構成・関数責務が変わる場合は task_02 側で `codebase_map.md` を更新する）

## 確認

- `data_schema.md` §5.4 に、差し替え後の条項が**5 点すべて**含まれる
  （①保存では更新しない ②空 / 読めなかった場合のみ更新 ③判定は起動時の実読込結果 ④他キーは従来どおり書く
  ⑤別名保存でも据え置く）。
- `grep -n "keymap_set_path" instructions/common/spec_detail -r` で、**保存時に更新する**と
  読める記述が他に残っていないこと。
- `5_08_09_orphan_sweep.md` の走査経路が**4 件のまま**で、経路 3 の根拠文だけが変わっていること。
- 節番号・見出しの差分がゼロであること（`git diff` で確認）。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視: **不要**（文書のみ）。
