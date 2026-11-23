# decisions_archive: phase 77 サンプルを config/user/ へ書き出す

暫定仕様先行モード（暫定 59 v0.2 凍結）・JSON スキーマ不変・2026-11-24 完了。起票元 = ユーザー要望（2026-11-23・idea なし）。

要点: 初回の「サンプル入り」の書き出し先を `config/sample/` → `config/user/`（構成セット `user/keymap_sets/sample.json`・子の名前は不変）。保存 / 読込のダイアログは開いているファイルのフォルダを優先するため、サンプルを開くと常に `config/sample/` へ案内されていた。構成セットが無いときは書き出す 13 子を `preview_child_payloads` の中身と照合し、違う・読めない・リンク切れがあれば何も書かず incomplete（警告して空で始める）。既存 `config/sample/` は移行しない・孤児の掃除の参照元（経路 5）は残す。昇格先は暫定 59 の冒頭の状態行。

## タスクと実装エージェント

- task_01 書き出し先と衝突照合 4819cdb7 = codex-implementer（Luna high・テスト 2 件の誤りを再依頼で修正）・reviewer 採用。
- task_02 統合確認 15763ad0 / 3543ef3b: 標準検証 4 種 pass（tests 2275・tests_ui 1316・smoke）・deep-reviewer 採用・codex-reviewer 3 件・実機目視 OK（ユーザー）。
- task_02a リンク切れの symlink 70a418f0 = codex-implementer（Luna high）・reviewer 採用（この Windows では symlink を作れずテストは skip）。
- task_03 正本反映（本記録）。refactor_check = 不要（M3 = preview と書き込みの子の並びの 2 か所目〔既知の保留・current.md 別タスク化候補〕・M6 = app.py の直値は既存の重複の値の置き換え・他は該当なし）。

### 【phase 77 起票】サンプルを config/user/ へ書き出す（暫定 59 v0.2・2026-11-23・ユーザー確定）
- 書き出し先を `config/sample/` → `config/user/` → **採用**（理由: 案内先が今開いているファイルのフォルダ優先のため、サンプルを開くと常に `config/sample/` へ案内された。「サンプル設定に戻す」はコードから作るので別フォルダに置く理由がない）。既存 `config/sample/` は**移行しない**・ファイル名はそのまま（ユーザー判断）
- Codex 敵対的レビュー（needs-attention・5 件・引用行は実測済み）の採否（ユーザー承認「案どおりでよい」）: 1 同名の子は書き出す全パスを事前照合 → **採用**（別プロセスとの競合は**除外**）/ 2 途中失敗の再試行 → **修正して採用**（中身が同じ子は衝突にしない）/ 3 利用者自作の同名構成セットがサンプルとして開く → **受容**（明記）/ 4 旧フォルダの「読まない」と経路 5 の維持の矛盾 → **採用**（「書かない・移行しない・読込と参照は続ける」）/ 5 旧サンプルの別名保存で子の案内先は移らない → **採用**（明記・受け入れ条件 3 を新規書き出しに限定）
- 孤児の掃除の参照元 `config/sample/keymap_sets/`（経路 5）は残す（v0.1 起票前の提案「消す」を撤回。旧サンプル経由で参照される `user/` の子の誤退避を防ぐ）

### 【phase 77 task_02 統合確認】deep-reviewer 採用（低・参考 5 件）/ codex-reviewer P2×2・P3×1 の採否（2026-11-24・ユーザー承認「案どおりでよい」）
- Codex ① preview（`validate_save_plan`）が衝突時も空の標準フォルダ（`user/keymaps/` 等）を作る（実測で事実）→ **受容**（普段の保存でも作る標準フォルダ・ファイルは書かない。task_03 で正本に明記）
- Codex ② `user/` の固定名 `.tmp` を上書きし得る → **除外**（アプリの全保存が同じ方式・残った `.tmp` は復旧用ファイルではない・範囲外）
- Codex ③ リンク切れの symlink を `os.path.exists` が「無い」と判定し置き換える → **採用**（task_02a: `os.path.lexists`・テスト 1 件）
- deep ① preview と書き込みの子の並びの二重記述 → **保留**（current.md「別タスク化候補」へ）/ deep ②〜⑤（except の型・相対の直接検査・混在時の error 文・app.py の直値）→ **除外**

### 【task_03 完了判定前レビュー】deep-reviewer 完了可（低 5）/ codex-adversarial-reviewer needs-attention（medium 4）の採否（2026-11-24・ユーザー承認「案どおりでよい」）
- Codex 1 構成セット本体がリンク切れだと「無い」とみなし置き換える（`sample_install.py:63` の `os.path.exists`・実測で事実）→ **採用**（task_03a: `lexists`）
- Codex 3 子の照合で `False == 0`（実測で事実）→ **採用**（task_03a: `json.dumps(sort_keys=True)` の文字列で比較）
- Codex 2 中身が同じ子のリンクが通常ファイルに置き換わる・親のジャンクション経由で旧 `config/sample/` に書き得る → **除外**（リンクで組んだ構成は想定外。正本に「リンク・ジャンクションを使う構成は扱わない」と明記）。deep 3 も同旨で除外
- Codex 4 `check_sample_complete` が個別プリセットの参照を辿らない（phase 73 からの判定）→ **除外**（今回変えていない・自作の同名構成セットを開くのは受容済み）。正本の「辿れる全ファイル」を「キーマップ・トリガー一覧・出力シーケンス」と明記して言い過ぎを直す
- deep 1 凍結後の暫定 59 に未来形の行 → **採用**（削除）/ deep 2 採否前の完了記載 → **採用**（task_03a の後に確定）/ deep 4 警告に英語のパスが並ぶ → **除外** / deep 5 refactor_check の実測記録 → **採用**（下記）
- refactor_check の実測（verifier・PHASE_BASE b98add5d・keyseq 3 ファイル +52 / -4）: M1 = sample_install.py 142 行 +34・save_plan_execution.py 522 行 +20・app.py 983 行 ±0（600 行超は app.py のみで増分 0）/ M2 = 追加関数 2 つとも約 19 行 / M3 = preview と書き込みの子の並びの 2 か所目（既知の保留）/ M4・M5 = 該当なし / M6 = app.py の直値は既存の重複の値の置き換え → **不要**
