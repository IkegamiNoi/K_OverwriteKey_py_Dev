# task_06_spec_promotion

## 目的

phase 59 の最終タスク。暫定 43 v0.6 を正本へ昇格して凍結し、判断履歴を集約し、フェーズの完了記載と `/refactor_check` を行う（`.claude/rules/task_execution.md`「フェーズ完了時」・暫定 43 §7・task_05 の中-2 / 低-4）。
**文書作業（メインセッション）。コードは変えない。**

## 対象範囲

- 正本への昇格: `features.md` §4.3「割り当て禁止のキー」（禁止のキー・キーボードUI・切替キーの取得と検査〔変えたときだけ〕・`??` の案内・既存データ〔読込・個別読込・貼り付けは検査しない〕・受容〔JIS の Caps 単独のフック側の名前は未実測〕）/
  §4.6「キーボード表示のウィンドウ」（左右の修飾キーの表・割り当て禁止の枠・レイアウトの JSON の左右の修飾キー〔`alt_gr`・`scan_code` を書かない・見本〕）/ `key_input.md` §7.1（左右の修飾キーの名前・AltGr 配列の右 Alt）・§7.4（切替キーの取得）
- `codebase_map.md`: `keyboard_window.py`・`hook_button_texts.py`・2 つの切替キーのダイアログの行 / phase 59 の節（`domain/key_identifiers.py` の禁止の判定・使う側・見本の追跡・テスト）
- 暫定 43 の凍結 / `decisions_archive/59_keyboard_ui_left_right_modifiers.md`・decisions.md の索引 / current.md の完了記載（次採番 = phase 60 / 暫定 44 / decisions 60 / 提案書 25）
- `/refactor_check`（M1〜M6 は verifier・判定はメイン）
- 完了判定前のレビュー（`deep-reviewer` + `codex-adversarial-reviewer`）
- 起票元 idea は無い（backlog の移動は不要。idea_46・idea_47 は本フェーズで起票した残件）

## 含まない

- コードの変更

## 確認

- 正本の各節が暫定 43 v0.6 と decisions phase 59 の決定に一致する（完了判定前レビューで確認）

## 完了条件

- 上記がすべて済み、完了判定前レビューの採用分を反映・`/refactor_check` の判定を完了報告に記載
