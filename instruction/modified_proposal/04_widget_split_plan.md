# リファクタリング計画書 04（Widget 分割・フォルダ再編・挙動不変）

- 作成日: 2026-07-05
- **前提: 計画書 03（`instruction/modified_proposal/03_view_binding_plan.md`）の全項目が完了していること。** views / dialogs / keyboard_window / コントローラは App のコントローラ公開属性（`app.hook` / `app.config_io` 等）を直接参照しており、app.py は組み立て + 実ロジック（約 400〜500 行）になっている状態を基準にする。行番号は記載しない。対象は必ずクラス名・メソッド名で特定し、**着手前に必ず `git grep` で現物を確認する**こと（計画 03 の実施結果によって細部が変わるため）。
- 実行環境の前提: Windows 11 / PowerShell / Python は `py` ランチャで起動する。
- 本計画の性質: **機能追加・仕様変更・バグ修正は一切行わない。** 目的は次の 4 点。
  1. 共有 Tk 変数を `UiVars` ホルダーへ集約し、App 属性への直接依存を減らす
  2. `views.py` の FullView / CompactView を **LabelFrame 単位の Widget クラス**へ分割する（**View 間で共通化しない**。View ごとに専用 Widget を持つ）
  3. 「View が App にウィジェット参照を生やす」逆流（`app.hook_toggle_btn = ...` 等）を解消する
  4. `instruction/common/file_organization_rules.md` の「フォルダ分類の判断順序」に従い、`controllers/` / `views/` の**種類別フォルダ**へ再編し、View 専用 Widget は `views/full_view/` / `views/compact_view/` の**所有者フォルダ**へ置く
- 併読必須: `AGENTS.md`、`instruction/common/architecture_rules.md`、`instruction/common/dev_rules.md`、`instruction/common/file_organization_rules.md`。

---

## 1. 設計（実行者への文脈共有）

### 1.1 完了後のフォルダ構成（目標）

```text
keyseq/presentation/
    app.py                     # Tk ルート・生成と配線（組み立て）のみ
    ui_vars.py                 # UiVars: 共有 Tk 変数ホルダー
    controllers/               # 種類別フォルダ（規約・基本原則4-1）
        config_io_controller.py
        dirty_state.py
        hook_controller.py
        key_capture.py
        keymap_panel_controller.py
        layout_controller.py
        trigger_panel_controller.py
    views/                     # 種類別フォルダ
        menu_bar.py            # メニューバー構築
        status_bar.py          # ステータスバー構築
        full_view/             # 所有者フォルダ（規約・基本原則4-2）
            full_view.py       # FullView: 配置（pack/grid）と Widget の組み立てのみ
            hook_frame.py      # FullHookFrame（取得/クリアボタン付き）
            display_frame.py   # FullDisplayFrame
            file_frame.py      # FileFrame
            keymap_box.py      # KeymapBox
            trigger_box.py     # FullTriggerBox（編集ボタン・suppress 付き）
            sequence_box.py    # SequenceBox
        compact_view/
            compact_view.py    # CompactView
            hook_frame.py      # CompactHookFrame（表示のみ）
            display_frame.py   # CompactDisplayFrame
            trigger_box.py     # CompactTriggerBox（一覧のみ）
    config_paths.py            # 以下は presentation 直下に残す（複数種から使われる共有モジュール）
    dialogs.py
    keyboard_layouts.py
    keyboard_window.py
    listbox_utils.py
    theme.py
    tk_keys.py
```

- Widget のモジュール名は現行の属性名（`hook_frame` / `display_frame` / `file_frame` / `keymap_box` / `trigger_box` / `sequence_box`）を引き継ぐ（追跡性のため）。クラス名は `Full` / `Compact` 接頭辞で衝突を避ける。
- **View 間の共通 Widget は作らない**（規約「共通化より局所化」。Full と Compact では部品構成・配置が異なるため）。将来、完全に同一と判明した Widget があれば昇格ルールに従って共通化する（本計画ではやらない）。

### 1.2 UiVars（共有 Tk 変数ホルダー）

App が直接持っている Tk 変数（`stop_key_var` / `toggle_key_var` / `always_on_top_var` / `keyboard_layout_var` / `suppress_var` / `run_to_end_var` / `run_to_end_delay_var` / `status_var` / `file_status_var` / `keyboard_show_physical_key_labels_var` など。**着手時に `git grep -nE "tk\.(String|Boolean|Int|Double)Var" -- keyseq/presentation/app.py` で全数を確認する**）を `UiVars` クラスへ移す。

```python
# keyseq/presentation/ui_vars.py
class UiVars:
    """View / コントローラ間で共有する Tk 変数のホルダー。App 生成直後に 1 度だけ作られ、差し替わらない。"""
    def __init__(self, master) -> None:
        self.stop_key_var = tk.StringVar(master=master)
        ...
```

- 変数名は現行のまま。参照は `app.stop_key_var` → `app.ui_vars.stop_key_var` へ機械置換する。
- **`AppState`（application 層）とは別物**。UiVars は Tk に依存する presentation 層の部品であり、選択インデックス等のアプリ状態は引き続き `AppState` が持つ。混ぜない。
- Tk 変数はアプリ生存中に差し替わらないため、Widget・コントローラが**コンストラクタで受け取って保持してよい**（`data` と違いキャッシュ禁止の対象外）。ただし迷ったら `self._app.ui_vars.` 経由でよい。

### 1.3 ウィジェット生やしの解消（登録方式）

現在、View は `app.hook_toggle_btn = ttk.Button(...)` のように App へウィジェット参照を生やし、コントローラは `hasattr` ガード付きで `self._app.hook_toggle_btn` を触っている。これを次の 2 方式で置き換える。

1. **複数 View に同種ウィジェットがあるもの（登録方式）**: コントローラに登録リストと登録メソッドを追加し、Widget が生成時に自分を登録する。同期メソッドは登録済みウィジェットを走査する形へ書き換える（走査順は「先に登録された順」= 現行の full → compact の更新順を保つこと）。
   - `HookController.register_hook_buttons(hook_btn, trigger_btn)` ← FullHookFrame / CompactHookFrame が呼ぶ。`sync_hook_toggle_buttons` / `sync_trigger_toggle_buttons` は登録ペアを走査。
   - `TriggerPanelController.register_trigger_list(listbox)` ← FullTriggerBox / CompactTriggerBox が呼ぶ。
   - `LayoutController.register_layout_combo(combo)` ← FullDisplayFrame / CompactDisplayFrame が呼ぶ。
2. **単一 View にしかないもの（所有 Widget の属性として持つ）**: `keymap_listbox` / キーマップ操作ボタン / `action_list` / suppress・連続実行チェック / 停止・トグルキーの Entry と取得・クリアボタン等は、所有 Widget（KeymapBox / SequenceBox / FullHookFrame 等）の属性にする。コントローラからの参照は `self._app.full_view.keymap_box.listbox` のように **App → View → Widget のパス**で辿る（`hasattr` ガードが現行にある箇所は、同等の存在ガードを維持する）。
   - `SingleKeyCaptureController` は現在 `var_attr` / `capture_btn_attr` 等の**属性名文字列**で App からウィジェットを引いている。これを「Tk 変数はコンストラクタで直接受け取り、ボタン・Entry は `register_widgets(entry, capture_btn, clear_btn)` で受け取る」形に変える（キャプチャ UI は FullView にしかないため登録は 1 回。**Compact 表示中もキャプチャ状態が破綻しないこと**を手動確認する）。

いずれの場合も、**登録し忘れ・パス変更漏れはスモーク・tests_ui・手動確認で検出する**。コントローラの同期メソッドのロジック（文言・state 遷移）は 1 文字も変えない。

### 1.4 Widget クラスの形

- 各 Widget は `ttk.LabelFrame` を継承し、`def __init__(self, parent, app)` で生成する（`text=` / `padding=` は現行値をそのまま移す）。
- Widget 内で完結する補助処理があれば Widget のメソッドとして閉じる。**Widget からコントローラへの参照は `app.<コントローラ名>` 経由**（バインドは計画 03 完了時点の形を維持）。
- FullView / CompactView は「Widget の生成と pack/grid 配置」だけを持つ組み立てクラスになる。

---

## 2. 項目 W0: 前提確認とブランチ作成（最初に必ず実行）

```powershell
git status                          # クリーンであること
git rev-parse HEAD                  # ベースラインとして記録

# 計画03の完了確認（例。詳細は 03 の V9 報告と突き合わせる）
git grep -n "command=app.hook.toggle_hook" -- keyseq/presentation/views.py   # 1 件以上
git grep -nE "def _refresh_triggers|def _set_dirty" -- keyseq/presentation/app.py  # 0 件（委譲削除済み）

py -m compileall -q keyseq main.py
py -m unittest discover -s tests -v      # 全緑
py -m unittest discover -s tests_ui -v   # 全緑
py -m tests.smoke_app                    # SMOKE OK
```

1 つでも満たさなければ中断して報告する。満たしたら `git switch -c refactor/04-widget-split`。

> **標準検証** = 計画 03 と同じ（compileall → tests → tests_ui → smoke）。

---

## 3. 作業項目リスト（この順に実行。1 項目 = 1 コミット）

### W1: UiVars の導入

- **どう変えるか**: §1.2 のとおり `keyseq/presentation/ui_vars.py` を新規作成し、App の Tk 変数定義を移す。`App.__init__` の早い段階（コントローラ生成より前）で `self.ui_vars = UiVars(self)` を生成する。全参照（app.py / views.py / コントローラ / tests_ui）を `git grep -n "<変数名>" -- keyseq tests_ui` で列挙して `app.ui_vars.<変数名>`（コントローラ内は `self._app.ui_vars.<変数名>`）へ置換する。App に旧名のプロパティは**残さない**。
  - `SingleKeyCaptureController` の `var_attr`（属性名文字列）は、この項目で「Tk 変数を直接コンストラクタで受け取る」形に変えてよい（§1.3-2 の前倒し。ボタン類の registration は W5 で行う）。
  - tests_ui の `app.status_var.get()` 等は `app.ui_vars.status_var.get()` へ（**アサーション変更禁止**）。
- **完了条件**: `git grep -nE "self\.(stop_key_var|status_var|file_status_var)\s*=" -- keyseq/presentation/app.py` が 0 件 → 標準検証 → 手動確認: 停止キー表示・ステータスバー・「常に手前」がフル/省略両方で機能する。
- **リスク / 戻し方**: 低〜中。`git revert HEAD`。
- **依存**: W0

### W2: メニューバーとステータスバーの移設

- **どう変えるか**: `App._build_menu`（ショートカットバインド `_bind_menu_shortcuts` を含むか否かは現物を確認して判断し、報告に残す）を `keyseq/presentation/views/menu_bar.py` の `build_menu_bar(app)` 関数へ、`App._build_status_area` を `keyseq/presentation/views/status_bar.py` の `build_status_area(app, parent)` へ移す（`views/` フォルダはこの項目で新規作成する）。メソッド本文は無変更で移し、`self.` → `app.` に置換する。App 側は移設先を呼ぶ 1 行にする。
- **完了条件**: `git grep -nE "def _build_menu|def _build_status_area" -- keyseq/presentation/app.py` が 0 件 → 標準検証 → 手動確認: 全メニュー項目が開く・ショートカットが効く・ステータスバー表示が従来どおり。
- **リスク / 戻し方**: 低。`git revert HEAD`。
- **依存**: W1

### W3: CompactView の Widget 分割

- **どう変えるか**: `views.py` の `CompactView.__init__` の LabelFrame 3 つを `views/compact_view/` 配下の `CompactHookFrame` / `CompactDisplayFrame` / `CompactTriggerBox` へ切り出し、`CompactView` は生成と配置のみにする。**この項目では App への生やし（`app.compact_hook_toggle_btn = ...` 等）は現行のまま維持する**（生やし解消は W5。1 項目 1 関心事）。`views.py` の `CompactView` 本体は `views/compact_view/compact_view.py` へ移し、`views.py` には移行用の re-export（`from keyseq.presentation.views.compact_view.compact_view import CompactView`）を置く（W6 で削除する。恒久化しない）。
- **完了条件**: 標準検証 → 手動確認: 省略表示へ切替 → フック開始/停止・停止キー表示・トリガー一覧・フル復帰。
- **リスク / 戻し方**: 低〜中。`git revert HEAD`。
- **依存**: W2

### W4: FullView の Widget 分割

- **どう変えるか**: W3 と同じ要領で `FullView` の LabelFrame 6 つを `views/full_view/` 配下へ切り出す。生やしは維持。`views.py` の `FullView` も `views/full_view/full_view.py` へ移し、re-export を置く。
- **完了条件**: 標準検証 → 手動確認: フル表示の全パネル（フック・表示・ファイル・キーマップ・トリガー・シーケンス）の操作一巡。
- **リスク / 戻し方**: 中（面積が大きい）。`git revert HEAD`。
- **依存**: W3

### W5: ウィジェット生やしの解消（登録方式への切替）

- **どう変えるか**: §1.3 のとおり。
  1. 対象の洗い出し: `git grep -nE "app\.[a-z_]+ = (ttk|tk)\." -- keyseq/presentation/views` と `git grep -nE "app\.(compact_)?[a-z_]*(btn|chk|entry|combo|listbox) =" -- keyseq/presentation/views` で View が App に生やしている全属性を列挙し、生やし箇所と読み取り側（コントローラの `self._app.<属性>`）の対応表を作って報告に含める。
  2. 複数 View 共有のもの（フック 2 ボタン・トリガー一覧・レイアウトコンボ）→ コントローラへ登録メソッドを追加し、Widget 生成時に登録。同期メソッドを登録リスト走査に書き換える（更新順・文言・state 遷移は不変）。
  3. 単一 View のもの → 所有 Widget の属性とし、コントローラの参照を `self._app.full_view.<widget>.<child>` パスへ付け替える。現行の `hasattr(self._app, "...")` ガードは「View 未生成でも落ちない」ための同等ガード（`getattr` 連鎖等）として維持する。
  4. `git grep -nE "app\.[a-z_]+ = (ttk|tk)\." -- keyseq/presentation/views` が 0 件になったことを確認する。
- **完了条件**: 上記 grep 0 件 → 標準検証 → **手動確認（必須）**: フック ON/OFF 時に**フル・省略両方**のボタン文言が切り替わる、キャプチャ取得中のボタン文言変化と Esc キャンセル、キーマップ管理ボタンの活性/非活性、レイアウトコンボ 2 箇所の同期。
- **リスク / 戻し方**: **本計画で最大**（コントローラと View の接点を全部触る）。`git revert HEAD`。
- **依存**: W3、W4

### W6: 種類別フォルダへの移動（controllers/ と views.py の後始末）

- **どう変えるか**:
  1. `git mv` で §1.1 の 7 ファイルを `keyseq/presentation/controllers/` へ移動し、`__init__.py` を作成、全 import を更新する（`git grep -n "from keyseq.presentation.hook_controller"` 等で列挙してから）。**ファイル内容は import 行以外変更しない。**
  2. `views.py` の re-export（W3/W4 で置いた移行用）を削除し、参照元（app.py / tests_ui）を新パスへ更新して `views.py` を削除する。
  3. `ui_vars.py` / `config_paths.py` / `listbox_utils.py` / `tk_keys.py` / `theme.py` / `dialogs.py` / `keyboard_window.py` / `keyboard_layouts.py` は presentation 直下に残す（複数種から使われる共有モジュール。規約の共通フォルダ制約に従い、雑多な `common/` は作らない）。
- **完了条件**: `git grep -n "presentation.views import\|presentation import views" -- keyseq tests tests_ui` で旧パス参照 0 件 → 標準検証。
- **リスク / 戻し方**: 低（機械的移動）。import 漏れは compileall で検出。`git revert HEAD`。
- **依存**: W5

### W7: App の組み立て専念化の最終確認・実測とドキュメント更新

- **やること**:
  1. app.py に残ったメソッドを列挙し、「Tk ルート管理 / 生成と配線 / View 切替 / 調整役 / dialogs 向け契約」のどれに属するか分類して報告する。どれにも属さない残留ロジックがあれば、**移動はせず**報告書に次期課題として列挙する（本計画の範囲外）。
  2. 標準検証をフルで実行し、さらに計画 02 S10 の**フック手動確認 6 項目**をフルで実施する。
  3. `(Get-Content keyseq/presentation/app.py | Measure-Object -Line).Lines` を実測し報告する。**目安は 300 行未満。**
  4. `instruction/common/codebase_map.md` を更新する（フォルダ構成図を §1.1 の形に、App / UiVars / 各 Widget の責務を追記）。
  5. 最終報告: コミット一覧、app.py / views 系ファイルの行数一覧、生やし解消の対応表、スキップ・失敗項目。
- **完了条件**: 上記すべて完了し `git status` クリーン。
- **依存**: W1〜W6

---

## 4. やらないことリスト（実行者は以下を行ってはならない）

1. **FullView と CompactView の間で Widget を共通化すること**（similar でも別クラスとして持つ。共通化の判断は将来の計画で行う）。
2. **挙動変更・バグ修正・機能追加**。文言・レイアウト値（padding / width / pady 等）は 1 文字も変えない。
3. **コントローラのロジック変更**（§1.3 で指定した「属性参照 → 登録リスト走査 / パス参照」への書き換えを除く）。
4. **`data` / `keymap_set_path` のキャッシュ**（Tk 変数・登録ウィジェット参照の保持は §1.2 / §1.3 のとおり可）。
5. **application / domain / infrastructure 層の変更**（`AppState` へ手を入れない）。
6. **tests/ の期待値変更、tests_ui のアサーション変更**（参照経路の書き換えのみ可）。
7. **恒久的な re-export・互換レイヤー**（W3/W4 の移行用 re-export は W6 で必ず削除する）。
8. **dialogs.py / keyboard_window.py / keyboard_layouts.py の内部構造変更**（参照経路の追従を除く）。
9. **フックを張ったままの放置**、**git push**。

## 5. 補足: 本計画完了後の姿と、その先（参考情報。作業対象ではない）

- app.py ≒ 200〜300 行（Tk ルート + 生成/配線 + View 切替 + 調整役 + dialogs 契約）。各 Widget ファイルは 100 行前後。
- その先の候補: Full/Compact で完全同一と判明した Widget の昇格統合／dialogs の親プロトコル（`parent.validate_hotkey` / `parent._dialog_result`）の明示インターフェイス化／コントローラの `app` 依存を絞る。

## 6. 実行者への指示文（この計画書を渡すときにそのままコピペする)

```
あなたはこのリポジトリのリファクタリング実行者です。
instruction/modified_proposal/04_widget_split_plan.md を最初から最後まで読み、記載どおりに作業してください。

厳守事項:
- まず「項目 W0」の前提条件チェックを行う。計画03が未完了なら作業せず、その旨を報告して終了する。
- W0 → W1 → … → W7 の順に 1 項目ずつ実施する。1 項目 = 1 コミット。
- 本計画は計画03完了後のコードを前提に書かれている。各項目の対象は着手前に必ず git grep で現物を確認し、
  計画の記載と食い違う場合は独自判断で進めず、中断して報告する。
- 「やらないことリスト」に該当する変更は、改善に見えても行わない。
  特に FullView / CompactView 間の Widget 共通化と、文言・レイアウト値の変更は禁止。
- tests_ui はアサーション変更禁止（参照経路の書き換えのみ可）。
- Python は py コマンドで実行する。挙動を変えないことが最優先。
- W5 の手動確認（フル・省略両方のボタン同期）と W7 のフック手動確認 6 項目は省略禁止。
  確認前に必ず停止キーを設定すること。

最終成果物:
- refactor/04-widget-split ブランチ上の一連のコミット
- 実施項目 / スキップ項目 / app.py と views 系の行数一覧 / 生やし解消の対応表 / 各項目の検証結果を列挙した報告
```
