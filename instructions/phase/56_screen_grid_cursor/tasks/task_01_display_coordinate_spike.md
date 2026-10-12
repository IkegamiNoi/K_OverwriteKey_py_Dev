# task_01_display_coordinate_spike

## 目的

枠の機能の座標系と、カーソル移動・クリックの手段を実機の測定で確定する（暫定 40 §6・§4.5・§7）。
**製品コードは変えない（スパイク）**。測定用のプローブは scratchpad に置く使い捨てのスクリプトで、コミットしない。
結果は本書の「結果」節と `decisions.md` の phase 56 節に記録し、task_03・task_04 の前提にする。
既定案（プロセスの DPI の状態は今のまま）で §6 の 1〜3 が一致しなければ**止めてユーザーへ §6 の (a)〜(c) を確認**する。

## 対象範囲（scratchpad のプローブ + 本書・decisions.md への記録のみ）

### プローブ（`<scratchpad>/grid_probe.py`・メインセッションが用意・コミットしない）

- **本番の起動経路を再現**: 最初に `import keyseq.presentation.app`（`main.py` と同じ import の副作用 = pyautogui の `SetProcessDPIAware`）→ `tk.Tk()` を作ってから測る。`App` 自体は起動しない（フック・設定を読まない）
- 測定結果は標準出力と `<scratchpad>/grid_probe.log` に書く
- 測ること（§6 の番号）:
  0. `GetThreadDpiAwarenessContext` の値（`AreDpiAwarenessContextsEqual` で UNAWARE / SYSTEM_AWARE / PER_MONITOR(V2) と照合）と `GetDpiForSystem`。比較用に import 前の値も出す
  1. `EnumDisplayMonitors` + `GetMonitorInfoW`（`MONITORINFOEXW`）の各画面の `rcMonitor`・`rcWork`・`szDevice`・主かどうか。比較用に Tk の `winfo_screenwidth/height`・`winfo_vrootx/y/width/height`
  2. 各画面の `rcMonitor` に、枠なし（`overrideredirect`）・最前面（`-topmost`）・背景を透過色（`-transparentcolor`）にした窓を置き、外周の線と、決まった点（四隅から 10px 内側・中心）に十字を描く。置いた後の `GetWindowRect`（ラッパーの HWND = `GetParent(winfo_id())`）を矩形と照合する
  3. 各画面の決まった点へ、(i) pyautogui の `moveTo` / `click`、(ii) Win32 の `SetCursorPos` + `SendInput`（左クリック）でカーソルを運ぶ。移動後の `GetCursorPos` を目標と照合する。クリックは、枠の窓の下に置いたクリック受け用の普通の窓（Tk の `Toplevel`・その画面いっぱい）が受けた `x_root/y_root` を目標と照合する（**負の y のモニター 2 を含む**）
  4. 枠の窓に、表示前に拡張スタイル `WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW` をラッパーの HWND へ付ける。窓を出す前後・別の画面へ移す前後で `GetForegroundWindow` が変わらないこと、3 のクリックが枠の窓を素通りして受け用の窓へ届くことを確かめる
  5. 3 の (i)・(ii) を UI スレッドで呼んだときの所要時間（`time.perf_counter`）。pyautogui は `PAUSE` の既定値のままと、`_pause=False` 相当で比べる
- 構成の変化（§6 末尾・§4.1）: プローブの窓のボタン（または一定間隔）で画面の列挙をやり直し、前回との差（識別子 = `szDevice` + 矩形）を出す。ユーザーが測定中に表示設定で配置を変える・モニター 2 を無効にする
- 連打（§6 末尾・§4.4）: `keyboard` で Space・Enter を suppress してフックし、`after(0, ...)` で UI スレッドへ数を送る。ユーザーがメモ帳を前面にして素早く連打し、メモ帳へ文字が漏れないこと・フックが受けた数と UI スレッドが処理した数が一致することを確かめる（プローブの終了時にフックを必ず外す）

### 記録

- 本書の末尾に「結果」節を足し、0〜5・構成の変化・連打の実測値と判定を書く
- 確定すること: (1) 既定案を採るか（採らなければユーザー判断）/ (2) カーソル移動・クリックの手段（pyautogui か Win32 か）と、pyautogui なら `PAUSE`・FAILSAFE の扱い / (3) 暫定 40 §3 の識別子（`<幅>x<高さ><左><上>`）の元になる座標系（物理か論理か）と、構成の変化をその識別子で検出できるか/ (4) 非アクティブ化・クリック素通しの拡張スタイルの組み合わせ
- `.claude_data/state/decisions.md` の phase 56 節へ 1〜数行で判断を記録する

### 設計メモ / 制約

- プローブは Win32 を ctypes で直接呼んでよい（使い捨てのため）。製品側では `infrastructure/win32_window.py` に置く（task_04）
- 既存の `_send_mouse_button`（`input_gateway.py:344-355`）は FAILSAFE を一時的に外して `moveTo` している。pyautogui を採るならこれと同じ扱いが前提（§4.5）
- 拡大率の混在は検証しない（§6・ユーザー判断）

## 読むファイル

- `instructions/history/40_screen_grid_cursor.md` §1「現状監査」・§4.1・§4.4・§4.5・§6・§7
- `main.py`（import 順）
- `keyseq/infrastructure/input_gateway.py:1-20`（import）・`:330-370`（クリックとマウスボタン）
- `.venv/Lib/site-packages/pyautogui/_pyautogui_win.py:10-25`（DPI の宣言）
- `keyseq/infrastructure/win32_window.py:1-60`（ctypes の呼び方の手本）

## 含まない

- 製品コードの変更（モニタの列挙・カーソル移動の infrastructure・枠の窓 = task_04 / 状態機械と振り分け = task_03 / `grid` の domain と JSON = task_02）
- 拡大率の混在する構成の検証（§6・受容）
- 既定案が成り立たない場合の (a)〜(c) の実装（ユーザー判断の後に別途）

## 確認

- プローブを `..\..\..\.venv\Scripts\python.exe <scratchpad>/grid_probe.py` で起動できる（素の `python` は使わない）
- 0・1・5 の数値と、2〜4 の照合結果（一致 / 不一致と差の px）がログに残っている
- ユーザーの目視: 両方の画面で外周の線が画面の端にぴったり重なる・十字の中心にカーソルが来る・クリックが受け用の窓へ届く・窓が出てもフォーカスが移らない
- 構成の変化: 配置の変更・モニター 2 の無効化の後に列挙をやり直すと、差が識別子で検出できる
- 連打: メモ帳へ漏れない・数が一致する
- プローブの終了後に `keyboard` のフックが残っていない（キー入力が普段どおり）

## 完了条件

- 上記確認 pass・本書の「結果」節と decisions.md の記録・**reviewer 採用**（対象 = 「結果」節の判定と記録した判断が §6 の既定案・確かめることを満たしているか）
- 実機目視は**本タスクで実施**（ユーザー）
- 既定案が成り立たない場合はここで止め、ユーザーの判断を得るまで task_02 以降へ進まない

## 結果（2026-10-12・VirtualBox ゲスト・ユーザーの実機で測定と目視）

測定環境: モニター 1 = 主 `\.\DISPLAY1` (0,0)-(1920,966)・作業領域 (0,0)-(1920,918) / モニター 2 = `\.\DISPLAY2` (0,-768)-(1024,0)・作業領域 (0,-768)-(1024,-48)・両方 96 dpi（100%）。
プローブ = `<scratchpad>/grid_probe.py`（コミットしない）。目視はユーザーが全項目「問題なし」と報告。

| 項目 | 実測 | 判定 |
|---|---|---|
| 0 DPI | import 前 UNAWARE → `keyseq.presentation.app` の import 後・`tk.Tk()` の後 = SYSTEM_AWARE / システム 96 dpi | 既定案の前提どおり |
| 1 列挙 | `EnumDisplayMonitors` + `GetMonitorInfoW` が上の矩形を返す。Tk の `winfo_screenwidth/height` は主モニタだけ（1920×966）・`winfo_vroot*` は外接矩形 (0,-768) 1920×1734 | 列挙は Win32 で行う |
| 2 窓の位置 | 枠なし・最前面・透過色の窓をモニタの矩形へ置くと `GetWindowRect` が両画面とも矩形と完全一致（`geometry` の `+0+-768` で負の y も可）。外周の線は画面の端にぴったり（目視） | OK |
| 3 移動・クリック | 2 画面 × 5 点（四隅から 10px 内側・中心）で、pyautogui `moveTo` / Win32 `SetCursorPos` とも `GetCursorPos` が目標と完全一致（負の y を含む）。クリックも pyautogui `click` / Win32 `SetCursorPos` + `SendInput` とも受け用の窓の `x_root/y_root` が目標と一致 | OK |
| 4 フォーカス・素通し | 窓の作成 → 隠したまま拡張スタイル付与（下記）→ 表示 → 別の画面へ移す、の間ずっとメモ帳が前面のまま（作り直しを含む）。クリックは枠の窓を素通りして下の窓へ届き、枠の窓はクリックを 1 度も受けていない | OK |
| 5 所要時間（UI スレッド） | pyautogui `moveTo` 既定 = 約 101ms（`PAUSE`）/ `_pause=False` = 0.2〜4.7ms / `SetCursorPos` = 0.1〜4.9ms。クリックは pyautogui（`_pause=False`）・Win32 とも 3〜42ms | `PAUSE` の既定は不可。他は可（`keyboard` のフックを入れない状態の値。フック動作中の値は task_04 の実装後に一度見る） |
| 構成の変化 | 2 秒ごとの再列挙で、モニター 2 の無効化・有効化・右への移動・上への移動（(895,-768)-(1919,0)）をすべて検出。配置の変更では `szDevice` は同じで矩形だけ変わる | 矩形由来の §3 の識別子で §4.1 のとおり「見つからない」と判定できる |
| 連打 | Space / Enter を suppress してフックし `after(0)` で UI へ送ると、169 回で フック = UI = 169・メモ帳へ漏れなし（目視） | OK |
| 終了後のフック | プローブの終了（`unhook_all`）後にキー入力が普段どおり（ユーザー確認） | OK |

補足（判定に影響しない）:
- 1 回目のクリックテストでモニター 2 の (10,-758) だけ 2 方式とも届かなかったのは、前面へ来たメモ帳が受け用の窓に重なったため（移動テストでは同じ点が一致・2 回目のクリックテストでは届いている）。プローブの受け用の窓が普通の z 順だったことによる
- 自アプリの窓が前面のときは、`tk.Toplevel` を作った時点で（隠したままでも）その窓が前面になった。別のアプリが前面のときは前面を取らない。製品では自アプリの窓が前面の場面で枠を作ると操作窓からフォーカスが外れうる（task_04 で枠の窓を作る時機に注意）

### 確定したこと

1. **既定案を採る**（プロセスの DPI の状態は今のまま = SYSTEM_AWARE。座標は列挙の矩形をそのまま使う）。(a)〜(c) は不要
2. **カーソル移動・クリックの手段 = pyautogui**（ユーザー判断 2026-10-12）。Win32 も同等に正確・高速だったが、Mac 対応の予定があり pyautogui は macOS にも対応するため、既存のクリックのアクションと同じ経路にそろえる。条件（§4.5）: 呼び出しごとに `_pause=False`・FAILSAFE は既存の `_send_mouse_button`（`input_gateway.py:344-355`）と同じく一時的に外して戻す。置き場所 = `infrastructure/input_gateway.py`（モニタの列挙・窓の拡張スタイルは Win32 のまま `win32_window.py`）。右クリックは未測定のため task_04 の実機目視で確認
3. **画面の識別子は暫定 40 §3 のまま**（`rcMonitor` から作る `<幅>x<高さ><左><上>`。例 `1024x768+0-768`）。元の座標系 = SYSTEM_AWARE プロセスの仮想画面座標（100% では物理と同じ）。`szDevice` は配置の変更でも変わらず識別には使えないため、実行時の補助情報（主モニタ判定の `dwFlags & MONITORINFOF_PRIMARY` と並べて持つ）に留める
4. **枠の窓**: `overrideredirect(True)` ・ `-topmost` ・ 背景と Canvas を透過色にして `-transparentcolor`（Tk が `WS_EX_LAYERED` を付ける）→ `update_idletasks()` の後、隠したままラッパーの HWND（`GetParent(winfo_id())`・表示後も同じ）へ `WS_EX_TRANSPARENT | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW` を足す（`WS_EX_LAYERED` は既に付いている）。表示後もスタイルは保たれる（0x080800a8）。表示・移動は `geometry` + `deiconify`
