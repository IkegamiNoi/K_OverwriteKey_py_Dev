# リファクタ提案書の一覧（modified_proposal/INDEX.md）

`/refactor_check` の提案書（`NN_*.md`・独立採番）の一覧と実施状況。判断の経緯は `.claude_data/state/decisions.md`「計画NN」節と各フェーズの `decisions_archive`。
> このファイルは 2026-11-26 に `instructions/phase/current.md` から分けた。提案書を起票・実施・保留したら、このファイルの該当行を更新する（次採番もここ）。

- リファクタ提案書（`instructions/modified_proposal/NN_*.md`）も独立採番。**29 まで起票済**
  （07 = phase 09 の `/refactor_check` 由来・**実施済＝計画07** / 08 = phase 11 由来・**実施済＝計画08** /
  **09 = phase 13 由来・実施済＝計画10**〔`collect_forbidden_refs` を 100 行 → 26 行へ分割〕/
  **10 = phase 19 由来・実施済＝phase 19 task_07** /
  **11 = phase 28 由来・実施済＝phase 28 task_07**〔Esc の別用途つき閉じ処理の 3 重複を 1 関数へ〕 /
  **12 = phase 30 由来・見送り**〔「キーがあれば coerce_label」の 5 重複を 1 関数へ。「別タスク化候補」へ送付〕 /
  **13 = phase 34 由来・実施済＝phase 34 task_09**〔内部キーの定数化・キーマップ追加フローを `controllers/keymap_panel/` へ〕 /
  **14 = phase 36 由来・実施済＝phase 36 task_09**〔`split_loading.py` のホットキープリセット 9 関数を `hotkey_presets_files.py` へ〕 /
  **15 = phase 37 由来・実施済＝phase 37 task_09**〔アクション編集を `controllers/trigger_panel/` へ・`ActionControlFields.__init__` の分割と定数参照〕 /
  **16 = phase 38 由来・実施済＝phase 38 task_08**〔`sequence_runner.py` の次ステップ予約の集約・file_line 分岐の切り出し・分割〕 /
  **17 = phase 40 由来・実施済＝phase 40 task_11_refactor**〔上限 10000 の定数化・待機の mixin `send_wait.py`・file_line 未設定の判定の一本化〕）・
  **18 = phase 43 由来・実施済＝phase 43 task_10**〔トリガーの追加・改名・削除を `trigger_row_edit.py` へ・まとめて設定のダイアログの `__init__` 分割・`range_or_index` の共通化〕 /
  **19 = phase 45 由来・実施済＝phase 45 task_12_refactor**〔`sequence_runner.py` 649 行の連続実行の進行を mixin へ・`apply_control` 104 行の分割〕 /
  **20 = phase 48 由来・実施済＝phase 48 task_07_refactor**〔`CallViewController` の省略表示の分岐を置き場の配置役へ・保存の待ち時間の定数共有〕 /
  **21 = phase 55 由来・実施済＝phase 55 task_06_refactor**〔Win32 の窓・マウスの問い合わせを `infrastructure/win32_window.py` へ・初回だけ記録の同型 4 個を共通補助へ〕 /
  **22 = phase 56 由来・実施済＝phase 56 task_09_refactor**〔keymap の任意キーの受け渡しの 3 か所を 1 定義へ・振り直しの段を自動割当の順から作る〕 /
  **23 = phase 57 由来・実施済＝phase 57 task_08_refactor**〔矢印の操作キーの集合を 1 か所に・選択の解除を 1 つの呼び出しに・パネルのボタンの色を定数に〕 /
  **24 = phase 58 由来・実施済＝phase 58 task_07_refactor**〔省略表示の上部の見出しの文言を 1 関数に・区画の題名と配置を登録時に受け取る・フル表示の 3 枠のタプルを 1 か所に〕 /
  **25 = phase 68 由来・実施済**（2026-10-25・フェーズ外で単独実施）〔子ファイルの種別の表示名の表 4 か所を `presentation/child_kind_labels.py` へ〕 /
  **26 = phase 69 由来・保留**（2026-10-26 ユーザー判断）〔`KeyboardWindow.redraw` 100 行からキーの文字の描画を抽出・キーが無いレイアウトの大きさの定数化〕 /
  **27 = phase 70 由来・保留**（2026-10-29 ユーザー判断）〔`app.py` の「呼んで失敗をログに残す」同型の try/except 5 個を 1 関数へ〕
  **28 = phase 75 由来・実施済＝phase 75 task_15**（2026-11-22）〔`macos/backend.py` を 1 クラス 1 ファイルへ・`modal.install_minimize_grab_custody` の入れ子の関数を外へ〕
  **29 = phase 81 由来・実施済＝phase 81 task_05_refactor**（2026-11-25）〔英字 1 文字の大文字の判定を domain の 1 関数へ・Windows の press / release の送る名前を 1 つの補助へ〕
  **30 = phase 84 由来・実施済＝phase 84 task_05_refactor**（2026-11-26）〔一時メッセージ欄の書き込みを `App._show_flash_area` に一本化（一時メッセージ、無ければ下敷き）〕
  次採番は **`31_<topic>`**。**「計画09」は提案書を持たない**（`/spec_split` による正本の分割で、
  規範は `.claude/skills/spec_split/SKILL.md`。**提案書 09 とは別物**）。
