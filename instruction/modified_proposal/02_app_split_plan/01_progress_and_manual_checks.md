# 進捗と手動確認の申し送り

- 作成日: 2026-07-05 / 随時更新

## 重要: 手動GUI確認について
本作業は自動検証（compileall / unittest tests / unittest tests_ui / smoke）は全て実行・全緑を
確認しているが、計画書が「手動確認（必須）」とする対話的GUI操作（実際にキーを押す・
ダイアログのボタンを押す等）は、この実行環境では実施できない。
tests_ui による特性テストで観測可能な契約は固定済みだが、下記の手動項目は
**利用者による最終確認を推奨**する。

## 進捗
| 項目 | 状態 | コミット |
|---|---|---|
| 0 UI特性テスト | 完了 | test: app.py 分割前の UI 特性テストを追加した。 |
| S1 デッドコード削除 | 完了 | refactor: 未使用のデッドコード2件を削除した。 |
| S2 listbox_utils 抽出 | 完了 | refactor: Listbox選択ヘルパをlistbox_utilsへ抽出した。 |
| S3 ConfigPaths 抽出 | 完了 | refactor: パス解決をConfigPathsへ抽出した。 |
| S4 DirtyStateTracker 抽出 | 完了 | refactor: ダーティ状態管理をDirtyStateTrackerへ抽出した。 |
| S5 SingleKeyCaptureController 抽出 | 完了（自動検証のみ） | refactor: 停止/トグルキーのキャプチャをSingleKeyCaptureControllerへ統合した。 |
| S6 ConfigIoController 抽出 | 完了（自動検証＋保存/読込ラウンドトリップ確認） | refactor: 保存・読込フローをConfigIoControllerへ抽出した。 |
| S7 LayoutController 抽出 | 完了 | refactor: レイアウト管理とKeyboardWindow開閉をLayoutControllerへ抽出した。 |
| S8 KeymapPanelController 抽出 | 完了 | refactor: キーマップ管理パネルをKeymapPanelControllerへ抽出した。 |
| S9 TriggerPanelController 抽出 | 完了 | refactor: トリガー/シーケンスパネルをTriggerPanelControllerへ抽出した。 |
| S10 HookController 抽出 | 完了（自動検証のみ・手動6項目は要利用者確認） | refactor: フック制御をHookControllerへ抽出した。 |

## S6 手動確認項目（利用者確認推奨）
新規作成→トリガー追加→保存→読込→Export→Import→別名保存を一巡し、各操作後の
ステータスバー表示（未保存/保存済み・フラッシュ文言）が従来どおりであること。
※プログラムによる save→load ラウンドトリップは Claude 側で実行し正常を確認済み。

## S10 手動確認項目（必須・要利用者確認）
※この環境では実キー入力・グローバルフック挙動を観測できないため未実施。
`py main.py`（要 PYTHONPATH=. または通常起動）で確認前に必ず停止キーを設定した上で:
1. トリガー(例 hotkey: ctrl+c)登録→開始(ON)→トリガーキーで実行→停止(OFF)
2. フックON中に編集ダイアログを開く→トリガーキー無反応→閉じると自動復帰して発火
   （ダイアログのネストでも復帰は最後の1回のみ）
3. 停止キーでフックが止まる
4. トグルキーで通常トリガーの有効/無効が切替
5. suppress チェックON/OFFでキーが飲まれる/通る
6. text送信で送信文字により再トリガーしない（send guard）
※ tests_ui の test_hook_suspend_counter_nesting がサスペンドカウンタ契約を固定済み。

## S5 の手動確認項目（利用者にお願いしたい）
`py main.py` で起動し（※要 PYTHONPATH=. または通常起動）:
1. 「キー入力で取得」→ F9 押下 → 停止トリガー欄に `f9` が入り「未保存」になる
2. もう一度取得 → Esc → キャンセルされ値が変わらない
3. トグルキー側でも同様に取得できる
4. 停止キーに設定済みのキーをトグルキーへ取得しようとするとエラーダイアログが出る
5. 「クリア」で空に戻る

## S5 実装メモ
- 停止キー版・トグルキー版のほぼ同型2実装を `key_capture.py` の
  `SingleKeyCaptureController` 1実装へ統合した（計画書が唯一許容する統合）。
- 固有値（data_key / 各ウィジェット属性名 / label / 単キー例 / 競合チェック群）は
  コンストラクタ引数化。エラーメッセージ文言は元コードと完全一致を確認:
  - 単キーエラー: `{label}は単キーのみ対応です（例: {example}）。`
  - 競合エラー: `{label}が{相手名}と重複しています:\n{key}`
  - 不明キー: `不明なキー名です:\n{key}\n\n{e}`
- 相互排他（片方開始時にもう片方を止める）は App ファサード
  `_start_stop_key_capture` / `_start_toggle_key_capture` で実現。
  controller.stop() は `if not capturing: return` でガードするため元と等価。
- `_capturing_stop_key` / `_capturing_toggle_key` は App に読み取りプロパティを残置
  （app.py の `_is_menu_shortcut_enabled` 相当・`show_compact_view`・tests_ui が参照）。
- 統合で不要になった `App._normalize_tk_key_for_trigger` を削除。それに伴い
  app.py で未使用となった `from ...tk_keys import normalize_tk_keysym` も削除
  （挙動影響なしの直接的な死コード除去）。
