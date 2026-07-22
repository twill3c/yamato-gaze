"""Gold 出力(F-07): sites.geojson / passages.json / counts.json(SPEC §5)。

- 実行: `python -m gold.export`(bronze → parse → tag → align → features → xy → gold)
- Q-05: 座標が verified=false の実体は sites.geojson に出さず、除外数を品質レポートへ
- 仏像(statue)は lat/lon 未設定なら親寺の座標・verified を継承する
- quote は表示層逐語(Q-03)。source_note は底本・入力者・校正者の三点を必ず含む
- ライセンス(N-04): 引用は PD(青空文庫)由来、features 等の自作データは CC BY 4.0
"""

from __future__ import annotations

import json
from pathlib import Path

LICENSE_STR = "quotes: PD (Aozora Bunko) / data: CC BY 4.0"

PUBLIC_DIRS = [Path("public/data"), Path("web/public/data")]


def format_source_note(sn: dict) -> str:
    parts = [f"底本:「{sn['底本名']}」{sn.get('底本レーベル') or ''}、{sn.get('底本出版社') or ''}".rstrip("、 ")]
    if sn.get("入力者"):
        parts.append(f"入力:{sn['入力者']}")
    if sn.get("校正者"):
        parts.append(f"校正:{sn['校正者']}")
    return " / ".join(parts)


def build_counts(passages: list[dict]) -> dict:
    counts: dict[str, dict] = {}
    for p in passages:
        c = counts.setdefault(
            p["entity_id"], {"passage_count": 0, "authors_count": 0, "by_author": {}}
        )
        c["passage_count"] += 1
        c["by_author"][p["author"]] = c["by_author"].get(p["author"], 0) + 1
    for c in counts.values():
        c["authors_count"] = len(c["by_author"])
    return counts


def build_sites(entity_rows: list[dict], counts: dict) -> tuple[dict, list[str]]:
    """entities 行と counts から FeatureCollection と除外 entity_id リストを返す。"""
    by_id = {r["entity_id"]: r for r in entity_rows}

    def resolved(row: dict) -> tuple[float, float, str] | None:
        lat, lon, ver = (row.get("lat") or "").strip(), (row.get("lon") or "").strip(), (row.get("verified") or "false").strip()
        if lat and lon and ver != "false":
            return float(lat), float(lon), ver
        parent = by_id.get((row.get("parent") or "").strip())
        if row.get("type") == "statue" and parent is not None:
            return resolved(parent)
        return None

    features, excluded = [], []
    for row in entity_rows:
        eid = row["entity_id"]
        if eid not in counts:
            continue  # 言及ゼロの実体は地図に出さない
        loc = resolved(row)
        if loc is None:
            excluded.append(eid)
            continue
        lat, lon, ver = loc
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {
                    "entity_id": eid,
                    "name": row["name"],
                    "type": row["type"],
                    "parent": (row.get("parent") or "").strip() or None,
                    "authors_count": counts[eid]["authors_count"],
                    "passage_count": counts[eid]["passage_count"],
                    "lat": lat,
                    "lon": lon,
                    "verified": ver,
                    "license": LICENSE_STR,
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}, excluded


def load_entity_rows(path: str | Path = "data/curated/entities.csv") -> list[dict]:
    import csv

    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def build_all() -> dict:
    """パイプライン全段を実行して gold 三点+品質レポートを返す。"""
    from analyze.project2d import FEATURE_KEYS, pca_2d
    from extract.aozora import load_bronze, parse
    from transform.align import build_passages
    from transform.entities import CURATED_ENTITIES, load_entities, tag_paragraphs
    from transform.stance import (
        CURATED_LEXICONS,
        WORK_AUTHORS,
        compute_features,
        load_lexicons,
    )

    lexicons = load_lexicons(CURATED_LEXICONS)
    entities = load_entities(CURATED_ENTITIES)
    passages: list[dict] = []
    raw_bodies: dict[str, str] = {}
    for wid, author in WORK_AUTHORS.items():
        doc = parse(load_bronze(wid))
        raw_bodies[wid] = doc.raw_body
        tags = tag_paragraphs([p.base for p in doc.paragraphs], entities).tags
        note = format_source_note(doc.source_note)
        for p in build_passages(wid, doc, tags):
            f = compute_features(p.analysis, lexicons)
            passages.append(
                {
                    "passage_id": p.passage_id,
                    "entity_id": p.entity_id,
                    "author": author,
                    "work": doc.title,
                    "quote": p.quote,
                    "source_note": note,
                    "char_start": p.char_start,
                    "char_end": p.char_end,
                    "features": {k: round(v, 6) for k, v in f.values.items()},
                    "lexicon_version": f.lexicon_version,
                }
            )

    rows = [[p["features"][k] for k in FEATURE_KEYS] for p in passages]
    pca = pca_2d(rows, standardize=True)
    for p, (x, y) in zip(passages, pca.xy):
        p["xy"] = [round(x, 4), round(y, 4)]

    counts = build_counts(passages)
    sites, excluded = build_sites(load_entity_rows(), counts)
    report = {
        "n_passages": len(passages),
        "n_entities_with_passages": len(counts),
        "n_sites": len(sites["features"]),
        "excluded_unverified": excluded,
        "n_excluded_unverified": len(excluded),
        "pca_explained": [round(e, 4) for e in pca.explained],
        "license": LICENSE_STR,
    }
    return {
        "sites": sites,
        "passages": passages,
        "counts": counts,
        "report": report,
        "raw_bodies": raw_bodies,
    }


def main() -> int:
    gold = build_all()
    for base in PUBLIC_DIRS:
        base.mkdir(parents=True, exist_ok=True)
        (base / "sites.geojson").write_text(
            json.dumps(gold["sites"], ensure_ascii=False, indent=1), encoding="utf-8"
        )
        (base / "passages.json").write_text(
            json.dumps(gold["passages"], ensure_ascii=False, indent=1), encoding="utf-8"
        )
        (base / "counts.json").write_text(
            json.dumps(gold["counts"], ensure_ascii=False, indent=1), encoding="utf-8"
        )
    out = Path("out/quality_report.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(gold["report"], ensure_ascii=False, indent=1), encoding="utf-8")
    r = gold["report"]
    print(
        f"passages {r['n_passages']} / sites {r['n_sites']} / "
        f"除外(未verified) {r['n_excluded_unverified']}"
    )
    print(f"→ {[str(b) for b in PUBLIC_DIRS]} + {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
