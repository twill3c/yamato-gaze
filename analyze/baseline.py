"""著者ベースライン距離(F-06)。

「大和を書くときの変位ベクトル」= 大和段落重心 − ベースライン重心(GUIDE §5)。

ベースライン構成(E-1 確定 2026-07-23):
- watsuji: 埋もれた日本・京の四季・城(全段落)
- kamei: 八ヶ岳登山記・馬鈴薯の花(全段落)
- hori: 『大和路・信濃路』の信濃三篇(斑雪・辛夷の花・橇の上にて)の段落を転用

段落は MIN_CHARS(30 字)未満を除外(日記の日付行等のノイズ対策。規則は docs/analyze.md)。
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from transform.stance import CURATED_LEXICONS, compute_features, load_lexicons

MIN_CHARS = 30

BASELINE_WORKS = {
    "watsuji": ["watsuji_umoreta", "watsuji_kyonoshiki", "watsuji_shiro"],
    "kamei": ["kamei_yatsugatake", "kamei_bareisho"],
}
HORI_SHINANO_SECTIONS = {"斑雪", "辛夷の花", "橇の上にて"}

FEATURE_KEYS = [
    "comparative", "religious", "sensory", "first_person",
    "present_tense", "sent_len", "comma_density",
]


def centroid(vectors: list[dict[str, float]]) -> dict[str, float]:
    if not vectors:
        raise ValueError("重心には 1 ベクトル以上が必要です")
    keys = list(vectors[0].keys())
    return {k: sum(v[k] for v in vectors) / len(vectors) for k in keys}


def displacement(
    yamato: list[dict[str, float]], baseline: list[dict[str, float]]
) -> dict[str, float]:
    """変位ベクトル = 大和重心 − ベースライン重心(F-06)。"""
    cy, cb = centroid(yamato), centroid(baseline)
    return {k: cy[k] - cb[k] for k in cy}


def _hori_shinano_paragraphs(doc) -> list[str]:
    out: list[str] = []
    current = None
    for p in doc.paragraphs:
        if p.kind == "heading":
            current = p.base.strip().replace("　", "")
            continue
        if current in HORI_SHINANO_SECTIONS:
            out.append(p.analysis)
    return out


def baseline_paragraph_texts() -> dict[str, list[str]]:
    """著者 → ベースライン段落(分析層)のリスト。"""
    from extract.aozora import load_bronze, parse

    result: dict[str, list[str]] = {}
    for author, works in BASELINE_WORKS.items():
        texts: list[str] = []
        for wid in works:
            doc = parse(load_bronze(wid))
            texts.extend(p.analysis for p in doc.paragraphs)
        result[author] = texts
    result["hori"] = _hori_shinano_paragraphs(parse(load_bronze("hori_yamatoji")))
    return {
        author: [t for t in texts if len(t.strip()) >= MIN_CHARS]
        for author, texts in result.items()
    }


def main() -> int:
    lexicons = load_lexicons(CURATED_LEXICONS)
    silver = json.loads(Path("out/silver_passages.json").read_text(encoding="utf-8"))

    yamato_by_author: dict[str, list[dict[str, float]]] = {}
    for rec in silver["passages"]:
        yamato_by_author.setdefault(rec["author"], []).append(rec["features"])

    report = {}
    for author, texts in baseline_paragraph_texts().items():
        base_vecs = [compute_features(t, lexicons).values for t in texts]
        disp = displacement(yamato_by_author[author], base_vecs)
        norm = math.sqrt(sum(v * v for v in disp.values()))
        report[author] = {
            "n_baseline_paragraphs": len(base_vecs),
            "n_yamato_passages": len(yamato_by_author[author]),
            "baseline_centroid": centroid(base_vecs),
            "yamato_centroid": centroid(yamato_by_author[author]),
            "displacement": disp,
            "norm": norm,
            "lexicon_version": compute_features("。", lexicons).lexicon_version,
        }
        print(f"── {author}: baseline {len(base_vecs)} 段落 / 大和 {len(yamato_by_author[author])} passages / |変位| = {norm:.4f}")
        for k in FEATURE_KEYS:
            print(f"   {k:>14}: {disp[k]:+.4f}")

    out = Path("out/baseline_displacement.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"→ {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
