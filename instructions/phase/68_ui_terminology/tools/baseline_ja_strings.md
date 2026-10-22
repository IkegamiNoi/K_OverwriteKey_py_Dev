
## keyseq/application/action_executor.py

- L51: `{cause} / 解放エラー: `
- L61: `(値なし)`
- L62: `file_line 実行エラー（種類: file_line / 値: {values}）: {exc}`
- L65: ` / ラベル: {label.strip()}`
- L130: `text の送信に失敗しました: {exc}`
- L141: `file_line は読込の経路（begin_file_line / poll_file_line）で実行します`
- L162: `カウンター名が空です`
- L164: `カウンター取得コールバックが未設定です`
- L166: `ファイルパス解決コールバックが未設定です`
- L168: `ファイル読込の仕組みが未設定です`
- L186: `ファイル読込の仕組みが未設定です`
- L191: `ファイル読込に失敗しました`
- L193: `ファイル読込の結果が不正です`
- L208: `種類が不正です（hotkey / text / mouse_click / mouse_scroll / system / file_line / key_hold のいずれか）。種類: {type_text or '(なし)'}`
- L209: `(なし)`
- L213: ` / ラベル: {label.strip()}`
- L275: ` / 解放エラー: `
- L299: `key_hold の実行に失敗しました: {exc}`
- L306: ` ラベル: {label.strip()}`
- L311: `mouse_scroll の指定が不正です: {parsed}（{details}）`
- L322: `mouse_scroll の送信に失敗しました: {exc}（{details}）`
- L334: `キーマップ送信に失敗しました。⏎{type(e).__name__}: {e}`
- L334: `キー送信エラー`
- L343: `mouse_click の x/y が不正です（整数で指定してください）。`
- L343: `送信エラー`
- L364: `mouse_click の実行に失敗しました。⏎{type(e).__name__}: {e}`
- L364: `送信エラー`
- L371: `mouse_click の to_x/to_y が不正です（ドラッグの離す位置を整数で指定してください）。`
- L371: `送信エラー`

## keyseq/application/call_context.py

- L113: `呼び出し: {' > '.join((key for key in chain if key))}`
- L138: `呼び出しの深さが {sequence_control.MAX_CALL_DEPTH} を超えます`
- L141: `呼び出しが循環します（{key}）`
- L144: `呼び出し先のトリガーがありません（{key}）`
- L153: `戻す・先頭へのトリガーは呼び出せません`
- L155: `呼び出し先が指定されていません`
- L168: `呼び出し先に無限ループがあります`
- L245: `呼び出し先のトリガーがありません（{frame.key}）`
- L283: `呼び出し先のステップを進められません`
- L305: `呼び出し先のトリガーがありません（{frame.key}）`
- L406: `呼び出し先のトリガーがありません（{frame.key}）`

## keyseq/application/config_service/__init__.py

- L141: `keymap JSON の形式が不正です。`
- L233: `保存できる keymap がありません。`

## keyseq/application/config_service/child_file_io.py

- L22: `sequence JSON の形式が不正です。`
- L76: `trigger_set JSON の形式が不正です。`

## keyseq/application/config_service/keymap_save_plan.py

- L66: `キーマップの保存計画と保存先が一致しません。`
- L99: `sequence の保存先変更には trigger_set の保存が必要です。`

## keyseq/application/config_service/keymap_set_history.py

- L61: `履歴ファイルを保存できませんでした: {exc}`
- L71: `履歴ファイルを読み込めず、退避もできないため記録できません。`
- L73: `構成セットのパスが空のため履歴を記録できません。`

## keyseq/application/config_service/save_plan_execution.py

- L258: `保存した trigger_set を読み直せません`
- L270: `移行元 keymap_set の参照整理に失敗しました: {trigger_set_path}: {exc}`
- L415: `未知の子種別です: {entry.kind}`
- L417: `不正な保存操作です: {entry.kind}:{entry.key}`
- L420: `保存計画が重複しています: {entry.kind}:{entry.key}`
- L423: `存在しない keymap です: {entry.key}`
- L425: `存在しない sequence です: {entry.key}`
- L427: `存在しない trigger_set です: {entry.key}`
- L431: `移行対象は保存しないを選択できません。`
- L434: `別名保存先が空です: {entry.kind}:{entry.key}`
- L440: `別名保存先のディレクトリを作成できません: {entry.kind}:{entry.key}`
- L449: `子ファイルの保存先が重複しています: {item['resolved_path']}`
- L453: `trigger_set {blocked_sets[0]} の保存先変更には keymap の保存が必要です。`
- L458: `sequence {blocked_keys[0]} の保存先変更には trigger_set の保存が必要です。`

## keyseq/application/config_service/split_loading.py

- L50: `keymap_set.json の読込に失敗しました。`
- L381: `旧トリガー一覧（{stem}）`

## keyseq/application/file_line_loader.py

- L93: `前回のファイル読込が終わっていません（ファイル: {path}）`
- L120: `前回のファイル読込が終わっていません（ファイル: {request.path}）`
- L130: `ファイルの読込が {self._timeout_seconds} 秒以内に終わりませんでした（ファイル: {request.path}）`
- L148: `ファイルの読込が {self._timeout_seconds} 秒以内に終わりませんでした（ファイル: {request.path}）`

## keyseq/application/file_line_reader.py

- L55: `(空)`
- L55: `文字コードが不正です: {encoding or '(空)'}（ファイル: {path}）`
- L57: `(空)`
- L57: `範囲外の扱いが不正です: {out_of_range or '(空)'}（ファイル: {path}）`
- L59: `行番号が整数ではありません: {line_number}（ファイル: {path}）`
- L69: `ファイルを文字コード {encoding} で復号できません（ファイル: {path}）`
- L89: `空ファイルでは行番号を折り返せません（行番号: {line_number}, 行数: 0, ファイル: {path}）`
- L93: `行番号が範囲外です（行番号: {line_number}, 行数: {line_count}, ファイル: {path}）`
- L119: `ファイルサイズが上限 1 MB を超えています（サイズ: {size} バイト, ファイル: {path}）`
- L126: `ファイルを読み込めません（ファイル: {path}）: {exc}`
- L129: `ファイルサイズが上限 1 MB を超えています（サイズ: 1 MB 超, ファイル: {path}）`

## keyseq/application/held_inputs.py

- L145: `リピート停止の判定でキー名を解けませんでした: %s`
- L162: `キーのリピート送信に失敗しました: {exc}`
- L173: ` / 解放エラー: {release_error}`

## keyseq/application/hook_coordinator.py

- L34: `フックの開始に失敗しました。⏎{e}`
- L34: `開始失敗`
- L71: `フック設定失敗`
- L71: `入力イベント監視の登録に失敗しました。⏎⏎{type(e).__name__}: {e}`
- L94: `トリガーが1件も登録されていません。`
- L94: `開始できません`
- L98: `アクションが入っているトリガーがありません。`
- L98: `開始できません`

## keyseq/application/hotkey_service.py

- L22: `不明なキー名があります: '{p}'（詳細: {e}）`

## keyseq/application/key_repeat.py

- L64: `リピート予約の取り消しに失敗しました`
- L94: `リピートのブロック判定に失敗しました`
- L107: `リピートの送信に失敗しました: %s`
- L114: `リピートの再予約に失敗しました: %s`

## keyseq/application/keymap_switch_batch.py

- L35: `Windows キー・Caps Lock・AltGr は切替キーにできません:⏎{key}`
- L105: `切替キーは必須です。`
- L107: `直接切替キーが停止キーと重複しています:⏎{key}`
- L109: `直接切替キーが一時停止/再開キーと重複しています:⏎{key}`
- L111: `直接切替キーが通常トリガーと重複しています:⏎{key}`
- L113: `直接切替キーがキーマップ元キーと重複しています:⏎{key}`
- L116: `この切替キーは既に使用されています:⏎{key} -> {existing_target_name}`
- L118: `直接切替キーは既に使用されています:⏎{key}`

## keyseq/application/save_plan.py

- L26: `sequence の行識別子が不正です。`
- L35: `sequence の行識別子が不正です。`
- L41: `sequence の行番号が不正です。`
- L43: `sequence の行番号が不正です。`
- L52: `sequence の識別子が不正です。`
- L59: `sequence の合成キーが不正です。`

## keyseq/application/screen_grid_session.py

- L247: `画面（モニタ）を取得できませんでした`

## keyseq/application/sequence_history.py

- L13: `戻す対象のトリガーがありません`
- L14: `対象のトリガーが待機中のため操作できません`

## keyseq/application/sequence_runner/call_run_to_end.py

- L343: `呼び出しを実行できません`

## keyseq/application/sequence_runner/call_wait.py

- L196: `呼び出しを実行できません`
- L317: `呼び出しを実行できません`

## keyseq/application/sequence_runner/file_line_wait.py

- L11: `file_line の読込の仕組みが未設定です`

## keyseq/application/sequence_runner/input_acceptance.py

- L67: `一時停止中の実行を破棄しました（{', '.join(selected)}）`
- L149: `一時停止中の {', '.join(paused)} を破棄します。もう一度押すと実行します`
- L214: `{key} を選びました（もう一度押すと実行します）`

## keyseq/application/sequence_runner/sequence_runner.py

- L97: `押下中の入力の解放に失敗しました: `
- L374: ` / 解放エラー: `

## keyseq/application/sequence_steps.py

- L15: `制御アクションの処理が 10000 回を超えました（通常アクションの無いループ等）`
- L45: `(なし)`
- L48: `(なし)`
- L48: `回数={action.get('count', '(なし)')}`
- L48: `無限`
- L50: `(なし)`
- L50: `{action.get('ms', '(なし)')}ms`
- L52: `(なし)`
- L52: `カウンター={action.get('counter', '(なし)')}`
- L56: `(なし)`
- L56: `呼び出し先={target or '(なし)'}`
- L63: ` / ラベル: {label.strip()}`
- L64: `system 実行エラー（{detail}）: {message}`
- L132: `ループの始まりに対応する終わりがありません`
- L134: `ループの入れ子が {MAX_LOOP_DEPTH} 段を超えています`
- L136: `ループの回数が不正です（1 以上の整数）`
- L144: `ループの終わりに対応する始まりがありません`
- L147: `ループの回数が不正です（1 以上の整数）`
- L161: `カウンター名が空です`
- L188: `system の操作が不正です。操作: {op}`
- L245: `呼び出し先に無限ループがあります`
- L267: `待機時間が不正です（1 以上の整数・ミリ秒）`
- L283: `戻す・先頭へは単独で登録してください`

## keyseq/domain/call_graph.py

- L54: `呼び出し先を選んでください`
- L58: `呼び出し先のトリガーがありません（{target}）`
- L60: `自分自身は呼び出せません`
- L64: `呼び出しが循環します（{' > '.join(path)}）`
- L67: `呼び出しの深さが {sequence_control.MAX_CALL_DEPTH} を超えます`
- L78: `戻す・先頭へのトリガーは呼び出せません`

## keyseq/domain/control_target.py

- L17: `対象のトリガーを選んでください`
- L21: `対象のトリガーがありません（{target}）`
- L23: `自分自身は指定できません`
- L35: `戻す・先頭へのトリガーは指定できません`

## keyseq/domain/hotkey.py

- L11: `hotkey が空です。`
- L18: `hotkey の '+' の前後が空です（例: 'ctrl++c' や '+ctrl+c' や 'ctrl+c+' は不可）。`
- L25: `hotkey に同じキーが重複しています（例: 'ctrl+ctrl+c'）。`

## keyseq/domain/key_hold.py

- L53: `押下方向は down または up を指定してください。`
- L56: `押下方向は down または up を指定してください。`
- L62: `マウスボタンは left / right / middle のいずれかを指定してください。`
- L66: `マウス座標は x と y の両方を指定してください。`
- L72: `マウス座標 x と y は整数に変換できる値を指定してください。`
- L77: `キー名は空でない文字列で指定してください。`
- L80: `キー名に + または , は使用できません。`
- L109: `中`
- L109: `右`
- L109: `左`
- L110: `マウス{button_names[name]}`
- L120: `押す`
- L120: `離す`
- L124: ` (リピート)`

## keyseq/domain/mouse_scroll.py

- L17: `上`
- L17: `下`
- L17: `右`
- L17: `左`
- L31: `向きは up / down / left / right のいずれかを指定してください。`
- L34: `向きは up / down / left / right のいずれかを指定してください。`
- L40: `単位は notch または delta を指定してください。`
- L42: `単位は notch または delta を指定してください。`
- L46: `量は整数で指定してください。`
- L51: `量は整数で指定してください。`
- L57: `量は整数に変換できる値を指定してください。`
- L59: `量は整数で指定してください。`
- L63: `量は 1〜{maximum} の範囲で指定してください。`
- L68: `マウス座標は x と y の両方を指定してください。`
- L74: `マウス座標 x と y は整数に変換できる値を指定してください。`
- L97: `[スクロール] {_DIRECTION_NAMES[parsed.direction]} {parsed.amount}`
- L99: ` (生)`
- L108: `(なし)`
- L108: `{key}={str(action[key]) if key in action else '(なし)'}`
- L111: `(なし)`
- L111: `{key}={str(action[key]) if key in action else '(なし)'}`

## keyseq/domain/screen_grid/assignment.py

- L77: `{location}: キーが空です`
- L79: `{location}: キー {key} が重複しています`
- L81: `{location}: 修飾キー {key} は使えません`
- L83: `{location}: 操作キー {key} と重なっています`
- L85: `{location}: 予約キー {key} は使えません`
- L97: `段がありません`
- L100: `段 {row_index}: 高さの比率は正の有限数にしてください`
- L102: `段 {row_index}: 列がありません`
- L104: `段 {row_index}・列 {col_index}`
- L106: `{location}: 幅の比率は正の有限数にしてください`
- L117: `細分化: 段数は1〜9にしてください`
- L120: `細分化: 列数は1〜9にしてください`
- L122: `細分化: 枠を2つ以上にしてください`
- L125: `細分化: キー数は{expected}個にしてください`
- L130: `細分化・枠 {index}`

## keyseq/domain/screen_grid/normalize.py

- L37: `キーが空です`
- L39: `キーが重複しています`
- L41: `修飾キー {key} です`
- L48: `段がありません`
- L53: `段の形が不正です`
- L55: `比率が不正です`
- L58: `列がありません`
- L62: `列の形が不正です`
- L64: `比率が不正です`
- L73: `比率が不正です`
- L78: `比率が不正です`
- L92: `形が不正です`
- L95: `段数が不正です`
- L97: `列数が不正です`
- L99: `段数・列数が不正です（枠を2つ以上にしてください）`
- L101: `キー数が不正です`

## keyseq/domain/screen_grid/ops.py

- L27: `深くする`
- L28: `戻る`
- L29: `クリック`
- L30: `次の画面へ`
- L31: `上へ`
- L32: `下へ`
- L33: `左へ`
- L34: `右へ`
- L90: `操作キー（{OP_LABELS[operation]}）: `
- L92: `キーが空です`
- L94: `修飾キー {key} です`
- L96: `固定の操作キー {key} です`
- L98: `キー {key} が先の操作と重複しています`
- L100: `予約キー {key} と重なっています`
- L102: `枠のキー {key} と重なっています`
- L109: `操作キー（戻る・固定）: 枠のキー {FIXED_BACK_KEY} と重なっています`
- L111: `操作キー（クリック・固定）: 枠のキー {FIXED_CLICK_KEY} と重なっています`

## keyseq/domain/sequence_control.py

- L202: `{display_name} （呼び出し先なし）`
- L206: `{display_name} {key}（参照先なし）`
- L222: `{display_name} → （参照先なし）`
- L227: `{display_name} → {key}（参照先なし）`

## keyseq/infrastructure/input_gateway.py

- L429: `テンキーのキー名は num 0〜num 9 / num add / num subtract / num multiply / num divide / num decimal / num enter のいずれかで指定してください。`

## keyseq/infrastructure/win32_window.py

- L61: `前面ウィンドウのプロセス判定に失敗しました`
- L62: `前面ウィンドウ HWND の取得に失敗しました`
- L63: `ウィンドウ位置の変更に失敗しました`
- L64: `マウスボタン状態の取得に失敗しました`
- L65: `モニター領域の列挙に失敗しました`
- L66: `仮想キーコードからスキャンコードへの変換に失敗しました`
- L67: `仮想キーコードから文字への変換に失敗しました`
- L68: `クリック透過ウィンドウの設定に失敗しました`

## keyseq/presentation/app.py

- L123: `startup.json 読込失敗`
- L124: `startup.json の読込に失敗しました。⏎{exc}⏎⏎既定設定で起動します。`
- L230: `停止トリガー`
- L233: `トリガー一覧`
- L234: `一時停止/再開キー`
- L235: `キーマップ直接切替キー`
- L236: `キーマップ元キー`
- L243: `一時停止/再開キー`
- L246: `トリガー一覧`
- L247: `停止キー`
- L248: `キーマップ直接切替キー`
- L249: `キーマップ元キー`
- L404: `フック`
- L408: `表示`
- L419: `(未設定)`
- L420: `保存済み`
- L420: `未保存`
- L421: `ファイル: {name} / {save_state}`
- L492: `フォントサイズを標準にしました。`
- L494: `フォントサイズを {new_delta} にしました。`
- L645: `ホットキープリセット編集`
- L648: `プリセットを更新しました。`
- L759: `終了`
- L785: `すべて解放`

## keyseq/presentation/controllers/config_io/child_save_columns.py

- L7: `保存先パス`
- L7: `共有状況`
- L7: `対象名`
- L7: `操作`
- L7: `種別`

## keyseq/presentation/controllers/config_io/child_save_dialog.py

- L37: `子ファイルの保存`
- L67: `キャンセル`
- L109: `保存`
- L109: `保存しない`
- L109: `別名保存`
- L170: `移行対象は保存しないを選択できません。`
- L183: `次の子ファイルの保存先が変わります:⏎{', '.join(blocked_labels)}⏎⏎{parent_name}の保存先: {trigger_set_row.target_path}⏎共有状況: {trigger_set_row.share_text}⏎⏎保存 = このまま{parent_name}を保存して索引を更新します。⏎別名保存 = 別の保存先へ{parent_name}を保存して索引を更新します。⏎保存しない = この保存では索引を更新しない（次回保存で反映）。⏎キャンセル = 一覧から選び直します。`
- L210: `{_kind_label(trigger_set_row.kind)}の保存が必要です`
- L230: `キャンセル`
- L231: `保存しない`
- L236: `別名保存`
- L240: `保存`
- L250: `再計算後の保存先に既存ファイルがあります:⏎⏎`
- L252: `種別: {_kind_label(row.kind)}⏎対象名: {row.display_name}⏎保存先: {row.target_path}⏎共有状況: {row.share_text}`
- L258: `⏎⏎「はい」= このまま上書き / 「いいえ」= 別名で保存 / 「キャンセル」= 保存を中止`
- L262: `再計算後の保存先を確認`
- L283: `{_kind_label(row.kind)}を別名で保存`
- L293: `キーマップ`
- L294: `トリガー一覧`
- L295: `出力シーケンス`

## keyseq/presentation/controllers/config_io/child_save_plan.py

- L56: `移行対象は保存しないを選択できません。`
- L69: `保存操作が未指定です: {child_id[0]}:{child_id[1]}`

## keyseq/presentation/controllers/config_io/child_save_rows.py

- L77: `同名の既存ファイルあり・安全のため別名`
- L79: `新規作成`
- L81: `この構成のみが所有・既存を上書き`
- L83: `{ref_count} 個の上位で共有中・全てに影響します`
- L85: `別の構成に属します`
- L86: `所有元不明・安全のため別名`
- L169: `{owner_name} / トリガー一覧`
- L198: `（{row_number} 行目）`

## keyseq/presentation/controllers/config_io/hotkey_presets_io.py

- L27: `プリセット保存失敗`
- L33: `global/ はグローバル用のため、専用プリセットの保存先にできません。⏎現在の保存先: {stored_path}`
- L38: `保存先がグローバルライブラリと同じファイルです。⏎config.json の hotkey_presets_path を global/ 配下へ直してください。⏎現在の保存先: {stored_path}`
- L42: `専用プリセットを保存できません`
- L53: `専用プリセットの上書き確認`
- L58: `保存先には既にファイルがありますが、プリセットとして読み込めません。`
- L60: `保存先には既にプリセットファイルがあり、表示中の一覧と内容が異なります。`
- L63: `{description}⏎保存先: {stored_path}`
- L74: `キャンセル`
- L78: `既存を読み込む`
- L83: `上書きする`

## keyseq/presentation/controllers/config_io/io_dialogs.py

- L16: `保存先の確認`
- L17: `同名ファイルが既にあります。⏎⏎{path}⏎⏎上書きしますか？⏎「いいえ」で別名保存します。`
- L41: `保存名: {self._app.paths.filename_stem(path)}`
- L42: `ラベル名も保存名に合わせる`
- L55: `キャンセル`
- L64: `キャンセルされました。`

## keyseq/presentation/controllers/config_io/keymap_file_io.py

- L34: `キーマップ`
- L34: `対象のキーマップを選択してください。`
- L46: `保存`
- L46: `読込で持ってきたキーマップです。⏎別名で保存しますか？`
- L54: `キーマップを保存`
- L72: `キーマップを別名で保存`
- L82: `キーマップ名の連動`
- L95: `キーマップ保存失敗: {e}`
- L96: `保存失敗`
- L104: `キーマップの保存を中止しました。`
- L201: `sequence の保存先変更には trigger_set の保存が必要です。`
- L227: `キーマップを保存しました。`
- L228: `キーマップを保存しました:⏎{path}`
- L230: `⏎上位の索引を保存すると追随します。`
- L231: `⏎上位の索引を保存すると追随します。`
- L233: `保存`
- L237: `キーマップを読込`
- L244: `このキーマップは既に読み込まれています`
- L244: `読込できません`
- L255: `キーマップ読込失敗: {e}`
- L256: `読込失敗`
- L316: `キーマップを読み込みました。`
- L317: `キーマップを読み込みました:⏎{path}`
- L317: `読込`

## keyseq/presentation/controllers/config_io/keymap_set_history_io.py

- L27: `構成セットの履歴を記録できませんでした: {exc}`

## keyseq/presentation/controllers/config_io/keymap_set_io.py

- L48: `未保存の変更`
- L49: `未保存の変更があります。⏎{action_name}の前に保存しますか？`
- L61: `新規作成`
- L83: `新規作成しました（未保存）。`
- L90: `保存しました。`
- L102: `別名で保存（keymap_set）`
- L112: `別名で保存しました。`
- L129: `保存を中止しました。`
- L135: `保存`
- L175: `トリガー一覧`
- L175: `参照元の子ファイル`
- L176: `{label}は未保存です。次回保存で索引を更新します。`
- L180: `保存しました:⏎{save_path}`
- L183: `保存`
- L192: `保存失敗: {e}`
- L193: `保存失敗`
- L198: `保存`
- L246: `トリガー一覧も保存して索引を更新しました。`
- L444: `トリガー一覧の保存先が変わったため、出力シーケンス {changed_sequences} 件の保存先を再計算しました。`
- L478: `{name} / トリガー一覧`
- L503: `{name} / トリガー一覧`
- L512: `（{row_number} 行目）`
- L549: `読込`
- L553: `keymap_set.json を読込`
- L577: `読み込みました。`
- L578: `読み込みました:⏎{path}`
- L578: `読込`
- L585: `読込失敗: {e}`
- L586: `読込失敗`
- L597: `読込`
- L598: `旧形式のトリガー一覧 {legacy.get('path', '')} を、キーマップ『{name}』に移しました（切替キーは未設定です）`
- L623: `Import しました。`
- L624: `単一JSONを取り込みました:⏎{path}`
- L626: `Import 失敗: {e}`
- L627: `Import 失敗`
- L641: `Export しました。`
- L642: `単一JSONを書き出しました:⏎{path}`
- L644: `Export 失敗: {e}`
- L645: `Export 失敗`
- L648: `例の復元`
- L650: `例の設定に戻します。よろしいですか？`
- L650: `確認`
- L668: `例の設定に戻しました（未保存）。`
- L672: `起動時に読むJSONの変更`
- L676: `起動時に読み込む keymap_set.json を選択`
- L689: `設定`
- L707: `起動時読み込み設定の保存に失敗しました。`
- L710: `起動時読み込み設定を更新しました。`
- L711: `次回起動時はこの keymap_set を読み込みます:⏎{path}`
- L711: `設定`
- L734: `保存先の確認`
- L735: `構成セットがデフォルト外に保存されます。⏎keymaps / trigger_sets / sequences も構成セット周辺に保存しますか？⏎⏎「いいえ」の場合はデフォルト保存先を使います。`

## keyseq/presentation/controllers/config_io/orphan_sweep_io.py

- L42: `孤児ファイルの棚卸し`
- L63: `孤児ファイルの棚卸し`
- L65: `隔離する孤児候補を確認してください。`
- L66: `隔離する`
- L73: `孤児ファイルの棚卸し`
- L80: `孤児ファイルの棚卸し`
- L80: `棚卸しの前に保存が必要です。保存しますか？`

## keyseq/presentation/controllers/config_io/quarantine_manage_io.py

- L20: `隔離された実行単位はありません。`
- L20: `隔離の管理`
- L36: `マニフェストが読めないため復元できません`
- L36: `隔離の管理`
- L42: `隔離の管理`
- L43: `復元する`
- L43: `復元する内容を確認してください。`
- L51: `隔離の管理`
- L59: `削除対象を列挙できません。削除していません。⏎{error}`
- L59: `隔離の管理`
- L62: `隔離の管理`
- L64: `削除する`
- L64: `削除する内容を確認してください。`
- L73: `隔離の管理`

## keyseq/presentation/controllers/config_io/reference_cleanup_io.py

- L19: `参照元の掃除`
- L20: `掃除するには構成セットの保存が必要です。保存しますか？`
- L35: `参照元の掃除`
- L40: `参照元の掃除`
- L53: `参照元の掃除`

## keyseq/presentation/controllers/config_io/save_target_snapshot.py

- L14: `保存の準備中にトリガー一覧が変わったため、保存を中止しました。もう一度保存してください。`

## keyseq/presentation/controllers/config_io/sequence_file_io.py

- L12: `出力シーケンス`
- L12: `対象のトリガーを選択してください。`
- L16: `保存`
- L16: `読込で持ってきた出力シーケンスです。⏎別名で保存しますか？`
- L21: `出力シーケンスを保存`
- L29: `出力シーケンス`
- L29: `対象のトリガーを選択してください。`
- L39: `出力シーケンスを別名で保存`
- L48: `出力シーケンス名の連動`
- L79: `出力シーケンスを保存しました。`
- L80: `出力シーケンスを保存しました:⏎{path}`
- L82: `⏎上位の索引を保存すると追随します。`
- L83: `⏎上位の索引を保存すると追随します。`
- L85: `保存`
- L88: `出力シーケンス保存失敗: {e}`
- L89: `保存失敗`
- L95: `出力シーケンス`
- L95: `読込先のトリガーを選択してください。`
- L98: `出力シーケンスを読込`
- L114: `出力シーケンスを読み込みました。`
- L115: `出力シーケンスを読み込みました:⏎{path}`
- L115: `読込`
- L117: `出力シーケンス読込失敗: {e}`
- L118: `読込失敗`

## keyseq/presentation/controllers/config_io/startup_io.py

- L63: `startup.json 保存失敗`

## keyseq/presentation/controllers/config_io/trigger_set_file_io.py

- L46: `トリガー一覧を保存`
- L60: `トリガー一覧を別名で保存`
- L78: `トリガー一覧の保存を中止しました。`
- L82: `保存`
- L91: `トリガー一覧保存失敗: {e}`
- L92: `保存失敗`
- L97: `保存`
- L140: `トリガー一覧を保存しました。`
- L141: `トリガー一覧を保存しました:⏎{path}`
- L143: `⏎上位の索引を保存すると追随します。`
- L144: `⏎上位の索引を保存すると追随します。`
- L146: `保存`
- L202: `トリガー一覧読込`
- L205: `トリガー一覧を読込`
- L214: `トリガー一覧読込失敗: {e}`
- L215: `読込失敗`
- L224: `読込先のキーマップがありません。`
- L293: `トリガー一覧を読み込みました。`
- L294: `トリガー一覧を読み込みました:⏎{path}`
- L294: `読込`

## keyseq/presentation/controllers/hook_controller.py

- L233: `すべて解放`
- L243: `開始できません`
- L244: `停止キーと一時停止/再開キーが重複しています:⏎{stop_key}`
- L274: `停止しました`
- L282: `停止キー`
- L283: `一時停止/再開キー`
- L284: `切替キー`
- L285: `上位の割り当て`
- L289: `{conflict.key} は{reason}と重複しているため、キーマップ {name} へ切り替えられません。切替キーを変更してください`
- L292: `{conflict.key} は{reason}と重複しているため、トリガーは実行されません。トリガーのキーを変更してください`
- L389: `キー送信中にエラーが発生しました。⏎送信キーに間違いがあります。修正してください。⏎⏎種別: {t}⏎値: {v}⏎⏎エラー: {err}`
- L401: `送信エラー`

## keyseq/presentation/controllers/key_capture.py

- L156: `{self._label}は単キーのみ対応です（例: {self._single_key_example}）。`
- L156: `設定できません`
- L162: `{self._label}が{other_name}と重複しています:⏎{key}`
- L162: `設定できません`
- L169: `不明なキー名です:⏎{key}⏎⏎{e}`
- L169: `設定できません`

## keyseq/presentation/controllers/keymap_panel/keymap_add_flow.py

- L24: `新規`
- L25: `新規`
- L29: `キーマップを追加しました: {normalize_key_name(created.get('id', ''))}`
- L34: `読込`
- L40: `貼り付け`
- L41: `貼り付け`
- L56: `貼り付け`
- L78: `キーマップ追加`
- L78: `新規`
- L78: `読込`
- L78: `読込キーマップの追加`
- L79: `キーマップ貼り付け`
- L79: `貼り付け`
- L84: `新規`
- L99: `既存`
- L118: `{rows[index][1]}: 不明なキー名です:⏎{value['key']}⏎⏎{exc}`
- L136: `貼り付け`

## keyseq/presentation/controllers/keymap_panel/keymap_list_edit.py

- L60: `実行中のためキーマップを並べ替えられません`
- L100: `キーマップをすべて削除することはできません。`
- L100: `削除できません`
- L108: `キーマップ {len(targets)} 件を削除しますか？`
- L110: `⏎⏎未保存のトリガー一覧・シーケンスも破棄されます。`
- L111: `確認`

## keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py

- L24: `連続実行中のためキーマップを切り替えられません`
- L55: `一時停止/再開キーと重複`
- L55: `停止キーと重複`
- L105: `キーマップは未登録です`
- L180: `設定できません`
- L181: `Windows キー・Caps Lock・AltGr は切替キーにできません:⏎{key}`
- L187: `直接切替キーが停止キーと重複しています:⏎{key}`
- L187: `設定できません`
- L192: `直接切替キーが一時停止/再開キーと重複しています:⏎{key}`
- L192: `設定できません`
- L197: `直接切替キーが通常トリガーと重複しています:⏎{key}`
- L197: `設定できません`
- L202: `直接切替キーがキーマップ元キーと重複しています:⏎{key}`
- L202: `設定できません`
- L212: `この切替キーは既に使用されています:⏎{key} -> {existing_name}`
- L212: `設定できません`
- L225: `この keymap には既に直接切替キーがあります:⏎{existing_switch_key} -> {target_name}`
- L225: `設定できません`
- L233: `不明なキー名です:⏎{key}⏎⏎{e}`
- L233: `設定できません`
- L255: `名前変更`
- L255: `名前変更したい keymap を選択してください。`
- L264: `名前変更`
- L265: `keymap の表示名を入力してください。⏎空欄にすると id 表示に戻ります。⏎⏎id: {keymap_id}`
- L276: `keymap 名は変更なしです: {self.format_keymap_display_name(target) or keymap_id}`
- L285: `keymap 名を変更しました: {normalized_label}`
- L287: `keymap 名をクリアしました: {keymap_id}`
- L298: `削除`
- L298: `削除したい keymap を選択してください。`
- L301: `キーマップが1つだけのため削除できません。`
- L301: `削除できません`
- L314: `keymap を削除しますか？⏎⏎{target_name}`
- L316: `⏎⏎未保存のトリガー一覧・シーケンスも破棄されます。`
- L317: `確認`
- L326: `キーマップを削除しました: {target_name} / 現在: {self.get_active_keymap_text()}`
- L328: `キーマップを削除しました: {target_name}`
- L347: `削除できません`
- L347: `選択した keymap を削除できませんでした。`
- L387: `変更`
- L387: `編集したい keymap を選択してください。`
- L393: `変更できません`
- L393: `選択した keymap を特定できませんでした。`
- L399: `キーマップ変更`
- L484: `キーマップが2つ以上ある場合、切替キーは空にできません。`
- L484: `設定できません`
- L544: `キーマップは変更なしです: {self.format_keymap_display_name(keymap) or keymap_id}`
- L550: `キーマップを変更しました: {self.format_keymap_display_name(keymap) or keymap_id}`
- L598: `アクティブなキーマップを切り替えました: {self.get_active_keymap_text()}`
- L600: `アクティブなキーマップは変更なしです: {self.get_active_keymap_text()}`
- L606: `(なし)`
- L608: `{label}（フック停止中）`
- L610: `{label}（一時停止）`
- L615: `(なし)`
- L624: `設定できません`
- L625: `Windows キー・Caps Lock・AltGr はキーマップの元キーにできません。`
- L629: `キーマップは単キーのみ対応です。`
- L629: `設定できません`
- L635: `このキーは予約キーのため、キーマップ元キーにできません:⏎{source}`
- L635: `設定できません`
- L638: `このキーはキーマップ直接切替キーに設定されています:⏎{source}`
- L638: `設定できません`
- L641: `このキーはアクティブキーマップのトリガーキーに設定されています:⏎{source}`
- L641: `設定できません`
- L647: `不明なキー名です:⏎{target}⏎⏎{e}`
- L647: `設定できません`
- L654: `キーマップを更新しました: {source} -> {target} ({keymap_id})`
- L656: `キーマップは変更なしです: {source} -> {target}`
- L667: `キーマップをクリアしました: {source} ({keymap_id})`
- L670: `クリア対象のキーマップはありません: {source}`

## keyseq/presentation/controllers/layout_controller.py

- L214: `すべて解放`
- L249: `保存失敗: {e}`
- L250: `保存失敗`
- L291: `外部レイアウトを追加`
- L303: `同じJSONファイルは既に登録されています。`
- L307: `レイアウト追加失敗`
- L312: `外部レイアウトを追加しました: {layout.layout_id}`
- L321: `レイアウト削除`
- L321: `削除できる外部レイアウトがありません。`
- L324: `レイアウトを削除`
- L332: `レイアウト削除`
- L332: `削除対象のレイアウト情報を取得できませんでした。`
- L335: `外部レイアウト '{target_id}' を削除しますか？`
- L335: `確認`
- L357: `外部レイアウトを削除しました: {target_id}`

## keyseq/presentation/controllers/trigger_panel/action_edit.py

- L66: `まずトリガーを選択してください。`
- L66: `追加`
- L75: `追加`
- L90: `追加`
- L91: `戻す・先頭へは、出力シーケンスにそれ 1 つだけで登録してください。`
- L103: `追加`
- L104: `ループの入れ子が {MAX_LOOP_DEPTH} 段を超えるため追加できません。`
- L128: `複製`
- L146: `貼り付け`
- L180: `対になっていないループの始まり / 終わりは複製 / 貼り付けできません。`
- L181: `ループの入れ子が {MAX_LOOP_DEPTH} 段を超えるため複製 / 貼り付けできません。`
- L182: `戻す・先頭へは、出力シーケンスにそれ 1 つだけで登録してください。`
- L189: `まずトリガーを選択してください。`
- L189: `編集`
- L194: `編集`
- L194: `編集したい行を選択してください。`
- L208: `編集`
- L209: `ループの対応が崩れているため編集できません。削除して追加し直してください`
- L219: `編集`
- L232: `編集`
- L233: `戻す・先頭へは、出力シーケンスにそれ 1 つだけで登録してください。`
- L249: `まずトリガーを選択してください。`
- L249: `削除`
- L254: `削除`
- L254: `削除したい行を選択してください。`
- L261: `確認`
- L276: `選択した行を削除しますか？`
- L279: `ループの始まりと終わりを削除します（中の行は残ります）。よろしいですか？`
- L280: `選択した {len(indices)} 行を削除しますか？`
- L282: `⏎ループの始まりと終わりは対で削除します（中の行は残ります）。`
- L288: `まずトリガーを選択してください。`
- L288: `移動`
- L292: `移動`
- L292: `移動したい行を選択してください。`
- L308: `ループの始まりと終わりの組が変わるため移動できません`

## keyseq/presentation/controllers/trigger_panel/effective_row_transition.py

- L29: `{key} は実行中のため、有効なトリガーを入れ替えられません`

## keyseq/presentation/controllers/trigger_panel/trigger_list_edit.py

- L54: `トリガー {count} 件を削除しますか？`
- L55: `トリガー {key} を削除しますか？`
- L56: `確認`

## keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py

- L34: `連続実行中は呼び出し先を変更できません（一時停止してから操作してください）`
- L220: `{s}（上のトリガーと重複）`
- L253: `停止キーと重複`
- L254: `一時停止/再開キーと重複`
- L255: `切替キーと重複`
- L256: `上位の割り当てと重複`
- L413: `一時停止`
- L417: `(未選択)`
- L420: ` / 押下中: {', '.join(held_names)}`
- L423: ` / 次: {self.get_next_action_summary(sel_key)}`
- L424: `フック: {hook_state} / キーマップ: {keymap_text}{held_suffix}⏎選択: {sel_key}{suffix}`
- L426: `フック: {one_line(hook_state)} / キーマップ: {one_line(keymap_text)}{one_line(held_suffix)}⏎選択: {one_line(sel_key)}{one_line(suffix)}`
- L432: `(未設定)`
- L446: ` / 選択中の次: {next_i}`
- L447: `フック: {hook_state} / キーマップ: {keymap_text} / トリガー: {keys_text} / 選択中: {sel_key}{suffix}{held_suffix}`
- L456: `(未選択)`
- L458: `(なし)`
- L461: `(なし)`
- L470: `(なし)`

## keyseq/presentation/controllers/trigger_panel/trigger_row_edit.py

- L23: `トリガー追加`
- L35: `すでに存在します: {key}`
- L35: `追加できません`
- L39: `このキーはフック停止トリガーに設定されています:⏎{key}`
- L39: `追加できません`
- L42: `このキーは一時停止/再開キーに設定されています:⏎{key}`
- L42: `追加できません`
- L45: `このキーはキーマップ直接切替キーに設定されています:⏎{key}`
- L45: `追加できません`
- L48: `このキーはアクティブキーマップの置換元キーに設定されています:⏎{key}`
- L48: `追加できません`
- L63: `変更`
- L63: `変更したいトリガーを選択してください。`
- L74: `トリガー変更`
- L87: `すでに存在します: {new}`
- L87: `変更できません`
- L90: `このキーはフック停止トリガーに設定されています:⏎{new}`
- L90: `変更できません`
- L93: `このキーは一時停止/再開キーに設定されています:⏎{new}`
- L93: `変更できません`
- L96: `このキーはキーマップ直接切替キーに設定されています:⏎{new}`
- L96: `変更できません`
- L99: `このキーはアクティブキーマップの置換元キーに設定されています:⏎{new}`
- L99: `変更できません`
- L157: `削除`
- L157: `削除したいトリガーを選択してください。`
- L163: `トリガー {key} を削除しますか？`
- L163: `確認`

## keyseq/presentation/dialogs/action_control_fields.py

- L30: `ループ`
- L31: `カウンター +1`
- L32: `カウンターを 0 に`
- L33: `待機`
- L34: `停止`
- L35: `呼び出し`
- L36: `戻す`
- L37: `先頭へ`
- L42: `エラーで停止`
- L43: `空を送る`
- L44: `折り返し`
- L68: `ループ`
- L69: `system 設定`
- L70: `file_line 設定`
- L78: `カウンター +1`
- L83: `操作`
- L90: `回数`
- L96: `無限`
- L106: `カウンター名`
- L111: `ミリ秒`
- L117: `呼び出し先`
- L130: `呼び出し先の「間隔(ms)」の間隔で実行します（連続実行 OFF でも使います）`
- L136: `呼び出し先を一括で実行する（停止の行は読み飛ばす）`
- L142: `対象のトリガーを指定する`
- L149: `ファイル`
- L152: `参照…`
- L156: `カウンター名`
- L164: `文字コード`
- L171: `エラーで停止`
- L172: `範囲外`
- L200: `呼び出し先`
- L200: `対象のトリガー`
- L229: `カウンター +1`
- L248: `エラーで停止`
- L263: `入力エラー`
- L263: `操作が不正です。`
- L275: `カウンター名が空です。`
- L275: `入力エラー`
- L284: `ミリ秒は 1 以上の整数で入力してください。`
- L284: `入力エラー`
- L306: `{self._missing_call_target}（参照先なし）`
- L314: `入力エラー`
- L315: `呼び出し先のトリガーがありません（{self._missing_call_target}）`
- L317: `入力エラー`
- L317: `呼び出し先を選んでください`
- L323: `入力エラー`
- L339: `入力エラー`
- L340: `対象のトリガーがありません（{self._missing_call_target}）`
- L342: `入力エラー`
- L342: `対象のトリガーを選んでください`
- L348: `入力エラー`
- L360: `入力エラー`
- L360: `回数は 1 以上の整数で入力してください。`
- L372: `ファイルが空です。`
- L372: `入力エラー`
- L375: `カウンター名が空です。`
- L375: `入力エラー`

## keyseq/presentation/dialogs/action_dialog.py

- L52: `種類`
- L58: `値`
- L65: `キー入力で記録`
- L68: `※記録中は、押したキーが hotkey として反映されます（Escで停止）`
- L72: `ラベル`
- L78: `OSショートカット（プリセット）`
- L88: `プリセット編集…`
- L94: `キャンセル`
- L97: `マウスクリック設定`
- L111: `ボタン`
- L116: `回数`
- L121: `クリック位置を取得`
- L123: `※押したあと、画面上の任意の場所を1回クリックすると座標が入ります`
- L153: `末尾に追加`
- L160: `ループ`
- L201: `入力エラー`
- L201: `種類が不正です。`
- L205: `値が空です。`
- L205: `入力エラー`
- L213: `mouse_click の X/Y が空です。`
- L213: `入力エラー`
- L218: `mouse_click の X/Y は整数で入力してください。`
- L218: `入力エラー`
- L240: `入力エラー`
- L240: `単位を選んでください。`
- L243: `マウス座標の X/Y は両方入力してください。`
- L243: `入力エラー`
- L247: `入力エラー`
- L258: `マウスのボタン`
- L260: `マウス座標の X/Y は両方入力してください。`
- L260: `入力エラー`
- L264: `入力エラー`
- L270: `キー名が不正です: {exc}`
- L270: `入力エラー`
- L285: `ドラッグ（範囲選択・ドラッグ&ドロップ）`
- L291: `離す位置 X`
- L292: `離す位置 Y`
- L293: `速度（px/秒）`
- L300: `離す位置を取得`
- L302: `※押したあと、画面上の任意の場所を1回クリックすると座標が入ります`
- L314: `掴む位置 X`
- L315: `掴む位置 Y`
- L322: `mouse_click の離す位置 X/Y が空です。`
- L322: `入力エラー`
- L327: `mouse_click の離す位置 X/Y は整数で入力してください。`
- L327: `入力エラー`
- L351: `…取得中：画面上の任意の場所を1回クリックしてください（右クリックでも可）`
- L359: `取得しました: ({int(x)}, {int(y)})`
- L384: `記録停止`
- L397: `キー入力で記録`
- L489: `※記録中は、押したキーが hotkey として反映されます（Escで停止）`
- L588: `ホットキープリセット編集`

## keyseq/presentation/dialogs/action_key_hold_fields.py

- L26: `キーの押下 / 解放`
- L29: `動作`
- L30: `押す`
- L32: `押す`
- L32: `離す`
- L38: `対象`
- L39: `キー`
- L41: `キー`
- L41: `マウスのボタン`
- L49: `キー名`
- L53: `1 キーを記録`
- L55: `キーを 1 つ押すと記録します`
- L60: `ボタン`
- L61: `左`
- L64: `中`
- L64: `右`
- L64: `左`
- L67: `中`
- L67: `右`
- L67: `左`
- L72: `座標を指定する`
- L88: `座標を取得`
- L96: `※押したあと、画面上の任意の場所を1回クリックすると座標が入ります`
- L103: `リピートする`
- L106: `（修飾キーは除く）`
- L111: `押す`
- L111: `離す`
- L113: `マウスのボタン`
- L121: `キー`
- L123: `キー`
- L123: `押す`
- L131: `押す`
- L131: `離す`
- L132: `キー`
- L145: `キー`
- L156: `キー`
- L156: `押す`
- L173: `記録中…`
- L174: `キーを 1 つ押してください（Esc で停止）`
- L183: `1 キーを記録`
- L184: `キーを 1 つ押すと記録します`

## keyseq/presentation/dialogs/action_mouse_scroll_fields.py

- L21: `上`
- L21: `下`
- L21: `右`
- L21: `左`
- L27: `マウススクロール`
- L30: `向き`
- L31: `下`
- L34: `上`
- L34: `下`
- L34: `右`
- L34: `左`
- L40: `ノッチ数`
- L48: `生の値（{WHEEL_DELTA} = 1 ノッチ）`
- L59: `座標を指定する`
- L72: `座標を取得`
- L79: `※押したあと、画面上の任意の場所を1回クリックすると座標が入ります`
- L98: `下`

## keyseq/presentation/dialogs/grid_editor_window.py

- L34: `編集できる画面がありません`
- L325: `細分化・段 {index}: キーは {cols} 個にしてください`
- L327: `枠を設定できません`
- L341: `細分化: 段数・列数は1〜9の整数にしてください`
- L343: `枠を設定できません`

## keyseq/presentation/dialogs/keymap_edit_dialog.py

- L62: `切替キー`
- L71: `クリア`
- L74: `ラベル`
- L80: `枠を使う`
- L84: `枠を編集…`
- L87: `例) 切替キー: 1⏎ラベル: numpad`
- L93: `キャンセル`
- L117: `枠を編集できません`
- L117: `画面（モニタ）を取得できませんでした。`
- L157: `取得中：切替キーにしたいキーを1回押してください（Escでキャンセル）`
- L168: `例) 切替キー: 1⏎ラベル: numpad`

## keyseq/presentation/dialogs/keymap_switch_batch_dialog.py

- L65: `例) 切替キー: 1⏎ラベル: numpad`
- L123: `切替キー`
- L136: `ラベル`
- L150: `枠を使う`
- L159: `キャンセル`
- L176: `設定できません`
- L224: `取得中：切替キーにしたいキーを1回押してください（Escでキャンセル）`
- L239: `例) 切替キー: 1⏎ラベル: numpad`

## keyseq/presentation/dialogs/layout_delete_dialog.py

- L28: `削除する外部レイアウトを選択してください。`
- L45: `削除`
- L46: `キャンセル`
- L58: `レイアウト削除`
- L58: `削除するレイアウトを選択してください。`

## keyseq/presentation/dialogs/orphan_sweep_dialog.py

- L21: `孤児ファイルの棚卸し`
- L31: `追加で走査するディレクトリを指定してください。⏎一覧の変更は「閉じる」でも保存されます。`
- L44: `追加…`
- L45: `削除`
- L48: `棚卸しを実行`
- L49: `閉じる`

## keyseq/presentation/dialogs/preset_dialog.py

- L21: `内容（hotkey）`
- L26: `ラベル`
- L31: `例）内容: windows+d / ラベル: Win+D（ラベルは重複禁止）`
- L37: `キャンセル`
- L46: `入力エラー`
- L46: `内容（hotkey）が空です。`
- L49: `ラベルが空です。`
- L49: `入力エラー`

## keyseq/presentation/dialogs/preset_manager.py

- L32: `保存先: {individual_path}`
- L34: `保存先: グローバル（{global_path}）`
- L39: `config 外のファイルを読み込み中。次の保存で管理下へ移ります。{default_individual_path} へ保存します`
- L45: `記録されていた個別の保存先は config 外にあり、読み込めません。{default_individual_path} へ保存します`
- L50: `記録されていた個別の保存先は config 外にあり、読み込めません。専用を再度有効にすると、{default_individual_path} へ保存します`
- L56: `グローバルを読み込めませんでした。組込既定を表示中（OK でグローバルを作成します）`
- L60: `グローバルを表示中`
- L62: `読み込めませんでした（既定を表示中）`
- L64: `構成セットを保存すると専用にできます`
- L76: `プリセット編集`
- L125: `プリセット一覧`
- L136: `追加`
- L137: `編集`
- L138: `削除`
- L140: `上へ`
- L141: `下へ`
- L147: `この構成セット専用にする`
- L173: `キャンセル`
- L232: `プリセットの切替`
- L233: `編集中の内容は破棄されます。切り替えますか？`
- L303: `プリセット追加`
- L314: `同名のプリセットが既に存在します。⏎⏎label: {label}`
- L314: `追加できません`
- L320: `プリセットの hotkey 値が不正です。⏎⏎入力: {value}⏎理由: {err_msg}`
- L320: `不正なhotkey`
- L331: `編集`
- L331: `編集したい行を選択してください。`
- L336: `プリセット編集`
- L350: `同名のプリセットが既に存在します。⏎⏎label: {label}`
- L350: `変更できません`
- L356: `プリセットの hotkey 値が不正です。⏎⏎入力: {value}⏎理由: {err_msg}`
- L356: `不正なhotkey`
- L369: `削除`
- L369: `削除したい行を選択してください。`
- L373: `選択したプリセットを削除しますか？`
- L374: `選択した {count} 件のプリセットを削除しますか？`
- L375: `確認`
- L382: `移動`
- L382: `移動したい行を選択してください。`

## keyseq/presentation/dialogs/quarantine_manage_dialog.py

- L21: `隔離の管理`
- L31: `実行単位を選択してください。`
- L43: `復元する…`
- L44: `削除する…`
- L45: `閉じる`

## keyseq/presentation/dialogs/reference_cleanup_dialog.py

- L20: `除去する参照元を確認してください。`
- L21: `実行`
- L53: `キャンセル`

## keyseq/presentation/dialogs/trigger_dialog.py

- L44: `トリガー`
- L52: `ラベル`
- L57: `例）トリガー: f1 ⏎   ラベル: コピー→ウィンドウ切替→貼り付け`
- L63: `キャンセル`
- L72: `トリガーが空です。`
- L72: `入力エラー`
- L92: `取得中：トリガーにしたいキーを1回押してください（Escでキャンセル）`
- L103: `例）トリガー: f1 / ラベル: コピー→ウィンドウ切替→貼り`

## keyseq/presentation/hook_button_texts.py

- L3: `キー入力で取得`
- L4: `取得中…（Escで停止）`
- L7: `このキーは取得できません。別のキーを押してください。（Escでキャンセル）`
- L10: `開始（フックON）`
- L11: `停止（フックOFF）`
- L14: `キーマップ一時停止`
- L15: `キーマップ再開`

## keyseq/presentation/keyboard_layouts.py

- L139: `JSONルートは object である必要があります。`
- L143: `{required_key} がありません。`
- L147: `layout_id は文字列である必要があります。`
- L150: `layout_id が空です。`
- L153: `layout_id '{layout_id}' は既に存在します。`
- L157: `display_name は文字列である必要があります。`
- L160: `display_name が空です。`
- L164: `keys が配列ではありません。`
- L166: `keys が空です。`
- L173: `{key_prefix} は object である必要があります。`
- L177: `{key_prefix}.{required_key} がありません。`
- L181: `{key_prefix}.id は文字列である必要があります。`
- L184: `{key_prefix}.id が空です。`
- L186: `{key_prefix}.id が重複しています: {key_id}`
- L191: `{key_prefix}.label は文字列である必要があります。`
- L199: `{key_prefix}.x は 0 以上である必要があります。`
- L201: `{key_prefix}.y は 0 以上である必要があります。`
- L203: `{key_prefix}.w は 0 より大きい必要があります。`
- L205: `{key_prefix}.h は 0 より大きい必要があります。`
- L215: `{key_prefix}.extra_scan_codes は整数の配列である必要があります。`
- L317: `{field_name} は数値である必要があります。`
- L324: `{field_name} は整数である必要があります。`

## keyseq/presentation/keyboard_window.py

- L62: `Keyboard UI — 編集中: {editing_key}（Escでキャンセル）`

## keyseq/presentation/keymap_set_history_text.py

- L5: `直近（最大 20 件）`
- L6: `（見つかりません）`
- L7: `履歴ファイルを読み込めませんでした。編集できません。`
- L8: `構成セットの履歴`
- L9: `名前`
- L10: `パス`
- L11: `分類名`
- L12: `＋分類を追加`
- L13: `分類名を変更`
- L14: `分類を削除`
- L15: `読み込む`
- L16: `読込`
- L17: `履歴から削除`
- L18: `分類へコピー…`
- L19: `閉じる`
- L20: `コピー先の分類`
- L22: `キャンセル`
- L23: `分類がありません。先に分類を追加してください。`
- L24: `分類名が空か、同名の分類が既にあります。`
- L25: `分類が存在しないか、分類名が空または同名です。`
- L26: `分類が存在しません。`
- L27: `分類が存在しないか、分類内に既に同じ構成セットがあります。`
- L28: `履歴の項目が存在しません。`
- L37: `履歴を編集できませんでした: {reason}`
- L41: `構成セットを読み込めませんでした: {reason}`
- L45: `分類「{name}」を配下の履歴ごと削除しますか？⏎実ファイルは削除しません。`
- L49: `この項目を履歴から削除しますか？⏎{path}⏎実ファイルは削除しません。`

## keyseq/presentation/orphan_sweep_text.py

- L4: `隔離できる孤児ファイルはありません。`
- L7: `キーマップ`
- L8: `トリガー一覧`
- L9: `出力シーケンス`
- L10: `個別プリセット`
- L14: `ファイルが見つかりません`
- L15: `読み取り / JSON 解析に失敗しました`
- L16: `リンク / ジャンクションのため参照側として読みませんでした`
- L17: `ディレクトリを読み取れませんでした`
- L21: `マニフェストを書き込めませんでした`
- L22: `移動できませんでした`
- L23: `移動直前の安全確認で対象外になりました`
- L24: `隔離の実行単位ディレクトリを作成できませんでした`
- L25: `隔離ルートがリンク / ジャンクションのため中止しました`
- L29: `注意: 走査範囲外に保存された構成セットから参照されている可能性があります。`
- L38: `警告: 読めなかった構成セット / トリガー一覧が {len(result.unreadable_sources)} 件あります。`
- L39: `それらが参照していた子ファイルを孤児と誤判定している可能性があります。`
- L46: `見つからなかった走査ディレクトリ: {len(result.missing_scan_dirs)} 件`
- L49: `構成セットとして解釈できなかった JSON: {len(result.non_keymap_set_sources)} 件`
- L57: `孤児候補: {len(candidates)} 件`
- L64: `対象外: {excluded_count} 件`
- L78: `提示後に対象外になったため隔離しなかった: {len(result.dropped_paths)} 件`
- L81: `再判定で新たに孤児候補になったため今回は隔離しなかった: {result.newly_orphan_count} 件`
- L91: `警告: 隔離の直前にも読めない参照側が {len(result.rescan_unreadable_sources)} 件ありました。`
- L92: `それらが参照していた子ファイルを孤児と誤判定している可能性があります。`
- L105: `移動できなかったファイル:`
- L109: `警告: マニフェストを書き込めず、隔離の記録が古い可能性があります。`
- L118: `ファイルは 1 件も移動していません。`
- L118: `隔離を中止しました: {reason}`
- L119: `（実行単位: {result.unit_id}）`
- L121: `隔離できませんでした: 0 件{unit_note}`
- L123: `隔離しました: {len(result.moved)} 件{unit_note}`

## keyseq/presentation/quarantine_manage_text.py

- L7: `復元先に同名ファイルがあります`
- L8: `復元先が対象外です`
- L9: `隔離側にファイルがありません（復元済み等）`
- L10: `復元できませんでした`
- L11: `実行単位 ID が不正、または実在しません`
- L12: `マニフェストが読めません`
- L19: `{unit.unit_id}  作成: {unit.created_at}  残り {unit.remaining_count}/{unit.entry_count} 件`
- L20: `  マニフェスト不正（復元できません）`
- L29: `隔離側に残っている {unit.remaining_count} 件を元の場所へ復元します。`
- L30: `復元先に同名ファイルがある場合は上書きせずスキップします。`
- L39: `1 件も戻していません。`
- L39: `復元を中止しました: {reason}`
- L40: `復元しました: {len(result.restored)} 件`
- L43: `スキップ: {len(result.skipped)} 件`
- L44: `  {_REASON_LABELS.get(reason, reason)}: {count} 件`
- L48: `実行単位は残っています。`
- L48: `実行単位を片付けました。`
- L56: `この操作は取り消せません。`
- L56: `削除する実行単位: {unit.unit_id}`
- L58: `マニフェストが読めないため、中身を確認できません。`
- L59: `ディレクトリごと削除します。`
- L67: `削除しました: {result.unit_id}`
- L69: `実行単位 ID が不正、または実在しません`
- L70: `隔離ルート自身、または隔離ルート外を指しています`
- L71: `マニフェストが読めません`
- L72: `削除できませんでした`
- L75: `一部が削除されている可能性があります。`
- L76: `削除していません。`
- L77: `削除を中止しました: {reason}`

## keyseq/presentation/reference_cleanup_text.py

- L4: `掃除する項目はありません。`
- L7: `キーマップ`
- L8: `トリガー一覧`
- L9: `出力シーケンス`
- L13: `読み直せませんでした`
- L14: `JSON の形式が不正です`
- L15: `保存できませんでした`
- L31: `対象ファイル: {target_count} 件、消える参照元: {stale_count} 件`
- L36: `消える参照元:`
- L40: `保護のため残す参照元:`
- L47: `警告: この掃除で参照元が 0 件になります。`
- L48: `子ファイル自体は削除しません。孤児かどうかは「孤児ファイルの棚卸し」で確認できます。`
- L58: `更新したファイル: {len(result.updated_files)} 件、除去した参照元: {removed_count} 件`
- L61: `失敗したファイル:`
- L63: `  {path}: {_FAILURE_MESSAGES.get(reason, '不明な理由で失敗しました')}`
- L63: `不明な理由で失敗しました`

## keyseq/presentation/screen_grid/grid_editor_panel.py

- L28: `枠を編集`
- L57: `枠をクリックして選ぶ → キーを押すとその枠のキー`
- L65: `段の削除`
- L65: `段の追加`
- L66: `列の削除`
- L66: `列の追加`
- L67: `この画面を既定に戻す`
- L67: `振り直し`
- L77: `キーを枠の左上に表示`
- L81: `操作キー（Esc = 戻る・テンキーの Enter = クリック は固定）`
- L100: `操作キーを既定に戻す`
- L104: `細分化（段数・列数 / 枠をクリックしてキーを押す）`
- L110: `列`
- L110: `段`
- L125: `キャンセル`
- L244: `列の削除`
- L244: `列の追加`
- L244: `段の削除`
- L244: `段の追加`

## keyseq/presentation/screen_grid/grid_overlay_window.py

- L42: `枠の窓のクリック透過設定に失敗しました`

## keyseq/presentation/screen_grid/screen_grid_controller.py

- L88: `枠の失敗後に状態を閉じられませんでした`
- L92: `枠の操作に失敗しました`
- L93: `枠の操作に失敗しました: {exc}`

## keyseq/presentation/views/compact_view/compact_view.py

- L28: `▸ フック`
- L32: `▸ 表示`

## keyseq/presentation/views/compact_view/display_frame.py

- L17: `▾ 表示`
- L24: `常に手前`
- L29: `フルに戻す`
- L31: `キーボードUI`
- L45: `キーボードUIを常に手前`

## keyseq/presentation/views/compact_view/hook_frame.py

- L18: `▾ フック`
- L37: `フック停止トリガー: `
- L42: `一時停止/再開キー: `
- L48: `このキーマップセットで個別指定する`
- L54: `確認して実行`

## keyseq/presentation/views/compact_view/sequence_frame.py

- L40: `▸ シーケンス`
- L40: `▾ シーケンス`

## keyseq/presentation/views/compact_view/trigger_box.py

- L18: `トリガー一覧`

## keyseq/presentation/views/full_view/call_view_frame.py

- L61: `▸ 呼び出し先`
- L63: `▾ 呼び出し先`
- L68: `呼び出し中ではありません`

## keyseq/presentation/views/full_view/display_frame.py

- L15: `表示`
- L19: `常に手前`
- L25: `省略表示`
- L27: `キーボードUI`
- L41: `キーボードUIを常に手前`

## keyseq/presentation/views/full_view/file_frame.py

- L13: `ファイル`
- L15: `保存`
- L16: `別名で保存...`
- L17: `読込...`
- L19: `新規作成`

## keyseq/presentation/views/full_view/hook_frame.py

- L17: `フック`
- L31: `フック停止トリガー: `
- L36: `クリア`
- L40: `一時停止/再開キー: `
- L45: `クリア`
- L50: `このキーマップセットで個別指定する`
- L58: `確認して実行`

## keyseq/presentation/views/full_view/keymap_box.py

- L17: `キーマップ管理`
- L45: `追加`
- L47: `キーマップ変更`
- L49: `削除`
- L52: `保存`
- L53: `別名で保存`
- L54: `読込`

## keyseq/presentation/views/full_view/sequence_box.py

- L19: `出力シーケンス（選択中トリガーの内容）`
- L59: `追加`
- L60: `編集`
- L61: `削除`
- L62: `複製`
- L64: `上へ`
- L65: `下へ`
- L67: `保存`
- L68: `別名で保存`
- L69: `読込`
- L74: `連続実行`
- L80: `確認して実行`
- L88: `間隔(ms)`

## keyseq/presentation/views/full_view/trigger_box.py

- L17: `トリガー一覧（選択して編集）`
- L46: `追加`
- L47: `トリガー変更`
- L48: `削除`
- L50: `保存`
- L51: `別名で保存`
- L52: `読込`
- L56: `トリガーキーを抑止（suppress）`

## keyseq/presentation/views/menu_bar.py

- L8: `新規作成`
- L10: `保存`
- L11: `別名で保存…`
- L12: `読込（構成セット）…`
- L13: `履歴から読み込む…`
- L18: `起動時に読む構成セットを指定…`
- L19: `例を復元`
- L21: `終了`
- L22: `ファイル`
- L25: `プリセット編集…`
- L26: `参照元を掃除…`
- L27: `孤児ファイルの棚卸し…`
- L28: `隔離の管理…`
- L29: `キーボードUIを開く`
- L31: `外部レイアウトを追加…`
- L32: `レイアウトを削除…`
- L35: `物理キー名を表示`
- L43: `標準 (0)`
- L50: `フォントサイズ`
- L52: `設定`

## keyseq/presentation/views/status_bar.py

- L47: `ステータス`
