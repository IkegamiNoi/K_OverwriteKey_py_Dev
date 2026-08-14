# task_07d_external_path_read

## 目的

**config 外を指す個別パスを、読み出しでは有効として扱う**（暫定仕様 08 **§2【O2】【O】/ §3-2**
〔v0.8 で改訂〕・受入条件 **15**）。**書き込みは従来どおり管理下の既定パスへ寄せる**【O3】ため、
外部パスは「**初回に内容を拾うための移行導線**」になり、個別 ON での保存が成功した時点で
`hotkey_presets_path` が管理下の値へ置き換わる（v0.6 の dirty 規則）。

task_07 の実機目視（項目 10）でのユーザー確認により、v0.7 までの「読み出しも無効にしてグローバルへ倒す」
を改める。

**レイヤ制約**: **application（読み出し用のパス解決の分離・状態判定）+ presentation（文言）**。
**書き込み側の解決（task_04 / task_05c）不変・【O4】ガード（task_07b）不変・
`build_keymap_set_payload` 不変・スキーマ不変**。

## 対象範囲

### 1. `keyseq/application/config_service/split_loading.py` — 読み出し用のパス解決を分離

現在の `resolve_individual_hotkey_presets_path`（`:99-116`）は
**「フラグ真 + 非空 + config 配下」でなければ空文字**を返し、**読み出し・状態判定・書き込み・
別名保存の複製元**の 4 箇所すべてがこれを使っている。**書き込み側の意味は変えられない**ため、
**読み出し用の解決を分ける**。

- **読み出し用**（新規。名前は実装者判断・例 `resolve_individual_hotkey_presets_read_path`）:
  **フラグが真 + `hotkey_presets_path` が非空**なら、**config 配下かどうかを問わずその表記を返す**。
- **書き込み用**（既存 `resolve_individual_hotkey_presets_path`）: **現状のまま**
  （config 外は空文字 →【O3】で既定パスへ寄る）。
  **`resolve_hotkey_presets_save_path` / `relocate_individual_hotkey_presets` /
  `individual_hotkey_presets_save_rejection_reason` の挙動を変えない**。
- **`build_runtime_data_from_split`（`:273-290`）は読み出し用を使う**。
  読めなければ従来どおり**グローバルへフォールバック**【C】→ それも読めなければ**置き換えない**。

### 2. 同 `describe_hotkey_presets_source` — 状態判定の意味を合わせる

現在の `individual_state` は `off` / `active` / `missing` / **`invalid`**（= config 外）。
**`invalid` の「読めない」前提が成り立たなくなる**ため、**マネージャが次を出し分けられる情報**を返す:

- 個別が **config 配下で読めた** … 従来の `active`
- 個別が **config 外だが読めた** … **「config 外のファイルを読み込み中」**と分かる状態
- 個別が **読めない**（config 内外を問わない） … グローバルへフォールバック中と分かる状態
- OFF … 従来の `off`

**状態値の設計（`invalid` の意味変更 / 値の追加）は実装者判断**でよいが、
**`displayed_source`（`individual` / `global` / `builtin`）の意味は変えない**。
`tests_ui/test_app_ui_flows.py` が `format_preset_manager_source_labels` を**直接呼んで文言を固定**
しているため、**状態値を変えたらそのテストも更新する**（本タスクの実装範囲）。

### 3. `keyseq/presentation/dialogs.py` — 文言（`format_preset_manager_source_labels` `:16-51`）

`individual_state == "invalid"` の 2 分岐（`:33-44`）を **v0.8 の【R】**に合わせて書き換える。

- **config 外だが読めた**（＝いまその内容を表示している）…
  **「config 外のファイルを読み込み中。次の保存で管理下へ移ります」**旨 + **これから書く既定パス**
  （`default_individual_path`）。
- **config 外で読めない** … 従来どおりグローバル / 組込既定へのフォールバック表示に加え、
  **記録されていた保存先が config 外である旨**と**これから書く既定パス**。
- **「無効」という語は使わない**（v0.8 で無効判定は書き込み側だけの概念になったため）。
- **保存先の表示（`save_destination`）は変えない**（＝書き込み側の解決に追従したまま）。

### 設計メモ / 制約

- **`_resolve_config_relative_path` / `_load_optional_json` は config 外の絶対パスをそのまま扱える**
  （相対値だけ config_root 基準で解決される）。**新しいパス解決を書かない**。
- **読み出しの正規化は 1 箇所のまま**（`load_hotkey_presets_file` → `normalize_hotkey_presets`）。
  **非文字列 `label`/`value` の除去を緩めない**（起動不能の再発防止。session.md の resume_hints）。
- **例外を握り潰す範囲を広げない**。`load_hotkey_presets_file` の `try` は現状のままで、
  到達不能パス・権限エラーは**従来どおり `None`**（＝グローバルへフォールバック）になる。
- **【既知の制約】読み出しは同期実行**のため、到達不能な UNC / 切断されたネットワークドライブを
  指していると読み込み中は UI が待たされる（trigger_set・keymap の読み出しと同じ性質。
  **本フェーズで非同期化はしない**）。
- **OFF で保存した場合、外部パスは置き換わらない**（書込先がグローバルで【O3】が発火しないため。
  【N】でそのまま保持され、次に ON へ戻したときに【O3】で寄せられる）。**これは仕様どおり**で、
  受入条件 15 もこの区別込みで判定する。

## 含まない

- **書き込み側を config 外へ許すこと**（【O】は書き込み側の制約として維持）
- **外部ファイルの削除・移動・自動コピー**（内容は次の個別保存で管理下へ書かれる。
  **別名保存の複製【L】も対象外** = 複製元の解決は書き込み側を使うため config 外からは複製しない）
- **残置パスの遮断**（v0.8【§3-5】）→ **task_07c**
- **トグル時の一覧の読み直し・破棄確認・OFF での書き込み**（v0.8【I】【H2 撤回】）→ **task_07e**
- 破損プリセットの検知・警告・退避（暫定仕様 §6 でスコープ外）
- 正本 `spec_detail/` への反映・`codebase_map.md` 更新 → **task_08**

## 確認

`.venv` の python で実行（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。実測は `verifier`。

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests` が **pass**（基準線 **229** + task_07c 追加分 + 本タスク追加分）
- `-m unittest discover -s tests_ui` が **pass**（基準線 **206** + 同上）
- `-m tests.smoke_app` が pass

### テスト（追加まで実装範囲。**実行は依頼しない**）

**`tests/test_config_service.py`**:

1. **config 外を読む**: フラグ true + `hotkey_presets_path` = **config_root の外**（tmp 配下の別ディレクトリ）に
   実体があるとき、**runtime のプリセットがその外部ファイルの内容**になる（グローバルへ倒れない）。
2. **読めなければグローバル**: 同じ設定で**外部ファイルが存在しない**と、**グローバルの内容**になる。
   グローバルも読めなければ**置き換えない**（組込既定のまま）。
3. **書き込み側は不変**: 1 の runtime に対し `resolve_hotkey_presets_save_path(..., individual=True)` が
   **`user/hotkey_presets/<stem>.json`**（管理下の既定パス）を返す。**外部パスを返さない**。
4. **状態判定**: 1 は「config 外だが読めた」、2 は「読めない」と区別できる値が返る。
5. **キーの値は書き換えない**: 読み込みで `hotkey_presets_path` の値が変化しない。

**`tests_ui/test_app_ui_flows.py`**:

6. **文言**: `format_preset_manager_source_labels` が、config 外で読めた状態のとき
   **「次の保存で管理下へ移る」旨 + 既定パス**を含む文字列を返す（**「無効」の語を含まない**）。
   既存の文言テスト（`invalid` / `invalid_while_global` の 2 ケース）を**新しい状態値・文言へ更新**する。
7. **保存で管理下へ移る**: config 外パスの状態で `save_hotkey_presets(..., individual=True)` を呼ぶと、
   **`user/hotkey_presets/<stem>.json` が作られ**、**`app.data["hotkey_presets_path"]` が管理下の値へ
   置き換わり**、**dirty が立つ**。**外部ファイルは変更されない**。

## 完了条件

- 上記確認がすべて pass し、**`reviewer` 採用**（観点: **書き込み側の解決を変えていない**か
  〔`resolve_hotkey_presets_save_path` / 複製 /【O4】ガードの挙動不変〕/ 読み出し用と書き込み用の
  **2 本立てが混線していない**か / `displayed_source` の意味を変えていないか /
  例外の握り潰し範囲を広げていないか / 新しいパス解決を自作していないか /
  後続タスク（07e / 08）の先取りがないか）。
- **実機目視は task_07 の観点リスト（項目 10 / 11）でまとめて実施**する（本タスクでは行わない）。
