## 6. 非機能要件（安全設計）

* フック暴走を起こさないこと（最優先）
* suppress の副作用を考慮すること
* keyboard の例外は必ず吸収すること
* UI スレッドをブロックしないこと（UI 更新は `after()` を使用）
* JSON の後方互換を必ず維持すること
* キーボード操作の応答性を優先すること
* オニオンアーキテクチャの依存ルールを守ること（domain は UI・フック実装に非依存）

### 画面の枠の座標系（phase 56）

`features.md` §4.7 の座標と Win32 の扱い。phase 56 task_01 の実測（VirtualBox ゲスト・2 画面〔主の上 = 負の y〕・拡大率 100%）で確定した。

* **DPI の状態は変えない**: プロセスは pyautogui の import 時の `SetProcessDPIAware()` でシステム DPI 対応（SYSTEM_AWARE）になっている。その状態の座標を
  モニタの列挙・枠の窓の位置・カーソル移動・クリックで共通に使う（100% では物理座標と同じ。負の座標の画面を含めて一致を実測）。アプリ全体の Per-Monitor 対応はしない
* **拡大率の混在する構成は検証していない**（受容）。主モニタと拡大率の違う画面では枠の線がぼやける・ずれる可能性がある
* モニタは Win32 `EnumDisplayMonitors` + `GetMonitorInfoW` の `rcMonitor`（作業領域ではない）で列挙し、識別子は矩形から作る（`data_schema.md` §5.6.1）。
  `szDevice`（`\\.\DISPLAY2` 等）は配置を変えても変わらず識別に使えないため使わない。Tk の `winfo_screenwidth/height` は主モニタだけなので使わない
* カーソル移動・クリックは pyautogui（`_pause=False`・FAILSAFE を一時的に外す）。既定の `PAUSE` は 1 回ごとに約 100ms UI スレッドを止めるため使わない（実測: `_pause=False` で 0.1〜5ms・クリックはフック動作中に 2〜36ms）
* 枠の窓は、透過色（`-transparentcolor`）の後、表示前に Tk のラッパーの HWND（`GetParent(winfo_id())`）へ `WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW` を足し、
  クリック素通し・フォーカスを取らない。**自アプリの窓が前面のときに `tk.Toplevel` を作るとその窓が前面になる**（実測）ため、窓は最初に表示するときに作る
* Win32 の呼び出しは `infrastructure/win32_window.py` に置き、presentation から ctypes を直接呼ばない。LastError は `use_last_error=True` の user32 で読む
* 失敗（窓の生成・列挙・カーソル移動 / クリック）では枠を畳んで操作キーの suppress をやめ、フックは止めない（窓が無いのにキーを握りつぶし続けない・`features.md` §4.7）

---
