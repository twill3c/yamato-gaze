# analyze/ — ベースライン距離と 2 次元射影(loop_005)

## ベースライン距離(F-06)— analyze/baseline.py

- 変位ベクトル = 大和段落重心 − ベースライン重心。大和側は passage 単位(silver)、
  ベースライン側は段落単位(30 字未満の段落は日付行等のノイズとして除外)
- ベースライン構成(E-1 確定): 和辻 = 埋もれた日本・京の四季・城(92 段落)/
  亀井 = 八ヶ岳登山記・馬鈴薯の花(43 段落 — 薄さは E-1 で許容済み)/
  堀 = 信濃三篇 斑雪・辛夷の花・橇の上にて(151 段落、見出し境界で切り出し)
- 実行: `python -m analyze.baseline` → out/baseline_displacement.json

### 実測(lexicon v1.0, 2026-07-23)

| 著者 | 主な変位(大和 − ベースライン) |
|---|---|
| 和辻 | comparative +0.030, present_tense +0.031, sent_len −4.3 |
| 亀井 | **comparative +0.085, religious +0.011, present_tense +0.120**, sent_len +5.9 |
| 堀 | sent_len +20.4, present_tense −0.125(信濃三篇は会話・短文が多い) |

既知の限界: ノルムは単位混在(sent_len の文字数が支配的)。軸別の解釈を主とし、
ノルム比較が必要になったら標準化変位の導入をエスカレーション。

## 2 次元射影(F-09 用 xy)— analyze/project2d.py

- PCA 自前実装(N-01 遵守・numpy 不使用): Jacobi 回転法による対称行列の固有分解。
  7 次元・570 点では十分に安定(T-042 で解析解一致を機械検査)
- 標準化(z-score)を既定で適用(sent_len のスケール支配を防ぐ)。
  符号規約: 各主成分は最大絶対値成分が正(決定論、T-042 で検査)
- 実行: `python -m analyze.project2d` → out/silver_passages_xy.json(xy+components+explained)

### 実測(570 passages)

- 寄与率: PC1 24.5% / PC2 16.3%
- PC1 ≈ 内省⇔スケッチ軸(present_tense +0.57, first_person −0.46, sent_len −0.49)
- PC2 ≈ 美術史比較軸(comparative +0.63, sensory +0.41)

## テスト規範(HC-004 反映)

解析解を期待する合成フィクスチャは、前提条件(直交性・一意性)をテスト内 assert で
検算し、導出をコメントに残す(T-042 に適用済み)。
