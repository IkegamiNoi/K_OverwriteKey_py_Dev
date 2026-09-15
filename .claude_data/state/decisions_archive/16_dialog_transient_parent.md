# decisions_archive / phase 16: ネストしたダイアログの前面維持

対応表: phase 16 / 暫定仕様 14（**凍結済・v0.5**）/ decisions 16。
起票元: [idea_17](../../../instructions/backlog/INDEX_done.md)（phase 14 の受け入れ条件 15・
暫定仕様 12 §6-5 で「フェーズ外・独立 idea」と確定した分離項目）。
完了 2026-09-15。**presentation 限定・スキーマ不変**（正本は `features.md` §4.6 のみ改訂）。
**production の実質変更は 6 行**（+ 本タスクの docstring 2 箇所）。

## 問題

ネストして開いたダイアログが**呼び出し元より前面に留まらない**。
アクション編集からプリセット編集を開いた状態で**アクション編集を掴んで動かすと前面に出る**
（ユーザーが実機で確認・2026-09-13）。原因は、ネストした窓が `grab_modal` の第 2 引数へ
**常に App を渡しており「App より前」としか指定されていない**こと。

## 確定した設計判断（ユーザー 2026-09-13）

| # | 判断 | 採らなかった案と理由 |
|---|---|---|
| 1 | **役割 2（前面維持 = `transient`）だけを直す** | 役割 1（所有関係 = `master`）を動かすと**破棄が連鎖**し、正本 `features.md` の「開いた順と違う順で閉じたら内側を優先する」条項と衝突する（実測確認済）。v0.1 の案 A は撤回 |
| 2 | **役割 3（App 参照 = `self.parent`）も動かさない** | `PresetManagerDialog` は App のメンバを 24 箇所使う。**引数分離も属性名の改名も不要** |
| 3 | **対象は食い違い 2 件とも**（①アクション編集 → プリセット編集 ②プリセット編集 → 上書き確認） | ②は起票時点で実機未確認だが**コード上は同型**。片方だけ直すと非対称が残る |
| 4 | **他 7 ダイアログへ予防的に広げない** | ネストして開く経路が無い窓に引数だけ足すのは過剰実装 |
| 5 | **既定の非対称**（`PresetManagerDialog` は既定 `parent` / `confirm_overwrite` はキーワード必須） | 後者は呼び出し元が 1 箇所のみで既定を置くと**初日から到達しない分岐**になる |
| 6 | **非 LIFO で閉じたときに前面維持の指定が消える点は受容** | 塞ぐには破棄を捕まえて張り直す結線が要り、**UI から到達しない経路のために可動部を増やす**ことになる（§1-④）。**受容した制限は `features.md` §4.6 へ条項として明記**（完了判定前レビュー由来・下記「正本への昇格」） |

## 実装の要点

- `dialogs/preset_manager.py` — `transient_parent`（キーワード・**既定 `None` → `parent`**）を追加し、
  `grab_modal(self, transient_parent if ... else parent)`。**`grab_modal` は `__init__` の最後の文のまま**
  （phase 14 の静的検査が固定）。`on_ok` のコールバックは `confirm_overwrite(..., transient_parent=self)`。
- `dialogs/action_dialog.py:339` — `PresetManagerDialog(self.parent, ..., transient_parent=self)`。
  **第 1 引数（App 参照 = 役割 3）はそのまま**。
- `controllers/config_io/hotkey_presets_io.py` — `confirm_overwrite` へ**キーワード必須**の
  `transient_parent` を追加し、`grab_modal(dialog, transient_parent)`（従来は `self._app`）。
  **`tk.Toplevel(self._app)`（役割 1）は不変**。
- `app.py:418`（メニュー経路）は**無変更**。既定で従来どおり App が相手になる。

## テスト

- 新規 `tests_ui/test_dialog_transient_parent.py`（前面維持の相手 / 所有関係が App のまま /
  既定の非変更）+ `test_nested_modal_grab.py` への追記。**`tests_ui` 321 → 324**。
- **既存テストの変更は引数契約の追随 4 件のみ**（`test_app_ui_flows.py:1201`・`:1261`・`:1313` /
  `test_nested_modal_grab.py:185`）。**grab・生存・復元先・`master` のアサーションは弱めていない**。
- 変異検査 2 件で偽 pass を排除。

## task_04 の指摘処理（ユーザー判定 2026-09-13、**1 は 2026-09-15 に再判定**）

| # | 指摘 | 判定 |
|---|---|---|
| 1 | §1-④ の受容根拠「UI からは到達しない」が誤り（`WM_DELETE_WINDOW` 未登録 = × で直接破棄される） | **取り下げ（2026-09-15）**。実機目視で**背面の × は grab に阻まれて押せず**、非 LIFO 破棄は UI から実行不能と確認。**根拠は元のまま維持**し、暫定仕様へ実測を 1 行追記した。**コード上 × が直接破棄すること自体は事実**だが、到達可能性の根拠にはならない |
| 2 | `PresetManagerDialog` の既定が将来の取り違えを許す | **保留（記録のみ）**。**3 箇所目の呼び出しが出た時点で再検討** |
| 3 | `transient_parent` の事前条件が未定義（破棄済みを渡すと `TclError` で初期化中断 → grab 未取得・フック停止のままの窓が残る） | **修正して採用（契約の明記のみ）**。到達可能性ゼロのため**ガードは足さず** docstring 2 箇所へ 1 行ずつ |
| 4 | T3 が `wait_window` をクラス単位で patch | **保留（現状維持）**。個体 patch は原理的に不可能（確認ダイアログは `confirm_overwrite` 内部で生成）。壊れ方は**偽 fail** で検出力は落ちない |
| 5 | 暫定仕様 §7 の `codebase_map.md` 更新想定が現物と食い違う | **採用**。更新先は `PresetManagerDialog` の項ではなく **`modal.py` の節**（第 2 引数の意味を追記） |
| 6 | 実機目視に「最小化 → 復元」を足す | **採用**（§5-6 として追加 → 実行不能と判明） |

## 実機目視（ユーザー 2026-09-15）

1〜4（前面維持 2 経路 / 既定経路の非退行 / phase 14 の非退行）**問題なし**。

- **5・6 は操作自体が実行不能**。grab を持つ子がいる間、**背面ダイアログの × も最小化ボタンも押せない**。
  これは失敗ではなく**非 LIFO 経路が UI から到達しないことの裏付け**（指摘 1 の再判定の根拠）。
- 6 の代替として Win+D（全最小化）を試した際、**grab を子ダイアログが持つ状態ではアプリを再表示できない**
  別問題を観測 → **[idea_19](../../../instructions/backlog/idea_19_minimize_restore_with_child_grab.md)**。
  **phase 16 由来ではない（実機で確定）**。最初は「grab 保持者が従来から子」を根拠に断定したが、
  `codex-adversarial-reviewer` の指摘 high（**phase 16 が変えたのは `transient` の相手そのもの**）を
  受けて撤回し、**phase 16 で変更していないネスト経路（`preset_dialog.py:40` = プリセット編集 →
  プリセット追加）でも再現する**ことをユーザーが実機で確認して決着した。
  補足として、`b.transient(root)` と `b.transient(a)` の `iconify` → `deiconify` に
  Tk レベルの差が無いことも実測済（ただし Win+D とタスクバー復元は再現できないため補足材料）。

## 正本への昇格

- **`features.md` §4.6 へ 2 条項を追加**（**当初は「改訂なし」の予定を覆した**）:
  「ネストして開いた子は呼び出し元より前面に留まる（親ウィンドウ＝所有関係は変えない）」
  「呼び出し元を先に閉じたら前面維持の指定は戻らない（生存と grab は変わらない）」。
  - **経緯**: 完了判定前の `deep-reviewer` 指摘 1（中）。正本 `spec_detail/` に前面維持の規定が
    **grep 0 件**で、①phase 14・15 は同じ §4.6 へ昇格しているのに phase 16 だけ非昇格という非対称
    ②受容した制限（§1-④）の唯一の記述先が「**本書の条項を実装の根拠に引かない**」と宣言した
    凍結文書になる ③暫定仕様 §7 の非改訂根拠「正本に規定が無い」は**追加すべき理由**であって
    非改訂の根拠にならない、の 3 点。**ユーザー判定 2026-09-15 = 採用**（`/spec_update` で実施）。
  - **役割 1（所有関係）は不変**のため `features.md` ③ の射程は変わらない。
- **`codebase_map.md`** の `presentation/modal.py` の節へ**第 2 引数の意味**を追記
  （前面維持の相手 / ネスト時は呼び出し元を渡す / 所有関係は App のまま）。
- 暫定仕様 14 は **v0.5 で凍結**。

## 分離した項目（このフェーズでやらない）

- **[idea_18](../../../instructions/backlog/idea_18_escape_delivery_flaky_test.md)** — `tests_ui` の
  Escape 依存テストが CPU 負荷下で不定期に fail（**phase 15 時点から存在**・実測で切り分け済）。
- **[idea_19](../../../instructions/backlog/idea_19_minimize_restore_with_child_grab.md)** — Win+D 後に
  アプリを再表示できない（上記）。
- 役割 1 の付け替えと `features.md` の改訂 / 作法の明文化と静的検査 / 他 7 ダイアログへの展開 /
  ダイアログ同型スケルトンの共通化（`current.md` の候補送り）。

## `/refactor_check`（2026-09-15・`PHASE_BASE = 0beb1b4`）

**判定: 不要**（M1〜M6 該当なし。対象 = `keyseq/` の変更 3 ファイル・**+18 / -7 行**）。
メトリクス収集は `verifier`（`.venv` の python / working tree 比較）:

| ファイル | M1 行数 / 増分 | M2 | M3 | M4 | M5 | M6 |
|---|---|---|---|---|---|---|
| `controllers/config_io/hotkey_presets_io.py` | 89 / +5 | なし | なし | なし | なし | なし |
| `dialogs/action_dialog.py` | 340 / ±0 | なし | なし | なし | なし | なし |
| `dialogs/preset_manager.py` | 387 / +6 | なし | なし | なし | なし | なし |

**task_05 の確認**: `compileall` clean / `tests_ui` **324 pass**（task_04 と同数）。
