# extract/aozora.py — パーサ規則(loop_002)

GUIDE §2 の実装規則。実体照合・スタンスに依存しない純パーサ(詩案・捕物帳案へ持ち回る共通資産)。

## 二層の実装(AGENTS §1)

| 層 | 実体 | 規則 |
|---|---|---|
| 表示層 | `AozoraDoc.header_raw / raw_body / footer_raw`、`Paragraph.raw`(= raw_body の逐語スライス) | 入力の部分文字列そのもの。`reconstruct()` = 三連結が入力全文と一致(T-012 で保証) |
| 中間 | `Paragraph.base` + `ruby[]` + `notes[]` | ルビ記法(《》・｜)と注記(［＃…］)を分離した親文字列。位置は base オフセット |
| 分析層 | `Paragraph.analysis` + `a2d` | base への**文字単位 NFKC**。`a2d[i]` = 分析層 i 文字目 → `raw` の文字範囲 |

## 規則と近似(明示)

1. **段落分割**: 本文の 1 物理行 = 1 形式段落(青空文庫散文の規約。空行は区切り、
   字下げ全角空白は base に保持)。注記のみの行(字下げ指示等)は段落にせず
   `block_notes` に種別付きで記録
2. **ルビ親文字判定**(｜なし時): 直前の漢字連続(々〆ヶ含む)を親とする近似。
   読み列は `Ruby.reading` に保持(将来のモーラ分析資産)
3. **NFKC は文字単位**: 複数文字の合成(か+濁点等)は扱わない。この近似により
   a2d の対応が常に 1 文字 → 1 範囲で保たれる(T-013/T-015)
4. **注記種別**: heading(「…」は大/中/小見出し)/ emphasis(傍点・傍線)/
   indent(字下げ)/ gaiji(※直後・水準・U+・「＋」を含む)/ other
5. **フッタ**: 行頭「底本：」以降を footer_raw とし、底本名・レーベル・出版社・親本・
   入力者・校正者を構造化。底本行が構造化できない場合は `AozoraFooterError`(T-014)
6. **文字コード**: bronze は cp932 バイト列で保存し `load_bronze()` で復号。
   フィクスチャは UTF-8(改行は原文どおり CRLF を newline='' で保持)

## bronze 取得(N-02)

- `make bronze`(= `python -m extract.aozora fetch`)の**手動実行のみ**。UA 明示・
  リトライ 3 回・1 秒間隔。対象は config/corpus.json(loop_001 で確定した 8 作品)
- テストは data/fixtures/ のみ参照(合成 1 + 実三作冒頭部 3)。ネットワーク不要

## 検証実績(loop_002)

bronze 全 8 作品で `reconstruct()` 逐語一致・オフセット対応の整合を確認
(和辻 551 段落/亀井 531 段落・ルビ 3106/堀 425 段落)。
