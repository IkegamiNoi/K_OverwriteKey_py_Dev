# 暫定仕様 54: タスクバーのアイコンで状態を表示（taskbar_status_icon）

> 状態: **未凍結・v0.3・主入力・ユーザー確定済（2026-10-31）・実装着手可**（§3.3・§5 の方式は task_01 の試作で決め、本書へ反映してユーザー確認する）。v0.1 の起票時 deep-reviewer「修正要」13 件・v0.2 の Codex 敵対的レビュー needs-attention 1 件（部分失敗後の状態の記録）を反映。本書がこのフェーズの確定設計（フェーズ中は正本を直接改訂しない）。
> フェーズ末タスクで正本 `instructions/common/spec_detail/` へ昇格し本書を凍結する。
> 起票元: [idea_55](../backlog/idea_55_taskbar_status_icon.md)（ユーザー要望 2026-10-31・タスクバーでアプリの ON / OFF / 一時停止が分かるようにする）。
> 番号対応: phase 71 / 暫定 54 / decisions 71。

---

## §1 目的 / 背景

タスクバーのボタンを見るだけで、フックが ON / OFF / 一時停止のどれかが分かるようにする。
窓のアイコン（`wm iconphoto`）を状態ごとに差し替え、土台の画像の**右上に色＋形の印**を重ねる。
**presentation のみの変更（§3.3 の案 B を採る場合だけ infrastructure に 1 関数）・新規依存なし・JSON スキーマ（config.json・構成セット・レイアウト）は変えない**。

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
  このためダイアログ・キーの取得の間、ステータス欄は `OFF` になる（§9-1）。
- 同梱データの場所は `presentation/help/bundled_paths.py` の `bundled_root()`（`Path(__file__).resolve().parents[3]`）に集約（phase 70）。
  利用はヘルプの 2 ファイル（`help_content.py:10` ・ `third_party.py:7`）+ テスト 2 ファイル。

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

### 3.3 タスクバーへの反映（最初のタスクで実機確認）

python.exe で動かすと、Windows はタスクバーのボタンを python の AppUserModelID でまとめ、`iconphoto` の変更がタスクバーに出ない場合がある（特に python をピン留めしているとき）。
**最初のタスクを実機での試作（スパイク）**とし、次を確かめてから本実装の方式を決める（結果は本書へ反映し v0.4 とする）:

- 案 A（既定）: `iconphoto` だけでタスクバーのボタンのアイコンが変わる → そのまま。
- 案 B（A で出ないとき）: 起動時（最初の窓を作る前）に、標準ライブラリの ctypes で `shell32.SetCurrentProcessExplicitAppUserModelID` を呼び、アプリ固有の ID を設定する（新規依存なし）。
  置き場 = `infrastructure/win32_window.py`（Win32 の問い合わせの集約先・phase 55）。Windows 以外・失敗時は何もしない。
- 試作では §5 の `-default` が開いている子窓に効くかも確かめる。

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
- 形（いずれもフチの白を外側に含めて領域 `s × s` に収める）:
  - ON = 円: 直径 `s` の白い円の内側に、直径 `s − 2b` の緑の円。
  - OFF = 正方形: 領域いっぱいの白い正方形の内側に、辺 `s − 2b` の赤の正方形。
  - 一時停止 = 2 本の棒: 棒の外形の幅 `w = (s − 1) // 2`・すき間 `s − 2w`・高さ `s`。各棒を白（外形）で塗り、内側 `b` を除いた部分を黄で塗る（フチは棒ごと）。
- 色（案）: ON = `#1E9E3E` / OFF = `#D93025` / 一時停止 = `#F2B400`。フチ = `#FFFFFF`。
- 描画は `PhotoImage` の `copy` と `put` だけで行う（新規依存なし）。形の画素の計算は Tk に依存しない純関数にし、`put` は**行単位でまとめて**渡す（1 画素ずつ呼ばない）。
- 7px（16px の画像の印）で形が見分けられるかは実機目視で確かめる。足りなければ寸法・色を調整してよい（調整後の値を本書へ反映する）。

### 4.4 画像の持ち方

- `PhotoImage` は**ルートの窓（Tk のインタプリタ）ごとに作る**（モジュール全体で共有しない。tests_ui で App を何度も作るため）。
- 3 状態分の画像は部品の作成時に作って部品が保持する（参照を持ち続け、GC で消えないようにする）。

## §5 子窓

- ルートの `iconphoto(True, ...)`（既定のアイコン）で、**これから作る子窓**も同じアイコンにする。
- **開いている子窓**の扱いは §3.3 の試作で決める:
  - 案 A（既定）: `-default` だけで開いている子窓も変わる → 全走査はしない。
  - 案 B（A で変わらないとき）: 状態が変わるたびに、ルートから辿れる `Toplevel` すべて（入れ子を含む）へ同じ画像を設定する。
    いったん個別に設定した子窓は既定に追従しなくなるため、**毎回全部へ設定し続ける**。
- `overrideredirect` の窓（ツールチップ・カーソルグリッドの枠・編集の窓）は区別しない（設定しても害がない）。
- 標準のメッセージボックス（`tkinter.messagebox`）は対象外。

## §6 配置

- 新規パッケージ `keyseq/presentation/status_icon/`:
  - `badge_shapes.py` — 形の画素の計算（純関数・Tk 非依存）
  - `status_icon.py` — `StatusIcon`: 画像の読込（§4.1）・印の合成・ルート（と §5 案 B なら子窓）への設定・前回の状態の記録
  - `images/` — 土台の画像（ユーザーが置く。無くても動く）
- `bundled_paths.py` は 2 つの機能（ヘルプ・アイコン）から使うことになるため、
  `presentation/help/bundled_paths.py` → **`presentation/bundled_paths.py` へ昇格**する（`file_organization_rules.md` の昇格ルール: Private → Feature Shared）。
  旧パスの横流しは残さず、import をすべて更新する。**`bundled_root()` は `parents[3]` → `parents[2]` に直す**（1 階層上がるため）。`status_icon_dir()` を足す。
- 判定関数 `hook_display_state` は `presentation/status_text.py`（§3.1）。

## §7 テスト

- tests:
  - `badge_shapes` の形（円・正方形・2 本の棒・フチ・最小 7px・右上の位置・§4.2 の全体の大きさ）。
  - `hook_display_state` の 4 通り（OFF 優先）。
  - 既存の `bundled_paths` のテスト（`tests/test_help_content.py` ・ `tests/test_third_party.py`）は import 先の変更に追従する。
- tests_ui:
  - Tk には設定したアイコンを読み返す手段が無いため、**`wm_iconphoto` を差し替えて呼び出し（引数・`default` の有無）を記録する**方式で確かめる。
  - 状態 → 差し替え（同じ状態では呼ばない・失敗の後は再試行する・**「ON 成功 → OFF で一部失敗 → ON」で ON を設定し直す**）・簡易表示でも追従・ステータス欄の文言との一致。
  - 画像の読込（使える画像が 0 枚 → 印だけ・正方形でない / 対象外の大きさ / 読めないものは使わない・フォルダが無い）。
  - 子窓（§5 で案 B を採るときだけ: 開いている子窓・入れ子への設定）。
  - `StatusIcon` を持たない App（既存の SimpleNamespace のフェイク）で `update_status` が壊れないこと。

## §9 確認事項（ユーザー判断）

1. **タスクバーへの反映の方式（§3.3）・開いている子窓の方式（§5）**: task_01 の試作の結果で決め、本書へ反映してユーザー確認する。
   （旧 §9-1〜3 = ダイアログ中の赤・画像のサイズ・用意の時期は 2026-10-31 に確定し §2 へ移した）

## §10 受け入れ条件（ドラフト）

1. フックを開始 / 停止 / キーマップ一時停止 / 再開すると、タスクバーのアイコンの印がステータス欄と同じ状態に変わる。詳細表示・簡易表示のどちらでも（§3）。
2. 印は ON = 緑●・OFF = 赤■・一時停止 = 黄‖ で、100% 表示のタスクバーで形が見分けられる（§4.3・実機目視）。
3. 開いている子窓・後から開く子窓も同じアイコンになる（§5・実機目視）。
4. 使える画像が 0 枚のときは印だけのアイコンで動き、エラーにならない。対象外・読めない画像は使わずログに残す（§4.1・§4.2）。
5. 反映の失敗でステータス欄の更新が止まらない（§3.2）。
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
  `trigger_panel_controller.py`（`update_status`）・`app.py`（部品の作成と初回設定）・（§3.3 案 B なら）`infrastructure/win32_window.py`。
- テスト: `tests/test_badge_shapes.py`（新規）・`tests/test_status_text.py` 相当（判定）・`tests_ui/`（新規 1 ファイル）・`tests/test_help_content.py` / `tests/test_third_party.py`（import の更新）。
- ライセンス: 土台の画像はユーザーの著作物（アプリと同じ GPL v3 の扱い）。ライセンスの窓の同梱物の一覧（第三者）には足さない。

## 関連

- [idea_55](../backlog/idea_55_taskbar_status_icon.md)
- phase 58（ステータス欄の 3 状態）: [decisions_archive/58](../../.claude_data/state/decisions_archive/58_window_size_fit.md)
- phase 70（`bundled_paths.py`）: [暫定 53](53_help_window.md)
- 正本 `features.md` §4.5 / §4.6
