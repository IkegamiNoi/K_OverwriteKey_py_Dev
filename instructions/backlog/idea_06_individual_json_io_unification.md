# idea_06_individual_json_io_unification.md

## 概要

個別 JSON の保存/読込フロー（**keymap / trigger_set / sequence** の 3 種）は、
`save_X` / `save_X_as` / `save_X_to_path` / `load_X_file` の **4 点セットが同じ骨格で 3 回反復**している。
これを共通テンプレート（基底クラスまたは高階関数）へ集約する案。

**現時点では着手しない（保留）**。骨格は同じでも**細部が 9 点食い違って**おり、
うち 2 点は既存の不整合（→ [idea_05](idea_05_trigger_set_source_path_inconsistency.md)）であるため。
**着手条件は下記「前提条件」を参照**。

## 起票経緯（2026-07-23）

出所: 暫定仕様 [03_config_io_controller_split](../history/03_config_io_controller_split.md) §5「案 2」。

phase 04（ConfigIoController の責務分割）の設計時に、3 種の同型ブロックを
「分割のみ・共通化しない（案 1）」か「共通テンプレートへ集約（案 2）」かで比較し、
**案 1 を採用**した。案 2 は将来の再評価対象として本 idea へ分離する。

ユーザー方針（2026-07-23）: `current.md` の「別タスク化候補」に置くと検討候補として
俎上に載らないため、**backlog へ idea 化して保留**とする
（同じ判断で [idea_04](idea_04_font_settings_controller.md) も起票済）。

## 現状

phase 04 の分割後は以下が対象になる想定（着手時に実際のパスを再確認すること）:

- `keyseq/presentation/controllers/config_io/keymap_file_io.py`（D・~94 行）
- `keyseq/presentation/controllers/config_io/trigger_set_file_io.py`（E・~78 行）
- `keyseq/presentation/controllers/config_io/sequence_file_io.py`（F・~83 行）

**共通の骨格**: `save_X`（source_path 判定 → 「読込で持ってきた…別名で保存しますか？」の askyesno →
未設定なら `choose_save_path_with_collision`）→ `save_X_as`（`asksaveasfilename` → to_path）→
`save_X_to_path`（try: service 呼び出し → 状態更新 → refresh → flash + showinfo /
except: flash(auto_clear=False) + showerror）→ `load_X_file`。

**食い違う 9 点**（実コードで裏取り済。詳細な表は暫定仕様 03 §5 が正）:
ダイアログ文言 / 対象の取得元 / dirty 管理 / load 前の `confirm_save_if_dirty` の有無（E のみ有）/
source_path の置き場 / 保存後の refresh 先 / 保存結果の反映方法（F のみ引数 dict を破壊的更新）/
**ラベル連動ダイアログの有無（E のみ無）** / **source_path の読み書きの対称性（E のみ分断）**。

最後の 2 点は設計上の差ではなく**既存の不整合**であり、共通化すると
「揃える」過程で意図せず修正され、挙動が変わる。これが phase 04 で案 2 を採らなかった直接の理由。

## 提案（方向性・要設計）

- **案 A: 基底クラス** — 共通フローを基底クラスに置き、3 種は差分をオーバーライドする。
- **案 B: 高階関数 / 設定オブジェクト** — 差分をパラメータ（文言・取得関数・dirty 更新関数・
  refresh 関数 等）として渡す。継承より結合が緩い。
- **併せて要検討**: 差分が 9 種類ある以上、パラメータが多すぎて
  「共通化したのに読みにくい」状態になりうる（`.claude/rules/anti_patterns.md`「過剰な共通化」）。
  **共通化しないという結論も正当な着地点**として扱う。

## 前提条件（すべて満たすまで着手しない）

1. **phase 04（ConfigIoController の分割）が完了していること**。分割前に共通化すると
   差分が読めなくなる。
2. **[idea_05](idea_05_trigger_set_source_path_inconsistency.md)（E の source_path 不整合）が
   解消されていること**。未解消のまま共通化すると、不整合を暗黙に修正してしまう。
   併せて食い違い 8 点目（E のラベル連動ダイアログ無し）も、意図的な仕様なのか
   実装漏れなのかを確定させる必要がある。
3. **共通化の動機が実際に存在すること**。以下のいずれか:
   - 個別 JSON の **4 種目**が追加される
   - 3 モジュールのいずれかを直すたびに**他 2 つも直している**という実績が出た
   - 上記 1・2 の解消により、9 点の差異が**実質 6 点以下**（文言・取得元・refresh 先など
     素直にパラメータ化できるものだけ）に減った

**注意**: 分割後は各モジュールが 80〜95 行に収まり責務も明確になるため、
「同型だが別物が 3 つ」は許容できる状態になる見込み。前提 3 を満たさないまま着手すると
`.claude/rules/anti_patterns.md`「将来必要そうという理由で広く実装する」に該当する。

## 想定スコープ

- 含む: `config_io/` 配下の keymap / trigger_set / sequence の 3 モジュールと、
  共通化先の新規モジュール。
- 含まない: A（構成セット）/ B（起動設定）/ C（共有ダイアログヘルパ）の共通化 /
  `config_service`（application 層）への変更 / `self._app.` reach-through の解消。
- 影響レイヤ: presentation のみ。
- 仕様変更: **なし**（挙動不変が前提。挙動が変わるなら前提条件 2 が未達ということ）。
- 優先度: **低**（保留）。

## 関連

- 分離元: 暫定仕様 [03_config_io_controller_split](../history/03_config_io_controller_split.md) §5（案 2・9 点の差異表が正）
- 前提: [idea_05](idea_05_trigger_set_source_path_inconsistency.md)（E の source_path 不整合の解消）
- 同種の保留 idea: [idea_04](idea_04_font_settings_controller.md)（着手トリガー成立まで保留）
