# task_01_spec_key_input

## 目的

phase 78 の確定事項（ユーザー 2026-11-23）を、実装に先立って正本 `instructions/common/spec_detail/key_input.md` に反映する（直接改訂モード）。
出力シーケンスの hotkey アクションは、保存時（OK）に `validate_hotkey` で全キー名を検査し、通った値を正規化して保存する。
**文書のみ・コード / JSON スキーマ不変。**

## 対象範囲（正本 key_input.md の 2 か所のみ）

### `instructions/common/spec_detail/key_input.md`

- §7.7 L232「hotkey のアクションは保存時にキー名を検査しない・既存。例外: 他方の OS の修飾キーの名前だけは保存時に拒否する」を、次の内容に書き換える。
  - 保存時（OK）の検査の内容: 文法の検査と各キーの `validate_key_name`。プリセット編集と同じ `validate_hotkey` を使う。
  - 検査に通らなければ保存しない。通れば正規化した値を保存する。
  - 他方の OS の修飾キーは、その前に §7.9 の検査で拒否する（文言は今のまま）。
  - 保存済みの値は再検査も移行もしない。実行時の正規化で送り、編集して OK を押せば正規化される。
- §7.9 L346 の hotkey の入口「他方の OS の修飾キーの名前だけを検査（§7.7 の『保存時に検査しない』の例外…）」を、§7.7 の新しい記述に合わせる。参照先の文言が消えるため、L232 と同時に直す。

## 読むファイル

- `instructions/common/spec_detail/key_input.md` の L226-234・L340-348
- `instructions/phase/78_action_hotkey_save_validation/phase.md`

## 含まない

- コードの変更・テスト（task_02）
- `codebase_map.md` の更新（task_03）
- 節番号・見出しの変更

## 確認

- `grep -n "保存時にキー名を検査しない\|だけを検査" instructions/common/spec_detail/key_input.md` が 0 件
- 改訂後の L232・L346 の記述が phase.md の「確定」3 点と一致し、相互参照が残っていること

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視なし（文書のみ）。
