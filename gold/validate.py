"""Gold 検査(F-07 / T-051〜T-055)。

`python -m gold.validate` で public/data/ と bronze を突合し、
違反があれば一覧を印字して終了コード 1。結果は out/quality_report.json に追記。
"""

from __future__ import annotations

import json
from pathlib import Path

AUTHORS = {"watsuji", "kamei", "hori"}
SITE_TYPES = {"temple", "statue"}
PASSAGE_REQUIRED = (
    "passage_id", "entity_id", "author", "work", "quote", "source_note",
    "char_start", "char_end", "features", "lexicon_version", "xy",
)


def check_quotes(passages: list[dict], raw_bodies: dict[str, str]) -> list[str]:
    """Q-03/T-051: quote が bronze 本文の該当範囲と逐語一致(1 字違いも FAIL)。"""
    errs = []
    for p in passages:
        wid = None
        # passage_id は {work_id}-... 形式。work フィールドは表示名のため id を引き当てる
        for known in raw_bodies:
            if p["passage_id"].startswith(known):
                wid = known
                break
        if wid is None:
            wid = p.get("work")
        raw = raw_bodies.get(wid)
        if raw is None:
            errs.append(f"{p['passage_id']}: 対応する bronze 本文が見つからない")
            continue
        sliced = raw[p["char_start"] : p["char_end"]].replace("\r\n", "\n").replace("\r", "\n")
        if sliced != p["quote"]:
            errs.append(f"{p['passage_id']}: quote が本文範囲と逐語一致しない(Q-03)")
    return errs


def check_coverage(counts: dict, min_multi: int = 12, min_all3: int = 5) -> list[str]:
    """Q-02/T-052: 2 名以上・3 名揃いの実体数下限。"""
    multi = sum(1 for c in counts.values() if c["authors_count"] >= 2)
    all3 = sum(1 for c in counts.values() if c["authors_count"] >= 3)
    errs = []
    if multi < min_multi:
        errs.append(f"Q-02: 2 名以上の実体 {multi} < {min_multi}")
    if all3 < min_all3:
        errs.append(f"Q-02: 3 名揃いの実体 {all3} < {min_all3}")
    return errs


def check_triangulation(sites: dict, passages: list[dict], counts: dict) -> list[str]:
    """T-054: counts / passages / sites を別経路で再集計して一致を確認。"""
    errs = []
    recount: dict[str, dict] = {}
    for p in passages:
        c = recount.setdefault(p["entity_id"], {"n": 0, "authors": set()})
        c["n"] += 1
        c["authors"].add(p["author"])

    if sum(c["passage_count"] for c in counts.values()) != len(passages):
        errs.append("T-054: counts の passage 合計 ≠ passages 件数")
    for eid, c in counts.items():
        r = recount.get(eid)
        if r is None or c["passage_count"] != r["n"] or c["authors_count"] != len(r["authors"]):
            errs.append(f"T-054: {eid} の counts が独立再計算と不一致")
    for f in sites.get("features", []):
        eid = f["properties"]["entity_id"]
        r = recount.get(eid)
        if r is None or f["properties"]["passage_count"] != r["n"]:
            errs.append(f"T-054: sites {eid} の passage_count が不一致")
    return errs


def check_contract(passages: list[dict], sites: dict) -> list[str]:
    """T-055: 必須フィールド・enum・source_note 100%(SPEC §5)。"""
    errs = []
    for p in passages:
        for k in PASSAGE_REQUIRED:
            if k not in p or p[k] in ("", None):
                errs.append(f"{p.get('passage_id', '?')}: 必須フィールド {k} 欠落")
        if p.get("author") not in AUTHORS:
            errs.append(f"{p.get('passage_id', '?')}: author enum 違反: {p.get('author')}")
    for f in sites.get("features", []):
        pr = f["properties"]
        if pr.get("type") not in SITE_TYPES:
            errs.append(f"{pr.get('entity_id')}: type enum 違反: {pr.get('type')}")
        for k in ("entity_id", "name", "authors_count", "passage_count", "verified", "license"):
            if pr.get(k) in ("", None):
                errs.append(f"{pr.get('entity_id', '?')}: sites 必須 {k} 欠落")
    return errs


def main() -> int:
    from extract.aozora import load_bronze, parse
    from transform.stance import WORK_AUTHORS

    base = Path("public/data")
    sites = json.loads((base / "sites.geojson").read_text(encoding="utf-8"))
    passages = json.loads((base / "passages.json").read_text(encoding="utf-8"))
    counts = json.loads((base / "counts.json").read_text(encoding="utf-8"))
    raw_bodies = {wid: parse(load_bronze(wid)).raw_body for wid in WORK_AUTHORS}

    errs = (
        check_quotes(passages, raw_bodies)
        + check_coverage(counts)
        + check_triangulation(sites, passages, counts)
        + check_contract(passages, sites)
    )
    report_path = Path("out/quality_report.json")
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}
    report["validate_errors"] = errs
    report["validate_ok"] = not errs
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

    if errs:
        print(f"NG — {len(errs)} 件:")
        for e in errs[:30]:
            print(f"  - {e}")
        return 1
    print(f"OK — quotes {len(passages)} 件逐語一致 / Q-02 / 三角測量 / 契約 すべて合格")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
