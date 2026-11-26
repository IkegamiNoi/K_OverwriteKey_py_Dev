# 暫定仕様 62: スクロールのアクションの向きの反転（scroll_direction_setting）

> 状態: **凍結（2026-11-26・正本反映済）**。正本（`data_schema.md` §5.4・§5.11.10 / `features.md` §4.6「スクロールの向き」・§4.8「メニューの処理」/ `codebase_map.md`）が最新。本書は経緯記録として凍結（v0.4 でユーザー確定・起票時 deep-reviewer・Codex 敵対的レビュー〔起票時・完了判定前〕を反映）。
> 起票元: [idea_58](../backlog/idea_58_scroll_direction_setting.md)（2026-11-15 phase 75 task_11a の Mac 実機目視でユーザーが要望）。
> 番号対応: phase 82 / 暫定 62 / decisions 82。

---

## §1 目的 / 背景

出力シーケンスの `mouse_scroll` の行が送る向きを、**アプリの設定で縦・横それぞれ反転**できるようにする。
Mac の「ナチュラルなスクロール」のように OS 側で向きを入れ替えて使う人は、アプリが送るスクロールと手で回したホイールの向きが逆に感じられる（アプリが送る事象は OS の入れ替えの影響を受けない）。

### 現状監査（2026-11-26）

- 向きと量 → 符号付きの値: `keyseq/domain/mouse_scroll.py:85` `scroll_deltas`（up・right = 正 / down・left = 負。ノッチ = ±120 を個数分・生の値 = 120 ずつ + 端数）。
- 実行: `keyseq/application/action_executor.py:330` `_execute_mouse_scroll` → `scroll_deltas` → `input_gateway.scroll_mouse(vertical, deltas, position)`（`keyseq/infrastructure/input_gateway.py:35`）→ 両 OS の backend。Windows（`os_backend/windows/mouse_backend.py`）は符号をそのまま `mouseData` へ、macOS（`os_backend/macos/mouse_backend.py:48-55`）は縦はそのまま・**横は符号を入れ替えて**（`-amount`・Quartz の第 2 軸は負 = 右）渡す。
- アプリが OS へスクロールを送る経路はこの 1 本のみ（キーマップ・グリッド・key_hold からの別経路なし。監査の申告・`grep scroll_mouse` で確認）。
- `ActionExecutor.__init__`（`action_executor.py:70`）はグローバル設定を受ける口を持たない。値は `get_counter` 等と同じく**呼び出し時に読む callable** で注入するのが前例（`app.py:217`・組み立ては `app.py:206`）。`_execute_mouse_scroll` の呼び出しはフックの受け渡し（`app.py:307` `create_hook_dispatcher`・UI へ渡すかは OS の `queued_hook_dispatch` で変わる）と Tk の `after` を通る。UI スレッド以外から呼ばれないとは言い切れないため、スレッドを問わず安全な形にする（§4）。
- config.json のグローバル設定: 読込 = `load_startup_settings`（`app.py:145`・未知のキーも残す）/ 書込 = `StartupIo.write_startup`（`presentation/controllers/config_io/startup_io.py:43`・読み込んだ dict に差分を重ねて書く・失敗時は messagebox を出して False）。dict の値ごとの判定の前例 = `compact_header_view`（正本 `data_schema.md` §5.4）。
- 設定メニュー: `keyseq/presentation/views/menu_bar.py:27-63`。チェック項目の前例 =「物理キー名を表示」（構成セット側の設定・未保存の印を立てる）、ラジオの前例 = フォントサイズ・Language。macOS ではモーダルを開き得るメニュー処理を `app.menu_commands.defer` で `after(0)` の待ち行列へ遅らせる（`views/menu_command_queue.py:16-23`・正本 `features.md` §4.8「メニューの処理」）。
- 正本: `data_schema.md` §5.4（config.json）・§5.11.10（mouse_scroll）/ `features.md` §4.6（設定メニューの各項目・「言語」は 1007 行付近）/ `ui_terms.md`（`mouse_scroll` = マウスのスクロール / Mouse scroll）。

## §2 確定事項（ユーザー 2026-11-26）

- **方式 = アプリのグローバル設定（config.json）**。アクションごとの指定（idea の案 B）・Mac の OS 設定への自動追従（案 C）は採らない。
- **縦と横を別々に**反転できる。
- **既定は反転なし**（キーが無い既存の config.json は今までどおりの向き）。
- 反転は application で符号を入れ替える（backend・OS の設定は変えない）。
- **メニュー = 設定 > サブメニュー「スクロールの向き」（`Scroll direction`）> チェック「縦を反転」（`Invert vertical`）/「横を反転」（`Invert horizontal`）**。「物理キー名を表示」の下の区切りの後、「フォントサイズ」の上に置く。
- **ヘルプ本文**の「主要機能」のマウスのスクロールの説明に、向きは設定メニューの「スクロールの向き」で反転できる旨の 1 文（Mac のナチュラルなスクロールの例を添える）を ja / en で足す。
- **mouse_scroll の編集ダイアログ・一覧には反転中であることを出さない**（JSON・ダイアログ・一覧は書いた向きを表し、反転は送るときだけの設定）。

## §3 データ（config.json）

- 新キー **`scroll_invert`** = `{"vertical": <bool>, "horizontal": <bool>}`（true = 反転）。
- **値ごとに判定**し、bool 以外・欠けていればその値は false。値が dict でなければ両方 false（エラー表示なし・ファイルは書き換えない）。**未知のキーは保持しない**（`compact_header_view` と同じ）。
- 書き込みは起動設定の書き出し経路（`write_startup`）を通す。書き込み契機 = 設定メニューで縦か横を切り替えたとき。**常に `vertical` と `horizontal` の両方の今の値を書く**。
- 符号は 3 段に分けて扱う: ①アプリ内の符号（`scroll_deltas`・up・right = 正）→ ②設定による反転（§4）→ ③OS へ渡す値（backend が決める。macOS の横は②の結果の符号を入れ替えて Quartz へ渡す）。本書の「反転」は②だけを指し、①と③は変えない。例: right の行は反転 OFF で gateway へ正（macOS の Quartz の横には負）、反転 ON で gateway へ負（Quartz の横には正）。
- 「未知のキーは保持しない」は本設定を切り替えて書いたときに効く。他の設定の保存では読み込んだ `scroll_invert` を（不正な値でも）そのまま残す（`compact_header_view` と同じ）。
- 正規化は domain の純関数 1 つ（例 `coerce_scroll_invert(value) -> ScrollInvert`）に置き、presentation の読込と保存の両方から使う。前例の `parse_compact_header_view` は presentation（`presentation/compact_header_view.py:6`）だが、本設定は application が型 `ScrollInvert` を使うため domain に置く。

## §4 実行（反転の適用）

- `_execute_mouse_scroll` で `scroll_deltas` の結果に反転を当ててから `scroll_mouse` へ渡す。縦（up / down）の行には `vertical`、横（left / right）の行には `horizontal` を見る。反転 = 全事象の符号を入れ替える（量・分け方・座標は変えない）。
- 反転は domain の純関数（例 `apply_scroll_invert(vertical, deltas, invert)`）にし、executor はそれを呼ぶだけにする。
- `ActionExecutor` は任意の引数 `get_scroll_invert: Callable[[], ScrollInvert] | None = None` を受ける（None = 反転なし）。**行を実行するたびに読む**。反転が効くのは**保存が成功して実行に使う値を差し替えた後に実行する `mouse_scroll` の行から**（実行中の出力シーケンスの途中でも）。差し替えより先に実行された行は前の向きのまま（macOS では保存がメニューの待ち行列で遅れるため、チェックを切り替えた後でも前の向きで送る行があり得る・受容）。終了が確定して待ち行列ごと捨てられた切り替えは保存も反映もしない。
- 値の持ち主は presentation（app）。メニューの BooleanVar は UI スレッド専用で、executor は別スレッドからも呼ばれるため、**executor へは Tk の変数ではなく、不変の値を返す callable** を渡す。`ScrollInvert` は frozen dataclass とし、差し替えは UI スレッドで**属性への 1 回の代入**で行う（フィールドを個別に書き換えない）。
- callable は `_execute_mouse_scroll` の try の中で呼び、例外は送信の例外と同じ扱い（止まる系）にする。
- 変わらないもの: JSON の `direction`・ダイアログの向きの選択肢・一覧の表示（`[scroll] 下3` は書いたとおりの向き）・検証と実行時エラー・send guard の対象外であること。

## §5 UI（設定メニュー）

- 設定メニューに **サブメニュー「スクロールの向き」** を置き、中に **チェック項目「縦を反転」「横を反転」** の 2 つ（§2）。
- チェックは config.json に保存された値に付ける。切り替えると `scroll_invert` を保存し、成功したら実行に使う値を差し替える。
  - **保存は `app.menu_commands.defer` を通す**（失敗の messagebox がモーダルのため。macOS では遅れて実行され、Windows では即時）。待ちの間もチェックは選んだ値を示す。
  - 書く値 = **保存を実行した時点のチェック 2 つの値**（両方書く）。それが保存済みの値（`_startup_settings` の `scroll_invert` を正規化したもの）と同じなら書かない。
  - **保存に失敗したら 2 つのチェックを保存済みの値へ戻し、実行に使う値も変えない**（Language と同じ扱い）。
  - 失敗の知らせは既存の起動設定の保存失敗と同じ経路（`write_startup` の messagebox）で出す。その間はフックを止めるため、**フックが動いていれば実行中の出力シーケンス・待ち・押したままの入力は止まり、離される**（他の設定の保存失敗と同じ・受容）。
- 反映は保存の成功の直後（再起動の案内は出さない）。
- **構成セットを未保存にしない**（グローバル設定のため）。新規作成・読込・Import・サンプル設定に戻す でも値は変わらない。
- メニューはフォントの変更で作り直される（`app.py:582`）ため、BooleanVar は `ui_vars` に置く。
- 文言は `ja.json` / `en.json` の両方に `menu.settings.scroll_direction*` のキーで足す（英語は `ui_terms.md` の E1〜E7 に従う）。

## §6 確認事項

なし（v0.3 で §2 へ確定済み）。

## §7 受け入れ条件（ドラフト）

1. `scroll_invert` が無い・dict でないとき、縦横とも反転なしで送る。片方だけ欠ける・bool でないときは、その向きだけ反転なしで、もう片方は保存値に従う（§3）。config.json が読めないときは今までどおりの読込失敗の警告を出し、縦横とも反転なし（§3）。
2. 縦だけ ON で up / down の符号だけが入れ替わり、left / right は変わらない。横だけ ON はその逆。両方 ON で両方（§4）。
3. ノッチ・生の値のどちらでも、量と分け方（120 ずつ + 端数）は変わらない（§4）。
4. 設定メニューで切り替えると config.json に両方の値が書かれ、再起動後もチェックと向きが保たれる（§3・§5）。
5. 保存に失敗するとチェックが戻り、送る向きも変わらない。フックが動いていれば止まり、実行中の出力シーケンスも止まる（§5）。macOS でメニューから切り替えても固まらず、失敗の知らせが出てチェックが戻る（§5）。
5a. 切り替えても構成セットは未保存にならない。新規作成・読込でも値は変わらない（§5）。
6. 反転は保存が成功して値を差し替えた後に実行する `mouse_scroll` の行から効き、それより前に実行された行は前の向きのまま（§4）。
7. 一覧・ダイアログ・JSON の `direction` は変わらない（§4）。
7a. ヘルプの「主要機能」のマウスのスクロールの説明に反転の 1 文がある（ja / en・§2）。
8. 実機（Windows・macOS）で、反転 ON のとき実際のスクロールの向きが入れ替わる（ユーザー目視。macOS の backend は横の符号を入れ替えて送るため、実際の向きの確認はこれが唯一）。

## §8 スコープ外（本フェーズでやらない）

- アクションごとの反転指定（idea の案 B）・Mac の OS の設定（`com.apple.swipescrolldirection`）の読み取り / 自動追従（案 C）。
- **多重起動で config.json の設定が上書きされる問題**（同じ設定フォルダで 2 つ起動すると、片方の保存がもう片方の起動時点の内容で全体を書き直し、保存済みの値が消える。本設定に限らず config.json の全設定に既存の問題・Codex 敵対的レビュー指摘 1・ユーザー判断 2026-11-26 でスコープ外）→ [idea_70](../backlog/idea_70_config_overwrite_on_multiple_instances.md)。
- OS の設定そのものの変更。アプリ内の画面（一覧・枠）のマウスホイールの向き（Tk の既定の動きのまま）。

## §9 正本反映（フェーズ末昇格・予定）

- 正本: `data_schema.md` §5.4（`scroll_invert` の項・書き込み契機の列挙に追加）・§5.11.10（実行③に反転を足す。符号を「アプリ内の符号 → 設定による反転 → OS へ渡す値」に分けて書き、macOS の横は OS へ渡すときに符号を入れ替えることを明記）/ `features.md` §4.6（設定メニューの「スクロールの向き」の項）・§4.8「メニューの処理」（遅らせる処理の列挙に本設定の保存を足す）/ `ui_terms.md`（用語を足す場合）/ `codebase_map.md`（domain の関数・executor の引数・メニュー）。
- 実装: `keyseq/domain/mouse_scroll.py`・`keyseq/application/action_executor.py`・`keyseq/presentation/app.py`・`keyseq/presentation/views/menu_bar.py`・`keyseq/presentation/ui_vars.py`（変数を置く場合）・`keyseq/shared/i18n/locales/ja.json`・`en.json`・ヘルプ本文 `help_ja.json`・`help_en.json`。
- テスト: `tests/test_mouse_scroll.py`（正規化・反転の純関数）・`tests/test_action_executor_mouse_scroll.py`（反転の適用・None のとき不変）・`tests_ui/`（メニューの切替と保存・保存失敗で戻る）。**既存の期待値を変えるテスト** = `tests/test_menu_bar_deferral.py`（:32 の `ui_vars` に新しい変数 2 つ・:46,50 の checkbutton の数 1 → 3・:49,51 の遅らせた処理の数 `22 + 言語数` → 新しいチェック 2 つの分だけ増える）。mouse_scroll の既存テストは既定が反転なしのため変わらない見込み。

## 関連

- [idea_58](../backlog/idea_58_scroll_direction_setting.md) / phase 67（mouse_scroll の導入・[decisions_archive/67](../../.claude_data/state/decisions_archive/67_mouse_scroll_action.md)）/ phase 75 task_11a（横の符号の修正）/ phase 72（Language の設定・保存失敗の扱いの前例）。
