# R17 申し送り

- 最終標準検証:
  - `compileall`: 成功
  - `unittest discover`: 50 件 OK
  - `tests/smoke_app.py`: `SMOKE OK`
- 主要 grep 条件:
  - `ActionDialog` in `views.py`: 0 件
  - `_cur_sel_or`: 0 件
  - `chain`: 0 件
  - `_refresh_keymap_switch_ui`: 0 件
  - `ConfigService` private helper 参照: 0 件
  - `"us_tkl"`: domain 定数定義のみ
  - `300`: run_to_end delay 定数定義と既存コメントのみ
- `instruction/common/codebase_map.md` と `architecture_rules.md` は今回のデッドコード削除・共通化・エラー表示追加と矛盾なし。更新不要。
- フック ON を含む手動シナリオは、この環境でグローバルフックを張るリスクを避けるため未実施。スモーク起動までは確認済み。
