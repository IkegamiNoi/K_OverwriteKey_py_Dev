# decisions_archive: 08_hotkey_presets_global

> phase 08（プリセットの config.json グローバル化 = 保存系リデザイン **プリセット案2**）の判断履歴。
> **2026-08-09 完了**。正本は `spec_detail/data_schema.md` **§5.10** + **§5.8.8** +
> §5.1 の例外 / §5.4 / §5.5 / §5.9.2、および `codebase_map.md`。
> 暫定仕様 07（`instructions/history/07_hotkey_presets_global.md`・**v0.6**）は**凍結済**（経緯の参照用）。

---

規範: [phase.md](../../../instructions/phase/08_hotkey_presets_global/phase.md) /
主入力 = 暫定仕様 07（`instructions/history/07_hotkey_presets_global.md`・**v0.3**）。**暫定仕様先行モード**。

### 【起票時】計画06 の候補送りを本フェーズが引き取る → **採用**（ユーザー確定 2026-08-06）
- 対象 = 「**runtime を新規化・置換する入口が 4 経路**あり、各所で注入 API を呼ぶ規約」の一本化。
  Phase γ の `/refactor_check` から候補送りされ、計画06 では**挙動保存の範囲を超える**ため見送っていた。
- **判断根拠**: ①規約は **task_07b の指摘 A（Import 経路の注入漏れ）で 1 度破れている** ②`app.py:77` の
  `new_default_data()` には注入が無く**起動シーケンスの順序依存だけで守られている**（5 個目の潜在的な穴）
  ③本フェーズでプリセットが同型の注入を追加するため、放置すると **4 経路 × 2 種類**へ増え、
  次の漏れは「プリセットが復活しない」形で出る。**2 例目が出る今が設計のタイミング**。
- **扱い**: 暫定仕様 07 を **v0.3** へ改訂し **§4 検討事項 A（未確定）** として起票。
  **task_03 でユーザー確定 → v0.4 へ改訂 → task_04 で実装**の順とする（設計先行の不変原則）。
  **確定内容が「現状維持」でも可**（その場合は根拠を暫定仕様へ残す）。§2・§3 の確定内容は無改変。
- 論点は 3 つ: ①生成の入口自体が供給済み runtime を返す形（`new_runtime_data(*, config_root)`）へ寄せるか
  ②**通常読込 `build_runtime_data_from_split` の条件付き注入との等価性**をどう保つか
  ③`app.py:77` を新方式へ寄せるか前提を明文化して据え置くか。

### 【起票時】整合チェック（`reviewer`・整合確認限定）= **修正して採用**
- 指摘 1（修正済）: 「このフェーズで読むファイル」の `app.py:405` は実際は **`:406`**。
- 指摘 2（修正済）: 受入条件 6（tests / tests_ui / smoke）の回収先がタスク表から読めない
  → **各タスクの完了条件に含める + task_07 で通し再実測**と明記。
- 主入力との齟齬なし / 最終タスクがフェーズ完了チェックリストを満たすこと / リンクと番号対応
  （phase 08 / 暫定 07 / decisions_archive 08・次採番 09）は OK。

### 【task_01】完了（2026-08-06）= グローバルプリセットパスの読み出し API
- `split_loading.load_global_hotkey_presets_path(service, *, config_root)` を新設（+22 行）。
  `load_global_hook_keys` と同じ骨格で、**保存されている表記をそのまま返し・パス解決はしない**
  （解決は `load_named_list` 側。相対値を `os.path` 系へ直接渡さない不変条件を守るため）。
- **タスク起票時の確定**: **「明示的な空文字」も既定へ縮退**させる（暫定仕様 §3 は「無ければ既定」までしか
  書いておらず空文字が未定義だった）。根拠 = §2 の「プリセットの置き場は常に 1 つ」。
  **task_08 の正本反映でこの契約を明記する**。
- **hook キーとの非対称は意図的**: `load_global_hook_keys` は `config_root` 空で `("", "")` へ縮退するが、
  本 API は**常に既定パスを返す**（キーは「未設定」があり得るが、プリセットの置き場は常に存在する）。
- **修正して採用（Codex の指摘を採用）**: タスク定義が示した `str(x or "").strip()` 一本では
  **数値 `42` が `"42"` になり「非文字列は既定へ縮退」の要件と矛盾する**ため、`isinstance(..., str)` の
  型ガードを追加。タスク定義の記述ミスであり、実装側の判断が正しい。
  reviewer の軽微指摘（ガード後の `str()` が冗長）はメインが 1 行へ整理し再実測。
- 検証: compile clean / tests **175 pass**（170 + 追加 5）/ tests_ui **178 pass**（無修正）/ smoke pass /
  差分は `split_loading.py` と `tests/test_config_service.py` の **2 ファイルのみ**。
- reviewer = **採用（完了可）**。5 経路すべての既定縮退・解決していないこと・既定値の定義元が
  `HOTKEY_PRESETS_RELATIVE_PATH` 1 箇所であること・「含まない」への未踏み込みを確認。

### 【task_02】完了（2026-08-06）= プリセットの読込元を config.json へ切替（**挙動変更**）
- `build_runtime_data_from_split` のプリセット読込 **1 行**を
  `keymap_set.get("hotkey_presets_path")` → `load_global_hotkey_presets_path(service, config_root=...)` へ差し替え。
  **keymap_set 側キーはこの関数から参照されなくなった = 読込時無視**（`pop` 等の能動削除はしない）。
- **既存テストの修正は 0 件**（挙動変更だが既存テストは同一 config_root で保存・再読込するため、
  グローバル既定パスと保存先の既定パスが一致し影響が出なかった）。追加 5 件のみ。
- **既知の中間状態（task_05 まで残す）**: 保存側は未変更のため「**別ディレクトリへ保存した keymap_set を
  読み直すとプリセットはグローバル側**」という非対称が残る。**先取りで直さない**とタスク定義に明記し、
  reviewer にも「本タスクでは正しい状態」として確認させた。
- 単一 JSON 互換の読込（`ensure_config_compatibility` のインライン `hotkey_presets`）は**対象外**（別形式）。
- 検証: compile clean / tests **180 pass**（175 + 追加 5）/ tests_ui **178 pass** / smoke pass /
  差分は `split_loading.py`（±1 行）と `tests/test_config_service.py` の 2 ファイルのみ。
- reviewer = **採用（完了可）**・指摘なし。観点 2 のテストが**グローバルと keymap_set 側に異なる内容を置いて
  値で区別**しており偽陽性でないことも確認。

### 【task_03】完了（2026-08-06）= 入口一本化の**設計確定**（文書のみ・暫定仕様 07 を **v0.5** へ）
- **方式 = 案B: 注入 API を 1 本に束ねる**（ユーザー確定）。`ConfigService.apply_global_defaults(runtime, *, config_root)`
  が **hook キー注入 + グローバルプリセット供給**を担う。**`app.py:77` も新方式へ寄せる**（ユーザー確定）。
  - **却下: 案A（供給済みファクトリ `new_runtime_data`）** — 通常読込は hook キーが**フラグ次第の条件付き注入**の
    ため素の `new_default_data()` を使い続けることになり「入口は 1 つ」にならない。公開 API 変更で
    テスト 6 + 呼び出し 4 箇所へ波及する割に得るものが小さい。
  - **却下: 案C（現状維持）** — 呼び忘れ面が **4 経路 × 2 種類**へ倍化する。
- **例外を 1 つ残す**: `App.toggle_hook_keys_individual` の **ON→OFF は従来どおり
  `apply_global_hook_key_defaults` を直接呼ぶ**。束ねた API を使うとキー切替だけで**プリセットが再読込**され、
  編集中の内容を取りこぼすため。**「hook キー単独の注入」と「runtime 置換時の全体注入」は別物**。
- **敵対的レビュー（`codex-adversarial-reviewer`）= needs-attention・指摘 2 件を実コードで裏取り →
  ユーザーが 2 件とも採用**（→ v0.5）:
  - **[high] 空リスト縮退が §2 を破る**（グローバルが空でも通常読込＝空 / 新規作成＝組込 8 件と経路で割れる。
    削除したプリセットが復活し task_06 の保存で再永続化され得る）→ 読み出しを **`list | None`** に変え
    **「読めた空リスト」と「読めない」を区別**。**読めたら空でも採用 / 読めなければ置き換えない**。
    **通常読込も同規則へ統一**（→ **task_02 のテスト「不存在・破損 → `[]`」は task_04 で
    「置き換えない = 組込 8 件」へ更新する**）。
  - **[medium] 入口台帳が不完全**（受入条件 7 が 5 経路しか見ず、通常読込 3 経路が漏れる）→
    `app.data` 置換の**実測 9 箇所**を **入口台帳 E1〜E5 / L1〜L3 / N1** として §3-2 へ列挙し、
    受入条件 7 を台帳全経路へ拡張・受入条件 9 を追加。
- **実測で判明した重要事実**: Import（`keymap_set_io.py:561`）は**レガシー単一 JSON 経路**で
  `build_runtime_data_from_split` を通らない。よって**インラインの `hotkey_presets` はグローバルが
  読めれば置き換わる**（§2 の帰結）。読めないときだけインラインが残る。
- レビュアーが触れなかった論点（ON→OFF の例外 / `app.py:77` の起動順序 / 正本 §5.9・codebase_map の
  「解決点は 4 つ」との整合）はメイン判断で v0.4 の記述を維持し、**正本側の更新は task_08 で行う**。
- 成果物は**文書のみ**（`keyseq` / `tests` / `tests_ui` は無変更）。

### task_04（`apply_global_defaults` の実装・入口台帳 E1〜E5 配線）— 2026-08-09

- 暫定仕様 07 §3-2（v0.5）をそのまま実装。**設計の再検討・仕様変更は発生していない**。
- 実装判断（いずれも仕様の範囲内・レビュー採用済）:
  - `load_global_hotkey_presets` は `load_global_hotkey_presets_path` → `_resolve_config_relative_path`
    → `_load_optional_json` の順で読み、**非 dict / 根キー非 list を `None`**、**list は空でも採用**。
    例外は握り潰さず `try` の範囲を読み出しに限定（例外を投げない契約）。
  - `apply_global_defaults` は **`apply_global_hook_key_defaults` を委譲呼び出し**（ロジック複製なし）。
  - **E1（`app.py:77`）は新規の 1 行追加**で、順序依存だけで守られていた穴を塞いだ。
- **想定外の先行実装**: なし（差分はタスク定義が挙げた production 5 + テスト 3 ファイルのみ）。
- 実測: compile clean / `tests` **186**（+6）/ `tests_ui` **181**（+3）/ smoke pass。
- `reviewer` = **採用（完了可・指摘なし）**。

### task_05（保存側からのプリセット切り離し）— 2026-08-09

- 暫定仕様 07 §2 指摘②・④ をそのまま実装。**仕様変更なし**。production 差分は**削除のみ**。
- 実装判断（仕様の範囲内・レビュー採用済）:
  - `HOTKEY_PRESETS_RELATIVE_PATH` と `ensure_split_config_dirs` の `user/hotkey_presets` 作成は
    **残した**（前者は task_01 の既定値、後者は task_06 の保存先）。
  - 既存 keymap_set の `hotkey_presets_path` は**能動削除せず**、生成停止による自然消滅とした
    （`data_schema.md` 既存キー削除禁止）。特性テストで固定。
- **中間状態を許容する判断**: task_05 完了時点で**プリセットの書き手が居ない**（保存では書かない /
  マネージャは task_06 で対応）。先取りして書き手を足さない方針を維持した。
- **運用上の学び**: `reviewer` は指示した差分範囲（`tests_ui`）しか見ず、`tests/test_config_service.py` の
  追随漏れ 2 件を拾えなかった。**verifier の実測が唯一の検出手段だった**
  → レビュー範囲は「変更ファイル」ではなく「呼び出し元を含む全テスト」で指示するとよい。
- 実測: compile clean / `tests` **190**（+4）/ `tests_ui` **181**（増減なし）/ smoke pass（追随修正後）。
- `reviewer` = **採用（完了可・指摘なし）**。

### task_06（プリセットマネージャの即時保存）— 2026-08-09

- 暫定仕様 07 §2 指摘③ をそのまま実装。**仕様変更なし**。これで**プリセットの書き手が 1 本に確定**。
- 設計判断（レビュー採用済）:
  - **新規モジュール `controllers/config_io/hotkey_presets_io.py` を作った**。理由 = `config_io/` は
    ファイル種別ごとの IO モジュール構成（`keymap_file_io` / `sequence_file_io` /
    `trigger_set_file_io` / `startup_io`）で、プリセットファイルは `startup_io`（config.json 専用）にも
    `keymap_set_io` にも属さない。App へ file IO と `messagebox` を持ち込む方が責務違反になる。
  - **例外の分担**: application（`save_global_hotkey_presets`）は**送出**、presentation
    （`HotkeyPresetsIo`）が捕捉して成否へ変換。`apply_global_defaults` の「例外を投げない」契約は
    **読み出し側のみ**であり、保存側とは別物として扱う。
  - **`open_preset_manager` から `set_dirty(True)` を削除**（プリセットは keymap_set の一部ではなくなった）。
- **想定外の先行実装**: なし。
- **運用上の学び（2 度目）**: `tests_ui/test_app_ui_flows.py` の `AppUiFlowsTest` は
  **`setUpClass` で App を共有**するため、`has_unsaved_changes()` を絶対値で assert すると
  他テストの副作用で落ちる。**前後差分 / `set_dirty` の呼出有無**で見ること。
- 実測: compile clean / `tests` **193**（+3）/ `tests_ui` **185**（+4）/ smoke pass（追随修正後）。
- `reviewer` = **採用（完了可・指摘なし）**。

### task_07（統合確認）+ task_07b（是正）— 2026-08-09 / 暫定仕様 **v0.6**

- 自動確認は全 pass。`codex-reviewer` = **指摘なし**。**`deep-reviewer` = 修正要**（実測付きの H1 が主）。
- **ユーザー確定（4 件）**:
  - **H1 = 是正・読み出し側で正規化**。通常読込は注入後に `ensure_config_compatibility` を通すが、
    `apply_global_defaults` は生の JSON を代入していたため **E1/E3/E4/E5 が非正規化**（E2 のみ N1 で救済）。
    非 dict 要素が runtime に残ると `dialogs.py` の `p.get` で **AttributeError**（phase 08 で新たに生じた破綻面）。
    → **正規化は読み出し側 1 箇所**（`load_global_hotkey_presets`）。注入 API 側へは置かない。
    通常読込の二重正規化は冪等なので許容。**`None` 判定は正規化の前**（受入条件 9 を壊さないため）。
  - **受入条件 7 を「グローバルが読めた場合」へ限定**（M4）。`None` 時の経路差は §3-2 が許容しており、
    旧文言のままでは条項間矛盾（達成不能）だった。
  - **M3（`None` 時の上書き内容が入口経路で割れる）は現状を制約として明文化**。
    実装での回避（`new_empty_data` に組込既定を載せる / 保存前に確認ダイアログ）は**却下**。
  - **task_07b へ M1 / M2 / L3 を同梱**（死にコード `load_named_list` 削除 / E1 の特性テスト / deepcopy）。
- **却下せず task_08 へ送った項目**: L1（旧「別ディレクトリ保存」の孤児プリセット）/ L2（Export の
  デッドデータ）/ L4（`hotkey_presets_path` はアプリが書かない = 手編集専用キー）→ **正本へ文書化**。
- **前提の誤りを 1 件訂正**: task_04 定義に書いた「`load_named_list` は他用途（trigger_set 等）で使用中」は
  誤り（trigger_set は `load_trigger_set` 担当）。task_02 → task_04 の切替で最後の利用者が消えていた。
- 実測: compile clean / `tests` **198**（+5）/ `tests_ui` **186**（+1）/ smoke pass。
- `reviewer`（task_07b）= **採用（完了可・指摘なし）**。`ensure_config_compatibility` の挙動不変も確認。
- **未了**: task_07 の実機目視（ユーザー担当・観点 6 件。⑥は task_07b の確認を兼ねる破損ファイルケース）。

---

### 【task_07】実機目視 = **OK**（2026-08-09・ユーザー実施）

観点 1〜5（全 keymap_set で共通 / 即時保存 / 保存失敗時に編集が残る / keymap_set 保存で書かれない /
既存 `hotkey_presets_path` の後方互換）に加え、task_07b の確認を兼ねた観点 6
（**破損 JSON・非 dict 要素を含むプリセットファイル**）まで**すべて OK**。指摘なし。
→ **受入条件 1〜6 の充足を確認**（7〜9 は特性テストが pass のままで回帰なし）。

### 【task_08】正本反映（2026-08-09）= **phase 08 完了**

- 正本へ昇格: `data_schema.md` **§5.10 新設**（データモデル / 解決順序・供給規則・読み出し側の正規化 /
  編集と保存の契約 / 契約上の制約）+ **§5.8.8 へ入口台帳**を追記 + §5.1 に**「削除禁止の例外＝生成停止」**
  + §5.4・§5.5 の改訂 + §5.9.2 を注入 API 経由へ更新。`codebase_map.md` は
  注入 5 経路 / プリセットの解決点 3 つ / `HotkeyPresetsIo`（7 クラス化）/ dirty 非汚染 /
  カスケードが書かないこと、を反映。
- 暫定仕様 07 を **凍結**（v0.6・参照専用）。
- **正本へ書いた既知の制約**（実装は変えない）: `None` 時の経路差 / 破損上書き /
  旧「別ディレクトリ保存」の孤児プリセット / Export のインライン値は Import で置き換わる。

### 【task_08】`/refactor_check` 判定 = **不要**（2026-08-09）

対象: `keyseq/` 配下 **11 ファイル / +126・-65 行**（PHASE_BASE = `675c7a7`）。**M1〜M6 該当なし**。

- M1: 最大は `keymap_set_io.py` 674 行だが**本フェーズの増分 0**。`config_service/__init__.py` は
  **599 行**（+30）で「600 行超 かつ +100 行以上」に届かない
- M2: 新規関数は最大 19 行 / M4・M5・M6: 該当なし
- **M3 は候補が 1 件出たが非該当に倒した**: `hotkey_presets_io.write_global_presets` の
  `try/except Exception → messagebox.showerror → return False` は `config_io/` の既存 13 箇所と同型
  （計 14 箇所）。ただし各箇所は**メッセージ・保存対象が独立**で「片方を直したらもう片方も直す」関係に
  なく、判定基準の「迷えば非該当」と境界事例の定性材料（責務 3 つ以上 / 説明しにくさ）にも当たらない。
  → **`current.md` の「別タスク化候補」へ 1 行送り**、次フェーズ以降の再判定に委ねる
  （`config_service/__init__.py` の 599 行も同様に候補送り）。

### 【task_08b】フェーズ完了レビューの High 是正（2026-08-09）

- **両レビュアーが独立に同じ High を指摘**（`codex-adversarial-reviewer` / `deep-reviewer`。実測で再現）:
  `normalize_hotkey_presets` が `label` / `value` へ `.strip()` を直接適用するため、**非文字列**
  （int・dict 等）で `AttributeError`。この呼び出しは `load_global_hotkey_presets` の `try` の外で、
  **E1（`App.__init__`）が捕捉しない** → **プリセットファイルの不正要素 1 つでアプリが起動不能**。
  phase 08 以前は同種の破損が `ensure_config_compatibility` で起き、通常読込経路の `except` に拾われて
  **空データ起動へ縮退**していた（＝**回復可能だった状態が起動不能へ変わっていた**）。
- **ユーザー確定 = 要素単位で除去**（非 dict 要素の除去と同じ思想）。却下は
  ①読み出しで `None` へ縮退（要素 1 つの型違いでファイル全体を無視するのは非 dict 要素の扱いと不整合）
  ②`str()` で強制文字列化（dict が `"{'x': 1}"` のようなゴミとして残る）。
- **設計を先に確定**: 正本 `data_schema.md` **§5.10.2** へ「`label` または `value` が文字列でない要素の除去」
  「**正規化はファイル単位で失敗しない**」を追記 → その後 task_08b を実装（直接改訂モード）。
- **`None` / キー無しは従来どおり空文字**（除去しない）。除去は「値が存在するが文字列でない」場合のみ。
  `ensure_config_compatibility` も同じ純関数を呼ぶため副次的に堅くなった（意図した改善）。
- 実測: compile clean / `tests` **203**（+5）/ `tests_ui` **186** / smoke pass。
  **サブエージェントがセッション上限で落ちたためメインで実測**（`verifier` へ委任できず・縮退）。
- `reviewer` = **採用（完了可・指摘なし）**。
- **残り**: 不正 `label` を含むファイルでの起動確認（実機目視 1 点）。

### 【フェーズ完了】2026-08-09

- **task_08b の実機確認 = OK**（不正 `label` を含むファイルで起動でき、不正要素だけが落ちる）。
- **受入条件 1〜9 をすべて充足**して phase 08 完了。
- 最終実測: compile clean / `tests` **203** / `tests_ui` **186** / smoke pass。
- `/refactor_check` = **不要**（候補送り 2 件は `instructions/phase/current.md`「別タスク化候補」）。
- **後続**: [idea_08](../../../instructions/backlog/idea_08_per_keymap_set_preset_ownership.md)
  （keymap_set 個別プリセット・**着手可**）。前提となる正本は `data_schema.md` §5.10。
