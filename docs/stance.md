# transform/align.py・stance.py — 整列と特徴量の規則(loop_004)

## 整列(F-04)

- entity_id ごとに著者別の段落束を作り、**同一実体タグが連続する段落範囲を 1 passage に併合**
- 複数実体を持つ段落は各実体の passage に重複して属してよい
- quote は表示層(Paragraph.raw)の逐語連結(\n 区切り)。正規化を一切加えない(Q-03 の構成的担保)
- Q-02 実測(辞書 v2.2・2026-07-23): **passages 570 / 2 名以上 31 実体(基準 12)/ 3 名揃い 14(基準 5)**

## 特徴量(F-05)— 算出規則 v1

| 特徴 | 定義 |
|---|---|
| comparative | 比較標識ヒット数(kind=pattern は正規表現)/ 文数 |
| religious, sensory | 辞書ヒット数(表層部分一致)/ 形態素数(補助記号・空白除く) |
| first_person | UniDic 代名詞かつ一人称リスト(私・わたくし・僕・俺・我・われ・吾)/ 形態素数 |
| present_tense | 非過去文数 / 文数。**近似規則: 文末 3 トークン内に助動詞「た」(語彙素)があれば過去文** |
| sent_len | 空白除去文字数 / 文数(文分割は 。！？) |
| comma_density | 読点「、」数 / 空白除去文字数 |

既知の近似(GUIDE §7 の「現在形率の粒度」に対応する明示):
- religious/sensory は分子=表層一致・分母=形態素数の混合単位
- 現在形率は文末近傍の「た」有無のみで判定(推量・命令等のモダリティは区別しない)
- 誤判定が特徴量を歪める兆候が出たら精緻化をエスカレーション

## レキシコン統治(AGENTS §3 / Q-04 / Q-06)

- data/curated/lexicons/*.csv は先頭行 `# version: X.Y` 必須(欠落は LexiconVersionError)
- 全特徴量レコードに `lexicon_version`(comparative:X|religious:X|sensory:X)を刻む(Q-04)
- 変更は `data: lexicon vX.Y` 専用コミット+感度分析(F-12: `sensitivity_report`)
- v0.1→v1.0(2026-07-23 承認): 570 passages 中 429 が変位(初回実計測化)。
  レポート: out/sensitivity/v0.1_to_v1.0.json
- 単字衝突対策: 「音」不採用(観音)・「唐」不採用(唐招提寺)・「光」は月光・日光菩薩との
  混在承知で採用

## 実行

- `python -m transform.stance` → out/silver_passages.json(passages+features+coverage)
- T-035(感度分析)は本ループで実装済み。GUIDE §1 の P4(loop_005)記載の F-12 は
  本実装の再利用(ベースライン適用時の感度分析運用)を指す
