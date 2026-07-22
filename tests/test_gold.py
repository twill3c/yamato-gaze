# T-024 / Q-01 — gold 30 段落に対する再現率・適合率の機械検査
#
# gold_annotations.csv は人手アノテ(2026-07-23 ユーザ承認)。注釈規約:
# - 別名限定主義: 辞書の名称・別名で言及された実体のみ(同一指示語は含めない)
# - 係り先明示(「聖林寺の十一面観音」)は両親寺文脈でも gold に含める
#   (タガーは保留するため、再現率は真の下限として測られる)
# bronze が無い環境(CI)では skip(実測は make bronze 後のローカル/手動工程)。
import csv
from pathlib import Path

import pytest

from transform.entities import load_entities, tag_paragraphs

ROOT = Path(__file__).parent.parent
BRONZE = ROOT / "data" / "bronze"
GOLD = ROOT / "data" / "curated" / "gold_annotations.csv"


@pytest.mark.validation
@pytest.mark.skipif(
    not (BRONZE / "watsuji_kojijunrei.txt").exists(),
    reason="bronze 未取得(make bronze の手動実行が必要)",
)
def test_t024_gold_recall_precision():
    from extract.aozora import load_bronze, parse

    with open(GOLD, encoding="utf-8", newline="") as f:
        gold_rows = list(csv.DictReader(f))
    assert len(gold_rows) == 30, "gold は 30 段落(Q-01)"

    entities = load_entities(ROOT / "data" / "curated" / "entities.csv")
    results = {}
    for wid in sorted({r["work_id"] for r in gold_rows}):
        doc = parse(load_bronze(wid))
        results[wid] = tag_paragraphs([p.base for p in doc.paragraphs], entities)

    tp = fp = fn = 0
    for r in gold_rows:
        i = int(r["para_index"])
        gold = set(filter(None, r["entity_ids"].split("|")))
        pred = {t.entity_id for t in results[r["work_id"]].tags[i]}
        tp += len(gold & pred)
        fp += len(pred - gold)
        fn += len(gold - pred)

    recall = tp / (tp + fn) if tp + fn else 1.0
    precision = tp / (tp + fp) if tp + fp else 1.0
    print(f"\nQ-01: recall={recall:.3f} (TP={tp} FN={fn}) precision={precision:.3f} (FP={fp})")
    assert recall >= 0.80, f"Q-01 再現率不足: {recall:.3f}"
    assert precision >= 0.90, f"Q-01 適合率不足: {precision:.3f}"
