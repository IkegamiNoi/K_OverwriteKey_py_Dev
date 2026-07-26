# 暫定仕様 03: ConfigIoController の責務分割（config_io_controller_split）

> 状態: **凍結・v0.4・正本反映済（2026-07-26・phase 04 task_06）**。本書はこのフェーズの確定設計であり、
> 以後は編集しない（履歴として凍結）。正本反映の結果は下記「§8 正本反映」および
> `.claude_data/state/decisions_archive/04_config_io_controller_split.md` を参照。
> **spec_detail への昇格は不要**（`config_io` の言及が spec_detail に 0 件・再 grep 済。担当層は
> `architecture.md §3.5` により `codebase_map.md` が正）。`codebase_map.md` の「コントローラ（controllers/）」節と
> ツリー図を分割後の6クラス構成へ更新済。
> 版履歴: v0.1 起票（2026-07-23）→ **v0.2** reviewer 指摘 2 件を反映（§4 の恒久ファサード案を
> 除外し 3 案へ再編 / §7 条件 2 に `load_startup_and_config` の 3 分岐を追加）→
> **v0.3** 敵対的レビュー指摘 4 件を反映（§1 に「既存の不整合」節を追加 / §1 の着手根拠から
> M3 援用を撤回 / §4 推奨を案 C → **案 B** へ変更 / §5 の差異を 7 → 9 点へ修正 /
> §7 に経路別の特性テスト表を追加）。
>
> → **v0.4 ユーザー確定（2026-07-23）**: §4 = 案 B / §5 = 案 1。§1「既存の不整合」と §5 案 2 を
> それぞれ [idea_05](../backlog/idea_05_trigger_set_source_path_inconsistency.md) /
> [idea_06](../backlog/idea_06_individual_json_io_unification.md) として起票。
>
> **ユーザー確定済・実装着手可**（`/phase_start` で phase 04 を起票してからタスクへ着手する）。
> フェーズ末タスクで正本 `instructions/common/spec_detail/` へ昇格し本書を凍結する。
> 起票元: ユーザー要望（2026-07-23）。`instructions/phase/current.md`「別タスク化候補」に
> 「`config_io_controller.py` が 598 行で 600 行目安に接近」として記録されていた項目の着手。

---

## §1 目的 / 背景

`keyseq/presentation/controllers/config_io_controller.py`（**598 行・1 クラス・29 メソッド**）を
**責務ごとに分割**し、保守性と修正時の説明可能性を回復する。**挙動不変が絶対前提**。

### 現状監査（2026-07-23）

対象ファイルは行順にほぼ 6 クラスタへ分かれている。

| ID | クラスタ | 行 | 概算 | メソッド |
|---|---|---|---|---|
| A | 構成セット（keymap_set） | 18-227 | ~210 | `confirm_save_if_dirty` / `new_config` / `save_keymap_set` / `save_as` / `save_keymap_set_to` / `load_keymap_set_from` / `import_config` / `export_config` / `restore_default` / `set_startup_keymap_set` / `apply_loaded_data_to_ui` |
| A' | 構成セット専用ヘルパ | 228-240 | ~13 | `choose_split_base_dir_for_keymap_set`（呼び出しは `save_keymap_set_to` のみ） |
| B | 起動設定（startup.json） | 241-288 | ~48 | `load_startup_and_config` / `write_startup` |
| C | 共有ダイアログヘルパ | 289-343 | ~55 | `choose_save_path_with_collision` / `ask_link_label_to_filename` |
| D | keymap 個別 JSON | 344-437 | ~94 | `selected_keymap_for_io` / `save_selected_keymap` / `save_selected_keymap_as` / `save_keymap_to_path` / `load_keymap_file` |
| E | trigger_set 個別 JSON | 438-515 | ~78 | `save_trigger_set_file` / `save_trigger_set_file_as` / `save_trigger_set_to_path` / `load_trigger_set_file` |
| F | sequence 個別 JSON | 516-598 | ~83 | `save_selected_sequence` / `save_selected_sequence_as` / `save_sequence_to_path` / `load_sequence_file` |

**確認した事実**:

1. **D / E / F は同型ブロック 3 つ**。いずれも `save_X`（source_path 判定 → 「読込で持ってきた…
   別名で保存しますか？」の askyesno → 未設定なら `choose_save_path_with_collision`）→
   `save_X_as`（`asksaveasfilename` → to_path）→
   `save_X_to_path`（try: service 呼び出し → 状態更新 → refresh → flash + showinfo /
   except: flash(auto_clear=False) + showerror）→ `load_X_file` という同一構造。
   **ただし「同型」は骨格のみ**で、細部は §5 に列挙する 9 点で食い違う
   （例: `ask_link_label_to_filename` を通すのは **D / F のみ**で E は通さない）。
2. **クラス docstring 自身が 2 責務を宣言**（`:12`「構成セット・個別JSON（keymap / trigger_set /
   sequence）の保存・読込フロー」）。`/refactor_check` 定性材料「異なる責務のまとまりが 3 つ以上」に該当。
3. **`self._app.` 参照が 169 箇所**。App への reach-through が全域にあり、分割後も残る。
   **本フェーズのスコープ外**（§9）。
4. **外部からの呼び出しは 8 ファイル 30 箇所**: `views/menu_bar.py` 8 / `app.py` 7 /
   `views/full_view/file_frame.py` 4 / `trigger_box.py` 3 / `sequence_box.py` 3 / `keymap_box.py` 3 /
   `controllers/layout_controller.py` 1 / `tests_ui/test_startup_font_characterization.py` 1。
5. **セクションコメントの位置が実態とずれている**。`:288`「# ---------------- 個別 JSON IO 系 ----------------」の
   直後は C（共有ヘルパ）であり、D の開始は `:344`。また A' は A のセクション内にある。
6. **B は他クラスタから使われる**。`write_startup` は A の `set_startup_keymap_set`（`:211`）と、
   **クラス外の `app.py:243`（フォント変更の永続化）**から呼ばれる。`load_startup_and_config` は
   `app.py` の起動シーケンスから呼ばれる。
7. **C は D / E / F と A の両方から使われる**（`choose_save_path_with_collision` は
   `save_keymap_set` 系では未使用だが D/E/F の 3 箇所で使用。`ask_link_label_to_filename` は D/F で使用）。

### 既存の不整合（発見・本フェーズでは直さない）

敵対的レビュー（2026-07-23）の指摘を受けて実コードで確認した、**既存の潜在バグ**。
**本フェーズでは修正しない**（挙動不変が絶対前提のため）。分割時に「明らかな誤りだから」と
直してしまうと受け入れ条件を破るので、実装タスクに**明示的な禁止事項として転記**する。

**E（trigger_set）の source_path が読み書きで分断している**:

| 種別 | 箇所 | 内容 |
|---|---|---|
| 読み | `:439` / `:451` | `getattr(self._app, "_trigger_set_source_path", "")` |
| 書き | `:221` / `:472` / `:502` | `self._app.dirty_tracker.trigger_set_source_path = ...` |

- **`App._trigger_set_source_path` はリポジトリ内のどこにも定義されていない**（grep 確認・
  定義 0 件 / 参照は上記 2 箇所のみ）。したがって読み出しは**常に `""`**。
- 書き込み先の `dirty_tracker.trigger_set_source_path` は `dirty_state.py:14` の初期化以外
  **読み手が存在しない**（write-only）。
- **帰結**: `save_trigger_set_file:440` の「読込で持ってきたトリガー一覧です。\n別名で保存しますか？」の
  askyesno 分岐は **到達不能なデッドコード**。トリガー一覧の上書き保存は毎回
  `choose_save_path_with_collision` からやり直しになる。D（keymap）/ F（sequence）は
  対象 dict の `INTERNAL_*_SOURCE_PATH` キーを読み書きするため、この問題は E だけに存在する。
- **扱い**: 本フェーズはこの挙動（デッドコードを含む）を**そのまま移設**する。
  修正は挙動変更を伴うため `.claude/rules/spec_change_workflow.md` の仕様変更フローで別途判断する
  → **[idea_05](../backlog/idea_05_trigger_set_source_path_inconsistency.md) として起票済**
  （2026-07-23・着手は phase 04 完了後）。

### 安全網の現状（重要）

- **`ConfigIoController` を直接対象とするテストは存在しない**。`tests/` 15 ファイル・`tests_ui/` 2 ファイル中、
  `config_io` に言及するのは `tests_ui/test_startup_font_characterization.py`（phase 03 で追加・
  `write_startup` 経由）のみ。
- 下位の `config_service` は `tests/test_config_service.py` が覆うが、**controller のフロー**
  （ダイアログ分岐・`dirty_tracker` 更新・flash 文言・例外時の挙動）は未検証。
- 特に `load_startup_and_config` は **`except Exception: pass`（`:261-262`）で読込失敗を握りつぶし、
  空データ起動へ fallback する**分岐を持つ。無検証で分割すると壊れても気づけないため、
  受け入れ条件 §7-2 で 3 分岐すべてを特性テスト対象に含める（reviewer 指摘 2026-07-23）。
- したがって**特性テストの先行追加なしに分割してはならない**（`/refactor_check`「項目 0 = 安全網の確認」に準拠）。

### 関連する既存の設計判断

- 計画03 で **views / dialogs / keyboard_window は App の委譲メソッドを介さず
  `app.<名前>`（`app.config_io` 等）でコントローラを直接参照する**方針が確定済
  （`codebase_map.md`「コントローラ（controllers/）」節）。**確定した §4 案 B はこの方針の素直な延長**
  （`app.keymap_io` 等を増やす形）であり、方針変更には当たらない。
- 担当層の割り当ては `spec_detail/architecture.md §3.5` により **`codebase_map.md` が正**。
  `spec_detail/` 配下に `ConfigIo` / `config_io` の言及は **0 件**（grep 確認済）。

### 着手根拠（メトリクスの位置づけ・正直な注記）

**本フェーズの着手根拠は「ユーザーが独立した設計タスクとして指示したこと」（2026-07-23）である。**
`/refactor_check` のメトリクスは根拠にしない。理由:

- **M1**（600 行超 **かつ** 当該フェーズで +100 行以上）: 非該当（598 行・直近フェーズでの増加なし）。
- **M3**（同型ブロック）: **援用しない**。M3 は「**このフェーズで追加した**コードが既存の同型ブロックの
  3 個目以降のコピーになっていないか」を測る指標であり、既存の重複には適用できない
  （敵対的レビュー指摘 2026-07-23 で誤用を修正）。
- **定性材料**（責務のまとまりが 3 つ以上 / 対象箇所を一言で説明しにくい）: 両方に該当するが、
  `/refactor_check` 上これは M1〜M6 が境界のときの tie-breaker 専用であり、単独トリガにはならない。
- `current.md`「別タスク化候補」には「600 行目安に接近・次フェーズの `/refactor_check` で再判定」と
  記録済み。本フェーズはその再判定を待たずユーザー判断で着手するものである。

つまり **D / E / F の重複や責務混在は「なぜ分割すると良いか」の説明材料**であって、
規則が分割を要求しているわけではない。この区別を昇格時の記録にも残す。

## §2 確定事項（ユーザー 2026-07-23）

- **本フェーズを暫定仕様先行モードで実施する**（複数ファイルに跨る・落とし先が探索的・タスク 3 以上）。
- **挙動不変が絶対前提**。ダイアログ文言・表示順・flash メッセージ・保存 JSON のバイト列・
  例外時の分岐を一切変えない。挙動変更が必要と判明した場合は本フェーズの範囲外とし、
  `.claude/rules/spec_change_workflow.md` の仕様変更フローへ回す。
- **安全網（特性テスト）の追加を最初のタスクに置く**。分割タスクはその後に着手する。
- **`self._app.` reach-through（169 箇所）の解消は本フェーズでは扱わない**（§9）。
- **§4 = 案 B（呼び出し元 30 箇所を本フェーズで差し替え）**（ユーザー確定 2026-07-23）。
  恒久ファサードは互換レイヤー禁止に抵触し、一時ラッパー案（案 C）は削除を強制するゲートを
  持てないため。実施条件はメソッド単位の対応表を先に作り機械的に置換し、
  `grep -rn "config_io\."` で残存 0 件を確認すること。
- **§5 = 案 1（分割のみ・共通化しない）**（ユーザー確定 2026-07-23）。
  共通化は [idea_06](../backlog/idea_06_individual_json_io_unification.md) として分離・保留。
- **§1「既存の不整合」（E の source_path 分断）は本フェーズで直さず、
  [idea_05](../backlog/idea_05_trigger_set_source_path_inconsistency.md) として起票済**
  （2026-07-23）。着手は phase 04 完了後。

## §3 分割の骨格（§4・§5 の結論に依存しない部分）

分割の**単位**は §1 現状監査のクラスタとする。ここは §4 / §5 の結論に依存しない。

- 配置は `.claude/rules/file_organization_rules.md`「フォルダ化（単一ファイル肥大化の分割時）」の
  **親フォルダ方式**に従い、`keyseq/presentation/controllers/config_io/` を新設して**親ごと入れる**
  （親をフォルダ外に残して補助だけフォルダへ入れる非推奨構成は採らない）。
- クラスタと落とし先の対応（案）:

  | ID | 落とし先 | 備考 |
  |---|---|---|
  | A + A' | `keymap_set_io.py` | A' は A からのみ呼ばれるため同居 |
  | B | `startup_io.py` | 他クラスタ・App から使われる（§1-6）ため独立 |
  | C | `io_dialogs.py` | 共有ダイアログヘルパ。名前に `utils` / `helper` を使わない（file_organization_rules） |
  | D | `keymap_file_io.py` | |
  | E | `trigger_set_file_io.py` | |
  | F | `sequence_file_io.py` | |

- 各モジュールは **1 ファイル 300 行以内の目安**（`.claude/rules/implementation.md`）に収まる見込み
  （最大は A+A' の ~223 行）。
- **セクションコメントのずれ（§1-5）は分割により自然解消する**。分割後に手で整合させる作業は発生しない。
- 分割後も各クラスは `app` を受け取り `self._app.` で参照する（reach-through は §9 のとおり温存）。

## §4 外部 30 箇所の呼び出しの扱い（**確定: 案 B**・2026-07-23）

**確定済（案 B・2026-07-23）→ §2 へ反映済**。以下は比較検討の記録として残す。

> **前提（reviewer 指摘 2026-07-23・v0.2 で反映）**: 「ファサードを恒久的に残す」案は
> `file_organization_rules.md`「恒久的な互換レイヤーは禁止」に抵触する。同ルールの例外は
> **パッケージ `__init__.py` の再輸出（公開面の定義）**に限定されており、通常モジュールに
> 委譲メソッドを並べる層は「横流し専用モジュール」に当たる。
> よって**恒久ファサード案は選択肢から除外**し、以下 3 案で検討する。

### 案 A: 公開面を `config_io/__init__.py` に定義

`ConfigIoController` の定義を `config_io/__init__.py` へ置き、実装は同フォルダ内の
分割モジュールへ委譲する（パッケージの公開面 = 例外規定に文字どおり適合させる）。

```python
# controllers/config_io/__init__.py
class ConfigIoController:
    def __init__(self, app) -> None:
        self._keymap_set = KeymapSetIo(app)
        self._startup = StartupIo(app)
        ...
    def save_keymap_set(self, *, show_success_dialog: bool = True) -> bool:
        return self._keymap_set.save(show_success_dialog=show_success_dialog)
```

- **長所**: 外部呼び出し **30 箇所すべてが無変更**（`app.config_io.<メソッド>` の形は不変）。
  クラスタ外の変更は `app.py:9` の import 1 行のみ。検証範囲が対象フォルダ内にほぼ閉じる。
- **短所**: 委譲メソッドが 20 個以上並ぶ層が恒久的に残ることに変わりはなく、
  「`__init__.py` に置けば公開面」という**形式適合にすぎない**という批判が成り立つ
  （例外規定が想定するのは再輸出であって、委譲クラスの定義ではない）。§6-1 で敵対的レビューに問う。

### 案 B: 呼び出し元を差し替え

`app` が分割後のクラスを個別に持ち（`app.keymap_set_io` / `app.keymap_io` / …）、
外部 30 箇所を新しい参照へ書き換える。

- **長所**: 薄い委譲層が残らない。計画03 の「`app.<名前>` でコントローラを直接参照する」方針とも素直に整合。
- **短所**: 差分が 8 ファイルへ広がる。`menu_bar.py`（8 箇所）・各 box（3 箇所ずつ）を触るため、
  挙動不変の検証範囲が UI 全域に及ぶ。`tests_ui/test_startup_font_characterization.py` の修正も必要。

### 案 C: 一時ラッパー + 後続フェーズで削除（2 段階）

本フェーズは案 A の形で分割を完了させるが、ファサードを**移行期間の一時ラッパーとして明示**し
（`file_organization_rules.md`「一時的なラッパー / re-export は移行期間のみ可」に該当）、
削除予定コメントを付与した上で、**呼び出し元 30 箇所の差し替えと層の削除を後続フェーズ**に切る。

- **長所**: 各フェーズの差分が最小で、段階ごとに挙動不変を検証できる。
  ルール上も**明示的に許容された枠**に収まる（案 A のような解釈論が不要）。
  最終的に到達する構造は案 B と同じで、恒久的な委譲層は残らない。
- **短所**: フェーズが 2 つに増える。後続フェーズが実施されないと案 A（恒久ファサード）と
  同じ状態で放置される → **後続フェーズの起票を本フェーズの正本反映タスクに含める**ことで担保する。

### 推奨の変遷と現在の推奨

| 版 | 推奨 | 変更理由 |
|---|---|---|
| v0.1 | 恒久ファサード維持 | — |
| v0.2 | 案 C | reviewer 指摘: 恒久ファサードは互換レイヤー禁止に抵触 |
| **v0.3** | **案 B** | 敵対的レビュー指摘（下記）を採用 |

**敵対的レビューの指摘（2026-07-23・[high]）**:

> 案 C の「削除予定コメント + フェーズ末での後続起票」には**実施期限・所有者・削除完了を強制する
> ゲートがない**。一方、実コードを走査した結果、30 箇所の呼び出しはすべて
> `app.config_io.<method>` の**静的参照**であり、動的ディスパッチ等で案 B の一括置換が
> 特に危険になる根拠は見つからなかった。つまり案 C は「既知の恒久互換層を導入する」確定コストを
> 払う一方、案 B の想定リスクは実測では裏付けられていない。

この指摘は妥当と判断する。ドラフトが案 B のリスクとして挙げた「検証範囲が UI 全域に及ぶ」は、
実際には**メソッド名の機械的置換**であり、§7 の特性テストと `compileall` + テストスイートで
十分に検出できる。対して案 C の「後続フェーズが実施されない」リスクは、
`instructions/` に候補として記録しても**過去に放置された前例がある**
（`action_list` alias は計画04 から据え置き中）。

**現在の推奨: 案 B**（呼び出し元 30 箇所を本フェーズで差し替え）。実施条件として:

- 差し替えは**メソッド単位の対応表**を先に作り、それに従って機械的に行う（対応表を実装タスクに添付）
- 差し替え後に `grep -rn "config_io\." keyseq main.py tests tests_ui` で**残存 0 件**を確認する
- 案 C を採る場合は、後続フェーズを**確定タスクとして起票し、削除完了までフェーズを
  完了扱いにしないゲート**を仕様に明記すること（ゲートなしの案 C は採らない）

## §5 同型ブロック 3 つ（D / E / F）の扱い（**確定: 案 1**・2026-07-23）

**確定済（案 1・2026-07-23）→ §2 へ反映済**。以下は比較検討の記録として残す。

### 案 1: 分割のみ・共通化しない

D / E / F を別モジュールへ分けるだけで、同型構造はそのまま残す。

- **長所**: 挙動不変の保証が容易（コードは移動のみ）。差分が読める。
  3 種の差異を吸収する設計判断が不要。
- **短所**: M3（同型ブロック）自体は解消しない。行数削減効果は小さい。

### 案 2: 共通テンプレートへ集約

`save_X` / `save_X_as` / `save_X_to_path` / `load_X_file` の 4 点セットを基底クラスまたは
高階関数へ集約し、3 種は差分のみ与える。

- **長所**: 重複が消え、行数削減が最大。以後 4 種目を足す際のコストが下がる。
- **短所**: **3 種の差異が想像より多く、吸収に設計判断が要る**。現状監査で確認した差異
  （**v0.3 で 2 点追加**。敵対的レビュー指摘により、v0.2 時点の 7 点は不完全だった）:
  - **E の `save_X_as` だけ `ask_link_label_to_filename` を呼ばない**（`:450-466`）。
    D（`:389`）/ F（`:555`）はラベル連動ダイアログを出し、hook の suspend/resume も伴う。
    E だけダイアログ 1 枚ぶん挙動が違う
  - **E の source_path は読み書きが分断している**（§1「既存の不整合」）。D / F は対象 dict の
    `INTERNAL_*_SOURCE_PATH` を読み書きする対称形だが、E は読み `app._trigger_set_source_path`
    （未定義）/ 書き `dirty_tracker.trigger_set_source_path`（read されない）で**繋がっていない**。
    共通化するとこの非対称を「揃えて」しまい、確実に挙動が変わる
  - ダイアログ文言が全て異なる（「キーマップ」/「トリガー一覧」/「出力シーケンス」）
  - 対象の取得元が異なる（D: `keymap_panel.selected_keymap_list_index()` + index /
    E: `app._trigger_set_source_path` 属性 / F: `trigger_panel.selected_trigger()`）
  - dirty 管理が異なる（D: `dirty_tracker.sync_dirty_state()` / E: `trigger_set_*` 3 属性を直接更新 /
    F: `mark_trigger_set_dirty()`）
  - **E だけ `load_trigger_set_file` の冒頭で `confirm_save_if_dirty` を呼ぶ**（D / F は呼ばない）
  - source_path の格納先が異なる（D/F: 対象 dict の `INTERNAL_*_SOURCE_PATH` キー /
    E: `dirty_tracker.trigger_set_source_path`）
  - 保存後の refresh 先が異なる（D: `keymap_panel` + `layout.refresh_keyboard_window()` /
    E・F: `trigger_panel` の 2 メソッド）
  - **F の `save_sequence_to_path` だけ成功時に `_set_flash_message` の後で `trigger.update()` 済**
    （引数が dict そのものを破壊的更新する）
  → 抽象化のパラメータが **9 種類**になり、**挙動差の混入リスクが高い**。

**推奨: 案 1**（v0.1 から変更なし。v0.3 の差異追加で根拠がさらに強まった）。
理由は `.claude/rules/anti_patterns.md`「過剰な共通化」「大きすぎる差分」の回避と、
上記の差異列挙から「共通化しても素直なテンプレートにならない」ことが読めるため。
特に追加された 2 点（E のラベル連動なし / E の source_path 分断）は、**共通化がバグの
「意図しない修正」を招く経路そのもの**であり、挙動不変フェーズでは致命的になりうる。
案 2 を採るなら、**特性テストが 3 種すべての save / save_as / load 経路を覆い、かつ
§1「既存の不整合」を維持したまま抽象化できることの確認が前提条件**。

## §6 レビュー記録（実施済）

| 実施 | エージェント | 判定 | 反映 |
|---|---|---|---|
| 2026-07-23 | `reviewer`（起票時・`/spec_draft`） | **修正して採用**（NG 2件） | v0.2 |
| 2026-07-23 | `codex-adversarial-reviewer`（確定前・`agent_selection.md`） | **needs-attention / No-ship**（high 3件・medium 1件） | v0.3 |

敵対的レビューで問うた点と結果:

1. §4 の 3 案の評価 → **指摘採用**。案 C にゲートがないこと・案 B のリスクが実測で裏付けられない
   ことから推奨を案 B へ変更（§4）
2. §3 のクラスタ分けの実装可能性（A↔B の `_startup_settings` 共有 / C の hook 依存 /
   `set_startup_keymap_set` → `write_startup`）→ **循環参照の指摘はなし**。§3 は維持
3. 「挙動不変」の保証可能性 → **指摘採用**。§7 に経路別の特性テスト表を追加
4. §5 の差異の見落とし → **指摘採用・実コードで裏取り済**。2 点追加（7 → 9 点）。
   推奨（案 1）は変わらず、根拠が強化された
5. §9 の reach-through スコープ外 → 追加指摘なし

※ 以下は当初「敵対的レビューで問う」として列挙していた項目（記録として残す）:

1. §4 の 3 案の評価。(a) 案 A の「`__init__.py` に置けば公開面の定義」は形式適合にすぎないのでは
   ないか。(b) 案 C の「後続フェーズで削除」は実施されず放置され、結局恒久ファサードになるのでは
   ないか（フェーズを 2 つに割ること自体の是非）。(c) 案 B を一括で行う場合の実際のリスクは
   ドラフトが書くほど大きいのか（30 箇所は機械的置換で済むのではないか）
2. §3 のクラスタ分けに漏れ・誤りはないか（特に C の共有ヘルパを 1 モジュールに置く判断、
   B が A から独立しうるか）
3. §5 で列挙した 3 種の差異に**見落としがないか**（見落としがあれば案 2 のリスクはさらに上がる）
4. 安全網（§7）の粒度で「挙動不変」を本当に保証できるか。特性テストが通っても壊れうる経路はどこか
5. `self._app.` reach-through をスコープ外にしたまま分割して、後で困る構造にならないか

## §7 受け入れ条件（ドラフト）

| # | 条件 | 対応 § |
|---|---|---|
| 1 | 分割前に特性テストを追加し、追加時点（分割前のコード）で **pass** することを確認済 | §1 安全網 |
| 2 | 特性テストが **§7-2 表**（下記）の経路をすべて覆う | §1 安全網・§5 |
| 3 | `config_io_controller.py` が `controllers/config_io/` 配下へ分割され、各ファイルが 300 行以内 | §3 |
| 4 | 分割後、`tests` / `tests_ui` / smoke が**分割前と同じ結果**（pass 86 / pass 20 / pass + 追加分） | §2 |
| 5 | ダイアログ文言・呼び出し順・flash メッセージが分割前と一致し、**保存 JSON は一時ディレクトリでのバイト列比較**で一致（特性テストで固定） | §2 |
| 6 | 外部呼び出し 30 箇所の扱いが §4 の確定案どおりに実装されている | §4 |
| 7 | 実機目視（保存・読込・別名保存・Import/Export・起動設定変更）でユーザー OK | §2 |
| 8 | `codebase_map.md` のコントローラ節が分割後の構成を反映している | §8 |

※ 条件 4 の基準値は phase 03 完了時点の実測（tests 86 / tests_ui 20 / smoke pass）。
特性テストの追加分だけ件数が増える。

### §7-2 表: 特性テストの対象経路（分割前に作成・分割前のコードで pass すること）

敵対的レビュー指摘（2026-07-23）により、v0.2 の「各系統 1 経路」から**メソッド × 分岐**の粒度へ引き上げた。

| クラスタ | 対象 | 覆う分岐 |
|---|---|---|
| A | `confirm_save_if_dirty` | dirty なし（即 True）/ yes → 保存成功 / yes → 保存失敗 / no / cancel（None）/ `keymap_set_path` の有無による save と save_as の分岐 |
| A | `save_keymap_set_to` | 成功（JSON バイト列比較・`startup_payload` 反映・dirty クリア）/ 例外（flash + showerror・dirty 維持）|
| A | `choose_split_base_dir_for_keymap_set` | config_root 内（即 ""）/ 外 + yes / 外 + no |
| A | `load_keymap_set_from` | 成功 / キャンセル（パス空）/ 例外 |
| A | `new_config` / `import_config` / `export_config` / `restore_default` | 各 1 経路 + 例外がある経路は例外側も |
| A | `set_startup_keymap_set` | 成功 / 読込例外（早期 return）/ **`write_startup` 内で保存失敗を吸収した後も後続処理（データ適用・dirty 解除・成功 showinfo）が続行される現挙動**（`:211-218`）|
| B | `write_startup` | 既定値マージ / `config_path` 除去 / `ui_font_delta_pt` の coerce / 保存例外時の showerror |
| B | `load_startup_and_config` | 正常読込 / stored path 不在 / **読込例外時の空データ fallback**（`:261-262` の握りつぶし）|
| C | `choose_save_path_with_collision` | 衝突なし / 衝突 + yes（上書き）/ 衝突 + no（別名ダイアログ）/ 衝突 + cancel（""）|
| C | `ask_link_label_to_filename` | OK + チェックあり / OK + チェックなし / キャンセル（RuntimeError）/ ウィンドウ閉じ。**hook の suspend / resume が釣り合うこと**（`:312` / `:339`）|
| D | `save_selected_keymap` / `_as` / `_to_path` / `load_keymap_file` | 未選択 / source_path あり・imported・dirty の askyesno 分岐 / source_path なし / ラベル連動 / 成功 / 例外 |
| E | `save_trigger_set_file` / `_as` / `_to_path` / `load_trigger_set_file` | 同上。ただし **`:440` の askyesno は到達不能である現状を固定する**（§1「既存の不整合」）。`load` 冒頭の `confirm_save_if_dirty` も含む |
| F | `save_selected_sequence` / `_as` / `_to_path` / `load_sequence_file` | 未選択 / askyesno 分岐 / ラベル連動 / 成功 / 例外 |

**実装方針**: `tests_ui/test_startup_font_characterization.py`（phase 03）の monkeypatch 手法を踏襲する。
`filedialog.*` / `messagebox.*` は呼び出し引数を記録する fake に差し替え（**文言と呼び出し順を assert**）、
`ask_link_label_to_filename` の `tk.Toplevel` は OK / キャンセル / 閉じるを駆動できる fake にする。
保存系は `tmp_path` 配下で実ファイルを書き、**バイト列で比較**する。

**この表が過大なら分割の前にユーザーへ相談する**（テスト作成だけで 1 フェーズを超える規模なら、
対象クラスタを絞って段階的に分割する選択肢がある）。

## §8 正本反映（フェーズ末昇格・予定）

| 対象 | 内容 |
|---|---|
| 正本 `spec_detail/` | **更新不要の見込み**。`ConfigIo` / `config_io` の言及が 0 件（grep 確認済）で、担当層の割り当ては `architecture.md §3.5` により `codebase_map.md` が正。昇格タスクで再 grep して確定する |
| `codebase_map.md` | 「コントローラ（controllers/）」節の `ConfigIoController` 行を分割後の構成へ更新。ツリー図（`:44`）も更新 |
| 実装 | `controllers/config_io/`（新規フォルダ + 6 ファイル）/ 案 B・C を採る場合は `app.py`・`views/menu_bar.py`・`views/full_view/{file_frame,trigger_box,sequence_box,keymap_box}.py`・`controllers/layout_controller.py` |
| テスト | `tests_ui/` に特性テストを追加（既存 `test_startup_font_characterization.py` の monkeypatch 手法を踏襲）。案 B を採る場合は同ファイルの参照も修正 |
| 別実装同期 | なし |

## §9 スコープ外（本フェーズでやらない）

- **`self._app.` reach-through（169 箇所）の解消**。分割とは独立した大きさの問題であり、
  同時に着手すると差分が読めなくなる。分割後に改めて評価する。
- **挙動・ダイアログ文言・保存形式の変更**（誤字修正を含む）。`:178`「例の設定に戻します」等の
  文言に違和感があっても触らない。
- **`app.py` 側の呼び出しフローの整理**（`load_startup_and_config` の起動シーケンス等）。
- **フォント設定まわりの構造変更** → [idea_04](../backlog/idea_04_font_settings_controller.md)（保留）。
  ただし `write_startup` が B クラスタに属するため、idea_04 着手時の前提が変わる点は
  昇格時に idea_04 へ 1 行追記する。
- **`config_service`（application 層）への変更**。本フェーズは presentation 内で完結させる。
- **E（trigger_set）の source_path 分断の修正**（§1「既存の不整合」）→
  [idea_05](../backlog/idea_05_trigger_set_source_path_inconsistency.md)（起票済・phase 04 完了後に着手）。
  挙動変更を伴うため本フェーズでは**そのまま移設**する。
- **D / E / F の共通化**（§5 案 2）→
  [idea_06](../backlog/idea_06_individual_json_io_unification.md)（起票済・**保留**）。
  着手条件は「phase 04 完了 + idea_05 の解消 + 共通化の実需」の 3 つすべて。

## 関連

- 起票元: `instructions/phase/current.md`「別タスク化候補」（598 行・600 行目安に接近）
- 前フェーズ: `03_startup_font_settings_cleanup`（[decisions_archive/03](../../.claude_data/state/decisions_archive/03_startup_font_settings_cleanup.md)）
- 関連 idea: [idea_04](../backlog/idea_04_font_settings_controller.md)（`write_startup` を共有・保留中）
- 参照ルール: `.claude/rules/file_organization_rules.md`（親フォルダ方式・互換レイヤー禁止）/
  `.claude/rules/anti_patterns.md`（過剰な共通化）/ `.claude/commands/refactor_check.md`（M3・定性材料）
- 正本: `spec_detail/architecture.md §3.5`（担当層は codebase_map.md が正）/
  `instructions/common/codebase_map.md`「コントローラ（controllers/）」
