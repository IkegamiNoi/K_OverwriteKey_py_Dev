# 暫定仕様 54: タスクバーのアイコンで状態を表示（taskbar_status_icon）

> 状態: **未凍結・v0.4・主入力・ユーザー確定済（2026-10-31）・実装着手可**（v0.4 = task_01 の試作の結果で §3.3 = 案 B・§5 = 案 A・§4.3 の印の形を確定）。v0.1 の起票時 deep-reviewer「修正要」13 件・v0.2 の Codex 敵対的レビュー needs-attention 1 件（部分失敗後の状態の記録）を反映。本書がこのフェーズの確定設計（フェーズ中は正本を直接改訂しない）。
> フェーズ末タスクで正本 `instructions/common/spec_detail/` へ昇格し本書を凍結する。
> 起票元: [idea_55](../backlog/idea_55_taskbar_status_icon.md)（ユーザー要望 2026-10-31・タスクバーでアプリの ON / OFF / 一時停止が分かるようにする）。
> 番号対応: phase 71 / 暫定 54 / decisions 71。

---

## §1 目的 / 背景

タスクバーのボタンを見るだけで、フックが ON / OFF / 一時停止のどれかが分かるようにする。
窓のアイコン（`wm iconphoto`）を状態ごとに差し替え、土台の画像の**右上に色＋形の印**を重ねる。
**presentation の変更 + infrastructure に 1 関数（AppUserModelID・§3.3）・新規依存なし・JSON スキーマ（config.json・構成セット・レイアウト）は変えない**。

### 現状監査（2026-10-31）

- 窓のアイコンは未設定（`iconphoto` / `iconbitmap` の使用 0 件・画像素材なし）。Tk 既定の羽のアイコン。
- メインの窓は `App(tk.Tk)`（`presentation/app.py:139` で `title` 設定）。通常の窓でタスクバーにボタンが出る。
  `overrideredirect` を使うのは補助の窓だけ（`dialogs/grid_editor_window.py:52` ・ `hover_tooltip.py:45` ・ `screen_grid/grid_overlay_window.py:32`）。
- DPI 対応の宣言（`SetProcessDpiAwareness` 等）・AppUserModelID の設定はどちらも 0 件。
- ステータス欄の 3 状態（正本 `features.md` §4.5「ステータス欄のフックの 3 状態」・phase 58）:
  `TriggerPanelController.update_status`（`controllers/trigger_panel/trigger_panel_controller.py:409`）の 410-415 行が
  `hook_active` が偽 → `OFF` / `custom_input_enabled` が偽 → `一時停止` / それ以外 → `ON` を決める（OFF 優先）。
  簡易表示中は 421-428 行で文言を設定して早く return する。
  `update_status` の呼び出しは約 30 か所（presentation 22・sequence_runner の `_update_status` 8）。
- `hook_active` / `custom_input_enabled` を書き換える所（`hook_controller.py:157-158, 172-174, 201, 219`）は、どれもその後 `update_status` へ進む。
  `update_status` を通らずに状態が変わる経路は無い（例外で途中終了した場合は文言も更新されない）。
- ダイアログを開くとフックは止まる（`hook_controller.py:49` `suspend_hook_for_dialog` → 55 行 `stop_hook`・`hook_active` が偽）。
  このためダイアログ・キーの取得の間、ステータス欄は `OFF` になる（アイコンも赤でよい・§2）。
- 同梱データの場所は `presentation/help/bundled_paths.py` の `bundled_root()`（`Path(__file__).resolve().parents[3]`）に集約（phase 70）。
  利用はヘルプの 2 ファイル（`help_content.py:10` ・ `third_party.py:7`）+ テスト 2 ファイル。
- 入口は `main.py`（`App()` を作って `mainloop`）。Win32 の呼び出しは `infrastructure/win32_window.py` に集約（`_guarded` で失敗をログに残して既定値を返す）。

### 試作の結果（task_01・2026-10-31・Windows 11 の実機目視）

- **AppUserModelID を設定しないと、`iconphoto` の差し替えがタスクバーのボタンに出ない**。設定すれば出る → §3.3 = 案 B。
- **`-default`（`iconphoto(True, …)`）だけで、開いている子窓も後から開く子窓も追従する** → §5 = 案 A。
  一度でも子窓へ個別に設定すると、その子窓は既定に追従しなくなる（予想どおり）。
- 印の形: 2 本の棒をそれぞれ白で縁取る形は見づらい → **3 つとも白い正方形の上に描く形**に改めた（§4.3）。16 / 32 px で判別できる。

## §2 確定事項（ユーザー 2026-10-31）

- **状態はステータス欄の「フック: ON / OFF / 一時停止」と常に一致させる**（同じ判定を使う。独自の判定を作らない）。
- **印 = 色＋形**: ON = 緑の● / OFF = 赤の■ / 一時停止 = 黄の‖。白のフチを付け、タスクバーの小さいサイズでも見分けられること。
- **土台は画像ファイル**（PNG・まず Claude のサンプルを同梱し、ユーザーが差し替える）。その上に印を描く。
- **子窓も同じアイコンにする**（開いている子窓も状態の変化に追従する）。
- **通知領域（トレイ）のアイコン・常駐化はしない**。Windows のオーバーレイアイコン（右下固定）は使わない。
- **phase 71 として多言語対応より先に入れる**。**Mac での見え方は対象外**（Windows のタスクバーで確認する）。
- **ダイアログ・キーの取得の間はアイコンも赤（OFF）でよい**（フックは実際に止まっており、ステータス欄とも一致する）。
- **土台の画像は Claude がサンプル（16 / 32 px）を作って同梱し、後でユーザーが同じファイル名で差し替える**（§4.1）。
- **タスクバーへの反映の方式（§3.3）と開いている子窓の方式（§5）は、最初のタスクの試作で決める**。
  → 試作の結果（2026-10-31）: **起動時に AppUserModelID を設定する**・**子窓は `-default` だけ**・**印は 3 つとも白い正方形の上に描く**（§3.3・§5・§4.3）。

## §3 状態の決め方と反映

### 3.1 判定

- ステータス欄の判定を Tk に依存しない純関数へ切り出す:
  `hook_display_state(hook_active: bool, custom_input_enabled: bool) -> "on" | "off" | "paused"`
  （置き場 = `presentation/status_text.py`）。ステータス欄の文言（`ON` / `OFF` / `一時停止`）とアイコンの両方がこれを使う。判定の内容は変えない（OFF 優先）。
- **シーケンス側の実行の一時停止**（連続実行の一時停止 `run_to_end_paused`・呼び出しの一時停止）は**含めない**（ステータス欄の「一時停止」はキーマップ一時停止だけ）。

### 3.2 反映の位置と規則

- `update_status` の中で、**判定の直後・簡易表示 / 詳細表示の分岐より前**に反映する（どちらの表示でも追従する）。
- **前回と同じ状態なら差し替えない**。ただし前回の状態は、**反映を始める前に消し、対象の窓すべてへの設定が成功した後にだけ記録する**
  （一部の窓で失敗したら記録しない。これで「ON 成功 → OFF で一部失敗 → ON」でも ON を設定し直す。失敗のあと次の `update_status` で再試行できる）。
- 反映の失敗（`TclError`・破棄されかけの窓等）は吸収してログに残し、**ステータス欄の更新を止めない**。
- アイコンの部品（§6 `StatusIcon`）がまだ作られていない（起動の途中）・持たない（tests_ui の SimpleNamespace の App 等）ときは**何もしない**。
- 起動時: `App` の初期化で、UI の構築（`_build_ui`）より前に部品を作り、`OFF` を設定する（フック開始前は OFF）。

### 3.3 タスクバーへの反映（AppUserModelID・試作で確定）

python.exe で動かすと、Windows はタスクバーのボタンを python の AppUserModelID でまとめ、`iconphoto` の変更がタスクバーに出ない（試作で確認）。
そこで**起動時、最初の窓を作る前に**アプリ固有の AppUserModelID を設定する:

- `infrastructure/win32_window.py` に `set_app_user_model_id(app_id: str) -> bool` を足す。標準ライブラリの ctypes で `shell32.SetCurrentProcessExplicitAppUserModelID` を呼ぶ（新規依存なし）。
  Windows 以外・失敗時は何もせず偽を返す（既存の `_guarded` と同じくログに残す）。
- 呼び出し元 = `main.py` の `main()`、`App()` を作る前。ID = `"keyseq.app"`（定数）。
- 副作用: タスクバーのボタンは python の他の窓とまとまらず、このアプリだけのボタンになる。python.exe をピン留めしたボタンとは別のボタンになる。

## §4 画像

### 4.1 土台の画像ファイル

- 置き場: `keyseq/presentation/status_icon/images/`。ファイル名 = `app_icon_<任意>.png`（例: `app_icon_16.png` / `app_icon_32.png`）。**フォルダが無くてもよい**。
- **サンプル**: Claude が `app_icon_16.png` / `app_icon_32.png`（キーキャップ風の簡単な図形・透過）を作って同梱する。作るのは一度きりのスクリプト（Tk の `PhotoImage.write`・新規依存なし）で、スクリプトは同梱しない。ユーザーは同じファイル名で差し替える。
- **正方形の PNG**（透過可）。**大きさはファイル名ではなく実際の画像で判定する**。
- 使うのは辺が **16 / 32 / 48 px** のものだけ（Windows 版の Tk は小 = 16・大 = 32 に近いものを使う。このアプリは DPI 対応を宣言していないため 48 は高 DPI 用の任意）。
  推奨 = **16 と 32 の 2 枚**。同じ大きさが複数あれば、ファイル名の昇順で最初の 1 枚を使う。
- 縮小・拡大はしない（Tk の `PhotoImage` は整数倍の間引きしかできず画質が落ちるため）。
- 正方形でない・16 / 32 / 48 でない・読めないファイルは使わず、ログに残す（エラーダイアログは出さない）。

### 4.2 使える画像が 0 枚のとき

- **印だけのアイコン**にする（16 / 32 の透過の正方形に、印を全体の大きさで描く）。
  画像の用意を待たずに機能を確認できる。フォルダが無い・全部不正なときも同じ。

### 4.3 印の描き方

- 四捨五入は `int(x + 0.5)`（Python の `round` は偶数丸めのため使わない）。
- **印の領域** = 右上の角に接する正方形。辺 `s = max(7, int(辺 × 0.45 + 0.5))`（16 → 7 / 32 → 14 / 48 → 22）。§4.2 では `s = 辺`。
- **フチの太さ** `b` = 1（辺 32 未満）/ 2（辺 32 以上。§4.2 も同じ基準）。
- 形（3 つとも**領域 `s × s` いっぱいの白い正方形**を描き、その内側 `b` を除いた `iw = s − 2b` の範囲に色の形を描く。試作で確定）:
  - ON = 円: 中心は領域の中心・直径 `iw` の緑の円（画素の中心が円の内側なら緑・それ以外は白）。
  - OFF = 正方形: 内側 `iw × iw` いっぱいの赤の正方形。
  - 一時停止 = 2 本の棒: すき間 `g = max(1, int(iw × 0.2 + 0.5))`・棒の幅 `bw = (iw − g) // 2`・高さ `iw`。余り `iw − (2bw + g)` は左右に振り分け（左 = 余り // 2）。棒の外は白。
  （16 → s 7・b 1・iw 5・g 1・bw 2 / 32 → s 14・b 2・iw 10・g 2・bw 4）
- 色: ON = `#1E9E3E` / OFF = `#D93025` / 一時停止 = `#F2B400`。下地 = `#FFFFFF`（試作で確定）。
- 描画は `PhotoImage` の `copy` と `put` だけで行う（新規依存なし）。形の画素の計算は Tk に依存しない純関数にし、`put` は**行単位でまとめて**渡す（1 画素ずつ呼ばない）。
- 16 / 32 px で形が見分けられることは試作で確認済み。土台の画像を差し替えた後の見え方は task_05 の実機目視で確かめる。

### 4.4 画像の持ち方

- `PhotoImage` は**ルートの窓（Tk のインタプリタ）ごとに作る**（モジュール全体で共有しない。tests_ui で App を何度も作るため）。
- 3 状態分の画像は部品の作成時に作って部品が保持する（参照を持ち続け、GC で消えないようにする）。

## §5 子窓

- ルートの `iconphoto(True, ...)`（既定のアイコン）で、**これから作る子窓**も同じアイコンにする。
- **開いている子窓も `-default` だけで追従する**（試作で確定）。**子窓へ個別に `iconphoto` を設定しない**（一度でも設定すると既定に追従しなくなるため）。
  ルートへの `iconphoto(True, …)` 1 回で、ルート・開いている子窓・後から開く子窓のすべてが変わる。
- `overrideredirect` の窓（ツールチップ・カーソルグリッドの枠・編集の窓）は区別しない（設定しても害がない）。
- 標準のメッセージボックス（`tkinter.messagebox`）は対象外。

## §6 配置

- 新規パッケージ `keyseq/presentation/status_icon/`:
  - `badge_shapes.py` — 形の画素の計算（純関数・Tk 非依存）
  - `status_icon.py` — `StatusIcon`: 画像の読込（§4.1）・印の合成・ルートへの `iconphoto(True, …)`・前回の状態の記録
  - `images/` — 土台の画像（ユーザーが置く。無くても動く）
- `bundled_paths.py` は 2 つの機能（ヘルプ・アイコン）から使うことになるため、
  `presentation/help/bundled_paths.py` → **`presentation/bundled_paths.py` へ昇格**する（`file_organization_rules.md` の昇格ルール: Private → Feature Shared）。
  旧パスの横流しは残さず、import をすべて更新する。**`bundled_root()` は `parents[3]` → `parents[2]` に直す**（1 階層上がるため）。`status_icon_dir()` を足す。
- 判定関数 `hook_display_state` は `presentation/status_text.py`（§3.1）。

## §7 テスト

- tests:
  - `badge_shapes` の形（円・正方形・2 本の棒・フチ・最小 7px・右上の位置・§4.2 の全体の大きさ）。
  - `hook_display_state` の 4 通り（OFF 優先）。
  - `set_app_user_model_id`（ctypes の呼び出しを差し替えて: 成功で真・失敗 / Windows 以外で偽）。
  - 既存の `bundled_paths` のテスト（`tests/test_help_content.py` ・ `tests/test_third_party.py`）は import 先の変更に追従する。
- tests_ui:
  - Tk には設定したアイコンを読み返す手段が無いため、**`wm_iconphoto` を差し替えて呼び出し（引数・`default` の有無）を記録する**方式で確かめる。
  - 状態 → 差し替え（同じ状態では呼ばない・失敗の後は再試行する・**「ON 成功 → OFF で一部失敗 → ON」で ON を設定し直す**）・簡易表示でも追従・ステータス欄の文言との一致。
  - 画像の読込（使える画像が 0 枚 → 印だけ・正方形でない / 対象外の大きさ / 読めないものは使わない・フォルダが無い）。
  - 子窓へ個別に `iconphoto` を呼ばないこと（ルートへの `default=True` の 1 回だけ）。
  - `StatusIcon` を持たない App（既存の SimpleNamespace のフェイク）で `update_status` が壊れないこと。

## §9 確認事項（ユーザー判断）

なし（旧 §9-1〜3 = ダイアログ中の赤・画像のサイズ・用意の時期 / 旧 §9-4 = §3.3・§5 の方式は 2026-10-31 に確定し、§2・§3.3・§5 へ移した）。

## §10 受け入れ条件（ドラフト）

1. フックを開始 / 停止 / キーマップ一時停止 / 再開すると、タスクバーのアイコンの印がステータス欄と同じ状態に変わる。詳細表示・簡易表示のどちらでも（§3）。
2. 印は ON = 緑●・OFF = 赤■・一時停止 = 黄‖ で、100% 表示のタスクバーで形が見分けられる（§4.3・実機目視）。
3. 開いている子窓・後から開く子窓も同じアイコンになる（§5・実機目視）。
4. 使える画像が 0 枚のときは印だけのアイコンで動き、エラーにならない。対象外・読めない画像は使わずログに残す（§4.1・§4.2）。
5. 反映の失敗でステータス欄の更新が止まらない（§3.2）。
5a. 起動時に AppUserModelID が設定され、失敗しても起動が止まらない（§3.3）。
6. `bundled_paths.py` が `presentation/` 直下にあり、旧パスが残っておらず、`bundled_root()` が同じ場所を返す（§6）。
7. tests / tests_ui / smoke が通る（§7）。

## §11 スコープ外（本フェーズでやらない）

- 通知領域（トレイ）のアイコン・常駐化・右クリックメニュー。
- Windows のオーバーレイアイコン（`ITaskbarList3::SetOverlayIcon`）。
- Mac での見え方（Dock のアイコン）。Mac 対応のフェーズで扱う。
- 土台の画像の本番のデザイン（サンプルは Claude が用意・本番はユーザーが差し替える）。
- DPI 対応の宣言（高 DPI で 48px を使わせる等）。
- exe 化の `.ico` の埋め込み（exe のファイルのアイコン）。

## §12 正本反映（フェーズ末昇格・予定）

- 正本: `features.md` §4.5（ステータス欄のフックの 3 状態の直後に「タスクバーのアイコン」を追加）/
  `instructions/common/codebase_map.md`（`status_icon/` ・ `bundled_paths.py` の移動・`hook_display_state`）/
  architecture の該当箇所（同梱データの置き場）。
- 実装: `presentation/status_icon/`（新規）・`presentation/bundled_paths.py`（移動）・`presentation/status_text.py`（判定関数）・
  `trigger_panel_controller.py`（`update_status`）・`app.py`（部品の作成と初回設定）・`infrastructure/win32_window.py`（`set_app_user_model_id`）・`main.py`（その呼び出し）。
- テスト: `tests/test_badge_shapes.py`（新規）・`tests/test_status_text.py` 相当（判定）・`tests_ui/`（新規 1 ファイル）・`tests/test_help_content.py` / `tests/test_third_party.py`（import の更新）。
- ライセンス: 土台の画像はユーザーの著作物（アプリと同じ GPL v3 の扱い）。ライセンスの窓の同梱物の一覧（第三者）には足さない。

## 関連

- [idea_55](../backlog/idea_55_taskbar_status_icon.md)
- phase 58（ステータス欄の 3 状態）: [decisions_archive/58](../../.claude_data/state/decisions_archive/58_window_size_fit.md)
- phase 70（`bundled_paths.py`）: [暫定 53](53_help_window.md)
- 正本 `features.md` §4.5 / §4.6
