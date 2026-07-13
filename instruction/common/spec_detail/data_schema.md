## 5. データ構造

## 5.1 content.json

```json
{
  "nodes": {
    "nodeId": {
      "text": "内容"
    }
  }
}
```

---

## 5.2 structure.json

```json
{
  "edges": [
    {
      "from": "nodeA",
      "to": "nodeB",
      "type": "normal"
    }
  ]
}
```

---

## 5.3 layout.json

```json
{
  "columns": [
    { "id": "c1", "width": 100 },
    { "id": "c2", "width": 150 }
  ],
  "rows": [
    { "id": "r1", "height": 100 },
    { "id": "r2", "height": 120 }
  ],
  "positions": {
    "nodeA": { "col": "c1", "row": "r1" }
  }
}
```

### 補足

* 上記 3 ファイルはマップの内容・構造・レイアウトを分離して保存する
* ビュー状態（スクロール位置、ズーム倍率）は MVP では保存対象外とする
* 将来的に UI 状態保存を追加する場合は別設定ファイルとして扱う

---
