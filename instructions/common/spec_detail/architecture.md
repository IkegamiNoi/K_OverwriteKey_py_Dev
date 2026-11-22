## 3. アーキテクチャ方針

### 3.1 採用アーキテクチャ

本ツールはオニオンアーキテクチャを採用する（パッケージは `keyseq/` 配下）。

### 3.2 依存ルール

* 外側の層は内側の層に依存してよい
* 内側の層は外側の層に依存してはならない
* domain 層は tkinter / keyboard / pyobjc 等の UI・フック・OS の実装に依存してはならない
* infrastructure 層は domain / application のインターフェースに従って実装する
* presentation 層は application 層を通じて操作を実行する
* **presentation は `application/config_service/` の内部モジュールを直接参照しない**。
  公開面は **`ConfigService` の公開 API（委譲メソッドおよび公開クラス定数 `INTERNAL_*` 等。
  `codebase_map.md`）と `application/config_service/contracts.py`** とする
  * `contracts.py` は**判定名・理由コード・結果型（データクラス）の唯一の定義場所**。
    表示文言の純関数（`reference_cleanup_text.py` / `orphan_sweep_text.py` /
    `quarantine_manage_text.py`）と対応する `config_io/` の IO クラスは、ここから import する
  * **実装モジュール（`orphan_scan` / `quarantine` 等）の直参照は定数・型・関数のいずれも不可**
  * `contracts.py` は **`config_service` 内の他モジュールを import しない**
    （依存は実装モジュール → `contracts` の一方向。stdlib は可）
* **application は presentation（`app`）を参照しない**。走査対象・保護対象などの入力は
  **引数で明示的に受け取る**
* **`keyseq/shared/` は全層（presentation / application / domain / infrastructure）から依存してよい**（Global Shared・phase 72）。
  shared は他の層に依存せず、**標準ライブラリだけ**を使う。今あるのは画面の文言の多言語対応 `shared/i18n/`（`codebase_map.md`）
  * 内側の層で作られて画面に出る文言も、その層で `shared.i18n.tr` を使って作る（言語は実行中に変わらないので、表示の時点で訳すのと結果は同じ）

### 3.3 各層の責務

#### domain（`keyseq/domain`）

* トリガー
* アクション
* 出力シーケンスのロジック

#### application（`keyseq/application`）

* ユースケース
* 実行制御（出力シーケンス実行・run_to_end）

#### infrastructure（`keyseq/infrastructure`）

* OS ごとの入力・窓・IME・起動の実装（`os_backend/`・下の §3.6）
* JSON 入出力（ConfigService）

#### presentation（`keyseq/presentation`）

* UI（tkinter）: FullView / CompactView / KeyboardWindow / ダイアログ
* イベント処理・各コントローラ
* ヘルプ・ライセンスの表示は `keyseq/presentation/help/` に置く。`HelpWindowController` はヘルプ窓を、`LicenseWindowController` はライセンス窓をそれぞれ管理し、ヘルプ本文・絞り込み・同梱ライセンスの読込もこのパッケージ内で行う。バージョン情報の表示は、層の外の `keyseq/__init__.py` が公開する `__version__` を参照する。
* 同梱データ（LICENSE・ヘルプ本文・ライセンス全文・アイコンの土台の画像）の位置は `keyseq/presentation/bundled_paths.py` の `bundled_root()` に集約する（exe 化時の変更点を 1 か所に・phase 71 で `help/` から昇格）。ビルド後（PyInstaller・`sys.frozen`）は `sys._MEIPASS`（Windows = exe の隣の `_internal`・Mac = `.app` の `Contents/Frameworks`）、開発実行はリポジトリの直下を返す（phase 75）。
* タスクバーのアイコン（フックの状態の印）は `keyseq/presentation/status_icon/` に置く。印の形の計算は Tk に依存しない純関数（`badge_shapes`）、画像の合成と窓への設定は `StatusIcon`。AppUserModelID の設定（Windows のみ）は backend の `AppIdentity.apply_process_identity` で、エントリーポイント `main.py` から呼ぶ（最初の窓を作る前に 1 回だけ設定するため。Mac は何もしない・phase 75）。

### 3.4 UI スレッド

* UI 更新は必ず UI スレッドで行う（`after()` を使用）
* フック処理は UI と分離する
* file_line のファイル読込はワーカー（デーモンスレッド）で行う。ワーカーは Tk を呼ばず、共有状態は `FileLineLoader` の 1 つのロックの下だけ。結果は UI スレッドの確認タイマー（`after`）で受け取る（phase 38・`features.md` §4.2.7）

### 3.5 実装状態の参照先

クラス構成・各コントローラの責務分担の現状は
`instructions/common/codebase_map.md` を正とする。

---

### 3.6 OS 境界（phase 75）

Windows と macOS（Apple Silicon）で動かすため、OS に依存する実装を `keyseq/infrastructure/os_backend/` に閉じる。

* 配置: `os_backend/__init__.py`（`get_backend()`）・`contracts.py`（Protocol と `Capabilities` / `OsBackend`）・`windows/`（Win32 と `keyboard`）・`macos/`（`pyobjc`・CGEventTap）・OS 共通の補助（`app_relaunch.py`・`pyautogui_mouse.py`）
* **`sys.platform` の分岐は `keyseq/` 内では `get_backend()` の 1 か所だけ**。Win32 と `keyboard` の import は `windows/`、`pyobjc` は `macos/` に閉じ、選ばれた OS でだけ import する（AST の検査テストで守る）。テストの `skipUnless` は対象外。Tk の差は `tk windowingsystem`（presentation の `tk_platform.py`）で判定する
* presentation は `os_backend` の公開面だけを参照する。domain / application は OS を判定しない（OS で変わる既定データ・語彙は backend から注入する）
* 境界（Protocol）: `KeyboardBackend`（フック・送信・キー名の検証と解決・リピート間隔・権限）/ `MouseBackend` / `WindowBackend`（前面の判定・モニタ一覧・クリック透過・重なり順・物理状態・最前面とモーダル）/ `TkKeyTranslator`（Tk のキーの解釈）/ `ImeBackend` / `AppIdentity`（起動時の OS 固有設定・設定のルート・再起動）
  * `InputGateway` の公開メソッドは維持し、application から見た契約を変えない
  * 窓を受ける API は Tk の窓オブジェクトを引数にする（HWND / NSWindow を Protocol に出さない）。モニタの座標は左上原点・Tk と同じ座標系
  * `Capabilities` は OS ごとに無い機能を宣言する（クリック透過・窓の重なり順は両 OS とも True。macOS は `status_icon` / `ime_control` を False と宣言しているが、今はどこからも参照されない。無効化の UI は、動かない機能が見つかったときに作る）
  * `OsBackend` の項目: `default_profile`（既定データ・`data_schema.md`）・`queued_hook_dispatch`（フックから UI への受け渡しの方式・`key_input.md` §7.9）・`platform_key`（`win32` / `darwin`。ライセンスの表の OS 列に使う）
* **設定のルート**（`AppIdentity.app_data_root`）: 開発実行はリポジトリの直下・ビルド後は Windows = exe のあるフォルダ・Mac = `~/Library/Application Support/keyseq/`。どちらもその下に `config/` を置く（相対の構造を OS で揃える）
  * レイアウトの見本は同梱物（`bundled_root()` の `config/user/keylayout/`）で、設定のルートに `config/user/keylayout/` のフォルダが**無いときだけ**全部コピーする（一時フォルダへ全件コピーしてから改名・失敗したら一時フォルダを消す・上書きしない）。消した見本は戻さない・更新で増えた見本は既にフォルダがある利用者には届かない。開発実行では同梱物と設定のルートが同じなので何もしない
* **再起動**（`AppIdentity.relaunch`）: ビルド後は argv[0] の重複を除いて起動し直す（Mac の `.app` も `open -n` は使わない・実測で 1 つだけ起き直る）
* ビルドは PyInstaller の onedir（各 OS で実行・クロスビルドしない）。定義と手順は `packaging/`（`packaging/README.md`）。配布物の中身は `features.md` §4.6「バージョン情報・ライセンス」
