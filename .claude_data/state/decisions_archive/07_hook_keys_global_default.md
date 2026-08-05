# decisions_archive: 07_hook_keys_global_default（保存系リデザイン Phase γ）

> Phase γ（`instructions/phase/07_hook_keys_global_default`・2026-08-03 起票 / **2026-08-05 完了**）の判断履歴。
> 設計の経緯は暫定仕様 [06](../../instructions/history/06_hook_keys_global_default.md)（v0.2・凍結済み）、
> 確定仕様は正本 `instructions/common/spec_detail/data_schema.md` **§5.9** +
> `spec_detail/key_input.md` **§7.6** + `instructions/common/codebase_map.md` が正。
> 受入条件と実機目視シナリオは
> `instructions/phase/07_hook_keys_global_default/tasks/task_07_integration_check.md`。

## 2026-08-03〜 (phase 07 = 保存系リデザイン Phase γ: hook キーの全体デフォルト化)

規範: `instructions/phase/07_hook_keys_global_default/phase.md`。
主入力（確定設計）= `instructions/history/06_hook_keys_global_default.md`（v0.2・ユーザー確定済 2026-07-27）。
モード = **暫定仕様先行モード**。番号対応: **phase 07 / 暫定 06 / decisions_archive 07**。

### 【起票】タスク分割と読むファイルの補正（2026-08-03）
- task_01 スキーマ/移行判定 → 02 キー解決点 → 03 保存時挙動 → 04 全体デフォルト更新 API（成否付き）→
  05 チェック UI → 06 所有者切替 capture → 07 統合確認 → 08 正本反映、の 8 タスク。
  **02 と 03 は 01 完了後なら並行可**。
- **暫定仕様 06 の「現状監査」の行番号は計画05 の分割で無効**になっていたため、phase.md
  「このフェーズで読むファイル」で現在の所在へ差し替えた（読込 = `config_service/split_loading.py` /
  保存 = `config_service/split_payloads.py`）。reviewer の整合確認で実ファイルとの一致を検証済み。

### 【task_01】完了（2026-08-03）
- `domain/config.py` のみ変更。`DEFAULT_CONFIG` へ `hook_keys_individual: False` +
  純関数 `resolve_hook_keys_individual(source)` を新設し、`ensure_config_compatibility` の
  hook キー正規化**直後**で呼ぶ（正規化後の値で判定させるため位置が重要）。
- **明示フラグの有無は `in` で判定**する（`.get()` の真偽で見ると `false` とキー無しを区別できず
  移行規則が壊れる）。フラグがあれば中身を見ずに `bool()`、無ければ
  「正規化後どちらか非空 → ON」。
- **冪等性を要件に含めた**: 「フラグ True のまま両キーが空」で False へ落ちると、
  暫定仕様 §2 の「ON→OFF で個別値を内部保持」が壊れるため。テストで固定済み。
- **split 経路ではこの移行は発火しない**（`build_runtime_data_from_split` は
  `new_default_data()` = フラグを含む土台から始まるため、最後の
  `ensure_config_compatibility` 時点でフラグが常に存在する）。
  **生の keymap_set dict に対して `resolve_hook_keys_individual` を呼ぶのは task_02 の責務**。
- 懸念していた**保存 JSON バイト列比較テストの破壊は発生しなかった**
  （keymap_set への書き出しは `split_payloads.py` の明示キー列挙のため）。
- 検証: compile clean / tests **155 pass**（145 + 追加 10）/ tests_ui 159 pass / smoke pass。
  reviewer = **完了可・指摘なし**。

### 【task_02】完了（2026-08-03）
- **キー解決点を 2 本の関数に集約**: `split_loading.load_global_hook_keys(service, config_root)`
  （config.json の全体デフォルト読み出し・正規化・失敗時 `("", "")` へ縮退）と、
  公開 API `ConfigService.apply_global_hook_key_defaults(runtime, config_root)`（OFF のみ注入・冪等）。
  **フック層（`input_router` / `hook_controller` / `keyboard_window` / `app.py`）は無変更**
  ＝ 暫定仕様 §3 の「常に解決済みの値を見る」を満たす。
- **移行判定に渡すのは生の `keymap_set` dict**（task_01 の申し送りどおり）。hook キーのコピーループの
  タプルへ `hook_keys_individual` を**追加しない**（明示代入で一本化・二重経路を作らない）。
- **注入は読込時だけでは足りない**（受入条件 2「新規作成で再設定不要」）。新しい runtime を生成する
  presentation 3 箇所（`keymap_set_io.new_config` / `restore_default` /
  `startup_io.load_startup_and_config` の空データフォールバック）からも API を呼ぶ。
  **`app.py:76` は対象外**（直後に `load_startup_and_config` が必ず上書きするため）。
- **tests_ui 3 件の期待値を更新**（`test_config_io_characterization_keymap_set_startup.py`）。
  スタブ dict（`{"empty": True}` / `{"d": 1}`）へ注入結果の空 hook キー 2 個が加わったため。
  **実装ではなくテスト側の追従**であり、実 runtime では `new_default_data()` が既に両キーを持つので
  実挙動の変化ではない（config.json 未設定時の注入値は空文字）。
- 検証: compile clean / tests **164 pass**（155 + 追加 9）/ tests_ui 159 pass / smoke pass。
  **保存 JSON のバイト列比較テストは無修正で pass**（本タスクは保存経路を触らない）。
  reviewer = **完了可・指摘なし**。

### 【task_03】完了（2026-08-03）
- 保存時の分岐は `split_payloads.build_keymap_set_payload` の **1 関数のみ**に閉じた。
  ON = 個別値をそのまま保存 / OFF = `hook_stop_key` / `hook_toggle_key` を **`""`** で書き出し
  `hook_keys_individual: false`。**キー自体は 3 つとも常に出力**（既存キー削除禁止）。
- **OFF 時に書くのは `""` であって `runtime.get(...)` ではない**（最も壊しやすい点）。
  OFF の runtime は task_02 で全体デフォルトが注入済みのため、そのまま書くと
  **全体デフォルトが keymap_set へ焼き付き**、次回読込で移行判定が「個別値あり」と誤発火する。
- **判定は `resolve_hook_keys_individual(runtime)` を通す**（`.get()` の真偽で見ない）。
  `build_keymap_set_payload` を直接呼ぶ経路（テスト等）はフラグを持たないため、
  純関数側の移行規則に載せることで**フラグ無しの旧 runtime は従来どおり個別値を保存**（後方互換）。
- **`runtime` は書き換えない**（payload 生成は副作用なし）。runtime の hook キーは
  OFF のとき解決済みの全体デフォルトを保持しており、フック層がこれを直読みするため。
- **tests_ui 1 件が fail → テスト側追従で解消**（想定内の唯一の破壊）:
  `_prepare_loaded_keymap_set` が `hook_keys_individual` 未設定のまま `hook_stop_key="f12"` を置いており、
  新契約では保存時に空文字化されて**既定復元後のファイルとバイト一致**してしまい
  `test_restore_default_overwrites_named_parent_and_trigger_set_but_not_sequences` の
  `assertNotEqual` が落ちた。フィクスチャの意図（個別指定された停止キー）どおり
  `hook_keys_individual = True` を明示して解消。**実装側の問題ではない**。
- **申し送り（task_06）**: 「OFF 保存後にセッション内保持していた個別値も破棄する」処理は本タスク範囲外。
  保持先が UI 側の状態のため task_06 が担当する。
- 検証: compile clean / tests **168 pass**（164 + 追加 4）/ tests_ui 159 pass / smoke pass。
  reviewer = **完了可・指摘なし**。

### 【task_04】完了（2026-08-03）
- **全体デフォルトの書き込み API は presentation（`StartupIo`）に置いた**。
  `write_startup` を `-> bool` 化（成功 True / 例外捕捉 False。既存の `base` 組み立て・
  `coerce_font_delta`・`showerror` は不変）+ `write_global_hook_keys(*, stop_key, toggle_key) -> bool` を新設。
  正規化は `normalize_key_name`（presentation → domain の直接 import は既存 14 ファイルの踏襲）。
- **書き込み経路を `write_startup` の 1 本に集約した理由**（最も壊しやすい点）:
  `_startup_settings`（in-memory の起動設定）と config.json が乖離すると、次の `write_startup`
  （フォント変更・keymap_set パス記録）が**古い `_startup_settings` を土台に上書きして hook キーを消す**。
  そのため ConfigService へ独自の read-modify-write な保存 API を作らなかった。
- **失敗時の旧値維持**は `self._app._startup_settings = base` が `try` 内・保存成功後にある
  既存構造で成立する。**この代入位置を動かさない**（受入条件 7）。
- keymap_set 保存カスケード（`keymap_set_io.py:116` → `build_startup_payload`）は `startup_data` を
  丸ごとコピーするため**全体デフォルトは自動的に維持される**。hook キー用の分岐を足さず、
  テストで固定した（確認 5）。
- **API を呼ぶコードは書いていない**（UI 配線 = task_05 / capture とランタイム反映 = task_06）。
- タスク定義の記述ミス 1 件を是正: 読み出し API を `ConfigService.load_global_hook_keys` と書いていたが
  実体は `split_loading.load_global_hook_keys(service, config_root=...)`（+ 公開 API は
  `apply_global_hook_key_defaults`）。Codex が実装時に指摘し、定義側を修正した。
- 検証: compile clean / tests **168 pass**（presentation 限定のため増減なし）/
  tests_ui **165 pass**（159 + 追加 6）/ smoke pass。reviewer = **完了可・指摘なし**。

### 【task_05】完了（2026-08-03）
- **チェック UI は presentation に閉じた 4 ファイル**: `ui_vars.hook_keys_individual_var`（BooleanVar・
  full / compact が**同一インスタンスを共有**）/ `app._sync_control_vars_from_data` へ 1 行（data → Var）/
  `App.toggle_hook_keys_individual`（Var → data + dirty）/ full・compact の `hook_frame` に
  `ttk.Checkbutton`（`full_hook_line2` / `compact_hook_line2` の row=2・grid 構造は不変）。
- **同期の入口は 2 本だけ**（data → Var = `_sync_control_vars_from_data` / Var → data =
  `toggle_hook_keys_individual`）。`apply_loaded_data_to_ui` / `new_config` / `restore_default` は
  既に前者を呼ぶため**無変更で追従**する。
- **チェック操作は dirty にする**。`hook_keys_individual` は keymap_set に保存される値のため。
  暫定仕様 §4 の「dirty 非汚染」は **OFF 時のキー編集**に対する要件でありチェック操作は対象外。
- **compact のチェックは表示専用（`state="disabled"`・`command` 無し）＝ユーザー確定（2026-08-03）**。
  compact のフックキーは既に readonly Entry のみで capture / clear を持たない＝「compact は表示のみ」
  という既存方針に合わせた判断。**確定済みのため task_07 で再確認しない**。
- **reviewer 指摘 1 件を修正して採用**: 確認 3（移行で ON になる keymap_set を読むとチェックが ON）が
  `app.data` への直接代入 + `apply_loaded_data_to_ui` の直呼びで代替されており、**移行判定を
  バイパスしていた**。実ファイル（フラグ無し・stop のみ非空 / 両方空）を
  `load_runtime_data_from_keymap_set_path` で読む特性テストをメインで追加して解消。
- 検証: compile clean / tests **168 pass**（presentation 限定のため増減なし）/
  tests_ui **169 pass**（165 → Codex 追加 3 → 指摘対応 +1）/ smoke pass。

### 【task_06 起票時】task_06 を 06 / 06b へ分割（2026-08-03）
- phase.md の task_06 は「所有者切替 capture + dirty 非汚染 + ON⇄OFF 表示切替 + 個別値の内部保持」を
  1 タスクに束ねていたが**範囲が広すぎる**ため、**06（書き込み先の切替と dirty 非汚染）**と
  **06b（表示切替と個別値のセッション内保持・OFF 保存後の破棄）**へ分割した。
  phase.md のタスク表と依存の並びも更新済み。

### 【task_06】完了（2026-08-03）
- **hook キーへの書き込み点を `SingleKeyCaptureController._apply_key` の 1 本へ集約**した
  （従来は `clear()` と `on_keypress()` の 2 箇所に散っていた）。
  ON = `app.data` 更新 + Var 反映 + dirty（従来どおり）/ OFF = `write_global_hook_keys` で
  config.json を更新し、**成功時のみ** `app.data` と Var を確定（§3 の即反映）。
- **dirty 非汚染は `DirtyStateTracker.capture_dirty_snapshot` / `restore_dirty_snapshot`**
  （記録対象は `is_dirty` / `config_dirty` の 2 つ。個別 dirty フラグは capture が触らないため対象外）。
  **`try` / `finally` で復元**するため例外経路でも汚れない（phase.md レビュー方針 3）。
  ユーザー案（暫定仕様 §4 の「OFF 前の dirty を記録し操作後に復元」）をそのまま実装したもので、
  「OFF なら `set_dirty` を呼ばないだけ」に簡略化していない（間接的な dirty 化にも耐えるため）。
- **既存挙動の維持**: `clear()` の「旧値が空なら dirty にしない」は `mark_dirty=bool(old)` で表現。
  OFF 経路では `mark_dirty` は使われない（snapshot 復元が優先されるため無害）。
- **OFF では 2 キーとも書く**（`write_global_hook_keys` が 2 キー同時指定の API のため）。
  更新しない側は `app.data` の現在値＝現在の全体デフォルトをそのまま再書き込みする。
- 保存失敗（偽 or 例外）時は **runtime も Var も書き換えない**（受入条件 7）。
  エラー表示は `write_startup` の `showerror` が既に行うため二重に出さない。
- 検証: compile clean / tests **168 pass**（presentation 限定のため増減なし）/
  tests_ui **173 pass**（169 → +4）/ smoke pass。reviewer = **完了可・指摘なし**。

### 【task_06b】完了（2026-08-03）
- **退避先は App が持つ `_retained_hook_keys`**（`app.data` の内部キーにしない = 保存経路・スキーマへ
  影響させない）。`toggle_hook_keys_individual` を拡張し、**ON→OFF で退避 → OFF→ON で復元（復元時に消費）**。
- **順序が重要**: `hook_keys_individual` を data へ書いた**後**に `apply_global_hook_key_defaults` を呼ぶ
  （この API はフラグが真なら何もしないため、逆順だと注入されない）。
- **退避が無い OFF→ON は両キーを `""` にする**（全体デフォルト値を個別値として引き継がない）。
  引き継ぐと全体デフォルトが keymap_set へ焼き付く。OFF の keymap_set は保存時に空文字化され（task_03）、
  読込時も個別値を runtime へ持ち込まない（task_02）ため `""` が唯一整合する値。
- **破棄は 4 箇所**（`keymap_set_io`）: `save_keymap_set_to` の**保存成功後** /
  `apply_loaded_data_to_ui` の先頭 / `new_config` / `restore_default`。
  保存失敗時は破棄に到達しない経路になっており「保存成功時のみ破棄」を満たす。
  **`_sync_control_vars_from_data` の中に破棄を入れてはいけない**（toggle 自身が呼ぶため退避が即消える）。
- 検証: compile clean / tests **168 pass**（増減なし）/ tests_ui **176 pass**（173 → +3）/ smoke pass。
  reviewer = **完了可・指摘なし**。

### 【task_07】統合確認・完了（自動確認 2026-08-03 / **実機目視 2026-08-05 OK**）

- **実機目視 G1〜G9 はすべて OK**（ユーザー実施・2026-08-05 報告）。中核の G1（OFF 編集で dirty に
  ならない）と G7（OFF 保存後は再 ON しても空）を含め、異常なし → task_08 へ進む条件を充足。

- 自動確認は全 pass（compile clean / tests 168 / tests_ui 176 / smoke）。**フック層は無変更**を
  `git diff caf41a7..HEAD` で実測確認（`application/input_router.py` / `hook_controller.py` /
  `keyboard_window.py` / `app.py` のフック供給部 `:96-109`）。受入条件 1〜7 は実装・テストで充足。
- レビューは **`deep-reviewer`（条件付き完了可）+ `codex-adversarial-reviewer`（needs-attention）**の併用。
  **両者が独立に「単一 JSON Import 経路で全体デフォルトが注入されない」を指摘**（＝実害あり）。
- **ユーザー判断（2026-08-03）: 指摘 A〜D の 4 件すべてを採用**（task_07b で是正）。
  D（起動 keymap_set パスの成否確認）は**hook キーと無関係でスコープ外**と提示したうえでの採用。
- **task_08 へ持ち越す指摘 E**（実装変更はせず**正本で契約として明記**する）:
  ① 全体デフォルトのキー衝突検証は**カレント keymap_set 内に閉じている**
  （セット A の全体デフォルトがセット B のトリガーを黙って無効化しうる。`input_router` では
  stop/toggle がトリガーより優先）/ ② **「明示 `false` + 非空個別値」の keymap_set** は
  読込→保存で個別値が失われる（本実装は生成しないが手編集・別実装由来では起こりうる）。
- **除外した指摘**: `resolve_hook_keys_individual` の非 bool 値の扱い（過剰実装）/
  `write_startup` の失敗ダイアログ文言 `"startup.json 保存失敗"`（実体は config.json。
  テスト 2 箇所が文言を固定しているため独立タスク扱い）。

### 【task_07b】完了（2026-08-03・レビュー指摘 A〜D の是正）
- **A**: `import_config` に `apply_global_hook_key_defaults` を 1 行追加。
  この経路だけ解決点を通らず、OFF なのにキーが空でフックが無反応だった（受入条件 1 の不変条件が破れていた）。
  **注入点は 3 箇所 → 4 箇所**（new_config / restore_default / 空データフォールバック / **Import**）。
- **B**: `apply_global_hook_key_defaults` の先頭へ `runtime.setdefault("hook_keys_individual", False)`。
  保存側が移行ヒューリスティック（`resolve_hook_keys_individual`）で判定するため、
  フラグ無し dict へ注入 → 保存で**全体デフォルトが焼き付く**構造的な穴があった。
  tests_ui のスタブ dict 期待値 3 箇所はテスト側追従。
- **C**: `discard_retained_hook_keys()` を保存成功後 → **`save_runtime_data` の直前**へ移動。
  保存は keymap_set（`save_plan_execution.py:138`）→ config.json（`:139`）の順で書くため、
  後段の失敗で退避が残り**再 ON で復活**しうる窓があった。**境界は「保存を実行した時点」**に変更。
  保存中止（`save_plan is None`）は早期 return が手前にあるため**退避が残る**（維持）。
- **D**: `set_startup_keymap_set` で `write_startup` の成否を見て、失敗時は成功表明
  （`showinfo` と成功フラッシュ）をしない。**エラーダイアログは `write_startup` が既に出すため二重にしない**。
  読み込んだデータの UI 反映自体は従来どおり行う（runtime は既に差し替わっており巻き戻しは範囲外）。
- 検証: compile clean / tests **169 pass**（168 → +1）/ tests_ui **178 pass**（176 → +2）/ smoke pass。
  reviewer = **完了可・指摘なし**。

### 【task_08】完了（2026-08-05・正本反映とフェーズ完了）

- **昇格先**: `spec_detail/data_schema.md` **§5.9**（5.9.1 データモデル / 5.9.2 解決順序 /
  5.9.3 移行規則 / 5.9.4 編集と保存の契約 / 5.9.5 既知の制約）+ `spec_detail/key_input.md` **§7.6**
  （供給源とフック挙動）+ `codebase_map.md`（責務）。**既存節は無改変**（追記のみ・節番号を動かさない）。
  暫定仕様 06 は**凍結**（本文の仕様記述は不変・昇格先を冒頭へ明記）。
- **指摘 E は実装を変えず契約として明記**（§5.9.5）: ① キー衝突検証はカレント keymap_set 内に閉じる
  （停止/トグルがトリガーより優先。`input_router` で実測確認済）② 「明示 `false` + 非空個別値」は
  読込→保存で個別値が失われる。
- **フェーズ完了判定レビュー = `deep-reviewer`（修正要・軽微）+ `codex-adversarial-reviewer`
  （needs-attention）**の併用。**ユーザー判断（2026-08-05）: 指摘 A〜H を採用 / I（3 件）は保留**。
  - **A（Codex high・最重要）**: §5.9.2 の「偽 / **未設定**なら注入」が §5.9.3 の移行規則と矛盾していた。
    実装は `split_loading.py:57-59` で**移行判定を先に評価**してから注入する。文言どおりに再実装すると
    **旧 keymap_set の個別キーを全体デフォルトで潰す後方互換回帰**になるため、
    「§5.9.3 の移行判定で確定させた値を見る」+「**注入 API 側はフラグ無しを OFF とみなす**（task_07b の B）」の
    2 段構えへ書き換えた。**移行判定を適用するのは読込経路のみ**という取り違え防止を明記。
  - **B（Codex med）/ G**: codebase_map の「解決点は 2 本」は**通常読込の分岐点を隠していた**。
    実際の分岐は 4 つ（`load_global_hook_keys` = 読み出し / `build_runtime_data_from_split` = 通常読込の選択 /
    `apply_global_hook_key_defaults` = 新規化・置換経路の直接注入・**通常読込は経由しない** /
    `build_keymap_set_payload` = 保存側）。`resolve_hook_keys_individual` の**渡すデータが 3 系統で違う**
    （読込=生 keymap_set / 保存=runtime / 互換化）点も明記。
  - **C / D / E**: §5.9.4 へ 3 点追記 — 内部保持の破棄は保存の実行に加え**runtime の置換・新規化
    （読込 / 新規作成 / 例を復元）でも行う** / **チェック操作自体は dirty にする**（dirty 非汚染は
    キー取得・クリアに対する規定）/ ON 側の dirty は**値が変わる場合**（`clear()` は旧値が空なら
    dirty にしない既存挙動）。
  - **F**: `phase.md` に完了記述を追加。`session.md` / `handoff.md` は `/save_state` + `/save_handoff` で再生成。
  - **H**: 提案書 06 の M3 計数を是正（`discard_retained_hook_keys` は 3 → **4 箇所**）。判定は不変。
  - **保留（I）**: 「全体デフォルトを書くのは 1 本のみ」の厳密化（`build_startup_payload` も
    `_startup_settings` 経由で config.json を書き直すが乖離は起きない）/ decisions_archive の相対リンク書式
    （**既存アーカイブ全件が同形式**のため横断案件）/ §5.5 から §5.9 への相互参照（既存節無改変の制約）。
- **`/refactor_check` 判定 = 推奨**（`PHASE_BASE = caf41a7` / 対象 12 ファイル・+171 / -12）。
  **M4 のみ該当**（stop/toggle を対で列挙する箇所が 5 → 10）→ 提案書
  `instructions/modified_proposal/06_refactor_hook_key_pair_enumeration.md` を起票（**未承認**・
  推奨は「(c) 見送り または (b) ミニフェーズ」）。M1 は 600 行超だが増分 +13 で非該当、M2/M5/M6 非該当。
  **M3 は非該当だが候補送り**（runtime を新規化・置換する入口 4 経路がそれぞれ注入 API を呼ぶ規約＝
  task_07b の指摘 A の温床。入口の一本化は設計変更のため挙動保存の範囲外。phase 08 で同型が出たら併せて設計）。
- 文書のみの変更のため回帰テストは再実行せず、`git diff -- keyseq tests tests_ui` が**空**であることで担保した
  （最終実測値は task_07b の compile clean / tests 169 / tests_ui 178 / smoke pass）。
