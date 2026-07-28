# yamato-gaze — 大和路の視線

和辻哲郎『古寺巡礼』・亀井勝一郎『大和古寺風物誌』・堀辰雄『大和路・信濃路』を、
奈良の寺院・仏像という対象を固定して整列比較し、視線の三型(比較 / 祈り / 感覚)を
計量して巡礼路地図の「三面鏡」として公開するプロジェクト。

theme-survey.md(全 13 案の調査)の案 11。stylometry 系と atlas 系の合流原型であり、
ISLP(Python)学習前のテキスト処理実践、および R/stylo への入口(P4 サイドカー)を兼ねる。

## ドキュメント構成(読む順)

1. **SETUP.md** — 開発開始手順(Windows / harness-kit 流用)
2. **CLAUDE.md / AGENTS.md** — エージェント規律(引用二層原則・実体辞書 curated 限定が生命線)
3. **SPEC.md** — 要求・スタンス特徴量・Gold 二枚契約(sites.geojson + passages.json)・品質基準
4. **IMPLEMENTATION_GUIDE.md** — フェーズ計画(P1 探査 → P2 パーサ → P3 整列 → P4 分析 → P5 公開 → P6 奈良)
5. **TEST_SPEC.md** — テストケース(引用逐語一致 T-051 が本案の要)

theme-survey.md は docs/ へコピーして最初のコミットに含めること。

## 実行(P5 時点)

```powershell
pip install pytest "fugashi[unidic-lite]"
make bronze                    # 青空文庫から 8 作品を取得(手動実行のみ, N-02)
python -m gold.export          # Gold 生成(sites/passages/counts)
python -m gold.validate        # 品質検査(Q-02/Q-03/三角測量/契約)
python -m pytest -q            # 84 テスト(フィクスチャ駆動・ネットワーク不要)
cd web; npm install; npm run dev   # 三面鏡 UI(localhost:3000)
```

## デプロイ(Vercel)

docs/deploy.md 参照。Root Directory = `web`、Framework = Next.js(静的エクスポート)。

## ライセンス

- コード: MIT(LICENSE)
- データ: 引用本文は PD(青空文庫由来・底本表記付き)、自作データは CC BY 4.0
  (LICENSE-DATA.md — N-04 の二層構成)

## 締切

P5(Vercel 公開)= 奈良行きの 2 週間前。P6 = 現地検証(スマホで三面鏡を開き、
仏像の前で引用範囲と座標を verified 更新する)。
